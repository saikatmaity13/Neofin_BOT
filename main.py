import streamlit as st
from app.ui_theme import apply_react_dark_theme, render_top_header

st.set_page_config(
    page_title="NeoFin Chat | Home",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_react_dark_theme()
render_top_header()

# Hide Sidebar on landing page
st.markdown(
    """<style>
    [data-testid="stSidebar"] { display: none !important; }
    </style>""",
    unsafe_allow_html=True,
)

st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div style="position:relative; text-align:center; max-width:800px; margin:0 auto; margin-bottom:100px; padding-top:60px;">
  <!-- Glowing Background Orbs -->
  <div style="position:absolute; top:-60px; left:50%; transform:translateX(-50%); width:600px; height:350px; background:radial-gradient(ellipse at center, rgba(59,130,246,0.1) 0%, rgba(0,0,0,0) 70%); z-index:0; filter:blur(40px); pointer-events:none;"></div>
  <div style="position:absolute; top:20px; left:20%; width:300px; height:200px; background:radial-gradient(circle, rgba(139,92,246,0.08) 0%, rgba(0,0,0,0) 70%); z-index:0; filter:blur(40px); pointer-events:none;"></div>
  
  <div style="position:relative; z-index:1;">
      <div style="width:100px; height:100px; background:linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(139,92,246,0.15) 100%); border:1px solid rgba(255,255,255,0.05); border-top:1px solid rgba(255,255,255,0.15); border-radius:32px; display:flex; align-items:center; justify-content:center; font-size:3.5rem; margin:0 auto 32px; box-shadow:0 10px 40px rgba(59,130,246,0.2), inset 0 2px 0 rgba(255,255,255,0.1); backdrop-filter:blur(10px);">
        💎
      </div>
      <h1 style="font-size:4.5rem; font-weight:900; color:var(--tx-white); letter-spacing:-.04em; margin-bottom:24px; line-height:1.05;">
        Transform your <br>
        <span style="background:linear-gradient(to right, #60A5FA, #A78BFA); -webkit-background-clip:text; -webkit-text-fill-color:transparent; display:inline-block; padding-bottom:10px;">financial future</span> 
        <span style="color:var(--tx-muted); opacity:0.6;">with us.</span>
      </h1>
      <p style="font-size:1.2rem; color:var(--tx-muted); max-width:550px; margin:0 auto; line-height:1.6; font-weight:500;">
        Enterprise-grade artificial intelligence powering next-generation credit underwriting and document intellect.
      </p>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Custom styled Streamlit links */
.stPageLink {
    text-decoration: none !important;
}
.stPageLink > a {
    background: linear-gradient(145deg, rgba(15,17,23,0.95) 0%, rgba(10,12,18,0.98) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.03);
    border-top: 1px solid rgba(255,255,255,0.08);
    border-radius: 28px;
    padding: 32px;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.03);
    position: relative;
    overflow: hidden;
}
.stPageLink > a::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 100%;
    background: linear-gradient(180deg, rgba(59,130,246,0.08) 0%, transparent 100%);
    opacity: 0;
    transition: opacity 0.4s ease;
    pointer-events: none;
}
.stPageLink > a:hover {
    border-color: rgba(59,130,246,0.4);
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 30px rgba(59,130,246,0.15), inset 0 1px 0 rgba(255,255,255,0.1);
}
.stPageLink > a:hover::before {
    opacity: 1;
}
.stPageLink > a > p {
    font-size: 1.4rem !important;
    font-weight: 800 !important;
    color: var(--tx-white) !important;
    letter-spacing: -0.02em;
    margin-top: 12px;
    z-index: 1;
}
.stPageLink > a > span {
    font-size: 2.2rem !important;
    margin-bottom: 20px;
    background: rgba(255,255,255,0.05);
    width: 64px; height: 64px;
    display: flex !important; 
    align-items: center !important; 
    justify-content: center !important;
    border-radius: 18px;
    box-shadow: inset 0 2px 0 rgba(255,255,255,0.1);
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)

# Navigation Deck
cols = st.columns(3, gap="large")

with cols[0]:
    st.page_link("pages/1_Credit_Intelligence.py", label="Credit Intelligence Terminal", icon="🛡️")
    st.markdown("""<p style="font-size:0.85rem; color:var(--tx-muted); margin-top:-10px; padding:0 30px;">Automated underwriting, B2B logic constraints, and dynamic risk assessment.</p>""", unsafe_allow_html=True)

with cols[1]:
    st.page_link("pages/2_Global_Market.py", label="Global Market Analysis", icon="🌐")
    st.markdown("""<p style="font-size:0.85rem; color:var(--tx-muted); margin-top:-10px; padding:0 30px;">Harness predictive search for immediate macro market logic and RBI updates.</p>""", unsafe_allow_html=True)

with cols[2]:
    st.page_link("pages/3_Know_Your_Bills.py", label="Know Your Bills", icon="📄")
    st.markdown("""<p style="font-size:0.85rem; color:var(--tx-muted); margin-top:-10px; padding:0 30px;">Instantly summarize and extract truth from complex generic financial PDFs.</p>""", unsafe_allow_html=True)

st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
