/* =============================================================================
   08b_compare_rent_check.sql
   Our P25 / median / P75 for the SAME 3 months as NSW Rent Check
   ("Based on latest data from 29/04/2026" = 3 months up to 29 April 2026),
   for the 5 combinations tested on https://www.nsw.gov.au/rent-check.
   Rent Check's "median rent range" is the 25th–75th percentile (interquartile range).
   It only READS from clean_bond_lodgements.
============================================================================= */

DECLARE @rc_end   DATE = '2026-04-29';                      -- Rent Check's "latest data"
DECLARE @rc_start DATE = DATEADD(MONTH, -3, @rc_end);       -- 3 months before

WITH tested AS (
    SELECT postcode, dwelling_type, bedroom_group, weekly_rent
    FROM clean_bond_lodgements
    WHERE lodgement_date > @rc_start AND lodgement_date <= @rc_end
      AND (   (postcode = '2000' AND dwelling_type = 'Flat / Unit' AND bedroom_group = '2')   -- test 1: $1,200 – $1,650
           OR (postcode = '2142' AND dwelling_type = 'Flat / Unit' AND bedroom_group = '2')   -- test 2: $550 – $720
           OR (postcode = '2017' AND dwelling_type = 'Flat / Unit' AND bedroom_group = '3')   -- test 3: $1,500 – $1,780
           OR (postcode = '2067' AND dwelling_type = 'House'       AND bedroom_group = '3')   -- test 4: $1,200 – $1,550
           OR (postcode = '2131' AND dwelling_type = 'House'       AND bedroom_group = '3'))  -- test 5: $879 – $1,000
)
SELECT DISTINCT
    postcode, dwelling_type, bedroom_group,
    COUNT(*) OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS leases,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p25_rent,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS median_rent,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY weekly_rent)
        OVER (PARTITION BY postcode, dwelling_type, bedroom_group) AS p75_rent
FROM tested
ORDER BY postcode;

