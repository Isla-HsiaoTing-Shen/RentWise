# Business Requirements Document — NSW Rent Fairness Dashboard

**Revision history**

| Version | Change |
|---|---|
| 0.1 | Initial draft |
| 0.2 | Study period set to 2021–2025 (annual files available). Stakeholders updated. Data cleaning rules refined using the official NSW Fair Trading field definitions. |
| 0.3 | Cleaning thresholds confirmed after data profiling (see `data_quality_log.md`): minimum sample size, zero-bedroom rule, bedroom caps, low-rent threshold, postcode rule. |

---

## 1. Background

Renters in New South Wales usually judge whether a rent is fair by scrolling through current listings. Listings show **asking** prices, not what tenants actually agreed to pay, and they give no sense of the typical range or how prices have moved over time.

NSW Fair Trading publishes every new rental bond lodged in the state, including the agreed weekly rent, postcode, dwelling type and number of bedrooms. This is one of the most complete public records of actual rents in NSW, but it is released as spreadsheets that most renters will never open.

This project turns that data into an interactive dashboard that answers two everyday questions:

1. **Is this rent reasonable for this area?**
2. **How have rents in this area changed over time?**

---

## 2. Problem Statement

> Renters in NSW lack an easy, data-backed way to tell whether a property's rent is below, within or above the typical market range for that area, and cannot easily see how local rents have changed over time. As a result, they negotiate and make decisions with limited information.

---

## 3. Proposed Solution & Value

| | |
|---|---|
| **Solution** | A Power BI dashboard built on NSW rental bond lodgement data. It shows the typical rent range (25th percentile, median, 75th percentile) for each postcode, dwelling type and bedroom count, lets users check a specific rent against that range, and shows rent trends from 2021 to 2025. |
| **Value** | Renters can assess a price before inspecting or applying, have evidence when negotiating a new lease or a renewal increase, and shortlist areas that fit their budget. |

---

## 4. Objectives

| ID | Objective | Delivered by |
|---|---|---|
| OBJ-01 | Provide a rent benchmark (p25 / median / p75) for every NSW postcode × dwelling type × bedroom combination that has enough data. | US-01, US-02 |
| OBJ-02 | Let a user classify a given rent as below, within or above the market range in under 30 seconds. | US-01 |
| OBJ-03 | Show quarterly rent trends from 2021 to 2025 and identify the areas with the largest increases. | US-03 |
| OBJ-04 | Be transparent about data sources, coverage and limitations so users know how far to trust each result. | US-05 |

---

## 5. Stakeholders

| Stakeholder | Role | Main need |
|---|---|---|
| **Private renters** (primary) | End users | Judge whether a rent is fair; understand local price trends |
| **International students** | End users | Find areas within a fixed, limited budget |
| **New arrivals to Sydney / NSW** | End users | Understand unfamiliar areas and typical prices quickly |
| **NSW Fair Trading** | Data provider | Data is cited correctly and interpreted within its stated limitations |

---

## 6. Scope

### In scope

- New rental bond lodgements in NSW, **January 2021 – December 2025** (annual files)
- Dwelling types: **Flat/unit, House, Terrace/townhouse/semi-detached**
- Postcode-level rent benchmarks by dwelling type and bedroom count
- Price fairness check for a user-entered rent
- Quarterly rent trends and year-on-year change
- Interactive map of median rent by postcode

### Out of scope

| Item | Reason |
|---|---|
| Dwelling type "Other" and "Unknown" | Per the source definition, "Other" may include rented rooms, garages and car spaces, which are not comparable with residential dwellings. |
| Years before 2021 | Annual files are only available from 2021. |
| Suburb recommendation / lifestyle scoring | Scoring weights would be subjective and cannot be validated against outcomes. |
| Rent forecasting | Reliable forecasts need external drivers (interest rates, migration, supply), which are outside this project's data. |
| Suburb-level analysis | The source data is only available at postcode level; one postcode often covers several suburbs. |
| Property-level valuation | The data has no information on size, condition, parking or other features. |
| Live / automated data refresh | Data is published monthly; manual refresh is sufficient for this version. |

---

## 7. User Stories & Acceptance Criteria

Priorities use **MoSCoW**: Must / Should / Could / Won't.

### US-01 — Check if a rent is fair · *Must*

> **As a** renter inspecting a property,
> **I want to** enter its weekly rent, postcode, dwelling type and number of bedrooms,
> **so that** I can tell whether the rent is below, within or above the typical market range.

**Acceptance criteria**
- [ ] User can select postcode (searchable by suburb name), dwelling type (Flat/unit, House, Terrace/townhouse) and bedroom group.
- [ ] User can enter a weekly rent amount.
- [ ] The dashboard shows p25, median and p75 for the selected combination.
- [ ] The rent is classified as *Below market range*, *Within market range* or *Above market range* (see BR-03).
- [ ] The sample size and benchmark period are displayed with the result.
- [ ] If the combination has fewer lodgements than the minimum sample size (BR-02), the dashboard shows "Insufficient data" and gives no classification.

