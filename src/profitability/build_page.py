"""Build page/kenya-insurance-loss-map.html from output/ and page/template.html (data inlined)."""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "output")
PAGE = os.path.join(ROOT, "page")


def r(v, nd=4):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) or pd.isna(v) else round(float(v), nd)


def short(name):
    name = name.split(" (")[0]
    for tail in [" Insurance Company", " Assurance Company", " Insurance Kenya", " Insurance", " Assurance", " Company"]:
        if name.endswith(tail) and len(name) > len(tail) + 3:
            return name[: -len(tail)]
    return name


def main():
    mk = pd.read_csv(os.path.join(OUT, "class_market.csv"))
    gap = pd.read_csv(os.path.join(OUT, "rate_gap.csv"))
    gc = pd.read_csv(os.path.join(OUT, "rate_gap_company.csv"))
    lc = pd.read_csv(os.path.join(OUT, "loss_concentration.csv"))
    low = pd.read_csv(os.path.join(OUT, "low_motor_loss_ratio.csv"))
    test = pd.read_csv(os.path.join(OUT, "low_motor_loss_ratio_test.csv"))
    es = pd.read_csv(os.path.join(OUT, "expense_scale.csv"))
    cc = pd.read_csv(os.path.join(OUT, "class_company.csv"))

    years = sorted(int(y) for y in mk.year.unique())
    classes = (mk[mk["class"] != "All classes"].groupby("class").underwriting_result.sum().sort_values().index.tolist())
    grid = {}
    for c in classes + ["All classes"]:
        g = mk[mk["class"] == c].set_index("year")
        grid[c] = dict(cr=[r(g.combined_ratio.get(y)) for y in years], uw=[r(g.underwriting_result.get(y) / 1e3, 1) for y in years],
                       nep=[r(g.net_earned_premium.get(y) / 1e3, 1) for y in years],
                       lr=[r(g.loss_ratio.get(y)) for y in years], gp=[r(g.gross_premium.get(y) / 1e3, 1) for y in years])
    cum = {c: r(mk[mk["class"] == c].underwriting_result.sum() / 1e3, 1) for c in classes + ["All classes"]}

    gaps = [dict(cls=x["class"], nep=r(x.net_earned_premium / 1e3, 1), uw=r(x.underwriting_result / 1e3, 1), lr=r(x.loss_ratio),
                 cm=r(x.commission_ratio), ex=r(x.expense_ratio), cr=r(x.combined_ratio), be=r(x.rate_change_to_break_even),
                 ai=r(x.rate_change_after_investment_income), shown=bool(x.shown)) for _, x in gap.iterrows()]
    yld = float(gap.investment_yield_on_premium.iloc[0])

    # motor by company, cumulative, plus yearly motor loss ratios for the dot plot
    motor = [dict(id=x.company_id, name=short(x.company_name), full=x.company_name, uw=r(x.underwriting_result / 1e3, 1),
                  cr=r(x.combined_ratio), share=r(x.market_share_motor_premium), lossshare=r(x.share_of_motor_losses))
             for _, x in lc.iterrows()]
    mm = cc[cc["class"].str.startswith("Motor")].groupby(["company_id", "company_name", "year"])[
        ["net_earned_premium", "claims_incurred"]].sum().reset_index()
    mm = mm[mm.net_earned_premium >= 200_000]
    mm["lr"] = mm.claims_incurred / mm.net_earned_premium
    troubled = set(low[low.trouble_same_year_or_later].company_id)
    ra = pd.read_csv(os.path.join(ROOT, "reference", "regulator_actions.csv")).set_index("company_id")
    dots = [dict(id=x.company_id, name=short(x.company_name), y=int(x.year), lr=r(x.lr), nep=r(x.net_earned_premium / 1e3, 1))
            for _, x in mm.iterrows()]
    lows = [dict(id=x.company_id, name=short(x.company_name), y=int(x.year), lr=r(x.loss_ratio), mkt=r(x.market_motor_loss_ratio),
                 action=None if pd.isna(x.regulator_action) else x.regulator_action,
                 neg=None if pd.isna(x.negative_equity_years) else x.negative_equity_years,
                 below=None if pd.isna(x.below_capital_floor_years) else x.below_capital_floor_years,
                 later=bool(x.trouble_same_year_or_later)) for _, x in low.iterrows()]
    tests = test.round(4).to_dict(orient="records")
    motor_mkt = mk[mk["class"].str.startswith("Motor")].groupby("year")[["claims_incurred", "net_earned_premium"]].sum()
    motor_lr = {int(y): r(v) for y, v in (motor_mkt.claims_incurred / motor_mkt.net_earned_premium).items()}

    comp_gap = [dict(id=x.company_id, name=short(x.company_name), book=x.book, nep=r(x.net_earned_premium / 1e3, 1),
                     cr=r(x.combined_ratio), be=r(x.rate_change_to_break_even)) for _, x in gc[gc.shown].iterrows()]

    scale = {}
    for y in years:
        e = es[es.year == y]
        b = np.polyfit(e.log_gross_premium, e.expense_to_gross_premium, 1)
        rho = np.corrcoef(e.log_gross_premium, e.expense_to_gross_premium)[0, 1]
        scale[y] = dict(pts=[dict(id=x.company_id, name=short(x.company_name), gp=r(x.gross_premium / 1e3, 1),
                                  ex=r(x.expense_to_gross_premium)) for _, x in e.iterrows()],
                        slope=r(b[0]), icpt=r(b[1]), rho=r(rho, 3), per_doubling=r(b[0] * np.log(2)),
                        small=r(e[e.gross_premium < 3e6].expense_to_gross_premium.median()),
                        large=r(e[e.gross_premium >= 10e6].expense_to_gross_premium.median()),
                        n_small=int((e.gross_premium < 3e6).sum()), n_large=int((e.gross_premium >= 10e6).sum()))

    m25 = mk[mk.year == years[-1]]
    mot25 = m25[m25["class"].str.startswith("Motor")][["gross_premium", "net_earned_premium", "claims_incurred"]].sum()
    all25 = m25[m25["class"] == "All classes"][["gross_premium", "net_earned_premium", "claims_incurred"]].iloc[0]
    head = dict(total=cum["All classes"], motor=r(sum(cum[c] for c in classes if c.startswith("Motor")), 1),
                rest=r(sum(cum[c] for c in classes if not c.startswith("Motor")), 1),
                wiba=cum.get("Workmen's Compensation"), gp_share=r(mot25.gross_premium / all25.gross_premium),
                nep_share=r(mot25.net_earned_premium / all25.net_earned_premium),
                claims_share=r(mot25.claims_incurred / all25.claims_incurred),
                profitable_motor=int((lc.underwriting_result > 0).sum()), motor_insurers=int(len(lc)),
                top10=r(lc.cumulative_share.iloc[9]))
    data = dict(years=years, classes=classes, grid=grid, cum=cum, gaps=gaps, yld=yld, motor=motor, dots=dots,
                lows=lows, tests=tests, motor_lr=motor_lr, comp_gap=comp_gap, scale=scale, head=head,
                actions=ra.reset_index().to_dict(orient="records"))
    js = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    with open(os.path.join(PAGE, "loss_map_data.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    tpl = open(os.path.join(PAGE, "template.html"), encoding="utf-8").read()
    body = tpl.replace("/*__DATA__*/null", js.replace("</", "<\\/"))
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>\n'
            + body + "\n</body></html>\n")
    with open(os.path.join(PAGE, "kenya-insurance-loss-map.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"page {len(html) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
