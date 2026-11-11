/* =============================================================================
   08_portfolio_checks.sql
   Two checks for the RentWise README. They only READ from clean_bond_lodgements.
   Run the whole file at once (the DECLARE lines are used by both checks).

   A. Coverage: how many benchmarks have 30+ leases, and what share of leases they cover.
   B. Validation: our median for the last 3 months, to compare with NSW Rent Check
      (https://www.nsw.gov.au/rent-check), which uses the last 3 months of bonds.
============================================================================= */

DECLARE @end_month DATE = (SELECT DATEFROMPARTS(YEAR(MAX(lodgement_date)), MONTH(MAX(lodgement_date)), 1)
                           FROM clean_bond_lodgements);           -- newest month, e.g. 2026-09-01
DECLARE @start     DATE = DATEADD(MONTH, -11, @end_month);        -- latest 12 months
DECLARE @start_3m  DATE = DATEADD(MONTH, -2,  @end_month);        -- latest 3 months
DECLARE @stop      DATE = DATEADD(MONTH, 1,   @end_month);


/* -----------------------------------------------------------------------------
   A. Coverage (latest 12 months)
   README line: "X of Y combinations have 30+ leases, covering Z% of all new leases."
----------------------------------------------------------------------------- */
WITH combos AS (
    SELECT postcode, dwelling_type, bedroom_group, COUNT(*) AS leases
    FROM clean_bond_lodgements
    WHERE lodgement_date >= @start AND lodgement_date < @stop
    GROUP BY postcode, dwelling_type, bedroom_group
)
SELECT
    COUNT(*)                                             AS combinations,
    SUM(CASE WHEN leases >= 30 THEN 1 ELSE 0 END)        AS combinations_30_plus,
    SUM(leases)                                          AS all_leases,
    SUM(CASE WHEN leases >= 30 THEN leases ELSE 0 END)   AS leases_in_30_plus,
    CAST(100.0 * SUM(CASE WHEN leases >= 30 THEN leases ELSE 0 END) / SUM(leases)
         AS DECIMAL(5, 1))                               AS pct_leases_covered
FROM combos;


/* -----------------------------------------------------------------------------
   B. Validation: last 3 months, for 4 example benchmarks
   Then enter the same postcode, type and bedrooms in NSW Rent Check and
   write its median and range next to ours. They should be close, not identical:
   Rent Check's 3 months and cleaning rules may differ slightly from ours.
----------------------------------------------------------------------------- */
WITH last3 AS (
    SELECT postcode, dwelling_type, bedroom_group, weekly_rent
    FROM clean_bond_lodgements
    WHERE lodgement_date >= @start_3m AND lodgement_date < @stop
      AND (   (postcode = '2142' AND dwelling_type = 'House'       AND bedroom_group = '2')
           OR (postcode = '2000' AND dwelling_type = 'Flat / Unit' AND bedroom_group = '2')
           OR (postcode = '2017' AND dwelling_type = 'Flat / Unit' AND bedroom_group = '1')
           OR (postcode = '2650' AND dwelling_type = 'House'       AND bedroom_group = '3'))
)
SELECT DISTINCT
    @start_3m AS from_month,
    @end_month AS to_month,
    postcode, dwelling_type, bedroom_group,
    COUNT(*) OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS leases,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p25_rent,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS median_rent,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p75_rent
FROM last3
ORDER BY postcode;