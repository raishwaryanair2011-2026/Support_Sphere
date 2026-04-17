"""
Run from D:\support-portal-v2 to see what's actually in ChromaDB.
    python check_chroma.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(".env", override=True)

import chromadb
from app.core.config import get_settings

settings = get_settings()
client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)

try:
    col = client.get_collection("kb_documents")
    count = col.count()
    print(f"\nChromaDB collection 'kb_documents': {count} chunks stored")
    if count == 0:
        print("\n❌ ChromaDB is EMPTY — KB documents need to be re-uploaded through the admin panel.")
        print("   Go to Admin → Knowledge Base → delete each document → re-upload the file.")
    else:
        print(f"\n✅ ChromaDB has {count} chunks — KB is indexed correctly.")
        # Show first 3 chunks as sample
        sample = col.get(limit=3, include=["documents", "metadatas"])
        for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"])):
            print(f"\n  Chunk {i+1}: [{meta.get('title','?')}]")
            print(f"  {doc[:100]}...")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("   The chroma folder may not exist yet.")