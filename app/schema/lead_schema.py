from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LeadCreateRequest(BaseModel):
    company_name: str
    contact_person_name: str
    email: EmailStr
    mobile_number: Optional[str] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    company_name: str
    contact_person_name: str
    email: str
    mobile_number: Optional[str] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
