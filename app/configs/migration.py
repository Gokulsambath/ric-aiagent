from app.configs.database import Base, engine
from app.models.chat_models import ChatSession, ChatMessage
from app.models.widget_config_model import WidgetConfig

# ---- Create Database and Tables if not exists ----
def migrate():
    Base.metadata.create_all(bind = engine)