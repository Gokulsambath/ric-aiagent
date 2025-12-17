from pydantic import BaseModel, EmailStr, field_validator
from email_validator import validate_email, EmailNotValidError

import bleach
from bleach.css_sanitizer import CSSSanitizer
import base64
import binascii
import re
ALLOWED_TAGS = [ "p", "br", "span", "div", "ul", "ol", "li", "strong", "em", "u", "h1", "h2", "h3", "blockquote" ]
ALLOWED_ATTRIBUTES = { "*": ["style", "class", "align"], "a": ["href", "title", "target"], "img": ["src", "alt", "title"] }
ALLOWED_STYLES = [ "color", "font-weight", "font-style", "text-decoration", "background-color", "font-size", "text-align", "line-height" ]

css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_STYLES)

#--------------------------------------------------------------------------
#         Code related to finding whether text is encoded or not
#--------------------------------------------------------------------------
def is_base64_encoded(s: str) -> bool:
    """Check if a string is Base64 encoded."""
    # Base64 pattern: alphanumeric, '+', '/', and '=' padding (0-2 at end)
    pattern = r'^[A-Za-z0-9+/]+={0,2}$'
    
    # Check if string matches pattern and has valid length
    if not re.fullmatch(pattern, s):
        return False
    
    # Check length is multiple of 4 (with padding)
    if len(s) % 4 != 0:
        return False
    
    try:
        # Try decoding to validate
        base64.b64decode(s, validate=True)
        return True
    except binascii.Error:
        return False

def decode_base64_param(param: str) -> str:
    """Decode if Base64 encoded, otherwise return original."""
    if is_base64_encoded(param):
        try:
            decoded_bytes = base64.b64decode(param)
            return decoded_bytes.decode('utf-8')
        except (binascii.Error, UnicodeDecodeError):
            return param
    return param

#--------------------------------------------------------------------------

class Email(BaseModel):
    email: list[EmailStr]
    subject: str
    message: str
    name: str | None = "No Name"
    customer_email: EmailStr | None = "no-reply@gmail.com"

    @field_validator("message", mode="before")
    def email_content_html(cls, value):
        #decode text if it is encoded
        value = decode_base64_param(value)
        # Sanitize HTML
        safe_html = bleach.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            #styles=ALLOWED_STYLES,
            css_sanitizer= css_sanitizer,
            strip=True
        )
        return safe_html
    
    @field_validator("email")
    @classmethod
    def validate_real_email(cls, values):
        validated = []
        for value in values:
            try:
                validate_email(value, check_deliverability=True)  # DNS check
            except EmailNotValidError as e:
                raise ValueError(str(e))
            validated.append(value)
        return validated
    
    @field_validator("name", mode="before")
    def set_default_name(cls, value):
        return value or "No Name"
    
    @field_validator("customer_email", mode="before")
    def set_default_email(cls, value):
        if not value:  # catches None, "", etc.
            return "no-reply@gmail.com"
        return value
    
    @field_validator("customer_email")
    def validate_customer_email(cls, value):
        try:
            validate_email(value, check_deliverability=True)  # DNS check
        except EmailNotValidError as e:
            raise ValueError(str(e))
        return value