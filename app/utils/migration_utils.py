import logging
import os
from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run alembic upgrade head programmatically.
    This ensures the database schema is up-to-date on application startup.
    """
    try:
        logger.info("Starting database migration...")
        
        # Point to the alembic.ini file in the project root
        alembic_cfg = Config("alembic.ini")
        
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migration completed successfully.")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        # Depending on requirements, we might want to raise the error to crash the app
        # if the database is in an inconsistent state.
        # raise e
