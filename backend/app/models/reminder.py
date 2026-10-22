from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class ReminderModel(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ta: Mapped[str] = mapped_column(String(255), nullable=False)
    message_en: Mapped[str] = mapped_column(Text, nullable=False)
    message_ta: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED", nullable=False, index=True) # SCHEDULED, SENT, CANCELLED, DISMISSED
    channel: Mapped[str] = mapped_column(String(50), default="IN_APP", nullable=False) # IN_APP, WHATSAPP, SMS
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["UserTaskModel"] = relationship("UserTaskModel", back_populates="reminders")