### US-02 — Explore rents on a map · *Must*

> **As a** renter new to Sydney,
> **I want to** see median rents on a map and click on an area,
> **so that** I can quickly see which areas fit my budget.

**Acceptance criteria**
- [ ] Each postcode appears on the map, coloured or sized by median rent.
- [ ] Dwelling type and bedroom filters update the map.
- [ ] Clicking a postcode filters all other visuals on the page.
- [ ] The tooltip shows postcode, suburbs included, median rent and sample size.

### US-03 — Understand rent trends · *Should*

> **As a** renter facing a lease renewal,
> **I want to** see how rents in my postcode have changed over time,
> **so that** I can judge whether a proposed rent increase is in line with the market.

**Acceptance criteria**
- [ ] A line chart shows quarterly median rent from Q1 2021 to Q4 2025 for the selected postcode and filters.
- [ ] The latest year-on-year % change is shown.
- [ ] A comparison line for NSW overall is shown on the same chart.

### US-04 — Find areas within budget · *Should*

> **As an** international student with a fixed budget,
> **I want to** find postcodes where the median rent for my preferred dwelling type is within my budget,
> **so that** I can shortlist areas to inspect.

**Acceptance criteria**
- [ ] User can set a maximum weekly budget.
- [ ] Postcodes with median rent at or below the budget are highlighted on the map.
- [ ] A sortable table lists matching postcodes with median rent and sample size.

### US-05 — Know how far to trust the data · *Must*

> **As** any user,
> **I want to** know where the data comes from and what its limitations are,
> **so that** I can decide how much to rely on the results.

**Acceptance criteria**
- [ ] An information panel states the data source, period covered and last refresh date.
- [ ] Key limitations (Section 12) are listed in plain language.

---

## 8. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | Each dashboard page loads and responds to filters within 5 seconds. Power BI imports pre-aggregated SQL views, not raw records. |
| NFR-02 | Usability | A first-time user can complete US-01 without instructions. Labels use plain language rather than statistical terms where possible. |
| NFR-03 | Accuracy | Every benchmark figure can be traced back to a documented SQL query. |
| NFR-04 | Maintainability | Adding a new year of data requires only re-running the load script and refreshing the dashboard. |
| NFR-05 | Privacy | The source data contains no personal identifiers or addresses. No personal data is collected from users. |
| NFR-06 | Security | Database credentials are stored in environment variables and never committed to the repository. |

---

## 9. Data Requirements

| Dataset | Source | Key fields | Grain | Period |
|---|---|---|---|---|
| Rental bond lodgements | NSW Fair Trading — annual lodgement files (XLSX) | Lodgement Date, Postcode, Dwelling Type, Bedrooms, Weekly Rent | One row per bond lodged | 2021–2025 |
| Postcode lookup | Matthew Proctor — Australian Postcodes (CSV) | Postcode, Locality, State, Latitude, Longitude | One row per postcode–locality | Current |

Field definitions, code values and data types are documented in [`data_dictionary.md`](data_dictionary.md).

---

## 10. Business Rules & Definitions

All thresholds below were set after profiling the raw data. The evidence for each one is recorded in [`data_quality_log.md`](data_quality_log.md).

### Benchmark rules

| ID | Rule |
|---|---|
| BR-01 | **Benchmark period:** benchmarks use the most recent 12 months of lodgements (calendar year 2025). |
| BR-02 | **Minimum sample size:** a benchmark is shown only when the combination has at least **30** lodgements in the benchmark period. Combinations below 30 are shown as "Insufficient data". In 2025, combinations with 30+ lodgements cover 87.9% of rows. |
| BR-03 | **Fairness classification:** rent < p25 → *Below market range*; p25 ≤ rent ≤ p75 → *Within market range*; rent > p75 → *Above market range*. |

### Data cleaning rules

