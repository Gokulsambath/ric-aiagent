from fastapi import APIRouter, Depends
#from app.schema.customer_dto import Customer as CustomerDTO
from app.repository.customer_repo import Customer as customerRepo
from app.services.customer_serv import Customer as CustomerServ
from app.configs.dependencies import get_service_factory

customerRoutes = APIRouter(prefix="/customers", tags=["customers"])

customer_service_dep = get_service_factory(CustomerServ, customerRepo)

@customerRoutes.get("/{customer_id}")
def find_customer(customer_id: int, service: CustomerServ = Depends(customer_service_dep)):
    result = service.findCustomer(customer_id)
    return result
