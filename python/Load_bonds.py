"""
load_bonds.py
Extract + Load step of the ELT pipeline.
Reads the NSW rental bond Excel files in data/ and appends the rows,
unchanged, to the raw_bond_lodgements table. Cleaning happens later in SQL.

Before running: execute sql/01_create_raw_tables.sql to create an empty table.
Run from the project folder:  python python/load_bonds.py
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

# 1. Connect to Azure SQL (credentials are read from the .env file)
load_dotenv()
url = URL.create(
    "mssql+pyodbc",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_SERVER"),
    database=os.getenv("DB_NAME"),
    query={"driver": "ODBC Driver 18 for SQL Server", "Encrypt": "yes"},
)
engine = create_engine(url, fast_executemany=True)

COLUMNS = ["Lodgement Date", "Postcode", "Dwelling Type", "Bedrooms", "Weekly Rent"]

# 2. Load each Excel file
for file in sorted(Path("data").glob("*.xlsx")):
    df = pd.read_excel(file, sheet_name=0, skiprows=2, dtype=str)

    # Stop if the columns are not what we expect
    if list(df.columns[:5]) != COLUMNS:
        raise ValueError(f"{file.name}: unexpected columns {list(df.columns)}")

    # Rename to match the SQL table and record which file each row came from
    df = df[COLUMNS]
    df.columns = ["lodgement_date", "postcode", "dwelling_type", "bedrooms", "weekly_rent"]
    df["source_file"] = file.name

    df.to_sql("raw_bond_lodgements", engine, if_exists="append",
              index=False, chunksize=10_000)
    print(f"{file.name}: {len(df):,} rows loaded")

# 3. Check the row count per file in the database
check = pd.read_sql(
    "SELECT source_file, COUNT(*) AS rows_loaded FROM raw_bond_lodgements "
    "GROUP BY source_file ORDER BY source_file",
    engine,
)
print("\nRows in database:")
print(check.to_string(index=False))