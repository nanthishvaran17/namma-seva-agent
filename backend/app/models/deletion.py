from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class DeletionReceiptModel(Base):
    """
    Cryptographically verifiable, non-PII deletion receipt under DPDP Act 2023 Sec 12.
    Retains minimal proof of erasure without retaining any citizen personal data.
    """
    __tablename__ = "deletion_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    request_channel: Mapped[str] = mapped_column(String(32), default="WEB", nullable=False)
    consent_withdrawal_recorded: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    consent_withdrawal_evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    receipt_signature: Mapped[str] = mapped_column(String(64), nullable=False)
