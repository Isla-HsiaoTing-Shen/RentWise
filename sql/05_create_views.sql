/* =============================================================================
   05_create_views.sql
   Views that Power BI will import. Each view is a saved query on
   clean_bond_lodgements; it stores no data of its own.

   - vw_rent_benchmark   2025 rent range per postcode × dwelling type × bedrooms (US-01)
   - vw_rent_trend       quarterly median rent per postcode × dwelling type × bedrooms (US-03)
   - vw_rent_trend_nsw   quarterly median rent for NSW overall (US-03 comparison line)

   Medians and percentiles use PERCENTILE_CONT, which is exact, so the
   numbers are the same every time the view is queried.

   GO separates batches: SQL Server requires each CREATE VIEW to run on its own.
============================================================================= */


/* -----------------------------------------------------------------------------
   View 1: vw_rent_benchmark
   One row per postcode × dwelling type × bedroom group, using 2025 lodgements.
   Benchmarks with fewer than 30 lodgements are flagged (BR-02).
----------------------------------------------------------------------------- */


CREATE OR ALTER VIEW vw_rent_benchmark AS
WITH stats AS (
    SELECT DISTINCT
        postcode,
        dwelling_type,
        bedroom_group,
        COUNT(*)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS sample_size,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p25_rent,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS median_rent,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY weekly_rent)
            OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p75_rent
    FROM clean_bond_lodgements
    WHERE lodgement_year = 2025
)
SELECT
    postcode,
    dwelling_type,
    bedroom_group,
    sample_size,
    p25_rent,
    median_rent,
    p75_rent,
    CASE WHEN sample_size >= 30 THEN 'Yes' ELSE 'No' END AS meets_min_sample
FROM stats;
GO






/* -----------------------------------------------------------------------------
   View 2: vw_rent_trend
   One row per postcode × dwelling type × bedroom group × quarter (2021–2025).
----------------------------------------------------------------------------- */

CREATE OR ALTER VIEW vw_rent_trend AS
SELECT DISTINCT
    postcode,
    dwelling_type,
    bedroom_group,
    lodgement_year,
    lodgement_quarter,
    COUNT(*)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group, lodgement_quarter) AS sample_size,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group, lodgement_quarter) AS median_rent
FROM clean_bond_lodgements;
GO



/* -----------------------------------------------------------------------------
   View 3: vw_rent_trend_nsw
   One row per dwelling type × bedroom group × quarter, for all of NSW.
   Needed because a median of postcode medians is NOT the NSW median,
   so the NSW line must be calculated from the individual lodgements.
----------------------------------------------------------------------------- */


CREATE OR ALTER VIEW vw_rent_trend_nsw AS
SELECT DISTINCT
    dwelling_type,
    bedroom_group,
    lodgement_year,
    lodgement_quarter,
    COUNT(*)
        OVER (PARTITION BY dwelling_type, bedroom_group, lodgement_quarter) AS sample_size,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY dwelling_type, bedroom_group, lodgement_quarter) AS median_rent
FROM clean_bond_lodgements;
GO

/* -----------------------------------------------------------------------------
   View 4: vw_dim_dwelling_type
   One row per dwelling type. Used by Power BI slicers to filter all views.
----------------------------------------------------------------------------- */
CREATE OR ALTER VIEW vw_dim_dwelling_type AS
SELECT DISTINCT dwelling_type
FROM clean_bond_lodgements;
GO


/* -----------------------------------------------------------------------------
   View 5: vw_dim_bedroom_group
   One row per bedroom group, with a sort order so Studio comes first.
----------------------------------------------------------------------------- */
CREATE OR ALTER VIEW vw_dim_bedroom_group AS
SELECT DISTINCT
    bedroom_group,
    CASE bedroom_group
        WHEN 'Studio' THEN 0
        WHEN '1' THEN 1
        WHEN '2' THEN 2
        WHEN '3' THEN 3
        WHEN '4+' THEN 4
    END AS bedroom_sort
FROM clean_bond_lodgements;
GO






/* -----------------------------------------------------------------------------
   Checks (run after the views are created)
----------------------------------------------------------------------------- */

-- 1. Top 10 benchmarks by sample size
SELECT TOP 10 *
FROM vw_rent_benchmark
ORDER BY sample_size DESC;

-- 2. Quarterly trend: 2-bedroom flats in Zetland (2017)
SELECT *
FROM vw_rent_trend
WHERE postcode = '2017'
  AND dwelling_type = 'Flat / Unit'
  AND bedroom_group = '2'
ORDER BY lodgement_quarter;

-- 3. Quarterly trend: 2-bedroom flats, NSW overall
SELECT lodgement_quarter, median_rent, sample_size
FROM vw_rent_trend_nsw
WHERE dwelling_type = 'Flat / Unit'
  AND bedroom_group = '2'
ORDER BY lodgement_quarter;

-- 4. How many benchmarks meet the 30-lodgement minimum?
SELECT
    meets_min_sample,
    COUNT(*)         AS combinations,
    SUM(sample_size) AS lodgements
FROM vw_rent_benchmark
GROUP BY meets_min_sample;

--5. Check the dimension views
SELECT * FROM vw_dim_dwelling_type;
SELECT * FROM vw_dim_bedroom_group ORDER BY bedroom_sort;
