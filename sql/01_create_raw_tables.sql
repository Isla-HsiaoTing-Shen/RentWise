-- 01_create_raw_tables.sql
-- Raw layer: NSW rental bond lodgements loaded exactly as published.
-- All source columns are text because Bedrooms and Weekly Rent can contain "U".

DROP TABLE IF EXISTS raw_bond_lodgements;

CREATE TABLE raw_bond_lodgements (
    lodgement_date  NVARCHAR(50),
    postcode        NVARCHAR(10),
    dwelling_type   NVARCHAR(10),
    bedrooms        NVARCHAR(10),
    weekly_rent     NVARCHAR(20),
    source_file     NVARCHAR(100),                  
    loaded_at       DATETIME2 DEFAULT SYSDATETIME() 
);