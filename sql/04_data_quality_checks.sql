/* =============================================================================
   04_data_quality_checks.sql
============================================================================= */


/* Rules 1-2 
WITH typed AS (
    SELECT
        TRY_CAST(LEFT(lodgement_date, 10) AS DATE) AS lodgement_date,
        postcode,
        dwelling_type AS dwelling_type_code,
        TRY_CAST(bedrooms    AS INT) AS bedrooms,
        TRY_CAST(weekly_rent AS DECIMAL(10,2)) AS weekly_rent,
        source_file
    FROM raw_bond_lodgements
)
SELECT COUNT(*) AS rows_left
FROM typed
WHERE dwelling_type_code IN ('F', 'H', 'T')
    AND bedrooms IS NOT NULL
    AND weekly_rent IS NOT NULL;*/

/* Rules 1-7*/
WITH typed AS (
    SELECT
        TRY_CAST(LEFT(lodgement_date, 10) AS DATE) AS lodgement_date,
        postcode,
        dwelling_type AS dwelling_type_code,
        TRY_CAST(bedrooms    AS INT) AS bedrooms,
        TRY_CAST(weekly_rent AS DECIMAL(10,2)) AS weekly_rent,
        source_file
    FROM raw_bond_lodgements
)
SELECT COUNT(*) AS rows_left
FROM typed
WHERE dwelling_type_code IN ('F', 'H', 'T')
    AND bedrooms IS NOT NULL
    AND weekly_rent IS NOT NULL
    AND NOT (bedrooms = 0 AND dwelling_type_code IN ('H','T'))
    AND NOT (dwelling_type_code IN ('F', 'T') AND bedrooms > 6)
    AND NOT (dwelling_type_code = 'H' AND bedrooms > 12)
    AND weekly_rent >= 100
    AND postcode <> '2617';




