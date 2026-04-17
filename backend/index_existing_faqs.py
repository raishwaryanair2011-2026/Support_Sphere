"""
Run once to index all existing FAQs into ChromaDB.
Place in D:\support-portal-v2 and run: python index_existing_faqs.py
"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(".env", override=True)

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.kb import FAQ


async def index_all_faqs():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(FAQ))
        faqs = result.scalars().all()

        if not faqs:
            print("No FAQs found in database.")
            return

        print(f"Found {len(faqs)} FAQs. Indexing into ChromaDB...\n")

        from app.services.ai.rag import add_chunks, _get_vector_store
        collection, embedder = _get_vector_store()

        if embedder is None:
            print(" Embedding model not available. Run the server first to download the model.")
            return

        for faq in faqs:
            faq_id = f"faq:{faq.id}"
            text = f"Question: {faq.question}\nAnswer: {faq.answer}"

            try:
                collection.delete(ids=[faq_id])
            except Exception:
                pass

            try:
                await add_chunks(
                    [text],
                    [{"title": faq.question, "category": faq.category or "FAQ",
                      "type": "faq", "faq_id": str(faq.id)}]
                )
                print(f"   {faq.question[:60]}...")
            except Exception as e:
                print(f"   Failed: {faq.question[:40]} — {e}")

        print(f"\n✅ Done! {len(faqs)} FAQs indexed into ChromaDB.")
        print("Restart the server and test the chatbot with a question from your FAQs.")


if __name__ == "__main__":
    asyncio.run(index_all_faqs())