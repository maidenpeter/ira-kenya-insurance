"""Build page/kenya-claims-settlement.html from output/ and page/claims_template.html, and write the README's
claims section from the same outputs (readme_block; tests/test_claims.py checks it is current)."""
import json
import os
import re

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "output")
PAGE = os.path.join(ROOT, "page")
README = os.path.join(ROOT, "README.md")
START, END = "<!-- claims start -->", "<!-- claims end -->"
BUS = {"general_liability": "liab", "general_non_liability": "nonl", "long_term": "life"}
WORDS = {3: "three", 4: "four"}


def pct(v):
    return f"{100 * v:.1f}%"


def readme_block():
    m = pd.read_csv(os.path.join(OUT, "claims_market.csv"))
    iy = pd.read_csv(os.path.join(OUT, "claims_insurer_year.csv"))
    rg = pd.read_csv(os.path.join(OUT, "claims_regulator.csv"))
    rn = pd.read_csv(os.path.join(OUT, "claims_runs.csv")).fillna("")
    ck = pd.read_csv(os.path.join(OUT, "claims_checks_summary.csv"))
    y = int(iy[iy.quarters == 4].year.max())
    pooled = {b: m[(m.business == b) & (m.year == y)] for b in BUS}
    pr = {b: x.paid.sum() / x.actionable.sum() for b, x in pooled.items()}
    med = {b: iy[(iy.business == b) & (iy.year == y) & iy.compared].median_payment_ratio.iloc[0] for b in BUS}
    q4 = m[(m.business == "general_liability") & (m.period == f"{y}Q4")].iloc[0]
    paid_q = pooled["general_liability"].paid.mean()
    peak = m[m.business == "general_liability"].sort_values("closing").iloc[-1]
    first_amt = m[(m.business == "general_liability") & m.closing_amount.notna()].iloc[0]
    under = rg.groupby("company_name", sort=False).under_half.sum()
    names = {c: short(c) for c in under.index}
    all4 = [names[c] for c, v in under.items() if v == 4]
    three = [f"{names[c]} in {WORDS[int(v)]} of four" for c, v in under.items() if v == 3]
    tri = rg[rg.company_id == "trident"].share_of_median
    compared = iy[(iy.business == "general_liability") & iy.compared].company_id.nunique()
    acted = rn[rn.regulator_action != ""].company_id.nunique()
    total = int(ck[["pass", "explained", "fail"]].sum().sum())
    neg = ck.set_index("check").loc["counts_not_negative", "fail"]
    quarters = m.period.nunique()
    if not (pr["general_liability"] < pr["general_non_liability"] < pr["long_term"]):
        raise SystemExit("the README says liability is the slowest business and life the fastest; the data no longer does")
    return f"""{START}
IRA publishes every insurer's claims movement each quarter: claims open at the start, claims reported, paid, declined and closed as no claim, and claims still open at the end. [ira-kenya-data](https://github.com/maidenpeter/ira-kenya-data) extracts the {quarters} quarterly workbooks IRA has published from Q1 2017 to Q1 2026, joins every printed name to a company and checks them {total:,} times. This module turns them into IRA's own payment ratio: claims paid in the quarter over the claims open in the quarter. It is the second analysis in the series, after the five pages above.

**Three speeds.** In an average quarter of {y} general insurers paid {pct(pr['general_liability'])} of the liability claims open to them (claims by third parties, most of them injury from motor accidents) and {pct(pr['general_non_liability'])} of their non-liability claims (medical, own damage, property), and life insurers paid {pct(pr['long_term'])} of theirs. The median insurer paid {pct(med['general_liability'])}, {pct(med['general_non_liability'])} and {pct(med['long_term'])}. Two medical insurers report most non-liability claims by number, which is why the market and the median differ there.

**The queue.** {int(q4.closing):,} liability claims were outstanding at the end of {y}, KSh {q4.closing_amount / 1e6:.1f}bn by the insurers' own estimates: {q4.closing / paid_q:.1f} quarters of payments at the {y} pace of {paid_q:,.0f} a quarter. The count peaked at {int(peak.closing):,} in Q{peak.period[5]} {peak.period[:4]}; by value the queue grew from KSh {first_amt.closing_amount / 1e6:.1f}bn in Q{first_amt.period[5]} {first_amt.period[:4]}, the first quarter IRA printed amounts.

**The five the regulator stepped into.** In the last four quarters each reported before the regulator acted, {' and '.join(all4)} paid liability claims at under half the median insurer's rate in all four, {', '.join(three)}. Resolution, mainly a medical insurer, paid close to or above the median; Trident reported paying {tri.min():.0f} to {tri.max():.0f} times the median. Paying slowly is common: {rn.company_id.nunique()} of the {compared} general insurers compared had four quarters running under half the median at some point since 2017, and {acted} of them later came under the regulator.

**Caveats.** The returns are unaudited. A low payment ratio can reflect a book of slow claims as much as slow payment. {neg} insurer-quarters print a negative count and are given no ratio; where an insurer's own claims do not add up from one quarter to the next, the return is kept as printed and counted. This is a screening view, not a credit opinion.
{END}"""


