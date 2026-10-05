"""
Standalone database seeding script.
Run this script to initialize the SQLite database and populate realistic sample leads:
    python seed_data.py
"""
import sys
import os

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.crud.crud_lead import crud_lead


def run_seed():
    print("=" * 60)
    print("AI Web Agency Lead Generator - Database Seeder")
    print("=" * 60)
    
    print("1. Initializing database schema...")
    init_db()
    
    print("2. Seeding initial test leads...")
    db = SessionLocal()
    try:
        count = crud_lead.seed_sample_data(db)
        if count > 0:
            print(f"Successfully seeded {count} high-opportunity test leads!")
        else:
            print("Database already contains leads. No new leads were inserted.")
    finally:
        db.close()
        
    print("Done! You can now start the FastAPI server and view leads in the dashboard.")


if __name__ == "__main__":
    run_seed()
