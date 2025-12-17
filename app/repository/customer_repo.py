from app.schema.customer_dto import Customer as CustomerDTO
from app.models.customer_model import Customer as CustomerModel
from app.repository.base_repo import BaseRepository

class Customer(BaseRepository[CustomerModel]):
    def __init__(self):
        super().__init__(CustomerModel)

    def findCustomer(self, customer_id: int):
        db = self._get_db()
        customer : CustomerDTO = db.get(CustomerModel, customer_id)
        db.close()

        return customer