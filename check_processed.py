import pandas as pd

# Read the four tables we made
names = ["postcodes", "postcode_suburb", "rent_stats", "postcode_crime"]

for name in names:
    df = pd.read_csv("processed_data/" + name + ".csv")
    print("=====", name, "=====")
    print("Rows:", len(df))
    print("Columns:", df.columns.tolist())
    print("Empty cells in each column:")
    print(df.isna().sum())
    print(df.head(3))
    print()