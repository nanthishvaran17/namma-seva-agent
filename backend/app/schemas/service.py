from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ServiceSource(BaseModel):
    title: str
    publisher: str
    url: str
    retrieval_date: str

class ServiceFee(BaseModel):
    amount_inr: float
    is_free: bool
    verified_description: str

class ProcessingTime(BaseModel):
    working_days: int
    description_en: str
    description_ta: str

class RequiredDoc(BaseModel):
    doc_code: str
    name_en: str
    name_ta: str
    description: Optional[str] = None
    mandatory: bool = True
    acceptable_formats: Optional[List[str]] = None

class ServiceListItem(BaseModel):
    service_id: str
    name_en: str
    name_ta: str
    description_en: str
    description_ta: str
    department: str
    category: str
    portal_url: str
    fee: ServiceFee
    processing_time: ProcessingTime
    dependencies: List[str]
    verification_status: str
    verified_by: Optional[str] = None
    last_verified: Optional[str] = None

class EligibilityCheckRequest(BaseModel):
    service_id: str
    user_profile: Dict[str, Any]

class ActionPlanRequest(BaseModel):
    target_service_id: str
    user_completed_services: Optional[List[str]] = None
    user_available_documents: Optional[List[str]] = None
