import pandas as pd

# Read the crime file
crime = pd.read_csv("raw_data/SuburbData25Q4.csv")

# Look at the columns and first rows
print("Column names:")
print(crime.columns.tolist())
print()
print(crime.head())
print()
print("Total rows:", len(crime))

# Step 5: Look at the first three columns
print()
print("Unique suburbs in crime file:", crime["Suburb"].nunique())
print()
print("Offence categories:")
print(crime["Offence category"].value_counts())
print()
print("Number of subcategories:", crime["Subcategory"].nunique())

# Step 6: Read the postcode lookup file
# (it only has suburbs that match our 609 rental postcodes)
lookup = pd.read_csv("raw_data/nsw_postcodes.csv")

# Step 7: Make suburb names the same style (capital letters, no extra spaces)
crime["SUBURB_NAME"] = crime["Suburb"].str.upper().str.strip()

# Step 8: Make a list of unique crime suburbs and check if they exist in the lookup
crime_suburbs = pd.DataFrame({"SUBURB_NAME": crime["SUBURB_NAME"].unique()})
crime_suburbs["in_lookup"] = crime_suburbs["SUBURB_NAME"].isin(lookup["SUBURB_NAME"])
print()
print("Crime suburbs found in lookup:")
print(crime_suburbs["in_lookup"].value_counts())

# Step 9: Show some crime suburbs that were NOT found
not_found = crime_suburbs[crime_suburbs["in_lookup"] == False]
print()
print("Examples of crime suburbs NOT found:")
print(not_found.head(20))

# Step 10: For the suburbs that were found, check how many postcodes each one has
postcodes_per_suburb = lookup.groupby("SUBURB_NAME")["POSTCODE"].nunique()
found_names = crime_suburbs[crime_suburbs["in_lookup"] == True]["SUBURB_NAME"]
counts = postcodes_per_suburb[found_names]
print()
print("Found suburbs with exactly 1 postcode:", (counts == 1).sum())
print("Found suburbs with more than 1 postcode:", (counts > 1).sum())