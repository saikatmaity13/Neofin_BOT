"""
NeoStats configuration — loaded from .env or environment variables.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── LLM Provider (choose one) ──────────────────────────────────────────
    # Option A: Anthropic Claude (default)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # Option B: Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"

    # Option C: Ollama (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # Option D: Groq (free, fast, recommended)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Active provider: "anthropic" | "gemini" | "ollama" | "groq"
    LLM_PROVIDER: str = "groq"

    # ── Data ──────────────────────────────────────────────────────────────
    CREDIT_DATA_PATH: str = "data/credit_risk.xlsx"
    VECTORSTORE_PATH: str = "vectorstore/financial_rag"

    # ── RAG / Embeddings ──────────────────────────────────────────────────
    # Uses sentence-transformers (free, local)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 4
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # ── Agent ─────────────────────────────────────────────────────────────
    MAX_ITERATIONS: int = 6

    # ── Compliance ────────────────────────────────────────────────────────
    # Loan must not exceed this fraction of annual income
    COMPLIANCE_INCOME_RATIO: float = 0.40

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
