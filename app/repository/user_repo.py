from app.schema.user_dto import User as UserDTO
from app.models.user_model import User as UserModel
from app.repository.base_repo import BaseRepository

class User(BaseRepository[UserModel]):
    def __init__(self):
        super().__init__(UserModel)

    def createUser(self, user: UserDTO):
        new_user = UserModel(name=user.name, email = user.email)
        db = self._get_db()
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # Refresh to get the new ID
        db.close()

        return new_user

    def readUser(self, user_id: int):
        db = self._get_db()
        usr : UserDTO = db.get(UserModel, user_id)
        db.close()

        return usr

    def readUsers(self):
        db = self._get_db()
        users = db.query(UserModel).all()
        all_users = [UserDTO(name=u.name, email=u.email).model_dump() for u in users]
        db.close()

        return all_users

    def updateUser(self, user_id: int, user: UserDTO):
        db = self._get_db()
        db_user = db.get(UserModel, user_id)
        if not db_user:
            return {"message": "User not found"}
        
        db_user.name = user.name
        db_user.email = user.email
        db.commit()
        db.refresh(db_user)
        db.close()

        return UserDTO(name=db_user.name, email=db_user.email).model_dump()

    def deleteUser(self, user_id: int):
        db = self._get_db()
        db_user = db.get(UserModel, user_id)
        if not db_user:
            return {"message": "User not found"}
        db.delete(db_user)
        db.commit()
        db.close()

        return {"message": "User deleted successfully"}