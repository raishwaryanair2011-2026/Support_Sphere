"""
Run this from D:\support-portal-v2 with the venv active:
    python reindex_kb.py

It finds all KB documents that are not properly indexed and re-indexes them.
"""
import asyncio, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(".env", override=True)

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.kb import KBDocument, KBChunk
from app.services.ai.rag import add_chunks, chunk_text
from app.utils.files import extract_text_from_file


async def reindex_all():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(KBDocument))
        docs = result.scalars().all()

        if not docs:
            print("No KB documents found in database.")
            return

        for doc in docs:
            print(f"\nProcessing: {doc.title} (id={doc.id}, status={doc.status})")

            try:
                text = extract_text_from_file(doc.file_path)
                if not text.strip():
                    print(f"  ✗ No text extracted from {doc.file_path}")
                    doc.status = "Failed"
                    continue

                chunks = chunk_text(text)
                metadatas = [
                    {"title": doc.title, "category": doc.category or "", "document_id": doc.id}
                    for _ in chunks
                ]

                # Remove old chunks from SQLite
                old_chunks = await db.execute(select(KBChunk).where(KBChunk.document_id == doc.id))
                for c in old_chunks.scalars().all():
                    await db.delete(c)

                # Add fresh chunks to SQLite
                for chunk in chunks:
                    db.add(KBChunk(document_id=doc.id, content=chunk))

                # Embed and store in ChromaDB
                await add_chunks(chunks, metadatas)

                doc.chunk_count = len(chunks)
                doc.status = "Indexed"
                print(f"  ✓ Indexed {len(chunks)} chunks")

            except Exception as e:
                print(f"  ✗ Failed: {e}")
                doc.status = "Failed"

        await db.commit()
        print("\n✅ Done! Restart the server and check the Knowledge Base page.")


if __name__ == "__main__":
    asyncio.run(reindex_all())