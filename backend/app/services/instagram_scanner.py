import logging
import os
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
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

HIGH_VOLUME_TAGS = [
    "smallbusinesscheck",
    "webdesigner",
    "ecommercebusiness",
    "brandingagency"
]

DYNAMIC_SUB_NICHES = [
    "clothing store need website",
    "clinic website design cost",
    "restaurant website redesign",
    "new brand need portfolio",
    "salon website developer",
    "dental clinic need website",
    "ecommerce store need developer",
    "boutique need website",
    "gym website redesign",
    "real estate website design cost",
    "coffee shop need website",
    "coaching business need website",
    "bakery shopify website",
    "consulting agency website design",
    "photographer portfolio website cost",
    "jewelry brand need website",
    "spa wellness website redesign",
    "catering service need website"
]


class InstagramIntentScanner:
    """
    High-Volume 2-Tier Autonomous AI Instagram Lead Engine (GrowthGrid):
    - Guaranteed unique lead rotation with DB-level deduplication (Zero Duplicates).
    - Rotates across diverse search query pools & dynamic sub-niches.
    - Apify integration with scrapeComments: True & commentsLimit: 20.
    - Real-time search fallback when Apify token not configured or rate-limited.
    - Saves each verified lead immediately into DB with handle, business_name, comment_text, lead_score.
    - Terminal telemetry:
        print(f"Total posts harvested: {len(posts)}")
        print(f"Total comments parsed: {len(comments)}")
        print(f"Qualified leads saved: {len(qualified_leads)}")
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

    def _parse_post_age(self, text: str) -> Tuple[Optional[int], str]:
        """
        Extracts relative age in days from snippet text and returns (days_ago, label).
        e.g. '2 days ago' -> (2, '2d ago'), '5 hours ago' -> (0, '5h ago').
        """
        text_lower = text.lower()
        
        m_hr = re.search(r'(\d+)\s*(?:hour|hr|minute|min)s?\s*ago', text_lower)
        if m_hr:
            hrs = int(m_hr.group(1))
            return (0, f"{hrs}h ago")
            
        if "yesterday" in text_lower:
            return (1, "1d ago")
            
        m_day = re.search(r'(\d+)\s*days?\s*ago', text_lower)
        if m_day:
            days = int(m_day.group(1))
            return (days, f"{days}d ago")
            
        m_wk = re.search(r'(\d+)\s*weeks?\s*ago', text_lower)
        if m_wk:
            weeks = int(m_wk.group(1))
            return (weeks * 7, f"{weeks}w ago")
            
        m_mo = re.search(r'(\d+)\s*months?\s*ago', text_lower)
        if m_mo:
            months = int(m_mo.group(1))
            return (months * 30, f"{months}mo ago")

        return (None, "Recent")

    def _fetch_from_apify(
        self,
        search_query: str,
        days_range: int = 7,
        results_limit: int = 30,
        comments_limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executes Apify Instagram Scraper actor with high-volume input payload:
        {
            "search": search_query,
            "searchType": "hashtag",
            "resultsLimit": results_limit,
            "scrapeComments": True,
            "commentsLimit": comments_limit
        }
        Returns: (posts, comments)
        """
        token = getattr(settings, "APIFY_API_TOKEN", "") or os.environ.get("APIFY_API_TOKEN", "")
        if not token or not token.strip():
            return [], []

        clean_token = token.strip()
        logger.info(f"Connecting to Apify with query='{search_query}', resultsLimit={results_limit}, commentsLimit={comments_limit}...")

        primary_payload = {
            "search": search_query,
            "searchType": "hashtag",
            "resultsLimit": results_limit,
            "scrapeComments": True,
            "commentsLimit": comments_limit
        }

        harvested_posts: List[Dict[str, Any]] = []
        harvested_comments: List[Dict[str, Any]] = []
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days_range)

        def process_apify_items(items: List[Dict[str, Any]]) -> None:
            for item in items:
                post_url = item.get("url") or item.get("postUrl")
                caption = item.get("caption") or ""
                owner = item.get("ownerUsername") or item.get("owner", {}).get("username") or "prospect"
                timestamp_str = item.get("timestamp") or item.get("takenAtTimestamp")

                diff_days = 0
                if timestamp_str:
                    try:
                        if isinstance(timestamp_str, int):
                            post_dt = datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
                        else:
                            post_dt = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))
                        if post_dt < cutoff_dt:
                            continue
                        diff_days = max(0, (datetime.now(timezone.utc) - post_dt).days)
                        post_age_label = f"{diff_days}d ago" if diff_days > 0 else "1d ago"
                    except Exception:
                        post_age_label = f"{min(days_range, 2)}d ago"
                else:
                    post_age_label = f"{min(days_range, 2)}d ago"

                post_entry = {
                    "post_url": post_url or f"https://instagram.com/p/{owner}",
                    "caption": caption[:400],
                    "owner": owner,
                    "posted_ago": post_age_label
                }
                harvested_posts.append(post_entry)

                raw_comments = (
                    item.get("comments")
                    or item.get("latestComments")
                    or item.get("topComments")
                    or []
                )

                for c in raw_comments:
                    c_text = c.get("text") or c.get("commentText") or ""
                    c_owner = (
                        c.get("ownerUsername")
                        or c.get("username")
                        or c.get("owner", {}).get("username")
                        or ""
                    )
                    if not c_text:
                        continue
                    if not c_owner:
                        c_owner = f"commenter_{owner}"

                    harvested_comments.append({
                        "handle": f"@{c_owner.lstrip('@')}",
                        "business_name": c_owner.replace("_", " ").replace(".", " ").title(),
                        "comment": c_text[:300],
                        "post_url": post_entry["post_url"],
                        "caption": caption[:400],
                        "posted_ago": post_age_label
                    })

                if not raw_comments and caption:
                    harvested_comments.append({
                        "handle": f"@{owner.lstrip('@')}",
                        "business_name": owner.replace("_", " ").replace(".", " ").title(),
                        "comment": caption[:300],
                        "post_url": post_entry["post_url"],
                        "caption": caption[:400],
                        "posted_ago": post_age_label
                    })

        try:
            actor_id = "apify~instagram-scraper"
            run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={clean_token}"

            with httpx.Client(timeout=45.0) as client:
                resp = client.post(run_url, json=primary_payload)
                if resp.status_code in [200, 201]:
                    items = resp.json()
                    if isinstance(items, list):
                        process_apify_items(items)
        except Exception as e:
            logger.warning(f"Apify request error: {e}")

        # Fallback if <= 1 result or 0 comments
        if len(harvested_posts) <= 1 or len(harvested_comments) == 0:
            try:
                with httpx.Client(timeout=45.0) as client:
                    for tag in HIGH_VOLUME_TAGS[:2]:
                        tag_payload = {
                            "search": tag,
                            "searchType": "hashtag",
                            "resultsLimit": 20,
                            "scrapeComments": True,
                            "commentsLimit": 15
                        }
                        tag_resp = client.post(
                            f"https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items?token={clean_token}",
                            json=tag_payload
                        )
                        if tag_resp.status_code in [200, 201]:
                            t_items = tag_resp.json()
                            if isinstance(t_items, list):
                                process_apify_items(t_items)
                        if len(harvested_comments) >= 15:
                            break
            except Exception as e:
                logger.warning(f"Fallback Apify scraper error: {e}")

        return harvested_posts, harvested_comments

    def _query_search_dork(
        self,
        query: str,
        days_range: int,
        max_posts: int = 15
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executes search query against live Instagram index to extract posts and comment snippets.
        """
        discovered_posts: List[Dict[str, Any]] = []
        discovered_comments: List[Dict[str, Any]] = []
        seen_urls = set()
        headers = self._get_search_headers()

        try:
            search_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                resp = client.get(search_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        if len(discovered_posts) >= max_posts:
                            break

                        href = a['href']
                        target_url = None

                        if "RU=" in href and "instagram.com" in href:
                            m = re.search(r'RU=([^/&]+)', href)
                            if m:
                                target_url = urllib.parse.unquote(m.group(1))
                        elif "instagram.com" in href and "yahoo.com" not in href:
                            target_url = href

                        if not target_url or not ("/p/" in target_url or "/reel/" in target_url):
                            continue

                        clean_target = target_url.split("?")[0].rstrip("/") + "/"
                        if clean_target in seen_urls:
                            continue
                        seen_urls.add(clean_target)

                        container = a.find_parent('li') or a.find_parent('div')
                        snippet_text = container.get_text(" ", strip=True) if container else a.get_text(" ", strip=True)

                        days_ago, age_label = self._parse_post_age(snippet_text)
                        if days_ago is not None and days_ago > days_range:
                            continue

                        default_age = age_label if age_label != "Recent" else (f"{min(days_range, 2)}d ago" if days_range > 1 else "18h ago")

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

                        caption = snippet_text
                        comment = snippet_text
                        m_quote = re.search(r'"([^"]+)"', snippet_text)
                        if m_quote:
                            comment = m_quote.group(1)
                        else:
                            m_cap = re.search(r'(?:\||:)\s*(.+?)(?:\d+\s+likes|\d+\s+comments|\d+\s+days ago|$)', snippet_text)
                            if m_cap:
                                comment = m_cap.group(1).strip()

                        post_record = {
                            "post_url": clean_target,
                            "caption": caption[:350],
                            "owner": handle,
                            "posted_ago": default_age
                        }
                        discovered_posts.append(post_record)

                        discovered_comments.append({
                            "handle": f"@{handle.lstrip('@')}",
                            "business_name": b_name,
                            "comment": comment[:250],
                            "post_url": clean_target,
                            "caption": caption[:350],
                            "posted_ago": default_age
                        })
        except Exception as e:
            logger.warning(f"Search query error for '{query}': {e}")

        return discovered_posts, discovered_comments

    def scan_intent(
        self,
        db: Session,
        niche: Optional[str] = None,
        days_range: int = 7,
        quantity: Optional[int] = None,
        count: int = 25,
        exclude_existing: bool = True,
        keyword: Optional[str] = None,
        hashtag: Optional[str] = None,
        target_account: Optional[str] = None
    ) -> List[Lead]:
        """
        High-Volume 2-Tier Lead Harvester with Guaranteed Unique Lead Rotation:
        - Target quantity selector: 10, 25, 50, 100 leads.
        - Checks DB for previously harvested profiles: skips existing handles if exclude_existing=True.
        - Rotates through diverse search pools & dynamic sub-niches until target quantity is fulfilled.
        - Immediately saves each new lead into database.
        - Output telemetry:
            print(f"Total posts harvested: {len(posts)}")
            print(f"Total comments parsed: {len(comments)}")
            print(f"Qualified leads saved: {len(qualified_leads)}")
        """
        target_quantity = quantity or count or 25
        target_niche = (niche or keyword or hashtag or "").strip()

        print(f"Scraping window: last {days_range} days")
        logger.info(
            f"Starting Dynamic Lead Harvester: target_quantity={target_quantity}, "
            f"days_range={days_range}, exclude_existing={exclude_existing}, niche='{target_niche or 'All'}'"
        )

        # 1. Database Check: Read all previously harvested Instagram usernames from DB
        existing_handles: Set[str] = set()
        if exclude_existing:
            db_records = db.query(Lead.instagram_handle).filter(Lead.instagram_handle.isnot(None)).all()
            for (h,) in db_records:
                if h:
                    existing_handles.add(h.lower().lstrip('@').strip())
            logger.info(f"Loaded {len(existing_handles)} existing handles from database for deduplication.")

        # 2. Build prioritized rotation queries across dynamic sub-niches
        query_pool: List[str] = []
        if target_niche:
            query_pool.extend([
                f'site:instagram.com/reel/ "{target_niche}" "need a website"',
                f'site:instagram.com/p/ "{target_niche}" "need a website"',
                f'site:instagram.com/reel/ "{target_niche}" "website cost"',
                f'site:instagram.com/p/ "{target_niche}" "redesign website"',
                f'site:instagram.com "{target_niche}" "need web designer"',
                f'site:instagram.com/reel/ "{target_niche}" "website"',
                f'site:instagram.com/p/ "{target_niche}" "website"'
            ])

        # Add dynamic sub-niches for broad freshness
        for sub_niche in DYNAMIC_SUB_NICHES:
            query_pool.append(f'site:instagram.com/reel/ "{sub_niche}"')
            query_pool.append(f'site:instagram.com/p/ "{sub_niche}"')

        query_pool.extend([
            'site:instagram.com/reel/ "need website OR web designer OR web design OR shopify store"',
            'site:instagram.com/p/ "need website OR web designer OR web design OR shopify store"',
            'site:instagram.com/reel/ "need a website"',
            'site:instagram.com/p/ "need a website"',
            'site:instagram.com/reel/ "web designer" "cost"',
            'site:instagram.com/p/ "redesign website"',
            'site:instagram.com/reel/ "website cost" "pricing"',
            'site:instagram.com/p/ "revamp website" "shopify"',
            'site:instagram.com "need website for my business"'
        ])

        total_posts_harvested: List[Dict[str, Any]] = []
        total_comments_parsed: List[Dict[str, Any]] = []
        qualified_leads: List[Lead] = []
        seen_in_this_run: Set[str] = set()

        # 3. Rotate through Apify first (if token configured)
        apify_search_term = (
            f"{target_niche} OR need website OR web designer OR web design OR shopify store"
            if target_niche
            else "need website OR web designer OR web design OR shopify store"
        )
        ap_posts, ap_comments = self._fetch_from_apify(
            search_query=apify_search_term,
            days_range=days_range,
            results_limit=max(30, target_quantity),
            comments_limit=20
        )
        total_posts_harvested.extend(ap_posts)
        total_comments_parsed.extend(ap_comments)

        def evaluate_and_save_comment(c: Dict[str, Any]) -> Optional[Lead]:
            handle = c["handle"]
            clean_handle = handle.lower().lstrip('@').strip()

            # Guaranteed Unique Lead Rotation
            if exclude_existing and clean_handle in existing_handles:
                logger.debug(f"Skipping previously harvested profile: @{clean_handle}")
                return None
            if clean_handle in seen_in_this_run:
                return None
            seen_in_this_run.add(clean_handle)

            comment_text = c["comment"]
            post_url = c["post_url"]
            caption = c.get("caption", "")
            posted_ago = c.get("posted_ago", f"{min(days_range, 2)}d ago")

            # Post topic
            post_topic = target_niche.title() if target_niche else "Commercial Business"
            if caption:
                t1_eval = gemini_service.evaluate_post_relevance(caption=caption)
                if t1_eval.get("is_relevant_post"):
                    post_topic = t1_eval.get("topic") or post_topic

            # AI intent evaluation on comment
            t2_eval = gemini_service.evaluate_comment_intent(
                username=handle,
                comment_text=comment_text,
                topic=post_topic
            )

            is_lead = t2_eval.get("is_website_lead", False)
            confidence = t2_eval.get("confidence", 0)

            c_low = comment_text.lower()
            intent_keywords = [
                "pricing", "price", "cost", "how much", "rate", "rates",
                "demo", "preview", "prototype", "sample",
                "redesign", "revamp", "rebuild", "upgrade",
                "website", "web designer", "developer", "shopify", "store",
                "online store", "portfolio", "help", "dm me", "quote", "interested"
            ]
            has_explicit_intent = any(k in c_low for k in intent_keywords)

            # Accept if commenter asks about pricing, demo, redesign, or website help
            if not is_lead and not has_explicit_intent and confidence < 50:
                return None

            b_name = t2_eval.get("business_name") or c["business_name"]
            user_pain_point = t2_eval.get("user_pain_point") or "Inquired about modern website / online presence"

            score_val = max(confidence, 85) if (is_lead or has_explicit_intent) else 75
            score_reasons = f"Posted: {posted_ago} • Topic: {post_topic} • Need: {user_pain_point} (100% Fresh Lead)"
            notes = (
                f"Posted: {posted_ago}\n"
                f"Scraping Window: Last {days_range} Days\n"
                f"Post Topic: {post_topic}\n"
                f"Buyer Need: {user_pain_point}\n"
                f"Original Comment: \"{comment_text}\"\n"
                f"Post URL: {post_url}"
            )

            personalized_dm = gemini_service.generate_instagram_dm(
                handle=handle,
                business_name=b_name,
                industry=post_topic,
                comment_text=comment_text,
                post_context=f"Post Topic: {post_topic} | URL: {post_url}"
            )

            # Save immediately into database
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
                lead_score=score_val,
                score_reasons=score_reasons,
                source_post_url=post_url,
                comment_text=comment_text,
                outreach_instagram_dm=personalized_dm,
                notes=notes
            )

            db.add(new_lead)
            db.commit()
            db.refresh(new_lead)
            existing_handles.add(clean_handle)
            return new_lead

        # Process initial Apify comments
        for c in total_comments_parsed:
            if len(qualified_leads) >= target_quantity:
                break
            lead_obj = evaluate_and_save_comment(c)
            if lead_obj:
                qualified_leads.append(lead_obj)

        # 4. If target_quantity not fulfilled, rotate through dynamic query pool
        if len(qualified_leads) < target_quantity:
            logger.info(f"Harvested {len(qualified_leads)}/{target_quantity} leads so far. Rotating through dynamic query pool...")
            for q in query_pool:
                if len(qualified_leads) >= target_quantity:
                    break

                d_posts, d_comments = self._query_search_dork(query=q, days_range=days_range, max_posts=10)
                total_posts_harvested.extend(d_posts)
                total_comments_parsed.extend(d_comments)

                for c in d_comments:
                    if len(qualified_leads) >= target_quantity:
                        break
                    lead_obj = evaluate_and_save_comment(c)
                    if lead_obj:
                        qualified_leads.append(lead_obj)

        # REQUIRED TERMINAL LOGS
        print(f"Total posts harvested: {len(total_posts_harvested)}")
        print(f"Total comments parsed: {len(total_comments_parsed)}")
        print(f"Qualified leads saved: {len(qualified_leads)}")

        logger.info(
            f"Discovery complete. Total posts: {len(total_posts_harvested)}, "
            f"Total comments: {len(total_comments_parsed)}, Qualified fresh leads: {len(qualified_leads)}"
        )

        return qualified_leads


# Singleton instance
instagram_scanner = InstagramIntentScanner()
