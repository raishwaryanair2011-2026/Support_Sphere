"""
Ticket classification service.
- Queue: deterministic keyword rules (fast, free, no latency).
- Priority: Groq LLM with keyword fallback on error.
"""
import json

from groq import AsyncGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.ticket import TicketPriority, TicketQueue

logger = get_logger(__name__)
settings = get_settings()

# ── Queue keyword rules ───────────────────────────────────────────────────────
_QUEUE_RULES: list[tuple[list[str], TicketQueue]] = [
    (["wifi", "laptop", "network", "system", "computer", "software", "hardware", "printer", "monitor"], TicketQueue.IT),
    (["salary", "leave", "hr", "payroll", "onboarding", "offboarding", "policy", "benefits"], TicketQueue.HR),
    (["invoice", "payment", "finance", "bill", "reimbursement", "expense", "budget"], TicketQueue.FINANCE),
]

_PRIORITY_RULES: list[tuple[list[str], TicketPriority]] = [
    (["urgent", "down", "crash", "not working", "outage", "critical", "emergency"], TicketPriority.HIGH),
    (["slow", "issue", "problem", "error", "broken", "intermittent"], TicketPriority.MEDIUM),
]


def _classify_queue_by_keyword(text: str) -> TicketQueue:
    for keywords, queue in _QUEUE_RULES:
        if any(k in text for k in keywords):
            return queue
    return TicketQueue.FACILITIES


def _classify_priority_by_keyword(text: str) -> TicketPriority:
    for keywords, priority in _PRIORITY_RULES:
        if any(k in text for k in keywords):
            return priority
    return TicketPriority.LOW


# ── LLM priority classification ───────────────────────────────────────────────
async def _classify_priority_llm(subject: str, description: str) -> TicketPriority | None:
    if not settings.GROQ_API_KEY:
        return None

    prompt = (
        "Classify the PRIORITY of this support ticket.\n"
        'Return ONLY valid JSON: {"priority": "low" | "medium" | "high"}\n\n'
        f"Subject: {subject}\nDescription: {description}"
    )

    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=settings.GROQ_CLASSIFIER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=30,
        )
        content = response.choices[0].message.content or ""
        parsed = json.loads(content)
        raw = parsed.get("priority", "").lower()
        return TicketPriority(raw)
    except Exception as exc:
        logger.warning("llm_priority_classification_failed", error=str(exc))
        return None


# ── Public interface ──────────────────────────────────────────────────────────
async def classify_ticket(
    subject: str, description: str
) -> tuple[TicketQueue, TicketPriority]:
    """
    Returns (queue, priority) for a new ticket.
    Queue is always determined by keywords (deterministic).
    Priority tries LLM first, falls back to keywords.
    """
    text = f"{subject} {description}".lower()
    queue = _classify_queue_by_keyword(text)

    priority = await _classify_priority_llm(subject, description)
    if priority is None:
        priority = _classify_priority_by_keyword(text)

    logger.info("ticket_classified", queue=queue, priority=priority)
    return queue, priority
