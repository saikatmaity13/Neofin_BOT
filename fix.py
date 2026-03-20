import os
import re

with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

bad_chunk = r'''# ════════════════════    # ── CHAT PANEL ──────────────────────────────────────────────────
    with chat_col:
        for msg in st.session_state.credit_history:
            tools_used = msg.get("tools_used", [])
            thoughts   = msg.get("thoughts",   [])
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-bubble">
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;
                              color:#4a6a84;margin-bottom:6px;">YOU</div>
                  <div style="color:#e8f4ff;font-size:0.92rem;line-height:1.6;">{msg["content"]}</div>
                </div>""", unsafe_allow_html=True)
            else:
                pills = "".join(f'<span class="tool-pill">⚙ {t}</span>' for t in tools_used)
                st.markdown(f"""
                <div class="agent-bubble" style="padding:9px 16px 7px; border-radius: 0 8px 0 0; border-bottom: none;">
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:#4a6a84;">
                      ARIA · CREDIT UNDERWRITER
                    </span>
                    <div>{pills}</div>
                  </div>
                </div>
                <div class="agent-bubble" style="padding:4px 16px 14px; margin-bottom:4px; border-radius: 0 0 8px 0; border-top: none; margin-top: 0;">
                  {msg["content"]}
                </div>
                """, unsafe_allow_html=True)

            if thoughts:ht:1.9;">'''

good_chunk = r'''# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;
    color:#4a6a84;letter-spacing:0.1em;text-transform:uppercase;padding-bottom:12px;
    border-bottom:1px solid #142d4a;margin-bottom:16px;">◈ Applicant Config</div>""",
    unsafe_allow_html=True)

    applicant_id = st.text_input("Applicant ID", value="A001", help="Search among 34,000+ IDs")
    loan_amount  = st.number_input("Loan Amount (₹)", min_value=10_000,
                                    max_value=100_000_000, value=500_000,
                                    step=10_000, format="%d")
    loan_purpose = st.selectbox("Loan Purpose",
        ["Home Purchase","Business Expansion","Education","Vehicle","Medical","Personal","Venture","Other"])
    industry = st.text_input("Industry / Sector", value="Retail")

    st.markdown("""<div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;
    color:#4a6a84;letter-spacing:0.1em;text-transform:uppercase;padding:12px 0;
    border-top:1px solid #142d4a;border-bottom:1px solid #142d4a;
    margin:14px 0;">◈ Agent Settings</div>""", unsafe_allow_html=True)

    max_iter = st.slider("Max Iterations", 3, 10, 6)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Clear Credit", use_container_width=True):
        memory_manager.clear(st.session_state.sid)
        st.session_state.credit_history = []
        st.session_state.memo = None
        st.rerun()
    if c2.button("Clear Chat", use_container_width=True):
        memory_manager.clear(f"general_{st.session_state.sid}")
        st.session_state.general_history = []
        st.rerun()

    st.markdown(f"""
    <div style="margin-top:14px;padding:10px;background:#071220;border:1px solid #142d4a;
                border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:0.6rem;
                color:#4a6a84;line-height:1.9;">
      <span style="color:#1e3f60;">SESSION</span><br>
      {st.session_state.sid[:22]}…
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_credit, tab_general = st.tabs([
    "🏦  Credit Underwriter",
    "🌐  General Assistant",
])


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                       TAB 1 · CREDIT UNDERWRITER                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab_credit:

    chat_col, memo_col = st.columns([57, 43], gap="large")

    # ── CHAT PANEL ──────────────────────────────────────────────────
    with chat_col:
        for msg in st.session_state.credit_history:
            tools_used = msg.get("tools_used", [])
            thoughts   = msg.get("thoughts",   [])
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-bubble">
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;
                              color:#4a6a84;margin-bottom:6px;">YOU</div>
                  <div style="color:#e8f4ff;font-size:0.92rem;line-height:1.6;">{msg["content"]}</div>
                </div>""", unsafe_allow_html=True)
            else:
                pills = "".join(f'<span class="tool-pill">⚙ {t}</span>' for t in tools_used)
                st.markdown(f"""
                <div class="agent-bubble" style="padding:9px 16px 7px; border-radius: 0 8px 0 0; border-bottom: none;">
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:#4a6a84;">
                      ARIA · CREDIT UNDERWRITER
                    </span>
                    <div>{pills}</div>
                  </div>
                </div>
                <div class="agent-bubble" style="padding:4px 16px 14px; margin-bottom:4px; border-radius: 0 0 8px 0; border-top: none; margin-top: 0;">
                  {msg["content"]}
                </div>
                """, unsafe_allow_html=True)

            if thoughts:'''

if bad_chunk in text:
    text = text.replace(bad_chunk, good_chunk)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Success: Replaced chunk.")
else:
    print("Error: bad_chunk not found in file.")
