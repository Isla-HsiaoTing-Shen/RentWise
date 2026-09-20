import pandas as pd

# Step 1: Read the rent stats we saved earlier
stats = pd.read_csv("processed_data/rent_stats.csv")
postcodes_with_stats = set(stats["Postcode"])

# Step 2: Read the raw rental files again to get all postcodes
df_2024 = pd.read_excel("raw_data/rentalbond_lodgements_year_2024.xlsx", header=2)
df_2025 = pd.read_excel("raw_data/rentalbond_lodgements_year_2025.xlsx", header=2)
df = pd.concat([df_2024, df_2025], ignore_index=True)
df["Postcode"] = pd.to_numeric(df["Postcode"], errors="coerce").astype(int)
all_postcodes = set(df["Postcode"])
print("Postcodes in the rental files:", len(all_postcodes))

# Step 3: Find the postcode that lost all its rows during cleaning
lost = sorted(all_postcodes - postcodes_with_stats)
print("Postcodes with no rent stats:", lost)
for p in lost:
    print()
    print("Rows for postcode", p)
    print(df[df["Postcode"] == p])

# Step 4: Make the postcodes table (one row per postcode)
postcodes = pd.DataFrame({"postcode": sorted(all_postcodes)})
postcodes.to_csv("processed_data/postcodes.csv", index=False)
print()
print("Saved", len(postcodes), "rows to processed_data/postcodes.csv")

# Step 5: Make the postcode_suburb table (one row per suburb name)
lookup = pd.read_csv("raw_data/nsw_postcodes.csv")
postcode_suburb = lookup[["POSTCODE", "SUBURB_NAME", "LGA_NAME"]].copy()
postcode_suburb.columns = ["postcode", "suburb_name", "lga_name"]
postcode_suburb = postcode_suburb[postcode_suburb["postcode"].isin(all_postcodes)]
postcode_suburb.to_csv("processed_data/postcode_suburb.csv", index=False)
print("Saved", len(postcode_suburb), "rows to processed_data/postcode_suburb.csv")

# Step 6: Check that the tables connect
print()
print("Postcodes with at least one suburb name:", postcode_suburb["postcode"].nunique())
print("Postcodes with rent stats:", stats["Postcode"].nunique())