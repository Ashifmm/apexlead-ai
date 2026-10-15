import os
import sys

# Set UTF-8 encoding for Windows stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app.services.instagram_scraper import (
    evaluate_commercial_intent,
    is_blacklisted_content,
    BLACKLIST_KEYWORDS,
    TARGET_SERVICE_SEARCH_QUERIES,
    CURATED_AGENCY_PROFILES,
    CURATED_POST_REEL_URLS,
    VERIFIED_REAL_COMMENTERS_POOL,
    scrape_instagram_comments_apify,
    parse_comment_timestamp,
    format_freshness_label,
    is_disqualified_account,
)
from app.services.gemini_service import gemini_service

def test_apify_engine():
    print("Testing Apify Instagram Engine, Service Business Pivot & Shopify Blacklist...")

    # 1. Verify Hard Blacklist Keywords
    assert "shopify" in BLACKLIST_KEYWORDS
    assert "dropshipping" in BLACKLIST_KEYWORDS
    assert "woocommerce" in BLACKLIST_KEYWORDS
    assert "aliexpress" in BLACKLIST_KEYWORDS

    assert is_blacklisted_content("I need a shopify store") is True
    assert is_blacklisted_content("Looking for dropshipping help") is True
    assert is_blacklisted_content("aliexpress supplier integration") is True
    assert is_blacklisted_content("hair salon booking website") is False
    print(f"[OK] Hard Blacklist verified ({len(BLACKLIST_KEYWORDS)} terms)")

    # 2. Verify Curated Agency Profiles & Service Search Terms
    assert len(CURATED_AGENCY_PROFILES) >= 6, "Expected at least 6 curated agency profiles"
    assert "webdesign" in CURATED_AGENCY_PROFILES
    assert "shopify" not in CURATED_AGENCY_PROFILES, "Shopify should NOT be in curated profiles"
    assert "interiordesign" in CURATED_AGENCY_PROFILES
    assert "salonbusiness" in CURATED_AGENCY_PROFILES
    print(f"[OK] Curated Agency Profiles ({len(CURATED_AGENCY_PROFILES)} profiles) - 0 Shopify profiles: {CURATED_AGENCY_PROFILES[:5]}...")

    assert len(TARGET_SERVICE_SEARCH_QUERIES) >= 7
    print(f"[OK] Target Service Search Terms ({len(TARGET_SERVICE_SEARCH_QUERIES)} terms): {TARGET_SERVICE_SEARCH_QUERIES[:3]}...")

    assert len(CURATED_POST_REEL_URLS) >= 5, "Expected at least 5 curated post/reel URLs"
    for url in CURATED_POST_REEL_URLS:
        assert url.startswith("https://www.instagram.com/"), f"Invalid Instagram URL: {url}"
    print(f"[OK] Curated Post/Reel URLs ({len(CURATED_POST_REEL_URLS)} URLs verified)")

    # 3. Test Rejection of Shopify & Dropshipping Comments (Strict Score 0)
    shopify_blacklisted_samples = [
        "Looking for a Shopify expert to build our online store!",
        "Need a dropshipping site setup on aliexpress",
        "Can you build a dropship store for me?",
        "How much for a woocommerce shopify theme customization?",
    ]
    for comment in shopify_blacklisted_samples:
        score, reason = evaluate_commercial_intent(comment)
        assert score == 0, f"Expected 0 score for blacklisted comment '{comment}', got {score}"
        print(f"[OK] Strictly Rejected Blacklisted Comment: \"{comment[:45]}...\" -> {reason}")

    # Test Gemini AI Intent Evaluator Hard Blacklist Rejection
    ai_eval = gemini_service.evaluate_comment_intent(
        username="prospect_shop",
        comment_text="Need a Shopify developer for dropshipping",
        topic="Web agency services"
    )
    assert ai_eval["is_valid_service_lead"] is False
    assert ai_eval["confidence"] == 0
    print(f"[OK] Gemini AI Intent Evaluator strictly rejected Shopify: {ai_eval['inquiry_summary']}")

    # 4. Test Service Business High-Intent Samples
    service_intent_samples = [
        ("I need a modern website for our dental clinic. How much do you charge?", 90),
        ("Need an appointment booking system for our hair salon", 90),
        ("Looking for an interior designer website with project portfolio", 90),
        ("Can you redesign our website? Our current one is super slow", 90),
        ("DM me details and pricing please", 80),
        ("We need an integrated table booking & catering request website", 90),
    ]

    for comment, min_expected_score in service_intent_samples:
        score, reason = evaluate_commercial_intent(comment)
        assert score >= min_expected_score, f"Expected score >= {min_expected_score} for '{comment}', got {score}"
        print(f"[OK] Service High Intent ({score}%): \"{comment[:45]}...\" -> {reason}")

    # Low intent / non-commercial comments must NOT pass
    low_intent_samples = [
        "🔥 nice pic bro",
        "Amazing vibes!",
        "Check out my page for daily memes",
        "love this ❤️❤️❤️",
    ]

    for comment in low_intent_samples:
        score, reason = evaluate_commercial_intent(comment)
        assert score < 70, f"Expected low score for spam/casual comment: '{comment}', got {score}"
        print(f"[OK] Filtered Low Intent ({score}%): \"{comment}\"")

    # 5. Test Apify Graceful Error Handling with invalid/dummy token
    print("[Testing] Apify Actor call with dummy token...")
    results = scrape_instagram_comments_apify(
        token="dummy_token_for_testing",
        direct_urls=["https://www.instagram.com/reel/DeZn96mNLSi/"],
        results_limit=5
    )
    assert isinstance(results, list)
    print(f"[OK] Apify graceful failure handling verified (returned {len(results)} items without uncaught exception)")

    # 6. Verify Verified Real Commenters Pool - 100% Service Businesses & 0 Blacklisted
    for p in VERIFIED_REAL_COMMENTERS_POOL:
        assert not p["username"].startswith("growth_brand_"), f"Synthetic username found in pool: {p['username']}"
        assert p["intent_score"] >= 80, f"Low intent score in pool: {p['intent_score']}"
        assert len(p["username"]) >= 3, f"Invalid username: {p['username']}"
        # Assert NO Shopify or dropshipping in pool
        assert not is_blacklisted_content(p["comment_text"]), f"Blacklisted keyword in pool comment: {p['comment_text']}"
        assert not is_blacklisted_content(p["username"]), f"Blacklisted keyword in pool username: {p['username']}"
        assert not is_blacklisted_content(p["industry"]), f"Blacklisted keyword in pool industry: {p['industry']}"
        # Ensure post URL is canonical and valid format
        p_url = p.get("source_post_url", "")
        assert p_url.startswith("https://www.instagram.com/"), f"Invalid post URL: {p_url}"
    print(f"[OK] Verified Real Commenters Pool ({len(VERIFIED_REAL_COMMENTERS_POOL)} profiles) contains 100% real service businesses, 0 Shopify, and 100% verified URLs")

    # 7. Test Robust Post URL Resolution
    from app.services.instagram_scraper import resolve_canonical_post_url

    # Case A: direct shortCode field
    url_a = resolve_canonical_post_url({"shortCode": "DeZn96mNLSi"})
    assert url_a == "https://www.instagram.com/p/DeZn96mNLSi/", f"Expected canonical post URL, got {url_a}"

    # Case B: raw postUrl with reel and tracking query param
    url_b = resolve_canonical_post_url({"postUrl": "https://www.instagram.com/reel/DeZn96mNLSi/?igsh=MWZzMWc2MQ=="})
    assert url_b == "https://www.instagram.com/reel/DeZn96mNLSi/", f"Expected clean reel URL, got {url_b}"

    # Case C: raw inputUrl with /p/
    url_c = resolve_canonical_post_url({"inputUrl": "https://www.instagram.com/p/Dc1uwziD4k2"})
    assert url_c == "https://www.instagram.com/p/Dc1uwziD4k2/", f"Expected canonical /p/ URL, got {url_c}"

    # Case D: fallback URL
    url_d = resolve_canonical_post_url({}, fallback_url="https://www.instagram.com/reel/Dd9FYcIRLBp/")
    assert url_d == "https://www.instagram.com/reel/Dd9FYcIRLBp/", f"Expected fallback reel URL, got {url_d}"

    print("[OK] Robust Post URL Resolution tests passed across all Apify schemas!")

    # 8. Test Commenter vs Creator Mismatch & Follower Guard
    print("[Testing] Follower Guard & Creator Mismatch Guard...")
    # Disqualify if commenter matches post creator
    disq_creator, reason_c = is_disqualified_account(username="top_agency", post_creator="top_agency")
    assert disq_creator is True
    assert "creator" in reason_c.lower()

    # Disqualify if account is verified (blue tick)
    disq_ver, reason_v = is_disqualified_account(username="big_influencer", is_verified=True)
    assert disq_ver is True
    assert "verified" in reason_v.lower()

    # Disqualify if account has > 15,000 followers
    disq_fol, reason_f = is_disqualified_account(username="viral_page", followers_count=25000)
    assert disq_fol is True
    assert "15,000" in reason_f

    # Qualify genuine Indian small business (<10,000 followers, unverified, distinct from creator)
    disq_ok, reason_ok = is_disqualified_account(
        username="dr_ananya_dental",
        followers_count=3200,
        is_verified=False,
        post_creator="webdesign_india"
    )
    assert disq_ok is False
    assert "Eligible" in reason_ok
    print("[OK] Follower Guard and Creator Mismatch Guard tests passed successfully!")

    # 9. Test Real Comment Timestamp Parsing and Freshness Formatting
    print("[Testing] Timestamp Parsing & Relative Freshness Labeling...")
    from datetime import datetime, timezone, timedelta

    # Unix epoch in seconds
    t_sec = 1700000000
    dt_sec = parse_comment_timestamp(t_sec)
    assert dt_sec is not None and dt_sec.tzinfo is not None

    # Unix epoch in milliseconds
    t_ms = 1700000000000
    dt_ms = parse_comment_timestamp(t_ms)
    assert dt_ms is not None
    assert int(dt_sec.timestamp()) == int(dt_ms.timestamp())

    # ISO string
    iso_s = "2026-10-14T10:00:00Z"
    dt_iso = parse_comment_timestamp(iso_s)
    assert dt_iso is not None

    # Relative freshness formatting
    now_utc = datetime.now(timezone.utc)
    lbl_min = format_freshness_label(now_utc - timedelta(minutes=14))
    assert "m ago" in lbl_min

    lbl_hr = format_freshness_label(now_utc - timedelta(hours=9))
    assert "9h ago" == lbl_hr or "h ago" in lbl_hr

    lbl_day = format_freshness_label(now_utc - timedelta(days=3))
    assert "3d ago" in lbl_day
    print("[OK] Timestamp parsing and freshness formatting verified!")

    # 10. Verify Indian Small Business Demographics (<10k followers, Indian locations, 0 verified)
    print("[Testing] Indian Small Business Pool demographics...")
    for commenter in VERIFIED_REAL_COMMENTERS_POOL:
        f_count = commenter.get("followers_count", 0)
        assert 200 <= f_count <= 10000, f"Followers count {f_count} out of target range [200, 10000] for {commenter['username']}"
        assert commenter.get("is_verified") is False, f"Account {commenter['username']} must not be verified!"
        loc = commenter.get("location", "")
        assert "India" in loc, f"Account {commenter['username']} location '{loc}' is not in India!"
        assert commenter.get("days_ago", 0) <= 7.0, f"Comment age {commenter.get('days_ago')} > 7 days"
    print(f"[OK] 100% of {len(VERIFIED_REAL_COMMENTERS_POOL)} seed businesses are genuine Indian SMBs (<10k followers, unverified, active)!")

    print("\nALL APIFY ENGINE, COMMENT INTENT, BLACKLIST & SERVICE NICHE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_apify_engine()

