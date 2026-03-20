# 🏦 NeoFIN -  Agentic Credit Underwriter

> **ARIA** (Agentic Risk Intelligence Analyst) — an AI-powered loan assessment engine built by Saikat Maity.

A production-grade **Streamlit** application featuring a multi-step agentic loop that evaluates loan applications using real credit data, RAG-based market intelligence, and rule-based compliance checks.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Agentic Reasoning** | Step-by-step tool-calling loop (up to N iterations) with visible thought process |
| 🔍 **Credit History Tool** | Queries `credit_risk.csv` for income, debt, score, defaults |
| 📈 **Market Trends RAG** | FAISS + sentence-transformers over Sujet Financial Dataset |
| ⚖️ **Compliance Engine** | Rule-based: 40% LTI cap, employment checks, default limits |
| 📊 **Risk Matrix Scorer** | Weighted composite score (credit 30%, DTI 25%, defaults 20%, …) |
| 📄 **Credit Memo** | Live structured output with APPROVE / REJECT / MANUAL REVIEW badge |
| ⬇️ **Download Report** | One-click `.txt` Credit Memo export |
| 🧠 **Thought Process** | Expandable step-by-step agent reasoning in the UI |

---

## 🚀 Quick Start

### 1. Clone / unzip the project

```bash
cd neostats_credit
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (or Gemini/Ollama)
```

### 4. Add credit data

Download `credit_risk.csv` from Kaggle:
https://www.kaggle.com/datasets/laotse/credit-risk-dataset

Place it at `data/credit_risk.csv`.

> **Demo data included:** `data/credit_risk.csv` ships with 20 synthetic applicants (A001–A020) so you can run immediately without Kaggle.

### 5. Build the RAG vectorstore (optional but recommended)

```bash
python setup_vectorstore.py
```

This downloads the [Sujet Financial RAG Dataset](https://huggingface.co/datasets/sujet-ai/Sujet-Financial-RAG-EN-Dataset) from Hugging Face, embeds it with `all-MiniLM-L6-v2`, and saves a FAISS index to `vectorstore/financial_rag/`.

> **Skip this step** — the app ships with a high-quality fallback corpus of financial sector risk data that works without FAISS.

### 6. Run the app

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501

---

## 🗂️ Project Structure

```
neostats_credit/
├── streamlit_app.py              # Main UI (Streamlit)
├── setup_vectorstore.py          # One-time RAG index builder
├── requirements.txt
├── .env.example
│
├── data/
│   └── credit_risk.csv           # Kaggle dataset (or demo data)
│
├── vectorstore/
│   └── financial_rag/            # Built by setup_vectorstore.py
│       ├── index.faiss
│       └── chunks.pkl
│
└── app/
    ├── config.py                 # Pydantic settings from .env
    │
    ├── llm/
    │   ├── agent.py              # Core agentic loop (tool dispatch, LLM calls)
    │   ├── system_prompt.py      # NeoStats ARIA system prompt
    │   └── tool_definitions.py   # Tool schemas for Claude / OpenAI format
    │
    ├── memory/
    │   └── manager.py            # In-memory session history
    │
    └── tools/
        ├── credit_history.py     # check_credit_history tool
        ├── market_trends.py      # research_market_trends tool (RAG)
        └── compliance.py         # regulatory_compliance_check + score_risk_matrix
```

---

## 🧠 Agentic Reasoning Flow

```
User Message
    │
    ▼
┌─────────────────────────────────────────────────┐
│                 ARIA AGENT LOOP                 │
│                                                 │
│  STEP 1 → check_credit_history                  │
│           Income, score, defaults, employment   │
│                                                 │
│  STEP 2 → regulatory_compliance_check           │
│           40% LTI rule, income threshold        │
│                                                 │
│  STEP 3 → research_market_trends (conditional)  │
│           RAG over Sujet Financial Dataset      │
│           Triggered if: low score / business /  │
│           high loan amount                      │
│                                                 │
│  STEP 4 → score_risk_matrix                     │
│           Weighted composite 0–100              │
│                                                 │
│  STEP 5 → Synthesize → Credit Memo              │
│           APPROVED / REJECTED / MANUAL REVIEW   │
└─────────────────────────────────────────────────┘
    │
    ▼
Structured Credit Memo + Download Report
```

---

## ⚙️ LLM Provider Options

Set `LLM_PROVIDER` in your `.env`:

| Provider | Setting | Notes |
|---|---|---|
| Anthropic Claude | `LLM_PROVIDER=anthropic` | **Recommended** — full tool calling |
| Google Gemini | `LLM_PROVIDER=gemini` | Single-shot (no native tool calling) |
| Ollama (local) | `LLM_PROVIDER=ollama` | Free, local, single-shot |

---

## 📊 Risk Scoring Weights

| Factor | Weight |
|---|---|
| Credit Score | 30% |
| Debt-to-Income Ratio | 25% |
| Previous Defaults | 20% |
| Employment Stability | 15% |
| Sector / Market Risk | 10% |

**Decision thresholds:**
- Score ≥ 75 → **APPROVED**
- Score 55–74 → **CONDITIONALLY APPROVED**
- Score 35–54 → **MANUAL REVIEW**
- Score < 35 → **REJECTED**

---

## 🔒 Compliance Rules

1. Loan amount ≤ 40% of annual income *(hard stop)*
2. Annual income > ₹1,80,000 *(poverty threshold)*
3. Not unemployed *(income verification)*
4. Previous defaults < 2 *(NeoStats policy)*
5. Loan purpose not prohibited *(no speculation/gambling)*

---

## 📝 Demo Applicants

| ID | Income | Score | Defaults | Notes |
|---|---|---|---|---|
| A001 | ₹8.5L | 745 | 0 | Strong profile |
| A003 | ₹4.2L | 610 | 0 | Borderline — education loan |
| A009 | ₹2.8L | 490 | 2 | High risk |
| A010 | ₹32L | 810 | 0 | Excellent — large business loan |
| A020 | ₹45L | 825 | 0 | Premium applicant |

---

*Built by NeoStats Data & AI · Powered by Anthropic Claude*
