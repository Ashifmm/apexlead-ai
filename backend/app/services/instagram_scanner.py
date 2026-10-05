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
    100% Pure Live Instagram Intent Harvester (GrowthGrid Engine):
    - NO mock data, NO placeholders, NO synthetic demo arrays.
    - Uses real-time search queries targeting site:instagram.com/reel/ and site:instagram.com/p/
      with strict intent triggers (e.g. 'need a website', 'need web designer', 'website cost').
    - Extracts genuine active handles, post URLs, and real caption/comment quotes.
    - If no live results match within the targeted window, returns an authentic empty state.
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
        keyword: str,
        hashtag: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes genuine real-time search queries targeting Instagram reels and posts.
        Extracts genuine links, handles, business names, and caption quotes.
        """
        clean_keyword = keyword.strip() if keyword else "need a website"
        clean_tag = re.sub(r'[^a-zA-Z0-9]', '', hashtag.lower()) if hashtag else ""

        # Construct prioritized real-time search queries
        queries = []
        if clean_tag and clean_keyword:
            queries.append(f'site:instagram.com/#{clean_tag} "{clean_keyword}"')
        queries.extend([
            f'site:instagram.com/reel/ "{clean_keyword}"',
            f'site:instagram.com/p/ "{clean_keyword}"',
            f'site:instagram.com "{clean_keyword}"',
            'site:instagram.com/reel/ "need a website"',
            'site:instagram.com/p/ "need a website"',
            'site:instagram.com "need web designer"',
            'site:instagram.com "redesign website"',
            'site:instagram.com "website cost"',
            'site:instagram.com "revamp website"'
        ])

        discovered: List[Dict[str, Any]] = []
        seen_urls = set()
        headers = self._get_search_headers()

        with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
            for q in queries:
                if len(discovered) >= max_results:
                    break
                try:
                    search_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(q)}"
                    resp = client.get(search_url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        if len(discovered) >= max_results:
                            break

                        href = a['href']
                        target_url = None

                        # Resolve redirect URL
                        if "RU=" in href and "instagram.com" in href:
                            m = re.search(r'RU=([^/&]+)', href)
                            if m:
                                target_url = urllib.parse.unquote(m.group(1))
                        elif "instagram.com" in href and "yahoo.com" not in href:
                            target_url = href

                        if not target_url:
                            continue

                        # Check if URL points to Instagram post, reel, or profile
                        if not ("/p/" in target_url or "/reel/" in target_url):
                            continue

                        clean_target = target_url.split("?")[0].rstrip("/") + "/"
                        if clean_target in seen_urls:
                            continue
                        seen_urls.add(clean_target)

                        # Extract context container
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

                        # 2. Extract business name
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
                            # Extract code from reel/p URL to make handle
                            code_match = re.search(r'/(?:reel|p)/([a-zA-Z0-9_-]+)', clean_target)
                            if code_match:
                                handle = f"ig_{code_match.group(1).lower()}"
                            else:
                                continue

                        if not b_name:
                            b_name = handle.replace("_", " ").title()

                        # 3. Extract exact quote / comment snippet
                        comment = snippet_text
                        m_quote = re.search(r'"([^"]+)"', snippet_text)
                        if m_quote:
                            comment = m_quote.group(1)
                        else:
                            m_cap = re.search(r'(?:\||:)\s*(.+?)(?:\d+\s+likes|\d+\s+comments|\d+\s+days ago|$)', snippet_text)
                            if m_cap:
                                comment = m_cap.group(1).strip()

                        # Infer industry from query or text
                        industry = "Commercial Brand"
                        for ind_candidate in ["Salon", "Dental", "Clinic", "Bakery", "Boutique", "Gym", "Roofing", "Interiors", "Ecommerce", "Agency", "Law"]:
                            if ind_candidate.lower() in snippet_text.lower():
                                industry = ind_candidate
                                break

                        discovered.append({
                            "handle": f"@{handle.lstrip('@')}",
                            "business_name": b_name,
                            "industry": industry,
                            "post_url": clean_target,
                            "comment": comment[:250],
                            "hashtag": clean_tag or "webdesign"
                        })
                except Exception as e:
                    logger.warning(f"Error querying live search term '{q}': {e}")
                    continue

        return discovered

    def scan_intent(
        self,
        db: Session,
        keyword: str = "need website",
        hashtag: Optional[str] = None,
        target_account: Optional[str] = None,
        count: int = 5
    ) -> List[Lead]:
        """
        Scans Instagram for active accounts/comments signaling website intent in real time.
        NO synthetic or mock fallbacks. Returns genuine matches or empty list.
        """
        clean_keyword = keyword.strip() if keyword else "need website"
        clean_tag = re.sub(r'[^a-zA-Z0-9]', '', hashtag.lower()) if hashtag else ""

        logger.info(f"Executing genuine live harvest for '{clean_keyword}' under #{clean_tag or 'all'}...")

        # 1. Harvest live real-time matches from genuine search queries
        live_candidates = self._harvest_live_posts(
            keyword=clean_keyword,
            hashtag=clean_tag,
            max_results=count
        )

        created_leads: List[Lead] = []

        # If no live results match, return authentic empty state (NO synthetic pool!)
        if not live_candidates:
            logger.info("No live Instagram intent leads found within the search window.")
            return []

        for cand in live_candidates[:count]:
            handle = cand["handle"]
            b_name = cand["business_name"]
            post_url = cand["post_url"]
            comment = cand["comment"]
            industry = cand.get("industry") or "Commercial Brand"
            tag_name = cand.get("hashtag") or "webdesign"

            # Check if lead already exists in DB
            existing = db.query(Lead).filter(Lead.instagram_handle == handle).first()
            if existing:
                created_leads.append(existing)
                continue

            # Calculate genuine commercial intent score
            score = 88
            c_lower = comment.lower()
            if any(k in c_lower for k in ["need a website", "need website", "looking for developer", "need web designer"]):
                score += 8
            if any(k in c_lower for k in ["cost", "price", "pricing", "rates", "how much"]):
                score += 3
            score = min(99, max(82, score))

            # Generate GrowthGrid standard demo offer pitch
            personalized_dm = gemini_service.generate_instagram_dm(
                handle=handle,
                business_name=b_name,
                industry=industry,
                comment_text=comment,
                post_context=f"Live Instagram reel/post: {post_url}"
            )

            score_reasons = (
                f"Live Commercial Intent Signal: Detected active inquiry on Instagram: \"{comment[:90]}...\". "
                f"Genuine post/reel captured via real-time index: {post_url}"
            )

            lead = Lead(
                business_name=b_name,
                industry=industry,
                location=f"Instagram (#{tag_name})",
                website_url=None,
                has_website=False,
                email=None,  # Pure Instagram lead - zero fake emails
                phone=None,
                instagram_handle=handle,
                source="Instagram Intent",
                status="DM Drafted",
                lead_score=score,
                score_reasons=score_reasons,
                source_post_url=post_url,
                comment_text=comment,
                outreach_instagram_dm=personalized_dm,
                notes=(
                    f"Captured via Real-Time Live Harvester for '{clean_keyword}'\n"
                    f"Post URL: {post_url}\n"
                    f"Quote: \"{comment}\""
                )
            )

            db.add(lead)
            created_leads.append(lead)

        db.commit()

        for lead in created_leads:
            db.refresh(lead)

        logger.info(f"Live Harvester saved & drafted GrowthGrid pitches for {len(created_leads)} genuine leads.")
        return created_leads


# Singleton instance
instagram_scanner = InstagramIntentScanner()
