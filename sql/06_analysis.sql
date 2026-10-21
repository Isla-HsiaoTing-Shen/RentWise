/* =============================================================================
   06_analysis.sql
   Answers the business questions behind the dashboard. The results are in the 
   "analysis_findings.md".
   All analysis uses medians (not averages), as decided in the profiling step.
============================================================================= */


/* -----------------------------------------------------------------------------
   Q1. How much have median rents changed across NSW from 2021 to 2025,
       by dwelling type?
----------------------------------------------------------------------------- */


WITH yearly AS (
    SELECT DISTINCT
        dwelling_type,
        lodgement_year,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY dwelling_type, lodgement_year) AS median_rent
    FROM clean_bond_lodgements
),
pivoted AS (
    SELECT
        dwelling_type,
        MAX(CASE WHEN lodgement_year = 2021 THEN median_rent END) AS median_2021,
        MAX(CASE WHEN lodgement_year = 2022 THEN median_rent END) AS median_2022,
        MAX(CASE WHEN lodgement_year = 2023 THEN median_rent END) AS median_2023,
        MAX(CASE WHEN lodgement_year = 2024 THEN median_rent END) AS median_2024,
        MAX(CASE WHEN lodgement_year = 2025 THEN median_rent END) AS median_2025
    FROM yearly
    GROUP BY dwelling_type
)
SELECT
    *,
    CAST((median_2025 - median_2021) * 100.0 / median_2021 AS DECIMAL(5,1)) AS pct_change_2021_2025
FROM pivoted
ORDER BY dwelling_type;


/* -----------------------------------------------------------------------------
   Q2. Which postcodes had the largest rent increase for 2-bedroom flats
       from 2021 to 2025?
       Only postcodes with at least 30 lodgements in BOTH years (BR-02).
       Change ORDER BY to ASC to see the smallest increases.
----------------------------------------------------------------------------- */




WITH yearly AS (
    SELECT DISTINCT
        postcode,
        lodgement_year,
        COUNT(*) OVER (PARTITION BY postcode, lodgement_year) AS sample_size,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, lodgement_year) AS median_rent
    FROM clean_bond_lodgements
    WHERE dwelling_type_code = 'F'
      AND bedrooms = 2
      AND lodgement_year IN (2021, 2025)
),
pivoted AS (
    SELECT
        postcode,
        MAX(CASE WHEN lodgement_year = 2021 THEN median_rent END) AS median_2021,
        MAX(CASE WHEN lodgement_year = 2025 THEN median_rent END) AS median_2025,
        MIN(sample_size) AS smaller_sample,
        COUNT(*) AS years_with_data
    FROM yearly
    GROUP BY postcode
)
SELECT TOP 10
    p.postcode,
    LEFT(d.suburbs, 60) AS suburbs,
    p.median_2021,
    p.median_2025,
    CAST((p.median_2025 - p.median_2021) * 100.0 / p.median_2021 AS DECIMAL(5,1)) AS pct_change
FROM pivoted p
LEFT JOIN dim_postcode d ON p.postcode = d.postcode
WHERE p.years_with_data = 2
  AND p.smaller_sample >= 30
ORDER BY pct_change DESC;


/* -----------------------------------------------------------------------------
   Q3. Has rent growth been different in Greater Sydney and the rest of NSW?
       Greater Sydney = ABS SA4 regions starting with "Sydney -" plus Central Coast.
       The 13 lodgements with no postcode match fall into "Rest of NSW"
       (too few to affect the medians).
----------------------------------------------------------------------------- */

SELECT DISTINCT region
FROM dim_postcode
ORDER BY region;

WITH labelled AS (
    SELECT
        c.lodgement_year,
        c.dwelling_type,
        c.weekly_rent,
        CASE
            WHEN d.region LIKE 'Sydney -%' OR d.region = 'Central Coast' THEN 'Greater Sydney'
            ELSE 'Rest of NSW'
        END AS area
    FROM clean_bond_lodgements c
    LEFT JOIN dim_postcode d ON c.postcode = d.postcode
),
yearly AS (
    SELECT DISTINCT
        area,
        dwelling_type,
        lodgement_year,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY area, dwelling_type, lodgement_year) AS median_rent
    FROM labelled
    WHERE lodgement_year IN (2021, 2025)
),
pivoted AS (
    SELECT
        area,
        dwelling_type,
        MAX(CASE WHEN lodgement_year = 2021 THEN median_rent END) AS median_2021,
        MAX(CASE WHEN lodgement_year = 2025 THEN median_rent END) AS median_2025
    FROM yearly
    GROUP BY area, dwelling_type
)
SELECT
    *,
    CAST((median_2025 - median_2021) * 100.0 / median_2021 AS DECIMAL(5,1)) AS pct_change
FROM pivoted
ORDER BY dwelling_type, area;






/* -----------------------------------------------------------------------------
   Q4. Where is the 2025 rent range widest for 2-bedroom flats?
       A wide range (p75 - p25) relative to the median means prices are less
       consistent, so a renter is more likely to overpay without checking.
----------------------------------------------------------------------------- */

/*SELECT
    postcode,
    sample_size,
    p25_rent,
    median_rent,
    p75_rent
FROM vw_rent_benchmark
WHERE dwelling_type = 'Flat / Unit'
  AND bedroom_group = '2'
  AND meets_min_sample = 'Yes';*/



SELECT TOP 10
    b.postcode,
    LEFT(d.suburbs, 60) AS suburbs,
    b.sample_size,
    b.p25_rent,
    b.median_rent,
    b.p75_rent,
    b.p75_rent - b.p25_rent  AS range_width,
    CAST((b.p75_rent - b.p25_rent) * 100.0 / b.median_rent AS DECIMAL(5,1)) AS range_pct_of_median
FROM vw_rent_benchmark b
LEFT JOIN dim_postcode d ON b.postcode = d.postcode
WHERE b.dwelling_type = 'Flat / Unit'
  AND b.bedroom_group = '2'
  AND b.meets_min_sample = 'Yes'
ORDER BY range_pct_of_median DESC;


/* -----------------------------------------------------------------------------
   Q5. Is there a busy season? Lodgements and median rent by month
       (2-bedroom flats, all years combined).
----------------------------------------------------------------------------- */

SELECT DISTINCT
    MONTH(lodgement_date)                                       AS month_no,
    DATENAME(MONTH, lodgement_date)                             AS month_name,
    COUNT(*) OVER (PARTITION BY MONTH(lodgement_date))          AS lodgements,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY MONTH(lodgement_date))               AS median_rent
FROM clean_bond_lodgements
WHERE dwelling_type_code = 'F'
  AND bedrooms = 2
ORDER BY month_no;