from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.lead import LeadOut


class IGScanRequest(BaseModel):
    niche: Optional[str] = Field(None, description="Target industry or niche, e.g. Salons, eCommerce, Clinics or empty for general")
    count: int = Field(5, ge=1, le=30, description="Target quantity of leads to capture (3, 5, 8, 12)")
    hashtag: Optional[str] = Field(None, description="Optional legacy hashtag")
    keyword: Optional[str] = Field(None, description="Optional legacy keyword")
    target_account: Optional[str] = Field(None, description="Optional target account")


class IGScanResponse(BaseModel):
    message: str
    niche: Optional[str] = None
    count: int
    leads: List[LeadOut]
    hashtag: Optional[str] = None
    keyword: Optional[str] = None


class GenerateDMRequest(BaseModel):
    custom_tone: Optional[str] = Field("casual & high-converting", description="Tone of outreach message")


class GenerateDMResponse(BaseModel):
    lead_id: int
    handle: str
    personalized_dm: str
    message: str


class IGDispatchBatchRequest(BaseModel):
    daily_limit: int = Field(15, ge=1, le=50, description="Maximum number of Instagram DMs to dispatch per day")


class IGDispatchBatchResponse(BaseModel):
    message: str
    dispatched_count: int
    daily_limit: int
    remaining_quota: int
    dispatched_leads: List[LeadOut]


class IGOutreachStatusResponse(BaseModel):
    daily_limit: int
    dispatched_today: int
    pending_queue: int
    available_quota: int
