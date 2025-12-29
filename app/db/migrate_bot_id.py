from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_bot_id():
    """
    Migration script to:
    1. Add bot_id column to widget_config table if it doesn't exist.
    2. Update existing records with correct bot_id.
    """
    # Create local engine from Env functionality to bypass potential app config issues
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not found in environment!")
        return

    logger.info(f"Using DATABASE_URL: {db_url}")
    engine = create_engine(db_url)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        # Debug: Print connection info
        logger.info(f"Connecting to DB URL: {engine.url}")
        
        logger.info("Starting migration: Add bot_id to widget_config")
        
        # 1. Add column if not exists
        # Note: We use raw SQL to avoid model validation issues before schema update
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE widget_config ADD COLUMN IF NOT EXISTS bot_id VARCHAR(50)"))
                conn.commit()
            logger.info("✅ Column 'bot_id' added (or already exists).")
        except Exception as e:
            logger.warning(f"⚠️ Error adding column (might already exist): {e}")

        # 2. Update Data
        updates = [
            {"tenant_id": "ric-tenant", "bot_id": "ric"},
            {"tenant_id": "cms-tenant", "bot_id": "ric-cms"}
        ]
        
        for update in updates:
            sql = text("UPDATE widget_config SET bot_id = :bot_id WHERE tenant_id = :tenant_id")
            session.execute(sql, update)
            logger.info(f"Updated {update['tenant_id']} -> bot_id: {update['bot_id']}")
            
        session.commit()
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_bot_id()
