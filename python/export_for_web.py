"""
export_for_web.py
Exports data for the RentWise website.
Runs the 4 queries from sql/07_export_for_web.sql and saves each one as a JSON file
in the rentwise project (../rentwise/data/).
It only READS from the database, so Power BI is not affected.

Run from the project folder (nsw-rent-fairness) with the ▶ button in VS Code.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

# 1. Connect to Azure SQL (same settings as load_bonds.py)
load_dotenv()
url = URL.create(
    "mssql+pyodbc",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_SERVER"),
    database=os.getenv("DB_NAME"),
    query={"driver": "ODBC Driver 18 for SQL Server", "Encrypt": "yes"},
)
engine = create_engine(url, connect_args={"timeout": 120})

# 2. The 4 queries (same as sql/07_export_for_web.sql)
QUERIES = {
    "postcodes": """
        SELECT postcode, postcode_label, region, latitude, longitude
        FROM dim_postcode
        WHERE postcode IN (SELECT DISTINCT postcode FROM vw_rent_benchmark)
        ORDER BY postcode
    """,

    "benchmark": """
        SELECT b.postcode, b.dwelling_type, b.bedroom_group, b.sample_size,
               b.p25_rent, b.median_rent, b.p75_rent,
               w.p05_rent, w.p95_rent, b.meets_min_sample
        FROM vw_rent_benchmark AS b
        LEFT JOIN (
            SELECT DISTINCT postcode, dwelling_type, bedroom_group,
                   PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY weekly_rent)
                       OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p05_rent,
                   PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY weekly_rent)
                       OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p95_rent
            FROM clean_bond_lodgements
            WHERE lodgement_year = 2025
        ) AS w
            ON  w.postcode = b.postcode
            AND w.dwelling_type = b.dwelling_type
            AND w.bedroom_group = b.bedroom_group
        ORDER BY b.postcode, b.dwelling_type, b.bedroom_group
    """,

    "trend": """
        SELECT postcode, dwelling_type, bedroom_group, lodgement_quarter,
               sample_size, median_rent
        FROM vw_rent_trend
        WHERE sample_size >= 30
        ORDER BY postcode, dwelling_type, bedroom_group, lodgement_quarter
    """,
    "trend_nsw": """
        SELECT dwelling_type, bedroom_group, lodgement_quarter,
               sample_size, median_rent
        FROM vw_rent_trend_nsw
        ORDER BY dwelling_type, bedroom_group, lodgement_quarter
    """,

    "trend_yearly": """
        SELECT postcode, dwelling_type, bedroom_group, lodgement_year,
               sample_size, median_rent
        FROM (
            SELECT DISTINCT postcode, dwelling_type, bedroom_group, lodgement_year,
                   COUNT(*) OVER (PARTITION BY postcode, dwelling_type, bedroom_group, lodgement_year) AS sample_size,
                   PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
                       OVER (PARTITION BY postcode, dwelling_type, bedroom_group, lodgement_year) AS median_rent
            FROM clean_bond_lodgements
        ) AS yearly
        WHERE sample_size >= 30
        ORDER BY postcode, dwelling_type, bedroom_group, lodgement_year
    """,
}

# 3. Where to save: D:\rentwise\data\ (created if it does not exist)
OUTPUT_FOLDER = Path("../rentwise/data")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# 4. Run each query and save it as JSON
for name, sql in QUERIES.items():
    df = pd.read_sql(sql, engine)

    # latitude/longitude come from SQL as DECIMAL; JSON needs normal numbers
    for col in ["latitude", "longitude"]:
        if col in df.columns:
            df[col] = df[col].astype(float)

    path = OUTPUT_FOLDER / f"{name}.json"
    df.to_json(path, orient="records", force_ascii=False)
    print(f"{name}.json: {len(df):,} rows")

print(f"\nDone. Files saved in {OUTPUT_FOLDER.resolve()}")