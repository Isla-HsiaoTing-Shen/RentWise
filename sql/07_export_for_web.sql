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
      Suburb names and coordinates are in postcodes.json (joined by postcode).
----------------------------------------------------------------------------- */
SELECT
    postcode,
    dwelling_type,
    bedroom_group,
    sample_size,
    p25_rent,
    median_rent,
    p75_rent,
    meets_min_sample
FROM vw_rent_benchmark
ORDER BY postcode, dwelling_type, bedroom_group;



SELECT COUNT(*) AS all_rows FROM vw_rent_trend;

SELECT COUNT(*) AS rows_30_plus FROM vw_rent_trend WHERE sample_size >= 30;

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