import pandas as pd

# Step 1: Read both rental files and put them together
df_2024 = pd.read_excel("raw_data/rentalbond_lodgements_year_2024.xlsx", header=2)
df_2025 = pd.read_excel("raw_data/rentalbond_lodgements_year_2025.xlsx", header=2)
df = pd.concat([df_2024, df_2025], ignore_index=True)
print("Rows at the start:", len(df))
print()
print("Cleaning rules (each number is how many rows this rule removed):")

# Step 2: Turn the text columns into numbers
# Anything that is not a number (like "U") becomes empty (NaN)
df["rent"] = pd.to_numeric(df["Weekly Rent"], errors="coerce")
df["bedrooms_num"] = pd.to_numeric(df["Bedrooms"], errors="coerce")
df["Postcode"] = pd.to_numeric(df["Postcode"], errors="coerce")

# Step 3: Apply the rules one by one, and count what each rule removes
before = len(df)
df = df[df["Dwelling Type"].isin(["F", "H", "T"])]
print("1. Dwelling Type is not F, H or T:", before - len(df))

before = len(df)
df = df[df["rent"].notna()]
print("2. Weekly rent is unknown:", before - len(df))

before = len(df)
df = df[df["rent"] > 0]
print("3. Weekly rent is 0 or less:", before - len(df))

before = len(df)
df = df[df["bedrooms_num"].notna()]
print("4. Bedrooms is unknown:", before - len(df))

before = len(df)
df = df[df["bedrooms_num"] <= 10]
print("5. More than 10 bedrooms:", before - len(df))

before = len(df)
df = df[(df["bedrooms_num"] > 0) | (df["Dwelling Type"] == "F")]
print("6. House or townhouse with 0 bedrooms:", before - len(df))

df = df.copy()
df["bed"] = df["bedrooms_num"].astype(int)
df["Postcode"] = df["Postcode"].astype(int)
print()
print("Rows kept:", len(df))

# Step 4: Calculate the numbers for each postcode, type and bedroom count
stats = df.groupby(["Postcode", "Dwelling Type", "bed"])["rent"].agg(
    n="count",
    median="median",
    p25=lambda x: x.quantile(0.25),
    p75=lambda x: x.quantile(0.75),
).reset_index()

# Step 5: Give each group a tier based on how many rows it has
def get_tier(n):
    if n >= 30:
        return "full"
    elif n >= 10:
        return "limited"
    else:
        return "insufficient"

stats["tier"] = stats["n"].apply(get_tier)

# Step 6: Check the results
print()
print("Number of groups:", len(stats))
print("Rows counted in the groups:", stats["n"].sum())
print()
print("Groups in each tier:")
print(stats["tier"].value_counts())
print()
print("Postcodes with at least one group in the full tier:",
      stats[stats["tier"] == "full"]["Postcode"].nunique(), "out of 609")

# Step 7: Sanity check, the median should be between p25 and p75
bad = stats[(stats["median"] < stats["p25"]) | (stats["median"] > stats["p75"])]
print("Groups where the median is outside p25 and p75:", len(bad))

# Step 8: Look at some examples (2 bedroom flats)
print()
print("Examples, 2 bedroom flats:")
example = stats[(stats["Dwelling Type"] == "F") & (stats["bed"] == 2) & (stats["Postcode"].isin([2000, 2148, 2170]))]
print(example)

# Step 9: For information only, rents that look extreme (not removed)
print()
print("Rows with rent below 50:", (df["rent"] < 50).sum())
print("Rows with rent above 5000:", (df["rent"] > 5000).sum())

# Step 10: Add the smallest and largest rent to the table
# (we can decide later whether to show these on the website)
extremes = df.groupby(["Postcode", "Dwelling Type", "bed"])["rent"].agg(
    rent_min="min",
    rent_max="max",
).reset_index()
stats = stats.merge(extremes, on=["Postcode", "Dwelling Type", "bed"])

# Step 11: Save the final table to a new folder called processed_data
import os
os.makedirs("processed_data", exist_ok=True)
stats.to_csv("processed_data/rent_stats.csv", index=False)
print()
print("Saved", len(stats), "rows to processed_data/rent_stats.csv")

# Step 12: How many postcodes are left, and how good is their data?
postcodes_all = set(df["Postcode"])
postcodes_full = set(stats[stats["tier"] == "full"]["Postcode"])
postcodes_limited = set(stats[stats["tier"] == "limited"]["Postcode"])
only_limited = postcodes_limited - postcodes_full
nothing = postcodes_all - postcodes_full - postcodes_limited
print()
print("Postcodes left after cleaning:", len(postcodes_all))
print("With at least one full group:", len(postcodes_full))
print("With limited groups only:", len(only_limited))
print("With insufficient groups only:", len(nothing))