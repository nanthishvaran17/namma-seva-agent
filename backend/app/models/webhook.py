from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class WebhookDeduplicationModel(Base):
    """
    Persistent store for webhook deduplication.
    Enforces idempotency and retry-safe state transitions across worker processes and restarts.
    Statuses: 'received', 'processing', 'processed', 'failed'
    """
    __tablename__ = "webhook_processed_messages"

    message_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="received", nullable=False, index=True)
    sender_id_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="whatsapp", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
