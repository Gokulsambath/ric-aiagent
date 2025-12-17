#OllamaAgent

from app.repository.base_repo import BaseRepository
from app.models.ollama_model import OllamaAgent as OllamaModel
from app.schema.ollama_dto import OllamaPrompt as OllamaDTO, Message as MessageDTO, OllamaChatRequest as ChatRequestDTO

from abc import ABC, abstractmethod

from typing import AsyncGenerator, Dict, Any, List

class OllamaStreamChat(BaseRepository[OllamaModel]):
    def __init__(self):
        super().__init__(OllamaModel)

"""
class OllamaRepository(ABC):
    @abstractmethod
    async def stream_chat(
        self, 
        messages: List[MessageDTO], 
        model: str,
        session
    ) -> AsyncGenerator[str, None]:
        pass

class OllamaStreamChat(OllamaRepository):
    #Implementation for Ollama chat streaming
    pass
"""