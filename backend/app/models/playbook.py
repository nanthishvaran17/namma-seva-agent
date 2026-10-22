from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Float, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class ServicePlaybookModel(Base):
    __tablename__ = "service_playbooks"

    service_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(255), nullable=False)
    description_en: Mapped[str] = mapped_column(Text, nullable=False)
    description_ta: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    portal_url: Mapped[str] = mapped_column(String(500), nullable=False)
    application_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Structured JSON data
    eligibility_rules: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    required_documents: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    optional_documents: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    fee: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    processing_time: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    application_steps: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    dependencies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    outputs: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    last_verified: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED", nullable=False, index=True) # DRAFT, NEEDS_VERIFICATION, VERIFIED, RETIRED
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    review_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    sources: Mapped[list["ServiceSourceModel"]] = relationship("ServiceSourceModel", back_populates="service", cascade="all, delete-orphan")

class ServiceSourceModel(Base):
    __tablename__ = "service_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[str] = mapped_column(String(100), ForeignKey("service_playbooks.service_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    retrieval_date: Mapped[str] = mapped_column(String(50), nullable=False)

    service: Mapped["ServicePlaybookModel"] = relationship("ServicePlaybookModel", back_populates="sources")
