"""
load_postcodes.py
Extract + Load step for the postcode lookup (Matthew Proctor, Australian Postcodes).

"""

import os

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
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "Encrypt": "yes",
        "Connection Timeout": "120",
    },
)
engine = create_engine(url, fast_executemany=True)

# 2. Read the CSV (all columns as text, so postcodes like 0800 keep the leading 0)
COLUMNS = ["postcode", "locality", "state", "lat", "long", "type", "sa4name"]
df = pd.read_csv("data/australian_postcodes.csv", usecols=COLUMNS, dtype=str)

# 3. Load into SQL. if_exists="replace" creates the table automatically.
df.to_sql("raw_postcodes", engine, if_exists="replace", index=False, chunksize=5_000)
print(f"raw_postcodes: {len(df):,} rows loaded")

# 4. Check the row count in the database
check = pd.read_sql("SELECT COUNT(*) AS rows_in_db FROM raw_postcodes", engine)
print(check.to_string(index=False))