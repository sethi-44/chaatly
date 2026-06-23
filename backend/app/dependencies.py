import logging
from app.database import SessionLocal
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        raise
    finally:
        db.close()