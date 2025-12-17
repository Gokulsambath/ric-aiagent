from sqlalchemy import String, Column
from app.models.base_model import BaseModel

class Customer(BaseModel):
    __tablename__ = "customers"

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    org_name = Column(String(255), nullable=True)
    address = Column(String(300), nullable=True)
    city = Column(String(255), nullable=True)
    country = Column(String(125), nullable=True)
    contact_number = Column(String(25), nullable=True)
    notes = Column(String(500))