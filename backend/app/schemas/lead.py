from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class LeadBase(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255, description="Name of the target business")
    industry: Optional[str] = Field(None, max_length=100, description="Business vertical/niche, e.g. Dental, HVAC, Restaurant")
    location: Optional[str] = Field(None, max_length=255, description="Geographic location, city, state")
    website_url: Optional[str] = Field(None, max_length=500, description="Current website URL if any")
    has_website: Optional[bool] = Field(None, description="Whether the business currently has an active website")
    email: Optional[str] = Field(None, max_length=255, description="Contact email address")
    phone: Optional[str] = Field(None, max_length=100, description="Contact phone number")
    instagram_handle: Optional[str] = Field(None, max_length=100, description="Instagram username or profile link")
    source: Optional[str] = Field("manual", max_length=50, description="Origin source: manual, google_maps, instagram, csv_import, n8n")
    status: Optional[str] = Field("new", max_length=50, description="Pipeline status: new, analyzed, scored, outreach_generated, demo_generated, contacted, converted, rejected")
    lead_score: Optional[int] = Field(0, ge=0, le=100, description="AI calculated opportunity score (0 to 100)")
    score_reasons: Optional[str] = Field(None, description="Breakdown / explanation for the assigned score")
    website_analysis: Optional[str] = Field(None, description="JSON or markdown audit summary of current website")
    outreach_email_subject: Optional[str] = Field(None, max_length=255, description="AI generated cold email subject line")
    outreach_email_body: Optional[str] = Field(None, description="AI generated cold email body")
    outreach_instagram_dm: Optional[str] = Field(None, description="AI generated personalized Instagram DM")
    demo_url: Optional[str] = Field(None, max_length=500, description="URL where generated website demo is previewed/hosted")
    demo_preview_html: Optional[str] = Field(None, description="HTML markup of generated demo")
    notes: Optional[str] = Field(None, description="Internal agency notes")

    @model_validator(mode="before")
    @classmethod
    def compute_has_website(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If has_website is not explicitly provided, infer it from website_url
            if data.get("has_website") is None:
                url = data.get("website_url")
                data["has_website"] = bool(url and str(url).strip())
        return data


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    has_website: Optional[bool] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    instagram_handle: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    lead_score: Optional[int] = Field(None, ge=0, le=100)
    score_reasons: Optional[str] = None
    website_analysis: Optional[str] = None
    outreach_email_subject: Optional[str] = None
    outreach_email_body: Optional[str] = None
    outreach_instagram_dm: Optional[str] = None
    demo_url: Optional[str] = None
    demo_preview_html: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_website_flag(cls, data: Any) -> Any:
        if isinstance(data, dict) and "website_url" in data and "has_website" not in data:
            url = data.get("website_url")
            data["has_website"] = bool(url and str(url).strip())
        return data


class LeadOut(LeadBase):
    id: int
    has_website: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadListResponse(BaseModel):
    items: List[LeadOut]
    total: int
    page: int
    page_size: int
    pages: int


class LeadStats(BaseModel):
    total_leads: int
    no_website_count: int
    has_website_count: int
    demos_ready_count: int
    outreach_ready_count: int
    contacted_count: int
    converted_count: int
    average_score: float
    status_breakdown: Dict[str, int]


class NicheSeedRequest(BaseModel):
    niche: str = Field(..., min_length=1, max_length=100, description="Target business vertical, e.g. Luxury Salon, Gym, Cafe, Dental Clinic")
    city: str = Field(..., min_length=1, max_length=100, description="Target city/location, e.g. Ghaziabad, Delhi, Noida")


class NicheSeedResponse(BaseModel):
    message: str
    niche: str
    city: str
    count: int
    leads: List[LeadOut]


class LeadStatusUpdateRequest(BaseModel):
    pipeline_status: str = Field(
        ...,
        description="Updated pipeline status: 'Outreach Ready' | 'Pitch Sent' | 'In Discussion' | 'Closed' | 'Not Interested'"
    )

