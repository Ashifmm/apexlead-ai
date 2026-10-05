from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("", summary="System Health & Diagnostic Check")
def health_check(db: Session = Depends(get_db)):
    """
    Returns system status, database connectivity, and configuration flags.
    Useful for health monitors and debugging.
    """
    # Check Database
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_ok,
        "gemini_api_configured": settings.is_gemini_configured,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
