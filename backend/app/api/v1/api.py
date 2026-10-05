from fastapi import APIRouter
from app.api.v1.endpoints import leads, health, ai, outreach

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Engine"])
api_router.include_router(outreach.router, prefix="/outreach", tags=["Outreach Engine"])

