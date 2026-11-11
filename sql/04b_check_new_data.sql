/* =============================================================================
   04b_check_new_data.sql
   Run after loading new monthly files (every 3 months).
   Checks that the cleaning rules, set on 2021–2025 data, still fit the new data:
   the share removed by each rule should be close to the cleaning summary in
   data_quality_log.md (Rule 1 about 6.9%, all rules about 8.1%).

   Change @from to the first month you want to check. It only READS from the raw table.
============================================================================= */

DECLARE @from DATE = '2026-01-01';     -- first new month to check


/* -----------------------------------------------------------------------------
   1. Rows per month and file (each month should come from one file)
----------------------------------------------------------------------------- */
SELECT
    LEFT(lodgement_date, 7)      AS month,
    COUNT(*)                     AS raw_rows,
    COUNT(DISTINCT source_file)  AS files
FROM raw_bond_lodgements
WHERE TRY_CAST(LEFT(lodgement_date, 10) AS DATE) >= @from
GROUP BY LEFT(lodgement_date, 7)
ORDER BY month;


/* -----------------------------------------------------------------------------
   2. Missing or unreadable dates (should be 0)
----------------------------------------------------------------------------- */
SELECT COUNT(*) AS bad_dates
FROM raw_bond_lodgements
WHERE source_file IN (
        SELECT DISTINCT source_file FROM raw_bond_lodgements
        WHERE TRY_CAST(LEFT(lodgement_date, 10) AS DATE) >= @from)
  AND TRY_CAST(LEFT(lodgement_date, 10) AS DATE) IS NULL;


/* -----------------------------------------------------------------------------
   3. Dwelling type codes (any code that is not F, H, T, O or U is new)
----------------------------------------------------------------------------- */
SELECT dwelling_type, COUNT(*) AS raw_rows
FROM raw_bond_lodgements
WHERE TRY_CAST(LEFT(lodgement_date, 10) AS DATE) >= @from
GROUP BY dwelling_type
ORDER BY raw_rows DESC;


/* -----------------------------------------------------------------------------
   4. Rows removed by each cleaning rule (same order as 03_create_clean_tables.sql;
      each row is counted under the first rule that removes it)
----------------------------------------------------------------------------- */
WITH typed AS (
    SELECT
        postcode,
        dwelling_type                           AS code,
        TRY_CAST(bedrooms    AS INT)            AS bedrooms,
        TRY_CAST(weekly_rent AS DECIMAL(10, 2)) AS weekly_rent
    FROM raw_bond_lodgements
    WHERE TRY_CAST(LEFT(lodgement_date, 10) AS DATE) >= @from
),
flagged AS (
    SELECT
        CASE
            WHEN code NOT IN ('F', 'H', 'T')                                   THEN '1. Dwelling type not F/H/T'
            WHEN bedrooms IS NULL                                               THEN '2. Bedrooms unknown (U)'
            WHEN weekly_rent IS NULL                                            THEN '3. Weekly rent unknown (U)'
            WHEN bedrooms = 0 AND code IN ('H', 'T')                            THEN '4. 0-bedroom house/terrace'
            WHEN (code IN ('F', 'T') AND bedrooms > 6) OR (code = 'H' AND bedrooms > 12)
                                                                                THEN '5. Above bedroom cap'
            WHEN weekly_rent < 100                                              THEN '6. Rent below $100'
            WHEN postcode = '2617'                                              THEN '7. Postcode 2617 (ACT only)'
            ELSE '0. Kept'
        END AS rule_name
    FROM typed
)
SELECT
    rule_name,
    COUNT(*) AS raw_rows,
    CAST(100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS DECIMAL(5, 2)) AS pct_of_raw
FROM flagged
GROUP BY rule_name
ORDER BY rule_name;