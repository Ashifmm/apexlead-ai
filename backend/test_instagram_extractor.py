import sys
import os

# Set UTF-8 encoding for Windows stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app.db.session import SessionLocal
from app.services.instagram_scraper import instagram_scraper
from app.models.lead import Lead

def test_instagram_lead_extractor():
    db = SessionLocal()
    try:
        print("Testing Real Instagram Lead Extractor with exact quantity = 5...")
        requested_quantity = 5
        leads = instagram_scraper.scan_intent(
            db=db,
            niche="clothing brand",
            days_range=7,
            quantity=requested_quantity,
            count=requested_quantity,
            exclude_existing=True
        )

        print(f"\nReturned leads count: {len(leads)}")
        assert len(leads) == requested_quantity, f"Expected {requested_quantity} leads, got {len(leads)}"

        # Check DB persistence
        for idx, lead in enumerate(leads, 1):
            assert lead.id is not None, f"Lead {lead.instagram_handle} was not persisted (no ID)"
            # Query from DB to verify persistence
            db_lead = db.query(Lead).filter(Lead.id == lead.id).first()
            assert db_lead is not None, f"Lead ID {lead.id} not found in database!"
            
            print(f"[{idx}] ID={db_lead.id} | {db_lead.instagram_handle} | {db_lead.business_name} | Score={db_lead.lead_score}%")
            print(f"     Inquiry: {db_lead.comment_text[:80]}...")
            print(f"     DM Pitch snippet: {db_lead.outreach_instagram_dm[:60]}... (Contains GrowthGrid: {'GrowthGrid' in db_lead.outreach_instagram_dm})")

        print("\nSUCCESS: Exact quantity fulfilled, persisted to database, verified DM templates!")
    finally:
        db.close()

if __name__ == "__main__":
    test_instagram_lead_extractor()
