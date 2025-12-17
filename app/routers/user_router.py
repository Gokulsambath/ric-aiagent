from fastapi import APIRouter, Depends
from app.schema.user_dto import User as UserDTO
from app.repository.user_repo import User as UserRepo
from app.services.user_serv import User as UserServ
from app.configs.dependencies import get_service_factory
#from app.auth.auth import authenticate_user

#userRoutes = APIRouter(prefix="/users", tags=["users"], dependencies = [Depends(authenticate_user)])
userRoutes = APIRouter(prefix="/users", tags=["users"])

user_service_dep = get_service_factory(UserServ, UserRepo)

# In FastAPI route --  Create new user:
@userRoutes.post("/")
def create_user(user: UserDTO, service: UserServ = Depends(user_service_dep)):
    result = service.createUser(user)
    return {"New User": result, "message": "User created successfully"}

# In FastAPI route --  Get user by ID:
@userRoutes.get("/{user_id}")
def read_user(user_id: int, service: UserServ = Depends(user_service_dep)):
    result = service.readUser(user_id)
    return result

# In FastAPI route --  Get all users:
@userRoutes.get("/", response_model=list[UserDTO])
def read_all_users(service: UserServ = Depends(user_service_dep), skip: int = 0, limit: int = 100):
    result = service.readUsers()
    return result

# In FastAPI route --  Update user by ID:
@userRoutes.put("/{user_id}", response_model=UserDTO)
def update_user(user_id: int, user: UserDTO, service: UserServ = Depends(user_service_dep)):
    result = service.updateUser(user_id, user)
    return result

# In FastAPI route --  Delete user by ID:
@userRoutes.post("/{user_id}")
def delete_user(user_id: int, service: UserServ = Depends(user_service_dep)):
    result = service.deleteUser(user_id)
    return result