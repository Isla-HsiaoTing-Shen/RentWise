/* =============================================================================
   04_data_quality_checks.sql
   Shows how many raw rows each cleaning rule removed, in the same order
   as 03_create_clean_tables.sql.
   Each row is counted once, under the FIRST rule that removes it.
============================================================================= */

WITH typed AS (
    SELECT
        postcode,
        dwelling_type                          AS dwelling_type_code,
        TRY_CAST(bedrooms    AS INT)           AS bedrooms,
        TRY_CAST(weekly_rent AS DECIMAL(10,2)) AS weekly_rent
    FROM raw_bond_lodgements
),
labelled AS (
    SELECT
        CASE
            WHEN dwelling_type_code NOT IN ('F', 'H', 'T')        THEN '1. Dwelling type not F/H/T'
            WHEN bedrooms IS NULL                                 THEN '2. Bedrooms unknown (U)'
            WHEN weekly_rent IS NULL                              THEN '3. Weekly rent unknown (U)'
            WHEN bedrooms = 0 AND dwelling_type_code IN ('H', 'T') THEN '4. 0-bedroom house/terrace'
            WHEN (dwelling_type_code IN ('F', 'T') AND bedrooms > 6)
              OR (dwelling_type_code = 'H' AND bedrooms > 12)     THEN '5. Above bedroom cap'
            WHEN weekly_rent < 100                                THEN '6. Rent below $100'
            WHEN postcode = '2617'                                THEN '7. Postcode 2617 (ACT only)'
            ELSE                                                       '8. Kept'
        END AS outcome
    FROM typed
)
SELECT
    outcome,
    COUNT(*)                                                       AS row_count,
    CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS DECIMAL(5,2)) AS pct_of_raw
FROM labelled
GROUP BY outcome
ORDER BY outcome;