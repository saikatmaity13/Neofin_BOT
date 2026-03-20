import os
import json
import pandas as pd
import streamlit as st
import tempfile
from dotenv import load_dotenv

from app.ui_theme import apply_react_dark_theme, render_top_header
from app.config import get_settings

load_dotenv()
settings = get_settings()

st.set_page_config(page_title="Know Your Bills", page_icon="📄", layout="wide")
apply_react_dark_theme()
render_top_header()

st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; max-width:600px; margin:0 auto; margin-bottom:40px;">
  <div style="width:80px; height:80px; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.2); border-radius:24px; display:flex; align-items:center; justify-content:center; font-size:2.5rem; margin:0 auto 20px; box-shadow:0 0 30px rgba(16,185,129,0.1);">
    📄
  </div>
  <h2 style="font-size:2.2rem; font-weight:900; color:var(--tx-white); letter-spacing:-.02em; margin-bottom:16px;">Know Your Bills</h2>
  <p style="font-size:1.1rem; color:var(--tx-muted);">Upload complex financial documents, bank statements, or loan agreements.<br>We extract the jargon and tell you exactly what you need to know.</p>
</div>
""", unsafe_allow_html=True)

# Application State
if "kyb_doc_text" not in st.session_state:
    st.session_state.kyb_doc_text = ""
if "kyb_analysis" not in st.session_state:
    st.session_state.kyb_analysis = None
if "kyb_chat_history" not in st.session_state:
    st.session_state.kyb_chat_history = []

col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    st.markdown("""
    <div style="background:var(--bg-sidebar); border:1px solid var(--border); border-radius:16px; padding:32px; box-shadow:0 10px 30px rgba(0,0,0,0.2);">
      <h3 style="color:var(--tx-white); font-size:1.2rem; font-weight:800; margin-bottom:16px; display:flex; align-items:center; gap:8px;">
        <span style="color:var(--emerald);">1.</span> Upload Document
      </h3>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Select PDF file", type=["pdf"], label_visibility="collapsed")
    
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        # Add extract button 
        if st.button("✨ EXTRACT & ANALYZE BILL", use_container_width=True, type="primary"):
            with st.spinner("Analyzing document with NeoStats AI..."):
                try:
                    import pypdf
                    
                    pdf_reader = pypdf.PdfReader(uploaded_file)
                    text_content = ""
                    for page in pdf_reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text_content += extracted + "\\n"
                            
                    if not text_content.strip():
                        st.error("Could not extract any text from this PDF. It might be a scanned image.")
                    else:
                        st.session_state.kyb_doc_text = text_content
                        
                        from groq import Groq
                        api_key = settings.GROQ_API_KEY
                        if not api_key:
                            st.error("No GROQ_API_KEY found. Please add it to your .env file.")
                        else:
                            client = Groq(api_key=api_key)
                            
                            prompt = (
                                "You are a highly skilled financial analyst taking apart a financial document (bill, bank statement, loan agreement). "
                                "Read the attached text carefully. Extract the financial insights into the following strict JSON format:\n"
                                "{\n"
                                '  "document_summary": "1 sentence describing what this document is.",\n'
                                '  "actions_required": ["List of immediate actions, due dates, bills to pay, etc."],\n'
                                '  "key_takeaways": ["Hidden fees, important bullet points"],\n'
                                '  "expenses": [{"description": "Item name", "category": "Software/Travel/Utilities/Food/Other", "amount": 10.50}],\n'
                                '  "anomalies": ["Flag suspicious inconsistencies, unusually high amounts, mismatching dates, or potential fraud."]\n'
                                "}\n"
                                "Make sure all amounts in `expenses` are numeric floats. Return ONLY valid JSON!"
                            )
                            
                            messages = [
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": f"Here is the text from the document:\n\n{text_content[:8000]}"}
                            ]
                            
                            response = client.chat.completions.create(
                                model=settings.GROQ_MODEL,
                                messages=messages,
                                response_format={"type": "json_object"},
                                max_tokens=1500,
                            )
                            
                            st.session_state.kyb_analysis = json.loads(response.choices[0].message.content)
                            st.session_state.kyb_chat_history = []
                except Exception as e:
                    st.error(f"Error processing document: {e}")

