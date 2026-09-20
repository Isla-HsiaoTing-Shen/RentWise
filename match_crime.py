import pandas as pd

# Step 1: Read only the Suburb column (we do not need the other 374 columns yet)
crime = pd.read_csv("raw_data/SuburbData25Q4.csv", usecols=["Suburb"])

# Step 2: Make a small table with one row per suburb
suburbs = pd.DataFrame({"Suburb": crime["Suburb"].unique()})
suburbs["CRIME_NAME"] = suburbs["Suburb"].str.upper().str.strip()

# Step 3: Split names like "BACK CREEK (BLAND)" into two parts
# BASE_NAME = the text before the bracket, BRACKET_LGA = the text inside the bracket
suburbs["BASE_NAME"] = suburbs["CRIME_NAME"].str.replace(r"\s*\(.*\)", "", regex=True)
suburbs["BRACKET_LGA"] = suburbs["CRIME_NAME"].str.extract(r"\((.*)\)")

# Step 4: Read the lookup file and make the LGA names capital letters too
lookup = pd.read_csv("raw_data/nsw_postcodes.csv")
lookup["LGA_UPPER"] = lookup["LGA_NAME"].str.upper().str.strip()

print("LGA names in the lookup file (first 15):")
print(lookup["LGA_UPPER"].unique()[:15])

# Step 5: Look only at suburbs that have a bracket
with_bracket = suburbs[suburbs["BRACKET_LGA"].notna()]
print()
print("Suburbs with a bracket:", len(with_bracket))

# Step 6: Try to match them using suburb name AND LGA name together
merged = with_bracket.merge(
    lookup,
    left_on=["BASE_NAME", "BRACKET_LGA"],
    right_on=["SUBURB_NAME", "LGA_UPPER"],
    how="left",
)
matched = merged[merged["POSTCODE"].notna()]
not_matched = merged[merged["POSTCODE"].isna()]
print("Bracket suburbs matched:", matched["CRIME_NAME"].nunique())
print("Bracket suburbs NOT matched:", not_matched["CRIME_NAME"].nunique())
print(not_matched["CRIME_NAME"].head(15).tolist())

# Step 7: Look at suburbs with no bracket that are still not in the lookup
no_bracket = suburbs[suburbs["BRACKET_LGA"].isna()]
missing = no_bracket[~no_bracket["CRIME_NAME"].isin(lookup["SUBURB_NAME"])]
print()
print("No bracket and not in lookup:", len(missing))
print(missing["CRIME_NAME"].head(40).tolist())


# Step 8: Look at all BACK CREEK rows in the lookup file
print()
print("BACK CREEK in the lookup file:")
print(lookup[lookup["SUBURB_NAME"] == "BACK CREEK"][["SUBURB_NAME", "POSTCODE", "LGA_NAME"]])

# Step 9: Search the lookup LGA names for words that appear in the brackets
print()
for word in ["BLAND", "TWEED", "MID", "CENTRAL COAST", "SNOWY", "QUEANBEYAN", "LISMORE"]:
    found = lookup[lookup["LGA_UPPER"].str.contains(word, na=False)]["LGA_UPPER"].unique()
    print(word, "->", found)

# Step 10: Check the LGA column in general
print()
print("Number of different LGA names:", lookup["LGA_UPPER"].nunique())
print("Empty LGA names:", lookup["LGA_NAME"].isna().sum())


# Step 11: Check which LGA names in the lookup file have brackets
print()
print("LGA names with brackets in the lookup file:")
print(sorted(lookup[lookup["LGA_UPPER"].str.contains("(", regex=False)]["LGA_UPPER"].unique()))

# Step 12: Make the LGA names in both files use the same style
# Lookup file: remove " (NSW)" from names like "CENTRAL COAST (NSW)"
lookup["LGA_CLEAN"] = lookup["LGA_UPPER"].str.replace(" (NSW)", "", regex=False)

# Crime file: remove " REGIONAL" from names like "QUEANBEYAN-PALERANG REGIONAL"
suburbs["BRACKET_CLEAN"] = suburbs["BRACKET_LGA"].str.replace(" REGIONAL", "", regex=False)

# Step 13: Try the match again with the cleaned names
with_bracket = suburbs[suburbs["BRACKET_LGA"].notna()]
merged2 = with_bracket.merge(
    lookup,
    left_on=["BASE_NAME", "BRACKET_CLEAN"],
    right_on=["SUBURB_NAME", "LGA_CLEAN"],
    how="left",
)
matched2 = merged2[merged2["POSTCODE"].notna()]
not_matched2 = merged2[merged2["POSTCODE"].isna()]
print()
print("Bracket suburbs matched now:", matched2["CRIME_NAME"].nunique())
print("Bracket suburbs still NOT matched:", not_matched2["CRIME_NAME"].nunique())
print(not_matched2["CRIME_NAME"].head(30).tolist())

# Step 14: Summary of the whole matching
total = len(suburbs)
bracket_ok = matched2["CRIME_NAME"].nunique()
no_bracket_ok = no_bracket["CRIME_NAME"].isin(lookup["SUBURB_NAME"]).sum()
print()
print("Total crime suburbs:", total)
print("Can be matched to a postcode:", bracket_ok + no_bracket_ok)
print("Will be excluded:", total - bracket_ok - no_bracket_ok)

# Step 15: Find suburbs (no bracket) that belong to more than one postcode
names = no_bracket[no_bracket["CRIME_NAME"].isin(lookup["SUBURB_NAME"])]["CRIME_NAME"]
counts = lookup[lookup["SUBURB_NAME"].isin(names)].groupby("SUBURB_NAME")["POSTCODE"].nunique()
multi = counts[counts > 1]

print()
print("Suburbs with more than 1 postcode:", len(multi))
print(multi.sort_values(ascending=False).head(10))

# Step 16: Show the details of the first 3 examples
for name in multi.index[:3]:
    print()
    print(lookup[lookup["SUBURB_NAME"] == name][["SUBURB_NAME", "POSTCODE", "LGA_NAME"]])