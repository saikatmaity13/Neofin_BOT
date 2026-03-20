import os
import uuid
import streamlit as st
from dotenv import load_dotenv

from app.llm.general_agent import run_general_agent
from app.ui_theme import apply_react_dark_theme, render_top_header

load_dotenv()

st.set_page_config(page_title="Global Market Insight", page_icon="🌐", layout="wide")
apply_react_dark_theme()
render_top_header()

# SESSION STATE
for key, val in [
    ("g_sid",              str(uuid.uuid4())),
    ("general_history",    []),
    ("_general_prefill",   ""),
]:
    if key not in st.session_state: st.session_state[key] = val

st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    
st.markdown("""
<div style="text-align:center; max-width:600px; margin:0 auto; margin-bottom:60px;">
  <div style="width:80px; height:80px; background:rgba(139,92,246,0.1); border:1px solid rgba(139,92,246,0.2); border-radius:24px; display:flex; align-items:center; justify-content:center; color:var(--violet); font-size:2.5rem; margin:0 auto 20px; box-shadow:0 0 30px rgba(139,92,246,0.1);">
    🌐
  </div>
  <h2 style="font-size:2.2rem; font-weight:900; color:var(--tx-white); letter-spacing:-.02em; margin-bottom:16px;">Global Market Intelligence</h2>
  <p style="font-size:1.1rem; color:var(--tx-muted);">Harness real-time data for market trends, RBI updates, and sector analysis.</p>
</div>
""", unsafe_allow_html=True)

g1, g2, g3 = st.columns([1, 8, 1])
with g2:
    # Quick prompts grid (2 cols)
    pc1, pc2 = st.columns(2)
    P1 = "What are the latest central bank interest rate revisions and their impact on retail loans?"
    P2 = "Calculate risk index for MSME retail clusters in India."
    P3 = "Verify KYC/AML compliance rules for non-resident retail clients."
    P4 = "Optimize loan book performance benchmarks for regional finance companies."
    
    def _render_gen_card(col, icon, title, desc, prompt, key):
        with col:
            st.markdown(f"""
            <div class="react-card" style="margin-bottom:16px;">
              <div style="font-size:1.8rem; margin-bottom:16px; opacity:0.8;">{icon}</div>
              <h3 style="font-size:1rem; font-weight:700; color:var(--tx-white); margin-bottom:8px;">{title}</h3>
              <p style="font-size:0.8rem; color:var(--tx-muted); line-height:1.6; margin-bottom:16px;">{desc}</p>
            </div>""", unsafe_allow_html=True)
            if st.button("EXECUTE QUERY ▸", key=key, use_container_width=True):
                st.session_state._auto_submit_general = prompt
                st.rerun()

    _render_gen_card(pc1, "📰", "Policy Updates", "Analyze latest central bank interest rate revisions.", P1, "g_btn1")
    _render_gen_card(pc2, "📉", "Sector Volatility", "Calculate risk index for MSME retail clusters.", P2, "g_btn2")
    _render_gen_card(pc1, "🏛️", "Regulatory Check", "Verify KYC/AML compliance for specific regions.", P3, "g_btn3")
    _render_gen_card(pc2, "💡", "Yield Strategies", "Optimize loan book performance benchmarks.", P4, "g_btn4")

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    for msg in st.session_state.general_history:
        if msg["role"] == "user":
            st.markdown(f"""<div class="react-bubble-user">{msg["content"]}</div>""", unsafe_allow_html=True)
        else:
            tools_used = msg.get("tools_used", [])
            thoughts = msg.get("thoughts", [])
            pills = "".join(f'<span class="react-tool-pill" style="color:var(--violet); border-color:rgba(139,92,246,.3); background:rgba(139,92,246,.15);">{t}</span>' for t in tools_used)
            st.markdown(f"""
            <div class="react-bubble-agent">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; padding-bottom:10px; border-bottom:1px solid rgba(30,41,59,0.6);">
                <span style="font-size:0.55rem; font-weight:900; color:var(--violet); text-transform:uppercase; letter-spacing:.1em;">ARIA · Market Assistant</span>
                <div style="display:flex; gap:6px;">{pills}</div>
              </div>
              {msg["content"]}
            </div>""", unsafe_allow_html=True)
            
            if thoughts:
                with st.expander(f"Search Steps ({len(thoughts)} steps)"):
                    for i, t in enumerate(thoughts, 1):
                        st.markdown(f"""
                        <div style="font-size:0.75rem; color:var(--tx-muted); display:flex; gap:8px; margin-bottom:6px;">
                          <span style="color:var(--violet); font-weight:700;">[{i}]</span> {t}
                        </div>""", unsafe_allow_html=True)

    with st.form("gen_form", clear_on_submit=True):
        cols = st.columns([85, 15])
        with cols[0]:
            g_input = st.text_input("Cmd", value=st.session_state._general_prefill, placeholder="Ask about markets, regulations, or concepts...", label_visibility="collapsed")
        with cols[1]:
            g_send = st.form_submit_button("SEND", use_container_width=True, type="primary")

    should_gen = (g_send and g_input.strip()) or st.session_state.get("_auto_submit_general")
    if should_gen:
        actual = st.session_state.pop("_auto_submit_general", g_input.strip())
        st.session_state._general_prefill = ""
        st.session_state.general_history.append({"role":"user", "content":actual})
        
        # We drop the direct Applicant Context from here since this is a global market tab now.
        ctx = "[CTX: GLOBAL MACRO Market Analysis]\n"
        
        with st.spinner("Accessing global web index..."):
            res = run_general_agent(st.session_state.g_sid, f"{ctx}{actual}")
        
        st.session_state.general_history.append({
            "role": "assistant", "content": res["reply"], "tools_used": res["tools_used"], "thoughts": res["thoughts"]
        })
        st.rerun()

    if st.button("🗑️ CLEAR SESSION LOG", use_container_width=False):
        st.session_state.general_history = []
        st.rerun()
