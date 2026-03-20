import os

with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

# We know the good text before this starts at "#  SIDEBAR  (shared)" right after the header block.
# Let's cleanly split on exactly what precedes the sidebar block and what follows the chat panel.
token_start = "# ══════════════════════════════════════════════════════════════════════════════\n#  SIDEBAR  (shared)"
token_end = "        # ── 4 Example Cards ───────────────────────────────────────────────\n        if not st.session_state.credit_history:"

# Find first occurrence of token_start
idx_start = text.find(token_start)
# Find last occurrence of token_end, because the file might have duplicates of the stuff in between, but token_end is unique (or we want the one at the bottom of the mess)
idx_end = text.find(token_end)

if idx_start == -1 or idx_end == -1:
    print("Could not find tokens!")
    print(idx_start, idx_end)
else:
    good_block = r'''# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR  (shared)
# ══════════════════════════════════════════════════════════════════════════════
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

            if thoughts:
                with st.expander(f"🧠  Thought Process  ({len(thoughts)} steps)"):
                    for n, t in enumerate(thoughts, 1):
                        icon  = "→" if "calling" in t.lower() or "search" in t.lower() else \
                                "←" if "returned" in t.lower() else \
                                "✓" if "done" in t.lower() or "final" in t.lower() else "·"
                        color = {"→":"#00c8f0","←":"#00e5a0","✓":"#ffb020"}.get(icon,"#4a6a84")
                        st.markdown(f"""
                        <div style="font-family:'JetBrains Mono',monospace;font-size:0.73rem;
                                    padding:4px 12px;margin:2px 0;
                                    border-left:2px solid {color}28;
                                    display:flex;gap:8px;color:#9ab8d0;">
                          <span style="color:{color};flex-shrink:0;">{icon}</span>{t}
                        </div>""", unsafe_allow_html=True)

\n'''

    new_text = text[:idx_start] + good_block + text[idx_end:]
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("Success: File patched!")
