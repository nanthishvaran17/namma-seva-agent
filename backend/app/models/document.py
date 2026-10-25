from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base
import json
from typing import Any, Dict
from backend.app.core.crypto import (
    encrypt_field,
    decrypt_field,
    compute_field_aad
)

def utcnow():
    return datetime.now(timezone.utc)

class UserDocumentModel(Base):
    __tablename__ = "user_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    doc_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. "photo", "income_proof", "community_certificate"
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # OCR & Intelligence (Encrypted at rest with dedicated AES-256 key + AAD binding)
    ocr_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, PROCESSED, FAILED
    _extracted_fields: Mapped[str] = mapped_column("extracted_fields", Text, default="{}", nullable=False)
    is_verified_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    _user_corrections: Mapped[str] = mapped_column("user_corrections", Text, default="{}", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        self.id = kwargs["id"]
        super().__init__(**kwargs)

    @property
    def extracted_fields(self) -> Dict[str, Any]:
        if not self._extracted_fields:
            return {}
        aad = compute_field_aad("user_documents", "extracted_fields", self.id)
        decrypted = decrypt_field(self._extracted_fields, associated_data=aad)
        if not decrypted:
            return {}
        try:
            return json.loads(decrypted) if isinstance(decrypted, str) else decrypted
        except Exception:
            return {}

    @extracted_fields.setter
    def extracted_fields(self, value: Any):
        row_id = getattr(self, "id", None) or str(uuid.uuid4())
        self.id = row_id
        payload_str = json.dumps(value) if not isinstance(value, str) else value
        aad = compute_field_aad("user_documents", "extracted_fields", row_id)
        self._extracted_fields = encrypt_field(payload_str, associated_data=aad)

    @property
    def user_corrections(self) -> Dict[str, Any]:
        if not self._user_corrections:
            return {}
        aad = compute_field_aad("user_documents", "user_corrections", self.id)
        decrypted = decrypt_field(self._user_corrections, associated_data=aad)
        if not decrypted:
            return {}
        try:
            return json.loads(decrypted) if isinstance(decrypted, str) else decrypted
        except Exception:
            return {}

    @user_corrections.setter
    def user_corrections(self, value: Any):
        row_id = getattr(self, "id", None) or str(uuid.uuid4())
        self.id = row_id
        payload_str = json.dumps(value) if not isinstance(value, str) else value
        aad = compute_field_aad("user_documents", "user_corrections", row_id)
        self._user_corrections = encrypt_field(payload_str, associated_data=aad)

    user: Mapped["User"] = relationship("User", back_populates="documents")
    task: Mapped["UserTaskModel"] = relationship("UserTaskModel", back_populates="documents")
