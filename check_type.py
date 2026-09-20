import pandas as pd

# Step 1: Read both rental files and put them together
# ignore_index=True gives the new table fresh row numbers (0, 1, 2, 3...)
df_2024 = pd.read_excel("raw_data/rentalbond_lodgements_year_2024.xlsx", header=2)
df_2025 = pd.read_excel("raw_data/rentalbond_lodgements_year_2025.xlsx", header=2)
df = pd.concat([df_2024, df_2025], ignore_index=True)

# Step 2: Keep only flats, houses and terraces
df = df[df["Dwelling Type"].isin(["F", "H", "T"])].copy()

# Step 3: Turn Bedrooms into numbers (U becomes empty)
df["bedrooms_num"] = pd.to_numeric(df["Bedrooms"], errors="coerce")
df = df[df["bedrooms_num"].notna()].copy()

# Step 4: Put 5 or more bedrooms into one group called 5
df["bedroom_group"] = df["bedrooms_num"].clip(upper=5)

# Step 5: Count rows for every combination of type and bedrooms
print("Number of rows for each combination:")
print(pd.crosstab(df["Dwelling Type"], df["bedroom_group"]))