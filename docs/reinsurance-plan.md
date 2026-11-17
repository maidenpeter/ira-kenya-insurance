# Reinsurance flows: plan and data checks

Module 3 of ira-kenya-insurance. The question: how much risk do Kenyan general insurers pass to reinsurers, which classes and which insurers depend on it most, and how do Kenya's own reinsurers fare on what they accept?

Everything below was checked against `ira-kenya-data/data/processed/` before any output was written. Figures are KSh thousands, fourth quarter, year to date, full years 2018 to 2025.

## Step 1: what the data says

### Claims are net of reinsurance; no gross claims exist

- The class tables' `claims_incurred`, summed over classes, equals the revenue account's `incurred_claims` ("Net incurred claims" in IRA's revenue account) for 337 of 337 company-years, insurers and reinsurers, to within KSh 5,000.
- IRA's sheet titles say only "claims paid" and "claims incurred". `claims_paid` is net too. Pooled over 2018 to 2025, paid claims are 80% to 103% of net incurred claims in every class except personal accident (146%). In aviation, where 98% of the premium is ceded, paid claims are 96% of net incurred claims. Gross paid claims would be many times the net figure there.
- No table, line or file in ira-kenya-data carries gross claims.

So recoveries cannot be measured and question 6 is dropped. The page says so in its own section.

### Gross premium and premium ceded reconcile exactly

- `gross_premium` equals `gross_direct_premium + inward_premium` for 4,634 of 4,634 company-class-years from 2018, to within KSh 5,000. The total gap is zero.
- `gross_premium - net_premium`, summed over classes, equals the revenue account's `outward_reinsurance` for 298 of 298 insurer-years and 39 of 39 reinsurer-years, to within KSh 5,000. That is IRA's rounding, so 5 (KSh thousands) is the documented tolerance.
- The class sums also equal the revenue account's gross premium (direct plus inward) and net premium written for every company-year.

### IFRS 17

- `reporting_basis` switches from IFRS 4 to IFRS 17 at **Q1 2024**, not 2023. The switch applies to the profit and loss account and the balance sheet only.
- The revenue account keeps the same lines in every year (gross direct, inward, outward, net premium written, reserves, earned premium, claims, commissions, expenses), and its identities hold in every year. The class tables keep the same tables.
- Insurer by insurer, the moves across the switch are no larger than in other years:

| Change into | Insurers in both years | Median change in cession rate | Mean absolute change |
|---|---|---|---|
| 2019 | 35 | +0.4 points | 4.7 points |
| 2020 | 33 | +0.1 | 3.7 |
| 2021 | 34 | +0.4 | 3.4 |
| 2022 | 31 | -0.6 | 4.6 |
| 2023 | 31 | +1.3 | 5.1 |
| 2024 (IFRS 17 returns) | 29 | -0.1 | 5.5 |
| 2025 | 29 | -0.6 | 4.9 |

- **2022 against 2023, as the brief asked.** This is the year the standard took effect for annual accounts. The market cession rate rose 3.5 points, from 28.9% to 32.3%: 2.5 points from insurers ceding more within classes and 1.0 from the class mix. Medical contributed 1.6 points; medical's own cession rate went from 17.3% to 22.0%. By insurer, Britam General ceded KSh 3.5bn more (+13.7 points). MUA (+30.0 points), AAR (+11.6) and Madison (+10.9) also rose. Kenya Orient fell 12.1 points. These are moves within books on unchanged definitions, not a break in the series.

**Treatment.** No definitional break, so the market line runs through the switch. The switch is marked on the time chart at Q1 2024, with the year-on-year comparison in its takeaway.

### The reinsurer segment

| Reinsurer | Full years in the data |
|---|---|
| Kenya Re | 2016, 2018 to 2025 |
| Continental Re | 2016, 2018 to 2025 |
| East Africa Re | 2016, 2018 to 2025 |
| Ghana Re (Kenya) | 2018 to 2025 |
| WAICA Re Kenya | 2019 to 2025 |

None disappears. 2017 is missing for everyone, because IRA has no Q4 2017 workbook online. Continental Re filed its 2021 accepted premium as gross direct premium, with zero inward premium. So a reinsurer's accepted premium is taken as gross direct plus inward.

### Merged companies

- Saham's Q4 2021 row and Allianz Kenya's Q4 2022 row are all zeros: listed, not filed. Sanlam General has no Q4 2025 row.
- With all-zero returns dropped, as in module 1, every merged company is counted once in each year. A test checks this against `reference/entries_exits.csv`.
- The absorbing insurer's full year includes the absorbed book's earlier quarters (the `merger_step` flags). Full-year figures are therefore right; single quarters are not used.

### Quality flags

The only fourth-quarter error flag from 2018 is Intra-Africa Q4 2024 (`premium_reversal`): its Q3 year-to-date premium was too high, not its Q4. Full-year figures are used as published, as in modules 1 and 2. The flags are carried in `reinsurance_insurer_retention.csv`.

### Something the brief should know about the data repo

ira-kenya-data tracks its processed panels in git: `data/processed/*.csv`, including the 211,785-row class table, and `explorer/explorer_data.json`. They are public on GitHub now. That contradicts "Marion does not release her IRA data files, raw or cleaned". This module adds only small derived outputs, but the existing files are Marion's call. Nothing was removed.

## Questions shipped

1. **Cession by class and year.** Shipped. 2025: motor 3.2%, medical 21.2%, fire industrial 78.9%, aviation 99.3%, all classes 29.3%. The expected pattern holds. Medical (29.7%) and fire industrial (27.5%) together make up 57% of all premium ceded.
2. **Who depends on reinsurance.** Shipped. Retention against size, every insurer writing at least KSh 0.5bn, each year.
   - There is no size gradient. In 2025 the median retention was 80% under KSh 3bn, 65% from KSh 3bn to 10bn and 75% over KSh 10bn. Rank correlation ran from -0.29 to -0.13 across the years.
   - **The link to the fragmentation finding is dropped.** Small insurers keep the most of their premium, so heavier cession does not explain their higher expense ratios, and those ratios are on gross premium anyway, so retention does not distort them. The numbers do not support a sentence linking the two.
3. **Does it move.** Shipped.
   - Each insurer's retention in 2018 and 2025: 27 insurers, 17 lower and 10 higher, median -3.5 points.
   - The market cession rate by year, with the IFRS 17 switch marked.
4. **How much could stay with local reinsurers.** Shipped as an upper bound, labelled as one. The local reinsurers' accepted premium was KSh 32.4bn in 2025 against KSh 66.6bn ceded, so at most 49% (75% at its peak in 2022).
5. **How Kenya's local reinsurers perform.** Shipped:
   - Premium, loss, commission, expense and combined ratios and underwriting result, by reinsurer, class and year, and for all five together.
   - Their underwriting profit together: 2020 to 2024. Losses: 2018, 2019 and 2025.
   - The commission ratio rose from 23.2% to 32.0% while the loss ratio fell from 65.1% to 58.0%.
6. **Recoveries.** Dropped: no gross claims exist (above). The page explains why.
7. **Tie-in to the Cedant Scorecard.** Shipped as one table and one paragraph.
   - **The scorecard is partly circular here.** Retention is one of its ten metrics (5 of 100 points), so the table also shows the score with retention taken out. It re-weights the business-profile pillar to scale and diversification, using the scorecard's own weights, read from its code.
   - **Result:** insurers keeping under half their premium had a median score of 69.7 without retention, against 53.5 for those keeping 70% or more (rank correlation -0.35). Even so, 31% of their years were graded D or E.
   - The page says it is a correlation, not a cause.

## Metric definitions and sources

| Metric | Definition | File |
|---|---|---|
| Gross premium | class table gross premium income (gross direct + inward) | `general_by_class_panel.csv`, table `gross_premium` |
| Net premium | class table net premium income | `general_by_class_panel.csv`, table `net_premium` |
| Premium ceded | gross premium - net premium | the two above |
| Cession rate | ceded / gross premium | |
| Retention | net / gross premium | |
| Outward reinsurance (check) | revenue account outward reinsurance | `general_revenue_panel.csv`, line `outward_reinsurance` |
| Accepted premium (reinsurers) | gross direct + inward premium | `general_revenue_panel.csv` and the class table's `gross_premium` |
| Loss, commission, expense, combined ratio | claims incurred, net commissions, management expenses over net earned premium, as module 1 | `general_by_class_panel.csv` |
| Return basis | IFRS 4 or IFRS 17 | `general_profit_loss.csv`, `reporting_basis` |
| Scorecard score and grade | as published | `ira-kenya-reinsurance/output/cedant_scorecard.csv` |

Motor Commercial PSV is folded into Motor Commercial, as in module 1. Insurers include micro insurers, as module 1 counts the market.

## Outputs

All in `output/`, small and derived; no panel or row-level table is copied.

| File | Level | Columns |
|---|---|---|
| `reinsurance_class_cession.csv` | class x year, plus All classes | insurers, gross, net and ceded premium, cession rate, share of ceded, outside_0_1 |
| `reinsurance_insurer_retention.csv` | insurer x year | gross, net, ceded premium, cession rate, retention, outward reinsurance, reconcile gap, size band, compared, quality flags, note |
| `reinsurance_size_gradient.csv` | size band x year | insurers, median and pooled retention, gross premium, rank correlation, band edges, threshold |
| `reinsurance_retention_change.csv` | insurer | gross premium and retention 2018 and 2025, change in points, absorbed companies |
| `reinsurance_market.csv` | year | gross, net, ceded premium, cession rate, basis, insurers in both years, median and mean absolute change, insurers' inward premium, local reinsurers, accepted premium, upper bound |
| `reinsurance_reinsurer_results.csv` | reinsurer x class x year, plus totals | accepted, net, earned premium, claims, commissions, expenses, result, ratios, filed_as_direct |
| `reinsurance_scorecard_link.csv` | retention group | insurer-years, insurers, medians, D or E share, rank correlations, scorecard weights |

`build.py` writes them; same inputs give byte-identical files. `build_page.py` builds the page and writes the README section from these files only.

## Checks (`tests/test_reinsurance.py`)

- Cession rate between 0 and 1 for every class and year with positive premium. An insurer outside 0 to 1 is kept with a note, not clipped; there are none.
- Classes add to the insurer totals and the market; shares of ceded premium add to one.
- Premium ceded reconciles to outward reinsurance for every insurer-year within KSh 5,000.
- Reinsurer results: earned premium less claims, commissions and expenses equals the result within KSh 5,000, as in module 1. Classes add to each reinsurer, and reinsurers add to the segment.
- Merged companies are counted once in each year.
- The upper bound is the accepted premium over the premium ceded.
- The README section and the page's data equal a fresh recomputation from the outputs. The words that state a direction ("motor keeps almost all", "the middle band keeps the least") are asserted against the data.
- Everything the module writes is plain ASCII.
- Outputs are byte-identical on a second run, and equal to the committed files. This one needs the data repos and is skipped on CI without them.

## Open items for Marion

- **Recoveries.** No gross claims were found, so recoveries are not on the page; a section says why.
- **IFRS 17.** The returns switched in Q1 2024, not 2023. The premium lines did not change, so the series is unbroken and the switch is marked on the chart.
- **Named findings to read before it goes live:**
  - **WAICA Re.** Its combined ratio has been under 100% every year since 2020; it lost money only in 2019, its first full year. Its premium grew from KSh 0.34bn (2019) to KSh 5.95bn (2025).
  - **Kenya Re.** It lost KSh 1.58bn in 2025 (combined ratio 114.1%) and KSh 2.40bn in 2019.
  - **Continental Re.** It lost KSh 1.36bn in 2024 (combined ratio 139.8%).
  - **East Africa Re.** It made an underwriting profit in every year it filed.
  - **Lowest retention, 2025:** Bupa Global keeps 9% of its premium, Occidental 44%, Mayfair 45%.
  - **Largest changes since 2018:** Occidental 75% to 44%, NCBA 23% to 51%.
  - **MUA** appears like every other insurer: +9.8 points since 2018, counted with Saham.
- **Published data files.** ira-kenya-data publishes its processed panels (above).
