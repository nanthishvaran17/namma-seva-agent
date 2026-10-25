from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from backend.app.db.session import Base
from typing import Optional
from backend.app.core.crypto import (
    encrypt_field,
    decrypt_field,
    compute_field_aad,
    compute_phone_blind_index
)

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    _full_name: Mapped[str] = mapped_column("full_name", Text, nullable=False)
    _phone_number: Mapped[Optional[str]] = mapped_column("phone_number", Text, nullable=True)
    phone_blind_index: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="CITIZEN", nullable=False) # CITIZEN, REVIEWER, ADMIN
    preferred_language: Mapped[str] = mapped_column(String(10), default="ta", nullable=False) # ta, en, ta-en
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        self.id = kwargs["id"]
        super().__init__(**kwargs)

    @property
    def full_name(self) -> str:
        aad = compute_field_aad("users", "full_name", self.id)
        return decrypt_field(self._full_name, associated_data=aad)

    @full_name.setter
    def full_name(self, value: str):
        if value is None:
            self._full_name = None
            return
        row_id = getattr(self, "id", None) or str(uuid.uuid4())
        self.id = row_id
        aad = compute_field_aad("users", "full_name", row_id)
        self._full_name = encrypt_field(str(value), associated_data=aad)

    @property
    def phone_number(self) -> Optional[str]:
        if not self._phone_number:
            return None
        aad = compute_field_aad("users", "phone_number", self.id)
        return decrypt_field(self._phone_number, associated_data=aad)

    @phone_number.setter
    def phone_number(self, value: Optional[str]):
        if not value:
            self._phone_number = None
            self.phone_blind_index = None
            return
        row_id = getattr(self, "id", None) or str(uuid.uuid4())
        self.id = row_id
        aad = compute_field_aad("users", "phone_number", row_id)
        self._phone_number = encrypt_field(str(value), associated_data=aad)
        self.phone_blind_index = compute_phone_blind_index(str(value))

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
