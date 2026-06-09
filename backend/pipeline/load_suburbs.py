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

# Read suburb list from CSV (same file as crime data, but we only need the suburb column)
print("📂 Reading suburb list...")
df = pd.read_csv(r"D:\Rental\raw_data\SuburbData25Q4.csv", usecols=['Suburb'])
suburbs = df['Suburb'].dropna().unique()
print(f"   Found {len(suburbs):,} suburbs")

# insert into suburbs table (ignore duplicates)
print("💾 Inserting into suburbs table...")
inserted = 0
for name in suburbs:
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM dbo.suburbs WHERE suburb_name = ?)
        INSERT INTO dbo.suburbs (suburb_name, postcode, state)
        VALUES (?, '0000', 'NSW')
    """, name, name)
    inserted += 1

conn.commit()
print(f"✅ Done! Inserted {inserted:,} suburbs")
conn.close()