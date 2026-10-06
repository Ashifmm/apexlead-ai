import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from app.main import app

def test_api_scan_instagram():
    client = TestClient(app)
    response = client.post(
        "/api/v1/leads/scan-instagram",
        json={
            "niche": "boutique",
            "quantity": 5,
            "days_range": 7,
            "exclude_existing": True
        }
    )
    print("Status code:", response.status_code)
    data = response.json()
    print("Message:", data.get("message"))
    print("Count:", data.get("count"))
    print("Quantity:", data.get("quantity"))
    assert response.status_code == 200
    assert len(data.get("leads", [])) == 5
    for l in data.get("leads", []):
        print(f"  Lead: @{l['instagram_handle']} - {l['business_name']} ({l['lead_score']}%)")
        print(f"  DM: {l['outreach_instagram_dm'][:50]}...")
    print("\nAPI TEST PASSED: Returned exactly 5 leads!")

if __name__ == "__main__":
    test_api_scan_instagram()
