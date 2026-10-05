import json
import logging
from typing import Optional, Dict, Any

try:
    from app.core.config import settings
    from app.schemas.ai import LeadAnalysisResult
except ImportError:
    from backend.app.core.config import settings
    from backend.app.schemas.ai import LeadAnalysisResult

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Custom exception raised when Gemini API communication fails."""
    pass


class GeminiService:
    """
    Reusable service for interacting with Google Gemini API via official google-genai SDK.
    - Securely reads GEMINI_API_KEY from backend environment.
    - Never prints, logs, or returns the API key.
    - Powers Lead Analysis, Scoring, and Outreach generation.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self.default_model = default_model or settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Returns True if an API key is present and non-empty."""
        return bool(self._api_key and self._api_key.strip() != "")

    def _get_client(self):
        """Lazy-initializes and caches the official google-genai client."""
        if not self.is_configured:
            raise GeminiServiceError(
                "GEMINI_API_KEY is not configured in backend/.env. "
                "Please add a valid API key to backend/.env."
            )

        if self._client is None:
            try:
                from google import genai
                # Initialize client securely passing the API key
                self._client = genai.Client(api_key=self._api_key.strip())
            except ImportError:
                raise GeminiServiceError(
                    "The 'google-genai' SDK is not installed. Run 'pip install google-genai'."
                )
            except Exception as e:
                # Log only the error type/message without leaking credentials
                logger.error(f"Failed to initialize Gemini client: {type(e).__name__}: {e}")
                raise GeminiServiceError(f"Failed to initialize Gemini client: {str(e)}")

        return self._client

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Sends a general text prompt to Gemini and returns the generated response.
        Uses modern interactions API with fallback to models.generate_content.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt message cannot be empty.")

        client = self._get_client()
        target_model = model or self.default_model

        try:
            # Modern SDK interactions API
            if hasattr(client, "interactions"):
                kwargs = {
                    "model": target_model,
                    "input": prompt.strip()
                }
                if system_instruction:
                    kwargs["system_instruction"] = system_instruction
                
                interaction = client.interactions.create(**kwargs)
                if interaction.output_text:
                    return interaction.output_text.strip()

            # Fallback to models.generate_content
            response = client.models.generate_content(
                model=target_model,
                contents=prompt.strip()
            )
            if response.text:
                return response.text.strip()
            
            return ""

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini API generation error: {type(e).__name__}: {error_msg}")
            raise GeminiServiceError(f"Gemini API request failed: {error_msg}")

    def analyze_lead(
        self,
        lead_data: Dict[str, Any],
        model: Optional[str] = None
    ) -> LeadAnalysisResult:
        """
        Evaluates a prospective business lead using Google Gemini with structured output:
        - Calculates lead_score (0-100) and priority (low/medium/high)
        - Determines website_needed boolean
        - Identifies concrete pain points
        - Formulates a customized high-converting agency solution
        - Crafts a personalized, non-spammy Instagram DM
        - Drafts a professional cold email (subject + body)
        """
        client = self._get_client()
        target_model = model or self.default_model

        business_name = lead_data.get("business_name") or "Target Business"
        industry = lead_data.get("industry") or "General Business"
        location = lead_data.get("location") or "Local Area"
        website_url = lead_data.get("website_url") or ""
        instagram = lead_data.get("instagram_handle") or ""
        notes = lead_data.get("notes") or ""

        # Build grounded prompt
        prompt = (
            f"Analyze this business prospect for a web design and digital agency:\n"
            f"- Business Name: {business_name}\n"
            f"- Industry / Niche: {industry}\n"
            f"- Location: {location}\n"
            f"- Existing Website: {website_url if website_url else 'None (No active website)'}\n"
            f"- Instagram Handle: {instagram if instagram else 'None provided'}\n"
            f"- Additional Notes/Context: {notes if notes else 'None provided'}\n\n"
            f"Evaluation Guidelines:\n"
            f"1. Lead Score (0-100): Score 80-100 if the business lacks a website or has an severely outdated site in a high-ticket local niche; score 50-79 if they have a basic site with clear gaps; score below 50 if they already have an established modern web presence.\n"
            f"2. Priority: Set to 'high' (score >= 75), 'medium' (50-74), or 'low' (< 50).\n"
            f"3. Website Needed: True if they need a brand new website or complete redesign.\n"
            f"4. Pain Points: Identify 2 to 4 realistic, un-hallucinated pain points (e.g. missing out on local Google search traffic, relying solely on manual social DMs, lack of mobile booking/estimate forms, lower customer trust).\n"
            f"5. Recommended Solution: Propose a specific, high-converting agency solution tailored to {industry} in {location}.\n"
            f"6. Personalized Instagram DM: 2-3 short, conversational, non-spammy sentences. Compliment their craft, casually mention how a website/instant booking could capture more clients, and ask a low-friction question.\n"
            f"7. Professional Cold Email: Write a compelling, natural subject line and a concise, personalized email body (under 150 words) focused on business growth with a soft call-to-action to review a free demo.\n"
            f"Strict Requirement: Ground all analysis directly in the provided business details. Do NOT hallucinate awards, fictitious team members, or unverified claims."
        )

        system_instruction = (
            "You are an elite digital agency growth strategist and B2B copywriter. "
            "You analyze business leads objectively and write authentic, high-converting, human-sounding outreach."
        )

        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LeadAnalysisResult,
                system_instruction=system_instruction,
                temperature=0.2,
            )

            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config
            )

            if not response.text:
                raise GeminiServiceError("Gemini returned an empty response during lead analysis.")

            raw_json = json.loads(response.text)
            return LeadAnalysisResult.model_validate(raw_json)

        except json.JSONDecodeError as jde:
            logger.error(f"Failed to parse Gemini JSON response: {jde}")
            raise GeminiServiceError(f"Failed to parse Gemini structured JSON: {str(jde)}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini lead analysis error: {type(e).__name__}: {error_msg}")
            raise GeminiServiceError(f"Gemini lead analysis failed: {error_msg}")

    def generate_instagram_dm(
        self,
        handle: str,
        business_name: str,
        industry: str,
        comment_text: str,
        post_context: Optional[str] = None
    ) -> str:
        """
        Context-Aware AI Dynamic DM Generator:
        Formula:
        1. Acknowledge what they commented on + post context
        2. Mention specific expertise relevant to their vertical
        3. Casual CTA inviting them to see a quick prototype or chat
        """
        clean_handle = handle if handle.startswith("@") else f"@{handle}"

        if self.is_configured:
            prompt = f"""
