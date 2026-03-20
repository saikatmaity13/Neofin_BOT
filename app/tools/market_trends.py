"""
Tool: research_market_trends
Uses FAISS + sentence-transformers to do RAG over the
Sujet Financial Dataset (or a fallback corpus if not downloaded).
"""

import logging
import os
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_vector_store = None  # lazy-loaded FAISS index
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"[RAGTool] Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except ImportError:
            logger.warning("[RAGTool] sentence-transformers not installed; RAG disabled.")
    return _embedder


def _load_vector_store():
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    store_path = settings.VECTORSTORE_PATH
    if os.path.exists(store_path):
        try:
            import faiss
            import pickle
            index = faiss.read_index(os.path.join(store_path, "index.faiss"))
            with open(os.path.join(store_path, "chunks.pkl"), "rb") as f:
                chunks = pickle.load(f)
            _vector_store = {"index": index, "chunks": chunks}
            logger.info(f"[RAGTool] Loaded FAISS index with {index.ntotal} vectors")
        except Exception as e:
            logger.warning(f"[RAGTool] Could not load FAISS index: {e}")
    return _vector_store


# ── Fallback corpus ───────────────────────────────────────────────────────────
FALLBACK_CORPUS = [
    {"sector": "retail", "text": "The retail sector faces elevated credit risk due to thin margins, high competition from e-commerce, and volatile consumer demand. Post-pandemic shifts to online shopping have weakened traditional brick-and-mortar retailers significantly."},
    {"sector": "retail", "text": "Retail businesses show higher default rates (12-18%) compared to the national average. Seasonal cash-flow gaps make loan repayment timing a key risk factor for lenders."},
    {"sector": "manufacturing", "text": "The manufacturing sector carries moderate credit risk. Supply chain disruptions, raw material price volatility, and energy costs are primary risk drivers. Export-oriented manufacturers face additional forex risk."},
    {"sector": "manufacturing", "text": "Manufacturing firms with long-term contracts show significantly lower default rates. Working capital loans in this sector typically perform well when secured against inventory."},
    {"sector": "technology", "text": "Technology startups present high-risk / high-reward credit profiles. Revenue predictability is low in early stages but improves significantly with SaaS recurring revenue models. VC-backed companies may have better repayment capacity."},
    {"sector": "technology", "text": "Established IT services firms show low default rates (3-5%) and strong cash flow visibility, making them relatively safe lending targets. However, over-reliance on a single client is a concentration risk."},
    {"sector": "agriculture", "text": "Agriculture credit carries high systemic risk from monsoon dependency, price volatility, and policy changes. Kharif season loan defaults spike in drought years. Government support schemes (PMFBY) partially mitigate risk."},
    {"sector": "real estate", "text": "Real estate sector credit risk is cyclical and correlated with interest rates. High leverage ratios (often 70-80%) amplify losses in downturns. RERA regulations have improved project completion rates, reducing construction risk."},
    {"sector": "healthcare", "text": "Healthcare businesses show resilient credit profiles with consistent demand. Hospitals and clinics have stable revenue streams, though capital-intensive nature requires careful liquidity analysis."},
    {"sector": "education", "text": "Private education institutions face regulatory risk and demographic shifts. Premium institutions show low default rates while budget edtech companies face higher churn and repayment pressure."},
    {"sector": "general", "text": "Key credit risk indicators across sectors: debt-service coverage ratio (DSCR) below 1.25x is a red flag; net profit margin below 5% signals stress; current ratio below 1.0 indicates liquidity risk."},
    {"sector": "general", "text": "RBI guidelines mandate that retail loans above ₹50 lakhs require comprehensive credit appraisal. CIBIL scores below 650 trigger enhanced due diligence. NPA rates in unsecured personal loans rose to 4.2% in FY24."},
    {"sector": "general", "text": "Interest rate sensitivity analysis: a 100 bps rate hike increases EMI burden by approximately 6-8%, which directly impacts DSCR for floating-rate borrowers. Variable-income borrowers are especially vulnerable."},
    {"sector": "fintech", "text": "Buy-now-pay-later and digital lending segments show rising NPAs (8-12%) as post-pandemic credit expansion matures. Thin underwriting standards in the 2021-22 boom are now showing delinquency stress."},
    {"sector": "vehicle", "text": "Commercial vehicle financing shows cyclical patterns aligned with GDP growth. CV loan NPAs typically lag the economic cycle by 6-9 months. EV transition poses residual value risk for conventional vehicle loans."},
]


