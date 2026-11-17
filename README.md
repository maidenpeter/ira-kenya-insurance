# ira-kenya-insurance

Kenya's general insurance market from the insurer's side: where the money is lost, who carries the loss and what it would take to close the gap. Built from the Insurance Regulatory Authority's quarterly returns, full years 2018 to 2025, using the tables in [ira-kenya-data](https://github.com/maidenpeter/ira-kenya-data).

Three modules so far: where the money is lost (the Loss Map), who holds the market (Market Structure) and what is passed on to reinsurers (Reinsurance Flows). The IFRS 17 transition follows.

## Where the money is lost

From 2018 to 2025 Kenya's general insurers lost KSh 33.1bn on underwriting. Motor alone lost KSh 52.6bn. Every other class together made KSh 19.6bn, two thirds of it from workmen's compensation.

| Class, 2018 to 2025 | Underwriting result (KSh bn) |
|---|---|
| Motor private | -29.3 |
| Motor commercial, including PSV | -23.4 |
| Medical | -2.5 |
| Engineering | -0.9 |
| Aviation | -0.7 |
| Fire, theft, liability, personal accident and miscellaneous (six classes) | +7.0 |
| Marine | +3.5 |
| Workmen's compensation | +13.1 |
| **All classes** | **-33.1** |

In 2025 motor was 27% of gross premium, 37% of earned premium and 40% of claims. It lost money in every one of the eight years, and in every year it lost more than the whole market did.

## What premiums would have to do

On 2023 to 2025 experience, using the loss ratio method of ratemaking:

| | Combined ratio | Premium change to break even | Counting investment income |
|---|---|---|---|
| Motor commercial | 114.1% | +15.6% | +2.2% |
| Motor private | 111.2% | +12.3% | -0.7% |
| Medical | 101.1% | +1.2% | -10.3% |
| All classes | 104.1% | +4.4% | -7.4% |

The investment income version credits every class with the market's investment income, 11.8% of earned premium. Much of that is earned on shareholders' capital rather than on premium, so it is the most generous reading, and motor commercial still falls short. Of 26 insurers with a motor book large enough to measure, 24 need a rate increase to break even and 8 need more than 20%.

This matters now. In September 2024 the Court of Appeal ruled that IRA has the power to regulate premium rates, but struck down its 2009 motor minimum rate guidelines because IRA had not shown that price setting was the right tool. Any new attempt will need evidence of this kind.

## Who carries the motor loss

Forty insurers wrote motor over the period. Only three made a meaningful profit on it: GA (KSh 0.12bn), Mayfair (KSh 0.40bn) and Trident (KSh 0.57bn). Ten insurers carry 62% of the loss.

## Motor results that are too good to be true

