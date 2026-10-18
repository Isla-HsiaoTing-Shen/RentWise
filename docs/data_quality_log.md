

### Check 1: File overview

**Question:** How many rows does each file have, and does each file only contain dates from its own year?

**Result:**

| File | Rows | First date | Last date |
|---|---|---|---|
| RentalBond_Lodgements_Year_2021.xlsx | 335,926 | 2021-01-01 | 2021-12-31 |
| RentalBond_Lodgements_Year_2022.xlsx | 330,396 | 2022-01-01 | 2022-12-31 |
| RentalBond_Lodgements_Year_2023.xlsx | 326,246 | 2023-01-01 | 2023-12-31 |
| RentalBond_Lodgements_Year_2024.xlsx | 328,183 | 2024-01-01 | 2024-12-31 |
| RentalBond_Lodgements_Year_2025.xlsx | 322,307 | 2025-01-01 | 2025-12-31 |
| **Total** | **1,643,058** | | |

**Findings:**
- Every file covers its full calendar year, with no dates from other years.
- Lodgements decline slightly each year (about 336k in 2021 to 322k in 2025).
- MIN and MAX ignore NULL values, so missing dates are checked separately in Check 2.

**Action:** None needed.


### Check 2: Missing values

**Question:** How many NULL or empty values does each column have?

**Result:** 0 in all five columns (lodgement_date, postcode, dwelling_type, bedrooms, weekly_rent).

**Findings:**
- No NULL or empty values in any column.
- Unknown values are recorded as the code "U" instead of being left blank. These are checked in Checks 3, 4 and 7.

**Action:** None needed for NULL/empty values.

### Check 3: Dwelling type

**Question:** Which dwelling type codes appear, and how often?

**Result:**

| Code | Rows | % |
|---|---|---|
| F (Flat/unit) | 824,626 | 50.19% |
| H (House) | 613,483 | 37.34% |
| T (Terrace/townhouse) | 91,993 | 5.60% |
| O (Other) | 58,736 | 3.57% |
| U (Unknown) | 54,182 | 3.30% |
| Invalid codes | 38 | 0.0023% |

**Findings:**
- 38 rows use codes that are not in the data definition (1, 3, 4, 5, G, I, P, R, X, Y, Z). These are likely data entry errors.
- O and U together make up 6.87% of rows.

**Action:**
- Keep F, H and T only. Remove O, U and invalid codes (6.87% of rows in total).

### Check 4: Bedrooms by dwelling type

**Question:** What is a reasonable maximum number of bedrooms for each dwelling type?

**Method:** Count rows per bedroom value, separately for F, H and T. Look for the point where counts drop sharply and values start to scatter.

**Result:**

| Dwelling type | Counts near the cut-off | Values above the cut-off |
|---|---|---|
| F (Flat/unit) | 5 bed: 448, 6 bed: 74, 7 bed: 26 | Scattered up to 29 |
| H (House) | 11 bed: 15, 12 bed: 14, 13 bed: 2 | Scattered up to 30 |
| T (Terrace/townhouse) | 5 bed: 1,457, 6 bed: 67, 7 bed: 7 | Scattered up to 22 |

**Findings:**
- The realistic maximum is different for each dwelling type. Houses can have many more bedrooms than flats or townhouses.
- Above the cut-off, values are scattered (e.g. 14, 22, 29), which suggests data entry errors.

**Action:**

| Dwelling type | Keep | Remove | Rows removed |
|---|---|---|---|
| F | 0–6 bedrooms | 7+ | 101 |
| H | 0–12 bedrooms | 13+ | 37 |
| T | 0–6 bedrooms | 7+ | 14 |
| **Total** | | | **152 (0.009%)** |

### Check 5: Zero bedrooms

**Question:** How many 0-bedroom rows are there for each dwelling type, and what do they rent for?

**Result:**

