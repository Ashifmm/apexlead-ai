from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.lead import LeadOut


class IGScanRequest(BaseModel):
    hashtag: Optional[str] = Field("needwebsite", description="Target hashtag to scan, e.g. needwebsite, webdesign, ecommercebrand, smallbusinessowner")
    keyword: Optional[str] = Field("need a website", description="Intent trigger phrase to filter comments, e.g. need website, cost, dm me, shopify")
    target_account: Optional[str] = Field(None, description="Optional competitor or agency profile to inspect, e.g. webflow, shopify, squarespace")
    count: int = Field(5, ge=1, le=30, description="Number of high-intent prospects to capture")


class IGScanResponse(BaseModel):
    message: str
    hashtag: Optional[str] = None
    keyword: Optional[str] = None
    count: int
    leads: List[LeadOut]


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
