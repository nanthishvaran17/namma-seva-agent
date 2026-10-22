from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base

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
    
    # OCR & Intelligence
    ocr_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, PROCESSED, FAILED
    extracted_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_verified_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_corrections: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="documents")
    task: Mapped["UserTaskModel"] = relationship("UserTaskModel", back_populates="documents")
