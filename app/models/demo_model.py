from sqlalchemy import String, Column, Integer, Date, Time, JSON #ARRAY
from app.models.base_model import BaseModel

class Demo(BaseModel):
    __tablename__ = "demos"

    title = Column(String(255), nullable=True)
    demo_date = Column(Date, nullable=True)
    demo_time = Column(Time, nullable=True)
    notes = Column(String(5000), nullable=True)
    participants = Column(JSON, nullable=True)
    presenter = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)

    customer_id = Column(Integer, nullable=False)