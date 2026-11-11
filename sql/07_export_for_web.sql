/* =============================================================================
   07_export_for_web.sql
   Queries that prepare data for the RentWise website.
   They only READ from clean_bond_lodgements and dim_postcode; the Power BI views
   are not changed, so Power BI is not affected.
   python/export_for_web.py runs the same queries and saves them as JSON.

   The website uses the LATEST 12 MONTHS of data. The window is found from the
   data itself (the newest month), so nothing needs changing when new months are added.

   Run the whole file at once: the DECLARE lines at the top are used by every query.
============================================================================= */


/* -----------------------------------------------------------------------------
   0. The 12-month window (today: Oct 2025 – Sep 2026)
----------------------------------------------------------------------------- */
DECLARE @end_month   DATE = (SELECT DATEFROMPARTS(YEAR(MAX(lodgement_date)), MONTH(MAX(lodgement_date)), 1)
                             FROM clean_bond_lodgements);              -- newest month, e.g. 2026-09-01
DECLARE @start       DATE = DATEADD(MONTH, -11, @end_month);           -- 2025-10-01
DECLARE @stop        DATE = DATEADD(MONTH, 1, @end_month);             -- 2026-10-01 (day AFTER the window)

SELECT @start AS window_start, @end_month AS window_end;

-- check: the window must have all 12 months (a missing month = a file not loaded)
SELECT COUNT(DISTINCT YEAR(lodgement_date) * 100 + MONTH(lodgement_date)) AS months_in_window   -- should be 12
FROM clean_bond_lodgements
WHERE lodgement_date >= @start AND lodgement_date < @stop;


/* -----------------------------------------------------------------------------
   1. benchmark.json – rent figures for the latest 12 months.
      P5/P95 = lowest and highest without extreme leases.
      meets_min_sample = 'Yes' when there are at least 30 leases (BR-02).
----------------------------------------------------------------------------- */
WITH latest AS (
    SELECT postcode, dwelling_type, bedroom_group, weekly_rent
    FROM clean_bond_lodgements
    WHERE lodgement_date >= @start AND lodgement_date < @stop
),
stats AS (
    SELECT DISTINCT
        postcode,
        dwelling_type,
        bedroom_group,
        COUNT(*) OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS sample_size,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p05_rent,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p25_rent,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS median_rent,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p75_rent,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p95_rent
    FROM latest
)
SELECT
    postcode, dwelling_type, bedroom_group, sample_size,
    p25_rent, median_rent, p75_rent, p05_rent, p95_rent,
    CASE WHEN sample_size >= 30 THEN 'Yes' ELSE 'No' END AS meets_min_sample
FROM stats
ORDER BY postcode, dwelling_type, bedroom_group;


/* -----------------------------------------------------------------------------
   2. postcodes.json – postcodes that have data in the latest 12 months.
      Used for the postcode list, map points and distance calculation.
----------------------------------------------------------------------------- */
SELECT postcode, postcode_label, region, latitude, longitude
FROM dim_postcode
WHERE postcode IN (
    SELECT DISTINCT postcode FROM clean_bond_lodgements
    WHERE lodgement_date >= @start AND lodgement_date < @stop
)
ORDER BY postcode;


/* -----------------------------------------------------------------------------
   3. rent_spread.json – how many leases at each $50 of rent, latest 12 months.
      bin_start 550 = $550 to $599.99. Used for the "Where most rents fall" chart.
      export_for_web.py keeps only benchmarks with 30+ leases (BR-02) and puts
      the bins for each benchmark in one row.
      (The rent history over the years is in Power BI, not on the website.)
----------------------------------------------------------------------------- */
SELECT
    postcode,
    dwelling_type,
    bedroom_group,
    CAST(FLOOR(weekly_rent / 50) * 50 AS INT) AS bin_start,
    COUNT(*) AS leases
FROM clean_bond_lodgements
WHERE lodgement_date >= @start AND lodgement_date < @stop
GROUP BY postcode, dwelling_type, bedroom_group, CAST(FLOOR(weekly_rent / 50) * 50 AS INT)
ORDER BY postcode, dwelling_type, bedroom_group, bin_start;


/* -----------------------------------------------------------------------------
   4. Spot checks (not exported)
----------------------------------------------------------------------------- */

-- 4a. P5/P95 vs min/max for one benchmark (why the site shows P5/P95)
SELECT DISTINCT
    MIN(weekly_rent) OVER ()                                          AS min_rent,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY weekly_rent) OVER () AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY weekly_rent) OVER () AS p95,
    MAX(weekly_rent) OVER ()                                          AS max_rent
FROM clean_bond_lodgements
WHERE lodgement_date >= @start AND lodgement_date < @stop
  AND postcode = '2017' AND dwelling_type = 'Flat / Unit' AND bedroom_group = '2';

-- 4b. The spread for one benchmark: the counts should add up to sample_size in benchmark.json
SELECT
    CAST(FLOOR(weekly_rent / 50) * 50 AS INT) AS bin_start,
    COUNT(*) AS leases,
    SUM(COUNT(*)) OVER () AS total_leases
FROM clean_bond_lodgements
WHERE lodgement_date >= @start AND lodgement_date < @stop
  AND postcode = '2142' AND dwelling_type = 'House' AND bedroom_group = '2'
GROUP BY CAST(FLOOR(weekly_rent / 50) * 50 AS INT)
ORDER BY bin_start;


