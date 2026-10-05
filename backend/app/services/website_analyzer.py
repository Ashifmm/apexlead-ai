import re
import json
import logging
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

try:
    from app.core.config import settings
    from app.services.gemini_service import gemini_service, GeminiServiceError
    from app.schemas.website import WebsiteAuditScores, WebsiteAuditResult
except ImportError:
    from backend.app.core.config import settings
    from backend.app.services.gemini_service import gemini_service, GeminiServiceError
    from backend.app.schemas.website import WebsiteAuditScores, WebsiteAuditResult

logger = logging.getLogger(__name__)


class WebsiteFetchError(Exception):
    """Raised when website cannot be reached, times out, or returns HTTP error."""
    pass


class WebsiteGeminiEvaluation(BaseModel):
    overall_score: int = Field(..., ge=0, le=100, description="Overall website health score (0-100)")
    design_score: int = Field(..., ge=0, le=100, description="Visual aesthetics and modern layout score (0-100)")
    mobile_score: int = Field(..., ge=0, le=100, description="Mobile responsiveness and viewport compliance (0-100)")
    conversion_score: int = Field(..., ge=0, le=100, description="CTA placement and lead conversion score (0-100)")
    redesign_opportunity: str = Field(..., description="'high' (huge agency pitch opportunity), 'medium', or 'low'")
    issues: List[str] = Field(..., description="List of concrete, verified technical or design flaws")
    improvements: List[str] = Field(..., description="Actionable recommendations for the redesign proposal")
    summary: str = Field(..., description="Concise executive summary of audit findings")


