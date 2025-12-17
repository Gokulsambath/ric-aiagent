from pydantic import BaseModel
from typing import List


class APIKeyConfig(BaseModel):
    name: str
    key: str
    permissions: List[str]
    enabled: bool
