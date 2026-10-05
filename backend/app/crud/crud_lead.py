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
            if s == "Outreach Ready":
                query = query.filter(or_(Lead.status == "Outreach Ready", Lead.status == "outreach_generated"))
            elif s == "Pitch Sent":
                query = query.filter(or_(Lead.status == "Pitch Sent", Lead.status == "contacted"))
            elif s in ("Closed", "Deal Won 🎉"):
                query = query.filter(or_(Lead.status == "Closed", Lead.status == "converted", Lead.status == "Deal Won 🎉"))
            elif s == "contacted":
                query = query.filter(or_(Lead.status == "contacted", Lead.status == "Pitch Sent"))
            elif s == "converted":
                query = query.filter(or_(Lead.status == "converted", Lead.status == "Closed", Lead.status == "Deal Won 🎉"))
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
        """Aggregate statistical metrics for dashboard."""
        total = db.query(func.count(Lead.id)).scalar() or 0
        no_website = db.query(func.count(Lead.id)).filter(Lead.has_website == False).scalar() or 0
        has_website = db.query(func.count(Lead.id)).filter(Lead.has_website == True).scalar() or 0
        demos_ready = db.query(func.count(Lead.id)).filter(Lead.demo_url.isnot(None), Lead.demo_url != "").scalar() or 0
        outreach_ready = db.query(func.count(Lead.id)).filter(
            or_(
                Lead.outreach_email_body.isnot(None),
                Lead.outreach_instagram_dm.isnot(None)
            )
        ).scalar() or 0
        contacted = db.query(func.count(Lead.id)).filter(
            or_(Lead.status == "contacted", Lead.status == "Pitch Sent")
        ).scalar() or 0
        converted = db.query(func.count(Lead.id)).filter(
            or_(Lead.status == "converted", Lead.status == "Closed", Lead.status == "Deal Won 🎉")
        ).scalar() or 0
        avg_score = db.query(func.avg(Lead.lead_score)).scalar() or 0.0

        # Status breakdown
        statuses = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
        status_breakdown = {status: count for status, count in statuses}

        return {
            "total_leads": total,
            "no_website_count": no_website,
            "has_website_count": has_website,
            "demos_ready_count": demos_ready,
            "outreach_ready_count": outreach_ready,
            "contacted_count": contacted,
            "converted_count": converted,
            "average_score": round(float(avg_score), 1),
            "status_breakdown": status_breakdown
        }

    def seed_sample_data(self, db: Session) -> int:
        """Seed realistic agency leads for development and dashboard testing."""
        # Only seed if table is currently empty
        existing_count = db.query(Lead).count()
        if existing_count > 0:
            return 0

        sample_leads = [
            Lead(
                business_name="Artisan Sourdough Bakery",
                industry="Bakery & Cafe",
                location="Austin, TX",
                website_url=None,
                has_website=False,
                email="hello@artisansourdoughaustin.com",
                phone="(512) 555-0192",
                instagram_handle="@artisanbakery_atx",
                source="instagram",
                status="new",
                lead_score=92,
                score_reasons="High engagement on Instagram (12k followers), active daily stories, no online ordering or menu website.",
                notes="Prime candidate for custom menu & online pickup ordering demo.",
            ),
            Lead(
                business_name="Apex Performance Chiropractic",
                industry="Healthcare & Wellness",
                location="Denver, CO",
                website_url="http://apexchiro-denver-old.net",
                has_website=True,
                email="contact@apexchiro-denver.com",
                phone="(303) 555-4481",
                instagram_handle="@apexchirodenver",
                source="google_maps",
                status="analyzed",
                lead_score=85,
                score_reasons="Existing website is outdated (HTTP only, non-responsive on mobile, slow load time 4.2s).",
                website_analysis="No SSL certificate. Broken appointment booking widget. Poor mobile score (34/100).",
                notes="Send modern redesign demo with integrated booking calendar.",
            ),
            Lead(
                business_name="Luxe Detail Garage",
                industry="Automotive Detailing",
                location="Miami, FL",
                website_url=None,
                has_website=False,
                email="booking@luxedetailgarage.com",
                phone="(305) 555-7823",
                instagram_handle="@luxedetail_garage",
                source="instagram",
                status="outreach_generated",
                lead_score=95,
                score_reasons="High-ticket services ($500-$2000 per detail), strong visual portfolio on IG, relying solely on DMs for booking inquiries.",
                outreach_email_subject="Quick question regarding Luxe Detail Garage's booking system",
                outreach_email_body="Hey Luxe Detail team,\n\nCame across your incredible ceramic coating work on Instagram. Noticed you handle all client bookings manually via DMs. We built an interactive booking & package showcase demo specifically tailored for high-end auto studios in Miami.",
                outreach_instagram_dm="Hey team @luxedetail_garage! Love the recent GT3 RS paint correction reel. Dropping a quick note — we created a modern showcase & instant booking concept for your shop so clients can pick packages seamlessly.",
                notes="Personalized IG DM ready for review.",
            ),
            Lead(
                business_name="Summit Peak Roofing",
                industry="Home Services & Construction",
                location="Seattle, WA",
                website_url="https://summitpeakroofing-sample.com",
                has_website=True,
                email="estimates@summitpeakroofing.com",
                phone="(206) 555-3211",
                instagram_handle=None,
                source="google_maps",
                status="demo_generated",
                lead_score=78,
                score_reasons="Established business with 40+ 5-star Google reviews but generic template site without quote calculator.",
                demo_url="https://demo.apexagency.ai/preview/summit-peak-roofing",
                outreach_email_subject="Built a live roofing quote calculator demo for Summit Peak",
                outreach_email_body="Hi Summit Peak team,\n\nYour 5-star reviews on Google are stellar. To help turn more local Seattle search traffic into phone calls, we designed a quick interactive instant estimate preview for you.",
                notes="Demo link generated. Ready for cold email blast.",
            ),
            Lead(
                business_name="Bella Cucina Trattoria",
                industry="Restaurant & Dining",
                location="Chicago, IL",
                website_url=None,
                has_website=False,
                email="info@bellacucinachicago.com",
                phone="(312) 555-9014",
                instagram_handle="@bellacucina_chi",
                source="manual",
                status="contacted",
                lead_score=88,
                score_reasons="New authentic Italian spot in West Loop, busy weekend foot traffic, PDF menu on Facebook only.",
                notes="Cold email sent on Monday. Follow up scheduled.",
            ),
            Lead(
                business_name="Vanguard Wealth Partners",
                industry="Financial Services",
                location="New York, NY",
                website_url="https://vanguardwealthsample.com",
                has_website=True,
                email="advisors@vanguardwealthsample.com",
                phone="(212) 555-6670",
                instagram_handle=None,
                source="manual",
                status="converted",
                lead_score=90,
                score_reasons="High ACV client, converted after receiving custom high-trust corporate portal demo.",
                demo_url="https://demo.apexagency.ai/preview/vanguard-wealth",
                notes="Closed $4,500 redesign package + $350/mo maintenance retainer.",
            )
        ]

        db.add_all(sample_leads)
        db.commit()
        return len(sample_leads)


crud_lead = CRUDLead()
