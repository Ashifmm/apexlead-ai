import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_gemini_client():
    """
    Returns an initialized Gemini client if GEMINI_API_KEY is configured.
    Otherwise returns None and logs an informational warning.
    This ensures the application runs smoothly even before the API key is set.
    """
    if not settings.is_gemini_configured:
        logger.warning(
            "GEMINI_API_KEY is not configured in .env. "
            "AI analysis, scoring, and outreach generation will be disabled until configured."
        )
        return None

    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return client
    except ImportError:
        logger.warning(
            "google-genai package not found. Install requirements to enable Gemini integration."
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None
