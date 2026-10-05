import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.db.session import get_db
    from app.schemas.outreach import (
        IGDispatchBatchRequest,
        IGDispatchBatchResponse,
        IGOutreachStatusResponse
    )
    from app.services.instagram_outreach import instagram_outreach
except ImportError:
    from backend.app.db.session import get_db
    from backend.app.schemas.outreach import (
        IGDispatchBatchRequest,
        IGDispatchBatchResponse,
        IGOutreachStatusResponse
    )
    from backend.app.services.instagram_outreach import instagram_outreach

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/instagram/dispatch", response_model=IGDispatchBatchResponse, summary="Dispatch daily batch of Instagram DMs")
def dispatch_instagram_batch(
    req: IGDispatchBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers automated daily batch dispatch of queued Instagram Intent DMs.
    - Enforces configured daily limit (default 15/day).
    - Simulates humanized randomized delays.
    - Transitions dispatched leads to 'contacted' status.
    """
    try:
        result = instagram_outreach.dispatch_batch(db, daily_limit=req.daily_limit)
        return IGDispatchBatchResponse(
            message=result["message"],
            dispatched_count=result["dispatched_count"],
            daily_limit=result["daily_limit"],
            remaining_quota=result["remaining_quota"],
            dispatched_leads=result["dispatched_leads"]
        )
    except Exception as e:
        logger.error(f"Error in Instagram DM dispatch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispatch Instagram DM batch: {str(e)}"
        )


@router.get("/instagram/status", response_model=IGOutreachStatusResponse, summary="Get Instagram DM quota and queue status")
def get_instagram_outreach_status(
    daily_limit: int = 15,
    db: Session = Depends(get_db)
):
    """
    Returns current Instagram dispatch metrics:
    - Daily limit
    - Number dispatched today
    - Pending queue count
    - Remaining available quota
    """
    status_data = instagram_outreach.get_status(db, daily_limit=daily_limit)
    return IGOutreachStatusResponse(**status_data)


@router.get("/agent/status", summary="Get live Autonomous AI Agent background status and activity stream")
def get_autonomous_agent_status(db: Session = Depends(get_db)):
    """
    Provides real-time telemetry for the background autonomous agent:
    - Active status flag
    - Today's DM quota (sent vs limit)
    - Pending intent queue
    - Real-time live event stream
    """
    from app.services.daily_scheduler import autonomous_agent
    return autonomous_agent.get_status(db)


@router.post("/agent/toggle", summary="Toggle Autonomous Agent between Active and Paused")
def toggle_autonomous_agent(db: Session = Depends(get_db)):
    """
    Pause or resume autonomous background scraping and outreach cycles.
    """
    from app.services.daily_scheduler import autonomous_agent
    is_active = autonomous_agent.toggle()
    status_data = autonomous_agent.get_status(db)
    return {
        "message": f"Autonomous Agent is now {'ACTIVE' if is_active else 'PAUSED'}",
        "is_active": is_active,
        "status": status_data
    }


@router.post("/agent/harvest-now", summary="Trigger immediate autonomous intent harvest and dispatch")
def trigger_agent_harvest_now(db: Session = Depends(get_db)):
    """
    Triggers an immediate live Instagram intent harvest cycle.
    """
    from app.services.instagram_scanner import instagram_scanner
    from app.services.daily_scheduler import autonomous_agent
    leads = instagram_scanner.harvest_live_intent(db, max_leads=3)
    autonomous_agent._log_event("harvest", f"Manual trigger harvested {len(leads)} live leads.")
    return {
        "message": f"Harvested {len(leads)} fresh intent leads from live Instagram hashtags.",
        "harvested_count": len(leads),
        "status": autonomous_agent.get_status(db)
    }

