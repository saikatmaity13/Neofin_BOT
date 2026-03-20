import asyncio
import os
import re
import uuid
from datetime import datetime

import google.generativeai as _genai
from dotenv import load_dotenv as _load_dotenv
import streamlit as st

from app.llm.agent         import run_agent
from app.ui_theme          import apply_react_dark_theme, render_top_header, generate_pdf, _decision_styles

_load_dotenv()
_genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARIZER LOGIC
# ══════════════════════════════════════════════════════════════════════════════
def _local_summarise(memo: dict) -> str:
    decision   = memo.get("decision", "Unknown").upper()
    applicant  = memo.get("applicant_id", "N/A")
    amount     = memo.get("loan_amount",  "N/A")
    score      = memo.get("composite_score", "N/A")
    risk       = memo.get("risk_level",   "N/A")
    cibil      = memo.get("credit_score", "N/A")
    dti        = memo.get("debt_to_income","N/A")
    defaults   = memo.get("defaults",     "0")
    compliance = memo.get("compliance",   "Unknown")
    violations = memo.get("violations",   [])
    warnings   = memo.get("warnings",     [])
    market     = memo.get("market_risk",  "N/A")

    dec_word = {"APPROVED": "approved ✅", "REJECTED": "rejected ❌",
                "CONDITIONAL": "conditionally approved ⚠️", "MANUAL REVIEW": "flagged for manual review 🔍"
               }.get(next((k for k in ["APPROVED","REJECTED","CONDITIONAL","MANUAL REVIEW"] if k in decision), ""), decision)
    b1 = f"• Applicant {applicant} requesting {amount} has been {dec_word} with a composite score of {score}/100."

    try:
        c = int(str(cibil).split(".")[0])
        credit_desc = "excellent" if c >= 750 else "good" if c >= 650 else "fair" if c >= 550 else "poor"
    except Exception:
        credit_desc = "N/A"
    b2 = f"• Credit score is {cibil} ({credit_desc}), risk level is {risk}, and the market risk is {market}."

    try:
        d = int(str(defaults).split(".")[0])
        def_text = "no prior defaults" if d == 0 else f"{d} prior default(s) — this raised concern"
    except Exception:
        def_text = f"{defaults} default(s)"
    b3 = f"• Debt-to-income ratio is {dti} with {def_text}."

    if violations:
        b4 = f"• Compliance status: {compliance}. Key violation: {violations[0]}."
    elif warnings:
        b4 = f"• Compliance status: {compliance}. Note: {warnings[0]}."
    else:
        b4 = f"• Compliance status is {compliance} — no major regulatory issues detected."

    if "APPROVED" in decision:
        b5 = "• Recommendation: Proceed with loan disbursement following standard documentation checks."
    elif "REJECT" in decision:
        b5 = "• Recommendation: Application declined. Applicant should address credit issues before reapplying."
    elif "CONDITION" in decision:
        b5 = "• Recommendation: Loan can proceed only after all listed conditions are met and verified."
    else:
        b5 = "• Recommendation: Route to senior underwriter for manual review and final decision."

    return "\\n".join([b1, b2, b3, b4, b5])

