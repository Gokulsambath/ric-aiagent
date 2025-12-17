from sqlalchemy import Column, Integer, DateTime, func
from app.configs.database import Base

class BaseModel(Base):
    __abstract__ = True  # ensures no table is created for this class
    
    id = Column(Integer, primary_key = True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
