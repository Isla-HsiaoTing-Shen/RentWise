import pandas as pd
import pyodbc
from dotenv import load_dotenv
import os
import math

load_dotenv(r"D:\Rental\.env")

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=tcp:{os.getenv('AZURE_SERVER')},1433;"
    f"DATABASE={os.getenv('AZURE_DATABASE')};"
    f"UID={os.getenv('AZURE_USERNAME')};"
    f"PWD={os.getenv('AZURE_PASSWORD')};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
print("✅ Connected successfully!")
cursor = conn.cursor()

# ── Haversine formula: calculate distance between two lat/lon points ──
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ── Read stops.txt and filter train/metro stations only ──
print("📂 Reading stops.txt...")
stops = pd.read_csv(r"D:\Rental\stops.txt", dtype=str)
stations = stops[
    (stops['location_type'] == '1') &
    (stops['stop_name'].str.contains('Station', case=False, na=False))
].copy()
stations['stop_lat'] = pd.to_numeric(stations['stop_lat'], errors='coerce')
stations['stop_lon'] = pd.to_numeric(stations['stop_lon'], errors='coerce')
stations = stations.dropna(subset=['stop_lat', 'stop_lon'])
print(f"   Train/Metro stations found: {len(stations):,}")

# Town Hall station coordinates (CBD reference point)
TOWN_HALL_LAT = -33.8734
TOWN_HALL_LON = 151.2070

# ── Load suburbs with coordinates ──
print("🔍 Loading suburbs...")
cursor.execute("SELECT suburb_id, suburb_name, latitude, longitude FROM dbo.suburbs WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
suburbs = cursor.fetchall()
print(f"   Suburbs with coordinates: {len(suburbs):,}")

if len(suburbs) == 0:
    print("⚠️  No suburbs have coordinates yet.")
    print("   Loading all suburbs and using postcode centroid approach instead...")
    cursor.execute("SELECT suburb_id, suburb_name, postcode FROM dbo.suburbs")
    suburbs_raw = cursor.fetchall()

    # Load coordinates from australian_postcodes.csv
    pc_df = pd.read_csv(r"D:\Rental\australian_postcodes.csv", dtype=str)
    pc_df.columns = [c.strip().lower() for c in pc_df.columns]
    pc_df = pc_df[pc_df['state'].str.upper() == 'NSW'][['postcode', 'lat', 'long']].copy()
    pc_df['postcode'] = pc_df['postcode'].str.zfill(4)
    pc_df['lat'] = pd.to_numeric(pc_df['lat'], errors='coerce')
    pc_df['long'] = pd.to_numeric(pc_df['long'], errors='coerce')
    pc_df = pc_df.dropna()
    pc_map = pc_df.groupby('postcode')[['lat', 'long']].mean().to_dict('index')

    suburbs = []
    for sid, name, pc in suburbs_raw:
        pc = str(pc).zfill(4)
        coords = pc_map.get(pc)
        if coords:
            suburbs.append((sid, name, coords['lat'], coords['long']))

    print(f"   Suburbs matched via postcode coords: {len(suburbs):,}")

# ── Calculate nearest station for each suburb ──
print("🔄 Calculating nearest station for each suburb...")
station_records = stations[['stop_name', 'stop_lat', 'stop_lon']].values.tolist()

inserted = 0
skipped = 0

for suburb in suburbs:
    sid, name, lat, lon = suburb[0], suburb[1], float(suburb[2]), float(suburb[3])

    # Find nearest station
    min_dist = float('inf')
    nearest_name = None

    for sname, slat, slon in station_records:
        dist = haversine(lat, lon, slat, slon)
        if dist < min_dist:
            min_dist = dist
            nearest_name = sname

    # Estimate travel time to CBD (Town Hall)
    # Rough estimate: 2 min/km by train + 10 min walking/waiting buffer
    dist_to_cbd = haversine(lat, lon, TOWN_HALL_LAT, TOWN_HALL_LON)
    travel_time = int(dist_to_cbd * 2 + 10)

    try:
        cursor.execute("""
            INSERT INTO dbo.transport_access
                (suburb_id, station_name, station_dist_km, travel_time_cbd)
            VALUES (?, ?, ?, ?)
        """, sid, nearest_name, round(min_dist, 2), travel_time)
        inserted += 1
    except Exception:
        skipped += 1

    if inserted % 500 == 0 and inserted > 0:
        conn.commit()
        print(f"   Processed {inserted:,} suburbs...", end='\r')

conn.commit()
print(f"\n✅ Done! Inserted {inserted:,} rows, skipped {skipped:,} rows")
conn.close()