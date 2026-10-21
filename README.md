# NSW Rent Fairness

A rent benchmark for New South Wales, built from 1.6 million rental bond lodgements (2021–2025).
For a postcode, dwelling type and number of bedrooms, it shows what a new lease usually costs.
A renter can use it to check if an asking rent is fair.

**Tools:** Python (pandas, SQLAlchemy) · Azure SQL (T-SQL) · Power BI

---

## Key insights

All figures are **median weekly rents** for new leases. I use the median, not the average,
because a few very high rents can pull the average up.

Full results and method for each question: [docs/analysis_findings.md](docs/analysis_findings.md)

### 1. Flat rents went up the most

| Dwelling type | 2021 | 2025 | Change |
|---|---|---|---|
| Flat / Unit | $460 | $700 | **+52.2%** |
| Terrace / Townhouse / Semi-detached | $520 | $720 | +38.5% |
| House | $510 | $680 | +33.3% |

In 2021, flats were the cheapest dwelling type. In 2025, flats cost more than houses.

### 2. The biggest rises were near universities (2-bedroom flats)

| Postcode | Suburbs | 2021 | 2025 | Change |
|---|---|---|---|---|
| 2032 | Daceyville, Kingsford | $450 | $850 | **+88.9%** |
| 2008 | Chippendale, Darlington | $650 | $1,198 | +84.2% |
| 2007 | Broadway, Ultimo | $580 | $1,050 | +81.0% |
| 2017 | Waterloo, Zetland | $650 | $1,150 | +76.9% |
| 2000 | Barangaroo, Haymarket, The Rocks, … | $750 | $1,319 | +75.9% |

Six of the ten biggest rises were in postcodes near UNSW, UTS or the University of Sydney.
In Kingsford, the median rent almost doubled.

*Possible reason (not tested): international students could not enter Australia in 2021,
so rents near universities were low. When students came back, rents there rose faster.*

*Only postcodes with at least 30 lodgements in both 2021 and 2025 are included.*

### 3. The rise in flat rents was mostly in Sydney

| Dwelling type | Greater Sydney | Rest of NSW |
|---|---|---|
| Flat / Unit | **+56.3%** ($480 → $750) | +28.6% ($350 → $450) |
| Terrace / Townhouse | +39.1% ($575 → $800) | +31.9% ($470 → $620) |
| House | +31.0% ($580 → $760) | **+33.3%** ($450 → $600) |

Flats in Greater Sydney went up about twice as much as flats in the rest of NSW.
For houses, the rest of NSW went up a little more than Sydney.

*Greater Sydney uses the ABS definition: all "Sydney -" SA4 regions plus Central Coast.*

### 4. Where renters can most easily pay too much (2-bedroom flats, 2025)

The range from P25 to P75 shows the middle half of rents. A wide range compared with the
median means similar flats are rented at very different prices.

| Postcode | Suburbs | P25 | Median | P75 | Range / median |
|---|---|---|---|---|---|
| 2627 | Bullocks Flat, Crackenback, Creel Bay, … | $500 | $550 | $850 | **63.6%** |
| 2163 | Carramar, Lansdowne, Villawood | $420 | $455 | $650 | 50.5% |
| 2068 | Castlecrag, Middle Cove, Willoughby, … | $700 | $820 | $1,100 | 48.8% |
| 2065 | Crows Nest, Greenwich, Naremburn, … | $800 | $950 | $1,193 | 41.3% |
| 2265 | Cooranbong, Martinsville | $270 | $440 | $450 | 40.9% |

In these postcodes, it is most useful to check an asking rent against the benchmark.

*Only benchmarks with at least 30 lodgements are included.*

### 5. February is the busiest month

| | Month | 2-bedroom flat lodgements (2021–2025) |
|---|---|---|
| Busiest | February | 42,748 |
| Quietest | December | 33,061 |

February has about 29% more new leases than December.

---

## Dashboard

*(Power BI screenshots will be added here.)*

---

## Data

| Source | What it contains |
|---|---|
| NSW Fair Trading, Rental Bond Lodgements | One row per new bond, 2021–2025: date, postcode, dwelling type, bedrooms, weekly rent |
| Matthew Proctor, Australian Postcodes | Postcode → suburb names, ABS SA4 region, latitude and longitude |

---

## Method

```
Excel / CSV ──→ Python ──→ Azure SQL ──→ Power BI
               (load)    (check, clean, model)
```

1. **Load** – Python loads the raw files into SQL without changes
   (`load_bonds.py`, `load_postcodes.py`).
2. **Profile** – 13 checks on the raw data before cleaning (`02_profiling.sql`).
3. **Clean** – 7 cleaning rules. 1,643,058 raw rows → **1,510,130 clean rows (91.9% kept)**.
   Each rule and the number of rows it removed is in
   [docs/data_quality_log.md](docs/data_quality_log.md).
4. **Model** – a postcode table (923 NSW postcodes) and three views for Power BI:
   - `vw_rent_benchmark` – 2025 P25, median and P75 for each postcode, dwelling type and bedroom group
   - `vw_rent_trend` – median rent by quarter for each postcode, dwelling type and bedroom group
   - `vw_rent_trend_nsw` – median rent by quarter for all of NSW
5. **Analyse** – the five questions above (`06_analysis.sql`).

Medians use `PERCENTILE_CONT` (exact), not `APPROX_PERCENTILE_CONT`, because the approximate
version gave different results each time it ran.

---

## Limitations

- Only **new** leases are included. Renewals and existing tenants are not.
- Rents are entered by agents and landlords. Very high rents were kept, because real
  high-end rentals cannot be reliably told apart from entry errors. Using medians reduces
  their effect.
- In insights 1 and 3, each median mixes all bedroom sizes. If the mix of properties changes,
  the median can change even if prices do not.
- 13 lodgements have postcodes that are not in the postcode table. They stay in the analysis
  but cannot be shown on the map.
- ABS puts some NSW border postcodes in ACT, Queensland or Victoria regions.

---

## How to run

Run these in order from the project folder. Database login details go in a `.env` file.

1. `sql/01_create_raw_tables.sql`
2. `python python/load_bonds.py`
3. `sql/02_profiling.sql`
4. `sql/03_create_clean_tables.sql`
5. `sql/04_data_quality_checks.sql`
6. `python python/load_postcodes.py`
7. `sql/03b_create_dim_postcode.sql`
8. `sql/05_create_views.sql`
9. `sql/06_analysis.sql`