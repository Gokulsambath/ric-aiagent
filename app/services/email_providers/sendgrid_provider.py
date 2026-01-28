import httpx
from typing import Dict, Any
from app.services.email_providers.base import BaseEmailProvider
from app.schema.email_dto import Email as EmailDTO
from app.configs.settings import settings

class SendGridProvider(BaseEmailProvider):
    async def send_email(self, email: EmailDTO, extras: str = "") -> Dict[str, Any]:
        try:
            print(f"📧 [SendGridProvider] Preparing to send email...", flush=True)
            
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
                    print(f"✅ [SendGridProvider] Email sent successfully (Status: {response.status_code})", flush=True)
                    return {"message": "Email sent successfully"}
                else:
                    print(f"❌ [SendGridProvider] API Error: {response.status_code} - {response.text}", flush=True)
                    raise Exception(f"SendGrid API Error: {response.text}")

        except Exception as e:
            print(f"❌ [SendGridProvider] FAILED to send email: {str(e)}", flush=True)
            raise e
