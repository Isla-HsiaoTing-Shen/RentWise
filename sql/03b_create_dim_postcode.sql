/* =============================================================================
   03b_create_dim_postcode.sql
   Builds dim_postcode: one row per NSW postcode, used for the map,
   suburb search and region filter in Power BI, and by the RentWise website export.

   area (added in v1.0): 'Greater Sydney' or 'Rest of NSW' (BR-16), the same
   definition as Q3 in 06_analysis.sql, so Power BI and the analysis match.

   Note: export_for_web.py reads postcode, postcode_label, region, latitude and
   longitude. Columns can be ADDED here, but do not rename or remove those five.
============================================================================= */


/* -----------------------------------------------------------------------------
   Step 1. Create the table
----------------------------------------------------------------------------- */
DROP TABLE IF EXISTS dim_postcode;

CREATE TABLE dim_postcode (
    postcode CHAR(4) PRIMARY KEY,
    suburbs NVARCHAR(MAX),
    postcode_label NVARCHAR(MAX),
    region NVARCHAR(100),
    area NVARCHAR(20),                  -- 'Greater Sydney' or 'Rest of NSW'
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);
GO   -- run the CREATE first, so the next part can see the new area column


/* -----------------------------------------------------------------------------
   Step 2. Fill it
   "nsw" keeps one row per postcode + locality (the CSV has a few repeats).
   STRING_AGG joins the suburb names into one text value per postcode.
   Greater Sydney = ABS SA4 regions starting with "Sydney -", plus Central Coast.
----------------------------------------------------------------------------- */
WITH nsw AS (
    SELECT
        postcode,
        locality,
        MAX(sa4name) AS sa4name,
        AVG(TRY_CAST(lat AS FLOAT)) AS lat,
        AVG(TRY_CAST(long AS FLOAT)) AS lon
    FROM raw_postcodes
    WHERE state = 'NSW'
      AND TRY_CAST(lat AS FLOAT) <> 0
      AND TRY_CAST(long AS FLOAT) <> 0
    GROUP BY postcode, locality
)
INSERT INTO dim_postcode (postcode, suburbs, postcode_label, region, area, latitude, longitude)
SELECT
    postcode,
    STRING_AGG(CAST(locality AS NVARCHAR(MAX)), ', ')
        WITHIN GROUP (ORDER BY locality) AS suburbs,
    CONCAT(postcode, ' – ',
        STRING_AGG(CAST(locality AS NVARCHAR(MAX)), ', ')
            WITHIN GROUP (ORDER BY locality)) AS postcode_label,
    MAX(sa4name) AS region,
    CASE
        WHEN MAX(sa4name) LIKE 'Sydney -%' OR MAX(sa4name) = 'Central Coast'
            THEN 'Greater Sydney'
        ELSE 'Rest of NSW'
    END AS area,
    AVG(lat) AS latitude,
    AVG(lon) AS longitude
FROM nsw
GROUP BY postcode;
GO

SELECT * FROM dim_postcode WHERE postcode IN ('2000', '2017', '2618');


/* -----------------------------------------------------------------------------
   Step 3. Checks
----------------------------------------------------------------------------- */

-- 3a. How many NSW postcodes? (923)
SELECT COUNT(*) AS nsw_postcodes FROM dim_postcode;

-- 3b. Example: postcode 2000
SELECT * FROM dim_postcode WHERE postcode = '2000';

-- 3c. Postcodes in the clean bond data that have no match in dim_postcode
--     (these rows stay in the analysis but cannot be shown on the map)
SELECT
    c.postcode,
    COUNT(*) AS lodgements
FROM clean_bond_lodgements c
LEFT JOIN dim_postcode d ON c.postcode = d.postcode
WHERE d.postcode IS NULL
GROUP BY c.postcode
ORDER BY lodgements DESC;

-- 3d. Postcodes and lodgements per area.
--     For 2021–2025 this should match Q3 in analysis_findings.md:
--     Greater Sydney 1,109,125 and Rest of NSW 401,005 lodgements
--     (Q3 counts the 13 unmatched lodgements as Rest of NSW; here they show as NULL).
SELECT
    d.area,
    COUNT(DISTINCT d.postcode) AS postcodes,
    COUNT(*) AS lodgements_2021_2025
FROM clean_bond_lodgements c
LEFT JOIN dim_postcode d ON c.postcode = d.postcode
WHERE c.lodgement_year BETWEEN 2021 AND 2025
GROUP BY d.area
ORDER BY d.area;

-- 3e. Which SA4 regions are in Greater Sydney? (every "Sydney - …" region plus Central Coast)
SELECT region, COUNT(*) AS postcodes
FROM dim_postcode
WHERE area = 'Greater Sydney'
GROUP BY region
ORDER BY region;

