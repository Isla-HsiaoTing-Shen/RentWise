import pandas as pd
import pyodbc
from dotenv import load_dotenv
import os

load_dotenv(r"D:\Rental\.env")

# ── 連線 Azure SQL ──────────────────────────────
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=tcp:{os.getenv('AZURE_SERVER')},1433;"
    f"DATABASE={os.getenv('AZURE_DATABASE')};"
    f"UID={os.getenv('AZURE_USERNAME')};"
    f"PWD={os.getenv('AZURE_PASSWORD')};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

print("✅ 連線成功！")
cursor = conn.cursor()

# ── 讀取 CSV ────────────────────────────────────
CSV_PATH = r"D:\Rental\SuburbData25Q4.csv"

CRIME_TYPES = [
    'Assault',
    'Robbery',
    'Malicious damage to property'
]

print("📂 讀取 CSV...")
df = pd.read_csv(CSV_PATH)
print(f"   總行數: {len(df):,}")

# ── 篩選需要的 crime type ───────────────────────
df = df[df['Offence category'].isin(CRIME_TYPES)].copy()
print(f"   篩選後: {len(df):,} 行")

# ── 寬表轉長表 ──────────────────────────────────
# 找出所有月份欄（2020 年之後就夠）
month_cols = [c for c in df.columns if any(
    str(y) in c for y in range(2020, 2026)
)]

df_long = df.melt(
    id_vars=['Suburb', 'Offence category', 'Subcategory'],
    value_vars=month_cols,
    var_name='month',
    value_name='incident_count'
)

# 轉成年份
df_long['year'] = df_long['month'].str.extract(r'(\d{4})').astype(int)

# 聚合成年度資料
df_year = (
    df_long
    .groupby(['Suburb', 'Offence category', 'year'], as_index=False)
    ['incident_count'].sum()
)
df_year.columns = ['suburb_name', 'crime_type', 'year', 'incident_count']
df_year = df_year[df_year['incident_count'] > 0]
print(f"   聚合後: {len(df_year):,} 行")

# ── 取得 suburb_id mapping ─────────────────────
print("🔍 比對 suburbs 表...")
cursor.execute("SELECT suburb_id, suburb_name FROM dbo.suburbs")
suburb_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
print(f"   suburbs 表有 {len(suburb_map)} 個區域")

# ── 插入 crime_stats ────────────────────────────
print("💾 插入資料中...")
inserted = 0
skipped = 0

for _, row in df_year.iterrows():
    sid = suburb_map.get(row['suburb_name'].lower())
    if sid is None:
        skipped += 1
        continue
    cursor.execute("""
        INSERT INTO dbo.crime_stats
            (suburb_id, year, crime_type, incident_count)
        VALUES (?, ?, ?, ?)
    """, sid, int(row['year']), row['crime_type'], int(row['incident_count']))
    inserted += 1

conn.commit()
print(f"✅ 完成！插入 {inserted:,} 筆，跳過 {skipped:,} 筆（suburb 不在表中）")
conn.close()
