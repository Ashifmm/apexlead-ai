import logging
from typing import Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

try:
    from app.db.session import get_db
    from app.crud.crud_lead import crud_lead
    from app.schemas.ai import (
        AITestRequest,
        AITestResponse,
        LeadAnalyzeRequest,
        LeadAnalysisResponse,
        LeadAnalysisResult,
    )
    from app.schemas.website import (
        WebsiteAnalyzeRequest,
        WebsiteAnalyzeResponse,
        WebsiteAuditResult,
    )
    from app.schemas.demo import (
        DemoGenerateRequest,
        DemoGenerateResponse,
        DemoDetailResponse,
    )
    from app.services.gemini_service import gemini_service, GeminiServiceError
    from app.services.website_analyzer import website_analyzer, WebsiteFetchError
    from app.services.demo_generator import demo_generator
except ImportError:
    from backend.app.db.session import get_db
    from backend.app.crud.crud_lead import crud_lead
    from backend.app.schemas.ai import (
        AITestRequest,
        AITestResponse,
        LeadAnalyzeRequest,
        LeadAnalysisResponse,
        LeadAnalysisResult,
    )
    from backend.app.schemas.website import (
        WebsiteAnalyzeRequest,
        WebsiteAnalyzeResponse,
        WebsiteAuditResult,
    )
    from backend.app.schemas.demo import (
        DemoGenerateRequest,
        DemoGenerateResponse,
        DemoDetailResponse,
    )
    from backend.app.services.gemini_service import gemini_service, GeminiServiceError
    from backend.app.services.website_analyzer import website_analyzer, WebsiteFetchError
    from backend.app.services.demo_generator import demo_generator
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/test", response_model=AITestResponse, summary="Test Gemini API Connectivity")
def test_gemini_api(req: AITestRequest):
    """
    Sends a test prompt to Google Gemini API using the official SDK.
    Verifies that GEMINI_API_KEY from backend/.env is valid and working.
    Never exposes or logs the API key.
    """
    if not gemini_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY is not configured in backend/.env."
        )

    try:
        reply = gemini_service.generate_text(prompt=req.message)
        return AITestResponse(
            success=True,
            response=reply
        )
    except GeminiServiceError as ge:
        logger.error(f"Gemini test error: {ge}")
        return AITestResponse(
            success=False,
            response=None,
            error=str(ge)
        )
    except Exception as e:
        logger.error(f"Unexpected error testing Gemini: {type(e).__name__}: {e}")
        return AITestResponse(
            success=False,
            response=None,
            error=f"Unexpected error: {str(e)}"
        )


