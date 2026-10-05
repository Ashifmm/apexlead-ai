from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.lead import LeadOut


class IGScanRequest(BaseModel):
    keyword: str = Field("need website", min_length=2, max_length=150, description="Keyword phrase signaling website intent, e.g. 'need website', 'looking for developer', 'want ecommerce'")
    count: int = Field(5, ge=1, le=20, description="Number of intent leads to discover")


class IGScanResponse(BaseModel):
    message: str
    keyword: str
    count: int
    leads: List[LeadOut]


class MapsScanRequest(BaseModel):
    niche: str = Field(..., min_length=2, max_length=100, description="Target vertical/industry, e.g. Dental Clinic, Luxury Salon, Gym, Cafe")
    city: str = Field(..., min_length=2, max_length=100, description="Target city/region, e.g. Ghaziabad, Delhi, Noida, Austin, New York")
    count: int = Field(5, ge=1, le=20, description="Number of local businesses to scrape")


class MapsScanResponse(BaseModel):
    message: str
    niche: str
    city: str
    count: int
    leads: List[LeadOut]


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
