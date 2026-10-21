# Analysis Findings

Results of the five questions in `sql/06_analysis.sql`.

- **Data:** `clean_bond_lodgements` (1,510,130 new bonds, NSW, 2021–2025),
  `dim_postcode` (923 NSW postcodes) and `vw_rent_benchmark`.
- **Measure:** median weekly rent. I use the median, not the average, because a few very
  high rents can pull the average up (see Check 10 in `data_quality_log.md`).
- **Minimum sample:** when results are by postcode, I only show groups with at least
  30 lodgements (see Check 13).
- Dollar amounts are rounded to the nearest dollar.

Each question has two parts:
- **What the data shows** – facts from the query results.
- **Possible reasons** – my ideas to explain the results. These are not tested with this data.

---

## Q1. How much did median rents change from 2021 to 2025, by dwelling type?

**Method:** median weekly rent for each dwelling type and year. Then the change from 2021 to 2025.

| Dwelling type | 2021 | 2022 | 2023 | 2024 | 2025 | Change |
|---|---|---|---|---|---|---|
| Flat / Unit | $460 | $520 | $620 | $680 | $700 | **+52.2%** |
| Terrace / Townhouse / Semi-detached | $520 | $580 | $630 | $680 | $720 | +38.5% |
| House | $510 | $560 | $600 | $650 | $680 | +33.3% |

**What the data shows:**
- Rents went up for all three dwelling types every year.
- Flats went up the most (+52%). Houses went up the least (+33%).
- In 2021, flats were the cheapest type ($460). In 2025, flats cost more than houses ($700 vs $680).
- The biggest one-year rise for flats was from 2022 to 2023 (+$100).

**Note:** these medians mix all bedroom sizes (Studio to 4+). If more large flats were rented
in 2025 than in 2021, the median goes up even if prices did not change. Q2 only looks at
2-bedroom flats to avoid this.

---

## Q2. Which postcodes had the biggest rent rise for 2-bedroom flats from 2021 to 2025?

**Method:** median rent for 2-bedroom flats in each postcode, in 2021 and 2025.
Only postcodes with at least 30 lodgements in **both** years. Suburb names come from `dim_postcode`.

| Rank | Postcode | Suburbs | 2021 | 2025 | Change |
|---|---|---|---|---|---|
| 1 | 2032 | Daceyville, Kingsford | $450 | $850 | **+88.9%** |
| 2 | 2008 | Chippendale, Darlington, Golden Grove | $650 | $1,198 | +84.2% |
| 3 | 2007 | Broadway, Ultimo | $580 | $1,050 | +81.0% |
| 4 | 2017 | Waterloo, Waterloo DC, Zetland | $650 | $1,150 | +76.9% |
| 5 | 2000 | Barangaroo, Darling Harbour, Dawes Point, Haymarket, Millers Point, … | $750 | $1,319 | +75.9% |
| 6 | 2036 | Chifley, Eastgardens, Hillsdale, La Perouse, Little Bay, … | $600 | $1,050 | +75.0% |
| 7 | 2033 | Kensington | $495 | $850 | +71.7% |
| 8 | 2195 | Lakemba, Lakemba DC, Wiley Park | $300 | $510 | +70.0% |
| 9 | 2018 | Eastlakes, Rosebery | $590 | $1,000 | +69.5% |
| 10 | 2218 | Allawah, Carlton | $400 | $670 | +67.5% |

**What the data shows:**
- In Kingsford (2032), the median rent almost doubled: $450 → $850.
- Six of the top ten postcodes are near a university:
  - near UNSW: 2032, 2033, 2036, 2018
  - near UTS and the University of Sydney: 2007, 2008
- Lakemba (2195) is not near a university. It started from a low rent ($300), so the
  percentage rise is large.

**Possible reasons:**
- In 2021, international students could not come to Australia because of COVID border rules.
  Areas near universities may have had fewer renters, so rents were low. When students came
  back, rents in these areas may have risen faster.

---

## Q3. Did rents grow differently in Greater Sydney and the rest of NSW?

**Method:** each lodgement gets a label from the ABS region (SA4) of its postcode.
Greater Sydney = all regions that start with "Sydney -" plus Central Coast (ABS definition).
Everything else = Rest of NSW. Median rent for 2021 and 2025.

| Area | Lodgements (2021–2025) | Share |
|---|---|---|
| Greater Sydney | 1,109,125 | 73.4% |
| Rest of NSW | 401,005 | 26.6% |

| Dwelling type | Area | 2021 | 2025 | Change |
|---|---|---|---|---|
| Flat / Unit | Greater Sydney | $480 | $750 | **+56.3%** |
| Flat / Unit | Rest of NSW | $350 | $450 | +28.6% |
| House | Greater Sydney | $580 | $760 | +31.0% |
| House | Rest of NSW | $450 | $600 | **+33.3%** |
| Terrace / Townhouse / Semi-detached | Greater Sydney | $575 | $800 | +39.1% |
| Terrace / Townhouse / Semi-detached | Rest of NSW | $470 | $620 | +31.9% |

