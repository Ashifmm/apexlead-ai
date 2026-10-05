import logging
import os
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
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


class InstagramIntentScanner:
    """
    High-Volume 2-Tier Autonomous AI Instagram Lead Engine (GrowthGrid):
    - Apify integration with scrapeComments: True & commentsLimit: 20
    - Fallback scraper using high-volume tags & comment scrapers
    - Loops through all harvested comments across all posts
    - AI buyer-intent evaluation accepting pricing, demo, redesign, or website help
    - Exact required terminal telemetry outputs
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
        niche: Optional[str] = None,
        days_range: int = 7,
        results_limit: int = 30,
        comments_limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executes Apify Instagram Scraper actor with high-volume input payload:
        {
            "search": "need website OR web designer OR web design OR shopify store",
            "searchType": "hashtag",
            "resultsLimit": 30,
            "scrapeComments": True,
            "commentsLimit": 20
        }
        Includes fallback to dedicated comment scraper and high-volume tags if <= 1 result returned.
        Returns: (posts, comments)
        """
        token = getattr(settings, "APIFY_API_TOKEN", "") or os.environ.get("APIFY_API_TOKEN", "")
        if not token or not token.strip():
            return [], []

        clean_token = token.strip()
        logger.info(f"Connecting to Apify with scrapeComments=True, resultsLimit={results_limit}, commentsLimit={comments_limit}...")

        search_query = (
            f"{niche} OR need website OR web designer OR web design OR shopify store"
            if niche
            else "need website OR web designer OR web design OR shopify store"
        )

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

                # Date filtering
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

                # Extract comments
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

                # If post had no comments but caption is an inquiry, preserve caption as a comment lead
                if not raw_comments and caption:
                    harvested_comments.append({
                        "handle": f"@{owner.lstrip('@')}",
                        "business_name": owner.replace("_", " ").replace(".", " ").title(),
                        "comment": caption[:300],
                        "post_url": post_entry["post_url"],
                        "caption": caption[:400],
                        "posted_ago": post_age_label
                    })

        # 1. Attempt Primary Apify Scraper Actor
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
            logger.warning(f"Primary Apify actor encountered error: {e}")

        # 2. Fallback Scraper Actor (if <= 1 result or 0 comments returned)
        if len(harvested_posts) <= 1 or len(harvested_comments) == 0:
            logger.info("Primary Apify run returned <= 1 result. Triggering Fallback Scraper with high-volume tags...")
            try:
                with httpx.Client(timeout=45.0) as client:
                    # Strategy A: Dedicated comment scraper if we have post URLs
                    if harvested_posts:
                        post_urls = [p["post_url"] for p in harvested_posts if p.get("post_url")]
                        comment_actor_id = "apify~instagram-comment-scraper"
                        comment_run_url = f"https://api.apify.com/v2/acts/{comment_actor_id}/run-sync-get-dataset-items?token={clean_token}"
                        comment_payload = {
                            "directUrls": post_urls,
                            "resultsLimit": 50
                        }
                        c_resp = client.post(comment_run_url, json=comment_payload)
                        if c_resp.status_code in [200, 201]:
                            c_items = c_resp.json()
                            if isinstance(c_items, list):
                                for c_item in c_items:
                                    c_text = c_item.get("text") or ""
                                    c_owner = c_item.get("ownerUsername") or c_item.get("username") or "user"
                                    c_url = c_item.get("postUrl") or post_urls[0]
                                    if c_text:
                                        harvested_comments.append({
                                            "handle": f"@{c_owner.lstrip('@')}",
                                            "business_name": c_owner.replace("_", " ").title(),
                                            "comment": c_text[:300],
                                            "post_url": c_url,
                                            "caption": "Instagram post context",
                                            "posted_ago": "1d ago"
                                        })

                    # Strategy B: High-volume tags fallback search
                    if len(harvested_comments) < 5:
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

    def _harvest_posts_and_comments(
        self,
        niche: Optional[str] = None,
        days_range: int = 7,
        max_posts: int = 30,
        max_comments_per_post: int = 20
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Harvests high-volume posts and all their comments via Apify (with search dork fallback).
        Returns: (posts, comments)
        """
        # 1. Try Apify first
        apify_posts, apify_comments = self._fetch_from_apify(
            niche=niche,
            days_range=days_range,
            results_limit=max_posts,
            comments_limit=max_comments_per_post
        )

        if apify_posts and apify_comments:
            return apify_posts, apify_comments

        # 2. Public Search Dork Fallback (extracts posts & comment snippets)
        clean_niche = (niche or "").strip()
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
            'site:instagram.com/reel/ "need website OR web designer OR web design OR shopify store"',
            'site:instagram.com/p/ "need website OR web designer OR web design OR shopify store"',
            'site:instagram.com/reel/ "need a website"',
            'site:instagram.com/p/ "need a website"',
            'site:instagram.com/reel/ "web designer" "cost"',
            'site:instagram.com/p/ "redesign website"',
            'site:instagram.com/reel/ "website cost" "pricing"',
            'site:instagram.com/p/ "revamp website" "shopify"',
            'site:instagram.com "need website for my business"',
            'site:instagram.com/reel/ "eCommerce store" "pricing"',
            'site:instagram.com/p/ "portfolio website" "looking for"'
        ])

        discovered_posts: List[Dict[str, Any]] = []
        discovered_comments: List[Dict[str, Any]] = []
        seen_urls = set()
        headers = self._get_search_headers()

        with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
            for q in queries:
                if len(discovered_posts) >= max_posts:
                    break
                try:
                    search_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(q)}"
                    resp = client.get(search_url)
                    if resp.status_code != 200:
                        continue

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

                        # Parse relative date
                        days_ago, age_label = self._parse_post_age(snippet_text)
                        if days_ago is not None and days_ago > days_range:
                            continue

                        default_age = age_label if age_label != "Recent" else (f"{min(days_range, 2)}d ago" if days_range > 1 else "18h ago")

                        # Handle extraction
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
                    logger.warning(f"Error querying term '{q}': {e}")
                    continue

        # Combine with any Apify partial results
        all_posts = apify_posts + discovered_posts
        all_comments = apify_comments + discovered_comments
        return all_posts, all_comments

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
        High-Volume 2-Tier Lead Harvester:
        - Scrapes high-volume posts and all their comments via Apify or fallback
        - Loops through all harvested comments across all posts
        - AI intent evaluation on each comment (pricing, demo, redesign, or website help)
        - Exact terminal telemetry outputs:
            print(f"Scraping window: last {days_range} days")
            print(f"Total posts harvested: {len(posts)}")
            print(f"Total comments parsed: {len(comments)}")
            print(f"Qualified leads saved: {len(qualified_leads)}")
        """
        target_niche = (niche or keyword or hashtag or "").strip()
        print(f"Scraping window: last {days_range} days")
        logger.info(f"Scraping window: last {days_range} days (niche: '{target_niche or 'All'}', target: {count})")

        # 1. Harvest high-volume posts and their comments
        posts, comments = self._harvest_posts_and_comments(
            niche=target_niche,
            days_range=days_range,
            max_posts=30,
            max_comments_per_post=20
        )

        # REQUIRED PRINT OUTPUTS:
        print(f"Total posts harvested: {len(posts)}")
        print(f"Total comments parsed: {len(comments)}")
        logger.info(f"Total posts harvested: {len(posts)}")
        logger.info(f"Total comments parsed: {len(comments)}")

        if not comments:
            print("Qualified leads saved: 0")
            logger.info("Qualified leads saved: 0")
            return []

        qualified_leads: List[Lead] = []
        seen_handles = set()

        # 2. Loop through all harvested comments across all posts
        for c in comments:
            if len(qualified_leads) >= count:
                break

            handle = c["handle"]
            comment_text = c["comment"]
            post_url = c["post_url"]
            caption = c.get("caption", "")
            posted_ago = c.get("posted_ago", f"{min(days_range, 2)}d ago")

            if handle in seen_handles:
                continue
            seen_handles.add(handle)

            # Context topic from post caption
            post_topic = target_niche.title() if target_niche else "Commercial Business"
            if caption:
                t1_eval = gemini_service.evaluate_post_relevance(caption=caption)
                if t1_eval.get("is_relevant_post"):
                    post_topic = t1_eval.get("topic") or post_topic

            # 3. Run AI intent evaluation on each comment
            t2_eval = gemini_service.evaluate_comment_intent(
                username=handle,
                comment_text=comment_text,
                topic=post_topic
            )

            is_lead = t2_eval.get("is_website_lead", False)
            confidence = t2_eval.get("confidence", 0)

            # Accept if commenter asks about pricing, demo, redesign, or website help
            c_low = comment_text.lower()
            intent_keywords = [
                "pricing", "price", "cost", "how much", "rate", "rates",
                "demo", "preview", "prototype", "sample",
                "redesign", "revamp", "rebuild", "upgrade",
                "website", "web designer", "developer", "shopify", "store",
                "online store", "portfolio", "help", "dm me", "quote", "interested"
            ]
            has_explicit_intent = any(k in c_low for k in intent_keywords)

            # As long as the commenter asks about pricing, demo, redesign, or website help, add them directly
            if not is_lead and not has_explicit_intent and confidence < 50:
                logger.info(f"Filtered out comment: {handle}: \"{comment_text[:60]}\"")
                continue

            b_name = t2_eval.get("business_name") or c["business_name"]
            user_pain_point = t2_eval.get("user_pain_point") or "Inquired about website, redesign, or pricing"

            # Check if lead already exists in DB
            existing = db.query(Lead).filter(Lead.instagram_handle == handle).first()
            if existing:
                existing.lead_score = max(existing.lead_score, confidence if confidence > 0 else 85)
                existing.industry = post_topic
                existing.score_reasons = f"Posted: {posted_ago} • Topic: {post_topic} • Need: {user_pain_point} (Intent Verified)"
                existing.source_post_url = post_url
                existing.comment_text = comment_text
                qualified_leads.append(existing)
                continue

            # Generate GrowthGrid demo pitch
            personalized_dm = gemini_service.generate_instagram_dm(
                handle=handle,
                business_name=b_name,
                industry=post_topic,
                comment_text=comment_text,
                post_context=f"Post Topic: {post_topic} | URL: {post_url}"
            )

            score_val = max(confidence, 82) if (is_lead or has_explicit_intent) else 75
            score_reasons = f"Posted: {posted_ago} • Topic: {post_topic} • Need: {user_pain_point} (Intent Verified)"
            notes = (
                f"Posted: {posted_ago}\n"
                f"Scraping Window: Last {days_range} Days\n"
                f"Post Topic: {post_topic}\n"
                f"Buyer Need: {user_pain_point}\n"
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
                source="Apify/Instagram Engine",
                status="DM Drafted",
                lead_score=score_val,
                score_reasons=score_reasons,
                source_post_url=post_url,
                comment_text=comment_text,
                outreach_instagram_dm=personalized_dm,
                notes=notes
            )

            db.add(new_lead)
            qualified_leads.append(new_lead)

        db.commit()

        for lead in qualified_leads:
            db.refresh(lead)

        # REQUIRED PRINT OUTPUT:
        print(f"Qualified leads saved: {len(qualified_leads)}")
        logger.info(f"Qualified leads saved: {len(qualified_leads)}")

        return qualified_leads


# Singleton instance
instagram_scanner = InstagramIntentScanner()
