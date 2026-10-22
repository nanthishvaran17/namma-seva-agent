from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="CITIZEN", nullable=False) # CITIZEN, REVIEWER, ADMIN
    preferred_language: Mapped[str] = mapped_column(String(10), default="ta", nullable=False) # ta, en, ta-en
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    consents: Mapped[list["UserConsent"]] = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list["UserTaskModel"]] = relationship("UserTaskModel", back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[list["UserDocumentModel"]] = relationship("UserDocumentModel", back_populates="user", cascade="all, delete-orphan")
    conversations: Mapped[list["ConversationModel"]] = relationship("ConversationModel", back_populates="user", cascade="all, delete-orphan")

class UserConsent(Base):
    __tablename__ = "user_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_purpose: Mapped[str] = mapped_column(String(100), nullable=False) # e.g., "DOCUMENT_OCR_PROCESSING", "TASK_TRACKING"
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="consents")