def _fallback_search(query: str, sector: str = "", top_k: int = 3) -> List[str]:
    """Simple keyword-based fallback when FAISS index is unavailable."""
    query_lower = query.lower()
    sector_lower = sector.lower() if sector else ""

    scored = []
    for item in FALLBACK_CORPUS:
        score = 0
        text_lower = item["text"].lower()
        item_sector = item["sector"].lower()

        # Sector match bonus
        if sector_lower and sector_lower in item_sector:
            score += 10
        if sector_lower and sector_lower in text_lower:
            score += 5

        # Keyword match
        for word in query_lower.split():
            if len(word) > 3 and word in text_lower:
                score += 1
            if len(word) > 3 and word in item_sector:
                score += 2

        scored.append((score, item["text"]))

    scored.sort(key=lambda x: -x[0])
    return [text for _, text in scored[:top_k] if _ >= 0]


def research_market_trends(query: str, sector: str = "") -> Dict[str, Any]:
    """
    Main tool function. Returns market/sector risk information via RAG.
    """
    embedder = _get_embedder()
    store = _load_vector_store()

    chunks = []

    if embedder and store:
        try:
            import numpy as np
            embedding = embedder.encode([query])
            embedding = np.array(embedding, dtype="float32")
            distances, indices = store["index"].search(embedding, settings.RAG_TOP_K)
            all_chunks = store["chunks"]
            for i, dist in zip(indices[0], distances[0]):
                if 0 <= i < len(all_chunks):
                    chunks.append({
                        "text": all_chunks[i],
                        "relevance_score": float(1 / (1 + dist)),
                    })
            logger.info(f"[RAGTool] Retrieved {len(chunks)} chunks for query: '{query}'")
        except Exception as e:
            logger.warning(f"[RAGTool] FAISS search failed: {e}; using fallback.")

    if not chunks:
        fallback_texts = _fallback_search(query, sector, top_k=settings.RAG_TOP_K)
        chunks = [{"text": t, "relevance_score": 0.75} for t in fallback_texts]
        logger.info(f"[RAGTool] Using fallback corpus: {len(chunks)} results")

    # Determine aggregate risk level from content
    combined = " ".join(c["text"] for c in chunks).lower()
    if any(w in combined for w in ["high risk", "elevated risk", "volatile", "default rate", "npa", "stress", "delinquency"]):
        risk_level = "HIGH"
    elif any(w in combined for w in ["moderate", "cyclical", "medium risk"]):
        risk_level = "MEDIUM"
    elif any(w in combined for w in ["low risk", "stable", "resilient", "strong"]):
        risk_level = "LOW"
    else:
        risk_level = "MEDIUM"

    return {
        "query": query,
        "sector": sector or "general",
        "risk_level": risk_level,
        "retrieved_chunks": chunks,
        "source": "Sujet Financial RAG Dataset (FAISS)" if (embedder and store) else "Fallback financial corpus",
    }


def format_market_research_for_llm(result: Dict[str, Any]) -> str:
    lines = [
        f"=== MARKET RESEARCH: {result['sector'].upper()} SECTOR ===",
        f"Aggregate Sector Risk Level: {result['risk_level']}",
        f"Source: {result['source']}",
        "",
        "Key Findings:",
    ]
    for i, chunk in enumerate(result["retrieved_chunks"], 1):
        lines.append(f"  [{i}] (relevance: {chunk['relevance_score']:.2f}) {chunk['text']}")
    return "\n".join(lines)
