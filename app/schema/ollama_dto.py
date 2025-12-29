from pydantic import BaseModel, Field
from datetime import  date, time
from typing import Optional, List

class Message(BaseModel):
    role: str  # "user", "assistant", or "system"
    content: str

class OllamaChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    stream: Optional[bool] = True
    session_id: Optional[str] = None
    thread_id: Optional[str] = None
    email: Optional[str] = None

class OllamaPrompt(BaseModel):
    model: Optional[str] = Field(default=None)
    prompt : str
    stream: bool = True
    clear_chat: bool = False
    session_id: Optional[str] = None
    thread_id: Optional[str] = None
    email: Optional[str] = None
    