@router.post("/analyze-lead", response_model=LeadAnalysisResponse, summary="Analyze Lead with Gemini AI (Phase 3)")
def analyze_lead_endpoint(
    req: LeadAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates a business lead using Google Gemini:
    - Calculates lead_score (0-100) and priority (low/medium/high)
    - Determines website_needed flag
    - Identifies specific pain points without hallucination
    - Recommends an agency solution
    - Drafts a short, personalized Instagram DM
    - Drafts a professional cold email (subject + body)
    
    If `lead_id` is provided, fetches and updates the lead record directly in SQLite.
    If `lead_id` is omitted, analyzes the provided business details payload directly.
    """
    if not gemini_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY is not configured in backend/.env."
        )

    # 1. Prepare lead data dictionary
    lead_record = None
    if req.lead_id is not None:
        lead_record = crud_lead.get(db, id=req.lead_id)
        if not lead_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {req.lead_id} not found in database."
            )
        lead_data = {
            "business_name": req.business_name or lead_record.business_name,
            "industry": req.industry or lead_record.industry,
            "location": req.location or lead_record.location,
            "website_url": req.website_url if req.website_url is not None else lead_record.website_url,
            "instagram_handle": req.instagram_handle if req.instagram_handle is not None else lead_record.instagram_handle,
            "email": req.email if req.email is not None else lead_record.email,
            "phone": req.phone if req.phone is not None else lead_record.phone,
            "notes": req.notes or lead_record.notes,
        }
    else:
        if not req.business_name or not req.business_name.strip():
            raise HTTPException(
                status_code=422,
                detail="Field 'business_name' is required when 'lead_id' is not provided."
            )
        lead_data = req.model_dump(exclude_unset=True)

    # 2. Run Gemini analysis
    try:
        analysis: LeadAnalysisResult = gemini_service.analyze_lead(lead_data=lead_data)

        # 3. If lead_id was provided, persist results into database
        if lead_record:
            update_fields = {
                "lead_score": analysis.lead_score,
                "score_reasons": f"Priority: {analysis.priority.upper()}. " + " | ".join(analysis.pain_points),
                "website_analysis": analysis.recommended_solution,
                "outreach_email_subject": analysis.cold_email.subject,
                "outreach_email_body": analysis.cold_email.body,
                "outreach_instagram_dm": analysis.personalized_instagram_dm,
            }
            # Advance status if in initial stages
            if lead_record.status in ["new", "analyzed", "scored"]:
                update_fields["status"] = "outreach_generated"

            crud_lead.update(db, db_obj=lead_record, obj_in=update_fields)

        return LeadAnalysisResponse(
            success=True,
            lead_id=req.lead_id,
            analysis=analysis
        )

    except GeminiServiceError as ge:
        logger.error(f"Lead analysis failed: {ge}")
        return LeadAnalysisResponse(
            success=False,
            lead_id=req.lead_id,
            analysis=None,
            error=str(ge)
        )
    except Exception as e:
        logger.error(f"Unexpected error analyzing lead: {type(e).__name__}: {e}")
        return LeadAnalysisResponse(
            success=False,
            lead_id=req.lead_id,
            analysis=None,
            error=f"Unexpected error: {str(e)}"
        )


@router.post("/analyze-website", response_model=WebsiteAnalyzeResponse, summary="Audit Live Website with Gemini AI (Phase 4)")
def analyze_website_endpoint(
    req: WebsiteAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Safely crawls a target website, extracts factual DOM signals (SSL, viewport, headings, CTAs, word count),
    and evaluates design, mobile, conversion, and overall scores with actionable agency recommendations.
    
    Strict Rule: If the website cannot be reached or is offline, returns an explicit unreachable error
    and NEVER hallucinates an audit.
    """
    if not gemini_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY is not configured in backend/.env."
        )

    # 1. Resolve target URL & context
    lead_record = None
    target_url = req.website_url
    business_name = req.business_name
    industry = req.industry

    if req.lead_id is not None:
        lead_record = crud_lead.get(db, id=req.lead_id)
        if not lead_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {req.lead_id} not found in database."
            )
        target_url = target_url or lead_record.website_url
        business_name = business_name or lead_record.business_name
        industry = industry or lead_record.industry

        # Check if lead has no website URL
        if not target_url or not target_url.strip():
            return WebsiteAnalyzeResponse(
                success=False,
                status="no_website",
                lead_id=req.lead_id,
                audit=None,
                error=f"Lead #{req.lead_id} ('{lead_record.business_name}') does not have a website URL on file."
            )
    else:
        if not target_url or not target_url.strip():
            raise HTTPException(
                status_code=422,
                detail="Field 'website_url' is required when 'lead_id' is not provided."
            )

    # 2. Safely crawl & analyze with anti-hallucination guardrails
    try:
        audit_result: WebsiteAuditResult = website_analyzer.analyze_website(
            url=target_url,
            business_name=business_name,
            industry=industry
        )

        # 3. If lead_id was provided, update database record
        if lead_record:
            audit_summary_text = (
                f"Website Audit ({audit_result.target_url}):\n"
                f"- Overall: {audit_result.scores.overall_score}/100 | Design: {audit_result.scores.design_score} | "
                f"Mobile: {audit_result.scores.mobile_score} | Conversion: {audit_result.scores.conversion_score}\n"
                f"- Redesign Opportunity: {audit_result.redesign_opportunity.upper()}\n"
                f"- Summary: {audit_result.summary}\n\n"
                f"Issues Found:\n- " + "\n- ".join(audit_result.issues) + "\n\n"
                f"Recommended Improvements:\n- " + "\n- ".join(audit_result.improvements)
            )

            update_data = {
                "website_analysis": audit_summary_text,
                "has_website": True,
                "website_url": audit_result.target_url,
            }
            
            # If site has poor scores, opportunity score is high for web agencies!
            if audit_result.redesign_opportunity == "high":
                update_data["lead_score"] = max(lead_record.lead_score, 85)
                update_data["score_reasons"] = f"High redesign opportunity. Audit score {audit_result.scores.overall_score}/100 with critical mobile/design gaps."
            elif audit_result.redesign_opportunity == "medium":
                update_data["lead_score"] = max(lead_record.lead_score, 70)

            if lead_record.status == "new":
                update_data["status"] = "analyzed"

            crud_lead.update(db, db_obj=lead_record, obj_in=update_data)

        return WebsiteAnalyzeResponse(
            success=True,
            status="success",
            lead_id=req.lead_id,
            audit=audit_result,
            error=None
        )

    except WebsiteFetchError as wfe:
        # STRICT RULE: Never hallucinate an audit if fetch fails!
        logger.warning(f"Website unreachable during audit for '{target_url}': {wfe}")
        return WebsiteAnalyzeResponse(
            success=False,
            status="unreachable",
            lead_id=req.lead_id,
            audit=None,
            error=str(wfe)
        )
    except GeminiServiceError as gse:
        logger.error(f"Gemini error during website audit for '{target_url}': {gse}")
        return WebsiteAnalyzeResponse(
            success=False,
            status="error",
            lead_id=req.lead_id,
            audit=None,
            error=str(gse)
        )
    except Exception as e:
        logger.error(f"Unexpected error analyzing website '{target_url}': {e}")
        return WebsiteAnalyzeResponse(
            success=False,
            status="error",
            lead_id=req.lead_id,
            audit=None,
            error=f"Unexpected error during website audit: {str(e)}"
        )


