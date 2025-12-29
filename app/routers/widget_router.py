from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.configs.database import get_db
from app.repository.widget_config_repo import WidgetConfigRepository
from typing import Dict

widgetRoutes = APIRouter(prefix="/api/widget", tags=["widget"])

@widgetRoutes.get("/validate")
async def validate_widget_key(
    key: str,
    widgetId: str = None,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Validate widget secret key and return tenant configuration.
    
    Args:
        key: Widget secret key
        widgetId: Optional widget (tenant) ID
        
    Returns:
        Tenant configuration if valid
        
    Raises:
        403: If key is invalid or tenant is inactive
    """
    if not key and not widgetId:
        raise HTTPException(status_code=400, detail="Missing API Key or Widget ID")
    
    # Find widget config
    repo = WidgetConfigRepository(db)
    widget_config = None
    
    # Prioritize widgetId (tenant_id) if provided
    if widgetId:
        widget_config = repo.get_by_tenant_id(widgetId)
        
    # Fallback to key if widgetId lookup failed or wasn't provided
    if not widget_config and key:
        widget_config = repo.get_by_secret_key(key)
    
    if not widget_config:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    if not widget_config.active:
        raise HTTPException(status_code=403, detail="Tenant access revoked")
    
    # Return configuration
    return {
        "valid": True,
        "tenant": {
            "id": widget_config.tenant_id,
            "name": widget_config.tenant_name
        },
        "config": {
            "theme": "light",
            "primaryColor": "#2563eb",
            "position": "bottom-right",
            "title": f"{widget_config.tenant_name} Assistant",
            "allowedOrigins": widget_config.get_allowed_origins()
        }
    }
