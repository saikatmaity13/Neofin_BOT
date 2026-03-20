import re

with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

new_style = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

:root{
  /* Ultra-Premium Linear/Vercel-like Dark Mode */
  --bg0: #040609; 
  --bg1: #0A0F16; 
  --bg2: #101621; 
  --bg3: #1B2333;
  --border: #1E2532; 
  --border2: #2B3545;
  --border-focus: #4F6182;
  
  --primary: #2962FF; /* Crisp electric blue */
  --primary-hover: #154EE0;
  --primary-glow: rgba(41, 98, 255, 0.25);
  --primary-light: rgba(41, 98, 255, 0.1);
  
  --secondary: #A067FE; /* Premium violet accent */
  --success: #00E676; 
  --success-glow: rgba(0, 230, 118, 0.15);
  
  --t0: #FFFFFF; /* Pure white headers/highlights */
  --t1: #D1D6E0; /* Primary reading text */
  --t2: #8F9BAD; /* Captions/labels */
}

/* ── Base ────────────────────────────────────────────────────── */
html, body, [data-testid="stApp"] {
  background: var(--bg0)!important;
  color: var(--t1)!important;
  font-family: 'Inter', sans-serif!important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-focus); }

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--bg1)!important;
  border-right: 1px solid var(--border)!important;
}
[data-testid="stSidebar"] * {
  color: var(--t1)!important; 
  font-family: 'Inter', sans-serif!important;
}

/* ── Tabs ────────────────────────────────────────────────────── */
[data-testid="stTabs"] > div:first-child {
  background: var(--bg1);
  border-bottom: 1px solid var(--border);
  border-radius: 12px 12px 0 0;
  padding: 0 8px;
  gap: 8px;
}
button[data-baseweb="tab"] {
  background: transparent!important;
  color: var(--t2)!important;
  font-family: 'JetBrains Mono', monospace!important;
  font-size: 0.82rem!important;
  font-weight: 500!important;
  letter-spacing: 0.03em!important;
  border: none!important;
  border-bottom: 2px solid transparent!important;
  padding: 16px 20px!important;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1)!important;
}
button[data-baseweb="tab"]:hover {
  color: var(--t0)!important;
  background: rgba(255,255,255,0.02)!important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--primary)!important;
  border-bottom: 2px solid var(--primary)!important;
  background: linear-gradient(180deg, rgba(41,98,255,0) 0%, rgba(41,98,255,0.05) 100%)!important;
}
[data-testid="stTabPanel"] {
  background: var(--bg0);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 12px 12px;
  padding: 24px!important;
}

/* ── Form Inputs ─────────────────────────────────────────────── */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>div {
  background: var(--bg2)!important;
  border: 1px solid var(--border)!important;
  color: var(--t0)!important;
  font-family: 'JetBrains Mono', monospace!important;
  font-size: 0.85rem!important;
  border-radius: 8px!important;
  padding: 12px 14px!important;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1)!important;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}
