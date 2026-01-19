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
            print(f"📧 [EmailRepo] Preparing to send email via SendGrid API...", flush=True)
            print(f"   - To: {email.email}", flush=True)
            print(f"   - Subject: {email.subject}", flush=True)
            
            # Prepare content
            email_body = email.message + "<br/><br/>" + "--------<br/>" + "Customer Name: " + email.name + "<br/>" + "Customer Email: " + email.customer_email + "<br/>" + extras + "<br/>--------"
            
            # Construct SendGrid payload
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": r} for r in email.email],
                        "subject": email.subject
                    }
                ],
                "from": {
                    "email": settings.mail.mail_from,
                    "name": "RIC Agent"
                },
                "content": [
                    {
                        "type": "text/html",
                        "value": email_body
                    }
                ]
            }

            headers = {
                "Authorization": f"Bearer {settings.mail.mail_password}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201, 202]:
                    print(f"✅ [EmailRepo] Email sent successfully via API (Status: {response.status_code})", flush=True)
                    return {"message": "Email sent successfully"}
                else:
                    print(f"❌ [EmailRepo] SendGrid API Error: {response.status_code} - {response.text}", flush=True)
                    raise Exception(f"SendGrid API Error: {response.text}")

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