# Method

## Data

IRA quarterly industry statistics, class tables for each insurer at the fourth quarter (year to date), from `general_by_class_panel.csv` in ira-kenya-data. Tables used: gross premium, net earned premium, net claims incurred, net commissions, management expenses and underwriting result. Insurers only (reinsurers are left out), micro insurers included, which is how IRA's own releases count the market. Years 2018 to 2025: 2016 has no earned premium or expense split by class, and 2017 has no year-end workbook online.

Motor Commercial and Motor Commercial PSV are combined, because insurers move business between them from quarter to quarter.

## Checks

- Every insurer-class-year satisfies earned premium less claims, commissions and management expenses equals the underwriting result (4,545 of 4,545 within KSh 5,000 in the class panel).
- Classes add to the market total every year.
- Class results summed over 2020 to 2024 match IRA's Insurance Industry Releases for Q4 2023 and Q4 2024 (tables 15 to 21): motor private -19.21bn, motor commercial including PSV -15.33bn, workmen's compensation +11.01bn, medical +1.30bn in 2020 and -0.47bn in 2024.

## Rate gap

Loss ratio method (Werner and Modlin, Basic Ratemaking, CAS 2016, chapter 8):

    change = (L + F) / (1 - V - Q) - 1

L is net claims incurred over earned premium, F management expenses over earned premium (treated as fixed), V net commissions over earned premium (variable), Q the target margin, zero here. Pooled over 2023 to 2025. The investment income version sets the target combined ratio to 1 + y, where y is the market's investment income over earned premium for the same years (11.8%): change = (L + F) / (1 + y - V) - 1.

What it leaves out: loss trend to the future policy period, premium on-levelling for past rate changes, development beyond insurers' booked reserves, and any charge for capital. Each of these would raise the indication. Classes with less than KSh 1bn of pooled earned premium (aviation) and insurer books with less than KSh 0.3bn, or without all three years, are not shown.

## Low motor loss ratios

An insurer-year is flagged when motor earned premium is at least KSh 0.2bn and the motor loss ratio (private and commercial together) is under 40%. Capital trouble means, in any year from 2018: regulator action (five cases with sources in `reference/regulator_actions.csv`), negative equity, or equity below IRA's minimum capital for a general insurer, the higher of KSh 600m and 20% of net earned premium. Balance sheets that are all zeros (a company listed but not filing) are ignored. The comparison group is every other insurer with a motor book of the same minimum size. Fisher's exact test, two sided, is computed directly.

## Expense scale

Management expenses over gross premium (not earned premium, which retention distorts), every insurer with more than KSh 0.1bn of gross premium, regressed on the log of gross premium each year. The slope times log 2 gives the change per doubling of premium.
