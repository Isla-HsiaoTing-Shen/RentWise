import os
import time
import pandas as pd
import pyodbc
from dotenv import load_dotenv

# Step 1: Read the login details from the .env file
load_dotenv()
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=" + os.getenv("AZURE_SERVER") + ";"
    "DATABASE=" + os.getenv("AZURE_DATABASE") + ";"
    "UID=" + os.getenv("AZURE_USERNAME") + ";"
    "PWD=" + os.getenv("AZURE_PASSWORD") + ";"
    "Encrypt=yes;TrustServerCertificate=no;"
)

# Step 2: Connect, and try again if the database is still waking up
connection = None
for attempt in range(1, 6):
    print("Attempt", attempt, "of 5...")
    try:
        connection = pyodbc.connect(connection_string, timeout=90)
        print("Connected!")
        break
    except pyodbc.Error as error:
        print("Not connected yet. Error code:", error.args[0])
        time.sleep(20)

if connection is None:
    print("Could not connect after 5 attempts.")
    raise SystemExit

cursor = connection.cursor()

# Step 3: Read the four CSV files
postcodes = pd.read_csv("processed_data/postcodes.csv")
postcode_suburb = pd.read_csv("processed_data/postcode_suburb.csv")
postcode_crime = pd.read_csv("processed_data/postcode_crime.csv")
rent_stats = pd.read_csv("processed_data/rent_stats.csv")

# Step 4: Give the rent_stats columns clean names (lowercase, no spaces)
rent_stats = rent_stats.rename(columns={
    "Postcode": "postcode",
    "Dwelling Type": "dwelling_type",
    "bed": "bedrooms",
    "median": "median_rent",
    "p25": "p25_rent",
    "p75": "p75_rent",
})
rent_stats = rent_stats[["postcode", "dwelling_type", "bedrooms", "n",
                         "median_rent", "p25_rent", "p75_rent",
                         "rent_min", "rent_max", "tier"]]

# Step 5: Delete the 4 NEW tables if they already exist (children first)
# The 8 old tables are not touched
for table in ["postcode_crime", "rent_stats", "postcode_suburb", "postcodes"]:
    cursor.execute("DROP TABLE IF EXISTS " + table)

# Step 6: Create the 4 new tables
cursor.execute("""
CREATE TABLE postcodes (
    postcode INT NOT NULL PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE postcode_suburb (
    postcode INT NOT NULL,
    suburb_name NVARCHAR(100) NOT NULL,
    lga_name NVARCHAR(100) NOT NULL,
    PRIMARY KEY (postcode, suburb_name),
    FOREIGN KEY (postcode) REFERENCES postcodes(postcode)
)
""")

cursor.execute("""
CREATE TABLE rent_stats (
    postcode INT NOT NULL,
    dwelling_type CHAR(1) NOT NULL CHECK (dwelling_type IN ('F', 'H', 'T')),
    bedrooms INT NOT NULL CHECK (bedrooms BETWEEN 0 AND 10),
    n INT NOT NULL,
    median_rent DECIMAL(10,2) NOT NULL,
    p25_rent DECIMAL(10,2) NOT NULL,
    p75_rent DECIMAL(10,2) NOT NULL,
    rent_min DECIMAL(10,2) NOT NULL,
    rent_max DECIMAL(10,2) NOT NULL,
    tier VARCHAR(12) NOT NULL CHECK (tier IN ('full', 'limited', 'insufficient')),
    PRIMARY KEY (postcode, dwelling_type, bedrooms),
    FOREIGN KEY (postcode) REFERENCES postcodes(postcode)
)
""")

cursor.execute("""
CREATE TABLE postcode_crime (
    postcode INT NOT NULL PRIMARY KEY,
    crime_3yr INT NOT NULL,
    FOREIGN KEY (postcode) REFERENCES postcodes(postcode)
)
""")
print("Created 4 new tables")

# Step 7: Load the data (postcodes first, because the other tables point to it)
cursor.fast_executemany = True

cursor.executemany(
    "INSERT INTO postcodes (postcode) VALUES (?)",
    postcodes.astype(object).values.tolist())

cursor.executemany(
    "INSERT INTO postcode_suburb (postcode, suburb_name, lga_name) VALUES (?, ?, ?)",
    postcode_suburb.astype(object).values.tolist())

cursor.executemany(
    "INSERT INTO rent_stats (postcode, dwelling_type, bedrooms, n, median_rent, p25_rent, p75_rent, rent_min, rent_max, tier) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    rent_stats.astype(object).values.tolist())

cursor.executemany(
    "INSERT INTO postcode_crime (postcode, crime_3yr) VALUES (?, ?)",
    postcode_crime.astype(object).values.tolist())

connection.commit()
print("Data loaded and saved")

# Step 8: Check that the number of rows in Azure matches the CSV files
print()
checks = [
    ("postcodes", len(postcodes)),
    ("postcode_suburb", len(postcode_suburb)),
    ("rent_stats", len(rent_stats)),
    ("postcode_crime", len(postcode_crime)),
]
for name, expected in checks:
    cursor.execute("SELECT COUNT(*) FROM " + name)
    actual = cursor.fetchone()[0]
    if actual == expected:
        print(name, ":", actual, "rows, OK")
    else:
        print(name, ": expected", expected, "but found", actual, "<-- MISMATCH")

# Step 9: Test the whole chain: suburb name -> postcode -> rent
print()
print("Test: 2 bedroom flats in HAYMARKET")
cursor.execute("""
SELECT s.suburb_name, s.postcode, r.n, r.median_rent, r.p25_rent, r.p75_rent, r.tier
FROM postcode_suburb s
JOIN rent_stats r ON s.postcode = r.postcode
WHERE s.suburb_name = ? AND r.dwelling_type = ? AND r.bedrooms = ?
""", "HAYMARKET", "F", 2)
for row in cursor.fetchall():
    print(list(row))

connection.close()