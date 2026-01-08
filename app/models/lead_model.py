from sqlalchemy import String, Column
from app.models.base_model import BaseModel

class Lead(BaseModel):
    __tablename__ = "leads"
    
    company_name = Column(String(255), nullable=False, index=True)
    contact_person_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    mobile_number = Column(String(50), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