| Dwelling type | Rows | Avg rent | Min rent | Max rent |
|---|---|---|---|---|
| F | 14,467 | $459.52 | $30.00 | $3,450.00 |
| O | 3,465 | $288.01 | $10.00 | $5,712.00 |
| H | 1,541 | $483.48 | $14.00 | $3,600.00 |
| T | 73 | $426.90 | $208.00 | $1,400.00 |
| U | 3 | $303.33 | $260.00 | $370.00 |

**Findings:**
- Most 0-bedroom rows are flats (F), which are studio apartments.
- 0-bedroom houses and townhouses are rare (1,614 rows, 0.10% of all rows). They may be granny flats or data entry errors; the data cannot tell them apart.
- Min and max rents include implausible values (e.g. $14 and $3,600 per week), which distort the averages. Extreme rents are handled in Checks 8 and 9.

**Action:**
- Keep F + 0 bedrooms and label them as "Studio".
- Remove H and T with 0 bedrooms (1,614 rows, 0.10%).


### Check 7: Non-numeric weekly rent

**Question:** Which weekly rent values are not numbers?

**Result:** Only one non-numeric value: "U" (unknown), 25,830 rows (1.57%).

**Findings:**
- No other unexpected text values (e.g. "$", "N/A").

**Action:** Remove rows where weekly rent is "U".

### Check 8: Weekly rent distribution

**Question:** What does the weekly rent distribution look like for F, H and T, and where do extreme values start?

**Result:**

| Type | Rows | Min | P1 | Median | P99 | Max |
|---|---|---|---|---|---|---|
| F | 824,626 | $1 | $196 | $590 | $1,599 | $10,000 |
| H | 613,483 | $0 | $215 | $600 | $2,203 | $10,000 |
| T | 91,993 | $1 | $250 | $620 | $1,834 | $9,000 |

**Findings:**
- Most rents (98%) fall between P1 and P99.
- The lowest values ($0–$1) are far below P1, and the highest values ($9,000–$10,000) are far above P99. These extreme values sit in the two ends of the distribution.
- Averages ($640–$691) are higher than medians ($590–$620) because a few very high rents pull them up. Medians will be used for analysis.
- Percentiles are approximate (APPROX_PERCENTILE_CONT), so P1 and P99 change slightly between runs. They are used only to see roughly where extreme values start.

**Action:** No rows removed yet. Low and high rent thresholds are decided in Checks 9 and 10.

### Check 9: Low rents

**Question:** Below what weekly rent is a whole-dwelling rental implausible?

**Method:** List every rent value under $200 for F, H and T, with the number of rows for each, and look for where counts start to rise.

**Result:**
- $0 (82 rows) and $1 (112 rows) are much more common than nearby values, which suggests they were entered when the real rent was unknown.
- Rents are usually entered as round numbers, so trends are clearest at round amounts:

| Weekly rent | Rows |
|---|---|
| $50 | 38 |
| $70 | 57 |
| $90 | 33 |
| $100 | 179 |
| $120 | 255 |
| $150 | 897 |

- Below $50: 271 rows. $50–$99: 621 rows. Total below $100: 892 rows (0.06% of F/H/T rows).
- Rows with rent of $3,000+ : 3,602 (0.24% of F/H/T rows)
- Rows with rent of $5,000+ : 693 (0.05% of F/H/T rows)

**Findings:**
- Counts stay low and flat from $50 to $90, then rise clearly from $100.
- A weekly rent under $100 for a whole flat, house or townhouse in NSW is very unlikely.
- Very high rents are rare. Even if all rents of $3,000+ were errors, they would be only 0.24% of rows, spread across many postcodes, so medians are barely affected.

**Action:**
- Remove rows with weekly rent below $100 (892 rows, 0.06%).
- One threshold is used for all three dwelling types, because the number of rows affected is very small.

### Check 10: High rents

**Question:** Are the very high rents plausible?

**Method:** List the 50 highest rents for F, H and T, with postcode, dwelling type and bedrooms, and judge each one.

