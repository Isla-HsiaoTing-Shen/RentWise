import requests
import pyodbc
from dotenv import load_dotenv
import os
import time

# ── Connect to Azure SQL ───────────────────────────────────────────
load_dotenv(r"D:\Rental\.env")

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=tcp:{os.getenv('AZURE_SERVER')},1433;"
    f"DATABASE={os.getenv('AZURE_DATABASE')};"
    f"UID={os.getenv('AZURE_USERNAME')};"
    f"PWD={os.getenv('AZURE_PASSWORD')};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
print("Connected successfully!")
cursor = conn.cursor()

# ── Target suburbs (28 specific suburbs) ──────────────────────────
TARGET_SUBURBS = [
    # north
    'Chatswood', 'North Ryde', 'Macquarie Park', 'Epping', 'Eastwood',
    # west
    'Parramatta', 'Lidcombe', 'Auburn', 'Granville', 'Westmead', 'Homebush', 'Merrylands',
    # inner west
    'Burwood', 'Strathfield', 'Ashfield', 'Campsie', 'Rhodes', 'Wolli Creek',
    # south
    'Mascot', 'Zetland', 'Waterloo', 'Kensington', 'Kingsford', 'Hurstville',
    # east
    'Bondi Junction', 'Coogee', 'Randwick', 'Maroubra',
]

# ── Load target suburbs with coordinates ──────────────────────────
print("Loading target suburbs...")
placeholders = ','.join(['?' for _ in TARGET_SUBURBS])
cursor.execute(f"""
    SELECT suburb_id, suburb_name, latitude, longitude
    FROM dbo.suburbs
    WHERE suburb_name IN ({placeholders})
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL
""", TARGET_SUBURBS)

suburbs = cursor.fetchall()
print(f"   Target suburbs found: {len(suburbs)}")

if len(suburbs) == 0:
    print("No suburbs found!")
    exit()

# Show which suburbs were found vs missing
found_names = {row[1] for row in suburbs}
missing = [s for s in TARGET_SUBURBS if s not in found_names]
if missing:
    print(f"   ⚠️  Not found in DB: {missing}")

# ── Amenity types to query ─────────────────────────────────────────
AMENITY_QUERIES = {
    'supermarket': '["shop"="supermarket"]',
    'gym':         '["leisure"="fitness_centre"]',
    'hospital':    '["amenity"="hospital"]',
    'park':        '["leisure"="park"]',
    'cafe':        '["amenity"="cafe"]',
    'university':  '["amenity"="university"]',
    'pharmacy':    '["amenity"="pharmacy"]',
}

RADIUS  = 1500
OSM_URL = "https://overpass-api.de/api/interpreter"

def query_osm(lat, lon, query_filter, radius=1500):
    query = f"""
        [out:json][timeout:15];
        node{query_filter}(around:{radius},{lat},{lon});
        out count;
    """
    try:
        resp = requests.post(OSM_URL, data=query, timeout=20)
        data = resp.json()
        return data['elements'][0]['tags'].get('total', 0)
    except Exception:
        return None

# ── Query OpenStreetMap for each suburb ────────────────────────────
print(f"Querying OpenStreetMap ({len(suburbs)} suburbs x {len(AMENITY_QUERIES)} types)...")
print("Note: existing records will be skipped automatically.\n")
inserted = 0
skipped  = 0

for i, (suburb_id, suburb_name, lat, lon) in enumerate(suburbs, 1):
    print(f"[{i}/{len(suburbs)}] {suburb_name}...")

    for amenity_type, query_filter in AMENITY_QUERIES.items():

        # Skip if already exists
        cursor.execute("""
            SELECT 1 FROM dbo.amenities
            WHERE suburb_id = ? AND amenity_type = ?
        """, suburb_id, amenity_type)
        if cursor.fetchone():
            skipped += 1
            continue

        count = query_osm(lat, lon, query_filter, RADIUS)

        if count is not None:
            cursor.execute("""
                INSERT INTO dbo.amenities
                    (suburb_id, amenity_type, count, radius_km)
                VALUES (?, ?, ?, ?)
            """, suburb_id, amenity_type, int(count), RADIUS / 1000)
            inserted += 1

        time.sleep(0.5)

    conn.commit()

print(f"\nDone! Inserted {inserted} rows, skipped {skipped} (already existed)")
conn.close()

