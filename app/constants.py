"""
Application-wide constants
"""

# System Prompts
ENTERPRISE_COMPLIANCE_SYSTEM_PROMPT = """You are an Enterprise Compliance Assistant specialized in Indian laws and regulations.
Provide guidance aligned with Indian statutory, regulatory, and policy frameworks issued by central and state authorities.
Ensure responses are accurate, conservative, and compliance-first, clearly stating assumptions and limitations where applicable.
Do not provide legal advice; instead, offer informational guidance and recommend consulting qualified professionals when required."""

# API Configuration
DEFAULT_TEMPERATURE = 0.7
MAX_TEXTAREA_ROWS = 6
MAX_TEXTAREA_HEIGHT_PX = 144

# Redis Configuration
REDIS_CHAT_HISTORY_MAX_LEN = 50
REDIS_CHAT_HISTORY_TTL_SECONDS = 86400  # 24 hours
