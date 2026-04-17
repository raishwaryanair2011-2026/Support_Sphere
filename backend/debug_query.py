"""
Run from D:\support-portal-v2 to see actual similarity scores for a test query.
    python debug_query.py
"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(".env", override=True)

import chromadb
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings

settings = get_settings()

def test_query(question: str):
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)
    col = client.get_collection("kb_documents")
    embedder = SentenceTransformer(settings.EMBEDDING_MODEL)

    embedding = embedder.encode([question]).tolist()
    result = col.query(query_embeddings=embedding, n_results=4,
                       include=["documents", "distances", "metadatas"])

    docs = result["documents"][0]
    dists = result["distances"][0]
    metas = result["metadatas"][0]

    print(f"\nQuery: '{question}'")
    print(f"Current threshold: {settings.KB_SIMILARITY_THRESHOLD}")
    print(f"\nTop {len(docs)} results:")
    for i, (doc, dist, meta) in enumerate(zip(docs, dists, metas)):
        status = " PASSES" if dist < settings.KB_SIMILARITY_THRESHOLD else "❌ FILTERED OUT"
        print(f"\n  [{i+1}] Distance: {dist:.4f} — {status}")
        print(f"       Title: {meta.get('title','?')}")
        print(f"       Text:  {doc[:80]}...")

    passing = [d for d in dists if d < settings.KB_SIMILARITY_THRESHOLD]
    print(f"\nResult: {len(passing)}/{len(docs)} chunks pass the threshold.")
    if len(passing) == 0:
        suggested = min(dists) + 0.05
        print(f"Suggestion: Lower threshold to {suggested:.2f} to allow the best match through.")

# Test with common questions
questions = [
    "how do I reset my password",
    "my laptop won't connect to wifi",
    "how do I apply for leave",
]

for q in questions:
    test_query(q)
    print("\n" + "="*60)