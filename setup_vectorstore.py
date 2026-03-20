"""
setup_vectorstore.py
====================
Downloads the Sujet Financial RAG dataset from Hugging Face and builds
a FAISS vector index using sentence-transformers embeddings.

Run ONCE before starting the app:
    python setup_vectorstore.py

Requirements:
    pip install datasets sentence-transformers faiss-cpu
"""

import os
import pickle
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

VECTORSTORE_PATH = "vectorstore/financial_rag"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 512
MAX_RECORDS = 5000  # Limit for speed; increase for higher coverage


def download_and_chunk_dataset() -> list[str]:
    """Download Sujet Financial RAG dataset and return text chunks."""
    logger.info("📥 Downloading sujet-ai/Sujet-Financial-RAG-EN-Dataset from Hugging Face...")
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Run: pip install datasets")

    dataset = load_dataset("sujet-ai/Sujet-Financial-RAG-EN-Dataset", split="train")
    logger.info(f"✅ Loaded {len(dataset)} records. Processing up to {MAX_RECORDS}...")

    chunks = []
    for i, record in enumerate(dataset):
        if i >= MAX_RECORDS:
            break
        # Common fields in this dataset
        for field in ["context", "answer", "question", "text", "passage"]:
            text = record.get(field, "")
            if text and len(text.strip()) > 50:
                # Simple chunking by character length
                for j in range(0, len(text), CHUNK_SIZE):
                    chunk = text[j:j + CHUNK_SIZE].strip()
                    if len(chunk) > 50:
                        chunks.append(chunk)
                break  # use the first non-empty field only

    logger.info(f"✅ Created {len(chunks)} text chunks.")
    return chunks


def build_faiss_index(chunks: list[str]) -> None:
    """Embed chunks and save FAISS index."""
    logger.info(f"🔢 Loading embedding model: {EMBEDDING_MODEL}...")
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
    except ImportError:
        raise ImportError("Run: pip install sentence-transformers faiss-cpu numpy")

    model = SentenceTransformer(EMBEDDING_MODEL)

    logger.info(f"🔄 Embedding {len(chunks)} chunks (this may take a few minutes)...")
    batch_size = 256
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        embs = model.encode(batch, show_progress_bar=False)
        all_embeddings.append(embs)
        if i % 1000 == 0:
            logger.info(f"  → Processed {i}/{len(chunks)} chunks...")

    embeddings = np.vstack(all_embeddings).astype("float32")
    logger.info(f"✅ Embeddings shape: {embeddings.shape}")

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    logger.info(f"✅ FAISS index built with {index.ntotal} vectors (dim={dim})")

    # Save
    Path(VECTORSTORE_PATH).mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, os.path.join(VECTORSTORE_PATH, "index.faiss"))
    with open(os.path.join(VECTORSTORE_PATH, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)

    logger.info(f"💾 Saved FAISS index to: {VECTORSTORE_PATH}/")
    logger.info("  • index.faiss")
    logger.info("  • chunks.pkl")


def verify_index() -> None:
    """Quick sanity check on the saved index."""
    import faiss
    import pickle
    import numpy as np
    from sentence_transformers import SentenceTransformer

    logger.info("🔍 Verifying index...")
    index = faiss.read_index(os.path.join(VECTORSTORE_PATH, "index.faiss"))
    with open(os.path.join(VECTORSTORE_PATH, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)

    model = SentenceTransformer(EMBEDDING_MODEL)
    query = "What are the credit risks in the retail sector?"
    query_emb = model.encode([query]).astype("float32")
    distances, indices = index.search(query_emb, 3)

    logger.info(f"✅ Test query: '{query}'")
    for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
        logger.info(f"  [{i+1}] (dist={dist:.2f}) {chunks[idx][:100]}...")

    logger.info("🎉 Vectorstore is ready for use!")


if __name__ == "__main__":
    print("=" * 60)
    print("  NeoStats — Financial RAG Vectorstore Setup")
    print("=" * 60)

    os.makedirs(VECTORSTORE_PATH, exist_ok=True)

    chunks = download_and_chunk_dataset()
    build_faiss_index(chunks)
    verify_index()

    print("\n✅ Setup complete! You can now run: streamlit run streamlit_app.py")