def write_readme():
    s = open(README, encoding="utf-8").read()
    block = readme_block()
    if START in s:
        s = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda _: block, s, flags=re.S)
    else:
        s = s.replace("## See it", "## Claims settlement (analysis 2)\n\n" + block + "\n\n## See it", 1)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def r(v, nd=4):
    return None if v is None or pd.isna(v) else round(float(v), nd)


def i(v):
    return None if v is None or pd.isna(v) else int(round(float(v)))


def short(name):
    name = name.split(" (")[0]
    for tail in [" Insurance Company", " Assurance Company", " Insurance Kenya", " Life Assurance Kenya", " Life Insurance",
                 " Life Assurance", " Insurance", " Assurance", " Company"]:
        if name.endswith(tail) and len(name) > len(tail) + 3:
            return name[: -len(tail)] + (" Life" if "Life" in tail else "")
    return name


def quarters(first, last):
    out, (y, q) = [], (int(first[:4]), int(first[5]))
    while f"{y}Q{q}" <= last:
        out.append(f"{y}Q{q}")
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def main():
    m = pd.read_csv(os.path.join(OUT, "claims_market.csv"))
    iy = pd.read_csv(os.path.join(OUT, "claims_insurer_year.csv"))
    rg = pd.read_csv(os.path.join(OUT, "claims_regulator.csv"))
    rn = pd.read_csv(os.path.join(OUT, "claims_runs.csv")).fillna("")
    ck = pd.read_csv(os.path.join(OUT, "claims_checks_summary.csv"))
    ra = pd.read_csv(os.path.join(ROOT, "reference", "regulator_actions.csv")).set_index("company_id")

    published = sorted(m.period.unique())
    periods = quarters(published[0], published[-1])
    market = {}
    for b, k in BUS.items():
        x = m[m.business == b].set_index("period")
        market[k] = [None if p not in x.index else dict(
            act=i(x.loc[p, "actionable"]), paid=i(x.loc[p, "paid"]), close=i(x.loc[p, "closing"]), rep=i(x.loc[p, "intimated"]),
            pr=r(x.loc[p, "payment_ratio"]), med=r(x.loc[p, "median_payment_ratio"]), n=i(x.loc[p, "insurers_compared"]),
            pa=r(x.loc[p, "paid_amount"] / 1e3, 1), ca=r(x.loc[p, "closing_amount"] / 1e3, 1),
            pra=r(x.loc[p, "payment_ratio_amount"])) for p in periods]
    # pooled by year, full years only
    years = {}
    for b, k in BUS.items():
        x = m[m.business == b].groupby("year").agg(q=("period", "nunique"), paid=("paid", "sum"), act=("actionable", "sum"))
        years[k] = {int(y): dict(q=int(v.q), pr=r(v.paid / v.act)) for y, v in x.iterrows()}

    last_year = int(iy[iy.quarters == 4].year.max())
    ins = {}
    for b, k in BUS.items():
        x = iy[(iy.business == b) & (iy.year == last_year) & iy.compared].sort_values("payment_ratio")
        ins[k] = dict(med=r(x.median_payment_ratio.iloc[0]), rows=[dict(
            id=v.company_id, name=short(v.company_name), act=i(v.actionable), paid=i(v.paid), pr=r(v.payment_ratio),
            close=i(v.closing_at_last), ca=r(v.closing_amount_at_last / 1e3, 1)) for _, v in x.iterrows()])

    reg = []
    for c, x in rg.groupby("company_id", sort=False):
        reg.append(dict(id=c, name=short(x.company_name.iloc[0]), action=x.action.iloc[0], date=x.action_date.iloc[0],
                        src=ra.loc[c, "source"] if str(ra.loc[c, "source"]).startswith("http") else None,
                        q=[dict(p=v.period, open=i(v.open_claims), pr=r(v.payment_ratio), med=r(v.median_payment_ratio),
                                sh=r(v.share_of_median, 3), under=bool(v.under_half)) for _, v in x.iterrows()]))
    acted = rn[rn.regulator_action != ""].drop_duplicates("company_id")
    in_year = rn[(rn["first"] >= f"{last_year}Q1") & (rn["last"] <= f"{last_year}Q4")].drop_duplicates("company_id")
    runs = dict(insurers=int(rn.company_id.nunique()), acted=int(acted.company_id.nunique()),
                acted_names=[short(n) for n in acted.company_name], in_year=[short(n) for n in in_year.company_name],
                compared=int(iy[(iy.business == "general_liability") & iy.compared].company_id.nunique()))
    checks = {v.check: dict(passed=int(v["pass"]), explained=int(v.explained), failed=int(v.fail)) for _, v in ck.iterrows()}
    data = dict(periods=periods, published=published, market=market, years=years, ins=ins, last=last_year, reg=reg,
                runs=runs, checks=checks, min_open=50)
    js = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
    with open(os.path.join(PAGE, "claims_data.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    tpl = open(os.path.join(PAGE, "claims_template.html"), encoding="utf-8").read()
    body = tpl.replace("/*__DATA__*/null", js.replace("</", "<\\/"))
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>\n'
            + body + "\n</body></html>\n")
    with open(os.path.join(PAGE, "kenya-claims-settlement.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    write_readme()
    print(f"page {len(html) / 1024:.0f} KB; README claims section written")


if __name__ == "__main__":
    main()
