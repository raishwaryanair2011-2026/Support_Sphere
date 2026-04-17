"""
Knowledge Base RAG service.

Design decisions vs original:
- Fully async — no blocking IO on the request thread.
- Stateless — no global LAST_TECH_ISSUE / LAST_OS variables (broken under concurrency).
  OS detection and topic tracking happen per-request within the function.
- Vector store operations run in a thread pool to avoid blocking the event loop
  (chromadb is sync).
- YouTube search is optional; gracefully skipped when API key is absent.
"""
import asyncio
from functools import lru_cache

import httpx
from groq import AsyncGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.kb import KBAskResponse

logger = get_logger(__name__)
settings = get_settings()


# ── Vector store (lazy-initialised, one instance per process) ─────────────────
@lru_cache(maxsize=1)
def _get_vector_store():
    import chromadb
    from sentence_transformers import SentenceTransformer

    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)
    collection = client.get_or_create_collection("kb_documents")
    try:
        embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    except Exception as exc:
        logger.warning("embedding_model_load_failed", error=str(exc))
        embedder = None
    return collection, embedder


def _add_chunks_sync(chunks: list[str], metadatas: list[dict]) -> None:
    """Called from a thread pool — do NOT await."""
    import uuid

    collection, embedder = _get_vector_store()
    if embedder is None:
        logger.warning("add_chunks_skipped", reason="embedder not available")
        return
    embeddings = embedder.encode(chunks).tolist()
    ids = [str(uuid.uuid4()) for _ in chunks]
    collection.add(documents=chunks, metadatas=metadatas, embeddings=embeddings, ids=ids)


def _query_chunks_sync(query: str, n_results: int = 4) -> dict:
    collection, embedder = _get_vector_store()
    if embedder is None:
        return {"documents": [[]], "distances": [[]]}
    embedding = embedder.encode([query]).tolist()
    return collection.query(query_embeddings=embedding, n_results=n_results)


async def add_chunks(chunks: list[str], metadatas: list[dict]) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _add_chunks_sync, chunks, metadatas)


async def query_chunks(query: str, n_results: int = 4) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _query_chunks_sync, query, n_results)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ── Helper: OS detection ──────────────────────────────────────────────────────
def _detect_os(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ("mac", "macbook", "macos")):
        return "mac"
    if any(k in t for k in ("linux", "ubuntu", "debian")):
        return "linux"
    return "windows"


# ── Helper: video intent ──────────────────────────────────────────────────────
def _is_video_request(text: str) -> bool:
    return any(w in text.lower() for w in ("video", "youtube", "tutorial", "watch"))


def _extract_video_topic(text: str) -> str:
    t = text.lower()
    for w in ("video", "youtube", "tutorial", "show", "give", "watch"):
        t = t.replace(w, "")
    return t.strip()


# ── YouTube search ────────────────────────────────────────────────────────────
async def _youtube_search(query: str, limit: int = 2) -> list[str]:
    if not settings.YOUTUBE_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": limit,
                    "key": settings.YOUTUBE_API_KEY,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                for item in data.get("items", [])
            ]
    except Exception as exc:
        logger.warning("youtube_search_failed", error=str(exc))
        return []


# ── Greeting / small-talk short-circuits ─────────────────────────────────────
_GREETINGS = {
    "hi", "hii", "hiii", "hello", "helo", "hlo", "hey", "heyy",
    "hy", "hai", "gm", "gn", "good morning", "good afternoon", "good evening",
}

_SMALL_TALK: dict[str, str] = {
    "ok": "Alright 👍 Let me know if you need anything else.",
    "okay": "Alright 👍 Let me know if you need anything else.",
    "thanks": "You're welcome 🙂",
    "thank you": "You're welcome 🙂",
    "thankyou": "You're welcome 🙂",
    "bye": "Goodbye 👋",
    "no": "Alright 👍 Let me know if you need help later.",
}


