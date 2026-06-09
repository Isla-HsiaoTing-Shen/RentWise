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
print("✅ Connected successfully!")
cursor = conn.cursor()

# ── Read schools CSV ───────────────────────────
print("📂 Reading nsw_schools.csv...")
df = pd.read_csv(r"D:\Rental\nsw_schools.csv", dtype=str)
print(f"   Total schools: {len(df):,}")

# Keep only needed columns
df = df[['School_name', 'Town_suburb', 'Postcode', 'Level_of_schooling',
         'Selective_school', 'ICSEA_value']].copy()

# Clean postcode
df['Postcode'] = df['Postcode'].str.strip().str.zfill(4)

# Clean ICSEA score (school quality rating)
df['ICSEA_value'] = pd.to_numeric(df['ICSEA_value'], errors='coerce')

# Map school type
def map_school_type(level):
    if pd.isna(level):
        return 'other'
    level = str(level).lower()
    if 'primary' in level:
        return 'public'
    elif 'secondary' in level:
        return 'public'
    elif 'central' in level:
        return 'public'
    else:
        return 'public'

df['school_type'] = df['Level_of_schooling'].apply(map_school_type)

# Normalise ICSEA to 0-10 rating
# ICSEA range is roughly 500-1200, median ~1000
icsea_min = df['ICSEA_value'].min()
icsea_max = df['ICSEA_value'].max()
df['rating'] = ((df['ICSEA_value'] - icsea_min) / (icsea_max - icsea_min) * 10).round(1)

print(f"   ICSEA range: {icsea_min:.0f} - {icsea_max:.0f}")

# ── Build postcode → suburb_id mapping ────────
print("🔍 Matching against suburbs table...")
cursor.execute("SELECT suburb_id, postcode FROM dbo.suburbs")
rows = cursor.fetchall()

postcode_map = {}
for sid, pc in rows:
    pc = str(pc).strip().zfill(4)
    if pc not in postcode_map:
        postcode_map[pc] = sid

print(f"   Postcode mappings: {len(postcode_map)}")

# ── Insert schools ─────────────────────────────
print("💾 Inserting schools...")
inserted = 0
skipped = 0

for _, row in df.iterrows():
    sid = postcode_map.get(str(row['Postcode']))
    if sid is None:
        skipped += 1
        continue

    rating = float(row['rating']) if pd.notna(row['rating']) else None

    cursor.execute("""
        INSERT INTO dbo.schools
            (suburb_id, school_name, school_type, rating)
        VALUES (?, ?, ?, ?)
    """, sid, str(row['School_name']), row['school_type'], rating)
    inserted += 1

conn.commit()
print(f"✅ Done! Inserted {inserted:,} schools, skipped {skipped:,} (postcode not matched)")
conn.close()



