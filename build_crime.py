import pandas as pd

# Step 1: Make a list of the 36 month columns (Jan 2023 to Dec 2025)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_columns = []
for year in [2023, 2024, 2025]:
    for m in months:
        month_columns.append(m + " " + str(year))

# Step 2: Read only the columns we need
crime = pd.read_csv("raw_data/SuburbData25Q4.csv", usecols=["Suburb"] + month_columns)

# Step 3: Add up the 36 months for each row
crime["crime_3yr"] = crime[month_columns].sum(axis=1)

# Step 4: Add up all offence rows so each suburb has one number
crime["CRIME_NAME"] = crime["Suburb"].str.upper().str.strip()
crime_by_suburb = crime.groupby("CRIME_NAME")["crime_3yr"].sum().reset_index()

# Step 5: Read the lookup file and clean the LGA names
lookup = pd.read_csv("raw_data/nsw_postcodes.csv")
lookup["LGA_CLEAN"] = lookup["LGA_NAME"].str.upper().str.strip().str.replace(" (NSW)", "", regex=False)

# Step 6: Split names like "BACK CREEK (BLAND)" into a base name and an LGA name
crime_by_suburb["BASE_NAME"] = crime_by_suburb["CRIME_NAME"].str.replace(r"\s*\(.*\)", "", regex=True)
crime_by_suburb["BRACKET_LGA"] = crime_by_suburb["CRIME_NAME"].str.extract(r"\((.*)\)", expand=False)
crime_by_suburb["BRACKET_LGA"] = crime_by_suburb["BRACKET_LGA"].str.replace(" REGIONAL", "", regex=False)

# Step 7: Match suburbs WITHOUT a bracket using the suburb name only
no_bracket = crime_by_suburb[crime_by_suburb["BRACKET_LGA"].isna()]
part1 = no_bracket.merge(
    lookup[["SUBURB_NAME", "POSTCODE"]],
    left_on="CRIME_NAME", right_on="SUBURB_NAME", how="inner")

# Step 8: Match suburbs WITH a bracket using the suburb name AND the LGA name
with_bracket = crime_by_suburb[crime_by_suburb["BRACKET_LGA"].notna()]
part2 = with_bracket.merge(
    lookup[["SUBURB_NAME", "LGA_CLEAN", "POSTCODE"]],
    left_on=["BASE_NAME", "BRACKET_LGA"], right_on=["SUBURB_NAME", "LGA_CLEAN"], how="inner")

# Step 9: Put the two matched parts together
columns = ["CRIME_NAME", "POSTCODE", "crime_3yr"]
matched = pd.concat([part1[columns], part2[columns]])

# Step 10: Keep only suburbs that belong to exactly ONE postcode
postcodes_per_suburb = matched.groupby("CRIME_NAME")["POSTCODE"].nunique()
keep_names = postcodes_per_suburb[postcodes_per_suburb == 1].index
clean = matched[matched["CRIME_NAME"].isin(keep_names)]

print("Total crime suburbs:", len(crime_by_suburb))
print("Matched to at least 1 postcode:", matched["CRIME_NAME"].nunique())
print("Matched to more than 1 postcode (excluded):", (postcodes_per_suburb > 1).sum())
print("Kept (exactly 1 postcode):", len(keep_names))
print("Excluded in total:", len(crime_by_suburb) - len(keep_names))

# Step 11: Add up crime for each postcode (one postcode can have several suburbs)
crime_by_postcode = clean.groupby("POSTCODE")["crime_3yr"].sum().reset_index()
print()
print("Postcodes in lookup file:", lookup["POSTCODE"].nunique())
print("Postcodes with crime data:", len(crime_by_postcode))

# Step 12: Quick check, the 5 postcodes with the most crime
print()
print(crime_by_postcode.sort_values("crime_3yr", ascending=False).head(5))
# Step 13: Save the crime table
import os
os.makedirs("processed_data", exist_ok=True)
postcode_crime = crime_by_postcode.copy()
postcode_crime.columns = ["postcode", "crime_3yr"]
postcode_crime["postcode"] = postcode_crime["postcode"].astype(int)
postcode_crime["crime_3yr"] = postcode_crime["crime_3yr"].astype(int)
postcode_crime.to_csv("processed_data/postcode_crime.csv", index=False)
print()
print("Saved", len(postcode_crime), "rows to processed_data/postcode_crime.csv")

# Step 14: Check that every crime postcode is in the postcodes table
postcodes = pd.read_csv("processed_data/postcodes.csv")
not_in_list = set(postcode_crime["postcode"]) - set(postcodes["postcode"])
print("Crime postcodes that are not in postcodes.csv:", len(not_in_list))