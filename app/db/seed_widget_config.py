"""
Seed script to populate initial widget configuration data.

Run this script after running migrations to set up the default widget keys.
"""

from app.models.widget_config_model import WidgetConfig
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def seed_widget_config():
    """Seed initial widget configuration data"""
    # Create local engine from Env functionality to bypass potential app config issues
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in environment!")
        return

    print(f"Using DATABASE_URL for seed: {db_url}")
    engine = create_engine(db_url)
    DBSession = sessionmaker(bind=engine)
    db = DBSession()
    
    try:
        # Check if data already exists
        existing = db.query(WidgetConfig).first()
        if existing:
            print("Widget config data already exists. Skipping seed.")
            return
        
        # Define initial widget configurations
        configs = [
            {
                "tenant_id": "ric-tenant",
                "tenant_name": "Ricago Website",
                "secret_key": "Key1",
                "active": True,
                "bot_id": "ric",
                "allowed_origins": json.dumps(["*"])
            },
            {
                "tenant_id": "cms-tenant",
                "tenant_name": "Client CMS",
                "secret_key": "KeyCms",
                "active": True,
                "bot_id": "ric-cms",
                "allowed_origins": json.dumps(["*"])
            },
            {
                "tenant_id": "apphub-tenant",
                "tenant_name": "App Hub",
                "secret_key": "KeyAppHub",
                "active": False,  # Inactive by default
                "bot_id": None,
                "allowed_origins": json.dumps(["*"])
            }
        ]
        
        # Insert configurations
        for config_data in configs:
            widget_config = WidgetConfig(**config_data)
            db.add(widget_config)
        
        db.commit()
        print(f"✅ Successfully seeded {len(configs)} widget configurations")
        
        # Print summary
        all_configs = db.query(WidgetConfig).all()
        for config in all_configs:
            status = "✓ Active" if config.active else "✗ Inactive"
            print(f"  - {config.tenant_name} ({config.tenant_id}): {status}")
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding widget config: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting widget config seed...")
    seed_widget_config()
    print("Seed complete!")