**Result:**
- The maximum rent is exactly $10,000, and many rows sit at this value. This may be an input limit in the lodgement system.
- Some high rents look plausible: e.g. 3–5 bedroom houses in Vaucluse (2030), Bellevue Hill (2023) and Mosman (2088) at $9,000–$10,000.
- Some look like errors: e.g. a 1-bedroom flat in Newtown (2042) at $8,675, possibly $867.50 with a missing decimal point.
- Several rows with very high bedroom counts (17, 19, 20, 25) are already removed by the bedroom caps in Check 4b.

**Findings:**
- High rents cannot be reliably split into real and wrong using the available columns.
- A single cut-off (e.g. P99 across NSW) would remove genuine luxury rentals and underestimate rents in expensive suburbs.
- The analysis uses medians, which are barely affected by a small number of extreme values.

**Action:**
- No upper rent threshold. High rents are kept.
- The analysis must use medians, not averages.

### Check 11: Postcodes

**Question:** Are all postcodes 4 digits, and are they within the NSW range?

**Result:**
- All 1,643,058 postcodes have 4 characters.
- Min postcode: 2000. Max postcode: 2898. All values are within 2000–2999, and none contain letters.
- 52 rows have postcodes in the ACT range 2600–2618: 2611 (6), 2617 (3), 2618 (43). No rows fall in 2900–2920.

**Verification (Australia Post postcode search):**
- 2618 covers Hall (ACT) and Wallaroo and Springrange (NSW).
- 2611 covers several ACT suburbs and Bimberi, Brindabella, Cooleman and Uriarra (NSW).
- 2617 covers ACT suburbs only (e.g. Belconnen, Bruce, Kaleen).
- NSW Fair Trading holds bonds for NSW residential tenancies, so rows in this dataset should be NSW properties.

**Findings:**
- Postcode format is clean.
- Rows with 2611 and 2618 are most likely NSW properties in border areas that share a postcode with the ACT.
- Rows with 2617 cannot be NSW properties and are likely data entry errors.

**Action:**
- Keep 2611 and 2618 (49 rows).
- Remove 2617 (3 rows).

### Check 12: Identical rows

**Question:** How many rows are exact copies of another row (all 5 columns the same)?

**Method:** GROUP BY all 5 columns, keep groups with HAVING COUNT(*) > 1.

**Result:**
- 66,052 combinations appear more than once, covering 163,712 rows.
- Extra identical rows (each group minus 1): 97,660 (5.9% of all rows).
- Of these, about 70,000 are F, H or T rows; the rest are O or U.
- Most groups (54,450) appear exactly twice.
- The largest groups are dwelling type O near universities and in the CBD
  (e.g. 145 identical rows in Kingsford 2032), and new apartment buildings
  (e.g. 60 identical 1-bedroom flats in Redfern 2016 on the same day).

**Findings:**
- The data has no address or unit number, so real duplicate entries cannot be
  told apart from separate leases in the same building.
- Large groups look like student accommodation and new buildings leasing many
  similar units on the same day.
- Many identical rows will be removed by other cleaning rules
  (dwelling type O/U in Check 3, rent below $100 in Check 9).

**Action:** Keep identical rows (no rows removed).

### Check 13: Sample size (2025)

**Question:** How many postcode × dwelling type × bedroom combinations in 2025 have at least 30 lodgements, and what share of rows do they cover?

**Method:** Count rows per combination for 2025, F/H/T only.

**Result:**
- 6,684 combinations, 297,147 rows.
- 1,749 combinations (26%) have 30 or more rows. They cover 261,186 rows (87.9%).
- 3,568 combinations have fewer than 10 rows; 1,208 have only 1 row.
- Largest: 2017 F 2-bed (3,383 rows), 2016 F 1-bed (2,492), 2000 F 1-bed (2,344).

**Findings:**
- Lodgements are highly concentrated in popular areas and common dwelling sizes.
- Only a quarter of combinations meet the 30-row threshold, but they hold
  almost 90% of the data.
- Counts are based on raw data and will fall slightly after cleaning.

**Action:**
- Report a median only when a combination has at least 30 rows.
- Combinations below 30 rows are shown as "insufficient data" (not removed from the clean table).