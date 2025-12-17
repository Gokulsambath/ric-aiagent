from fastapi import APIRouter, Depends
from app.schema.email_dto import Email as EmailDTO
from app.schema.email_extra_dto import EmailExtra as EmailExtraDTO
from app.repository.email_repo import Email as EmailRepo
from app.services.email_serv import Email as EmailServ
from app.configs.dependencies import get_service_factory

emailRoutes = APIRouter(prefix="/emails", tags=["emails"])

email_service_dep = get_service_factory(EmailServ, EmailRepo)

@emailRoutes.post("/")
async def send_email(email: EmailDTO, service: EmailServ = Depends(email_service_dep)):
    result = service.sendEmail(email)
    return result

@emailRoutes.put("/")
async def send_email_extra(email: EmailExtraDTO, service: EmailServ = Depends(email_service_dep)):
    result = service.sendEmailExtras(email)
    return result
