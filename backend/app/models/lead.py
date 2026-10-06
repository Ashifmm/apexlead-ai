from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import synonym
from app.db.base import Base


class Lead(Base):
    """
    SQLAlchemy Model representing a prospective business lead.
    Designed with extensibility for the complete AI Web Agency lifecycle:
    Stage 1: Lead capture & CRUD
    Stage 2: Lead scoring (lead_score, score_reasons)
    Stage 3: Website analysis (website_analysis)
    Stage 4: AI outreach generation (outreach_email_subject, outreach_email_body, outreach_instagram_dm)
    Stage 5 & 6: AI demo generation & deployment (demo_url, demo_preview_html)
    Stage 7 & 8: Dashboard & n8n automation (source, status, timestamps)
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Business Core Information
    business_name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=True, index=True)
    location = Column(String(255), nullable=True, index=True)
    
    # Online Presence
    website_url = Column(String(500), nullable=True)
    has_website = Column(Boolean, default=False, nullable=False, index=True)
    
    # Contact Channels
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    
    # Instagram Context Tracking
    source_post_url = Column(String(500), nullable=True)
    comment_text = Column(Text, nullable=True)
    
    # Lead Pipeline & Origin
    # source: "Instagram Intent", "manual", "instagram"
    source = Column(String(50), default="Instagram Intent", nullable=False)
    # status: "Intent Detected", "DM Drafted", "DM Queued", "Sent"
    status = Column(String(50), default="Intent Detected", nullable=False, index=True)
    
    # Synonyms for platform and username interoperability
    username = synonym("instagram_handle")
    platform = synonym("source")
    intent_score = synonym("lead_score")
    
    # Stage 2: AI Lead Scoring (0 to 100)
    lead_score = Column(Integer, default=0, nullable=False, index=True)
    score_reasons = Column(Text, nullable=True)  # JSON or text breakdown
    
    # Stage 3: Website Audit & Analysis
    website_analysis = Column(Text, nullable=True)  # JSON or text audit report
    
    # Stage 4: AI Personalized Outreach Drafts
    outreach_email_subject = Column(String(255), nullable=True)
    outreach_email_body = Column(Text, nullable=True)
    outreach_instagram_dm = Column(Text, nullable=True)
    
    # Stage 5 & 6: AI Generated Website Demo
    demo_url = Column(String(500), nullable=True)
    demo_preview_html = Column(Text, nullable=True)
    
    # Agency Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        lead_id = self.__dict__.get("id", None)
        b_name = self.__dict__.get("business_name", "lead")
        lead_status = self.__dict__.get("status", "New")
        return f"<Lead id={lead_id} business_name='{b_name}' status='{lead_status}'>"
