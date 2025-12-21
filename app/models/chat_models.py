#---------------------- CREATE Tables -----------------------------------------------------
# Python entitiy classes creates/updates tables directly into the database and access them
#------------------------------------------------------------------------------------------
from sqlalchemy import String, Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel
from app.models.user_model import User

class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", backref="chat_sessions")
    messages = relationship("ChatMessage", backref="session", cascade="all, delete-orphan")

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Relationships
    # session is defined in ChatSession backref