# ── RENDER RESULTS ──
if st.session_state.kyb_analysis:
    analysis = st.session_state.kyb_analysis
    
    with col2:
        # 0. Anomalies / Fraud Detection
        anomalies = analysis.get("anomalies", [])
        if anomalies and len(anomalies) > 0 and anomalies[0].strip() != "":
            st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
            st.error(f"🚩 **Fraud Detection & Anomalies Flagged ({len(anomalies)} items)**")
            for an in anomalies:
                st.warning(f"• {an}")
                
        # 1. Intelligence Report
        st.markdown("""
        <div style="margin-top:24px; background:var(--bg-input); border:1px solid var(--border); border-left:4px solid var(--emerald); border-radius:12px; padding:32px;">
          <h4 style="color:var(--emerald); font-size:0.8rem; font-weight:900; text-transform:uppercase; letter-spacing:.1em; margin-bottom:20px;">Document Intelligence Report</h4>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**What is this document?**<br>{analysis.get('document_summary','')}", unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color:var(--border); margin:16px 0;'>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**⚠️ Immediate Actions:**")
            for act in analysis.get("actions_required", []):
                st.markdown(f"- {act}")
        with col_b:
            st.markdown("**🔑 Key Takeaways:**")
            for tk in analysis.get("key_takeaways", []):
                st.markdown(f"- {tk}")
                
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. Expense Categorization & Bar Chart
        expenses = analysis.get("expenses", [])
        if expenses:
            st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
            df = pd.DataFrame(expenses)
            
            col_chart, col_emi = st.columns([2, 1], gap="large")
            
            with col_chart:
                st.markdown("### Expense Categorization")
                if "category" in df.columns and "amount" in df.columns:
                    cat_spend = df.groupby("category")["amount"].sum().reset_index()
                    st.bar_chart(cat_spend, x="category", y="amount", use_container_width=True)
            
            # 3. Predictive EMI Visualization
            with col_emi:
                st.markdown("""
                <div style="background:var(--bg-sidebar); border:1px solid var(--border); padding:24px; border-radius:12px;">
                  <h4 style="font-size:0.8rem; font-weight:800; color:var(--tx-white); text-transform:uppercase; margin-bottom:8px;">Predictive EMI Impact</h4>
                  <p style="font-size:0.75rem; color:var(--tx-muted); margin-bottom:16px;">Visualize how a proposed loan EMI impacts your monthly burn rate based on this bill.</p>
                """, unsafe_allow_html=True)
                proposed_emi = st.number_input("Proposed Monthly EMI (₹)", min_value=0, value=5000, step=1000)
                
                total_spend = float(df["amount"].sum())
                new_burn = total_spend + proposed_emi
                
                st.markdown(f"""
                <div style="margin-top:16px;">
                  <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:var(--tx-muted); font-size:0.75rem;">Current Document Spend:</span>
                    <span style="color:var(--tx-white); font-weight:700;">₹{total_spend:,.2f}</span>
                  </div>
                  <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                    <span style="color:var(--blue); font-size:0.75rem;">Proposed EMI:</span>
                    <span style="color:var(--blue); font-weight:700;">+ ₹{proposed_emi:,.2f}</span>
                  </div>
                  <div style="height:1px; background:var(--border); margin-bottom:12px;"></div>
                  <div style="display:flex; justify-content:space-between;">
                    <span style="color:var(--tx-white); font-size:0.85rem; font-weight:800;">Projected Burn:</span>
                    <span style="color:var(--rose); font-size:1.1rem; font-weight:900;">₹{new_burn:,.2f}</span>
                  </div>
                </div>
                </div>
                """, unsafe_allow_html=True)
                
        # 4. RAG-Powered Q&A
        st.markdown("<hr style='border-color:var(--border); margin:40px 0;'>", unsafe_allow_html=True)
        st.markdown("### Document Q&A (Conversational RAG)")
        st.markdown("<p style='color:var(--tx-muted);'>Interrogate your bill directly. The AI has the full document context.</p>", unsafe_allow_html=True)
        
        # Render chat history
        for msg in st.session_state.kyb_chat_history:
            cls = "react-bubble-user" if msg["role"] == "user" else "react-bubble-agent"
            # we use the UI Theme classes !
            st.markdown(f"""<div class="{cls}">{msg['content']}</div>""", unsafe_allow_html=True)
            
        chat_input = st.chat_input("Ask a specific question about this document...")
        if chat_input:
            st.session_state.kyb_chat_history.append({"role": "user", "content": chat_input})
            st.rerun()

        # If the last message is a user message, fetch response
        if len(st.session_state.kyb_chat_history) > 0 and st.session_state.kyb_chat_history[-1]["role"] == "user":
            with st.spinner("Searching document context..."):
                try:
                    from groq import Groq
                    client = Groq(api_key=settings.GROQ_API_KEY)
                    
                    system_chat = (
                        "You are a helpful assistant specialized in answering questions about a specific financial document. "
                        "Use the provided document text as your ONLY source of truth. If the answer is not in the text, clearly state that the document does not mention it.\\n\\n"
                        f"DOCUMENT TEXT:\\n{st.session_state.kyb_doc_text[:8000]}"
                    )
                    
                    messages_payload = [{"role": "system", "content": system_chat}]
                    for m in st.session_state.kyb_chat_history:
                        messages_payload.append({"role": m["role"], "content": m["content"]})
                        
                    resp = client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        messages=messages_payload,
                        max_tokens=1024,
                    )
                    reply = resp.choices[0].message.content
                    st.session_state.kyb_chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                except Exception as e:
                    st.error(f"Q&A Error: {e}")
