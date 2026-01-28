from app.services.email_providers.base import BaseEmailProvider
from app.services.email_providers.gmail import GmailProvider
from app.services.email_providers.sendgrid_provider import SendGridProvider
from app.configs.settings import settings

class EmailProviderFactory:
    @staticmethod
    def get_provider() -> BaseEmailProvider:
        provider_type = settings.mail.mail_provider.lower()
        
        if provider_type == "gmail":
            return GmailProvider()
        elif provider_type == "sendgrid":
            return SendGridProvider()
        else:
            # Default to Gmail if unknown or not specified
            print(f"⚠️ [EmailFactory] Unknown provider '{provider_type}', defaulting to Gmail.", flush=True)
            return GmailProvider()
