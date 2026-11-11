"""
load_bonds.py
Extract + Load step of the ELT pipeline.
Reads the NSW rental bond Excel files in data/ and appends the rows,
unchanged, to the raw_bond_lodgements table. Cleaning happens later in SQL.

Safe to run again: a file that is already in the database is SKIPPED,
so adding a new month never loads the old months twice.

To load a file again (e.g. NSW Fair Trading corrected it), delete it first in SQL:
    DELETE FROM raw_bond_lodgements WHERE source_file = 'the_file_name.xlsx';

First time only: execute sql/01_create_raw_tables.sql to create an empty table.
Run from the project folder:  python python/load_bonds.py
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

COLUMNS = ["Lodgement Date", "Postcode", "Dwelling Type", "Bedrooms", "Weekly Rent"]


def connect():
    """Connect to Azure SQL (credentials are read from the .env file)."""
    load_dotenv()
    url = URL.create(
        "mssql+pyodbc",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_SERVER"),
        database=os.getenv("DB_NAME"),
        query={"driver": "ODBC Driver 18 for SQL Server", "Encrypt": "yes"},
    )
    return create_engine(url, fast_executemany=True)


def load_new_files(engine, folder="data"):
    """Load only the Excel files that are not in raw_bond_lodgements yet."""

    # 1. Which files are already in the database?
    done = set(pd.read_sql(
        "SELECT DISTINCT source_file FROM raw_bond_lodgements", engine
    )["source_file"])

    files = sorted(Path(folder).glob("*.xlsx"))
    new_files = [f for f in files if f.name not in done]
    print(f"{len(files)} files in {folder}/, {len(done)} already loaded, {len(new_files)} new\n")

    # 2. Load each new file
    for file in new_files:
        df = pd.read_excel(file, sheet_name=0, skiprows=2, dtype=str)

        # Stop if the columns are not what we expect
        if list(df.columns[:5]) != COLUMNS:
            raise ValueError(f"{file.name}: unexpected columns {list(df.columns)}")

        # Rename to match the SQL table and record which file each row came from
        df = df[COLUMNS]
        df.columns = ["lodgement_date", "postcode", "dwelling_type", "bedrooms", "weekly_rent"]
        df["source_file"] = file.name

        # which month(s) the file covers, so you can see it is the file you meant
        months = sorted(df["lodgement_date"].str[:7].dropna().unique())

        df.to_sql("raw_bond_lodgements", engine, if_exists="append",
                  index=False, chunksize=10_000)
        print(f"{file.name}: {len(df):,} rows loaded  (months: {', '.join(months)})")

    if not new_files:
        print("Nothing new to load.")


def show_months(engine):
    """Rows per month in the database: every month should appear once, with a similar count."""
    check = pd.read_sql(
        "SELECT LEFT(lodgement_date, 7) AS month, COUNT(*) AS rows_loaded, "
        "COUNT(DISTINCT source_file) AS files "
        "FROM raw_bond_lodgements GROUP BY LEFT(lodgement_date, 7) ORDER BY month",
        engine,
    )
    print("\nRows per month in the database:")
    print(check.to_string(index=False))

    # warning: a month that came from more than one file = loaded twice
    twice = check[check["files"] > 1]
    if len(twice):
        print("\n⚠️  These months come from more than one file (loaded twice?):")
        print(twice.to_string(index=False))


if __name__ == "__main__":
    engine = connect()
    load_new_files(engine)
    show_months(engine)

    