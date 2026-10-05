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
        """Seed realistic Instagram intent prospects with comments and personalized AI DMs."""
        existing_count = db.query(Lead).count()
        if existing_count > 0:
            return 0

        sample_leads = [
            Lead(
                business_name="Velvet Hair Studio",
                industry="Luxury Salon",
                location="Instagram (#salondesign)",
                instagram_handle="@velvet_hair_studio",
                source="Instagram Intent",
                status="DM Drafted",
                lead_score=96,
                source_post_url="https://instagram.com/p/C7x9LmP3qK1",
                comment_text="We are expanding our salon next month and desperately need a modern website with online booking for 4 stylists. How much would this cost? DM me portfolio!",
                score_reasons="High commercial intent: Explicit inquiry for online booking system + budget inquiry ('how much would this cost?') + request to DM portfolio.",
                outreach_instagram_dm="Hey @velvet_hair_studio! Saw your comment asking about website pricing and online booking for 4 stylists. We specialize in ultra-fast, high-converting booking portals for luxury salons that fill empty chairs automatically. Put together a quick visual concept for you — mind if I drop the preview link here?",
                notes="Captured under #salondesign reel. High-priority lead with active stylist expansion."
            ),
            Lead(
                business_name="Aura Aesthetic Dental",
                industry="Dental Clinic",
                location="Instagram (#smallbusinessowner)",
                instagram_handle="@auradental_implants",
                source="Instagram Intent",
                status="DM Queued",
                lead_score=94,
                source_post_url="https://instagram.com/p/C8y2KlQ4rM2",
                comment_text="Looking for a serious web developer to revamp our clinic website and patient appointment portal. What are your rates?",
                score_reasons="High conversion potential: Active clinic search for qualified web developer to build patient appointment workflow.",
                outreach_instagram_dm="Hey @auradental_implants! Saw your comment about revamping your clinic's patient appointment portal. We build high-trust, HIPAA-compliant dental websites that make scheduling seamless on mobile. Put together a quick interactive prototype for your practice — mind if I send over the link?",
                notes="Lead queued for automated dispatch batch."
            ),
            Lead(
                business_name="Iron Foundry Strength Club",
                industry="Fitness & Gym",
                location="Instagram (#needwebsite)",
                instagram_handle="@iron_foundry_gym",
                source="Instagram Intent",
                status="Sent",
                lead_score=95,
                source_post_url="https://instagram.com/p/C6w8PzR9tN3",
                comment_text="Need a clean Shopify or Next.js website for gym memberships and merch checkout ASAP. Please dm me with pricing and turnaround.",
                score_reasons="Immediate purchase intent: 'ASAP' timeline mentioned with explicit request for pricing and turnaround on membership checkout.",
                outreach_instagram_dm="Hey @iron_foundry_gym! Saw your comment about needing a clean membership & merch checkout website ASAP. We specialize in fast Next.js & Shopify fitness platforms that automate recurring gym signups. Put together a live concept preview for you — mind if I drop the link here?",
                notes="[Auto-DM Dispatched with safe humanized interval 48s]"
            ),
            Lead(
                business_name="Cinnamon & Sage Bakehouse",
                industry="Artisan Cafe",
                location="Instagram (#ecommercebrand)",
                instagram_handle="@cinnamon_sage_bakehouse",
                source="Instagram Intent",
                status="DM Drafted",
                lead_score=91,
                source_post_url="https://instagram.com/p/C9t1VxY5sL4",
                comment_text="Our bakery is launching wholesale orders online. Need an ecommerce site to take catering deposits. How much for a custom shop?",
                score_reasons="B2B Catering revenue signal: Looking to collect online deposits and wholesale orders digitally.",
                outreach_instagram_dm="Hey @cinnamon_sage_bakehouse! Saw your comment about launching online wholesale ordering and catering deposits. We build custom ecommerce flows for artisan bakeries that make wholesale reordering effortless. Built a quick visual concept for you — mind if I share the preview?",
                notes="Ready for review and queueing."
            ),
            Lead(
                business_name="Obsidian Auto Detailing",
                industry="Auto Detailing",
                location="Instagram (#smallbusinessowner)",
                instagram_handle="@obsidian_auto_detail",
                source="Instagram Intent",
                status="Intent Detected",
                lead_score=89,
                source_post_url="https://instagram.com/p/C5q7JnB2mK5",
                comment_text="Our current site is broken on mobile. Looking to hire a web developer for full redesign with instant quote calculator. DM me!",
                score_reasons="Identified pain point: Broken mobile UX and manual quoting taking up too much time.",
                outreach_instagram_dm="Hey @obsidian_auto_detail! Saw your comment about needing an instant quote calculator and mobile fix for your detailing studio. We build interactive package selectors and ceramic coating booking sites that 2x inbound requests. Would love to show you a quick prototype!",
                notes="New intent detected from competitor agency comment section."
            )
        ]

        db.add_all(sample_leads)
        db.commit()
        return len(sample_leads)


crud_lead = CRUDLead()
