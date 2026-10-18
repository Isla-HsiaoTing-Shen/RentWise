SELECT TOP 10 * FROM raw_bond_lodgements;


SELECT    source_file,
COUNT(*) as year_records
FROM      raw_bond_lodgements
GROUP BY  source_file

/*question 1 */
SELECT TOP 10
    lodgement_date,
    CASE WHEN TRY_CAST(LEFT(lodgement_date, 10) AS DATE) IS NULL THEN 1 ELSE 0 END AS invalid_date
FROM raw_bond_lodgements


Select source_file, 
    count(*) as year_records,
    min(TRY_CAST(LEFT(lodgement_date, 10) AS DATE)) as first_date_of_the_year,
    max(TRY_CAST(LEFT(lodgement_date, 10) AS DATE)) as last_date_of_the_year
from raw_bond_lodgements
GROUP BY source_file


/*question 2 */
SELECT 
    COUNT(*) as null_postcode_count
FROM raw_bond_lodgements
WHERE postcode IS NULL or postcode = '';

SELECT 
    COUNT(*) as null_dwelling_type_count
FROM raw_bond_lodgements
WHERE dwelling_type IS NULL or dwelling_type = '';

SELECT 
    COUNT(*) as null_bedrooms_count
FROM raw_bond_lodgements
WHERE bedrooms IS NULL or bedrooms = '';


SELECT 
    COUNT(*) as null_weekly_rent_count
FROM raw_bond_lodgements
WHERE weekly_rent IS NULL or weekly_rent = '';

/*question 3 */
SELECT dwelling_type,
    COUNT(*) AS dwelling_type_count
FROM raw_bond_lodgements
GROUP BY dwelling_type
order by dwelling_type_count desc


/*question 4 */
SELECT bedrooms,
    COUNT(*) AS bedrooms_count
FROM raw_bond_lodgements
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC

/*how many bedrooms in apartments */
SELECT bedrooms,
    COUNT(*) AS apartments_bedrooms_count
FROM raw_bond_lodgements
WHERE dwelling_type = 'F'
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC


/*how many bedrooms in Houses */
SELECT bedrooms,
    COUNT(*) AS houses_bedrooms_count
FROM raw_bond_lodgements
WHERE dwelling_type = 'H'
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC


/*how many bedrooms in Townhouses */
SELECT bedrooms,
    COUNT(*) AS townhouses_bedrooms_count
FROM raw_bond_lodgements
WHERE dwelling_type = 'T'
GROUP BY bedrooms 
ORDER BY TRY_CAST(bedrooms AS INT) DESC

/*question 5 */
SELECT dwelling_type,
    COUNT(*) AS dwelling_type_zero_bedrooms_count,
    CAST(AVG((TRY_CAST(weekly_rent AS DECIMAL(10,2))))AS DECIMAL(10,2)) AS avg_weekly_rent,
    Min(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS min_weekly_rent,
    Max(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS max_weekly_rent
FROM raw_bond_lodgements
WHERE bedrooms = '0'
GROUP BY dwelling_type
ORDER BY dwelling_type_zero_bedrooms_count DESC

/*question 7 */
SELECT dwelling_type,
    COUNT(*) AS weekly_rent_count
FROM raw_bond_lodgements
WHERE TRY_CAST(weekly_rent AS DECIMAL(10,2)) IS NULL
GROUP BY dwelling_type
ORDER BY weekly_rent_count DESC

/*question 8 */

SELECT dwelling_type,
    COUNT(*) AS dwelling_type_count,
    AVG(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS avg_weekly_rent,
    MIN(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS min_weekly_rent,
    MAX(TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS max_weekly_rent,
    APPROX_PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))) AS median_weekly_rent,
    ROUND(APPROX_PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))), 2) AS p1_weekly_rent,
    ROUND(APPROX_PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))), 2) AS p99_weekly_rent
FROM raw_bond_lodgements
WHERE dwelling_type = 'F' OR dwelling_type = 'H' OR dwelling_type = 'T'
GROUP BY dwelling_type

/*question 9 */
SELECT weekly_rent,
    COUNT(*) AS rent_count
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND TRY_CAST(weekly_rent AS DECIMAL(10,2)) < 200
GROUP BY weekly_rent
ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2))

/*question 10 */
SELECT top 50
    postcode,
    dwelling_type,
    bedrooms,
    TRY_CAST(weekly_rent AS DECIMAL(10,2)) AS weekly_rent
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
ORDER BY TRY_CAST(weekly_rent AS DECIMAL(10,2)) DESC

SELECT top 50
    COUNT(*) AS rent_3000_plus_count
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND TRY_CAST(weekly_rent AS DECIMAL(10,2)) >= 3000

SELECT top 50
    COUNT(*) AS rent_5000_plus_count
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND TRY_CAST(weekly_rent AS DECIMAL(10,2)) >= 5000


  /*question 11 */
SELECT
    LEN(postcode) AS postcode_length,
    COUNT(*) AS postcode_length_count
FROM raw_bond_lodgements
GROUP BY LEN(postcode)

SELECT
    MIN(postcode) AS min_postcode_number,
    MAX(postcode) AS max_postcode_number
FROM raw_bond_lodgements

 /*2600-2618 = ACT */
SELECT
    COUNT(*) AS act_postcodes_count
FROM raw_bond_lodgements
WHERE postcode BETWEEN '2600' AND '2618'

SELECT
    postcode,
    COUNT(*) AS act_postcodes_count
FROM raw_bond_lodgements
WHERE postcode BETWEEN '2600' AND '2618'
GROUP BY postcode


  /*question 12 */
SELECT
    lodgement_date,
    postcode,
    dwelling_type,
    bedrooms,
    weekly_rent,
    COUNT(*) AS copies
FROM raw_bond_lodgements
GROUP BY lodgement_date, postcode, dwelling_type, bedrooms, weekly_rent
HAVING COUNT(*) > 1
ORDER BY copies DESC;


/*question 13 */
SELECT
    postcode,
    dwelling_type,
    bedrooms,
    COUNT(*) AS n
FROM raw_bond_lodgements
WHERE dwelling_type IN ('F', 'H', 'T')
  AND lodgement_date >= '2025-01-01'
GROUP BY postcode, dwelling_type, bedrooms
ORDER BY n DESC