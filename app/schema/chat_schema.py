from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Unique session identifier. Pass null or 'new' to start a new session.")
    thread_id: Optional[str] = Field(None, description="Unique thread identifier within a session.")
    email: str = Field(..., description="User email for identification and history persistence")
    message: str = Field(..., description="Message content to send to the bot")
    provider: Optional[str] = Field("botpress", description="Chat provider to use (default: botpress)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context or metadata")
    is_new_chat: Optional[bool] = Field(False, description="Flag to force a new session or thread")
    app_id: Optional[str] = Field(None, description="App ID or Widget ID (used to identify bot configuration)")
    user_name: Optional[str] = Field(None, description="User's full name (for CMS bot)")
    user_name: Optional[str] = Field(None, description="User's full name (for CMS bot)")
    user_designation: Optional[str] = Field(None, description="User's designation/role (for CMS bot)")
    is_support_ticket: Optional[bool] = Field(False, description="Flag indicating if the message is a support ticket")

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
    
    model_config = ConfigDict(from_attributes=True)

class ThreadListResponse(BaseModel):
    session_id: int
    threads: List[ChatThreadResponse]
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessageResponse(BaseModel):
    id: int
    thread_id: int
    role: str
    content: str
    created_at: Any
    updated_at: Any
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdateRequest(BaseModel):
    current_email: str
    new_email: str
    name: Optional[str] = None
