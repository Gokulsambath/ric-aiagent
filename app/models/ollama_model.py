from app.models.base_model import BaseModel
from sqlalchemy import String, Column

class OllamaAgent(BaseModel):
    __tablename__ = "aiagents"
    prompt = Column(String(250000)) # Column(JSON)