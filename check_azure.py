import os
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
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
)

# Step 2: Connect to the database
print("Connecting... (a paused database can take about a minute to wake up)")
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()
print("Connected!")

# Step 3: List all tables in the database
cursor.execute("SELECT name FROM sys.tables ORDER BY name")
table_names = [row[0] for row in cursor.fetchall()]

# Step 4: Count the rows in each table
print()
print("Tables in the database:")
for name in table_names:
    cursor.execute("SELECT COUNT(*) FROM [" + name + "]")
    count = cursor.fetchone()[0]
    print(name, "->", count, "rows")

connection.close()