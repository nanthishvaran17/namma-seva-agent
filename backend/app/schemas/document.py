from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: Optional[str]
    doc_code: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    ocr_status: str
    extracted_fields: Dict[str, Any]
    is_verified_by_user: bool
    created_at: datetime

class DocumentCorrectionRequest(BaseModel):
    user_corrections: Dict[str, Any]
    is_verified: bool = True
