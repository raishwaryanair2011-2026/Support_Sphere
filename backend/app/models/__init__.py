# Import all models here so Alembic's autogenerate picks them up.
from app.models.user import User, UserRole  # noqa: F401
from app.models.ticket import Ticket, TicketMessage, TicketAttachment  # noqa: F401
from app.models.ticket import TicketStatus, TicketPriority, TicketQueue  # noqa: F401
from app.models.kb import FAQ, KBDocument, KBChunk  # noqa: F401
