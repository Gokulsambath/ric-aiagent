from typing import TypeVar, Generic
from sqlalchemy.orm import Session
from app.configs.database import DBSession

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model: type[T]):
        self.model = model

    def _get_db(self) -> Session:
        #Get a new database session
        return DBSession()