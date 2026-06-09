"""
RentWise — Database Quality Check
執行方式：python check_db_quality.py
會輸出所有資料品質問題，重點檢查 transport_access 車站距離錯誤
"""

import pyodbc
import pandas as pd
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

print("=" * 65)
print("  RentWise — Database Quality Check")
print("=" * 65)

issues_found = 0

# ─────────────────────────────────────────────────────────────────
# 1. TRANSPORT: 每個 suburb 對應到的是真正最近的車站嗎？
#    問題根源：transport_access 存的是「最近車站」，
#    但如果用 GTFS stops.txt 的方式算距離，有時候算到跨 LGA 的站。
# ─────────────────────────────────────────────────────────────────
print("\n📍 [1] Transport — 車站距離可疑的 suburb (>5 km)")
print("-" * 65)

transport_df = pd.read_sql("""
    SELECT s.suburb_name, t.station_name, t.station_dist_km,
           s.latitude, s.longitude
    FROM dbo.transport_access t
    JOIN dbo.suburbs s ON t.suburb_id = s.suburb_id
    ORDER BY t.station_dist_km DESC
""", conn)

far = transport_df[transport_df['station_dist_km'] > 5].copy()
if far.empty:
    print("  ✅ 全部 < 5 km，無明顯異常")
else:
    issues_found += len(far)
    print(f"  ⚠️  發現 {len(far)} 筆距離 > 5 km：")
    for _, r in far.iterrows():
        print(f"    {r['suburb_name']:<25} → {r['station_name']:<30} {r['station_dist_km']:.1f} km")

# 重點：Wolli Creek 和鄰近 suburb
print("\n📍 [1b] Transport — 南區重點 suburb 檢查（Wolli Creek / Arncliffe / Sydenham 等）")
print("-" * 65)
south = transport_df[transport_df['suburb_name'].isin([
    'Wolli Creek', 'Arncliffe', 'Sydenham', 'Tempe', 'St Peters',
    'Mascot', 'Marrickville', 'Kogarah', 'Hurstville', 'Rockdale',
    'Banksia', 'Bardwell Park', 'Turrella', 'Bardwell Valley'
])].copy()
for _, r in south.sort_values('suburb_name').iterrows():
    flag = "⚠️ " if r['station_dist_km'] > 3 else "  ✅"
    print(f"  {flag} {r['suburb_name']:<25} → {r['station_name']:<30} {r['station_dist_km']:.2f} km")

# ─────────────────────────────────────────────────────────────────
# 2. TRANSPORT: 同一個車站被重複分配給太多 suburb（可能是最近站算錯）
# ─────────────────────────────────────────────────────────────────
print("\n📍 [2] Transport — 同一車站被分配給太多 suburb (>8 個)")
print("-" * 65)

dup_stations = pd.read_sql("""
    SELECT t.station_name, COUNT(*) AS suburb_count,
           STRING_AGG(s.suburb_name, ', ') AS suburbs
    FROM dbo.transport_access t
    JOIN dbo.suburbs s ON t.suburb_id = s.suburb_id
    GROUP BY t.station_name
    HAVING COUNT(*) > 8
    ORDER BY COUNT(*) DESC
""", conn)

if dup_stations.empty:
    print("  ✅ 無異常集中情況")
else:
    issues_found += len(dup_stations)
    for _, r in dup_stations.iterrows():
        print(f"  ⚠️  {r['station_name']}: {r['suburb_count']} suburbs")
        print(f"       → {r['suburbs'][:120]}...")

# ─────────────────────────────────────────────────────────────────
# 3. TRANSPORT: 距離為 0 或 NULL
# ─────────────────────────────────────────────────────────────────
print("\n📍 [3] Transport — 距離為 0 或 NULL")
print("-" * 65)

zero_dist = pd.read_sql("""
    SELECT s.suburb_name, t.station_name, t.station_dist_km
    FROM dbo.transport_access t
    JOIN dbo.suburbs s ON t.suburb_id = s.suburb_id
    WHERE t.station_dist_km IS NULL OR t.station_dist_km = 0
""", conn)

if zero_dist.empty:
    print("  ✅ 無距離為 0 或 NULL")
else:
    issues_found += len(zero_dist)
    for _, r in zero_dist.iterrows():
        print(f"  ⚠️  {r['suburb_name']} → {r['station_name']} = {r['station_dist_km']}")

