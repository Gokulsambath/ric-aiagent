from sqlalchemy import Column, String, Boolean, Text, Index
from app.models.base_model import BaseModel
import json

class WidgetConfig(BaseModel):
    __tablename__ = "widget_config"
    
    tenant_id = Column(String(50), unique=True, nullable=False, index=True)
    tenant_name = Column(String(255), nullable=False)
    secret_key = Column(String(255), nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False)
    bot_id = Column(String(50), nullable=True)  # Botpress Bot ID
    allowed_origins = Column(Text, nullable=False, default='["*"]')  # Stored as JSON string
    
    # Index for fast lookup by secret_key
    __table_args__ = (
        Index('idx_widget_secret_key', 'secret_key'),
    )
    
    def get_allowed_origins(self) -> list:
        """Parse allowed_origins JSON string to list"""
        try:
            return json.loads(self.allowed_origins)
        except:
            return ["*"]
    
    def set_allowed_origins(self, origins: list):
        """Set allowed_origins from list"""
        self.allowed_origins = json.dumps(origins)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "active": self.active,
            "allowed_origins": self.get_allowed_origins(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
