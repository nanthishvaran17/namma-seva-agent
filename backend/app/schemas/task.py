from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime

class TaskCreate(BaseModel):
    service_id: str
    target_deadline: Optional[datetime] = None

class TaskStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None
    step_index: Optional[int] = None
    form_data: Optional[Dict[str, Any]] = None
    submission_evidence: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_id: str
    status: str
    current_step_index: int
    action_plan: Dict[str, Any]
    form_data: Dict[str, Any]
    submission_evidence: Dict[str, Any]
    next_action_en: Optional[str]
    next_action_ta: Optional[str]
    target_deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime
