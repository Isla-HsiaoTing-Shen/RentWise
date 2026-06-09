import pandas as pd
import pyodbc
from dotenv import load_dotenv
import os

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

# ── Read nsw_postcodes.csv (NSW only, already filtered) ────────────
# 欄位: suburb_name, postcode, state, latitude, longitude, lga_name, lga_code, sa3_name, sa4_name
print("Reading nsw_postcodes.csv...")
df = pd.read_csv(r"D:\Rental\nsw_postcodes.csv", dtype=str)

df['suburb_name_lower'] = df['suburb_name'].str.lower().str.strip()
df['latitude']  = pd.to_numeric(df['latitude'],  errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df = df.dropna(subset=['latitude', 'longitude'])
print(f"   NSW records with coordinates: {len(df):,}")

# Build lookup: suburb_name_lower → (latitude, longitude, lga_name)
lookup = (
    df
    .groupby('suburb_name_lower')
    .first()
    [['latitude', 'longitude', 'lga_name']]
    .to_dict('index')
)
print(f"   Unique suburb names: {len(lookup):,}")

# ── Load suburbs from database ─────────────────────────────────────
print("Loading suburbs from database...")
cursor.execute("SELECT suburb_id, suburb_name FROM dbo.suburbs")
rows = cursor.fetchall()
print(f"   Total suburbs in DB: {len(rows):,}")

# ── Update each suburb ─────────────────────────────────────────────
print("Updating latitude, longitude and lga_name...")
updated   = 0
not_found = 0

for suburb_id, suburb_name in rows:
    key   = suburb_name.lower().strip()
    match = lookup.get(key)

    if match:
        cursor.execute("""
            UPDATE dbo.suburbs
            SET latitude  = ?,
                longitude = ?,
                lga_name  = ?
            WHERE suburb_id = ?
        """,
            float(match['latitude']),
            float(match['longitude']),
            match['lga_name'],
            suburb_id
        )
        updated += 1
    else:
        not_found += 1

conn.commit()
print(f"Done! Updated {updated:,} suburbs, {not_found:,} not matched")
conn.close()

