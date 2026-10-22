from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Service Inquiry", nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="WEB", nullable=False) # WEB, WHATSAPP, VOICE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["MessageModel"]] = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")

class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(50), nullable=False) # "USER", "AGENT", "SYSTEM"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="ta", nullable=False) # ta, en, ta-en
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False) # tool_calls, citations, structured cards
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    conversation: Mapped["ConversationModel"] = relationship("ConversationModel", back_populates="messages")
