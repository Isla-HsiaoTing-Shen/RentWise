import pandas as pd

# Step 1: Read both rental files and put them together
df_2024 = pd.read_excel("raw_data/rentalbond_lodgements_year_2024.xlsx", header=2)
df_2025 = pd.read_excel("raw_data/rentalbond_lodgements_year_2025.xlsx", header=2)
df = pd.concat([df_2024, df_2025], ignore_index=True)

# Step 2: Turn rent, bedrooms and postcode into numbers (bad values become empty)
df["rent"] = pd.to_numeric(df["Weekly Rent"], errors="coerce")
df["bedrooms_num"] = pd.to_numeric(df["Bedrooms"], errors="coerce")
df["Postcode"] = pd.to_numeric(df["Postcode"], errors="coerce")

# Step 3: Keep flats, houses and terraces with a known rent and bedrooms
df = df[df["Dwelling Type"].isin(["F", "H", "T"])]
df = df[df["rent"].notna() & df["bedrooms_num"].notna()]
df = df[df["rent"] > 0].copy()

# Step 4: Remove rows with more than 10 bedrooms, keep the real bedroom number
df = df[df["bedrooms_num"] <= 10].copy()
df["bed"] = df["bedrooms_num"].astype(int)
print("Rows kept after cleaning:", len(df))

# Step 5: Count rows for each postcode, type and bedroom number
cells = df.groupby(["Postcode", "Dwelling Type", "bed"]).size().reset_index(name="n")

# Step 6: For each type and bedroom number, how many postcodes have enough rows?
cells["at_least_10"] = cells["n"] >= 10
cells["at_least_30"] = cells["n"] >= 30
summary = cells.groupby(["Dwelling Type", "bed"])[["at_least_10", "at_least_30"]].sum()
summary["postcodes_with_data"] = cells.groupby(["Dwelling Type", "bed"]).size()
print()
print("Number of postcodes with enough rows (out of 609):")
print(summary)

# Step 7: Compare min, max and percentiles for 2 bedroom flats in three postcodes
example = df[(df["Dwelling Type"] == "F") & (df["bed"] == 2) & (df["Postcode"].isin([2000, 2148, 2170]))]
print()
print("Rent summary for 2 bedroom flats:")
print(example.groupby("Postcode")["rent"].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]))