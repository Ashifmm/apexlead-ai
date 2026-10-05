import logging
from app.db.base import Base
from app.db.session import engine
# Import all models here so that Base has them registered before create_all
from app.models.lead import Lead  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Initializes database schema and ensures all tables exist.
    Called automatically on FastAPI startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified and initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
