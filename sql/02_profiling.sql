/* =============================================================================
   02_profiling.sql
   Data profiling of raw_bond_lodgements (2021–2025).

   Purpose: understand the data BEFORE cleaning it. Nothing is changed here.
   Each section answers one question. Run one section at a time
   (highlight it, then press Run) and record the findings in
   docs/data_quality_log.md.
============================================================================= */


/* -----------------------------------------------------------------------------
   1. Overview: how many rows per file, and does each file only contain
      dates from its own year?
----------------------------------------------------------------------------- */
Select source_file, 
    count(*) as year_records,
    min(TRY_CAST(LEFT(lodgement_date, 10) AS DATE)) as first_date_of_the_year,
    max(TRY_CAST(LEFT(lodgement_date, 10) AS DATE)) as last_date_of_the_year
from raw_bond_lodgements
GROUP BY source_file


/* -----------------------------------------------------------------------------
   2. Missing values: how many NULL / blank values does each column have?
----------------------------------------------------------------------------- */
SELECT 
    COUNT(*) as null_postcode_count
FROM raw_bond_lodgements
WHERE postcode IS NULL or postcode = '';

SELECT 
    COUNT(*) as null_dwelling_type_count
FROM raw_bond_lodgements
WHERE dwelling_type IS NULL or dwelling_type = '';

SELECT 
    COUNT(*) as null_bedrooms_count
FROM raw_bond_lodgements
WHERE bedrooms IS NULL or bedrooms = '';


SELECT 
    COUNT(*) as null_weekly_rent_count
FROM raw_bond_lodgements
WHERE weekly_rent IS NULL or weekly_rent = '';


/* -----------------------------------------------------------------------------
   3. Dwelling type: which codes appear, and how often?
      The definition only allows F, H, T, O, U.
----------------------------------------------------------------------------- */
SELECT dwelling_type,
    COUNT(*) AS dwelling_type_count
FROM raw_bond_lodgements
GROUP BY dwelling_type
order by dwelling_type_count desc

/* -----------------------------------------------------------------------------
   4. Bedrooms: which values appear, and how often?
----------------------------------------------------------------------------- */
SELECT bedrooms,
    COUNT(*) AS bedrooms_count
FROM raw_bond_lodgements
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC

/*how many bedrooms in apartments */
SELECT bedrooms,
    COUNT(*) AS apartments_bedrooms_count
FROM raw_bond_lodgements
WHERE dwelling_type = 'F'
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC


/*how many bedrooms in Houses */
SELECT bedrooms,
    COUNT(*) AS houses_bedrooms_count
FROM raw_bond_lodgements
WHERE dwelling_type = 'H'
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC


/*how many bedrooms in Townhouses */
SELECT bedrooms,
    COUNT(*) AS townhouses_bedrooms_count
FROM raw_bond_lodgements
WHERE dwelling_type = 'T'
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC

/* -----------------------------------------------------------------------------
   5. Zero bedrooms: how many per dwelling type, and what do they rent for?
      Helps decide BR-06 (keep 0-bedroom only for flats/units?).
----------------------------------------------------------------------------- */
SELECT dwelling_type,
    COUNT(*) AS dwelling_type_zero_bedrooms_count,
    CAST(AVG((TRY_CAST(weekly_rent AS DECIMAL(10,2))))AS DECIMAL(10,2)) AS avg_weekly_rent,
    Min(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS min_weekly_rent,
    Max(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS max_weekly_rent
FROM raw_bond_lodgements
WHERE bedrooms = '0'
GROUP BY dwelling_type
ORDER BY dwelling_type_zero_bedrooms_count DESC

/* -----------------------------------------------------------------------------
   6. High bedroom counts: what do 7+ bedroom lodgements look like?
      Helps decide whether to cap bedrooms. 
      Covered by Check 4b. Bedroom caps were set per dwelling type.
----------------------------------------------------------------------------- */


/* -----------------------------------------------------------------------------
   7. Weekly rent: values that are not numbers (e.g. "U").
----------------------------------------------------------------------------- */
SELECT
    weekly_rent,
    COUNT(*) AS row_count
FROM raw_bond_lodgements
WHERE TRY_CAST(weekly_rent AS DECIMAL(10,2)) IS NULL
GROUP BY weekly_rent
ORDER BY row_count DESC;


/* -----------------------------------------------------------------------------
   8. Weekly rent distribution (F, H, T only).
      Percentiles show where the extreme values start.
      Approximate percentiles are used because they are much faster on 1.6M rows.
----------------------------------------------------------------------------- */

SELECT dwelling_type,
    COUNT(*) AS dwelling_type_count,
    AVG(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS avg_weekly_rent,
    MIN(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS min_weekly_rent,
    MAX(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS max_weekly_rent,
    APPROX_PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS median_weekly_rent,
    ROUND(APPROX_PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))), 2) AS p1_weekly_rent,
    ROUND(APPROX_PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))), 2) AS p99_weekly_rent
