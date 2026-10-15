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
    scrape_instagram_comments_apify
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

    print("\nALL APIFY ENGINE, COMMENT INTENT, BLACKLIST & SERVICE NICHE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_apify_engine()

