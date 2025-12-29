#---------------------- CREATE Tables -----------------------------------------------------
# Python entitiy classes creates/updates tables directly into the database and access them
#------------------------------------------------------------------------------------------
from sqlalchemy import String, Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel
from app.models.user_model import User

class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", backref="chat_sessions")
    threads = relationship("ChatThread", backref="session", cascade="all, delete-orphan")

class ChatThread(BaseModel):
    __tablename__ = "chat_threads"
    
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True, index=True)
    
    # Relationships
    messages = relationship("ChatMessage", backref="thread", cascade="all, delete-orphan")

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Relationships
    # thread is defined in ChatThread backref
