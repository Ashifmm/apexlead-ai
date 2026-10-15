import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "agency_leads.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find leads with blacklisted references
blacklist_terms = ["shopify", "dropship", "aliexpress", "woocommerce"]
conditions = []
for term in blacklist_terms:
    conditions.append(f"LOWER(comment_text) LIKE '%{term}%'")
    conditions.append(f"LOWER(business_name) LIKE '%{term}%'")
    conditions.append(f"LOWER(notes) LIKE '%{term}%'")
    conditions.append(f"LOWER(score_reasons) LIKE '%{term}%'")

where_clause = " OR ".join(conditions)

cursor.execute(f"""
    SELECT id, business_name, instagram_handle, comment_text 
    FROM leads 
    WHERE {where_clause}
""")
matching = cursor.fetchall()
print(f"Found {len(matching)} leads with blacklisted references to delete:")
for row in matching:
    print(f"  ID {row[0]}: {row[2]} ({row[1]}) -> {row[3][:60] if row[3] else ''}")

cursor.execute(f"""
    DELETE FROM leads 
    WHERE {where_clause}
""")
conn.commit()
print(f"Deleted {cursor.rowcount} blacklisted leads successfully.")

cursor.execute("SELECT COUNT(*) FROM leads")
total_remaining = cursor.fetchone()[0]
print(f"Total remaining leads in database: {total_remaining}")

conn.close()
