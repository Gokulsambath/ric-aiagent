from typing import Dict, Any
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from app.services.email_providers.base import BaseEmailProvider
from app.schema.email_dto import Email as EmailDTO
from app.configs.settings import settings

class GmailProvider(BaseEmailProvider):
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail.mail_username,
            MAIL_PASSWORD=settings.mail.mail_password,
            MAIL_FROM=settings.mail.mail_from,
            MAIL_PORT=settings.mail.mail_port,
            MAIL_SERVER=settings.mail.mail_server,
            MAIL_STARTTLS=settings.mail.mail_starttls,
            MAIL_SSL_TLS=settings.mail.mail_ssl_tls,
            USE_CREDENTIALS=settings.mail.use_credentials,
            VALIDATE_CERTS=settings.mail.validate_certs
        )

    async def send_email(self, email: EmailDTO, extras: str = "") -> Dict[str, Any]:
        try:
            print(f"📧 [GmailProvider] Preparing to send email...", flush=True)
            
            email_body = f"""
            {email.message}<br/><br/>
            --------<br/>
            Customer Name: {email.name}<br/>
            Customer Email: {email.customer_email}<br/>
            {extras}<br/>
            --------
            """

            message = MessageSchema(
                subject=email.subject,
                recipients=email.email,  # List of recipients
                body=email_body,
                subtype="html"
            )

            fm = FastMail(self.conf)
            await fm.send_message(message)
            
            print(f"✅ [GmailProvider] Email sent successfully", flush=True)
            return {"message": "Email sent successfully"}

        except Exception as e:
            print(f"❌ [GmailProvider] FAILED to send email: {str(e)}", flush=True)
            raise e