The market's loss ratio on all motor business, private and commercial together, ran between 65% and 81%. Ten insurers booked a year under 40%. Eight of those ten faced regulator action, negative equity or equity below IRA's minimum capital at some point since 2018, against 7 of the other 28 motor insurers (Fisher's exact test, p = 0.006; the gap holds at 35%, 45% and 50% thresholds). For seven of the ten the trouble came in the same year or later.

The list includes Invesco's 11% in 2023, the year it was liquidated, and Trident's 13% and 30% in 2021 and 2022, the two years before it stopped filing returns. Trident's motor profit above sits on those two years. A motor book that looks far better than everyone else's is more often a reserving question than a pricing success.

## Small insurers pay far more to run

In 2025, insurers writing under KSh 3bn a year spent a median 34% of gross premium on management expenses. Those writing over KSh 10bn spent 15%. Across the market, each doubling of premium comes with about six points less expense (correlation -0.68, and between -0.63 and -0.81 in every year).

## Market structure: a crowded market

Kenya had 34 general insurers in 2025 sharing KSh 227.2bn of written premium. The largest, CIC General, held 9.1%. The Herfindahl-Hirschman index was 530, about half the 1,000 at which US competition authorities start to call a market moderately concentrated, and the same as 19 equal-sized insurers. The top spot has changed hands four times since 2016.

**Scale is arriving, slowly.** In 2020 two insurers wrote more than KSh 10bn a year and held 16% of the market. By 2025 seven did, holding 53%. The top ten's share rose from 59% to 65%. Part of the move past KSh 10bn is inflation (premium grew 8.4% a year from 2018), but the rising top ten share is not.

**What fragmentation costs.** Measured class for class against the five largest insurers' expense rates, everyone else spent KSh 23.9bn more on management expenses from 2018 to 2025. The market's underwriting loss over the same years was KSh 33.1bn. The gap is an order of magnitude, not a promise of savings, but it puts the cost of a divided market in the same range as the loss.

**The insurers losing ground are the ones losing money.** The ten insurers that grew slower than the market from 2018 to 2025 ran a median combined ratio of 112.0%, six of them above 110%. The seventeen that gained share ran a median of 103.2%. Cheap growth is not being rewarded; the insurers pricing below cost are shrinking.

**Who moved, 2020 to 2025 (pro forma for mergers).** GA (+1.5 points), Mayfair (+1.4), CIC (+1.3), AAR (+1.3) and APA (+1.3) gained most among established insurers; Bupa Global took 2.4% in its first year. Geminia (-1.7), Occidental (-1.4) and MUA with Saham (-1.2) lost most among insurers still writing.

**Medical is taking over the book.** Medical rose from 31% of gross premium in 2018 to 41% in 2025, while motor fell from 36% to 27%. Medical is the one large class that is concentrated: an HHI of 1,019, and three insurers (Jubilee Health, AAR and Old Mutual) write 44% of it.

**Who came and went.** Five insurers left through the regulator (Resolution, Xplico, Invesco, Trident, Corporate), three through mergers (Saham into MUA; Allianz Kenya and Sanlam General into what is now Sanlam Allianz General), and Jubilee split its general business in 2020. Star Discover arrived in 2023, and Definite, Equity General, Equity Health and Bupa Global in 2025.

<!-- reinsurance flows: written by src/reinsurance/build_page.py -->
## Reinsurance flows

From 2018 to 2025 Kenya's general insurers passed KSh 402.4bn of premium to reinsurers. In 2025 they ceded KSh 66.6bn, 29.3% of their gross premium; the rate has stayed between 28.2% (2018) and 32.3% (2023). Insurers IRA listed with an all-zero full-year return are left out of that year, and the page names them; the largest gap is in 2024, an insurer that wrote KSh 4.7bn in 2023.

**Where it goes out.** Motor keeps almost all of its premium (insurers cede 3.2% of it); aviation keeps almost none (99.3% ceded) and fire industrial cedes 78.9%. Medical and fire industrial together make up 57.2% of everything ceded in 2025: medical because it is the largest class, though only 21% of it is ceded, and fire industrial because most of it is.

**Who depends on it.** There is no simple size gradient. In 2025 insurers writing under KSh 3bn kept a median 80% of their premium, those over KSh 10bn 75%, and those in between the least, 65%. The rank correlation between retention and size ran from -0.29 to -0.13 across the years, a weak relationship.

**Does it move.** Of 27 insurers writing at least KSh 0.5bn in both 2018 and 2025, 17 keep less of their premium than they did and 10 keep more (median change -3.5 points). The largest rise in the market rate came in 2023 (+3.5 points). Insurers that filed in both years account for 3.0 points of it, and the rest reflects which insurers filed; medical, the largest class, went from ceding 17.3% to 22.0%. The returns moved to IFRS 17 statements in 2024 but kept their premium lines, and there is no systematic shift that year: among insurers writing at least KSh 0.5bn in both years, the median cession rate moved -0.1 points. The average size of their moves, 5.5 points in either direction, was the largest of the seven years, though close to 2023's 5.1; the series is treated as unbroken and the switch is marked.

**How much could go to the local reinsurers.** The five reinsurers that file IRA's returns accepted KSh 32.4bn of premium in 2025, so at most 49% of what Kenyan insurers ceded could have gone to them. It is an upper bound, not a measured flow: they also accept business from outside Kenya, and insurers also cede to reinsurers that do not file these returns (abroad, and the regional reinsurers that operate in Kenya under regional charters) and to each other.

**How the local reinsurers fare.** Together, Continental Re, East Africa Re, Ghana Re, Kenya Re and WAICA Re (from 2019) made an underwriting profit in every year from 2020 to 2024, and lost money in 2018, 2019 and 2025: a loss of KSh 0.94bn in 2025, a combined ratio of 103.5%. Their loss ratio fell from 65.1% in 2018 to 58.0% in 2025, 7.1 points, while their net commission (commission and brokerage paid, less commission received) rose from 23.2% to 32.0% of earned premium, 8.8 points. Over 2018 to 2025 fire industrial (31% of their premium) made KSh 8.7bn and medical (19%) lost KSh 8.5bn, a combined ratio of 120.9%.

**Recoveries.** IRA's class tables and revenue accounts carry claims net of reinsurance only, so what insurers recover from their reinsurers cannot be measured. Separately, the reinsurers' returns do not split their business by where it comes from, so their result on Kenyan cessions alone cannot be measured either.

**The Cedant Scorecard.** Insurers keeping under 50% of their premium had a median score of 69.7 on the scorecard's other measures, against 53.5 for those keeping 70% and over (rank correlation -0.35, 2018 to 2025). It is a correlation, not a cause, and the same group was also graded D or E most often: 31% of its insurer-years, against 12% (50% to 70%) and 25% (70% and over).
<!-- reinsurance flows end -->

## Claims settlement (analysis 2)

<!-- claims start -->
IRA publishes every insurer's claims movement each quarter: claims open at the start, claims reported, paid, declined and closed as no claim, and claims still open at the end. [ira-kenya-data](https://github.com/maidenpeter/ira-kenya-data) extracts the 32 quarterly workbooks IRA has published from Q1 2017 to Q1 2026, joins every printed name to a company and checks them 12,791 times. This module turns them into IRA's own payment ratio: claims paid in the quarter over the claims open in the quarter. It is the second analysis in the series, after the five pages above.

**Three speeds.** In an average quarter of 2025 general insurers paid 11.7% of the liability claims open to them (claims by third parties, most of them injury from motor accidents) and 60.1% of their non-liability claims (medical, own damage, property), and life insurers paid 78.7% of theirs. The median insurer paid 9.2%, 39.8% and 79.0%. Two medical insurers report most non-liability claims by number, which is why the market and the median differ there.

**The queue.** 125,141 liability claims were outstanding at the end of 2025, KSh 33.4bn by the insurers' own estimates: 7.2 quarters of payments at the 2025 pace of 17,448 a quarter. The count peaked at 150,062 in Q2 2024; by value the queue grew from KSh 29.7bn in Q4 2022, the first quarter IRA printed amounts.

**The five the regulator stepped into.** In the last four quarters each reported before the regulator acted, Invesco and Corporate paid liability claims at under half the median insurer's rate in all four, Xplico in three of four. Resolution, mainly a medical insurer, paid close to or above the median; Trident reported paying 4 to 7 times the median. Paying slowly is common: 12 of the 39 general insurers compared had four quarters running under half the median at some point since 2017, and 3 of them later came under the regulator.

**Caveats.** The returns are unaudited. A low payment ratio can reflect a book of slow claims as much as slow payment. 8 insurer-quarters print a negative count and are given no ratio; where an insurer's own claims do not add up from one quarter to the next, the return is kept as printed and counted. This is a screening view, not a credit opinion.
<!-- claims end -->

## See it

`page/kenya-insurance-loss-map.html` opens in any browser: the class map year by year, the rate gap by class and by insurer, the motor loss by company, the low loss ratio test and the expense curve for any year.

`page/kenya-insurance-market-structure.html`: every insurer's share, concentration over time, the fragmentation cost, growth against results, share shifts, the class mix and a timeline of entries and exits.

`page/kenya-insurance-reinsurance-flows.html`: cession by class and year, retention against size for every insurer, the change in each insurer's retention, the local reinsurers' capacity against what is ceded, their results by company and class, and retention against the Cedant Scorecard.

`page/kenya-claims-settlement.html` (analysis 2): the liability claims queue quarter by quarter, the median insurer's payment ratio for liability, non-liability and life claims, every insurer's payment ratio for the last full year, the five regulator cases against the median, and what the checks found.

## Files

| File | What it holds |
|---|---|
| `output/class_market.csv` | Market by class and year: premium, earned premium, claims, commissions, expenses, result and ratios |
| `output/class_company.csv` | The same for every insurer, class and year |
| `output/rate_gap.csv` | Premium change each class needs, 2023 to 2025 |
| `output/rate_gap_company.csv` | The same for each insurer's motor and medical book |
| `output/loss_concentration.csv` | Each insurer's cumulative motor result and share of the loss |
| `output/low_motor_loss_ratio.csv` | Every insurer-year with a motor loss ratio under 40%, and what happened to the company |
| `output/low_motor_loss_ratio_test.csv` | The comparison with every other motor insurer at four thresholds |
| `output/expense_scale.csv` | Management expenses against size, every insurer and year |
| `output/structure_market.csv` | Insurers, premium, HHI, top 5 and top 10 share, leader and equivalent number of insurers, by year |
| `output/structure_shares.csv` | Every insurer's written premium, share and rank each year |
| `output/structure_share_shift.csv` | Share change 2020 to 2025, pro forma for mergers |
| `output/structure_class_mix.csv` | Each class's share of the market and its own concentration |
| `output/structure_growth_results.csv` | Premium growth 2018 to 2025 against combined ratio |
| `output/structure_fragmentation.csv` | Extra management expense outside the five largest, class for class, against the underwriting result |
| `output/reinsurance_class_cession.csv` | Insurers by class and year: gross, net and ceded premium, cession rate and each class's share of all premium ceded |
| `output/reinsurance_insurer_retention.csv` | Every insurer and year: gross, net and ceded premium, retention, size band, and the revenue account's outward reinsurance it reconciles to |
| `output/reinsurance_size_gradient.csv` | Retention by size band each year, and its rank correlation with size |
| `output/reinsurance_retention_change.csv` | Each insurer's retention in the first and last year |
| `output/reinsurance_market.csv` | Per year: premium ceded, cession rate, the return basis, how far insurers' rates moved, and the local reinsurers' accepted premium against it |
| `output/reinsurance_reinsurer_results.csv` | Each local reinsurer, and all of them together, by class and year: premium accepted, claims, commissions, expenses, result and ratios |
| `output/reinsurance_scorecard_link.csv` | Insurers grouped by retention against the Cedant Scorecard's score, with and without its retention metric |
| `output/claims_market.csv` | Per quarter and business (general liability, general non-liability, life): claims open, paid, declined, closed and outstanding, the market's and the median insurer's payment ratio, and amounts from Q4 2022 |
| `output/claims_insurer_year.csv` | Every insurer, business and year: claims open and paid over the year's quarters, the pooled payment ratio, claims outstanding at the year's last quarter, and whether it is compared |
| `output/claims_regulator.csv` | The five regulator cases: liability payment ratio in each of the last four quarters before the action, against the median |
| `output/claims_runs.csv` | Every run of four published quarters in which a general insurer paid liability claims at under half the median insurer's rate |
| `output/claims_checks_summary.csv` | ira-kenya-data's checks on the claims tables, counted by result |
| `reference/regulator_actions.csv` | The five regulator interventions since 2022, with sources |
| `reference/entries_exits.csv` | Every entry, exit, merger and split, with sources |

## Running it

Clone next to [ira-kenya-data](https://github.com/maidenpeter/ira-kenya-data) (or set `IRA_DATA_DIR`). The reinsurance module also reads the Cedant Scorecard, so clone [ira-kenya-reinsurance](https://github.com/maidenpeter/ira-kenya-reinsurance) beside it too (or set `IRA_REINSURANCE_DIR`). The modules read ira-kenya-data's tables, which it builds locally from IRA's files with `./run_all.sh`; the outputs here are committed, so the tests and pages work without them. Then:

```
pip install -r requirements.txt
./run.sh
pytest tests
```

The tests check that every class result adds up, that classes add to the market, that the class totals match IRA's own PDF industry releases for 2020 to 2024, that market premium matches ira-kenya-data, that shares and pro forma shares add to one, and the rate, test, concentration and fragmentation arithmetic. For reinsurance flows they check that every cession rate lies between 0 and 1, that classes add to insurers and to the market, that premium ceded reconciles to each insurer's outward reinsurance, that the reinsurers' results add up the same way, that merged companies are counted once, and that the README's figures match a fresh recomputation. GitHub Actions runs them on every push. The test that rebuilds the outputs and checks they are byte-identical runs where ira-kenya-data and ira-kenya-reinsurance are present.

## Caveats

- IRA's quarterly returns are unaudited. Class results (earned premium, claims, commissions, expenses) are net of reinsurance, as IRA publishes them; reinsurance flows uses gross and net written premium, which IRA publishes both of.
- No gross claims are published, so reinsurance recoveries cannot be measured. The local reinsurers are the companies that file IRA's returns as reinsurers. Their figures cover all the business they accept, from Kenya and abroad, so their share of Kenyan cessions is an upper bound on what they could have taken, not on what stayed in Kenya. Their results are not their result on Kenyan business alone.
- An insurer IRA listed without a full-year return is left out of that year's totals; reinsurance flows names them, year by year.
- The rate change is an indication of the size of the gap, not a filed rate: no loss trend, no development beyond what insurers booked, no charge for capital. The true need is higher.
- Motor Commercial includes PSV. Insurers move business between the two; in Q4 2025 Madison moved KSh 1.6bn of earned premium from PSV to Motor Commercial, which left PSV with negative earned premium for the year.
- A low loss ratio is a warning, not proof. It can reflect a good book, heavy reinsurance or thin reserves. The test compares ten insurers with twenty-eight.
- 2016 is left out because IRA's 2016 class tables have no earned premium or expense split, and IRA has no year-end 2017 workbook online.
- Premium and shares are nominal. The fragmentation cost compares each insurer with the five largest class for class; part of any gap may be the cost of serving smaller clients, so treat it as a size, not a saving.
- Everything here is public IRA data. Nothing comes from inside any insurer.

## Sources

- Insurance Regulatory Authority, Kenya: quarterly industry statistics, via ira-kenya-data
- Werner and Modlin, Basic Ratemaking, Casualty Actuarial Society, 2016: https://www.casact.org/sites/default/files/old/studynotes_werner_modlin_ratemaking.pdf
- Court of Appeal ruling on IRA's motor underwriting guidelines, 20 September 2024 (EY tax alert): https://www.ey.com/en_gl/technical/tax-alerts/kenyan-court-of-appeal-declares-insurance-regulatory-authoritys-powers-include-price-regulation
- Regulator actions and entries and exits: see `reference/regulator_actions.csv` and `reference/entries_exits.csv`
- US Department of Justice, Herfindahl-Hirschman Index (2023 Merger Guidelines thresholds): https://www.justice.gov/atr/herfindahl-hirschman-index

Marion Peter
