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

# ── Read nsw_postcodes.csv (NSW only, already filtered) ────────────
#  suburb_name, postcode, state, latitude, longitude, lga_name, lga_code, sa3_name, sa4_name
print("📂 Reading australian_postcodes.csv (Delivery Area only)...")
df = pd.read_csv(r"D:\Rental\raw_data\australian_postcodes.csv", dtype=str)
df.columns = [c.strip().lower() for c in df.columns]
df_nsw = df[
    (df['state'].str.upper() == 'NSW') &
    (df['type'] == 'Delivery Area')
][['locality', 'postcode']].copy()
df_nsw.columns = ['suburb_name', 'postcode']
df_nsw['postcode'] = df_nsw['postcode'].str.strip().str.zfill(4)
df_nsw['suburb_name_lower'] = df_nsw['suburb_name'].str.lower().str.strip()
lookup = df_nsw.groupby('suburb_name_lower')['postcode'].first().to_dict()
print(f"   NSW Delivery Area records: {len(df_nsw):,}")
print(f"   Unique suburb names: {len(lookup):,}")

# ── Load suburbs from database ─────────────────
print("🔍 Loading suburbs table...")
cursor.execute("SELECT suburb_id, suburb_name FROM dbo.suburbs")
rows = cursor.fetchall()
print(f"   Suburbs in DB: {len(rows):,}")

# ── Match and update ───────────────────────────
print("🔄 Updating postcodes...")
updated = 0
not_found = 0

for sid, name in rows:
    key = name.lower().strip()
    pc = lookup.get(key)
    if pc:
        cursor.execute(
            "UPDATE dbo.suburbs SET postcode = ? WHERE suburb_id = ?",
            pc, sid
        )
        updated += 1
    else:
        not_found += 1

conn.commit()
print(f"✅ Done! Updated {updated:,} suburbs, {not_found:,} not matched")
conn.close()

