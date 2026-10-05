import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.init_db import init_db
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agency_lead_system")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes database tables and starts autonomous agent scheduler on startup.
    """
    logger.info("Initializing database schema...")
    init_db()
    logger.info(f"Loaded configuration for environment: {settings.ENVIRONMENT}")
    if settings.is_gemini_configured:
        logger.info("Google Gemini API is configured and ready.")
    else:
        logger.warning("GEMINI_API_KEY is not set. Running in foundation mode (CRUD only).")

    # Start Autonomous Agent Scheduler
    try:
        from app.services.daily_scheduler import autonomous_agent
        autonomous_agent.start_scheduler()
        logger.info("Autonomous Agent APScheduler daemon started.")
    except Exception as e:
        logger.warning(f"Could not start autonomous agent scheduler: {e}")

    yield

    logger.info("Shutting down AI Web Agency Lead System backend.")
    try:
        from app.services.daily_scheduler import autonomous_agent
        autonomous_agent.stop_scheduler()
    except Exception:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend engine for AI-Powered Web Agency Lead Generation.\n\n"
        "### Capabilities:\n"
        "- **Lead Management & CRUD**: Track prospects, website status, contacts, and stages.\n"
        "- **Pipeline Analytics**: Real-time aggregation of high-opportunity leads.\n"
        "- **Gemini AI Ready**: Foundation in place for automated website audit, scoring, and outreach.\n"
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also expose /api/ai directly to satisfy exact /api/ai/test path
from app.api.v1.endpoints import ai
app.include_router(ai.router, prefix="/api/ai", tags=["AI Engine"])

# Mount static demo directory for Phase 6 Website Demo Generator
from fastapi.staticfiles import StaticFiles
from app.services.demo_generator import DEMOS_STORAGE_DIR
os.makedirs(DEMOS_STORAGE_DIR, exist_ok=True)
app.mount("/demos", StaticFiles(directory=DEMOS_STORAGE_DIR, html=True), name="demos")


@app.get("/", tags=["Root"])
def root():
    """Root info endpoint providing API status and documentation links."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR,
        "status": "online"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
