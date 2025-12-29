from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Unique session identifier. Pass null or 'new' to start a new session.")
    thread_id: Optional[str] = Field(None, description="Unique thread identifier within a session.")
    email: str = Field(..., description="User email for identification and history persistence")
    message: str = Field(..., description="Message content to send to the bot")
    provider: Optional[str] = Field("botpress", description="Chat provider to use (default: botpress)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context or metadata")
    is_new_chat: Optional[bool] = Field(False, description="Flag to force a new session or thread")

class ChatResponse(BaseModel):
    session_id: str
    thread_id: str
    role: str = "assistant"
    content: str
    provider: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatThreadResponse(BaseModel):
    id: int
    session_id: int
    title: Optional[str] = None
    created_at: Any
    updated_at: Any

class ThreadListResponse(BaseModel):
    session_id: int
    threads: List[ChatThreadResponse]
