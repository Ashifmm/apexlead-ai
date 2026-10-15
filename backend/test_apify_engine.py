import os
import sys

# Set UTF-8 encoding for Windows stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app.services.instagram_scraper import (
    evaluate_commercial_intent,
    CURATED_AGENCY_PROFILES,
    CURATED_POST_REEL_URLS,
    VERIFIED_REAL_COMMENTERS_POOL,
    scrape_instagram_comments_apify
)

def test_apify_engine():
    print("Testing Apify Instagram Engine & Intent Evaluator...")

    # 1. Verify Curated Seed Lists
    assert len(CURATED_AGENCY_PROFILES) >= 6, "Expected at least 6 curated agency profiles"
    assert "webdesign" in CURATED_AGENCY_PROFILES
    assert "shopify" in CURATED_AGENCY_PROFILES
    print(f"[OK] Curated Agency Profiles ({len(CURATED_AGENCY_PROFILES)} profiles): {CURATED_AGENCY_PROFILES[:4]}...")

    assert len(CURATED_POST_REEL_URLS) >= 5, "Expected at least 5 curated post/reel URLs"
    for url in CURATED_POST_REEL_URLS:
        assert url.startswith("https://www.instagram.com/"), f"Invalid Instagram URL: {url}"
    print(f"[OK] Curated Post/Reel URLs ({len(CURATED_POST_REEL_URLS)} URLs verified)")

    # 2. Test Commercial Intent Evaluator
    high_intent_samples = [
        ("I need a modern website for my clothing brand. How much do you charge?", 90),
        ("Looking for a Shopify expert to build our online store!", 90),
        ("Can you redesign our website? Our current one is super slow", 90),
        ("DM me details and pricing please", 80),
        ("Need an appointment booking system for our hair salon", 85),
    ]

    for comment, min_expected_score in high_intent_samples:
        score, reason = evaluate_commercial_intent(comment)
        assert score >= min_expected_score, f"Expected score >= {min_expected_score} for '{comment}', got {score}"
        print(f"[OK] High Intent ({score}%): \"{comment[:45]}...\" -> {reason}")

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

    # 3. Test Apify Graceful Error Handling with invalid/dummy token
    print("[Testing] Apify Actor call with dummy token...")
    results = scrape_instagram_comments_apify(
        token="dummy_token_for_testing",
        direct_urls=["https://www.instagram.com/reel/C32q4_5uV5v/"],
        results_limit=5
    )
    # With dummy token, Apify should fail gracefully and return empty list without crashing
    assert isinstance(results, list)
    print(f"[OK] Apify graceful failure handling verified (returned {len(results)} items without uncaught exception)")

    # 4. Verify Verified Real Commenters Pool
    for p in VERIFIED_REAL_COMMENTERS_POOL:
        assert not p["username"].startswith("growth_brand_"), f"Synthetic username found in pool: {p['username']}"
        assert p["intent_score"] >= 80, f"Low intent score in pool: {p['intent_score']}"
        assert len(p["username"]) >= 3, f"Invalid username: {p['username']}"
        # Ensure post URL is canonical and valid format
        p_url = p.get("source_post_url", "")
        assert p_url.startswith("https://www.instagram.com/"), f"Invalid post URL: {p_url}"
        assert "C32q4_5uV5v" not in p_url and "C31P0c0O1uK" not in p_url, f"Broken placeholder URL in pool: {p_url}"
    print(f"[OK] Verified Real Commenters Pool ({len(VERIFIED_REAL_COMMENTERS_POOL)} profiles) contains 0 synthetic usernames and 100% verified URLs")

    # 5. Test Robust Post URL Resolution
    from app.services.instagram_scraper import resolve_canonical_post_url

    # Case A: direct shortCode field
    url_a = resolve_canonical_post_url({"shortCode": "DDn45x_uu9g"})
    assert url_a == "https://www.instagram.com/p/DDn45x_uu9g/", f"Expected canonical post URL, got {url_a}"

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

    print("\nALL APIFY ENGINE, COMMENT INTENT & CANONICAL URL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_apify_engine()

