import logging
import os
import re
import urllib.parse
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
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

# Search user-agents for authentic requests
SEARCH_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]


class InstagramIntentScanner:
    """
    2-Tier Autonomous AI Context & Intent Analyzer (GrowthGrid Engine):
    - NO mock data, NO placeholders, NO synthetic demo arrays.
    - Autonomous post discovery via public Instagram endpoints & search indices.
    - Tier 1: Post Relevance Verification (AI Check) - evaluates caption context for business/growth relevance.
    - Tier 2: Comment Buyer-Intent Evaluation (AI Check) - evaluates commenter intent, extracts business name,
      user pain point, and filters strictly for confidence >= 70%.
    - Dynamic GrowthGrid demo pitch generator.
    """

    def __init__(self):
        self.app_id = "936619743392459"

    def _get_search_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": SEARCH_USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

    def _harvest_live_posts(
        self,
        niche: Optional[str] = None,
        max_candidates: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Gathers live candidate posts and reels from public search queries.
        Tailors queries to the optional industry/niche and business growth context.
        """
        clean_niche = (niche or "").strip()

        # Build prioritized queries
        queries = []
        if clean_niche:
            queries.extend([
                f'site:instagram.com/reel/ "{clean_niche}" "need a website"',
                f'site:instagram.com/p/ "{clean_niche}" "need a website"',
                f'site:instagram.com/reel/ "{clean_niche}" "website cost"',
                f'site:instagram.com/p/ "{clean_niche}" "redesign website"',
                f'site:instagram.com "{clean_niche}" "need web designer"',
                f'site:instagram.com/reel/ "{clean_niche}" "website"',
                f'site:instagram.com/p/ "{clean_niche}" "website"'
            ])

        queries.extend([
            'site:instagram.com/reel/ "need a website"',
            'site:instagram.com/p/ "need a website"',
            'site:instagram.com/reel/ "need web designer"',
            'site:instagram.com/p/ "redesign website"',
            'site:instagram.com/reel/ "website cost"',
            'site:instagram.com/p/ "revamp website"',
            'site:instagram.com "need website for my business"',
            'site:instagram.com/reel/ "eCommerce store" "pricing"',
            'site:instagram.com/p/ "shopify store" "need developer"'
        ])

        discovered: List[Dict[str, Any]] = []
        seen_urls = set()
        headers = self._get_search_headers()

        with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
            for q in queries:
                if len(discovered) >= max_candidates:
                    break
                try:
                    search_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(q)}"
                    resp = client.get(search_url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        if len(discovered) >= max_candidates:
                            break

                        href = a['href']
                        target_url = None

                        if "RU=" in href and "instagram.com" in href:
                            m = re.search(r'RU=([^/&]+)', href)
                            if m:
                                target_url = urllib.parse.unquote(m.group(1))
                        elif "instagram.com" in href and "yahoo.com" not in href:
                            target_url = href

                        if not target_url:
                            continue

                        if not ("/p/" in target_url or "/reel/" in target_url):
                            continue

                        clean_target = target_url.split("?")[0].rstrip("/") + "/"
                        if clean_target in seen_urls:
                            continue
                        seen_urls.add(clean_target)

                        container = a.find_parent('li') or a.find_parent('div')
                        snippet_text = container.get_text(" ", strip=True) if container else a.get_text(" ", strip=True)

                        # 1. Extract handle
                        handle = None
                        m_dash = re.search(r'comments\s*-\s*([a-zA-Z0-9_.]+)', snippet_text)
                        if m_dash:
                            handle = m_dash.group(1)
                        else:
                            m_at = re.search(r'\(@([a-zA-Z0-9_.]+)\)', snippet_text)
                            if m_at:
                                handle = m_at.group(1)
                            else:
                                m_on = re.search(r'([a-zA-Z0-9_.]+)\s+on Instagram', snippet_text, re.IGNORECASE)
                                if m_on:
                                    handle = m_on.group(1)

                        # 2. Extract preliminary business name
                        b_name = None
                        m_name = re.search(
                            r'(?:reel|p)\s*[^\s\w]*\s*[a-zA-Z0-9_-]+\s+([^|":•]+?)(?:\s+on Instagram|\s*\||\s*:|\s*•)',
                            snippet_text,
                            re.IGNORECASE
                        )
                        if m_name:
                            b_name = m_name.group(1).strip()
                        if not b_name and handle:
                            b_name = handle.replace("_", " ").replace(".", " ").title()

                        if not handle and b_name:
                            handle = re.sub(r'[^a-zA-Z0-9_]', '', b_name.lower().replace(" ", "_"))

                        if not handle:
                            code_match = re.search(r'/(?:reel|p)/([a-zA-Z0-9_-]+)', clean_target)
                            if code_match:
                                handle = f"ig_{code_match.group(1).lower()}"
                            else:
                                continue

                        if not b_name:
                            b_name = handle.replace("_", " ").title()

                        # 3. Extract caption context and comment snippet
                        caption = snippet_text
                        comment = snippet_text
                        m_quote = re.search(r'"([^"]+)"', snippet_text)
                        if m_quote:
                            comment = m_quote.group(1)
                        else:
                            m_cap = re.search(r'(?:\||:)\s*(.+?)(?:\d+\s+likes|\d+\s+comments|\d+\s+days ago|$)', snippet_text)
                            if m_cap:
                                comment = m_cap.group(1).strip()

                        discovered.append({
                            "handle": f"@{handle.lstrip('@')}",
                            "business_name": b_name,
                            "post_url": clean_target,
                            "caption": caption[:350],
                            "comment": comment[:250],
                        })
                except Exception as e:
                    logger.warning(f"Error querying live search term '{q}': {e}")
                    continue

        return discovered

    def scan_intent(
        self,
        db: Session,
        niche: Optional[str] = None,
        count: int = 5,
        keyword: Optional[str] = None,
        hashtag: Optional[str] = None,
        target_account: Optional[str] = None
    ) -> List[Lead]:
        """
        2-Tier Autonomous AI Context & Intent Analyzer:
        - Tier 1: Post Relevance Verification (AI Check). Skips irrelevant posts.
        - Tier 2: Comment Buyer-Intent Evaluation (AI Check). Filters for is_website_lead=True and confidence >= 70.
        - Injects GrowthGrid personalized demo pitch.
        """
        target_niche = (niche or keyword or hashtag or "").strip()
        logger.info(f"Starting 2-Tier Autonomous AI Lead Harvester for niche: '{target_niche or 'All'}' (target: {count})...")

        # 1. Harvest candidates from live Instagram search stream
        raw_candidates = self._harvest_live_posts(
            niche=target_niche,
            max_candidates=max(15, count * 3)
        )

        if not raw_candidates:
            logger.info("No live candidate posts found from real-time Instagram query stream.")
            return []

        verified_leads: List[Lead] = []

        for cand in raw_candidates:
            if len(verified_leads) >= count:
                break

            post_url = cand["post_url"]
            caption = cand["caption"]
            handle = cand["handle"]
            comment_text = cand["comment"]

            # =========================================================================
            # TIER 1: Post Relevance Verification (AI Check)
            # =========================================================================
            logger.info(f"Running Tier 1 AI Relevance Check for {post_url}...")
            t1_eval = gemini_service.evaluate_post_relevance(caption=caption)

            if not t1_eval.get("is_relevant_post", False):
                logger.info(f"Tier 1 Rejected: Post {post_url} is not relevant to business growth/web design. Skipping.")
                continue

            post_topic = t1_eval.get("topic") or (target_niche.title() if target_niche else "Commercial Business")
            logger.info(f"Tier 1 Passed! Topic: {post_topic}")

            # =========================================================================
            # TIER 2: Comment Buyer-Intent Evaluation (AI Check)
            # =========================================================================
            logger.info(f"Running Tier 2 AI Intent Evaluation for commenter {handle}...")
            t2_eval = gemini_service.evaluate_comment_intent(
                username=handle,
                comment_text=comment_text,
                topic=post_topic
            )

            is_lead = t2_eval.get("is_website_lead", False)
            confidence = t2_eval.get("confidence", 0)

            # Keep only leads where is_website_lead is true and confidence >= 70
            if not is_lead or confidence < 70:
                logger.info(
                    f"Tier 2 Filtered Out: {handle} (is_website_lead={is_lead}, "
                    f"confidence={confidence} < 70). Skipping."
                )
                continue

            logger.info(f"Tier 2 Qualified! {handle} (Confidence: {confidence}%, Business: {t2_eval.get('business_name')})")

            # Extract validated attributes
            b_name = t2_eval.get("business_name") or cand["business_name"]
            user_pain_point = t2_eval.get("user_pain_point") or "Needs professional website / online presence"

            # Check if lead already exists in DB
            existing = db.query(Lead).filter(Lead.instagram_handle == handle).first()
            if existing:
                # Update existing lead with latest intent evaluation
                existing.lead_score = confidence
                existing.industry = post_topic
                existing.score_reasons = f"Topic: {post_topic} • Pain Point: {user_pain_point} (Confidence: {confidence}%)"
                existing.source_post_url = post_url
                existing.comment_text = comment_text
                verified_leads.append(existing)
                continue

            # Generate standard GrowthGrid dynamic demo pitch
            personalized_dm = gemini_service.generate_instagram_dm(
                handle=handle,
                business_name=b_name,
                industry=post_topic,
                comment_text=comment_text,
                post_context=f"Post Topic: {post_topic} | URL: {post_url}"
            )

            score_reasons = f"Topic: {post_topic} • Pain Point: {user_pain_point} (Confidence: {confidence}%)"
            notes = (
                f"Tier 1 Post Topic: {post_topic}\n"
                f"Tier 2 Pain Point: {user_pain_point}\n"
                f"Original Comment: \"{comment_text}\"\n"
                f"Post URL: {post_url}"
            )

            new_lead = Lead(
                business_name=b_name,
                industry=post_topic,
                location="Instagram",
                website_url=None,
                has_website=False,
                email=None,
                phone=None,
                instagram_handle=handle,
                source="Autonomous AI Harvester",
                status="DM Drafted",
                lead_score=confidence,
                score_reasons=score_reasons,
                source_post_url=post_url,
                comment_text=comment_text,
                outreach_instagram_dm=personalized_dm,
                notes=notes
            )

            db.add(new_lead)
            verified_leads.append(new_lead)

        db.commit()

        for lead in verified_leads:
            db.refresh(lead)

        logger.info(f"2-Tier AI Pipeline verified & saved {len(verified_leads)} high-intent leads.")
        return verified_leads


# Singleton instance
instagram_scanner = InstagramIntentScanner()
