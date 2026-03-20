import re

with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. FIX CREDIT CARD Auto-run
old_credit_card = '''                    if st.button(f"▶  Try this", key=f"card_btn_{idx}",
                                 use_container_width=True):
                        # Construct prompt using sidebar values dynamically
                        generated_prompt = card["prompt_template"].format(
                            id=applicant_id, 
                            amt=loan_amount, 
                            purp=loan_purpose, 
                            ind=industry
                        )
                        st.session_state._credit_prefill = generated_prompt
                        st.rerun()'''
new_credit_card = '''                    if st.button(f"▶  Try this", key=f"card_btn_{idx}",
                                 use_container_width=True):
                        generated_prompt = card["prompt_template"].format(
                            id=applicant_id, 
                            amt=loan_amount, 
                            purp=loan_purpose, 
                            ind=industry
                        )
                        st.session_state._auto_submit_credit = generated_prompt
                        st.rerun()'''

text = text.replace(old_credit_card, new_credit_card)

# 2. FIX CREDIT FORM Logic
old_credit_form = '''        if send and user_input.strip():
            st.session_state._credit_prefill = ""
            ctx = (f"[CTX: ID={applicant_id} | LOAN=₹{loan_amount:,} | "
                   f"PURPOSE={loan_purpose} | INDUSTRY={industry}]")
            full_msg = f"{ctx}\\n\\n{user_input.strip()}"
            st.session_state.credit_history.append({"role":"user","content":user_input.strip()})'''
new_credit_form = '''        should_run_credit = (send and user_input.strip()) or st.session_state.get("_auto_submit_credit")
        if should_run_credit:
            actual_prompt = st.session_state.pop("_auto_submit_credit", user_input.strip())
            st.session_state._credit_prefill = ""
            ctx = (f"[CTX: ID={applicant_id} | LOAN=₹{loan_amount:,} | "
                   f"PURPOSE={loan_purpose} | INDUSTRY={industry}]")
            full_msg = f"{ctx}\\n\\n{actual_prompt}"
            st.session_state.credit_history.append({"role":"user","content":actual_prompt})'''

text = text.replace(old_credit_form, new_credit_form)

# 3. FIX GENERAL CARD Auto-run
old_gen_card = '''                if st.button(f"▶  Ask this", key=f"gen_btn_{idx}", use_container_width=True):
                    st.session_state._general_prefill = prompt
                    st.rerun()'''
new_gen_card = '''                if st.button(f"▶  Ask this", key=f"gen_btn_{idx}", use_container_width=True):
                    st.session_state._auto_submit_general = prompt
                    st.rerun()'''

text = text.replace(old_gen_card, new_gen_card)

# 4. FIX GENERAL FORM Logic & Context Inject
old_gen_form = '''    if gen_send and gen_input.strip():
        st.session_state._general_prefill = ""
        st.session_state.general_history.append({"role":"user","content":gen_input.strip()})
        with st.spinner("🌐 Searching and reasoning…"):
            result = run_general_agent(
                session_id=st.session_state.sid,
                user_message=gen_input.strip(),
            )'''
new_gen_form = '''    gen_should_run = (gen_send and gen_input.strip()) or st.session_state.get("_auto_submit_general")
    if gen_should_run:
        actual_gen_prompt = st.session_state.pop("_auto_submit_general", gen_input.strip())
        st.session_state._general_prefill = ""
        st.session_state.general_history.append({"role":"user","content":actual_gen_prompt})
        
        ctx = (f"[Applicant Context: ID={applicant_id} | LOAN=₹{loan_amount:,} | "
               f"PURPOSE={loan_purpose} | INDUSTRY={industry}]\\n(Use this context if relevant.)\\n\\n")
        full_gen_msg = f"{ctx}{actual_gen_prompt}"
        
        with st.spinner("🌐 Searching and reasoning…"):
            result = run_general_agent(
                session_id=st.session_state.sid,
                user_message=full_gen_msg,
            )'''

text = text.replace(old_gen_form, new_gen_form)


# 5. ENHANCE CSS (Replace block from <style> to </style>)
# We will use regex to find the style block and replace it with a more vibrant version.
new_style = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

:root{
  --bg0:#0b0f19; --bg1:#111827; --bg2:#1f2937; --bg3:#374151;
  --border:#374151; --border2:#4b5563;
  --primary:#00d0ff; --primary-glow:rgba(0, 208, 255, 0.4);
  --secondary:#8b5cf6; --secondary-glow:rgba(139, 92, 246, 0.4);
  --success:#10b981; --danger:#ef4444; --warning:#f59e0b;
  --t0:#f9fafb; --t1:#d1d5db; --t2:#9ca3af;
}

html,body,[data-testid="stApp"]{
  background:var(--bg0)!important;
  color:var(--t0)!important;
  font-family:'Space Grotesk',sans-serif!important;
}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg0)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--primary)}

[data-testid="stSidebar"]{
  background:var(--bg1)!important;
  border-right:1px solid var(--border)!important;
  box-shadow: 4px 0 15px rgba(0,0,0,0.2);
}
[data-testid="stSidebar"] *{color:var(--t0)!important;font-family:'Space Grotesk',sans-serif!important}

