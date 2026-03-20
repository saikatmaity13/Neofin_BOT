import streamlit as st
import re
from fpdf import FPDF

def apply_react_dark_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

    :root {
      --bg-app:     #020408;
      --bg-sidebar: #06080E;
      --bg-panel:   #0A0C12;
      --bg-input:   #0F1117;
      --border:     rgba(30, 41, 59, 0.6);   /* slate-800/60 */
      --border-sub: rgba(30, 41, 59, 0.3);
      
      --tx-main:    #CBD5E1; /* slate-300 */
      --tx-muted:   #64748B; /* slate-500 */
      --tx-white:   #FFFFFF;
      
      --blue:       #3B82F6; /* blue-500 */
      --blue-hover: #2563EB; /* blue-600 */
      --blue-dim:   rgba(59, 130, 246, 0.1);
      --emerald:    #10B981;
      --amber:      #F59E0B;
      --rose:       #F43F5E;
      --violet:     #8B5CF6;
      
      --r-sm: 8px; --r-md: 12px; --r-lg: 16px;
    }

    /* ── Base ── */
    html, body, [data-testid="stApp"] {
      background: var(--bg-app) !important;
      color: var(--tx-main) !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 14px;
    }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

    /* ── Hide Chrome ── */
    [data-testid="stDecoration"], [data-testid="stHeader"], footer { display: none !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
      background: var(--bg-sidebar) !important;
      border-right: 1px solid var(--border) !important;
      padding-top: 24px;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 1rem; }

    /* ── Tabs ── */
    [data-testid="stTabs"] > div:first-child {
      background: rgba(6, 8, 14, 0.8);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 0 32px;
    }
    button[data-baseweb="tab"] {
      background: transparent !important;
      color: var(--tx-muted) !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 700 !important;
      font-size: 0.85rem !important;
      border: none !important;
      border-bottom: 2px solid transparent !important;
      padding: 20px 16px !important;
      transition: color .2s !important;
    }
    button[data-baseweb="tab"]:hover { color: var(--tx-white) !important; }
    button[data-baseweb="tab"][aria-selected="true"] {
      color: var(--blue) !important;
      border-bottom-color: var(--blue) !important;
    }
    [data-testid="stTabPanel"] { background: var(--bg-app); padding: 0 !important; }

    /* ── Inputs ── */
    .stTextInput>div>div>input, .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
      background: var(--bg-input) !important;
      border: 1px solid var(--border) !important;
      color: var(--tx-main) !important;
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 0.85rem !important;
      border-radius: var(--r-sm) !important;
      padding: 10px 14px !important;
      transition: border .2s !important;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
      border-color: var(--blue) !important;
      box-shadow: 0 0 0 1px var(--blue) !important;
    }
    label, .stSelectbox label {
      color: var(--tx-muted) !important;
      font-size: 0.65rem !important;
      font-weight: 800 !important;
      text-transform: uppercase !important;
      letter-spacing: .05em !important;
    }

    /* ── Buttons ── */
    button[kind="primary"] {
      background: var(--blue-hover) !important;
      border: none !important;
      color: var(--tx-white) !important;
      font-weight: 600 !important;
      border-radius: var(--r-sm) !important;
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.2) !important;
      padding: 15px !important;
    }
    button[kind="primary"]:hover { background: var(--blue) !important; }

    button[kind="secondary"] {
      background: #0F1117 !important;
      border: 1px solid var(--border) !important;
      color: var(--tx-muted) !important;
      font-size: 0.65rem !important;
      font-weight: 800 !important;
      border-radius: var(--r-sm) !important;
      transition: all .2s !important;
    }
    button[kind="secondary"]:hover { background: #1E293B !important; color: var(--tx-main) !important; }

    /* ── Custom HTML Components ── */
    .react-card {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: var(--r-md);
      padding: 24px;
      cursor: pointer;
      transition: all .2s;
    }
    .react-card:hover { border-color: var(--tx-muted); transform: translateY(-2px); }

    .react-bubble-user {
      background: var(--blue-hover);
      color: var(--tx-white);
      padding: 20px;
      border-radius: var(--r-lg);
      margin-bottom: 20px;
      max-width: 85%;
      margin-left: auto;
      box-shadow: 0 10px 25px rgba(37,99,235,.15);
      font-size: 0.9rem;
      line-height: 1.6;
    }
    .react-bubble-agent {
      background: var(--bg-input);
      border: 1px solid var(--border);
      color: var(--tx-main);
      padding: 20px;
      border-radius: var(--r-lg);
      margin-bottom: 20px;
      max-width: 85%;
      font-size: 0.9rem;
      line-height: 1.6;
    }
    .react-tool-pill {
      background: rgba(59,130,246,.1);
      border: 1px solid rgba(59,130,246,.2);
      color: var(--blue);
      font-size: 0.55rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }

    [data-testid="stExpander"] { background: transparent !important; border: none !important; }
    [data-testid="stExpander"] summary { color: var(--tx-white) !important; font-size: 0.65rem !important; font-weight: 800 !important; text-transform: uppercase !important; letter-spacing: .1em !important; }

    /* Full white-text overrides for dark theme readability */
    p, span, div, li, td, th, .stMarkdown p { color: var(--tx-white) !important; }
    .stRadio label, .stCheckbox label { color: var(--tx-white) !important; font-size: 0.85rem !important; }
    .stNumberInput label, .stSlider label, .stFileUploader label { color: var(--tx-white) !important; font-size: 0.85rem !important; }
    .stMetric label, .stMetric [data-testid="stMetricValue"] { color: var(--tx-white) !important; }
    [data-testid="stTab"] p, [data-testid="stTabContent"] p { color: var(--tx-main) !important; }
    .stAlert p, .stAlert div { color: #1a1a1a !important; } /* keep alerts readable */
    </style>
    """, unsafe_allow_html=True)


def _decision_styles(decision: str):
    d = decision.upper()
    if   "REJECT"    in d: return "text-rose-500", "#F43F5E", "bg-[rgba(244,63,94,0.1)] border-[rgba(244,63,94,0.2)]"
    elif "CONDITION" in d: return "text-amber-500", "#F59E0B", "bg-[rgba(245,158,11,0.1)] border-[rgba(245,158,11,0.2)]"
    elif "MANUAL"    in d: return "text-violet-500", "#8B5CF6", "bg-[rgba(139,92,246,0.1)] border-[rgba(139,92,246,0.2)]"
    else:                  return "text-emerald-500", "#10B981", "bg-[rgba(16,185,129,0.1)] border-[rgba(16,185,129,0.2)]"

def generate_pdf(memo: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(10,12,18); pdf.rect(0,0,210,36,'F')
    pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",18)
    pdf.set_y(7); pdf.cell(0,10,"NEOSTATS v3.0",align="C",ln=True)
    pdf.set_font("Helvetica","",9); pdf.set_text_color(100,116,139)
    pdf.cell(0,5,"Credit Intelligence Terminal  |  CONFIDENTIAL",align="C",ln=True)
    pdf.ln(8)
    
    _, dcol_hex, _ = _decision_styles(memo.get("decision",""))
    r,g,b = tuple(int(dcol_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    pdf.set_fill_color(r,g,b); pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",12); pdf.set_x(20)
    pdf.cell(170,10,f"VERDICT: {memo.get('decision','').upper()}",align="C",fill=True,ln=True); pdf.ln(5)
    
    pdf.set_text_color(50,50,50); pdf.set_font("Helvetica","",9)
    pdf.multi_cell(0,6,f"Rationale: {re.sub(r'\\*+|#{1,6} ','', memo.get('rationale',''))[:1500]}")
    return bytes(pdf.output())

def render_top_header():
    st.markdown("""
    <div style="padding:16px 32px; border-bottom:1px solid rgba(30,41,59,0.6); background:rgba(6,8,14,0.8); backdrop-filter:blur(12px); display:flex; justify-content:space-between; align-items:center;">
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.2rem; font-weight:900; color:var(--tx-white); letter-spacing:-.02em;">NeoFin <span style="color:var(--blue);">Chat</span></span>
      </div>
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:8px; height:8px; border-radius:50%; background:var(--emerald); box-shadow:0 0 12px var(--emerald);"></div>
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; font-weight:800; color:var(--emerald); letter-spacing:.1em;">ARIA_CONNECTED</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
