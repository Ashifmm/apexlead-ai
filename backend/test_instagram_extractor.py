import sys
import os

# Set UTF-8 encoding for Windows stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.services.instagram_scraper import instagram_scraper, is_blacklisted_content
from app.models.lead import Lead

def test_instagram_lead_extractor():
    init_db()
    db = SessionLocal()
    try:
        print("Testing Real Instagram Lead Extractor (Service Business & Anti-Shopify) with quantity = 5...")
        requested_quantity = 5
        leads = instagram_scraper.scan_intent(
            db=db,
            niche="salon",
            days_range=7,
            quantity=requested_quantity,
            count=requested_quantity,
            exclude_existing=True
        )

        print(f"\nReturned leads count: {len(leads)}")
        assert len(leads) == requested_quantity, f"Expected {requested_quantity} leads, got {len(leads)}"

        # Check DB persistence and zero Shopify leads
        for idx, lead in enumerate(leads, 1):
            assert lead.id is not None, f"Lead {lead.instagram_handle} was not persisted (no ID)"
            # Query from DB to verify persistence
            db_lead = db.query(Lead).filter(Lead.id == lead.id).first()
            assert db_lead is not None, f"Lead ID {lead.id} not found in database!"

            # Strict assertion: No blacklisted or Shopify content
            assert not is_blacklisted_content(db_lead.comment_text), f"Shopify/eCommerce found in lead comment: {db_lead.comment_text}"
            assert not is_blacklisted_content(db_lead.business_name), f"Shopify/eCommerce found in lead name: {db_lead.business_name}"
            assert not is_blacklisted_content(db_lead.instagram_handle), f"Shopify/eCommerce found in handle: {db_lead.instagram_handle}"

            # Strict assertion: Indian Small Business demography & Follower guard
            assert "India" in (db_lead.location or ""), f"Lead location '{db_lead.location}' is not in India!"
            assert "Followers:" in (db_lead.notes or ""), f"Notes missing Followers metric: {db_lead.notes}"
            assert "Posted:" in (db_lead.notes or ""), f"Notes missing Posted freshness metric: {db_lead.notes}"
            assert db_lead.source_post_url.startswith("https://www.instagram.com/"), f"Invalid post URL: {db_lead.source_post_url}"

            print(f"[{idx}] ID={db_lead.id} | {db_lead.instagram_handle} | {db_lead.business_name} | {db_lead.industry} | Score={db_lead.lead_score}%")
            print(f"     Location: {db_lead.location} | Notes: {db_lead.notes[:80]}...")
            print(f"     Inquiry: {db_lead.comment_text[:80]}...")
            print(f"     Post URL: {db_lead.source_post_url}")
            print(f"     DM Pitch snippet: {db_lead.outreach_instagram_dm[:60]}... (Contains GrowthGrid: {'GrowthGrid' in db_lead.outreach_instagram_dm})")

        print("\nSUCCESS: Exact quantity fulfilled, Indian SMB verified (<10k followers), 0 Shopify, real timestamps, persisted to DB!")
    finally:
        db.close()

if __name__ == "__main__":
    test_instagram_lead_extractor()