def _ai_summarise(memo: dict, reply_text: str) -> str:
    import google.api_core.exceptions as _gex

    model = _genai.GenerativeModel("gemini-2.0-flash")
    prompt = (
        "You are a financial analyst. Summarise the credit underwriting result "
        "in exactly 5 bullet points (≤25 words each), jargon-free, starting each with •.\\n\\n"
        f"Decision: {memo.get('decision','N/A')}  |  "
        f"Score: {memo.get('composite_score','N/A')}/100  |  "
        f"CIBIL: {memo.get('credit_score','N/A')}  |  "
        f"Risk: {memo.get('risk_level','N/A')}  |  "
        f"DTI: {memo.get('debt_to_income','N/A')}  |  "
        f"Defaults: {memo.get('defaults','N/A')}  |  "
        f"Compliance: {memo.get('compliance','N/A')}  |  "
        f"Violations: {', '.join(memo.get('violations',[])) or 'None'}  |  "
        f"Warnings: {', '.join(memo.get('warnings',[])) or 'None'}\\n\\n"
        f"Extra context:\\n{reply_text[:1500]}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except _gex.ResourceExhausted:
        return _local_summarise(memo) + "\\n\\n_⚡ Generated offline (Gemini quota exhausted — resets daily)_"
    except Exception:
        return _local_summarise(memo) + "\\n\\n_⚡ Generated offline (API unavailable)_"

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Credit Terminal", page_icon="🛡️", layout="wide")
apply_react_dark_theme()
render_top_header()

# SESSION STATE
for key, val in [
    ("c_sid",              str(uuid.uuid4())),
    ("credit_history",     []),
    ("c_memo",             None),
    ("c_memo_summary",     None),
    ("_credit_prefill",    ""),
]:
    if key not in st.session_state: st.session_state[key] = val

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
chat_col, memo_col = st.columns([55, 45], gap="large")

with chat_col:
    st.markdown("""
    <div style="margin-bottom:24px;">
      <h2 style="font-size:1.8rem; font-weight:900; color:var(--tx-white); letter-spacing:-.02em; margin:0;">Credit Intelligence Terminal</h2>
      <p style="font-size:0.9rem; color:var(--tx-muted); margin-top:4px;">Automated underwriting for existing ID verifications or new applicant evaluations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Old vs New User selection
    tab_old, tab_new = st.tabs(["🏛️ Evaluate Existing User", "📝 Evaluate New User"])
    
    # Context storage mapping
    applicant_ctx = ""
    run_analysis_flag = False
    
    with tab_old:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem; color:var(--tx-muted); margin-bottom:16px;'>Load applicant via their internal ID and perform deep data-layer aggregation and underwriting logic.</p>", unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        with rc1:
            applicant_id_old = st.text_input("Applicant ID", value="A-984210", key="old_id")
            loan_amount_old  = st.text_input("Loan Amount (INR)", value="₹5,00,000", key="old_amt")
        with rc2:
            purpose_old = st.selectbox("Loan Purpose", ["Retail Expansion", "Home Purchase", "Working Capital", "Venture", "Other"], key="old_purp")
            industry_old = st.selectbox("Industry", ["Retail & E-Commerce", "Infrastructure", "Fintech Services", "Manufacturing"], key="old_ind")
            
        old_cmd = st.text_area("Analysis Query", value="Run full compliance and baseline risk analysis.", key="old_cmd", height=70)
        
        if st.button("▶ RUN EXISTING USER ANALYSIS", type="primary", use_container_width=True, key="run_old"):
            applicant_ctx = (f"[CTX: ID={applicant_id_old} | LOAN={loan_amount_old} | "
                             f"PURPOSE={purpose_old} | INDUSTRY={industry_old}]")
            st.session_state._credit_prefill = old_cmd
            run_analysis_flag = True

    with tab_new:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem; color:var(--tx-muted); margin-bottom:16px;'>Evaluate a retail applicant not in the DB by manually supplying their raw metrics for instant analysis.</p>", unsafe_allow_html=True)
        nc1, nc2 = st.columns(2)
        with nc1:
            annual_inc = st.number_input("Annual Income (INR)", min_value=100000, value=800000, step=50000)
            req_loan   = st.number_input("Requested Loan (INR)", min_value=10000, value=250000, step=10000)
            cibil_est  = st.number_input("Estimated CIBIL Score", min_value=300, max_value=900, value=710)
        with nc2:
            current_debt = st.number_input("Current Outstanding Debt (INR)", min_value=0, value=150000, step=10000)
            age = st.number_input("Applicant Age", min_value=18, max_value=85, value=34)
            defaults = st.selectbox("Prior Defaults (5 Yrs)", [0, 1, 2, "3+"])
            
        new_cmd = st.text_area("Analysis Context / Notes", value="Please evaluate risk factoring in recent debt.", key="new_cmd", height=70)

        if st.button("▶ RUN NEW USER ANALYSIS", type="primary", use_container_width=True, key="run_new"):
            st.session_state._credit_prefill = new_cmd
            # Since no ID exists, we mock an ID or mark it new.
            generated_id = f"NEW-{str(uuid.uuid4())[:6].upper()}"
            applicant_ctx = (f"[NEW APPLICANT DATA | ID={generated_id}]\n"
                             f"- Annual Income: ₹{annual_inc:,.2f}\n"
                             f"- Requested Loan: ₹{req_loan:,.2f}\n"
                             f"- Current Debt: ₹{current_debt:,.2f}\n"
                             f"- Est. CIBIL: {cibil_est}\n"
                             f"- Age: {age}\n"
                             f"- Past Defaults: {defaults}\n"
                             f"Instructions: You must generate a full credit memo decision based almost entirely on these raw metrics because there is no DB history.")
            run_analysis_flag = True

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Agent Execution Engine
    if run_analysis_flag:
        user_input = st.session_state._credit_prefill
        full_msg = f"{applicant_ctx}\\n\\n{user_input}"
        
        st.session_state.credit_history.append({"role":"user", "content": f"**Analysis Request:** {user_input}"})
        
        with st.spinner("Processing analysis through ARIA Engine..."):
            result = asyncio.run(run_agent(
                session_id=st.session_state.c_sid,
                user_message=full_msg,
                max_iterations=6,
            ))
        
        st.session_state.credit_history.append({
            "role":"assistant",
            "content":    result["reply"],
            "tools_used": result["tools_used"],
            "thoughts":   result["thoughts"],
        })
        if result.get("credit_memo"):
            st.session_state.c_memo = result["credit_memo"]
            st.session_state.c_memo_summary = None  # Reset summary
        
        # We don't need a hard rerun since streamlit executes linearly and updating session_state reflects immediately.
        # But a st.rerun() ensures clean state.
        st.rerun()

    # Chat History rendering
    if st.session_state.credit_history:
        st.markdown("<div style='border-top:1px solid rgba(30,41,59,0.6); margin:32px 0; padding-top:24px;'><p style='font-size:0.65rem; font-weight:800; color:var(--tx-muted); text-transform:uppercase; letter-spacing:.1em;'>ARIA Dialogue Log</p></div>", unsafe_allow_html=True)
        
        for msg in reversed(st.session_state.credit_history):
            tools_used = msg.get("tools_used", [])
            thoughts   = msg.get("thoughts",   [])
            
            if msg["role"] == "user":
                st.markdown(f"""<div class="react-bubble-user">{msg['content']}</div>""", unsafe_allow_html=True)
            else:
                pills = "".join(f'<span class="react-tool-pill">{t}</span>' for t in tools_used)
                hdr = f"""<div style="display:flex; align-items:center; gap:12px; margin-bottom:12px; padding-bottom:10px; border-bottom:1px solid rgba(30,41,59,0.6); overflow-x:auto;">
                  <span style="font-size:0.55rem; font-weight:900; color:var(--tx-muted); font-family:'JetBrains Mono',monospace; text-transform:uppercase; letter-spacing:.1em; white-space:nowrap;">ARIA Engine</span>
                  <div style="display:flex; gap:6px;">{pills}</div>
                </div>""" if tools_used else ""
                
                st.markdown(f"""<div class="react-bubble-agent">{hdr}{msg['content']}</div>""", unsafe_allow_html=True)
                
            if "thoughts" in msg and thoughts:
                with st.expander(f"Logic Audit ({len(thoughts)} Steps)"):
                    for i, t in enumerate(thoughts, 1):
                        st.markdown(f"""<div style="font-size:0.75rem; color:var(--tx-muted); display:flex; gap:8px; margin-bottom:6px;"><span style="color:var(--blue); font-weight:700;">[{i}]</span> {t}</div>""", unsafe_allow_html=True)

    if st.button("🗑️ CLEAR SESSION LOG", use_container_width=True):
        st.session_state.credit_history = []
        st.session_state.c_memo = None
        st.session_state.c_memo_summary = None
        st.rerun()

# ── MEMO PANEL ─────────────────────────────────────────────────────────────
with memo_col:
    memo = st.session_state.c_memo
    ref_id = memo.get("applicant_id", "A-XXXXXX") if memo else "A-XXXXXX"
    
    st.markdown(f"""
    <div style="background:var(--bg-sidebar); border:1px solid var(--border); border-bottom:none; border-radius:16px 16px 0 0; padding:16px 24px; display:flex; justify-content:space-between; align-items:center;">
      <span style="font-size:0.65rem; font-weight:800; color:var(--tx-muted); text-transform:uppercase; letter-spacing:.1em; display:flex; align-items:center; gap:8px;">
        📄 Credit Memo Review
      </span>
      <span style="font-size:0.65rem; font-family:'JetBrains Mono',monospace; color:var(--tx-muted);">REF: {ref_id}</span>
    </div>
    """, unsafe_allow_html=True)

    html_out = """<div style="background:var(--bg-sidebar); border:1px solid var(--border); border-top:none; border-radius:0 0 16px 16px; padding:32px 24px; min-height:600px;">"""
    
    if not memo:
        html_out += """
        <div style="padding:40px 24px; text-align:center;">
          <p style="color:var(--tx-muted); font-size:0.85rem;">Run an analysis query to generate the official credit memo based on Applicant ID details or manual inputs.</p>
        </div>"""
    else:
        decision = memo.get("decision", "APPROVED")
        t_class, hex_col, bg_border = _decision_styles(decision)
        if "rose" in t_class: bg_col, border_col = "rgba(244,63,94,0.1)", "rgba(244,63,94,0.2)"
        elif "amber" in t_class: bg_col, border_col = "rgba(245,158,11,0.1)", "rgba(245,158,11,0.2)"
        elif "violet" in t_class: bg_col, border_col = "rgba(139,92,246,0.1)", "rgba(139,92,246,0.2)"
        else: bg_col, border_col = "rgba(16,185,129,0.1)", "rgba(16,185,129,0.2)"
        
        html_out += f"""
<div style="padding:24px; border-radius:12px; margin-bottom:32px; background:{bg_col}; border:1px solid {border_col}; box-shadow:inset 0 2px 4px rgba(0,0,0,0.15);">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div>
      <p style="font-size:0.65rem; font-weight:800; text-transform:uppercase; letter-spacing:-.02em; opacity:0.8; margin:0 0 4px 0; color:{hex_col};">Underwriter Verdict</p>
      <h3 style="font-size:1.8rem; font-weight:900; letter-spacing:-.05em; font-style:italic; margin:0; color:{hex_col};">{decision}</h3>
    </div>
    <div style="text-align:right;">
      <p style="font-size:2.4rem; font-weight:900; color:var(--tx-white); line-height:1; letter-spacing:-.05em; margin:0;">{memo.get("composite_score", 0)}<span style="font-size:1rem; opacity:0.3;">/100</span></p>
      <p style="font-size:0.65rem; font-weight:800; text-transform:uppercase; opacity:0.5; margin:4px 0 0 0; color:var(--tx-white);">Composite Alpha</p>
    </div>
  </div>
</div>
"""
        html_out += f"""
<div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:32px;">
  <div style="background:var(--bg-panel); border:1px solid var(--border); padding:16px; border-radius:12px;">
    <div style="display:flex; justify-content:space-between; color:var(--tx-muted); margin-bottom:8px;">
      <span style="font-size:0.55rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em;">Credit Score</span>
      <span>🏛️</span>
    </div>
    <div style="font-size:1.4rem; font-weight:900; color:var(--tx-white); letter-spacing:-.05em;">{memo.get("credit_score","—")}</div>
    <div style="font-size:0.55rem; font-weight:600; color:var(--tx-muted);">CIBIL Transunion</div>
  </div>
  <div style="background:var(--bg-panel); border:1px solid var(--border); padding:16px; border-radius:12px;">
    <div style="display:flex; justify-content:space-between; color:var(--tx-muted); margin-bottom:8px;">
      <span style="font-size:0.55rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em;">Market Context</span>
      <span>🌐</span>
    </div>
    <div style="font-size:1.4rem; font-weight:900; color:var(--emerald); letter-spacing:-.05em;">{memo.get("market_risk","—")}</div>
    <div style="font-size:0.55rem; font-weight:600; color:var(--tx-muted);">Sector Trend</div>
  </div>
  <div style="background:var(--bg-panel); border:1px solid var(--border); padding:16px; border-radius:12px;">
    <div style="display:flex; justify-content:space-between; color:var(--tx-muted); margin-bottom:8px;">
      <span style="font-size:0.55rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em;">Debt/Income</span>
      <span>💼</span>
    </div>
    <div style="font-size:1.4rem; font-weight:900; color:var(--tx-white); letter-spacing:-.05em;">{memo.get("debt_to_income","—")}</div>
    <div style="font-size:0.55rem; font-weight:600; color:var(--tx-muted);">Leverage</div>
  </div>
  <div style="background:var(--bg-panel); border:1px solid var(--border); padding:16px; border-radius:12px;">
    <div style="display:flex; justify-content:space-between; color:var(--tx-muted); margin-bottom:8px;">
      <span style="font-size:0.55rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em;">Risk Level</span>
      <span>🛡️</span>
    </div>
    <div style="font-size:1.4rem; font-weight:900; color:#60A5FA; letter-spacing:-.05em;">{memo.get("risk_level","—")}</div>
    <div style="font-size:0.55rem; font-weight:600; color:var(--tx-muted);">Tier Rating</div>
  </div>
</div>

<div style="margin-bottom:32px;">
  <h4 style="font-size:0.65rem; font-weight:800; color:var(--tx-muted); text-transform:uppercase; letter-spacing:.1em; margin-bottom:16px;">Risk Factor Breakdown</h4>
  <div style="background:var(--bg-panel); border:1px solid var(--border); border-radius:12px; padding:20px;">
"""

        for key, val in memo.get("sub_scores", {}).items():
            v = int(float(str(val).replace("N/A","0"))) if val else 0
            html_out += f"""
<div style="margin-bottom:16px;">
  <div style="display:flex; justify-content:space-between; font-size:0.65rem; font-weight:600; margin-bottom:6px;">
    <span style="color:var(--tx-muted);">{key.replace('_',' ').title()}</span>
    <span style="color:var(--tx-white);">{v}%</span>
  </div>
  <div style="height:4px; background:rgba(30,41,59,1); border-radius:2px; overflow:hidden;">
    <div style="height:100%; width:{v}%; background:rgba(59,130,246,0.8); border-radius:2px;"></div>
  </div>
</div>
"""
        
        html_out += """
  </div>
</div>

<div style="margin-bottom:32px;">
  <h4 style="font-size:0.65rem; font-weight:800; color:var(--tx-muted); text-transform:uppercase; letter-spacing:.1em; margin-bottom:12px;">Executive Summary</h4>
  <div style="padding:20px; background:rgba(59,130,246,0.05); border:1px solid rgba(59,130,246,0.1); border-radius:12px; font-style:italic; color:var(--tx-muted); font-size:0.85rem; line-height:1.6;">
    "{rat}"
  </div>
</div>
""".replace("{rat}", re.sub(r'#+ \*+', '', memo.get("rationale","No rationale provided.")))

        html_out += "</div>"
        st.markdown(html_out, unsafe_allow_html=True)

        warnings = memo.get("warnings", []) + memo.get("violations", [])
        if warnings:
            st.markdown(f"""
<div style="padding:16px; background:rgba(245,158,11,0.05); border:1px solid rgba(245,158,11,0.2); border-radius:12px; display:flex; gap:12px; margin-bottom:32px;">
  <span style="font-size:1.2rem;">⚠️</span>
  <div>
    <p style="font-size:0.65rem; font-weight:800; color:var(--amber); text-transform:uppercase; margin:0 0 4px 0;">Underwriter Flag</p>
    <p style="font-size:0.75rem; color:rgba(245,158,11,0.8); margin:0; line-height:1.4;">{warnings[0]}</p>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:var(--border); margin:32px 0;'>", unsafe_allow_html=True)
        
        # Summarizer logic from user requirements
        if st.button("✨ GENERATE PLAIN-ENGLISH SUMMARY", use_container_width=True):
            last_reply = ""
            for m in reversed(st.session_state.credit_history):
                if m["role"] == "assistant":
                    last_reply = m["content"]; break
            with st.spinner("Compiling summary..."):
                st.session_state.c_memo_summary = _ai_summarise(memo, last_reply)

        if st.session_state.get("c_memo_summary"):
            st.markdown(f"""
<div style="margin-top:20px; padding:20px; background:var(--bg-input); border:1px dashed var(--blue); border-radius:12px;">
  <h5 style="color:var(--blue); font-size:0.7rem; text-transform:uppercase; letter-spacing:.1em; margin-bottom:10px;">Executive Brief</h5>
  <div style="font-size:0.85rem; color:var(--tx-main); line-height:1.6;">
    {st.session_state.c_memo_summary.replace('•', '<br>•')}
  </div>
</div>
""", unsafe_allow_html=True)

        try:
            pdf_bytes = generate_pdf(memo)
            st.download_button(
                "📥 DOWNLOAD OFFICIAL MEMO", data=pdf_bytes,
                file_name=f"neostats_{ref_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf", use_container_width=True,
            )
        except Exception as e:
            st.warning(f"PDF builder err: {e}")
            
    st.markdown("</div>", unsafe_allow_html=True)
