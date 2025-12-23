from app.configs.database import Base, engine
from app.models.chat_models import ChatSession, ChatMessage
from app.models.widget_config_model import WidgetConfig
from app.models.user_model import User
from app.models.customer_model import Customer
from app.models.demo_model import Demo
from app.models.email_model import Email
from app.models.ollama_model import OllamaAgent

# ---- Create Database and Tables if not exists ----
def migrate():
    Base.metadata.create_all(bind = engine)