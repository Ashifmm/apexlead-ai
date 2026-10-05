import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.crud_lead import crud_lead
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadOut,
    LeadListResponse,
    LeadStats,
    LeadStatusUpdateRequest
)
from app.schemas.outreach import (
    IGScanRequest,
    IGScanResponse
)
from app.services.instagram_scanner import instagram_scanner
from app.services.instagram_outreach import instagram_outreach
from app.services.gemini_service import gemini_service
from app.models.lead import Lead

router = APIRouter()


@router.get("", response_model=LeadListResponse, summary="List leads with search, filters, and pagination")
def list_leads(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, handle, comment, industry, location, or notes"),
    status: Optional[str] = Query(None, description="Filter by status ('Intent Detected', 'DM Drafted', 'DM Queued', 'Sent')"),
    has_website: Optional[bool] = Query(None, description="Filter by presence of website (true/false)"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum intent score filter")
):
    """
    Retrieve Instagram intent leads with comprehensive filtering and pagination support.
    """
    skip = (page - 1) * page_size
    items, total = crud_lead.get_multi(
        db,
        skip=skip,
        limit=page_size,
        search=search,
        status=status,
        has_website=has_website,
        min_score=min_score
    )
    pages = math.ceil(total / page_size) if total > 0 else 1

    return LeadListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/stats", response_model=LeadStats, summary="Get aggregated Instagram lead generation metrics")
def get_lead_stats(db: Session = Depends(get_db)):
    """
    Returns pipeline aggregate counts:
    - total leads
    - intent detected count
    - DMs drafted count
    - DMs queued count
    - sent count
    - average intent score
    """
    return crud_lead.get_stats(db)


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED, summary="Create a new lead")
def create_lead(
    lead_in: LeadCreate,
    db: Session = Depends(get_db)
):
    """
    Manually add an Instagram prospect into the outreach engine.
    """
    new_lead = crud_lead.create(db, obj_in=lead_in)
    return new_lead


@router.post("/seed", summary="Seed sample Instagram intent prospects for demo and testing")
def seed_leads(db: Session = Depends(get_db)):
    """
    Populates sample high-intent Instagram prospects if table is currently empty.
    """
    count = crud_lead.seed_sample_data(db)
    if count == 0:
        return {"message": "Database already contains leads. Seeding skipped.", "inserted": 0}
    return {"message": f"Successfully seeded {count} high-intent Instagram prospects with AI DMs.", "inserted": count}


@router.post("/scan-instagram", response_model=IGScanResponse, summary="Scan Instagram for accounts/comments signaling website intent")
def scan_instagram_leads(
    req: IGScanRequest,
    db: Session = Depends(get_db)
):
    """
    Instagram Intent Scanner:
    - Searches public posts, reels, and target agency hashtags (e.g. #needwebsite, #webdesign, #ecommercebrand).
    - Filters comments for high-intent triggers ('need a website', 'cost', 'dm me', 'website price', 'shopify', 'portfolio').
    - Extracts commenter @handle, post context URL, and exact comment text.
    - Generates Context-Aware AI dynamic outreach DMs.
    """
    leads = instagram_scanner.scan_intent(
        db,
        keyword=req.keyword or "need website",
        hashtag=req.hashtag,
        target_account=req.target_account,
        count=req.count
    )
    if len(leads) == 0:
        msg = f"No live Instagram leads found matching '{req.keyword or 'need website'}' within the targeted 48h search window."
    else:
        msg = f"Harvested {len(leads)} genuine live Instagram prospects actively inquiring for website development."

    return IGScanResponse(
        message=msg,
        hashtag=req.hashtag,
        keyword=req.keyword,
        count=len(leads),
        leads=leads
    )


@router.post("/{lead_id}/queue", response_model=LeadOut, summary="Queue lead for auto-DM dispatch")
def queue_lead_for_dispatch(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Moves lead status to 'DM Queued'.
    """
    lead = instagram_outreach.queue_lead(db, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return lead


@router.post("/{lead_id}/mark-sent", response_model=LeadOut, summary="Mark lead as Sent after 1-Click web DM")
def mark_lead_as_sent(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Marks lead as 'Sent' and records timestamp when operator dispatches via 1-Click Instagram Web DM.
    """
    lead = instagram_outreach.mark_lead_sent(db, lead_id, note_prefix="1-Click Web DM")
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return lead


@router.post("/{lead_id}/regenerate-dm", response_model=LeadOut, summary="Regenerate context-aware tailored DM for lead")
def regenerate_dm(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Uses Gemini AI to re-craft a hyper-personalized outreach DM based on the commenter's exact inquiry.
    """
    lead = crud_lead.get(db, id=lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )

    new_dm = gemini_service.generate_instagram_dm(
        handle=lead.instagram_handle or "@prospect",
        business_name=lead.business_name,
        industry=lead.industry or "Commercial Brand",
        comment_text=lead.comment_text or "Looking for web developer",
        post_context=lead.source_post_url or "Instagram post"
    )

    lead.outreach_instagram_dm = new_dm
    if lead.status == "Intent Detected":
        lead.status = "DM Drafted"
    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/{lead_id}", response_model=LeadOut, summary="Get lead details by ID")
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch complete record for a single lead.
    """
    lead = crud_lead.get(db, id=lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return lead


@router.put("/{lead_id}", response_model=LeadOut, summary="Update lead details")
def update_lead(
    lead_id: int,
    lead_in: LeadUpdate,
    db: Session = Depends(get_db)
):
    """
    Update lead attributes (e.g. status, score, notes, tailored DM).
    """
    lead = crud_lead.get(db, id=lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    updated = crud_lead.update(db, db_obj=lead, obj_in=lead_in)
    return updated


@router.patch("/{lead_id}/status", response_model=LeadOut, summary="Update outreach pipeline status and record dispatch timestamp")
def update_lead_status(
    lead_id: int,
    status_in: LeadStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update pipeline status: 'Intent Detected' | 'DM Drafted' | 'DM Queued' | 'Sent' | 'Closed'
    """
    lead = crud_lead.get(db, id=lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )

    pipeline_status = status_in.pipeline_status.strip()
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    timestamp_log = f"\n[Status updated to '{pipeline_status}' at {now_ts}]"
    lead.status = pipeline_status
    lead.notes = (lead.notes or "") + timestamp_log
    lead.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", response_model=LeadOut, summary="Delete a lead")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently remove a lead from the database.
    """
    lead = crud_lead.get(db, id=lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    removed = crud_lead.remove(db, id=lead_id)
    return removed
