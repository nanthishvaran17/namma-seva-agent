from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    preferred_language: str = "ta"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ConsentCreate(BaseModel):
    consent_purpose: str
    is_granted: bool = True

class ConsentResponse(BaseModel):
    id: str
    consent_purpose: str
    is_granted: bool
    granted_at: datetime
