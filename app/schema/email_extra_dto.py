from typing import Dict, Any

from app.schema.email_dto import Email as EmailDTO

class EmailExtra(EmailDTO):
    extra_params: Dict[str, Any] = {}  # holds unknown dynamic params

    class Config:
        extra = "allow"  # allows arbitrary top-level fields