Write an authentic, hyper-personalized Instagram DM from a boutique web agency to an active prospect who commented on Instagram.

Target Lead:
- Instagram Handle: {clean_handle}
- Business/Name: {business_name}
- Industry: {industry}
- Comment they wrote: "{comment_text}"
- Post Context: {post_context or 'Target design/ecommerce post'}

Formula to strictly follow:
1. Acknowledge what they commented on (cite their comment or inquiry naturally).
2. Mention our agency's specific expertise in {industry} (e.g. mobile bookings, Shopify conversions, custom design).
3. Low friction, casual CTA inviting them to see a quick tailored prototype.

Rules:
- 2 to 3 sentences total.
- Keep it casual, friendly, and human (NO corporate buzzwords, NO "I hope this finds you well").
- Greeting: "Hey {clean_handle}!"
Return ONLY the raw DM text.
"""
            try:
                dm = self.generate_text(
                    prompt,
                    system_instruction="You are a talented agency designer writing natural, non-spammy, high-converting Instagram direct messages."
                )
                if dm and len(dm.strip()) > 20:
                    clean_dm = dm.strip().strip('"').strip("'")
                    return clean_dm
            except Exception as e:
                logger.warning(f"Gemini DM generation error, using dynamic formula fallback: {e}")

        # Deterministic formulaic fallback
        comment_snippet = (comment_text or "").strip().rstrip("?.!")
        if len(comment_snippet) > 65:
            comment_snippet = comment_snippet[:62] + "..."

        ind = industry or "modern"
        return (
            f"Hey {clean_handle}! Saw your comment: \"{comment_snippet}\". "
            f"We build ultra-fast, high-converting websites and booking portals specifically tailored for {ind} brands to turn followers into paying clients. "
            f"Put together a quick visual concept for you — mind if I drop the preview link here?"
        )


# Singleton instance for application-wide dependency injection
gemini_service = GeminiService()
