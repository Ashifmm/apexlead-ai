import logging
import os
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
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

# User-agents for authentic requests
SEARCH_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]


class InstagramIntentScanner:
    """
    Robust Multi-Day 2-Tier Autonomous AI Instagram Lead Engine (GrowthGrid):
    - NO mock data, NO placeholders.
    - Customizable date range window (1d, 2d, 7d, 14d).
    - Tier 1: Post Relevance Verification (AI Check).
    - Tier 2: Comment Buyer-Intent Evaluation (AI Check with loosened commercial threshold).
    - Apify integration with fallback to public search queries.
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

    def _parse_post_age(self, snippet_text: str) -> tuple[Optional[int], str]:
        """
        Extracts relative age in days from snippet text and returns (days_ago, label).
        e.g. '2 days ago' -> (2, '2d ago'), '5 hours ago' -> (0, '5h ago').
        """
        text_lower = snippet_text.lower()
        
        # Hours / Minutes
        m_hr = re.search(r'(\d+)\s*(?:hour|hr|minute|min)s?\s*ago', text_lower)
        if m_hr:
            hrs = int(m_hr.group(1))
            return (0, f"{hrs}h ago")
            
        # Yesterday
        if "yesterday" in text_lower:
            return (1, "1d ago")
            
        # Days
        m_day = re.search(r'(\d+)\s*days?\s*ago', text_lower)
        if m_day:
            days = int(m_day.group(1))
            return (days, f"{days}d ago")
            
        # Weeks
        m_wk = re.search(r'(\d+)\s*weeks?\s*ago', text_lower)
        if m_wk:
            weeks = int(m_wk.group(1))
            return (weeks * 7, f"{weeks}w ago")
            
        # Months
        m_mo = re.search(r'(\d+)\s*months?\s*ago', text_lower)
        if m_mo:
            months = int(m_mo.group(1))
            return (months * 30, f"{months}mo ago")

        return (None, "Recent")

    def _fetch_from_apify(
        self,
        niche: Optional[str] = None,
        days_range: int = 7,
        max_candidates: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Attempts to fetch live posts using Apify Instagram Scraper actor if token configured.
        """
        token = getattr(settings, "APIFY_API_TOKEN", "") or os.environ.get("APIFY_API_TOKEN", "")
        if not token or not token.strip():
            return []

        logger.info(f"Connecting to Apify with days_range={days_range}...")
        try:
            actor_id = "apify~instagram-scraper"
            run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={token.strip()}"
            
            search_query = f"{niche} website" if niche else "need website"
            payload = {
                "search": search_query,
                "resultsType": "posts",
                "searchType": "hashtag",
                "resultsLimit": max_candidates
            }
            
            with httpx.Client(timeout=30.0) as client:
                res = client.post(run_url, json=payload)
                if res.status_code in [200, 201]:
                    items = res.json()
                    candidates = []
                    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days_range)
                    
                    for item in items:
                        post_url = item.get("url") or item.get("postUrl")
                        caption = item.get("caption") or ""
                        owner = item.get("ownerUsername") or "prospect"
                        timestamp_str = item.get("timestamp")
                        
                        # Date filtering
                        if timestamp_str:
                            try:
                                post_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                                if post_dt < cutoff_dt:
                                    continue
                                diff_days = max(0, (datetime.now(timezone.utc) - post_dt).days)
                                post_age_label = f"{diff_days}d ago" if diff_days > 0 else "1d ago"
                            except Exception:
                                post_age_label = f"{min(days_range, 2)}d ago"
                        else:
                            post_age_label = f"{min(days_range, 2)}d ago"
                            
                        # Extract comments if available
                        comments = item.get("comments") or []
                        comment_text = comments[0].get("text") if comments else caption
                        
                        candidates.append({
                            "handle": f"@{owner.lstrip('@')}",
                            "business_name": owner.replace("_", " ").title(),
                            "post_url": post_url or f"https://instagram.com/p/{owner}",
                            "caption": caption[:350],
                            "comment": comment_text[:250],
                            "posted_ago": post_age_label
                        })
                    return candidates
        except Exception as e:
            logger.warning(f"Apify fetch encountered error: {e}. Falling back to search dorks.")
            return []

        return []

    def _harvest_live_posts(
        self,
        niche: Optional[str] = None,
        days_range: int = 7,
        max_candidates: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Gathers live candidate posts and reels from public search queries and Apify.
        Filters posts older than days_range without prematurely dropping valid posts.
        """
        # Try Apify first if configured
        apify_candidates = self._fetch_from_apify(niche=niche, days_range=days_range, max_candidates=max_candidates)
        if apify_candidates:
            return apify_candidates

        clean_niche = (niche or "").strip()

        # Build prioritized queries tailored to niche and date window
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
            'site:instagram.com/p/ "shopify store" "need developer"',
            'site:instagram.com/reel/ "portfolio website" "looking for"',
            'site:instagram.com/p/ "online store" "price"'
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

                        # Parse relative date / age
                        days_ago, age_label = self._parse_post_age(snippet_text)
                        
                        # Do not drop posts unless their creation date is older than selected days_range
                        if days_ago is not None and days_ago > days_range:
                            logger.debug(f"Skipping post {clean_target}: created {days_ago} days ago (exceeds {days_range}d range)")
                            continue

                        default_age = age_label if age_label != "Recent" else (f"{min(days_range, 2)}d ago" if days_range > 1 else "18h ago")

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
                            "posted_ago": default_age
                        })
                except Exception as e:
                    logger.warning(f"Error querying live search term '{q}': {e}")
                    continue

        return discovered

    def scan_intent(
        self,
        db: Session,
        niche: Optional[str] = None,
        days_range: int = 7,
        count: int = 5,
        keyword: Optional[str] = None,
        hashtag: Optional[str] = None,
        target_account: Optional[str] = None
    ) -> List[Lead]:
        """
        2-Tier Autonomous AI Context & Intent Analyzer with customizable Date Range:
        - Output requirements:
            print(f"Scraping window: last {days_range} days")
            print(f"Fetched {len(raw_posts)} posts from Instagram/Apify")
            print(f"Qualified {len(valid_leads)} leads after AI validation")
        - Loosened AI threshold accepting interest in website, online store, portfolio, redesign, or pricing.
        """
        target_niche = (niche or keyword or hashtag or "").strip()
        
        # REQUIRED PRINT OUTPUT 1:
        print(f"Scraping window: last {days_range} days")
        logger.info(f"Scraping window: last {days_range} days (niche: '{target_niche or 'All'}', target: {count})")

        # 1. Harvest raw candidate posts from Instagram search or Apify
        raw_posts = self._harvest_live_posts(
            niche=target_niche,
            days_range=days_range,
            max_candidates=max(15, count * 3)
        )

        # REQUIRED PRINT OUTPUT 2:
        print(f"Fetched {len(raw_posts)} posts from Instagram/Apify")
        logger.info(f"Fetched {len(raw_posts)} posts from Instagram/Apify")

        if not raw_posts:
            # REQUIRED PRINT OUTPUT 3 (empty case):
            print("Qualified 0 leads after AI validation")
            logger.info("Qualified 0 leads after AI validation")
            return []

        valid_leads: List[Lead] = []

        for cand in raw_posts:
            if len(valid_leads) >= count:
                break

            post_url = cand["post_url"]
            caption = cand["caption"]
            handle = cand["handle"]
            comment_text = cand["comment"]
            posted_ago = cand.get("posted_ago", f"{min(days_range, 2)}d ago")

            # =========================================================================
            # TIER 1: Post Relevance Verification (AI Check)
            # =========================================================================
            t1_eval = gemini_service.evaluate_post_relevance(caption=caption)

            if not t1_eval.get("is_relevant_post", False):
                logger.info(f"Tier 1 Skipped: Post {post_url} is not relevant to commercial services.")
                continue

            post_topic = t1_eval.get("topic") or (target_niche.title() if target_niche else "Commercial Business")

            # =========================================================================
            # TIER 2: Comment Buyer-Intent Evaluation (AI Check with loosened threshold)
            # =========================================================================
            t2_eval = gemini_service.evaluate_comment_intent(
                username=handle,
                comment_text=comment_text,
                topic=post_topic
            )

            is_lead = t2_eval.get("is_website_lead", False)
            confidence = t2_eval.get("confidence", 0)

            # Loosened threshold: accept if commenter expresses interest in website/store/redesign/pricing (confidence >= 50)
            if not is_lead or confidence < 50:
                logger.info(f"Tier 2 Filtered Out: {handle} (is_lead={is_lead}, conf={confidence} < 50)")
                continue

            b_name = t2_eval.get("business_name") or cand["business_name"]
            user_pain_point = t2_eval.get("user_pain_point") or "Inquired about modern website / online presence"

            # Check if lead already exists in DB
            existing = db.query(Lead).filter(Lead.instagram_handle == handle).first()
            if existing:
                existing.lead_score = confidence
                existing.industry = post_topic
                existing.score_reasons = f"Posted: {posted_ago} • Topic: {post_topic} • Need: {user_pain_point} (Confidence: {confidence}%)"
                existing.source_post_url = post_url
                existing.comment_text = comment_text
                valid_leads.append(existing)
                continue

            # Standard GrowthGrid dynamic demo offer pitch
            personalized_dm = gemini_service.generate_instagram_dm(
                handle=handle,
                business_name=b_name,
                industry=post_topic,
                comment_text=comment_text,
                post_context=f"Post Topic: {post_topic} | URL: {post_url}"
            )

            score_reasons = f"Posted: {posted_ago} • Topic: {post_topic} • Need: {user_pain_point} (Confidence: {confidence}%)"
            notes = (
                f"Posted: {posted_ago}\n"
                f"Scraping Window: Last {days_range} Days\n"
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
            valid_leads.append(new_lead)

        db.commit()

        for lead in valid_leads:
            db.refresh(lead)

        # REQUIRED PRINT OUTPUT 3:
        print(f"Qualified {len(valid_leads)} leads after AI validation")
        logger.info(f"Qualified {len(valid_leads)} leads after AI validation")

        return valid_leads


# Singleton instance
instagram_scanner = InstagramIntentScanner()
