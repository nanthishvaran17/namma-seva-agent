from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ReminderCreate(BaseModel):
    task_id: Optional[str] = None
    title_en: str
    title_ta: str
    message_en: str
    message_ta: str
    scheduled_for: datetime
    channel: str = "IN_APP"

class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: Optional[str]
    title_en: str
    title_ta: str
    message_en: str
    message_ta: str
    scheduled_for: datetime
    status: str
    channel: str
    created_at: datetime
    sent_at: Optional[datetime]
