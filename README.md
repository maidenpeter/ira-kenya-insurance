# ira-kenya-insurance

Kenya's general insurance market from the insurer's side: where the money is lost, who carries the loss and what it would take to close the gap. Built from the Insurance Regulatory Authority's quarterly returns, full years 2018 to 2025, using the tables in [ira-kenya-data](https://github.com/maidenpeter/ira-kenya-data).

This is the first of four modules. Market structure, the IFRS 17 transition and reinsurance flows follow.

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

The market's motor loss ratio ran between 65% and 81%. Ten insurers booked a year under 40%. Eight of those ten faced regulator action, negative equity or equity below IRA's minimum capital at some point since 2018, against 7 of the other 28 motor insurers (Fisher's exact test, p = 0.006; the gap holds at 35%, 45% and 50% thresholds). For seven of the ten the trouble came in the same year or later.

The list includes Invesco's 11% in 2023, the year it was liquidated, and Trident's 13% and 31% in 2021 and 2022, the two years before it stopped filing returns. Trident's motor profit above sits on those two years. A motor book that looks far better than everyone else's is more often a reserving question than a pricing success.

## Small insurers pay far more to run

In 2025, insurers writing under KSh 3bn a year spent a median 34% of gross premium on management expenses. Those writing over KSh 10bn spent 15%. Across the market, each doubling of premium comes with about six points less expense (correlation -0.68, and between -0.63 and -0.81 in every year).

## See it

`page/kenya-insurance-loss-map.html` opens in any browser: the class map year by year, the rate gap by class and by insurer, the motor loss by company, the low loss ratio test and the expense curve for any year.

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
| `reference/regulator_actions.csv` | The five regulator interventions since 2022, with sources |

## Running it

Clone next to [ira-kenya-data](https://github.com/maidenpeter/ira-kenya-data) (or set `IRA_DATA_DIR`), then:

```
pip install -r requirements.txt
./run.sh
pytest tests
```

The tests check that every class result adds up, that classes add to the market, that the class totals match IRA's own PDF industry releases for 2020 to 2024, and the rate and test arithmetic. GitHub Actions runs them on every push.

## Caveats

- IRA's quarterly returns are unaudited. Class figures are net of reinsurance, as IRA publishes them.
- The rate change is an indication of the size of the gap, not a filed rate: no loss trend, no development beyond what insurers booked, no charge for capital. The true need is higher.
- Motor Commercial includes PSV. Insurers move business between the two; in Q4 2025 Madison moved KSh 1.6bn of earned premium from PSV to Motor Commercial, which left PSV with negative earned premium for the year.
- A low loss ratio is a warning, not proof. It can reflect a good book, heavy reinsurance or thin reserves. The test compares ten insurers with twenty-eight.
- 2016 is left out because IRA's 2016 class tables have no earned premium or expense split, and IRA has no year-end 2017 workbook online.
- Everything here is public IRA data. Nothing comes from inside any insurer.

## Sources

- Insurance Regulatory Authority, Kenya: quarterly industry statistics, via ira-kenya-data
- Werner and Modlin, Basic Ratemaking, Casualty Actuarial Society, 2016: https://www.casact.org/sites/default/files/old/studynotes_werner_modlin_ratemaking.pdf
- Court of Appeal ruling on IRA's motor underwriting guidelines, 20 September 2024 (EY tax alert): https://www.ey.com/en_gl/technical/tax-alerts/kenyan-court-of-appeal-declares-insurance-regulatory-authoritys-powers-include-price-regulation
- Regulator actions: see `reference/regulator_actions.csv`

Marion Peter
