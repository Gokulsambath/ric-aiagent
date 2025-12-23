from sqlalchemy.orm import Session
from app.models.widget_config_model import WidgetConfig
from typing import Optional

class WidgetConfigRepository:
    """Repository for widget configuration database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_secret_key(self, secret_key: str) -> Optional[WidgetConfig]:
        """Find widget config by secret key"""
        return self.db.query(WidgetConfig).filter(
            WidgetConfig.secret_key == secret_key,
            WidgetConfig.active == True
        ).first()
    
    def get_by_tenant_id(self, tenant_id: str) -> Optional[WidgetConfig]:
        """Find widget config by tenant ID"""
        return self.db.query(WidgetConfig).filter(
            WidgetConfig.tenant_id == tenant_id
        ).first()
    
    def create(self, tenant_id: str, tenant_name: str, secret_key: str, 
               allowed_origins: list = None) -> WidgetConfig:
        """Create new widget configuration"""
        widget_config = WidgetConfig(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            secret_key=secret_key,
            active=True
        )
        if allowed_origins:
            widget_config.set_allowed_origins(allowed_origins)
        
        self.db.add(widget_config)
        self.db.commit()
        self.db.refresh(widget_config)
        return widget_config
    
    def update_secret_key(self, tenant_id: str, new_secret_key: str) -> Optional[WidgetConfig]:
        """Update secret key for a tenant"""
        widget_config = self.get_by_tenant_id(tenant_id)
        if widget_config:
            widget_config.secret_key = new_secret_key
            self.db.commit()
            self.db.refresh(widget_config)
        return widget_config
    
    def deactivate(self, tenant_id: str) -> bool:
        """Deactivate a widget configuration"""
        widget_config = self.get_by_tenant_id(tenant_id)
        if widget_config:
            widget_config.active = False
            self.db.commit()
            return True
        return False