FROM raw_bond_lodgements
WHERE dwelling_type = 'F' OR dwelling_type = 'H' OR dwelling_type = 'T'
GROUP BY dwelling_type



/* -----------------------------------------------------------------------------
   9. Low rents in detail: how many rows fall in each low band?
      Helps choose the lower threshold for BR-07.
----------------------------------------------------------------------------- */

SELECT weekly_rent,
    COUNT(*) AS rent_count
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND TRY_CAST(weekly_rent AS DECIMAL(10,2)) < 200
GROUP BY weekly_rent
ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))

/* -----------------------------------------------------------------------------
   10. High rents in detail: where are the very high rents, and are they
       plausible for that area and size? (e.g. a 1-bedroom flat at $5,000/week
       is probably a monthly rent entered by mistake)
----------------------------------------------------------------------------- */
SELECT top 50
    postcode,
    dwelling_type,
    bedrooms,
    TRY_CAST(weekly_rent AS DECIMAL(10,2)) AS weekly_rent
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2)) DESC

SELECT top 50
    COUNT(*) AS rent_3000_plus_count
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND TRY_CAST(weekly_rent AS DECIMAL(10,2)) >= 3000

SELECT top 50
    COUNT(*) AS rent_5000_plus_count
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND TRY_CAST(weekly_rent AS DECIMAL(10,2)) >= 5000


/* -----------------------------------------------------------------------------
   11. Postcodes: are they all 4 digits, and in which ranges?
       NSW residential postcodes are mostly 2000–2999
       (2600–2618 and 2900–2920 are ACT).
----------------------------------------------------------------------------- */
SELECT
    LEN(postcode) AS postcode_length,
    COUNT(*) AS postcode_length_count
FROM raw_bond_lodgements
GROUP BY LEN(postcode)

SELECT
    MIN(postcode) AS min_postcode_number,
    MAX(postcode) AS max_postcode_number
FROM raw_bond_lodgements

 /*2600-2618 = ACT */
SELECT
    COUNT(*) AS act_postcodes_count
FROM raw_bond_lodgements
WHERE postcode BETWEEN '2600' AND '2618'

SELECT
    postcode,
    COUNT(*) AS act_postcodes_count
FROM raw_bond_lodgements
WHERE postcode BETWEEN '2600' AND '2618'
GROUP BY postcode


/* -----------------------------------------------------------------------------
   12. Identical rows: how many rows are exact copies of another row?
       (Kept under BR-09, but worth knowing how common they are.)
----------------------------------------------------------------------------- */
SELECT
    lodgement_date,
    postcode,
    dwelling_type,
    bedrooms,
    weekly_rent,
    COUNT(*) AS copies
FROM raw_bond_lodgements
GROUP BY lodgement_date, postcode, dwelling_type, bedrooms, weekly_rent
HAVING COUNT(*) > 1
ORDER BY copies DESC;


/* -----------------------------------------------------------------------------
   13. Sample size check for 2025 (the benchmark year):
       how many postcode × dwelling type × bedroom combinations have at least
       30 lodgements, and what share of rows do they cover?
       Helps decide BR-02 (minimum sample size).
----------------------------------------------------------------------------- */
SELECT
    postcode,
    dwelling_type,
    bedrooms,
    COUNT(*) AS n
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND lodgement_date >= '2025-01-01'
GROUP BY postcode, dwelling_type, bedrooms
ORDER BY n DESC

