from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class DemoGenerateRequest(BaseModel):
    lead_id: Optional[int] = Field(None, description="Target lead ID to generate demo for (if not provided in path)")
    custom_instructions: Optional[str] = Field(None, description="Optional extra agency instructions or specific features to include in the demo")
    theme_color: Optional[str] = Field(None, description="Optional color theme palette: e.g. 'indigo', 'amber', 'emerald', 'cyan', 'rose', 'slate'")


class DemoGenerateResponse(BaseModel):
    success: bool = Field(..., description="Whether demo website generation succeeded")
    lead_id: int = Field(..., description="Lead ID for which demo was generated")
    demo_url: str = Field(..., description="Direct URL to preview the live multi-page demo")
    business_name: str = Field(..., description="Name of the business")
    industry: Optional[str] = Field(None, description="Industry vertical")
    message: str = Field(..., description="Status summary")
    preview_snippet: Optional[str] = Field(None, description="Short HTML snippet or title")
    error: Optional[str] = Field(None, description="Error details if generation failed")
    pages_generated: Optional[List[str]] = Field(
        default=["index.html", "about.html", "services.html", "contact.html"],
        description="List of generated HTML pages in the multi-page site"
    )


class DemoDetailResponse(BaseModel):
    lead_id: int = Field(..., description="Lead ID")
    business_name: str = Field(..., description="Business name")
    demo_url: Optional[str] = Field(None, description="Hosted live demo URL")
    has_demo: bool = Field(..., description="Whether demo has been generated")
    pages: Dict[str, str] = Field(default_factory=dict, description="Dictionary mapping page name to HTML markup")