# ─────────────────────────────────────────────────────────────────
# 4. RENTALS: 租金異常值
# ─────────────────────────────────────────────────────────────────
print("\n💰 [4] Rentals — 每個 suburb 的中位數租金異常值")
print("-" * 65)

rent_df = pd.read_sql("""
    SELECT s.suburb_name,
           COUNT(*) AS listings,
           MIN(r.price_weekly) AS min_rent,
           MAX(r.price_weekly) AS max_rent,
           AVG(CAST(r.price_weekly AS FLOAT)) AS avg_rent,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.price_weekly)
               OVER (PARTITION BY r.suburb_id) AS median_rent
    FROM dbo.rentals r
    JOIN dbo.suburbs s ON r.suburb_id = s.suburb_id
    WHERE r.price_weekly BETWEEN 100 AND 5000
    GROUP BY s.suburb_name, r.suburb_id
""", conn).drop_duplicates(subset=['suburb_name'])

extreme = rent_df[(rent_df['median_rent'] > 3000) | (rent_df['median_rent'] < 200)]
if extreme.empty:
    print("  ✅ 無中位數租金異常值")
else:
    issues_found += len(extreme)
    for _, r in extreme.iterrows():
        print(f"  ⚠️  {r['suburb_name']:<25} median=${r['median_rent']:.0f}  min=${r['min_rent']}  max=${r['max_rent']}  n={r['listings']}")

# ─────────────────────────────────────────────────────────────────
# 5. SUBURB_SCORES: 分數為 NULL 或超出範圍
# ─────────────────────────────────────────────────────────────────
print("\n🏆 [5] Suburb Scores — NULL 或超出 0–10 的分數")
print("-" * 65)

score_issues = pd.read_sql("""
    SELECT s.suburb_name, p.profile_name,
           ss.overall_score, ss.price_score, ss.safety_score,
           ss.transport_score, ss.school_score, ss.amenity_score
    FROM dbo.suburb_scores ss
    JOIN dbo.suburbs s ON ss.suburb_id = s.suburb_id
    JOIN dbo.user_profiles p ON ss.profile_id = p.profile_id
    WHERE ss.overall_score IS NULL OR ss.overall_score < 0 OR ss.overall_score > 10
       OR ss.price_score IS NULL OR ss.safety_score IS NULL
       OR ss.transport_score IS NULL OR ss.school_score IS NULL
       OR ss.amenity_score IS NULL
""", conn)

if score_issues.empty:
    print("  ✅ 所有分數正常")
else:
    issues_found += len(score_issues)
    for _, r in score_issues.iterrows():
        print(f"  ⚠️  {r['suburb_name']} ({r['profile_name']}): overall={r['overall_score']}")

# ─────────────────────────────────────────────────────────────────
# 6. SUBURBS: 缺少經緯度 (地圖上會消失)
# ─────────────────────────────────────────────────────────────────
print("\n🗺️  [6] Suburbs — 缺少經緯度 (地圖上不會顯示)")
print("-" * 65)

no_coords = pd.read_sql("""
    SELECT s.suburb_name
    FROM dbo.suburbs s
    JOIN dbo.suburb_scores ss ON s.suburb_id = ss.suburb_id
    WHERE s.latitude IS NULL OR s.longitude IS NULL
    GROUP BY s.suburb_name
""", conn)

if no_coords.empty:
    print("  ✅ 所有有分數的 suburb 都有座標")
else:
    issues_found += len(no_coords)
    print(f"  ⚠️  {len(no_coords)} 個 suburb 缺少座標：")
    print("  " + ", ".join(no_coords['suburb_name'].tolist()))

# ─────────────────────────────────────────────────────────────────
# 7. CRIME: 異常高的犯罪值
# ─────────────────────────────────────────────────────────────────
print("\n🚨 [7] Crime — 犯罪數異常高的 suburb (top 10)")
print("-" * 65)

crime_df = pd.read_sql("""
    SELECT s.suburb_name, SUM(c.incident_count) AS total_incidents
    FROM dbo.crime_stats c
    JOIN dbo.suburbs s ON c.suburb_id = s.suburb_id
    GROUP BY s.suburb_name
    ORDER BY total_incidents DESC
""", conn)

print("  Top 10 高犯罪區域（確認是否合理）：")
for _, r in crime_df.head(10).iterrows():
    print(f"    {r['suburb_name']:<25} {r['total_incidents']:>6} incidents")

# ─────────────────────────────────────────────────────────────────
# 總結
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"  總結：發現 {issues_found} 個需要注意的資料問題")
print("=" * 65)

conn.close()