| ID | Rule | Reason |
|---|---|---|
| BR-04 | **Dwelling type:** keep F (Flat/unit), H (House) and T (Terrace/townhouse/semi-detached). Exclude O (Other), U (Unknown) and codes not in the data definition. | "Other" may include rooms, garages and car spaces. 38 rows use undefined codes (e.g. 1, G, X), which are entry errors. |
| BR-05 | **Unknown values:** exclude records where Bedrooms or Weekly Rent is "U". | Cannot be benchmarked. |
| BR-06 | **Zero bedrooms:** keep 0-bedroom records only for Flat/unit (labelled "Studio"). Exclude 0-bedroom House and Terrace records. | Per the source definition, 0 bedrooms may indicate a garage or car space. 0-bedroom houses and townhouses are rare (about 0.1% of rows) and cannot be verified. |
| BR-06a | **Bedroom caps:** keep up to 6 bedrooms for Flat/unit, 12 for House and 6 for Terrace/townhouse. | Above these values, counts are very small and scattered (e.g. 22, 29), which suggests entry errors. |
| BR-07 | **Low rents:** exclude weekly rents below **$100**. **No upper limit** is applied. | Rents under $100 for a whole dwelling are implausible, and counts rise clearly from $100. High rents cannot be reliably split into genuine luxury rentals and errors, so they are kept and all analysis uses medians, which are barely affected by a few extreme values. |
| BR-08 | **Postcode validity:** all postcodes are 4 digits within 2000–2898. Exclude postcode 2617, which covers ACT suburbs only. Keep 2611 and 2618, which also cover NSW border localities. | NSW Fair Trading holds bonds for NSW properties only. |
| BR-09 | **Identical records are kept.** | The data has no unique ID; identical rows may be different units in the same building lodged on the same day. |

### Grouping and display rules

| ID | Rule |
|---|---|
| BR-10 | **Bedroom groups:** Studio (0), 1, 2, 3, 4+. Grouping 4+ keeps sample sizes adequate. No records are removed by this rule. |
| BR-11 | **Postcode location:** each postcode is plotted at the average latitude and longitude of its localities. |
| BR-12 | **Postcode labels:** all analysis is at postcode level. Suburb names in a postcode are combined into one label for display and search only. Records are never duplicated across suburbs. |

### Glossary

| Term | Meaning |
|---|---|
| Median | The middle rent: half of lodgements are below it, half above. |
| p25 / p75 | 25% of lodgements are below p25; 75% are below p75. |
| Market range | Rents between p25 and p75 — the middle 50% of the market. |
| Bond lodgement | A bond registered with NSW Fair Trading at the start of a new tenancy. |
| Lodgement date | The date the bond was lodged, which is usually close to, but not exactly, the tenancy start date. |

---

## 11. Assumptions & Constraints

**Assumptions**
- The weekly rent recorded at lodgement is the rent agreed at the start of the tenancy.
- The lodgement date is close enough to the tenancy start date for quarterly trend analysis.
- Bond lodgements are broadly representative of the new-lease private rental market in each postcode.

**Constraints**
- Data is only available at postcode level, not suburb or property level.
- Annual files are only available from 2021, so there is no pre-2021 baseline.
- The data has no property features (size, condition, parking, furnishings), so benchmarks cannot adjust for quality.
- Public sharing options for Power BI may be limited; the dashboard is presented through screenshots, a demo GIF and the `.pbix` file.

---

## 12. Risks & Limitations

| Risk / limitation | Impact | Mitigation |
|---|---|---|
| Data covers **new** leases only, not rents paid by existing tenants | Benchmarks may be higher than average rents across all tenancies | State clearly in the dashboard and README |
| Values are self-reported by agents and landlords | Entry errors may distort percentiles | Cleaning rules BR-04 to BR-08; all exclusions logged with row counts; medians used instead of averages |
| One postcode covers several suburbs with different price levels | A benchmark may hide variation within a postcode | Show which suburbs each postcode includes (BR-12) |
| Small sample sizes in some combinations | Unreliable percentiles | Minimum sample size rule (BR-02) |
| Study period starts in 2021 | Trends cannot be compared with pre-COVID levels | State as a limitation; describe trends from 2021 onwards only |
| Tenancies with no bond lodged are not captured | Some segments of the market may be under-represented | Document as a known limitation |
| Column names or layout may differ between annual files | Load errors or misaligned fields | Load all files into a raw table first; validate columns and row counts per file |

---

## 13. Traceability Matrix

| User story | Dashboard element | Data source (SQL view) |
|---|---|---|
| US-01 | Price check panel (What-if rent input + result card) | `vw_rent_benchmark` |
| US-02 | Postcode map + filters | `vw_postcode_summary` |
| US-03 | Rent trend line chart + YoY card | `vw_rent_trend` |
| US-04 | Budget slider + highlighted map + table | `vw_postcode_summary` |
| US-05 | Information panel | Static content + `vw_data_refresh` |

---

## 14. Success Criteria

- All *Must* user stories meet their acceptance criteria.
- At least 80% of in-scope lodgements in the benchmark period fall into combinations that meet the minimum sample size.
- Every number on the dashboard can be reproduced from the SQL scripts in this repository.
- The README presents at least three data-backed insights.

---

## 15. Open Questions

1. If Terrace/townhouse has small sample sizes in many postcodes, should it be merged with House?
2. Should the trend comparison line be NSW overall or Greater Sydney only?
3. Should regional NSW postcodes appear on the main map, or on a separate view?