import pandas as pd

# Step 1: Read the 2024 file
# The real column names are on the 3rd row, so we skip the first 2 rows
df_2024 = pd.read_excel("raw_data/rentalbond_lodgements_year_2024.xlsx", header=2)

# Step 2: Read the 2025 file
df_2025 = pd.read_excel("raw_data/rentalbond_lodgements_year_2025.xlsx", header=2)

# Step 3: Put the two files together into one table
df = pd.concat([df_2024, df_2025])

# Step 4: Look at the data
print("Column names:")
print(df.columns.tolist())
print()
print("First 5 rows:")
print(df.head())
print()

# Step 5: Count how many rows we have
print("Total rows:", len(df))

# Step 6: Count how many different postcodes there are
print("Unique postcodes:", df["Postcode"].nunique())

# Step 7: Show the postcodes that are not numbers (possible bad data)
print("Missing postcodes:", df["Postcode"].isna().sum())

# Step 8: Turn Postcode into numbers so we can compare them
# If a value is not a number, it becomes empty (NaN)
df["Postcode"] = pd.to_numeric(df["Postcode"], errors="coerce")
print()
print("Postcodes that are not numbers:", df["Postcode"].isna().sum())

# Step 9: Find postcodes outside the normal NSW range (2000 to 2999)
outside = df[(df["Postcode"] < 2000) | (df["Postcode"] > 2999)]
print("Rows outside 2000-2999:", len(outside))
print(outside["Postcode"].unique())

# Step 10: Count how many rows each postcode has
counts = df["Postcode"].value_counts()
print("Postcodes with fewer than 10 rows:", (counts < 10).sum())
print(counts.tail(10))

# Step 11: See what values are in Dwelling Type and Bedrooms
print()
print(df["Dwelling Type"].value_counts())
print(df["Bedrooms"].value_counts())

# Step 12: Make a list of the unique postcodes from the rental files
postcode_list = sorted(df["Postcode"].dropna().astype(int).unique())
print()
print("Number of postcodes:", len(postcode_list))

# Step 13: Save this list to a new CSV file
postcode_table = pd.DataFrame({"Postcode": postcode_list})
postcode_table.to_csv("raw_data/rental_postcodes.csv", index=False)

# Step 14: Look at the postcode file that you already have
lookup = pd.read_csv("raw_data/nsw_postcodes.csv")
print()
print("Lookup file columns:")
print(lookup.columns.tolist())
print(lookup.head())
print("Lookup file rows:", len(lookup))
# Step 14: Check which states are in the lookup file
print()
print("States in lookup file:")
print(lookup["STATE"].value_counts())

# Step 15: Make a small table of the 609 rental postcodes
rental_postcodes = pd.DataFrame({"POSTCODE": postcode_list})

# Step 16: For each rental postcode, check if it exists in the lookup file
rental_postcodes["in_lookup"] = rental_postcodes["POSTCODE"].isin(lookup["POSTCODE"])
print()
print("Rental postcodes found in lookup file:")
print(rental_postcodes["in_lookup"].value_counts())

# Step 17: Show the rental postcodes that are NOT in the lookup file
not_found = rental_postcodes[rental_postcodes["in_lookup"] == False]
print()
print("Rental postcodes NOT found in lookup file:")
print(not_found)

# Step 18: Keep only the lookup rows that match a rental postcode
matched = lookup[lookup["POSTCODE"].isin(postcode_list)]
print()
print("Suburb rows that match rental postcodes:", len(matched))

# Step 19: Count how many suburbs each postcode has
suburbs_per_postcode = matched["POSTCODE"].value_counts()
print("Postcodes with more than 1 suburb:", (suburbs_per_postcode > 1).sum())
print("Postcodes with only 1 suburb:", (suburbs_per_postcode == 1).sum())
print()
print("Top 10 postcodes with the most suburbs:")
print(suburbs_per_postcode.head(10))

# Step 20: Count how many rental rows each missing postcode has
missing_list = [2301, 2407, 2617, 2789]
print()
for p in missing_list:
    print("Postcode", p, "has", (df["Postcode"] == p).sum(), "rental rows")

# Step 21: Check if the same suburb + postcode appears more than once
print()
print("Duplicate suburb + postcode rows:", lookup.duplicated(subset=["SUBURB_NAME", "POSTCODE"]).sum())

# Step 22: Check if one suburb name belongs to more than one postcode
postcodes_per_suburb = lookup.groupby("SUBURB_NAME")["POSTCODE"].nunique()
many = postcodes_per_suburb[postcodes_per_suburb > 1]
print()
print("Suburb names with more than 1 postcode:", len(many))
print(many.head(10))

