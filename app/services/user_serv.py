from app.schema.user_dto import User as UserDTO
from app.repository.user_repo import User as UserRepo

class User:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    def createUser(self, user: UserDTO):
        new_user = self.repo.createUser(user)
        return new_user

    def readUser(self, user_id: int):
        usr = self.repo.readUser(user_id)
        return usr

    def readUsers(self):
        all_users = self.repo.readUsers()
        return all_users

    def updateUser(self, user_id: int, user: UserDTO):
        upd_user = self.repo.updateUser(user_id, user)
        return upd_user

    def deleteUser(self, user_id: int):
        del_user = self.repo.deleteUser(user_id)
        return del_user