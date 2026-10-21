/* =============================================================================
   03b_create_dim_postcode.sql
   Builds dim_postcode: one row per NSW postcode, used for the map,
   suburb search and region filter in Power BI.

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
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);


/* -----------------------------------------------------------------------------
   Step 2. Fill it
   "nsw" keeps one row per postcode + locality (the CSV has a few repeats).
   STRING_AGG joins the suburb names into one text value per postcode.
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
INSERT INTO dim_postcode (postcode, suburbs, postcode_label, region, latitude, longitude)
SELECT
    postcode,
    STRING_AGG(CAST(locality AS NVARCHAR(MAX)), ', ')
        WITHIN GROUP (ORDER BY locality) AS suburbs,
    CONCAT(postcode, ' – ',
        STRING_AGG(CAST(locality AS NVARCHAR(MAX)), ', ')
            WITHIN GROUP (ORDER BY locality)) AS postcode_label,
    MAX(sa4name) AS region,
    AVG(lat) AS latitude,
    AVG(lon) AS longitude
FROM nsw
GROUP BY postcode;

SELECT * FROM dim_postcode WHERE postcode IN ('2000', '2017', '2618');
/* -----------------------------------------------------------------------------
   Step 3. Checks
----------------------------------------------------------------------------- */

-- 3a. How many NSW postcodes?
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


