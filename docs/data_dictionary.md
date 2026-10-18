# Data Dictionary — NSW Rent Fairness Dashboard

This document describes every table in the pipeline, from the raw source files to the views used by Power BI.

```
Source files ──► raw_bond_lodgements ──► clean_bond_lodgements ──► views ──► Power BI
Postcode CSV ──► raw_postcodes ────────► dim_postcode ───────────┘
```

---

## 1. Source: NSW rental bond lodgements

**Publisher:** NSW Fair Trading
**Format:** Annual XLSX files, 2021–2025
**Grain:** One row per rental bond lodged
**Note:** All values are provided by the agent or landlord at the start of a tenancy.

| Column | Definition (from source) | Values |
|---|---|---|
| Lodgement Date | Date the bond was lodged with Fair Trading. For bonds lodged through Rental Bonds Online, the date the agent or landlord completed the lodgement. | Date |
| Postcode | Postcode of the rented premises. | 4-digit code |
| Dwelling Type | Type of rented premises. | F = Flat/unit; H = House; T = Terrace/townhouse/semi-detached; O = Other (may include rented rooms, garages and car spaces); U = Unknown |
| Bedrooms | Number of bedrooms. | Number, or U = Unknown. 0 may indicate a bedsitter or studio, or premises such as a garage or car space. |
| Weekly Rent | Weekly rent amount. | Number, or U = Unknown |

> Because Bedrooms and Weekly Rent can contain the letter "U", these columns must be loaded as text and converted to numbers during cleaning.

---

## 2. Source: Australian postcodes

**Publisher:** Matthew Proctor — Australian Postcodes
**Format:** CSV
**Grain:** One row per postcode–locality (one postcode can have several localities)

| Column used | Description |
|---|---|
| postcode | 4-digit postcode |
| locality | Suburb or locality name |
| state | State abbreviation (filter: NSW) |
| lat | Latitude of the locality |
| long | Longitude of the locality |

> Confirm the exact column names against the downloaded file.

---

## 3. Table: `raw_bond_lodgements`

Source data loaded as-is. Nothing is cleaned or removed here, so the original values can always be checked.

| Column | Type | Description |
|---|---|---|
| lodgement_date | NVARCHAR(50) | As in source |
| postcode | NVARCHAR(10) | As in source |
| dwelling_type | NVARCHAR(10) | As in source |
| bedrooms | NVARCHAR(10) | As in source (may contain "U") |
| weekly_rent | NVARCHAR(20) | As in source (may contain "U") |
| source_file | NVARCHAR(100) | File the row came from, e.g. `lodgements_2023.xlsx` |
| loaded_at | DATETIME2 | When the row was loaded |

---

## 4. Table: `clean_bond_lodgements`

Rows that pass all cleaning rules (BR-04 to BR-09 in the business requirements). Created by `sql/03_create_clean_tables.sql`., with correct data types and derived fields.

| Column | Type | Description |
|---|---|---|
| lodgement_date | DATE | Converted from source |
| lodgement_year | INT | Year of lodgement |
| lodgement_quarter | CHAR(7) | e.g. `2023-Q2` |
| postcode | CHAR(4) | Valid NSW postcode |
| dwelling_type_code | CHAR(1) | F, H or T |
| dwelling_type | NVARCHAR(30) | Flat/unit, House, Terrace/townhouse |
| bedrooms | INT | Number of bedrooms |
| bedroom_group | NVARCHAR(10) | Studio, 1, 2, 3, 4+ |
| weekly_rent | DECIMAL(10,2) | Weekly rent in AUD |
| source_file | NVARCHAR(100) | Carried from raw table for traceability |

---

## 5. Table: `dim_postcode`

One row per NSW postcode. Used for map location, labels and suburb search.

| Column | Type | Description |
|---|---|---|
| postcode | CHAR(4) | Primary key |
| suburbs | NVARCHAR(MAX) | All localities in the postcode, comma-separated (for display and search only) |
| latitude | DECIMAL(9,6) | Average latitude of localities |
| longitude | DECIMAL(9,6) | Average longitude of localities |
| postcode_label | NVARCHAR(MAX) | e.g. `2000 – Barangaroo, Dawes Point, Haymarket, …` |

---

## 6. Views for Power BI

| View | Grain | Key columns | Used for |
|---|---|---|---|
| `vw_rent_benchmark` | Postcode × dwelling type × bedroom group (benchmark period) | p25, median, p75, sample_size, meets_min_sample | US-01 price check |
| `vw_rent_trend` | Postcode × dwelling type × bedroom group × quarter | median_rent, sample_size, yoy_change_pct | US-03 trends |
| `vw_postcode_summary` | Postcode × dwelling type × bedroom group | median_rent, sample_size, latitude, longitude, suburbs | US-02 map, US-04 budget search |
| `vw_data_refresh` | One row | data_start, data_end, last_loaded, total_rows, rows_in_scope | US-05 information panel |