**What the data shows:**
- About three in four lodgements are in Greater Sydney.
- Flats in Greater Sydney went up about twice as much as flats in the rest of NSW (+56% vs +29%).
- For houses, the rest of NSW went up a little more than Greater Sydney (+33% vs +31%).
- So the big rise in flat rents in Q1 comes mostly from Sydney.

**Possible reasons:**
- During and after COVID, some people moved out of the city. This may explain why
  house rents outside Sydney rose a little faster.

**Notes:**
- The 13 lodgements with no postcode match are counted in Rest of NSW. This is too few to
  change the medians.
- ABS puts some NSW border postcodes in ACT, Queensland or Victoria regions. They are still
  counted in Rest of NSW, which is correct.

---

## Q4. Where is the 2025 rent range widest for 2-bedroom flats?

**Method:** from `vw_rent_benchmark` (2025), 2-bedroom flats with at least 30 lodgements.
- Range = P75 − P25 (the middle half of rents).
- Range / median = range divided by the median. This makes cheap and expensive areas fair to compare.

| Rank | Postcode | Suburbs | Lodgements | P25 | Median | P75 | Range | Range / median |
|---|---|---|---|---|---|---|---|---|
| 1 | 2627 | Bullocks Flat, Burrungubugge, Crackenback, Creel Bay, … | 65 | $500 | $550 | $850 | $350 | **63.6%** |
| 2 | 2163 | Carramar, Lansdowne, Villawood | 98 | $420 | $455 | $650 | $230 | 50.5% |
| 3 | 2068 | Castlecrag, Middle Cove, North Willoughby, Willoughby, … | 141 | $700 | $820 | $1,100 | $400 | 48.8% |
| 4 | 2065 | Crows Nest, Gore Hill, Greenwich, Naremburn, … | 1,036 | $800 | $950 | $1,193 | $393 | 41.3% |
| 5 | 2265 | Cooranbong, Martinsville | 36 | $270 | $440 | $450 | $180 | 40.9% |
| 6 | 2039 | Rozelle | 99 | $780 | $985 | $1,150 | $370 | 37.6% |
| 7 | 2570 | Belimbla Park, Bickley Vale, Brownlow Hill, … | 67 | $470 | $500 | $650 | $180 | 36.0% |
| 8 | 2204 | Marrickville, Marrickville Metro, Marrickville South | 640 | $650 | $750 | $920 | $270 | 36.0% |
| 9 | 2061 | Kirribilli, Milsons Point | 253 | $875 | $1,050 | $1,250 | $375 | 35.7% |
| 10 | 2008 | Chippendale, Darlington, Golden Grove | 394 | $925 | $1,198 | $1,350 | $425 | 35.5% |

**What the data shows:**
- In these postcodes, 2-bedroom flats are rented at very different prices.
- Postcode 2627 has the widest range: the middle half of rents goes from $500 to $850.
- In Cooranbong (2265), most rents are close to the median ($440–$450), but a quarter are
  $270 or less.
- Several postcodes are in the inner west and lower North Shore of Sydney (2068, 2065, 2061, 2039).

**Possible reasons:**
- Postcode 2627 is in the Snowy Mountains ski area. Some flats may be rented for the ski season
  or with furniture.
- In harbour suburbs like Kirribilli, flats with water views and older flats may be in the
  same postcode.

**Why this matters:** in these areas, a renter can easily pay too much. It is most useful to
check an asking rent against the P25–P75 range here.

---

## Q5. Is there a busy season?

**Method:** number of lodgements and median rent by month. 2-bedroom flats, all five years together.

| Month | Lodgements | Median rent |
|---|---|---|
| January | 40,057 | $590 |
| **February** | **42,748** | $600 |
| March | 39,700 | $575 |
| April | 34,010 | $580 |
| May | 37,352 | $600 |
| June | 36,742 | $600 |
| July | 39,725 | $620 |
| August | 38,706 | $630 |
| September | 36,609 | $620 |
| October | 34,373 | $620 |
| November | 34,542 | $620 |
| **December** | **33,061** | $620 |

**What the data shows:**
- February is the busiest month (42,748 lodgements).
- December is the quietest month (33,061). February has about 29% more lodgements than December.
- January and March are also busy.
- Median rent is higher from July to December ($620–$630) than from January to June ($575–$600).

**Possible reasons:**
- February and March are the start of the university year and the end of summer holidays,
  when many people move.

**Note:** the higher median in the second half of the year is probably **not** a seasonal effect.
Rents went up every year from 2021 to 2025, so later months in each year are naturally higher.
To check for a real seasonal effect, months would need to be compared within the same year.

---

## Summary

1. From 2021 to 2025, rents went up for all dwelling types. Flats went up the most (+52%).
2. The rise in flat rents was mostly in Greater Sydney (+56%, vs +29% in the rest of NSW).
3. Among 2-bedroom flats, six of the ten biggest rises were in postcodes near universities.
   Kingsford (2032) almost doubled.
4. For houses, the rest of NSW went up a little more than Greater Sydney.
5. Rents for similar flats vary most in 2627 (Snowy Mountains) and some inner Sydney postcodes.
   This is where checking the benchmark helps most.
6. February is the busiest month for new leases.