from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class WebhookDeduplicationModel(Base):
    """
    Persistent store for webhook deduplication.
    Enforces idempotency across worker processes and restarts.
    """
    __tablename__ = "webhook_processed_messages"

    message_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    sender_id_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="whatsapp", nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
