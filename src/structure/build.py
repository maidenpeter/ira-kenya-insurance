"""Who holds Kenya's general insurance market, how that is changing, and what fragmentation costs.

Reads the revenue panel and class panel from ira-kenya-data (IRA_DATA_DIR, default ../ira-kenya-data)
and module 1's class table (output/class_company.csv), and writes to output/:

  structure_market.csv          per year: insurers, written premium, Herfindahl-Hirschman index, top 5 and
                                top 10 shares, the leader, the equivalent number of equal-sized insurers,
                                and how many insurers write over KSh 10bn
  structure_shares.csv          every insurer's written premium, share and rank each year
  structure_share_shift.csv     share change 2020 to 2025, pro forma for mergers (absorbed companies'
                                2020 premium is added to the company that took them over)
  structure_class_mix.csv       each class's share of market gross premium, and its own HHI, by year
  structure_growth_results.csv  premium growth 2018 to 2025 against combined ratio over the same years
  structure_fragmentation.csv   the extra management expense carried by insurers outside the five largest,
                                class for class, against the market's underwriting result

Written premium is gross direct premium plus inward reinsurance, insurers only, micro insurers included,
full years (Q4 year to date). HHI is the sum of squared percentage shares (0 to 10,000).

Fragmentation cost: for each year, the five largest insurers' management expenses over gross premium are
taken class by class as the benchmark. Every other insurer's expected expense is its gross premium in each
class times that class's benchmark. The cost is actual less expected, summed, so an insurer leaner than
the benchmark reduces it. Class-for-class matching keeps a medical-heavy insurer from being judged
against a motor-heavy benchmark.
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.environ.get("IRA_DATA_DIR", os.path.join(ROOT, "..", "ira-kenya-data"))
OUT = os.path.join(ROOT, "output")
MERGERS = {"allianz_kenya": "sanlam_allianz_general", "sanlam_general": "sanlam_allianz_general", "saham": "mua"}
BIG = 10_000_000  # KSh 10bn, in thousands
GROWTH = (2018, 2025)


def hhi(s):
    s = s.clip(lower=0)
    s = s / s.sum()
    return float((s ** 2).sum() * 1e4)


def main():
    rp = pd.read_csv(os.path.join(DATA, "data", "processed", "general_revenue_panel.csv"))
    names = rp.drop_duplicates("company_id").set_index("company_id").company_name
    r = rp[(rp.quarter == 4) & (rp.segment == "insurer")]
    w = r.pivot_table(index=["company_id", "year"], columns="line", values="ytd_ksh_000", aggfunc="sum").reset_index()
    w["written_premium"] = w.gross_direct_premium.fillna(0) + w.inward_reinsurance.fillna(0)
    w = w[w.written_premium > 0].copy()
    w["company_name"] = w.company_id.map(names)

    # shares and market concentration
    w["share"] = w.written_premium / w.groupby("year").written_premium.transform("sum")
    w["rank"] = w.groupby("year").written_premium.rank(ascending=False, method="first").astype(int)
    shares = w[["company_id", "company_name", "year", "written_premium", "share", "rank"]].sort_values(["year", "rank"])
    mk = []
    for y, g in w.groupby("year"):
        g = g.sort_values("written_premium", ascending=False)
        h = hhi(g.written_premium)
        mk.append(dict(year=y, insurers=len(g), written_premium=g.written_premium.sum(), hhi=h,
                       top5_share=g.share.iloc[:5].sum(), top10_share=g.share.iloc[:10].sum(),
                       leader=g.company_name.iloc[0], leader_share=g.share.iloc[0], equivalent_insurers=1e4 / h,
                       insurers_over_10bn=int((g.written_premium >= BIG).sum()),
                       share_over_10bn=g[g.written_premium >= BIG].share.sum()))
    mk = pd.DataFrame(mk)

    # pro forma share shift 2020 to 2025
    p = w.pivot(index="company_id", columns="year", values="written_premium")
    pf = p.rename(index=lambda i: MERGERS.get(i, i)).groupby(level=0).sum(min_count=1)
    sh = pf / pf.sum()
    shift = pd.DataFrame({"share_2020": sh[2020], "share_2025": sh[2025]}).fillna(0)
    shift["change_points"] = (shift.share_2025 - shift.share_2020) * 100
    shift["absorbed"] = [", ".join(names[k] for k, v in MERGERS.items() if v == i) for i in shift.index]
    shift = shift[(shift.share_2020 > 0) | (shift.share_2025 > 0)].reset_index().rename(columns={"index": "company_id"})
    shift.insert(1, "company_name", shift.company_id.map(names))
    shift = shift.sort_values("change_points")

    # class mix and class concentration
    cc = pd.read_csv(os.path.join(ROOT, "output", "class_company.csv"))
    mix = []
    for (y, cl), g in cc.groupby(["year", "class"]):
        mix.append(dict(year=y, **{"class": cl}, gross_premium=g.gross_premium.sum(), hhi=hhi(g.gross_premium),
                        insurers=int((g.gross_premium > 0).sum()),
                        top3_share=g.gross_premium.clip(lower=0).nlargest(3).sum() / g.gross_premium.clip(lower=0).sum()))
    mix = pd.DataFrame(mix)
    mix["share_of_market"] = mix.gross_premium / mix.groupby("year").gross_premium.transform("sum")

    # growth against results
    a, b = GROWTH
    span = w[w.year.between(a, b)]
    res = span.groupby("company_id")[["incurred_claims", "net_commissions", "management_expenses", "net_earned_premium",
                                      "underwriting_result"]].sum()
    res["combined_ratio"] = (res.incurred_claims + res.net_commissions + res.management_expenses) / res.net_earned_premium
    gr = p[[a, b]].dropna()
    gr = gr[gr[a] >= 500_000]
    gr["growth_a_year"] = (gr[b] / gr[a]) ** (1 / (b - a)) - 1
    mkt_growth = (p[b].sum() / p[a].sum()) ** (1 / (b - a)) - 1
    gr = gr.join(res[["combined_ratio", "underwriting_result"]]).reset_index()
    gr.insert(1, "company_name", gr.company_id.map(names))
    gr = gr.rename(columns={a: f"written_premium_{a}", b: f"written_premium_{b}"})
    gr["gained_share"] = gr.growth_a_year > mkt_growth
    gr["market_growth_a_year"] = mkt_growth

    # fragmentation cost, class for class
    fr = []
    for y, g in cc.groupby("year"):
        co = g.groupby("company_id").gross_premium.sum()
        top = co.nlargest(5).index
        t = g[g.company_id.isin(top)].groupby("class")[["management_expenses", "gross_premium"]].sum()
        bench = (t.management_expenses / t.gross_premium.where(t.gross_premium > 0)).clip(lower=0).fillna(0)
        rest = g[~g.company_id.isin(top)]
        expected = (rest["class"].map(bench) * rest.gross_premium.clip(lower=0)).sum()
        actual = rest.management_expenses.sum()
        fr.append(dict(year=y, top5=";".join(top), top5_expense_ratio=t.management_expenses.sum() / t.gross_premium.sum(),
                       rest_share=rest.gross_premium.sum() / g.gross_premium.sum(), rest_expenses=actual,
                       rest_expected_at_top5_rates=expected, extra_expense=actual - expected,
                       market_underwriting_result=g.underwriting_result.sum()))
    fr = pd.DataFrame(fr)

    kw = dict(index=False, lineterminator="\n", float_format="%.4f")
    mk.to_csv(os.path.join(OUT, "structure_market.csv"), **kw)
    shares.to_csv(os.path.join(OUT, "structure_shares.csv"), **kw)
    shift.to_csv(os.path.join(OUT, "structure_share_shift.csv"), **kw)
    mix.to_csv(os.path.join(OUT, "structure_class_mix.csv"), **kw)
    gr.to_csv(os.path.join(OUT, "structure_growth_results.csv"), **kw)
    fr.to_csv(os.path.join(OUT, "structure_fragmentation.csv"), **kw)

    pd.set_option("display.width", 220)
    print(mk.assign(written_premium=mk.written_premium / 1e6).round(3).to_string(index=False))
    print(fr[["year", "top5_expense_ratio", "extra_expense", "market_underwriting_result"]].assign(
        extra_expense=fr.extra_expense / 1e6, market_underwriting_result=fr.market_underwriting_result / 1e6).round(3).to_string(index=False))
    print("market growth", round(mkt_growth, 4))
    print(gr.groupby("gained_share").combined_ratio.describe().round(3))


if __name__ == "__main__":
    main()
