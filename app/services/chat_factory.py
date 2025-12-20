from app.services.chat_strategy import ChatStrategy
from app.services.botpress_service import BotpressService
# from app.services.ollama_service import OllamaService # Future integration

class ChatFactory:
    @staticmethod
    def get_strategy(provider: str) -> ChatStrategy:
        if provider.lower() == "botpress":
            return BotpressService()
        # elif provider.lower() == "ollama":
        #     return OllamaService()
        else:
            raise ValueError(f"Unknown chat provider: {provider}")
