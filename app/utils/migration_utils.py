import logging
import os
from datetime import datetime
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime import migration

logger = logging.getLogger(__name__)

def check_pending_migrations():
    """
    Check if there are any pending model changes that need migration.
    Returns True if new migrations are needed.
    """
    try:
        alembic_cfg = Config("alembic.ini")
        # Use check command to detect pending changes
        # This will raise SystemExit if there are pending migrations
        command.check(alembic_cfg)
        return False
    except SystemExit:
        # SystemExit is raised when there are pending migrations
        return True
    except Exception as e:
        logger.warning(f"Could not check migration status: {e}")
        return False

def generate_migration_if_needed():
    """
    Generate a new migration if model changes are detected.
    """
    if check_pending_migrations():
        try:
            logger.info("Detected model changes, generating new migration...")
            alembic_cfg = Config("alembic.ini")
            
            # Generate migration with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            message = f"Auto-generated migration {timestamp}"
            
            command.revision(alembic_cfg, autogenerate=True, message=message)
            logger.info(f"Generated new migration: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate migration: {e}")
            return False
    return False

def run_migrations():
    """
    Run alembic upgrade head programmatically.
    This ensures the database schema is up-to-date on application startup.
    Now includes automatic migration generation for model changes.
    """
    try:
        logger.info("Starting database migration process...")
        
        # Point to the alembic.ini file in the project root
        alembic_cfg = Config("alembic.ini")
        
        # Check and generate new migrations if needed
        if generate_migration_if_needed():
            logger.info("New migration generated, proceeding with upgrade...")
        
        # Run all pending migrations
        command.upgrade(alembic_cfg, "head")
        
        # Verify migration completed successfully
        logger.info("Verifying migration status...")
        if not check_pending_migrations():
            logger.info("All migrations applied successfully. Database is up-to-date.")
        else:
            logger.warning("Some migrations may still be pending after upgrade.")
        
        # Seed initial data if needed
        from app.utils.seed_widget_config import seed_widget_config
        seed_widget_config()
        
        logger.info("Database migration and seeding completed successfully.")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        # Depending on requirements, we might want to raise the error to crash the app
        # if the database is in an inconsistent state.
        # raise e
