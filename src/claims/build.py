"""Claims settlement: how much of what is claimed gets paid, how fast, and by whom.

Reads the claims panel from ira-kenya-data (IRA_DATA_DIR, default ../ira-kenya-data), built from IRA's
quarterly claims settlement statistics, and the regulator actions in reference/regulator_actions.csv. Writes
to output/:

  claims_market.csv       per quarter and business: claims open, paid, declined, closed and outstanding;
                          the market's payment ratio, the median insurer's, and amounts where IRA prints them
  claims_insurer_year.csv per insurer, business and year: claims open and paid over the year's quarters, the
                          payment ratio, and the claims still outstanding at the year's last quarter
  claims_regulator.csv    the five insurers the regulator has stepped into since 2022: their liability payment
                          ratio in each of the last four published quarters before the action, against the median
  claims_runs.csv         every run of four published quarters in which a general insurer paid liability claims
                          at under half the median insurer's rate, and whether the regulator later acted
  claims_checks_summary.csv  the data repo's checks on the claims tables, counted by result

The payment ratio is IRA's: claims paid in the quarter over the claims open to the insurer in the quarter
(paid + declined + closed as no claim + still outstanding at the end). Over a year it is pooled: the year's
claims paid over the year's open claims, quarter by quarter. Counts are claims; amounts are KSh thousands.

An insurer is compared in a quarter when it had at least MIN_OPEN claims open in that business. Micro insurers
are left out. Three businesses: general liability (claims by third parties, most of them motor injury),
general non-liability (own damage, medical, property and the rest) and long-term (life, pensions, funeral).
"""
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.environ.get("IRA_DATA_DIR", os.path.join(ROOT, "..", "ira-kenya-data"))
OUT = os.path.join(ROOT, "output")
MIN_OPEN = 50
HALF = 0.5
FIELDS = ["actionable", "paid", "declined", "closed", "declined_closed", "closing", "opening", "intimated"]


def pidx(period):
    return int(period[:4]) * 4 + int(period[5]) - 1


def load():
    p = pd.read_csv(os.path.join(DATA, "data", "processed", "claims_panel.csv"))
    return p[p.is_micro == 0].copy()


def market(p):
    n = p[p.unit == "number"]
    a = p[p.unit == "amount"]
    g = n.groupby(["period", "year", "quarter", "business"])[FIELDS].sum(min_count=1).reset_index()
    g["insurers"] = n[n.actionable > 0].groupby(["period", "business"]).company_id.nunique().reindex(
        pd.MultiIndex.from_frame(g[["period", "business"]])).values
    g["payment_ratio"] = g.paid / g.actionable
    big = n[n.actionable >= MIN_OPEN]
    med = big.groupby(["period", "business"]).payment_ratio.agg(["median", "count"]).reset_index()
    g = g.merge(med.rename(columns={"median": "median_payment_ratio", "count": "insurers_compared"}),
                on=["period", "business"], how="left")
    am = a.groupby(["period", "business"])[["paid", "closing", "intimated", "actionable"]].sum(min_count=1).reset_index()
    am.columns = ["period", "business", "paid_amount", "closing_amount", "intimated_amount", "actionable_amount"]
    g = g.merge(am, on=["period", "business"], how="left")
    g["payment_ratio_amount"] = g.paid_amount / g.actionable_amount
    g["quarters_to_clear"] = g.closing / g.paid
    return g.sort_values(["business", "year", "quarter"])


def insurer_year(p):
    n = p[p.unit == "number"].copy()
    n["pi"] = n.period.map(pidx)
    last = n.sort_values("pi").groupby(["company_id", "business", "year"]).tail(1)[
        ["company_id", "business", "year", "period", "closing"]].rename(columns={"period": "last_period", "closing": "closing_at_last"})
    g = n.groupby(["company_id", "company_name", "business", "year"]).agg(
        quarters=("period", "nunique"), actionable=("actionable", "sum"), paid=("paid", "sum"),
        declined=("declined", "sum"), avg_open=("actionable", "mean")).reset_index()
    g = g.merge(last, on=["company_id", "business", "year"])
    # the ratio pools only quarters with a ratio: a return with a negative count has none (see ira-kenya-data)
    v = n[n.payment_ratio.notna()].groupby(["company_id", "business", "year"]).agg(
        valid_quarters=("period", "nunique"), actionable_valid=("actionable", "sum"), paid_valid=("paid", "sum")).reset_index()
    g = g.merge(v, on=["company_id", "business", "year"], how="left")
    g["valid_quarters"] = g.valid_quarters.fillna(0).astype(int)
    g["payment_ratio"] = (g.paid_valid / g.actionable_valid).where(g.actionable_valid > 0)
    a = p[p.unit == "amount"].copy()
    a["pi"] = a.period.map(pidx)
    la = a.sort_values("pi").groupby(["company_id", "business", "year"]).tail(1)[["company_id", "business", "year", "closing"]]
    pa = a.groupby(["company_id", "business", "year"]).paid.sum().rename("paid_amount").reset_index()
    g = g.merge(la.rename(columns={"closing": "closing_amount_at_last"}), on=["company_id", "business", "year"], how="left")
    g = g.merge(pa, on=["company_id", "business", "year"], how="left")
    # the median insurer's pooled ratio that year, among insurers compared (MIN_OPEN open claims on average)
    # and a ratio in all but at most one of the year's published quarters (a quarter printed as all zeros has none)
    cmp_ = g[(g.avg_open >= MIN_OPEN) & (g.valid_quarters >= g.groupby(["business", "year"]).quarters.transform("max") - 1)]
    med = cmp_.groupby(["business", "year"]).payment_ratio.median().rename("median_payment_ratio")
    g = g.merge(med.reset_index(), on=["business", "year"], how="left")
    g["compared"] = g.index.isin(cmp_.index)
    return g.sort_values(["business", "year", "payment_ratio"])


