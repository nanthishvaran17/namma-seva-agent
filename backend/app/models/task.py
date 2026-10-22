from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class UserTaskModel(Base):
    __tablename__ = "user_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id: Mapped[str] = mapped_column(String(100), ForeignKey("service_playbooks.service_id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False, index=True)
    
    # State data
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    action_plan: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    form_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    submission_evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    next_action_en: Mapped[str] = mapped_column(String(500), nullable=True)
    next_action_ta: Mapped[str] = mapped_column(String(500), nullable=True)
    target_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tasks")
    service: Mapped["ServicePlaybookModel"] = relationship("ServicePlaybookModel")
    events: Mapped[list["TaskEventModel"]] = relationship("TaskEventModel", back_populates="task", cascade="all, delete-orphan")
    documents: Mapped[list["UserDocumentModel"]] = relationship("UserDocumentModel", back_populates="task", cascade="all, delete-orphan")
    reminders: Mapped[list["ReminderModel"]] = relationship("ReminderModel", back_populates="task", cascade="all, delete-orphan")

class TaskEventModel(Base):
    __tablename__ = "task_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status: Mapped[str] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    task: Mapped["UserTaskModel"] = relationship("UserTaskModel", back_populates="events")
