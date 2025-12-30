from abc import ABC, abstractmethod
from app.schema.chat_schema import ChatResponse

class ChatStrategy(ABC):
    @abstractmethod
    async def send_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None) -> ChatResponse:
        """
        Send a message to the chat provider and return the response.
        """
        pass
    
    @abstractmethod
    async def stream_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None):
        """
        Stream a message to the chat provider and yield chunks.
        """
        pass