class WebsiteAnalyzer:
    """
    Safely fetches public website HTML, extracts concrete DOM signals,
    and runs a grounded Gemini audit without hallucination.
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 ApexLeadAuditor/1.0"
    )

    def normalize_url(self, raw_url: str) -> str:
        """Sanitizes and prefixes http/https protocol if missing."""
        if not raw_url or not raw_url.strip():
            raise WebsiteFetchError("Website URL cannot be empty.")

        url = raw_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        parsed = urlparse(url)
        if not parsed.netloc:
            raise WebsiteFetchError(f"Invalid website URL format: '{raw_url}'")

        return url

    def fetch_website_html(self, url: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Safely fetches website HTML with timeouts and security limits.
        Returns: (final_url, html_content, fetch_metadata)
        Raises WebsiteFetchError if unreachable.
        """
        target_url = self.normalize_url(url)
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Safe client configuration with strict timeouts
        try:
            with httpx.Client(
                headers=headers,
                follow_redirects=True,
                timeout=httpx.Timeout(10.0, connect=5.0, read=8.0),
                verify=False  # Allow auditing sites with expired/invalid SSL
            ) as client:
                response = client.get(target_url)

                # Check HTTP status
                if response.status_code >= 400:
                    raise WebsiteFetchError(
                        f"Website returned HTTP error {response.status_code} ({response.reason_phrase})."
                    )

                # Limit HTML response size to 1MB to prevent memory exhaustion
                content = response.text[:1_000_000]
                final_url = str(response.url)

                fetch_meta = {
                    "status_code": response.status_code,
                    "final_url": final_url,
                    "is_https": final_url.startswith("https://"),
                    "content_length_kb": round(len(content) / 1024, 1),
                }

                return final_url, content, fetch_meta

        except httpx.ConnectTimeout:
            raise WebsiteFetchError(f"Connection timed out. Server at '{target_url}' did not respond within 5s.")
        except httpx.ConnectError as ce:
            raise WebsiteFetchError(f"Unable to connect to '{target_url}'. Domain may not exist or DNS lookup failed.")
        except httpx.HTTPError as he:
            raise WebsiteFetchError(f"HTTP request error while reaching '{target_url}': {str(he)}")
        except Exception as e:
            raise WebsiteFetchError(f"Failed to fetch website '{target_url}': {str(e)}")

    def extract_signals(self, html: str, final_url: str, fetch_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses HTML and extracts factual DOM metrics:
        - Viewport tag (responsive readiness)
        - Metadata (title, description, og tags)
        - Heading hierarchy (h1, h2, h3)
        - Visual assets (images, missing alt tags)
        - CTA elements & forms
        - Direct contact links (tel, mailto, social)
        - Text density and technology markers
        """
        soup = BeautifulSoup(html, "html.parser")

        # 1. Metadata & Responsive Viewport
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        meta_desc = None
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()

        viewport_tag = soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})
        has_viewport = bool(viewport_tag and viewport_tag.get("content"))

        og_title = soup.find("meta", attrs={"property": "og:title"})
        og_image = soup.find("meta", attrs={"property": "og:image"})
        has_og_tags = bool(og_title or og_image)

        # 2. Heading Structure
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))

        # 3. Images & Media
        img_tags = soup.find_all("img")
        total_images = len(img_tags)
        images_missing_alt = sum(1 for img in img_tags if not img.get("alt") or not img.get("alt").strip())

        # 4. CTAs and Forms
        forms_count = len(soup.find_all("form"))
        buttons_count = len(soup.find_all(["button", "input[type='submit']"]))
        cta_keywords = ["contact", "book", "schedule", "quote", "estimate", "call", "order", "get started", "appointment"]
        
        found_cta_texts = []
        for el in soup.find_all(["a", "button"]):
            text = el.get_text(strip=True).lower()
            if any(kw in text for kw in cta_keywords) and len(text) < 40:
                found_cta_texts.append(el.get_text(strip=True))
                if len(found_cta_texts) >= 5:
                    break

        # 5. Contact Channels
        tel_links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith("tel:")]
        mailto_links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith("mailto:")]
        
        social_platforms = []
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if "instagram.com" in href and "instagram" not in social_platforms:
                social_platforms.append("instagram")
            elif "facebook.com" in href and "facebook" not in social_platforms:
                social_platforms.append("facebook")
            elif "linkedin.com" in href and "linkedin" not in social_platforms:
                social_platforms.append("linkedin")
            elif ("twitter.com" in href or "x.com" in href) and "twitter" not in social_platforms:
                social_platforms.append("twitter")

        # 6. Content density & clean text sample
        for script_or_style in soup(["script", "style", "svg", "noscript"]):
            script_or_style.extract()

        visible_text = soup.get_text(separator=" ", strip=True)
        word_count = len(visible_text.split())
        text_sample = visible_text[:1200]

        # 7. Technology Markers
        raw_html_lower = html.lower()
        detected_tech = []
        if "wp-content" in raw_html_lower or "wordpress" in raw_html_lower:
            detected_tech.append("WordPress")
        if "squarespace" in raw_html_lower:
            detected_tech.append("Squarespace")
        if "wix.com" in raw_html_lower or "wixsite" in raw_html_lower:
            detected_tech.append("Wix")
        if "shopify" in raw_html_lower:
            detected_tech.append("Shopify")
        if "bootstrap" in raw_html_lower:
            detected_tech.append("Bootstrap")
        if "tailwind" in raw_html_lower:
            detected_tech.append("Tailwind CSS")
        if "jquery" in raw_html_lower:
            detected_tech.append("jQuery")

        return {
            "target_url": final_url,
            "ssl_enabled": fetch_meta.get("is_https", False),
            "page_size_kb": fetch_meta.get("content_length_kb", 0),
            "title": title or "Missing Title Tag",
            "meta_description_present": bool(meta_desc),
            "has_responsive_viewport": has_viewport,
            "has_social_og_tags": has_og_tags,
            "h1_count": len(h1_tags),
            "primary_h1": h1_tags[0] if h1_tags else "No H1 Found",
            "h2_count": h2_count,
            "h3_count": h3_count,
            "total_images": total_images,
            "images_missing_alt": images_missing_alt,
            "forms_count": forms_count,
            "buttons_count": buttons_count,
            "detected_cta_elements": found_cta_texts,
            "has_phone_link": len(tel_links) > 0,
            "has_email_link": len(mailto_links) > 0,
            "social_platforms_linked": social_platforms,
            "word_count": word_count,
            "detected_technologies": detected_tech or ["Custom / Traditional HTML"],
            "content_sample": text_sample
        }

    def analyze_website(
        self,
        url: str,
        business_name: Optional[str] = None,
        industry: Optional[str] = None
    ) -> WebsiteAuditResult:
        """
        1. Safely fetches HTML (fails explicitly if unreachable).
        2. Extracts concrete DOM signals.
        3. Evaluates scores and recommendations via Gemini structured output.
        """
        # Step 1: Safely fetch website (will raise WebsiteFetchError if offline)
        final_url, html, fetch_meta = self.fetch_website_html(url)

        # Step 2: Extract verified technical signals
        signals = self.extract_signals(html, final_url, fetch_meta)

        # Step 3: Run grounded Gemini evaluation
        client = gemini_service._get_client()

        prompt = (
            f"You are conducting a professional website audit for a web design agency proposal.\n\n"
            f"Business Context:\n"
            f"- Business Name: {business_name or 'Prospective Client'}\n"
            f"- Industry / Niche: {industry or 'Local Business'}\n"
            f"- Target URL: {signals['target_url']}\n\n"
            f"Verified Scraped Technical Signals (FACTUAL - DO NOT HALLUCINATE):\n"
            f"- SSL Security Enabled (HTTPS): {signals['ssl_enabled']}\n"
            f"- Mobile Viewport Tag: {'Present (Mobile Responsive Tag)' if signals['has_responsive_viewport'] else 'MISSING (Fails mobile responsiveness)'}\n"
            f"- Page Title: {signals['title']}\n"
            f"- Meta Description: {'Present' if signals['meta_description_present'] else 'MISSING'}\n"
            f"- Heading Hierarchy: {signals['h1_count']} H1 tags (Primary: '{signals['primary_h1']}'), {signals['h2_count']} H2 tags\n"
            f"- Call-To-Action (CTA) Buttons/Links: {signals['detected_cta_elements'] if signals['detected_cta_elements'] else 'No prominent CTA buttons detected'}\n"
            f"- Forms Found: {signals['forms_count']}\n"
            f"- Direct Contact Links: Phone Click-to-Call: {signals['has_phone_link']}, Email Click-to-Mail: {signals['has_email_link']}\n"
            f"- Social Links Found: {signals['social_platforms_linked'] if signals['social_platforms_linked'] else 'None'}\n"
            f"- Images: {signals['total_images']} total ({signals['images_missing_alt']} missing alt accessibility tags)\n"
            f"- Word Count: {signals['word_count']} words\n"
            f"- Detected Framework / Platform: {', '.join(signals['detected_technologies'])}\n"
            f"- Content Sample: \"{signals['content_sample'][:600]}\"\n\n"
            f"Audit Instructions:\n"
            f"1. Score design_score (0-100), mobile_score (0-100), conversion_score (0-100), and overall_score (0-100).\n"
            f"   - If mobile viewport is missing, mobile_score MUST be below 40.\n"
            f"   - If SSL is missing, deduct 20 points from overall_score.\n"
            f"   - If no CTAs or forms are present, conversion_score MUST be below 50.\n"
            f"2. Set redesign_opportunity to 'high' (if overall_score < 65 or mobile/conversion are poor), 'medium' (65-80), or 'low' (> 80).\n"
            f"3. List 3 to 5 verified issues directly evidenced by the technical signals above.\n"
            f"4. List 3 to 5 actionable improvements for the web agency's redesign pitch.\n"
            f"5. Write a 2-3 sentence executive summary of the audit.\n"
            f"STRICT RULE: Only cite issues directly evidenced by the signals above. Do NOT invent nonexistent bugs."
        )

        system_instruction = (
            "You are a rigorous web agency technical auditor and UI/UX consultant. "
            "You evaluate websites factually using real DOM metrics, without fluff or hallucinated data."
        )

        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WebsiteGeminiEvaluation,
                system_instruction=system_instruction,
                temperature=0.2,
            )

            response = client.models.generate_content(
                model=gemini_service.default_model,
                contents=prompt,
                config=config
            )

            if not response.text:
                raise GeminiServiceError("Gemini returned an empty audit evaluation.")

            eval_data = json.loads(response.text)

            # Ensure redesign_opportunity is strictly one of 'low', 'medium', 'high'
            opp = eval_data.get("redesign_opportunity", "medium").lower()
            if opp not in ["low", "medium", "high"]:
                opp = "high" if eval_data.get("overall_score", 50) < 65 else "medium"

            scores = WebsiteAuditScores(
                overall_score=eval_data.get("overall_score", 50),
                design_score=eval_data.get("design_score", 50),
                mobile_score=eval_data.get("mobile_score", 50),
                conversion_score=eval_data.get("conversion_score", 50)
            )

            # Expose technical signals cleanly (remove huge raw text sample from return object)
            clean_signals = {k: v for k, v in signals.items() if k != "content_sample"}

            return WebsiteAuditResult(
                target_url=final_url,
                scores=scores,
                redesign_opportunity=opp,
                issues=eval_data.get("issues", []),
                improvements=eval_data.get("improvements", []),
                technical_signals=clean_signals,
                summary=eval_data.get("summary", "Website audit completed.")
            )

        except Exception as e:
            logger.error(f"Gemini evaluation error during website audit: {e}")
            raise GeminiServiceError(f"Website analysis model evaluation failed: {str(e)}")


website_analyzer = WebsiteAnalyzer()
