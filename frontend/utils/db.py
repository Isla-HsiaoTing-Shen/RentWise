import pyodbc
from dotenv import load_dotenv
import os

load_dotenv(r"D:\Rental\.env")

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER=tcp:{os.getenv('AZURE_SERVER')},1433;"
        f"DATABASE={os.getenv('AZURE_DATABASE')};"
        f"UID={os.getenv('AZURE_USERNAME')};"
        f"PWD={os.getenv('AZURE_PASSWORD')};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )