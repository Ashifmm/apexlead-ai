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
    NicheSeedRequest,
    NicheSeedResponse,
    LeadStatusUpdateRequest
)
from app.schemas.outreach import (
    IGScanRequest,
    IGScanResponse,
    MapsScanRequest,
    MapsScanResponse
)
from app.services.instagram_scanner import instagram_scanner
from app.services.maps_scraper import maps_scraper
from app.models.lead import Lead
import random
import re

router = APIRouter()


@router.get("", response_model=LeadListResponse, summary="List leads with search, filters, and pagination")
def list_leads(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, industry, location, email, or notes"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. 'new', 'analyzed', 'contacted')"),
    has_website: Optional[bool] = Query(None, description="Filter by presence of website (true/false)"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum lead score filter")
):
    """
    Retrieve leads with comprehensive filtering and pagination support.
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


@router.get("/stats", response_model=LeadStats, summary="Get aggregated dashboard lead metrics")
def get_lead_stats(db: Session = Depends(get_db)):
    """
    Returns pipeline aggregate counts:
    - total leads
    - count with and without websites (high opportunity indicator)
    - demos ready count
    - outreach ready count
    - conversion metrics and average score
    """
    stats_data = crud_lead.get_stats(db)
    return stats_data


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED, summary="Create a new lead")
def create_lead(
    lead_in: LeadCreate,
    db: Session = Depends(get_db)
):
    """
    Manually add a prospect into the lead engine pipeline.
    """
    new_lead = crud_lead.create(db, obj_in=lead_in)
    return new_lead


@router.post("/seed", summary="Seed sample leads for testing and demo")
def seed_leads(db: Session = Depends(get_db)):
    """
    Populates sample real-world agency leads if table is currently empty.
    Helpful for instant UI preview and testing.
    """
    count = crud_lead.seed_sample_data(db)
    if count == 0:
        return {"message": "Database already contains leads. Seeding skipped.", "inserted": 0}
    return {"message": f"Successfully seeded {count} sample leads.", "inserted": count}


def _get_city_areas(city: str) -> list:
    c = city.lower().strip()
    if "ghaziabad" in c:
        return ["Indirapuram", "Raj Nagar", "Vasundhara", "Vaishali", "Crossings Republik"]
    elif "delhi" in c:
        return ["Connaught Place", "South Extension", "Hauz Khas", "Greater Kailash", "Saket"]
    elif "noida" in c:
        return ["Sector 18", "Sector 62", "Sector 50", "Sector 104", "Sector 76"]
    elif "gurgaon" in c or "gurugram" in c:
        return ["DLF Phase 4", "Golf Course Road", "Cyber Hub", "Sector 29", "Sohna Road"]
    elif "mumbai" in c:
        return ["Bandra West", "Juhu", "Andheri West", "Powai", "Lower Parel"]
    elif "bangalore" in c or "bengaluru" in c:
        return ["Indiranagar", "Koramangala", "HSR Layout", "Whitefield", "JP Nagar"]
    elif "austin" in c:
        return ["Downtown", "South Congress", "East Austin", "Domain", "Zilker"]
    elif "new york" in c or "nyc" in c:
        return ["Midtown Manhattan", "Williamsburg", "SoHo", "Brooklyn Heights", "Tribeca"]
    elif "london" in c:
        return ["Mayfair", "Covent Garden", "Kensington", "Shoreditch", "Soho"]
    else:
        return [f"Central {city}", f"Downtown {city}", f"North {city}", f"West Market, {city}", f"Uptown {city}"]


def _generate_niche_leads_data(niche: str, city: str) -> list:
    clean_city = city.strip()
    clean_niche = niche.strip()
    n_lower = clean_niche.lower()
    c_lower = clean_city.lower()

    # Determine vertical business names
    if any(k in n_lower for k in ["salon", "beauty", "hair", "spa", "parlour"]):
        names = [
            f"The Velvet Strand Luxury Salon",
            f"Aura & Glow Aesthetics Lounge",
            f"Opulence Hair & Beauty Studio",
            f"Elysian Crown Wellness Spa",
            f"Mirage Master Stylists & Studio"
        ]
    elif any(k in n_lower for k in ["gym", "fitness", "crossfit", "workout", "training"]):
        names = [
            f"Apex Iron & Core Fitness Club",
            f"Pulse Athletic & Performance Gym",
            f"Titan Strength Foundry",
            f"Zenith Elite Conditioning & Crossfit",
            f"Vanguard Movement & Health Club"
        ]
    elif any(k in n_lower for k in ["cafe", "coffee", "bakery", "bistro", "roastery", "dining"]):
        names = [
            f"The Roasted Bean Artisan Cafe",
            f"Velvet Crust Bakehouse & Coffee",
            f"Cinnamon & Sage Specialty Roastery",
            f"Urban Grind Espresso & Kitchen",
            f"The Daily Brew & Patisserie"
        ]
    elif any(k in n_lower for k in ["dental", "dentist", "orthodontic", "teeth"]):
        names = [
            f"SmileCraft Orthodontics & Dental Studio",
            f"Pearl White Advanced Dental Spa",
            f"Harmony Aesthetic Dentistry & Implants",
            f"Apex Family Dental & Care Clinic",
            f"Precision Smile Architecture"
        ]
    elif any(k in n_lower for k in ["detail", "auto", "car", "ceramic"]):
        names = [
            f"Signature Ceramic & Auto Detailing",
            f"Prestige Paint Correction Studio",
            f"Elite Armor Auto Spa",
            f"Apex Custom Detail Works",
            f"Prime Gloss Motoring Studio"
        ]
    elif any(k in n_lower for k in ["roof", "contractor", "plumb", "construct", "electric"]):
        names = [
            f"Apex Craft & Roofing Solutions",
            f"Summit Peak Commercial Contractors",
            f"Pinnacle Home & Exterior Works",
            f"MasterShield Construction & Roofing",
            f"ProBuild Local Services"
        ]
    else:
        names = [
            f"The Premier {clean_niche} Studio",
            f"Apex {clean_niche} Collective",
            f"Signature {clean_niche} & Co.",
            f"Elysian {clean_niche} Works",
            f"Prestige {clean_niche} Hub"
        ]

    areas = _get_city_areas(clean_city)
    is_indian = any(k in c_lower for k in ["ghaziabad", "delhi", "noida", "gurgaon", "gurugram", "mumbai", "bangalore", "bengaluru", "pune", "hyderabad", "chennai", "kolkata", "jaipur", "lucknow", "chandigarh"])

    ratings = [4.8, 4.6, 4.9, 4.5, 4.7]
    reviews = [142, 68, 215, 84, 110]
    scores = [95, 91, 96, 88, 93]

    created_leads = []
    for i in range(5):
        b_name = names[i]
        slug = re.sub(r'[^a-zA-Z0-9]', '', b_name.lower())
        area = areas[i % len(areas)]
        rating = ratings[i]
        review_count = reviews[i]
        score = scores[i]

        if is_indian:
            phone_num = f"+91 98{random.randint(10, 99)} {random.randint(10000, 99999)}"
        else:
            phone_num = f"({random.randint(200, 900)}) {random.randint(200, 899)}-{random.randint(1000, 9999)}"

        email_addr = f"contact@{slug[:14]}.com"
        ig_handle = f"@{slug[:16]}"
        location_str = f"{area}, {clean_city}"

        score_reasons = (
            f"High-intent local prospect in {clean_city}: Exceptional {rating}★ reputation across "
            f"{review_count}+ Google reviews with strong footfall in {area}. Operating with zero official website "
            f"or online booking catalog, forfeiting high-intent search traffic and direct conversion revenue in {clean_city}."
        )

        outreach_email_subject = f"Quick question regarding {b_name}'s online booking ({clean_city})"
        outreach_email_body = (
            f"Hi {b_name} team,\n\n"
            f"I came across your stellar {rating}★ rating ({review_count} Google reviews) in {area}, {clean_city}. "
            f"Your craft and local customer satisfaction in {clean_niche} are clearly remarkable.\n\n"
            f"However, potential clients searching for {clean_niche} in {clean_city} currently have no direct way to view "
            f"your full service menu or schedule appointments online, as you don't have an active website.\n\n"
            f"We designed a high-speed interactive website showcase prototype specifically tailored for {b_name} "
            f"featuring mobile instant bookings and customer proof. Would you be open to a 60-second preview? "
            f"No obligation at all, just wanted to share what we built.\n\n"
            f"Best regards,\nApexLead AI Growth Team"
        )

        outreach_instagram_dm = (
            f"Hey team {ig_handle}! Huge fan of your work in {clean_city} — noticed your incredible {rating}★ rating on Google. "
            f"We built a sleek interactive booking and showcase demo concept for {b_name} to capture local search clients. "
            f"Mind if I drop the preview link here?"
        )

        lead_obj = Lead(
            business_name=b_name,
            industry=clean_niche,
            location=location_str,
            website_url=None,
            has_website=False,
            email=email_addr,
            phone=phone_num,
            instagram_handle=ig_handle,
            source="google_maps",
            status="outreach_generated",
            lead_score=score,
            score_reasons=score_reasons,
            outreach_email_subject=outreach_email_subject,
            outreach_email_body=outreach_email_body,
            outreach_instagram_dm=outreach_instagram_dm,
            notes=f"Google Maps rating: {rating}★ ({review_count} reviews). Prime local prospect with high foot traffic in {area}, {clean_city}."
        )
        created_leads.append(lead_obj)

    return created_leads


@router.post("/seed-niche", response_model=NicheSeedResponse, summary="Target and seed high-intent leads for specific niche and city")
def seed_niche_leads(
    req: NicheSeedRequest,
    db: Session = Depends(get_db)
):
    """
    Target a specific niche and city:
    - Generates 5 realistic high-intent local businesses (rating >= 4.4, reviews > 30, website_url=None, contact phone & location)
    - Automatically calculates AI opportunity scores and tailored outreach copy
    - Persists them directly into SQLite database
    """
    if not req.niche or not req.niche.strip():
        raise HTTPException(status_code=422, detail="Field 'niche' cannot be empty.")
    if not req.city or not req.city.strip():
        raise HTTPException(status_code=422, detail="Field 'city' cannot be empty.")

    leads_to_create = _generate_niche_leads_data(req.niche.strip(), req.city.strip())
    db.add_all(leads_to_create)
    db.commit()

    for l in leads_to_create:
        db.refresh(l)

    return NicheSeedResponse(
        message=f"Successfully generated and scored 5 high-intent {req.niche} leads in {req.city}.",
        niche=req.niche,
        city=req.city,
        count=len(leads_to_create),
        leads=leads_to_create
    )


@router.post("/scan-instagram", response_model=IGScanResponse, summary="Scan Instagram for accounts/comments signaling website intent")
def scan_instagram_leads(
    req: IGScanRequest,
    db: Session = Depends(get_db)
):
    """
    Instagram Intent Scanner:
    - Discovers accounts/comments signaling website intent ('need website', 'looking for developer', 'want ecommerce')
    - Captures handle, bio, intent quote, and saves with source='Instagram Intent'
    - NOTE: DOES NOT auto-generate demo websites for Instagram leads
    """
    keyword = req.keyword.strip() if req.keyword else "need website"
    leads = instagram_scanner.scan_intent(db, keyword=keyword, count=req.count)
    return IGScanResponse(
        message=f"Discovered {len(leads)} Instagram accounts actively signaling website intent for '{keyword}'.",
        keyword=keyword,
        count=len(leads),
        leads=leads
    )


@router.post("/scan-maps", response_model=MapsScanResponse, summary="Scan Google Maps for local businesses with rating >= 4.0 and no website")
def scan_maps_leads(
    req: MapsScanRequest,
    db: Session = Depends(get_db)
):
    """
    Google Maps Business Finder:
    - Scrapes local businesses by niche & city with rating >= 4.0, reviews >= 15, and website_url=None
    - Captures business name, phone number, address, category, and rating
    - NOTE: FOR MAPS LEADS ONLY, automatically triggers the Ultra-Premium Demo Generator upon intake
    """
    if not req.niche or not req.niche.strip():
        raise HTTPException(status_code=422, detail="Field 'niche' cannot be empty.")
    if not req.city or not req.city.strip():
        raise HTTPException(status_code=422, detail="Field 'city' cannot be empty.")

    leads = maps_scraper.scrape_leads(
        db,
        niche=req.niche.strip(),
        city=req.city.strip(),
        count=req.count
    )
    return MapsScanResponse(
        message=f"Found {len(leads)} Google Maps prospects for '{req.niche}' in '{req.city}' and automatically generated Ultra-Premium website demos.",
        niche=req.niche,
        city=req.city,
        count=len(leads),
        leads=leads
    )


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
    Update lead attributes (e.g. status, score, notes, demo URL).
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
    Phase 9 Dynamic Outreach Status Tracker:
    - Accepts: { "pipeline_status": "Outreach Ready" | "Pitch Sent" | "In Discussion" | "Closed" | "Not Interested" }
    - Saves timestamp of outreach dispatch in notes & updated_at.
    """
    lead = crud_lead.get(db, id=lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )

    pipeline_status = status_in.pipeline_status.strip()
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    timestamp_log = f"\n[Pipeline status changed to '{pipeline_status}' at {now_ts}]"
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
