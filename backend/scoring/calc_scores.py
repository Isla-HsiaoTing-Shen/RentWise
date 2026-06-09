"""
calc_scores.py
NSW Rental Suitability Project
================================
Calculate suburb suitability scores for three personas and write to suburb_scores table.

Workflow:
1. Load 28 target suburbs (curated selection across North/West/Inner West/South/East Sydney)
2. Calculate raw values for each scoring dimension
3. Min-Max normalise to 0-10 scale
4. Apply persona-specific weights and calculate overall score
5. Write results to suburb_scores table

Methodology references:
- Higgs et al. (2019) Urban Liveability Index - composite indicator design and normalisation
- Nasreen (2017) - Sydney rental affordability context
"""

import pyodbc
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv(r"D:\Rental\.env")

# ── Connect to Azure SQL ────────────────────────────────────────────────────
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=tcp:{os.getenv('AZURE_SERVER')},1433;"
    f"DATABASE={os.getenv('AZURE_DATABASE')};"
    f"UID={os.getenv('AZURE_USERNAME')};"
    f"PWD={os.getenv('AZURE_PASSWORD')};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
print("Connected to Azure SQL")
cursor = conn.cursor()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: Load 28 target suburbs
# ══════════════════════════════════════════════════════════════════════════════
print("\nStep 1: Loading target suburb list...")

TARGET_SUBURBS = [
    # 北區
    'Chatswood', 'North Ryde', 'Macquarie Park', 'Epping', 'Eastwood',
    # 西區
    'Parramatta', 'Lidcombe', 'Auburn', 'Granville', 'Westmead', 'Homebush', 'Merrylands',
    # 內西
    'Burwood', 'Strathfield', 'Ashfield', 'Campsie', 'Rhodes', 'Wolli Creek',
    # 南區
    'Mascot', 'Zetland', 'Waterloo', 'Kensington', 'Kingsford', 'Hurstville',
    # 東區
    'Bondi Junction', 'Coogee', 'Randwick', 'Maroubra',
]

placeholders = ','.join(['?' for _ in TARGET_SUBURBS])
target_df = pd.read_sql(
    f"SELECT suburb_id, suburb_name FROM dbo.suburbs WHERE suburb_name IN ({placeholders})",
    conn,
    params=TARGET_SUBURBS
)
target_ids = tuple(target_df['suburb_id'].tolist())
print(f"   Target suburbs: {len(target_ids)}")

