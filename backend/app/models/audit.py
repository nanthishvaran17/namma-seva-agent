from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. "USER_LOGIN", "DATA_EXPORT", "DATA_DELETION", "DOC_UPLOAD"
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
