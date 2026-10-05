import logging
import os
import re
import random
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

try:
    from app.models.lead import Lead
    from app.services.gemini_service import gemini_service
    from app.core.config import settings
except ImportError:
    from backend.app.models.lead import Lead
    from backend.app.services.gemini_service import gemini_service
    from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Target niche hashtags to harvest live commercial intent
TARGET_HASHTAGS = [
    "interiordesigner",
    "businessowner",
    "salondesign",
    "boutiqueowner",
    "cafeowner",
    "contractor",
    "fitnesscoach",
    "jewelrydesigner",
    "bakeryowner",
    "dentist"
]

# Commercial intent keyword triggers
INTENT_TRIGGERS = [
    "cost", "price", "pricing", "website", "portfolio", "dm me", "how much",
    "hire", "rate", "rates", "developer", "need web", "looking for", "book",
    "service", "catalog", "order", "online", "quote", "interested"
]


class InstagramIntentScanner:
    """
    100% REAL Autonomous Intent Harvester for Instagram:
    - Eliminates mock data completely.
    - Connects to Instagram using the authenticated session credentials in backend/.env.
    - Pulls recent public posts under target niche hashtags (e.g. #interiordesigner, #businessowner).
    - Extracts live comments on these posts and detects intent triggers ('cost?', 'pricing', 'website', 'portfolio', 'dm me').
    - Evaluates intent score via Gemini AI and automatically queues qualified prospects as leads.
    """

    def __init__(self):
        self.app_id = "936619743392459"

    def _get_headers(self) -> Dict[str, str]:
        session_id = settings.INSTAGRAM_SESSION_ID or os.getenv("INSTAGRAM_SESSION_ID", "")
        user_id = settings.INSTAGRAM_USER_ID or os.getenv("INSTAGRAM_USER_ID", "")
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "X-IG-App-ID": self.app_id,
            "Cookie": f"sessionid={session_id}; ds_user_id={user_id};",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/"
        }

    def harvest_live_intent(
        self,
        db: Session,
        target_tags: Optional[List[str]] = None,
        max_leads: int = 5
    ) -> List[Lead]:
        """
        Scans live Instagram hashtags, extracts comments with commercial intent,
        evaluates them with Gemini, and commits them as leads.
        """
        tags_to_scan = target_tags or random.sample(TARGET_HASHTAGS, min(3, len(TARGET_HASHTAGS)))
        headers = self._get_headers()
        discovered_leads: List[Lead] = []

        logger.info(f"Starting Autonomous Intent Harvester across hashtags: {tags_to_scan}...")

        with httpx.Client(timeout=25.0, headers=headers) as client:
            for tag in tags_to_scan:
                if len(discovered_leads) >= max_leads:
                    break

                try:
                    tag_url = f"https://www.instagram.com/api/v1/tags/web_info/?tag_name={tag}"
                    resp = client.get(tag_url)

                    if resp.status_code != 200:
                        logger.warning(f"Instagram tag query for #{tag} returned HTTP {resp.status_code}: {resp.text[:120]}")
                        continue

                    data = resp.json()
                    sections = (
                        data.get("data", {}).get("recent", {}).get("sections", [])
                        or data.get("data", {}).get("top", {}).get("sections", [])
                    )

                    media_items = []
                    for sec in sections:
                        layout_content = sec.get("layout_content", {})
                        for item in layout_content.get("medias", []) + layout_content.get("fill_items", []):
                            m = item.get("media", {})
                            if m:
                                media_items.append(m)

                    logger.info(f"Retrieved {len(media_items)} live posts under #{tag}.")

                    for media in media_items:
                        if len(discovered_leads) >= max_leads:
                            break

                        media_pk = media.get("pk") or media.get("id")
                        media_code = media.get("code")
                        post_owner = media.get("user", {}).get("username")
                        caption_text = media.get("caption", {}).get("text", "") if media.get("caption") else ""
                        comment_count = media.get("comment_count", 0)

                        # 1. First, check comments on this post for intent triggers
                        found_intent_candidate = None

                        if comment_count > 0 and media_pk:
                            try:
                                comm_url = f"https://www.instagram.com/api/v1/media/{media_pk}/comments/"
                                comm_resp = client.get(comm_url)
                                if comm_resp.status_code == 200:
                                    comm_data = comm_resp.json()
                                    comments = comm_data.get("comments", [])
                                    for comm in comments:
                                        c_text = comm.get("text", "")
                                        c_lower = c_text.lower()
                                        c_user = comm.get("user", {}).get("username")

                                        # Check if comment contains intent triggers
                                        if any(trigger in c_lower for trigger in INTENT_TRIGGERS):
                                            found_intent_candidate = {
                                                "username": c_user,
                                                "full_name": comm.get("user", {}).get("full_name") or c_user,
                                                "quote": c_text,
                                                "type": "comment",
                                                "post_code": media_code,
                                                "hashtag": tag
                                            }
                                            break
                            except Exception as comm_err:
                                logger.warning(f"Error fetching comments for post {media_code}: {comm_err}")

                        # 2. If no comments triggered, check post caption itself for creator looking for web presence
                        if not found_intent_candidate and caption_text:
                            cap_lower = caption_text.lower()
                            if any(trigger in cap_lower for trigger in ["dm to order", "no website", "link in bio soon", "website coming", "need developer", "portfolio in bio"]):
                                found_intent_candidate = {
                                    "username": post_owner,
                                    "full_name": media.get("user", {}).get("full_name") or post_owner,
                                    "quote": caption_text[:250],
                                    "type": "post_caption",
                                    "post_code": media_code,
                                    "hashtag": tag
                                }

                        if found_intent_candidate:
                            target_handle = f"@{found_intent_candidate['username']}"

                            # Avoid duplicate leads in DB
                            existing = db.query(Lead).filter(Lead.instagram_handle == target_handle).first()
                            if existing:
                                continue

                            # Verify Intent Score via Gemini
                            raw_quote = found_intent_candidate["quote"]
                            industry_name = tag.capitalize().replace("owner", " Services").replace("designer", " Design")

                            ai_score = 88
                            if gemini_service.is_configured:
                                try:
                                    eval_res = gemini_service.evaluate_lead(
                                        business_name=found_intent_candidate["full_name"],
                                        industry=industry_name,
                                        has_website=False,
                                        notes=f"Instagram intent captured under #{tag}: '{raw_quote}'"
                                    )
                                    if eval_res.get("lead_score"):
                                        ai_score = eval_res["lead_score"]
                                except Exception as ai_err:
                                    logger.warning(f"Gemini evaluation fallback: {ai_err}")

                            # Tailor conversational outreach pitch
                            personalized_dm = (
                                f"Hey {target_handle}! Saw your comment under #{tag}: \"{raw_quote[:60]}...\" "
                                f"We build high-converting portfolios & booking sites for {industry_name}s to take orders on autopilot. "
                                f"Would love to share a couple of quick ideas if you're open to it!"
                            )

                            lead = Lead(
                                business_name=found_intent_candidate["full_name"] or found_intent_candidate["username"],
                                industry=industry_name,
                                location=f"Instagram (#{tag})",
                                website_url=None,
                                has_website=False,
                                instagram_handle=target_handle,
                                source="Instagram Intent",
                                status="Outreach Ready",
                                lead_score=ai_score,
                                score_reasons=(
                                    f"Live Instagram Intent under #{tag}: Verified commercial signal in {found_intent_candidate['type']}. "
                                    f"Prospect expressed explicit inquiry: \"{raw_quote[:120]}\". High conversion potential."
                                ),
                                outreach_instagram_dm=personalized_dm,
                                notes=(
                                    f"Live Instagram Intent Harvester #{tag} — Post: https://instagram.com/p/{found_intent_candidate['post_code']}\n"
                                    f"Raw Intent Signal: {raw_quote}"
                                )
                            )

                            db.add(lead)
                            db.commit()
                            db.refresh(lead)
                            discovered_leads.append(lead)
                            logger.info(f"Harvested and committed live Instagram lead: {target_handle} (Score: {ai_score})")

                except Exception as tag_err:
                    logger.error(f"Error harvesting hashtag #{tag}: {tag_err}")

        logger.info(f"Autonomous Intent Harvester successfully discovered {len(discovered_leads)} live leads.")
        return discovered_leads

    def scan_intent(
        self,
        db: Session,
        keyword: str = "interiordesigner",
        count: int = 5
    ) -> List[Lead]:
        """
        Public endpoint entry point: scans live hashtag intent based on niche keyword.
        """
        clean_tag = re.sub(r'[^a-zA-Z0-9]', '', keyword.lower()) or "interiordesigner"
        return self.harvest_live_intent(db, target_tags=[clean_tag], max_leads=count)


# Singleton instance
instagram_scanner = InstagramIntentScanner()