# Warn if any suburbs not found
found = set(target_df['suburb_name'].tolist())
missing = [s for s in TARGET_SUBURBS if s not in found]
if missing:
    print(f"   ⚠️  Not found in DB: {missing}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: Calculate raw values for each dimension
# ══════════════════════════════════════════════════════════════════════════════
print("\nStep 2: Calculating raw dimension values...")

# ── 2a. Transport (station_dist_km, lower is better) ───────────────────────
# Filter outliers: only keep suburbs within 50km of a station
# This excludes remote suburbs like Broken Hill (190km+) which are
# outside the 26 LGA study area
transport_query = f"""
    SELECT suburb_id, station_dist_km
    FROM dbo.transport_access
    WHERE suburb_id IN {target_ids}
    AND station_dist_km <= 50
"""
transport_df = pd.read_sql(transport_query, conn)
transport_df = transport_df.rename(columns={'station_dist_km': 'transport_raw'})
print(f"   Transport: {len(transport_df)} records (outliers >50km removed)")

# ── 2b. Safety (crime incident count, lower is better) ─────────────────────
# Use 3-year average (2022-2025) across all crime types:
# Assault, Robbery, Malicious damage to property
# Note: crime_rate column is NULL as population data unavailable,
# using incident_count as a proxy instead
crime_query = f"""
    SELECT suburb_id,
           AVG(CAST(incident_count AS FLOAT)) AS crime_raw
    FROM dbo.crime_stats
    WHERE suburb_id IN {target_ids}
    AND year >= 2022
    GROUP BY suburb_id
"""
crime_df = pd.read_sql(crime_query, conn)
print(f"   Safety: {len(crime_df)} records (3-year average 2022-2025)")

# ── 2c. Schools (ICSEA rating already normalised to 0-10, higher is better)
# ICSEA scores were normalised to 0-10 during load_schools.py
# Using suburb-level average of all school ratings
school_query = f"""
    SELECT suburb_id,
           AVG(rating) AS school_raw
    FROM dbo.schools
    WHERE suburb_id IN {target_ids}
    AND rating IS NOT NULL
    GROUP BY suburb_id
"""
school_df = pd.read_sql(school_query, conn)
print(f"   Schools: {len(school_df)} records")

# ── 2d. Amenities (weighted count, higher is better) ───────────────────────
# Daily essentials (supermarket, pharmacy) weighted higher than
# lifestyle amenities (cafe, gym, park) following the principle
# that access to basic services is a fundamental liveability indicator
# (Higgs et al., 2019 - social infrastructure mix domain)
amenity_query = f"""
    SELECT suburb_id,
           SUM(
               CASE amenity_type
                   WHEN 'supermarket' THEN count * 3
                   WHEN 'pharmacy'    THEN count * 2
                   WHEN 'hospital'    THEN count * 2
                   WHEN 'cafe'        THEN count * 1
                   WHEN 'gym'         THEN count * 1
                   WHEN 'park'        THEN count * 1
                   WHEN 'university'  THEN count * 1
                   ELSE count
               END
           ) AS amenity_raw
    FROM dbo.amenities
    WHERE suburb_id IN {target_ids}
    GROUP BY suburb_id
"""
amenity_df = pd.read_sql(amenity_query, conn)
print(f"   Amenities: {len(amenity_df)} records")

# ── 2e. Price (median weekly rent, lower is better) ─────────────────────────
# Filter outliers: $100-$3000/week covers the realistic NSW rental range
# Using only active listings from the past 90 days for current market data
price_query = f"""
    SELECT suburb_id,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_weekly)
               OVER (PARTITION BY suburb_id) AS price_raw
    FROM dbo.rentals
    WHERE suburb_id IN {target_ids}
    AND is_active = 'True'
    AND price_weekly BETWEEN 100 AND 3000
"""

price_df = pd.read_sql(price_query, conn)
price_df = price_df.drop_duplicates(subset=['suburb_id'])
print(f"   Price: {len(price_df)} records (outliers filtered, active listings only)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Merge all dimensions
# ══════════════════════════════════════════════════════════════════════════════
print("\nStep 3: Merging all dimensions...")

# Start from amenities as the base (most complete, covers all 474 suburbs)
df = amenity_df.copy()
df = df.merge(transport_df, on='suburb_id', how='left')
df = df.merge(crime_df,     on='suburb_id', how='left')
df = df.merge(school_df,    on='suburb_id', how='left')
df = df.merge(price_df,     on='suburb_id', how='left')

print(f"   Total rows after merge: {len(df)}")
print("   Null value check:")
for col in ['transport_raw', 'crime_raw', 'school_raw', 'amenity_raw', 'price_raw']:
    null_count = df[col].isna().sum()
    print(f"     {col}: {null_count} nulls")

# Fill missing values with median (conservative approach to avoid bias)
for col in ['transport_raw', 'crime_raw', 'school_raw', 'amenity_raw', 'price_raw']:
    median_val = df[col].median()
    df[col] = df[col].fillna(median_val)
    print(f"   {col}: nulls filled with median value {median_val:.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Min-Max normalisation to 0-10 scale
# ══════════════════════════════════════════════════════════════════════════════
print("\nStep 4: Applying Min-Max normalisation...")

def min_max_normalize(series, reverse=False):
    """
    Normalise a series to 0-10 scale using Min-Max normalisation.

    Args:
        series: pandas Series of raw values
        reverse: if True, lower raw values produce higher scores.
                 Used for crime count and transport distance, where
                 less is better. Follows the reverse-scaling approach
                 described in Higgs et al. (2019) for negative indicators
                 such as air pollution.

    Returns:
        pandas Series of normalised scores rounded to 2 decimal places
    """
    min_val = series.min()
    max_val = series.max()

    # Handle edge case where all values are identical
    if max_val == min_val:
        return pd.Series([5.0] * len(series), index=series.index)

    if reverse:
        normalized = (max_val - series) / (max_val - min_val) * 10
    else:
        normalized = (series - min_val) / (max_val - min_val) * 10

    return normalized.round(2)


# Apply normalisation - reverse=True for dimensions where lower is better
df['transport_score'] = min_max_normalize(df['transport_raw'], reverse=True)
df['safety_score']    = min_max_normalize(df['crime_raw'],     reverse=True)
df['school_score']    = min_max_normalize(df['school_raw'],    reverse=False)
df['amenity_score']   = min_max_normalize(df['amenity_raw'],   reverse=False)
df['price_score']     = min_max_normalize(df['price_raw'],     reverse=True)

print("   Normalised score summary:")
for score_col in ['transport_score', 'safety_score', 'school_score',
                  'amenity_score', 'price_score']:
    print(f"     {score_col}: "
          f"min={df[score_col].min():.2f}, "
          f"max={df[score_col].max():.2f}, "
          f"avg={df[score_col].mean():.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: Load persona weights and calculate weighted overall score
# ══════════════════════════════════════════════════════════════════════════════
print("\nStep 5: Loading persona weights and calculating overall scores...")

profiles_query = """
    SELECT profile_id, profile_name,
           price_weight, safety_weight, transport_weight,
           school_weight, amenity_weight
    FROM dbo.user_profiles
"""
profiles_df = pd.read_sql(profiles_query, conn)
print(f"   Loaded {len(profiles_df)} personas: {profiles_df['profile_name'].tolist()}")

# Calculate weighted overall score for each suburb x persona combination.
# This implements the persona-specific liveability profiles concept proposed
# by Higgs et al. (2019, Future Applications):
# "It is possible to extend the ULI to accommodate sub-group specific domain
# weighting profiles, recognising that not all indicators are of equal
# importance to all groups of people."
results = []

for _, profile in profiles_df.iterrows():
    temp_df = df[['suburb_id', 'price_score', 'safety_score',
                  'transport_score', 'school_score', 'amenity_score']].copy()

    temp_df['profile_id'] = profile['profile_id']

    temp_df['overall_score'] = (
        temp_df['price_score']     * profile['price_weight']     +
        temp_df['safety_score']    * profile['safety_weight']    +
        temp_df['transport_score'] * profile['transport_weight'] +
        temp_df['school_score']    * profile['school_weight']    +
        temp_df['amenity_score']   * profile['amenity_weight']
    ).round(2)

    results.append(temp_df)
    print(f"   {profile['profile_name']}: overall_score range "
          f"{temp_df['overall_score'].min():.2f} - "
          f"{temp_df['overall_score'].max():.2f}")

final_df = pd.concat(results, ignore_index=True)
print(f"\n   Total rows: {len(final_df)} "
      f"({len(df)} suburbs x {len(profiles_df)} personas)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: Write results to suburb_scores table
# ══════════════════════════════════════════════════════════════════════════════
print("\nStep 6: Writing to suburb_scores table...")

# Clear existing records for this version before re-inserting
cursor.execute("DELETE FROM dbo.suburb_scores WHERE score_version = 'v2.0'")
conn.commit()
print("   Existing v1.0 records cleared")

inserted = 0
errors = 0

for _, row in final_df.iterrows():
    try:
        cursor.execute("""
            INSERT INTO dbo.suburb_scores (
                suburb_id, profile_id, score_version,
                price_score, safety_score, transport_score,
                school_score, amenity_score, overall_score,
                calculated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            int(row['suburb_id']),
            int(row['profile_id']),
            'v2.0',
            float(row['price_score']),
            float(row['safety_score']),
            float(row['transport_score']),
            float(row['school_score']),
            float(row['amenity_score']),
            float(row['overall_score']),
            datetime.now()
        )
        inserted += 1
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"   Insert error: {e}")

    if inserted % 200 == 0 and inserted > 0:
        conn.commit()
        print(f"   Inserted {inserted} rows...", end='\r')

conn.commit()
print(f"\n   Done! Inserted {inserted} rows, {errors} errors")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7: Validation - show top suburbs for each persona
# ══════════════════════════════════════════════════════════════════════════════
print("\nStep 7: Validating results...")

validation_query = """
    SELECT
        p.profile_name,
        s.suburb_name,
        ss.overall_score,
        ss.price_score,
        ss.safety_score,
        ss.transport_score,
        ss.school_score,
        ss.amenity_score
    FROM dbo.suburb_scores ss
    JOIN dbo.suburbs s       ON ss.suburb_id  = s.suburb_id
    JOIN dbo.user_profiles p ON ss.profile_id = p.profile_id
    WHERE ss.score_version = 'v2.0'
    AND ss.overall_score IN (
        SELECT TOP 3 overall_score
        FROM dbo.suburb_scores
        WHERE profile_id = ss.profile_id
        AND score_version = 'v2.0'
        ORDER BY overall_score DESC
    )
    ORDER BY p.profile_name, ss.overall_score DESC
"""

validation_df = pd.read_sql(validation_query, conn)
print("\n   Top suburbs per persona:")
print(validation_df.to_string(index=False))

conn.close()
print("\ncalc_scores.py complete!")
print("Next step: Connect Power BI to suburb_scores table and build visualisations.")



