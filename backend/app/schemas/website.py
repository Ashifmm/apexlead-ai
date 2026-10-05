from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class WebsiteAuditScores(BaseModel):
    overall_score: int = Field(..., ge=0, le=100, description="Overall website health score (0-100, where 100 is flawless and <60 indicates urgent redesign need)")
    design_score: int = Field(..., ge=0, le=100, description="Visual aesthetics, typography, and modern layout score (0-100)")
    mobile_score: int = Field(..., ge=0, le=100, description="Mobile responsiveness, viewport presence, and touch friendliness (0-100)")
    conversion_score: int = Field(..., ge=0, le=100, description="Lead capture effectiveness, CTA prominence, and contact ease (0-100)")


class WebsiteAuditResult(BaseModel):
    target_url: str = Field(..., description="The verified URL that was crawled")
    scores: WebsiteAuditScores = Field(..., description="Component audit scores")
    redesign_opportunity: Literal["low", "medium", "high"] = Field(..., description="Agency pitch opportunity: 'high' if site is poor/outdated, 'low' if site is already modern")
    issues: List[str] = Field(..., description="Specific technical, mobile, or design issues found in the crawled HTML")
    improvements: List[str] = Field(..., description="Actionable recommendations for the web agency proposal")
    technical_signals: Dict[str, Any] = Field(..., description="Factual extracted DOM metrics (SSL, viewport, headings, CTAs, word count)")
    summary: str = Field(..., description="Executive summary of the website audit")


class WebsiteAnalyzeRequest(BaseModel):
    website_url: Optional[str] = Field(None, description="Website URL to crawl and audit")
    lead_id: Optional[int] = Field(None, description="Optional lead ID from database to fetch website_url from and persist results to")
    business_name: Optional[str] = Field(None, description="Optional business name for context")
    industry: Optional[str] = Field(None, description="Optional industry vertical for context")


class WebsiteAnalyzeResponse(BaseModel):
    success: bool = Field(..., description="Whether the website analysis succeeded")
    status: str = Field(..., description="Status code: 'success', 'unreachable', 'no_website', 'invalid_url', 'error'")
    lead_id: Optional[int] = Field(None, description="Lead ID analyzed if provided")
    audit: Optional[WebsiteAuditResult] = Field(None, description="Full website audit report if website was reachable")
    error: Optional[str] = Field(None, description="Descriptive error message if unreachable or failed")
