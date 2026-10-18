/* =============================================================================
   03_create_clean_tables.sql
   Builds clean_bond_lodgements from raw_bond_lodgements.
============================================================================= */


/* -----------------------------------------------------------------------------
   Step 1. Create an empty clean table with the correct data types
----------------------------------------------------------------------------- */
DROP TABLE IF EXISTS clean_bond_lodgements;

CREATE TABLE clean_bond_lodgements (
    lodgement_date      DATE,
    lodgement_year      INT,
    lodgement_quarter   CHAR(7),         -- e.g. 2025-Q3
    postcode            CHAR(4),
    dwelling_type_code  CHAR(1),         
    dwelling_type       NVARCHAR(50),    
    bedrooms            INT,
    bedroom_group       NVARCHAR(10),    
    weekly_rent         DECIMAL(10,2),
    source_file         NVARCHAR(100)
);

Select * from clean_bond_lodgements;


/* -----------------------------------------------------------------------------
   Step 2. Convert, filter and insert
----------------------------------------------------------------------------- */

WITH typed AS (
    SELECT
        TRY_CAST(LEFT(lodgement_date, 10) AS DATE)  AS lodgement_date,
        postcode,
        dwelling_type AS dwelling_type_code,
        TRY_CAST(bedrooms AS INT) AS bedrooms,
        TRY_CAST(weekly_rent AS DECIMAL(10,2)) AS weekly_rent,
        source_file
    FROM raw_bond_lodgements
)
INSERT INTO clean_bond_lodgements (
    lodgement_date,
    lodgement_year,
    lodgement_quarter,
    postcode,
    dwelling_type_code,
    dwelling_type,
    bedrooms,
    bedroom_group,
    weekly_rent,
    source_file
)
SELECT
    lodgement_date,
    YEAR(lodgement_date) AS lodgement_year,
    CONCAT(YEAR(lodgement_date), '-Q', DATEPART(QUARTER, lodgement_date)) AS lodgement_quarter,
    postcode,
    dwelling_type_code,
    CASE dwelling_type_code
        WHEN 'F' THEN 'Flat / Unit'
        WHEN 'H' THEN 'House'
        WHEN 'T' THEN 'Terrace / Townhouse / Semi-detached'
    END AS dwelling_type,
    bedrooms,
    CASE
        WHEN bedrooms = 0 THEN 'Studio'
        WHEN bedrooms = 1 THEN '1'
        WHEN bedrooms = 2 THEN '2'
        WHEN bedrooms = 3 THEN '3'
        WHEN bedrooms >= 4 THEN '4+'
    END AS bedroom_group,
    weekly_rent,
    source_file

FROM typed
WHERE dwelling_type_code IN ('F', 'H', 'T')
    AND bedrooms IS NOT NULL
    AND weekly_rent IS NOT NULL
    AND NOT (bedrooms = 0 AND dwelling_type_code IN ('H','T'))
    AND NOT (dwelling_type_code IN ('F', 'T') AND bedrooms > 6)
    AND NOT (dwelling_type_code = 'H' AND bedrooms > 12)
    AND weekly_rent >= 100
    AND postcode <> '2617';


SELECT COUNT(*) FROM clean_bond_lodgements;



/* -----------------------------------------------------------------------------
   Step 3. Quick checks 
----------------------------------------------------------------------------- */

/* 3a. Rows kept vs raw rows */
SELECT COUNT(*) AS raw_rows   FROM raw_bond_lodgements;
SELECT COUNT(*) AS clean_rows FROM clean_bond_lodgements;

/* 3b. Rows per year */
SELECT
    lodgement_year, 
    COUNT(*) AS year_count
FROM clean_bond_lodgements
GROUP BY lodgement_year
ORDER BY lodgement_year;

/* 3c. Rows per dwelling type and bedroom group */
SELECT
    dwelling_type,
    bedroom_group,
    COUNT(*) AS row_count
FROM clean_bond_lodgements
GROUP BY dwelling_type, bedroom_group
ORDER BY dwelling_type, bedroom_group;


/* 3d-1. Rent below $100 → should be 0 */
SELECT COUNT(*) AS bad_rows
FROM clean_bond_lodgements
WHERE weekly_rent < 100;

/* 3d-2. Studio units with dwelling type code 'H' or 'T' → should be 0 */
SELECT COUNT(*) AS bad_rows
FROM clean_bond_lodgements
WHERE bedrooms = 0 AND dwelling_type_code IN ('H', 'T');

/* 3d-3. Postcode '2617' → should be 0 */
SELECT COUNT(*) AS bad_rows
FROM clean_bond_lodgements
WHERE postcode = '2617';


/* 3d-4. Missing dates → should be 0 */
SELECT COUNT(*) AS bad_rows
FROM clean_bond_lodgements
WHERE lodgement_date IS NULL;

/* 3d-5. Bedrooms above the caps → should be 0 */
SELECT COUNT(*) AS bad_rows
FROM clean_bond_lodgements
WHERE (dwelling_type_code IN ('F', 'T') AND bedrooms > 6)
   OR (dwelling_type_code = 'H' AND bedrooms > 12);