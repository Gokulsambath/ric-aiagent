from sqlalchemy import String, Column
from app.models.base_model import BaseModel

class Email(BaseModel):
    __tablename__ = "emails"
    email = Column(String(255)) # Column(JSON)
    subject = Column(String(500), index=True)
    message = Column(String(50000))
    name = Column(String(255))
    customer_email = Column(String(255), index=True)