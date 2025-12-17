from app.schema.email_dto import Email as EmailDTO
from app.schema.email_extra_dto import EmailExtra as EmailExtraDTO

from typing import Dict, Any

def to_email_dto(extra_dto: EmailExtraDTO) -> EmailDTO:
    allowed_keys = EmailDTO.model_fields.keys()  # use model_fields in Pydantic v2
    filtered_data = {k: getattr(extra_dto, k) for k in allowed_keys}
    return EmailDTO(**filtered_data)

def extra_params_to_string(extra_params: Dict[str, Any]) -> str:
    if not extra_params:
        return ""
    # Convert each key-value pair to "key: value" and join with separator
    return " | ".join(f"{k}: {v}" for k, v in extra_params.items())