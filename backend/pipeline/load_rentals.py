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

# ── 28 target suburbs ─────────────────────────
TARGET_SUBURBS = [
    # North
    'Chatswood', 'North Ryde', 'Macquarie Park', 'Epping', 'Eastwood',
    # West
    'Parramatta', 'Lidcombe', 'Auburn', 'Granville', 'Westmead',
    'Homebush', 'Merrylands',
    # Inner West
    'Burwood', 'Strathfield', 'Ashfield', 'Campsie', 'Rhodes', 'Wolli Creek',
    # South
    'Mascot', 'Zetland', 'Waterloo', 'Kensington', 'Kingsford', 'Hurstville',
    # East
    'Bondi Junction', 'Coogee', 'Randwick', 'Maroubra',
]

# ── Property type mapping ──────────────────────
KEEP_DWELLING = {'F', 'H', 'T'}

def map_type(row):
    if row["dwelling_type"] == "F":
        return "apartment"
    elif row["dwelling_type"] in ["H", "T"]:
        return "house"

# ── Read XLSX files ────────────────────────────
FILES = [
    r"D:\Rental\raw_data\rentalbond_lodgements_year_2024.xlsx",
    r"D:\Rental\raw_data\rentalbond_lodgements_year_2025.xlsx",
]

dfs = []
for f in FILES:
    print(f"Reading {os.path.basename(f)}...")
    df = pd.read_excel(f, sheet_name=0, skiprows=2, header=0)
    df.columns = ["lodgement_date", "postcode", "dwelling_type", "bedrooms", "weekly_rent"]
    df = df[df["lodgement_date"] != "Lodgement Date"]
    dfs.append(df)
    print(f"   {len(df):,} rows")

df = pd.concat(dfs, ignore_index=True)
print(f"\nCombined total: {len(df):,} rows")

# ── Clean data ─────────────────────────────────
print("\nCleaning data...")

before = len(df)
df = df[df["dwelling_type"].isin(KEEP_DWELLING)]
print(f"   Exclude O/U dwelling:     {before:,} -> {len(df):,} (removed {before-len(df):,})")

before = len(df)
df = df[df["weekly_rent"].notna()]
df = df[df["weekly_rent"] != "U"]
df["weekly_rent"] = pd.to_numeric(df["weekly_rent"], errors="coerce")
df = df[(df["weekly_rent"] > 0) & (df["weekly_rent"] <= 10000)]
df["weekly_rent"] = df["weekly_rent"].astype(int)
print(f"   Exclude invalid rent:     {before:,} -> {len(df):,} (removed {before-len(df):,})")

before = len(df)
df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
df = df[df["bedrooms"].notna() & (df["bedrooms"] <= 9)]
df["bedrooms"] = df["bedrooms"].astype(int)
print(f"   Exclude invalid bedrooms: {before:,} -> {len(df):,} (removed {before-len(df):,})")

df["property_type"] = df.apply(map_type, axis=1)
df["postcode"] = df["postcode"].astype(str).str.zfill(4)
df["lodgement_date"] = pd.to_datetime(df["lodgement_date"], errors="coerce").dt.date

print(f"\nFinal clean rows: {len(df):,}")
print("\nProperty type breakdown:")
for pt, cnt in df["property_type"].value_counts().items():
    print(f"   {pt:<12} {cnt:>7,}")

# ── Build postcode -> suburb_id mapping ────────
# Only use the 28 target suburbs to avoid postcode conflicts
# (e.g. postcode 2142 covers Granville, Camellia, Clyde etc.)
print("\nMatching postcodes to target suburbs only...")
placeholders = ','.join(['?' for _ in TARGET_SUBURBS])
cursor.execute(
    f"SELECT suburb_id, suburb_name, postcode FROM dbo.suburbs WHERE suburb_name IN ({placeholders})",
    TARGET_SUBURBS
)
rows = cursor.fetchall()

postcode_map = {}
for sid, suburb_name, pc in rows:
    pc = str(pc).strip().zfill(4)
    if pc not in postcode_map:
        postcode_map[pc] = sid
        print(f"   {suburb_name:<20} postcode {pc} -> suburb_id {sid}")

print(f"\n   Postcode mappings found: {len(postcode_map)}")

# ── Batch insert ───────────────────────────────
print("\nInserting records...")
inserted = 0
skipped  = 0
BATCH_SIZE = 1000
batch = []

for _, row in df.iterrows():
    sid = postcode_map.get(str(row["postcode"]))
    if sid is None:
        skipped += 1
        continue

    batch.append((
        sid,
        row["property_type"],
        int(row["bedrooms"]),
        int(row["weekly_rent"]),
        row["lodgement_date"],
        "rental_bond_nsw",
    ))

    if len(batch) >= BATCH_SIZE:
        cursor.executemany("""
            INSERT INTO dbo.rentals
                (suburb_id, property_type, bedrooms, price_weekly, listing_date, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()
        inserted += len(batch)
        batch = []
        print(f"   Inserted {inserted:,} rows...", end="\r")

if batch:
    cursor.executemany("""
        INSERT INTO dbo.rentals
            (suburb_id, property_type, bedrooms, price_weekly, listing_date, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, batch)
    conn.commit()
    inserted += len(batch)

print(f"\nDone! Inserted {inserted:,} rows, skipped {skipped:,} rows (postcode not in target suburbs)")
conn.close()