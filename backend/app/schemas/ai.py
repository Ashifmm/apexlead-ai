from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class AITestRequest(BaseModel):
    message: str = Field(
        default="Say hello in one short sentence",
        description="Test message or prompt to send to Gemini API"
    )


class AITestResponse(BaseModel):
    success: bool = Field(..., description="Whether the Gemini API call succeeded")
    response: Optional[str] = Field(None, description="Generated response from Gemini")
    error: Optional[str] = Field(None, description="Error message if request failed")


# ==============================================================================
# Tier 1 & Tier 2 Autonomous AI Lead Intelligence Schemas
# ==============================================================================

class PostRelevanceResult(BaseModel):
    is_relevant_post: bool = Field(..., description="Whether post relates to business growth, web design, eCommerce, brand building, or agency services")
    topic: str = Field(..., description="Identified topic or niche of the post")


class CommentIntentResult(BaseModel):
    is_website_lead: bool = Field(..., description="Whether commenter has commercial intent to get a website, redesign, store, pricing, or developer help")
    confidence: int = Field(..., ge=1, le=100, description="Confidence score from 1 to 100")
    business_name: str = Field(..., description="Extracted business or display name")
    user_pain_point: str = Field(..., description="Identified user pain point or requirement")


# ==============================================================================
# Phase 3: AI Lead Analyzer Schemas
# ==============================================================================

class ColdEmail(BaseModel):
    subject: str = Field(..., description="Compelling, personalized, non-clickbait cold email subject line")
    body: str = Field(..., description="Professional, personalized cold email body with a soft call-to-action")


class LeadAnalysisResult(BaseModel):
    lead_score: int = Field(..., ge=0, le=100, description="Lead opportunity score from 0 to 100 based on website gap and revenue potential")
    priority: Literal["low", "medium", "high"] = Field(..., description="Lead prioritization category: low, medium, or high")
    website_needed: bool = Field(..., description="True if the business needs a new website or major modern redesign")
    pain_points: List[str] = Field(..., description="Specific business challenges, missed traffic, or digital vulnerabilities")
    recommended_solution: str = Field(..., description="Specific high-converting web agency solution proposed for this business")
    personalized_instagram_dm: str = Field(..., description="Short, friendly, non-spammy Instagram DM (2-3 sentences max) with a low-friction question")
    cold_email: ColdEmail = Field(..., description="Professional cold email with custom subject and body")


class LeadAnalyzeRequest(BaseModel):
    lead_id: Optional[int] = Field(None, description="Optional ID of existing lead in the database to analyze and persist")
    business_name: Optional[str] = Field(None, description="Name of the business (required if lead_id is not provided)")
    industry: Optional[str] = Field(None, description="Business vertical or niche, e.g. Roofing, Dental, Bakery")
    location: Optional[str] = Field(None, description="City, State or area")
    website_url: Optional[str] = Field(None, description="Existing website URL if any")
    instagram_handle: Optional[str] = Field(None, description="Instagram username or profile")
    email: Optional[str] = Field(None, description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    notes: Optional[str] = Field(None, description="Existing observations or context about the lead")


class LeadAnalysisResponse(BaseModel):
    success: bool = Field(..., description="Whether the analysis succeeded")
    lead_id: Optional[int] = Field(None, description="ID of the lead analyzed if applicable")
    analysis: Optional[LeadAnalysisResult] = Field(None, description="Structured lead analysis from Gemini")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
