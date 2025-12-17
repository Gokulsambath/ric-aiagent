from pydantic import BaseModel

class Customer(BaseModel):
    name: str
    email: str
    org_name: str
    address: str
    city: str
    country: str
    contact_number: str
    notes: str