/* ── Tab bar ─────────────────────────────────────────────────── */
[data-testid="stTabs"] > div:first-child{
  background:var(--bg1);
  border-bottom:1px solid var(--border);
  border-radius:12px 12px 0 0;
  padding:0 12px;
  gap:8px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
button[data-baseweb="tab"]{
  background:transparent!important;
  color:var(--t2)!important;
  font-family:'JetBrains Mono',monospace!important;
  font-size:0.85rem!important;
  font-weight:600!important;
  letter-spacing:0.05em!important;
  border:none!important;
  border-bottom:2px solid transparent!important;
  padding:16px 24px!important;
  transition:all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
}
button[data-baseweb="tab"]:hover{
  color:var(--t0)!important;
  background: rgba(255,255,255,0.03)!important;
}
button[data-baseweb="tab"][aria-selected="true"]{
  color:var(--primary)!important;
  border-bottom:2px solid var(--primary)!important;
  text-shadow: 0 0 10px var(--primary-glow);
}
[data-testid="stTabPanel"]{
  background:var(--bg0);
  border:1px solid var(--border);
  border-top:none;
  border-radius:0 0 12px 12px;
  padding:24px!important;
}

/* ── Inputs ──────────────────────────────────────────────────── */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>div{
  background:var(--bg2)!important;
  border:1px solid var(--border2)!important;
  color:var(--t0)!important;
  font-family:'JetBrains Mono',monospace!important;
  font-size:0.8rem!important;
  border-radius:6px!important;
  padding:10px 14px!important;
  transition:all 0.2s;
}
.stTextInput>div>div>input:focus,
.stNumberInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stSelectbox>div>div>div:focus{
  border-color:var(--primary)!important;
  box-shadow:0 0 0 1px var(--primary)!important;
  outline:none!important;
}
label{
  color:var(--t1)!important;
  font-weight:500!important;
  font-size:0.8rem!important;
  margin-bottom:4px!important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
button[kind="secondary"], button[kind="primary"]{
  background:linear-gradient(135deg, var(--bg2), var(--bg3))!important;
  border:1px solid var(--border2)!important;
  color:var(--t0)!important;
  font-family:'JetBrains Mono',monospace!important;
  font-size:0.75rem!important;
  font-weight:600!important;
  letter-spacing:0.05em!important;
  border-radius:6px!important;
  padding:6px 16px!important;
  transition:all 0.2s!important;
}
button[kind="secondary"]:hover, button[kind="primary"]:hover{
  border-color:var(--primary)!important;
  color:var(--primary)!important;
  box-shadow: 0 0 12px var(--primary-glow)!important;
  transform: translateY(-1px);
}
button[kind="primary"]{
  background:linear-gradient(135deg, rgba(0,208,255,0.1), rgba(139,92,246,0.1))!important;
  border-color:var(--secondary)!important;
  color:var(--t0)!important;
}
button[kind="primary"]:hover{
  border-color:var(--primary)!important;
  box-shadow: 0 0 15px var(--secondary-glow)!important;
}

/* ── Cards & Chat ────────────────────────────────────────────── */
.example-card{
  background:var(--bg1);
  border:1px solid var(--border);
  border-radius:10px;
  padding:16px;
  margin-bottom:6px;
  height:calc(100% - 6px);
  transition:all 0.3s;
  cursor:pointer;
  position: relative;
  overflow: hidden;
}
.example-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  opacity: 0.5;
}
.example-card:hover{
  border-color:var(--primary);
  background:var(--bg2);
  box-shadow:0 8px 24px rgba(0,0,0,0.3);
  transform: translateY(-2px);
}
.example-card:hover::before { opacity: 1; }
.card-icon{font-size:1.8rem;margin-bottom:8px;}
.card-title{font-size:0.95rem;font-weight:600;color:var(--t0);margin-bottom:6px;letter-spacing:0.02em}
.card-desc{font-size:0.75rem;color:var(--t2);line-height:1.5;margin-bottom:12px;}
.card-tag{
  background:rgba(0,208,255,0.1);
  border:1px solid rgba(0,208,255,0.3);
  color:var(--primary);
  font-family:'JetBrains Mono',monospace;
  font-size:0.6rem;
  padding:3px 8px;
  border-radius:12px;
  font-weight:600;
}

/* User vs Agent Bubbles */
.user-bubble{
  background:linear-gradient(135deg, var(--bg2), #2d3748);
  border:1px solid var(--border);
  border-left:3px solid var(--primary);
  border-radius:8px 8px 8px 0;
  padding:12px 16px;
  margin-bottom:18px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.agent-bubble{
  background:var(--bg1);
  border:1px solid var(--border);
  border-left:3px solid var(--success);
  margin-bottom:18px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.tool-pill{
  background:rgba(16,185,129,0.1);
  border:1px solid rgba(16,185,129,0.3);
  color:var(--success);
  font-family:'JetBrains Mono',monospace;
  font-size:0.65rem;
  padding:3px 8px;
  border-radius:12px;
  margin-left:6px;
}
.web-pill{
  background:rgba(144,96,255,0.1);
  border:1px solid rgba(144,96,255,0.3);
  color:var(--secondary);
  font-family:'JetBrains Mono',monospace;
  font-size:0.65rem;
  padding:3px 8px;
  border-radius:12px;
  margin-left:6px;
}

.sec-label{
  font-family:'JetBrains Mono',monospace;
  font-size:0.76rem;
  font-weight:600;
  letter-spacing:0.12em;
  color:var(--t0);
  margin-bottom:16px;
  display:flex;
  align-items:center;
  gap:8px;
  text-shadow: 0 0 10px rgba(255,255,255,0.1);
}
</style>'''

text = re.sub(r'<style>.*?</style>', new_style, text, flags=re.DOTALL)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Applied fixes to main.py")
