#---------------------- CREATE Tables -----------------------------------------------------
# Python entitiy classes creates/updates tables directly into the database and access them
#------------------------------------------------------------------------------------------
from sqlalchemy import String, Column
from app.models.base_model import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    name = Column(String(255), nullable = False, index = True)
    email = Column(String(100), nullable = True, unique = True)