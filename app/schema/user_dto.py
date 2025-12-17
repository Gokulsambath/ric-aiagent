#---------------------- PyDantic Models ---------------------------------------
# You cant user entities directly in FastAPI routes, so we use Pydantic models
#------------------------------------------------------------------------------
from pydantic import BaseModel

class User(BaseModel):
    name : str
    email : str
#------------------------------------------------------------------------------