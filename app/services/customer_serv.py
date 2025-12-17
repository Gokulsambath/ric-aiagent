#from app.schema.customer_dto import Customer as CustomerDTO
from app.repository.customer_repo import Customer as CustomerRepo

class Customer:
    def __init__(self, repo: CustomerRepo):
        self.repo = repo

    def findCustomer(self, customer_id: int):
        customer = self.repo.findCustomer(customer_id)
        return customer