"""
export_for_web.py
Exports data for the RentWise website.
Saves JSON files in the rentwise project (../rentwise/data/).
It only READS from the database, so Power BI is not affected.

The website always uses the LATEST 12 MONTHS of data. The script finds the newest
month in clean_bond_lodgements by itself, so after adding new months you just run it
again - no years or dates to change.

  benchmark.json        rent figures for the latest 12 months
  postcodes.json        postcodes that have data in the latest 12 months
  rent_spread.json      how many leases at each $50 of rent (for the "where most rents fall" chart)
  meta.json             the dates, so the website can say "Oct 2025 – Sep 2026"

The rent history (trend over the years) is in Power BI, not on the website.

Run from the project folder (nsw-rent-fairness) with the ▶ button in VS Code.
The same queries are in sql/07_export_for_web.sql, to run by hand.
"""

import json
import os
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

MIN_SAMPLE = 30          # BR-02: at least 30 leases
BIN_WIDTH  = 50          # rent_spread.json: one count per $50 ($550 = $550 to $599)
OUTPUT_FOLDER = Path("../rentwise/data")


def connect():
    """Connect to Azure SQL (same settings as load_bonds.py)."""
    load_dotenv()
    url = URL.create(
        "mssql+pyodbc",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_SERVER"),
        database=os.getenv("DB_NAME"),
        query={"driver": "ODBC Driver 18 for SQL Server", "Encrypt": "yes"},
    )
    return create_engine(url, connect_args={"timeout": 120})


def add_months(d, n):
    """date(2026, 9, 1) + -11 months -> date(2025, 10, 1)"""
    m = d.year * 12 + (d.month - 1) + n
    return date(m // 12, m % 12 + 1, 1)


# ===== 1. Work out the 12-month window from the data =====

def find_window(engine):
    row = pd.read_sql(
        "SELECT MAX(lodgement_date) AS last_date FROM clean_bond_lodgements", engine
    ).iloc[0]
    end = pd.Timestamp(row["last_date"]).date().replace(day=1)     # newest month, e.g. 2026-09-01

    w = {
        "end_month":   end,                       # 2026-09-01
        "start":       add_months(end, -11),      # 2025-10-01 (12 months incl. end month)
        "stop":        add_months(end, 1),        # 2026-10-01 (first day AFTER the window)
    }
    return w


def check_window(engine, w):
    """Stop if a month is missing in the window - the medians would be wrong."""
    months = pd.read_sql(text(
        "SELECT DISTINCT YEAR(lodgement_date) * 100 + MONTH(lodgement_date) AS ym "
        "FROM clean_bond_lodgements "
        "WHERE lodgement_date >= :start AND lodgement_date < :stop"
    ), engine, params={"start": w["start"], "stop": w["stop"]})
    if len(months) != 12:
        raise ValueError(f"The latest 12 months should have 12 months of data, found {len(months)}: "
                         f"{sorted(months['ym'])}. Check that every monthly file is loaded.")


# ===== 2. The queries (same as sql/07_export_for_web.sql) =====

BENCHMARK_SQL = """
    WITH latest AS (
        SELECT postcode, dwelling_type, bedroom_group, weekly_rent
        FROM clean_bond_lodgements
        WHERE lodgement_date >= :start AND lodgement_date < :stop
    ),
    stats AS (
        SELECT DISTINCT
            postcode, dwelling_type, bedroom_group,
            COUNT(*) OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS sample_size,
            PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY weekly_rent)
                OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p05_rent,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY weekly_rent)
                OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p25_rent,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
                OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS median_rent,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY weekly_rent)
                OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p75_rent,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY weekly_rent)
                OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p95_rent
        FROM latest
    )
    SELECT postcode, dwelling_type, bedroom_group, sample_size,
           p25_rent, median_rent, p75_rent, p05_rent, p95_rent,
           CASE WHEN sample_size >= 30 THEN 'Yes' ELSE 'No' END AS meets_min_sample
    FROM stats
    ORDER BY postcode, dwelling_type, bedroom_group
"""

POSTCODES_SQL = """
    SELECT postcode, postcode_label, region, latitude, longitude
    FROM dim_postcode
    WHERE postcode IN (
        SELECT DISTINCT postcode FROM clean_bond_lodgements
        WHERE lodgement_date >= :start AND lodgement_date < :stop
    )
    ORDER BY postcode
"""

# number of leases in each $50 of rent, e.g. bin_start 550 = $550 to $599.99
SPREAD_SQL = """
    SELECT postcode, dwelling_type, bedroom_group,
           CAST(FLOOR(weekly_rent / 50) * 50 AS INT) AS bin_start,
           COUNT(*) AS leases
    FROM clean_bond_lodgements
    WHERE lodgement_date >= :start AND lodgement_date < :stop
    GROUP BY postcode, dwelling_type, bedroom_group, CAST(FLOOR(weekly_rent / 50) * 50 AS INT)
    ORDER BY postcode, dwelling_type, bedroom_group, bin_start
"""


# ===== 3. Run and save =====

def save(df, name):
    path = OUTPUT_FOLDER / f"{name}.json"
    df.to_json(path, orient="records", force_ascii=False)
    print(f"{name}.json: {len(df):,} rows")


def main():
    engine = connect()
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    w = find_window(engine)
    check_window(engine, w)
    print(f"Latest 12 months: {w['start']:%b %Y} – {w['end_month']:%b %Y}\n")

    params = {"start": w["start"], "stop": w["stop"]}

    benchmark = pd.read_sql(text(BENCHMARK_SQL), engine, params=params)
    save(benchmark, "benchmark")

    postcodes = pd.read_sql(text(POSTCODES_SQL), engine, params=params)
    for col in ["latitude", "longitude"]:      # DECIMAL from SQL -> normal numbers for JSON
        postcodes[col] = postcodes[col].astype(float)
    save(postcodes, "postcodes")

    spread = pd.read_sql(text(SPREAD_SQL), engine, params=params)
    # only benchmarks with 30+ leases (BR-02), one row each: bins = [[550, 12], [600, 9], ...]
    reliable = benchmark.loc[benchmark["meets_min_sample"] == "Yes",
                             ["postcode", "dwelling_type", "bedroom_group"]]
    spread = spread.merge(reliable, on=["postcode", "dwelling_type", "bedroom_group"])
    spread["bins"] = [[int(b), int(n)] for b, n in zip(spread["bin_start"], spread["leases"])]
    spread = (spread.groupby(["postcode", "dwelling_type", "bedroom_group"], as_index=False)
                    .agg(bins=("bins", list)))
    save(spread, "rent_spread")

    # dates for the website
    meta = {
        "period_start": f"{w['start']:%Y-%m}",
        "period_end":   f"{w['end_month']:%Y-%m}",
        "min_sample":   MIN_SAMPLE,
        "bin_width":    BIN_WIDTH,
        "updated":      f"{date.today():%Y-%m-%d}",
    }
    (OUTPUT_FOLDER / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"meta.json: {meta['period_start']} to {meta['period_end']}")

    print(f"\nDone. Files saved in {OUTPUT_FOLDER.resolve()}")


if __name__ == "__main__":
    main()

    