def quarterly_liability(p):
    n = p[(p.unit == "number") & (p.business == "general_liability") & (p.actionable >= MIN_OPEN) & p.payment_ratio.notna()].copy()
    n["median"] = n.groupby("period").payment_ratio.transform("median")
    n["share_of_median"] = n.payment_ratio / n["median"]
    n["under_half"] = n.share_of_median < HALF
    n["pi"] = n.period.map(pidx)
    return n.sort_values(["company_id", "pi"])


def regulator(q):
    ra = pd.read_csv(os.path.join(ROOT, "reference", "regulator_actions.csv"))
    rows = []
    for _, a in ra.iterrows():
        y, m = map(int, a.date.split("-"))
        cut = y * 4 + (m - 1) // 3          # quarters that ended before the action's quarter began
        x = q[(q.company_id == a.company_id) & (q.pi < cut)].tail(4)
        for _, r in x.iterrows():
            rows.append(dict(company_id=a.company_id, company_name=r.company_name, action=a.action, action_date=a.date,
                             period=r.period, open_claims=r.actionable, paid=r.paid, payment_ratio=r.payment_ratio,
                             median_payment_ratio=r["median"], share_of_median=r.share_of_median, under_half=r.under_half))
    return pd.DataFrame(rows)


def runs(q):
    ra = pd.read_csv(os.path.join(ROOT, "reference", "regulator_actions.csv")).set_index("company_id")
    rows = []
    for c, x in q.groupby("company_id"):
        x = x.reset_index(drop=True)
        for i in range(3, len(x)):
            w = x.iloc[i - 3:i + 1]
            if w.under_half.all():
                act = ra.action.get(c)
                rows.append(dict(company_id=c, company_name=w.company_name.iloc[-1], first=w.period.iloc[0], last=w.period.iloc[-1],
                                 max_share_of_median=w.share_of_median.max(), regulator_action=act if isinstance(act, str) else "",
                                 action_date=ra.date.get(c, "")))
    return pd.DataFrame(rows, columns=["company_id", "company_name", "first", "last", "max_share_of_median",
                                       "regulator_action", "action_date"])


def main():
    p = load()
    os.makedirs(OUT, exist_ok=True)
    m = market(p)
    m.to_csv(os.path.join(OUT, "claims_market.csv"), index=False, lineterminator="\n", float_format="%.6f")
    iy = insurer_year(p)
    iy.to_csv(os.path.join(OUT, "claims_insurer_year.csv"), index=False, lineterminator="\n", float_format="%.6f")
    q = quarterly_liability(p)
    rg = regulator(q)
    rg.to_csv(os.path.join(OUT, "claims_regulator.csv"), index=False, lineterminator="\n", float_format="%.6f")
    rn = runs(q)
    rn.to_csv(os.path.join(OUT, "claims_runs.csv"), index=False, lineterminator="\n", float_format="%.6f")

    ck = pd.read_csv(os.path.join(DATA, "validation", "claims_checks.csv"))
    cs = ck.groupby("check").result.value_counts().unstack(fill_value=0).reindex(columns=["pass", "explained", "fail"], fill_value=0)
    cs.reset_index().to_csv(os.path.join(OUT, "claims_checks_summary.csv"), index=False, lineterminator="\n")

    L = m[m.business == "general_liability"].set_index("period")
    y = iy[(iy.business == "general_liability") & (iy.year == 2025)]
    print(f"liability: {int(L.loc['2025Q4', 'closing']):,} open at end-2025, payment ratio "
          f"{L.loc['2025Q4', 'payment_ratio']:.1%} in Q4 2025; {int(y.compared.sum())} insurers compared in 2025")
    print(f"runs under half the median: {rn.company_id.nunique()} insurers, "
          f"{rn[rn.regulator_action != ''].company_id.nunique()} later under the regulator")
    print(rg.groupby("company_id").under_half.agg(["sum", "count"]).to_string())


if __name__ == "__main__":
    main()
