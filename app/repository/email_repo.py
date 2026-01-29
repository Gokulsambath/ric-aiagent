from app.repository.base_repo import BaseRepository
from app.models.email_model import Email as EmailModel
from app.schema.email_dto import Email as EmailDTO
from app.schema.email_extra_dto import EmailExtra as EmailExtraDTO
from app.mappers.email_mapper import to_email_dto, extra_params_to_string

from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
import json
import asyncio
import httpx
from app.configs.settings import settings

class Email(BaseRepository[EmailModel]):
    def __init__(self):
        super().__init__(EmailModel)

    def emailConfig(self):
        conf = ConnectionConfig(
            MAIL_USERNAME = settings.mail.mail_username,
            MAIL_PASSWORD = settings.mail.mail_password,
            MAIL_FROM = settings.mail.mail_from,
            MAIL_PORT = settings.mail.mail_port,
            MAIL_SERVER = settings.mail.mail_server,
            MAIL_STARTTLS = settings.mail.mail_starttls,
            MAIL_SSL_TLS = settings.mail.mail_ssl_tls,
            USE_CREDENTIALS = settings.mail.use_credentials,
            VALIDATE_CERTS = settings.mail.validate_certs
        )
        return conf

    async def sendEmail(self, email: EmailDTO, extras: str = ""):
        try:
            # Use the configured provider via Factory
            from app.services.email_providers.factory import EmailProviderFactory
            provider = EmailProviderFactory.get_provider()
            return await provider.send_email(email, extras)

        except Exception as e:
            print(f"❌ [EmailRepo] FAILED to send email: {str(e)}", flush=True)
            import traceback
            print(traceback.format_exc(), flush=True)
            return {"message": "Email failed to send"}
    
    def sendEmailBackground(self, email: EmailDTO):
        task = asyncio.create_task(self.sendEmail(email))
        return {"message": "Email queued in background"}
    
    def sendEmailExtraBackground(self, email: EmailExtraDTO):
        extra_params: str = extra_params_to_string(email.extra_params)
        extra_params = extra_params
        email_dto: EmailDTO = to_email_dto(email)
        asyncio.create_task(self.sendEmail(email_dto, extras = extra_params))
        return {"message": "Email sent successfully"}