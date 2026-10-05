from typing import Optional, List, Tuple, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate


class CRUDLead:
    def get(self, db: Session, id: int) -> Optional[Lead]:
        """Fetch a single lead by ID."""
        return db.query(Lead).filter(Lead.id == id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
        has_website: Optional[bool] = None,
        min_score: Optional[int] = None
    ) -> Tuple[List[Lead], int]:
        """
        Fetch paginated leads with flexible filtering:
        - search: searches in business_name, industry, location, email, notes
        - status: exact match for status (e.g. 'new', 'analyzed', etc.)
        - has_website: boolean filter
        - min_score: filter by minimum lead_score
        """
        query = db.query(Lead)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Lead.business_name.ilike(term),
                    Lead.industry.ilike(term),
                    Lead.location.ilike(term),
                    Lead.email.ilike(term),
                    Lead.instagram_handle.ilike(term),
                    Lead.notes.ilike(term)
                )
            )

        if status and status.strip() and status != "all":
            s = status.strip()
            if s == "Intent Detected":
                query = query.filter(or_(Lead.status == "Intent Detected", Lead.status == "new"))
            elif s == "DM Drafted":
                query = query.filter(or_(Lead.status == "DM Drafted", Lead.status == "Outreach Ready", Lead.status == "outreach_generated"))
            elif s == "DM Queued":
                query = query.filter(Lead.status == "DM Queued")
            elif s in ("Sent", "Pitch Sent"):
                query = query.filter(or_(Lead.status == "Sent", Lead.status == "Pitch Sent", Lead.status == "contacted"))
            elif s in ("Closed", "Deal Won 🎉", "converted"):
                query = query.filter(or_(Lead.status == "Closed", Lead.status == "converted", Lead.status == "Deal Won 🎉"))
            else:
                query = query.filter(Lead.status == s)

        if has_website is not None:
            query = query.filter(Lead.has_website == has_website)

        if min_score is not None:
            query = query.filter(Lead.lead_score >= min_score)

        total = query.count()
        items = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def create(self, db: Session, *, obj_in: LeadCreate) -> Lead:
        """Create a new lead."""
        db_obj = Lead(
            business_name=obj_in.business_name,
            industry=obj_in.industry,
            location=obj_in.location,
            website_url=obj_in.website_url,
            has_website=obj_in.has_website if obj_in.has_website is not None else bool(obj_in.website_url and obj_in.website_url.strip()),
            email=obj_in.email,
            phone=obj_in.phone,
            instagram_handle=obj_in.instagram_handle,
            source=obj_in.source or "manual",
            status=obj_in.status or "new",
            lead_score=obj_in.lead_score or 0,
            score_reasons=obj_in.score_reasons,
            website_analysis=obj_in.website_analysis,
            outreach_email_subject=obj_in.outreach_email_subject,
            outreach_email_body=obj_in.outreach_email_body,
            outreach_instagram_dm=obj_in.outreach_instagram_dm,
            demo_url=obj_in.demo_url,
            demo_preview_html=obj_in.demo_preview_html,
            notes=obj_in.notes
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Lead,
        obj_in: Union[LeadUpdate, Dict[str, Any]]
    ) -> Lead:
        """Update an existing lead with partial or complete attributes."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Synchronize has_website if website_url was changed and has_website wasn't explicitly given
        if "website_url" in update_data and "has_website" not in update_data:
            url = update_data["website_url"]
            update_data["has_website"] = bool(url and str(url).strip())

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[Lead]:
        """Delete a lead by ID."""
        obj = db.query(Lead).filter(Lead.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Aggregate statistical metrics for Instagram lead pipeline."""
        total = db.query(func.count(Lead.id)).scalar() or 0
        intent_detected = db.query(func.count(Lead.id)).filter(
            Lead.status.in_(["Intent Detected", "new"])
        ).scalar() or 0
        dm_drafted = db.query(func.count(Lead.id)).filter(
            Lead.status.in_(["DM Drafted", "Outreach Ready", "outreach_generated"])
        ).scalar() or 0
        dm_queued = db.query(func.count(Lead.id)).filter(
            Lead.status == "DM Queued"
        ).scalar() or 0
        sent_count = db.query(func.count(Lead.id)).filter(
            Lead.status.in_(["Sent", "Pitch Sent", "contacted"])
        ).scalar() or 0
        converted = db.query(func.count(Lead.id)).filter(
            Lead.status.in_(["converted", "Closed", "Deal Won 🎉"])
        ).scalar() or 0
        avg_score = db.query(func.avg(Lead.lead_score)).scalar() or 0.0

        # Status breakdown
        statuses = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
        status_breakdown = {status: count for status, count in statuses}

        return {
            "total_leads": total,
            "intent_detected_count": intent_detected,
            "dm_drafted_count": dm_drafted,
            "dm_queued_count": dm_queued,
            "sent_count": sent_count,
            "converted_count": converted,
            "average_score": round(float(avg_score), 1),
            "status_breakdown": status_breakdown,
            # Legacy compatibility fields
            "no_website_count": total,
            "has_website_count": 0,
            "demos_ready_count": dm_drafted,
            "outreach_ready_count": dm_drafted + dm_queued,
            "contacted_count": sent_count,
        }

    def seed_sample_data(self, db: Session) -> int:
        """
        Pure Live Production Mode:
        NO synthetic or mock leads. Triggers genuine real-time extraction for active prospects.
        """
        try:
            from app.services.instagram_scanner import instagram_scanner
        except ImportError:
            from backend.app.services.instagram_scanner import instagram_scanner

        leads = instagram_scanner.scan_intent(db, keyword="need a website", count=5)
        return len(leads)


crud_lead = CRUDLead()
