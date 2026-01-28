from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from app.schema.email_dto import Email as EmailDTO

class BaseEmailProvider(ABC):
    @abstractmethod
    async def send_email(self, email: EmailDTO, extras: str = "") -> Dict[str, Any]:
        """Send an email using the provider."""
        pass
