/* =============================================================================
   07_export_for_web.sql
   Queries that prepare data for the RentWise website.
   They only READ from the views; nothing is changed, so Power BI is not affected.
   python/export_for_web.py runs the same queries and saves them as JSON.
============================================================================= */


/* -----------------------------------------------------------------------------
   1. postcodes.json – one row per postcode that has rent data.
      Used for the postcode list, map points and distance calculation.
----------------------------------------------------------------------------- */
SELECT
    postcode,
    postcode_label,
    region,
    latitude,
    longitude
FROM dim_postcode
WHERE postcode IN (SELECT DISTINCT postcode FROM vw_rent_benchmark)
ORDER BY postcode;


/* -----------------------------------------------------------------------------
   2. benchmark.json – 2025 rent benchmark.
      Used for the rent check, budget finder and map colours.
      min_rent / max_rent come from clean_bond_lodgements (same 2025 rows
      as the view), so the view itself is not changed and Power BI is not affected.
----------------------------------------------------------------------------- */
SELECT
    b.postcode,
    b.dwelling_type,
    b.bedroom_group,
    b.sample_size,
    b.p25_rent,
    b.median_rent,
    b.p75_rent,
    m.min_rent,
    m.max_rent,
    b.meets_min_sample
FROM vw_rent_benchmark AS b
LEFT JOIN (
    SELECT
        postcode,
        dwelling_type,
        bedroom_group,
        MIN(weekly_rent) AS min_rent,
        MAX(weekly_rent) AS max_rent
    FROM clean_bond_lodgements
    WHERE lodgement_year = 2025
    GROUP BY postcode, dwelling_type, bedroom_group
) AS m
    ON  m.postcode      = b.postcode
    AND m.dwelling_type = b.dwelling_type
    AND m.bedroom_group = b.bedroom_group
ORDER BY b.postcode, b.dwelling_type, b.bedroom_group;




SELECT DISTINCT
    MIN(weekly_rent) OVER ()                                          AS min_rent,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY weekly_rent) OVER () AS p05,
    PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY weekly_rent) OVER () AS p10,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY weekly_rent) OVER () AS p90,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY weekly_rent) OVER () AS p95,
    MAX(weekly_rent) OVER ()                                          AS max_rent
FROM clean_bond_lodgements
WHERE lodgement_year = 2025
  AND postcode       = '2017'
  AND dwelling_type  = 'Flat / Unit'
  AND bedroom_group  = '2';


/* -----------------------------------------------------------------------------
   3. trend.json – quarterly median rent per postcode, dwelling type and bedrooms.
      Only quarters with at least 30 lodgements (BR-02), so the trend line
      is not driven by a few unusual leases.
----------------------------------------------------------------------------- */
SELECT
    postcode,
    dwelling_type,
    bedroom_group,
    lodgement_quarter,
    sample_size,
    median_rent
FROM vw_rent_trend
WHERE sample_size >= 30
ORDER BY postcode, dwelling_type, bedroom_group, lodgement_quarter;


/* -----------------------------------------------------------------------------
   4. trend_nsw.json – quarterly median rent for all of NSW.
      Every quarter has thousands of lodgements, so no filter is needed.
----------------------------------------------------------------------------- */
SELECT
    dwelling_type,
    bedroom_group,
    lodgement_quarter,
    sample_size,
    median_rent
FROM vw_rent_trend_nsw
ORDER BY dwelling_type, bedroom_group, lodgement_quarter;