.stTextInput>div>div>input:focus,
.stNumberInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stSelectbox>div>div>div:focus {
  background: var(--bg1)!important;
  border-color: var(--primary)!important;
  box-shadow: 0 0 0 4px var(--primary-light), inset 0 1px 3px rgba(0,0,0,0.1)!important;
  outline: none!important;
}
label {
  color: var(--t2)!important;
  font-weight: 500!important;
  font-size: 0.82rem!important;
  margin-bottom: 6px!important;
  letter-spacing: 0.01em!important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
button[kind="secondary"], button[kind="primary"] {
  background: var(--bg2)!important;
  border: 1px solid var(--border2)!important;
  color: var(--t1)!important;
  font-family: 'Inter', sans-serif!important;
  font-size: 0.8rem!important;
  font-weight: 600!important;
  letter-spacing: 0.02em!important;
  border-radius: 8px!important;
  padding: 8px 18px!important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1)!important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
button[kind="secondary"]:hover, button[kind="primary"]:hover {
  background: var(--bg3)!important;
  border-color: var(--border-focus)!important;
  color: var(--t0)!important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
button[kind="primary"] {
  background: linear-gradient(180deg, var(--primary), var(--primary-hover))!important;
  border: 1px solid var(--primary)!important;
  color: #ffffff!important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.2)!important;
}
button[kind="primary"]:hover {
  background: var(--primary-hover)!important;
  box-shadow: 0 4px 14px var(--primary-glow)!important;
  border-color: var(--primary)!important;
}

/* ── Interactive Cards ───────────────────────────────────────── */
.example-card {
  background: var(--bg1);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 8px;
  height: calc(100% - 8px);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.example-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, rgba(255,255,255,0.05), rgba(255,255,255,0.1), rgba(255,255,255,0.05));
  opacity: 1;
}
.example-card:hover {
  background: var(--bg2);
  border-color: var(--border-focus);
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  transform: translateY(-2px);
}
.card-icon { font-size: 1.8rem; margin-bottom: 12px; opacity: 0.9; }
.card-title { font-size: 1rem; font-weight: 600; color: var(--t0); margin-bottom: 8px; }
.card-desc { font-size: 0.82rem; color: var(--t1); line-height: 1.6; margin-bottom: 16px; font-weight: 400; }
.card-tag {
  background: var(--bg3);
  border: 1px solid var(--border2);
  color: var(--t1);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
  letter-spacing: 0.05em;
}

/* ── Chat Bubbles ────────────────────────────────────────────── */
.user-bubble {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--primary);
  border-radius: 10px 10px 10px 0;
  padding: 16px 20px;
  margin-bottom: 24px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}
.agent-bubble {
  background: var(--bg1);
  border: 1px solid var(--border);
  border-left: 3px solid var(--success);
  margin-bottom: 24px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  border-radius: 10px 10px 0 10px;
}

/* ── Tool Pills ──────────────────────────────────────────────── */
.tool-pill {
  background: var(--success-glow);
  border: 1px solid rgba(0,230,118,0.25);
  color: var(--success);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 4px 10px;
  border-radius: 20px;
  margin-left: 8px;
  font-weight: 500;
}
.web-pill {
  background: rgba(160, 103, 254, 0.1);
  border: 1px solid rgba(160, 103, 254, 0.25);
  color: var(--secondary);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 4px 10px;
  border-radius: 20px;
  margin-left: 8px;
  font-weight: 500;
}

/* ── Section Labels ──────────────────────────────────────────── */
.sec-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--t1);
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}
</style>'''

text = re.sub(r'<style>.*?</style>', new_style, text, flags=re.DOTALL)

# Also let's clean up all those inline color values to match the sophisticated palette
# We'll use our root CSS variables where possible, or replace garish colors with refined ones.
text = text.replace('border-bottom:1px solid #142d4a', 'border-bottom:1px solid #1E2532')
text = text.replace('border-top:1px solid #142d4a', 'border-top:1px solid #1E2532')
text = text.replace('background:#071220;border:1px solid #142d4a', 'background:#0A0F16;border:1px solid #1E2532')
text = text.replace('border:1px dashed #142d4a', 'border:1px dashed #2B3545')
text = text.replace('background:#0a1520', 'background:#101621')
text = text.replace('background:#0b1c30', 'background:#101621')

text = text.replace('color:#00e5a0;', 'color:#00E676;')
text = text.replace('color:#9060ff;', 'color:#A067FE;')
text = text.replace('color:#4a6a84', 'color:#8F9BAD')
text = text.replace('color:#e8f4ff', 'color:#FFFFFF')

# Adjust the UI agent formatting
text = text.replace('border-left:3px solid #9060ff', 'border-left:3px solid #A067FE')
text = text.replace('border-left:2px solid #9060ff28', 'border-left:2px solid rgba(160,103,254,0.15)')

# Specific color corrections in thought expander
text = text.replace('"#00c8f0"', '"#2962FF"')
text = text.replace('"#00e5a0"', '"#00E676"')
text = text.replace('"#ffb020"', '"#F59E0B"')
text = text.replace('"#4a6a84"', '"#8F9BAD"')
text = text.replace('color:#9ab8d0', 'color:#D1D6E0')

with open("main.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Applied professional CSS fixes to main.py")