# =========================================================================
# Phase 6: Website Demo Generator Endpoints
# =========================================================================

@router.post("/generate-demo", response_model=DemoGenerateResponse, summary="Generate Multi-Page Website Demo (Phase 6)")
def generate_demo_endpoint(
    req: DemoGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Creates a bespoke multi-page HTML prototype styled with modern Tailwind CSS:
    - Generates index.html, about.html, services.html, and contact.html
    - Saves all files to /demos/{lead_id}/ for instant interactive preview
    - Stores the primary preview in SQLite and advances status to 'demo_generated'
    """
    if req.lead_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'lead_id' is required to generate a website demo."
        )

    lead_record = crud_lead.get(db, id=req.lead_id)
    if not lead_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {req.lead_id} not found."
        )

    try:
        res = demo_generator.generate_multi_page_demo(
            lead=lead_record,
            db=db,
            custom_instructions=req.custom_instructions,
            theme_color=req.theme_color
        )
        return res
    except Exception as e:
        logger.error(f"Failed to generate demo for lead #{req.lead_id}: {e}")
        return DemoGenerateResponse(
            success=False,
            lead_id=req.lead_id,
            demo_url="",
            business_name=lead_record.business_name,
            industry=lead_record.industry,
            message="Failed to generate website demo",
            error=str(e),
            pages_generated=[]
        )


@router.post("/generate-demo/{lead_id}", response_model=DemoGenerateResponse, summary="Generate Multi-Page Website Demo for Lead (Phase 6)")
def generate_demo_for_lead_endpoint(
    lead_id: int,
    req: Optional[DemoGenerateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Generates multi-page HTML demo for the specified lead ID.
    Can accept optional custom instructions and color theme.
    """
    lead_record = crud_lead.get(db, id=lead_id)
    if not lead_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found."
        )

    custom_instructions = req.custom_instructions if req else None
    theme_color = req.theme_color if req else None

    try:
        res = demo_generator.generate_multi_page_demo(
            lead=lead_record,
            db=db,
            custom_instructions=custom_instructions,
            theme_color=theme_color
        )
        return res
    except Exception as e:
        logger.error(f"Failed to generate demo for lead #{lead_id}: {e}")
        return DemoGenerateResponse(
            success=False,
            lead_id=lead_id,
            demo_url="",
            business_name=lead_record.business_name,
            industry=lead_record.industry,
            message="Failed to generate website demo",
            error=str(e),
            pages_generated=[]
        )


@router.get("/demo/{lead_id}", response_model=DemoDetailResponse, summary="Get Generated Demo Details and Pages (Phase 6)")
def get_demo_details_endpoint(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves information on the generated demo for a lead, including the full
    dictionary of generated HTML pages (index.html, about.html, services.html, contact.html).
    """
    lead_record = crud_lead.get(db, id=lead_id)
    if not lead_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found."
        )

    pages = demo_generator.get_demo_pages(lead_id)
    if not pages and lead_record.demo_preview_html:
        pages = {"index.html": lead_record.demo_preview_html}

    return DemoDetailResponse(
        lead_id=lead_record.id,
        business_name=lead_record.business_name,
        demo_url=lead_record.demo_url,
        has_demo=bool(lead_record.demo_url or lead_record.demo_preview_html or pages),
        pages=pages
    )


@router.get("/demo/{lead_id}/preview", response_class=HTMLResponse, summary="Preview Demo HTML Page Directly (Phase 6)")
def preview_demo_page_endpoint(
    lead_id: int,
    page: str = "index.html",
    db: Session = Depends(get_db)
):
    """
    Directly serves the HTML of a requested demo page for embedding in iframes or opening standalone.
    Supported pages: index.html, about.html, services.html, contact.html.
    """
    lead_record = crud_lead.get(db, id=lead_id)
    if not lead_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found."
        )

    pages = demo_generator.get_demo_pages(lead_id)
    if page in pages:
        return HTMLResponse(content=pages[page], media_type="text/html")

    if page == "index.html" and lead_record.demo_preview_html:
        return HTMLResponse(content=lead_record.demo_preview_html, media_type="text/html")

    # If demo hasn't been generated on disk yet, generate on the fly
    try:
        demo_generator.generate_multi_page_demo(lead=lead_record, db=db)
        fresh_pages = demo_generator.get_demo_pages(lead_id)
        if page in fresh_pages:
            return HTMLResponse(content=fresh_pages[page], media_type="text/html")
    except Exception as e:
        logger.error(f"Error generating demo on-the-fly for #{lead_id}: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Page '{page}' not found for lead #{lead_id}."
    )

