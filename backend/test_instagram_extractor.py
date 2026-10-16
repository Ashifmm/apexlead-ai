import sys
import os

# Set UTF-8 encoding for Windows stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.services.instagram_scraper import (
    instagram_scraper,
    is_blacklisted_content,
    verify_live_instagram_url,
    contains_intent_keyword,
    evaluate_commercial_intent,
    resolve_canonical_post_url,
    format_growthgrid_pitch,
)
from app.models.lead import Lead

def test_instagram_lead_extractor():
    init_db()
    db = SessionLocal()
    try:
        print("Testing Real Instagram Lead Extractor (Zero-Synthetic & 1-to-1 Raw Extraction)...")

        # 1. Zero-Synthetic Policy: Must return 0 leads when token missing / empty (NEVER hallucinate leads)
        leads = instagram_scraper.scan_intent(
            db=db,
            niche="salon",
            days_range=7,
            quantity=5,
            count=5,
            exclude_existing=True,
            apify_token=None
        )
        print(f"Returned leads count without Apify token: {len(leads)}")
        assert len(leads) == 0, f"Expected 0 leads without Apify token, got {len(leads)}"
        db_count = db.query(Lead).count()
        assert db_count == 0, f"Expected 0 leads in database, found {db_count}"
        print("[OK] Zero-Synthetic Policy verified: Strictly returns 0 leads instead of fake/hallucinated leads!")

        # 2. Enforce 1-to-1 Single-Source Mapping with Live Test Post
        print("\nTesting 1-to-1 Raw Comment Extraction from live test post...")
        live_test_reel = "https://www.instagram.com/reel/DeZn96mNLSi/"
        raw_apify_comment_item = {
            "ownerUsername": "the_dentist_hub_delhi",
            "text": "Need a modern clinic website with online appointment booking calendar. Please DM pricing details!",
            "postUrl": live_test_reel,
            "timestamp": 1700000000,
            "owner": {
                "username": "the_dentist_hub_delhi",
                "isVerified": False,
                "followersCount": 2400
            }
        }

        # Validate 1-to-1 fields
        raw_text = raw_apify_comment_item["text"]
        user_handle = raw_apify_comment_item["ownerUsername"]
        parent_url = resolve_canonical_post_url(raw_apify_comment_item)

        assert raw_text == "Need a modern clinic website with online appointment booking calendar. Please DM pricing details!"
        assert user_handle == "the_dentist_hub_delhi"
        assert parent_url == live_test_reel

        # Verify exact commercial keyword matching
        assert contains_intent_keyword(raw_text) is True
        assert not is_blacklisted_content(raw_text)

        # Verify live URLs
        profile_url = f"https://www.instagram.com/{user_handle}/"
        assert verify_live_instagram_url(profile_url) is True, f"Profile URL failed live verification: {profile_url}"
        assert verify_live_instagram_url(parent_url) is True, f"Post URL failed live verification: {parent_url}"

        # Ingest and persist 1-to-1 genuine lead
        score, reason = evaluate_commercial_intent(raw_text)
        assert score >= 80

        pitch = format_growthgrid_pitch("The Dentist Hub Delhi")
        lead = Lead(
            business_name="The Dentist Hub Delhi",
            industry="Dental Clinic",
            location="Delhi, India",
            website_url=None,
            has_website=False,
            email=None,
            phone=None,
            instagram_handle=f"@{user_handle}",
            source="Instagram Intent",
            status="Intent Detected",
            lead_score=score,
            score_reasons=f"Intent Score: {score}% • {reason}",
            source_post_url=parent_url,
            comment_text=raw_text, # Pure raw string, untouched
            outreach_instagram_dm=pitch,
            notes=f"Discovered via Apify Real Comment Harvester | Inquiry: {raw_text[:140]}"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        assert lead.id is not None
        persisted = db.query(Lead).filter(Lead.id == lead.id).first()
        assert persisted is not None
        assert persisted.comment_text == raw_text
        assert persisted.instagram_handle == "@the_dentist_hub_delhi"
        assert persisted.source_post_url == live_test_reel

        print(f"[OK] 1-to-1 Single-Source Lead persisted: ID={persisted.id}")
        print(f"     Commenter Handle: {persisted.instagram_handle}")
        print(f"     Raw Comment Text: \"{persisted.comment_text}\"")
        print(f"     Source Reel URL:  {persisted.source_post_url}")
        print(f"     GrowthGrid Pitch: {persisted.outreach_instagram_dm[:60]}...")

        # Clean up database so it remains 100% wiped
        db.query(Lead).delete()
        db.commit()
        assert db.query(Lead).count() == 0
        print("[OK] Database cleaned: 0 leads remaining in DB")

        print("\nSUCCESS: All Zero-Synthetic, Raw Comment & 1-to-1 Mapping tests passed cleanly!")
    finally:
        db.close()

if __name__ == "__main__":
    test_instagram_lead_extractor()
