"""Build page/kenya-insurance-market-structure.html from output/ and page/structure_template.html."""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "output")
PAGE = os.path.join(ROOT, "page")


def r(v, nd=4):
    return None if v is None or pd.isna(v) else round(float(v), nd)


def short(name):
    name = name.split(" (")[0]
    for tail in [" Insurance Company", " Assurance Company", " Insurance Kenya", " Insurance", " Assurance", " Company"]:
        if name.endswith(tail) and len(name) > len(tail) + 3:
            return name[: -len(tail)]
    return name


def main():
    mk = pd.read_csv(os.path.join(OUT, "structure_market.csv"))
    shares = pd.read_csv(os.path.join(OUT, "structure_shares.csv"))
    shift = pd.read_csv(os.path.join(OUT, "structure_share_shift.csv"))
    mix = pd.read_csv(os.path.join(OUT, "structure_class_mix.csv"))
    gr = pd.read_csv(os.path.join(OUT, "structure_growth_results.csv"))
    fr = pd.read_csv(os.path.join(OUT, "structure_fragmentation.csv"))
    ee = pd.read_csv(os.path.join(ROOT, "reference", "entries_exits.csv"))
    ra = pd.read_csv(os.path.join(ROOT, "reference", "regulator_actions.csv"))
    names = shares.drop_duplicates("company_id").set_index("company_id").company_name

    market = [dict(y=int(x.year), n=int(x.insurers), wp=r(x.written_premium / 1e3, 1), hhi=r(x.hhi, 1), top5=r(x.top5_share),
                   top10=r(x.top10_share), leader=short(x.leader), lshare=r(x.leader_share), eq=r(x.equivalent_insurers, 2),
                   big=int(x.insurers_over_10bn), bigshare=r(x.share_over_10bn)) for _, x in mk.iterrows()]
    last = int(mk.year.max())
    strip = [dict(id=x.company_id, name=short(x.company_name), wp=r(x.written_premium / 1e3, 1), share=r(x.share))
             for _, x in shares[shares.year == last].sort_values("rank").iterrows()]
    sh = [dict(id=x.company_id, name=short(x.company_name), s20=r(x.share_2020), s25=r(x.share_2025), d=r(x.change_points, 3),
               absorbed=None if pd.isna(x.absorbed) or not x.absorbed else ", ".join(short(a) for a in x.absorbed.split(", ")))
          for _, x in shift.iterrows() if abs(x.change_points) >= 0.05]
    years = sorted(int(y) for y in mix.year.unique())
    top_classes = mix[mix.year == last].sort_values("gross_premium", ascending=False)["class"].tolist()[:5]
    cmix = {}
    for cl in top_classes + ["Other classes"]:
        if cl == "Other classes":
            g = mix[~mix["class"].isin(top_classes)].groupby("year").share_of_market.sum()
        else:
            g = mix[mix["class"] == cl].set_index("year").share_of_market
        cmix[cl] = [r(g.get(y)) for y in years]
    chhi = {cl: r(mix[(mix["class"] == cl) & (mix.year == last)].hhi.iloc[0], 0) for cl in top_classes}
    ctop3 = {cl: r(mix[(mix["class"] == cl) & (mix.year == last)].top3_share.iloc[0]) for cl in top_classes}
    growth = [dict(id=x.company_id, name=short(x.company_name), g=r(x.growth_a_year), cr=r(x.combined_ratio),
                   uw=r(x.underwriting_result / 1e3, 1), wp=r(x.written_premium_2025 / 1e3, 1), gained=bool(x.gained_share))
              for _, x in gr.iterrows()]
    gstats = dict(mkt=r(gr.market_growth_a_year.iloc[0]),
                  cr_gain=r(gr[gr.gained_share].combined_ratio.median()), cr_lose=r(gr[~gr.gained_share].combined_ratio.median()),
                  n_gain=int(gr.gained_share.sum()), n_lose=int((~gr.gained_share).sum()),
                  lose_over_110=int(((~gr.gained_share) & (gr.combined_ratio > 1.10)).sum()),
                  gain_over_110=int((gr.gained_share & (gr.combined_ratio > 1.10)).sum()))
    frag = [dict(y=int(x.year), extra=r(x.extra_expense / 1e3, 1), uw=r(x.market_underwriting_result / 1e3, 1),
                 bench=r(x.top5_expense_ratio), rest=r(x.rest_share), top5=[short(names.get(i, i)) for i in x.top5.split(";")])
            for _, x in fr.iterrows()]
    first_last = shares.groupby("company_id").year.agg(["min", "max"])
    events = []
    for _, x in ee.iterrows():
        fl = first_last.loc[x.company_id] if x.company_id in first_last.index else None
        events.append(dict(id=x.company_id, name=short(names.get(x.company_id, x.company_id)), kind=x.kind,
                           first=None if fl is None else int(fl["min"]), last=None if fl is None else int(fl["max"]),
                           what=x.what_happened, src=x.source if str(x.source).startswith("http") else None))
    data = dict(market=market, strip=strip, shift=sh, years=years, cmix=cmix, chhi=chhi, ctop3=ctop3, growth=growth,
                gstats=gstats, frag=frag, events=events, last=last)
    js = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    with open(os.path.join(PAGE, "structure_data.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    tpl = open(os.path.join(PAGE, "structure_template.html"), encoding="utf-8").read()
    body = tpl.replace("/*__DATA__*/null", js.replace("</", "<\\/"))
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>\n'
            + body + "\n</body></html>\n")
    with open(os.path.join(PAGE, "kenya-insurance-market-structure.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"page {len(html) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