def _quick_reply(normalized: str) -> KBAskResponse | None:
    if normalized in _GREETINGS or normalized.startswith(("hi", "he", "ha")):
        return KBAskResponse(
            answer="Hi 👋 How can I help you today?",
            intent="greeting",
            source="static",
            confidence=1.0,
            suggest_ticket=False,
        )
    if normalized in _SMALL_TALK:
        return KBAskResponse(
            answer=_SMALL_TALK[normalized],
            intent="small_talk",
            source="static",
            confidence=1.0,
            suggest_ticket=False,
        )
    return None


# ── Conversation history formatter ───────────────────────────────────────────
def _format_history(history: list) -> list[dict]:
    """
    Convert frontend chat history into Groq message format.
    Keeps last 10 exchanges (20 messages max) to stay within context limits.
    """
    messages = []
    # Take last 20 messages (10 user + 10 bot)
    recent = history[-20:] if len(history) > 20 else history
    for msg in recent:
        role = "user" if msg.role == "user" else "assistant"
        messages.append({"role": role, "content": msg.text})
    return messages


# ── Main public function ──────────────────────────────────────────────────────
async def answer_question(question: str, history: list | None = None) -> KBAskResponse:
    """
    Answer a user question using:
    1. Static greeting/small-talk handlers
    2. YouTube search (if video intent detected)
    3. Vector KB search + Groq LLM (with conversation memory)
    4. Suggest raising a ticket if KB has no match
    """
    normalized = question.strip().lower()
    history = history or []

    # 1. Static short-circuits (greetings don't need history)
    quick = _quick_reply(normalized)
    if quick:
        return quick

    # 2. Video intent
    if _is_video_request(question):
        topic = _extract_video_topic(question) or question
        os_hint = _detect_os(topic)
        videos = await _youtube_search(f"{topic} {os_hint} fix tutorial")
        return KBAskResponse(
            answer="Here's a tutorial that may help:",
            intent="video",
            source="youtube",
            confidence=1.0,
            suggest_ticket=False,
            videos=videos,
        )

    # 3. Vector search
    result = await query_chunks(question)
    retrieved_docs = result.get("documents", [[]])[0]
    distances = result.get("distances", [[]])[0]

    documents = [
        doc for doc, dist in zip(retrieved_docs, distances)
        if dist < settings.KB_SIMILARITY_THRESHOLD
    ]
    context = "\n\n".join(documents)
    os_hint = _detect_os(question)
    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    # Build conversation history messages for Groq
    history_messages = _format_history(history)

    if not context:
        # 4. No KB match — suggest raising a ticket directly
        return KBAskResponse(
            answer=(
                "I wasn't able to find an answer to that in our Knowledge Base. "
                "To get the right help, please raise a support ticket and one of our "
                "agents will assist you as soon as possible."
            ),
            intent="no_match",
            source="static",
            confidence=0.0,
            suggest_ticket=True,
        )

    # 5. KB match found — answer using context + conversation history
    system_prompt = (
        "You are a helpful company support assistant covering IT, HR, Finance, and Facilities.\n"
        "Answer using ONLY the context provided. Do NOT invent information.\n"
        "Be concise. Use numbered steps for procedural answers.\n"
        "If the user's question refers to something from earlier in the conversation, "
        "use that context to give a more relevant answer.\n\n"
        f"Knowledge Base context:\n{context}"
    )

    # Build messages: system + history + current question
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": question})

    if not groq_client:
        return KBAskResponse(
            answer="The AI service is currently unavailable. Please raise a support ticket for help.",
            intent="no_groq",
            source="static",
            confidence=0.0,
            suggest_ticket=True,
        )

    try:
        resp = await groq_client.chat.completions.create(
            model=settings.GROQ_KB_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=400,
        )
        answer_text = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.error("kb_llm_failed", error=str(exc))
        answer_text = "Something went wrong. Please try again or raise a support ticket."

    return KBAskResponse(
        answer=answer_text,
        intent="kb_answer",
        source="kb",
        confidence=0.85,
        suggest_ticket=False,
    )