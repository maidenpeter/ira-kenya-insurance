"""Build page/kenya-insurance-reinsurance-flows.html from output/ and page/reinsurance_template.html, and
write the README's reinsurance section from the same figures.

    python src/reinsurance/build_page.py

facts() computes every number the page's text and the README quote, from the output files only, so the
tests can recompute them without the data repository.
"""
import json
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "output")
PAGE = os.path.join(ROOT, "page")
README = os.path.join(ROOT, "README.md")
START, END = "<!-- reinsurance flows: written by src/reinsurance/build_page.py -->", "<!-- reinsurance flows end -->"
CAVEAT = "From the insurer's unaudited returns to the IRA. A screening view, not a credit opinion."
CAVEAT_RE = "From the reinsurer's unaudited returns to the IRA. A screening view, not a credit opinion."


def r(v, nd=4):
    return None if v is None or pd.isna(v) else round(float(v), nd)


def short(name):
    name = name.split(" (")[0]
    for tail, new in [(" Reinsurance Corporation", " Re"), (" Reinsurance Company", " Re"), (" Reinsurance Kenya", " Re"),
                      (" Reinsurance", " Re")]:
        if name.endswith(tail):
            return name[: -len(tail)] + new
    for tail in [" Insurance Company", " Assurance Company", " Insurance Kenya", " Insurance", " Assurance", " Company"]:
        if name.endswith(tail) and len(name) > len(tail) + 3:
            return name[: -len(tail)]
    return name


def tiny(name):
    """A name short enough for a phone's label column: no "The", no Insurance, Assurance, Company, Kenya or of Africa."""
    n = short(name)
    words = [w for i, w in enumerate(n.split()) if w not in ("The", "Insurance", "Assurance", "Company", "of", "Africa")
             and not (w == "Kenya" and i > 0)]
    t = " ".join(words) or n
    if len(t) > 15 and words and words[-1] == "General":
        t = " ".join(words[:-1])
    return t


def read(name):
    return pd.read_csv(os.path.join(OUT, name))


def facts():
    cc, co, sg = read("reinsurance_class_cession.csv"), read("reinsurance_insurer_retention.csv"), read("reinsurance_size_gradient.csv")
    rc, mk, rr = read("reinsurance_retention_change.csv"), read("reinsurance_market.csv"), read("reinsurance_reinsurer_results.csv")
    ln = read("reinsurance_scorecard_link.csv")
    y0, y1 = int(mk.year.min()), int(mk.year.max())
    m = mk.set_index("year")
    F = dict(first=y0, last=y1)
    F["ceded_last"], F["cr_last"], F["gp_last"] = m.ceded_premium[y1], m.cession_rate[y1], m.gross_premium[y1]
    F["ceded_total"] = mk.ceded_premium.sum()
    F["cr_min"], F["cr_min_year"] = m.cession_rate.min(), int(m.cession_rate.idxmin())
    F["cr_max"], F["cr_max_year"] = m.cession_rate.max(), int(m.cession_rate.idxmax())
    F["insurers_last"] = int(cc[(cc.year == y1) & (cc["class"] == "All classes")].insurers.iloc[0])
    F["reconcile_max"] = float(co.reconcile_gap.abs().max())  # KSh thousands

    last = cc[(cc.year == y1) & (cc["class"] != "All classes")].set_index("class")
    F["cls"] = {k: dict(cr=v.cession_rate, sh=v.share_of_ceded) for k, v in last.iterrows()}
    motor = last.loc[["Motor Private", "Motor Commercial"]]
    F["motor_cr"] = motor.ceded_premium.sum() / motor.gross_premium.sum()
    top2 = last.sort_values("share_of_ceded", ascending=False).head(2)
    F["top2"] = list(top2.index)
    F["top2_share"] = top2.share_of_ceded.sum()

    # the year with the largest rise in the market cession rate: how much came from classes ceding more, how much from the mix
    p = cc[cc["class"] != "All classes"].pivot(index="class", columns="year", values=["gross_premium", "cession_rate"]).fillna(0)
    rise = m.cession_rate.diff()
    yr = int(rise.idxmax())
    w0 = p["gross_premium"][yr - 1] / p["gross_premium"][yr - 1].sum()
    w1 = p["gross_premium"][yr] / p["gross_premium"][yr].sum()
    within = w0 * (p["cession_rate"][yr] - p["cession_rate"][yr - 1])
    F["rise_year"], F["rise_pts"] = yr, rise[yr] * 100
    F["rise_within_pts"], F["rise_mix_pts"] = within.sum() * 100, ((w1 - w0) * p["cession_rate"][yr]).sum() * 100
    F["rise_top_class"], F["rise_top_class_pts"] = within.idxmax(), within.max() * 100

    # the IFRS 17 switch in the returns
    i17 = int(mk[mk.basis.str.contains("IFRS 17")].year.min())
    others = mk[(mk.year != i17) & mk.mean_abs_change_from_prior_year.notna()]
    F["ifrs17_year"] = i17
    F["ifrs17_abs"], F["ifrs17_med"] = m.mean_abs_change_from_prior_year[i17] * 100, m.median_change_from_prior_year[i17] * 100
    F["other_abs_min"], F["other_abs_max"] = others.mean_abs_change_from_prior_year.min() * 100, others.mean_abs_change_from_prior_year.max() * 100
    F["ifrs17_cr_change"] = (m.cession_rate[i17] - m.cession_rate[i17 - 1]) * 100

    # size
    s = sg[sg.year == y1].set_index("size_band")
    F["band_med"] = {b: s.median_retention[b] for b in s.index if b != "All compared"}
    F["band_edges"] = sorted({float(v) for v in pd.concat([sg.lower_ksh_000, sg.upper_ksh_000]).dropna()} - {0.0})
    F["min_gp"] = float(sg.compare_threshold_ksh_000.iloc[0])
    F["band_n"] = {b: int(s.insurers[b]) for b in s.index if b != "All compared"}
    rho = sg[sg.size_band == "All compared"].spearman_retention_size
    F["rho_min"], F["rho_max"] = rho.min(), rho.max()
    cmp_last = co[(co.year == y1) & co.compared].sort_values("retention")
    F["compared_last"] = len(cmp_last)
    F["lowest"] = [(short(n), v) for n, v in zip(cmp_last.company_name.head(3), cmp_last.retention.head(3))]
    F["highest"] = [(short(n), v) for n, v in zip(cmp_last.company_name.tail(3)[::-1], cmp_last.retention.tail(3)[::-1])]
    F["median_retention_last"] = cmp_last.retention.median()

    # change 2018 to 2025
    F["chg_n"], F["chg_fell"], F["chg_rose"] = len(rc), int((rc.change_points < 0).sum()), int((rc.change_points > 0).sum())
    F["chg_median"] = rc.change_points.median()
    lo, hi = rc.sort_values("change_points").iloc[0], rc.sort_values("change_points").iloc[-1]
    F["chg_low"] = (short(lo.company_name), lo[f"retention_{y0}"], lo[f"retention_{y1}"], lo.change_points)
    F["chg_high"] = (short(hi.company_name), hi[f"retention_{y0}"], hi[f"retention_{y1}"], hi.change_points)

    # how much could stay with local reinsurers
    F["acc_last"], F["ub_last"], F["nre_last"] = m.local_reinsurers_accepted_premium[y1], m.local_share_upper_bound[y1], int(m.local_reinsurers[y1])
    F["ub_max"], F["ub_max_year"] = m.local_share_upper_bound.max(), int(m.local_share_upper_bound.idxmax())
    F["acc_max"], F["acc_max_year"] = m.local_reinsurers_accepted_premium.max(), int(m.local_reinsurers_accepted_premium.idxmax())
    F["ceded_rising"] = bool(m.ceded_premium.is_monotonic_increasing)

    # local reinsurers
    seg = rr[(rr.company_id == "all_local_reinsurers") & (rr["class"] == "All classes")].set_index("year")
    F["re_profit_years"] = [int(y) for y in seg.index[seg.underwriting_result > 0]]
    F["re_loss_years"] = [int(y) for y in seg.index[seg.underwriting_result < 0]]
    F["re_uw_last"], F["re_cr_last"] = seg.underwriting_result[y1], seg.combined_ratio[y1]
    F["re_uw_total"] = seg.underwriting_result.sum()
    F["re_comm_first"], F["re_comm_last"] = seg.commission_ratio[y0], seg.commission_ratio[y1]
    F["re_lr_first"], F["re_lr_last"] = seg.loss_ratio[y0], seg.loss_ratio[y1]
    L = ["accepted_premium", "net_earned_premium", "claims_incurred", "commissions", "management_expenses", "underwriting_result"]
    pc = rr[(rr.company_id == "all_local_reinsurers") & (rr["class"] != "All classes")].groupby("class")[L].sum()
    pc["share"] = pc.accepted_premium / pc.accepted_premium.sum()
    pc["combined_ratio"] = (pc.claims_incurred + pc.commissions + pc.management_expenses) / pc.net_earned_premium
    best, worst = pc.underwriting_result.idxmax(), pc.underwriting_result.idxmin()
    F["re_best"] = (best, pc.underwriting_result[best], pc.share[best], pc.combined_ratio[best])
    F["re_worst"] = (worst, pc.underwriting_result[worst], pc.share[worst], pc.combined_ratio[worst])
    one = rr[(rr.company_id != "all_local_reinsurers") & (rr["class"] == "All classes")]
    F["re_names"] = sorted(short(n) for n in one.company_name.unique())
    big = one[one.year == y1].sort_values("accepted_premium", ascending=False).iloc[0]
    F["re_largest"] = (short(big.company_name), big.accepted_premium / seg.accepted_premium[y1], big.underwriting_result, big.combined_ratio)
    # reinsurers with an underwriting profit in every year they filed
    every = one.groupby("company_name").underwriting_result.apply(lambda v: bool((v > 0).all()))
    F["re_every_year"] = sorted(short(n) for n in every.index[every])
    F["re_direct"] = [(short(n), int(y)) for n, y in zip(rr[rr.filed_as_direct].company_name, rr[rr.filed_as_direct].year)]

    # Cedant Scorecard
    lk = ln.set_index("retention_group")
    F["link"] = {g: dict(n=int(v.insurer_years), med=v.median_score_without_retention, de=v.share_graded_d_or_e)
                 for g, v in lk.iterrows() if g != "All scored"}
    F["link_rho"], F["link_rho_ex"] = lk.spearman_retention_score["All scored"], lk.spearman_retention_score_without_retention["All scored"]
    F["sc_weight"], F["sc_total"], F["sc_metrics"] = int(ln.retention_weight.iloc[0]), int(ln.total_weight.iloc[0]), int(ln.scorecard_metrics.iloc[0])
    return F


def bn(v, nd=1):
    """KSh thousands to a KSh bn string."""
    return f"KSh {v / 1e6:,.{nd}f}bn"


def pct(v, nd=1):
    return f"{v * 100:.{nd}f}%"


def years_list(ys):
    """2018, 2019, 2025 and a run like 2020 to 2024 written as such."""
    ys, runs = sorted(ys), []
    for y in ys:
        if runs and y == runs[-1][1] + 1:
            runs[-1][1] = y
        else:
            runs.append([y, y])
    parts = []
    for a, b in runs:  # a run of three or more years is written as a span; shorter runs year by year
        parts += [f"every year from {a} to {b}"] if b - a >= 2 else [str(y) for y in range(a, b + 1)]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


WORDS = "zero one two three four five six seven eight nine ten".split()


def word(n):
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def check_words(F):
    """The prose says which way things point; stop the build if the data stops saying the same."""
    b = F["band_med"]
    assert F["motor_cr"] < 0.10 and F["cls"]["Aviation"]["cr"] > 0.90, "motor keeps almost all, aviation almost none"
    assert F["top2"] == ["Medical", "Fire Industrial"], F["top2"]
    assert F["cls"]["Medical"]["cr"] < 0.5 < F["cls"]["Fire Industrial"]["cr"], "medical mostly kept, fire industrial mostly ceded"
    assert b["KSh 3bn to 10bn"] < min(b["Under KSh 3bn"], b["Over KSh 10bn"]), "the middle band keeps the least"
    assert F["rho_max"] < 0, "larger insurers do not keep more"
    assert F["chg_fell"] > F["chg_rose"] and F["chg_median"] < 0
    assert F["rise_within_pts"] > F["rise_mix_pts"], "the largest rise came mostly from within classes"
    assert F["re_lr_last"] < F["re_lr_first"] and F["re_comm_last"] > F["re_comm_first"]
    assert F["re_uw_last"] < 0 and F["re_best"][1] > 0 > F["re_worst"][1]
    assert F["link"]["Under 50%"]["med"] > F["link"]["70% and over"]["med"] and F["link_rho_ex"] < 0
    assert F["ub_last"] < 0.5 and F["ub_max_year"] < F["last"], "more than half went elsewhere, and the ceiling fell"
    assert F["ceded_rising"], "cessions grew every year"
    return True


def readme_block(F):
    check_words(F)
    b = F["band_med"]
    lk = F["link"]
    lines = [
        START,
        "## Reinsurance flows",
        "",
        f"From {F['first']} to {F['last']} Kenya's general insurers passed {bn(F['ceded_total'])} of premium to reinsurers. "
        f"In {F['last']} they ceded {bn(F['ceded_last'])}, {pct(F['cr_last'])} of their gross premium; the rate has stayed between "
        f"{pct(F['cr_min'])} ({F['cr_min_year']}) and {pct(F['cr_max'])} ({F['cr_max_year']}).",
        "",
        f"**Where it goes out.** Motor keeps almost all of its premium (insurers cede {pct(F['motor_cr'])} of it); aviation keeps almost none "
        f"({pct(F['cls']['Aviation']['cr'])} ceded) and fire industrial cedes {pct(F['cls']['Fire Industrial']['cr'])}. "
        f"{F['top2'][0]} and {F['top2'][1].lower()} together make up {pct(F['top2_share'], 0)} of everything ceded in {F['last']}: "
        f"medical because it is the largest class, though only {pct(F['cls']['Medical']['cr'], 0)} of it is ceded, and fire industrial because most of it is.",
        "",
        f"**Who depends on it.** There is no simple size gradient. In {F['last']} insurers writing under KSh 3bn kept a median "
        f"{pct(b['Under KSh 3bn'], 0)} of their premium, those over KSh 10bn {pct(b['Over KSh 10bn'], 0)}, and those in between the least, "
        f"{pct(b['KSh 3bn to 10bn'], 0)}. The rank correlation between retention and size ran from {F['rho_min']:.2f} to {F['rho_max']:.2f} across the years.",
        "",
        f"**Does it move.** Of {F['chg_n']} insurers writing at least KSh 0.5bn in both {F['first']} and {F['last']}, {F['chg_fell']} keep less of their premium "
        f"than they did and {F['chg_rose']} keep more (median change {F['chg_median']:+.1f} points). The largest rise in the market rate came in "
        f"{F['rise_year']} (+{F['rise_pts']:.1f} points), {F['rise_within_pts']:.1f} points of it from insurers ceding more within classes, "
        f"{F['rise_top_class'].lower()} above all. The returns moved to IFRS 17 statements in {F['ifrs17_year']} but kept their premium lines: "
        f"insurers' cession rates moved by {F['ifrs17_abs']:.1f} points on average that year, against {F['other_abs_min']:.1f} to {F['other_abs_max']:.1f} in the others.",
        "",
        f"**How much could stay in Kenya.** The {word(F['nre_last'])} local reinsurers accepted {bn(F['acc_last'])} of premium in {F['last']}, so at most "
        f"{pct(F['ub_last'], 0)} of what Kenyan insurers ceded could have gone to them. It is an upper bound, not a measured flow: the local "
        f"reinsurers also write business from outside Kenya, and insurers cede abroad and to each other.",
        "",
        f"**How the local reinsurers fare.** {', '.join(F['re_names'][:-1])} and {F['re_names'][-1]} made an underwriting profit together in "
        f"{years_list(F['re_profit_years'])}, and lost money in {years_list(F['re_loss_years'])}: a loss of {bn(-F['re_uw_last'], 2)} in {F['last']}, "
        f"a combined ratio of {pct(F['re_cr_last'])}. Their loss ratio fell from {pct(F['re_lr_first'])} in {F['first']} to {pct(F['re_lr_last'])} in {F['last']}, "
        f"while the commission they pay back to insurers rose from {pct(F['re_comm_first'])} to {pct(F['re_comm_last'])} of earned premium. "
        f"Over {F['first']} to {F['last']} {F['re_best'][0].lower()} ({pct(F['re_best'][2], 0)} of their premium) made {bn(F['re_best'][1])} "
        f"and {F['re_worst'][0].lower()} ({pct(F['re_worst'][2], 0)}) lost {bn(-F['re_worst'][1])}, a combined ratio of {pct(F['re_worst'][3])}.",
        "",
        f"**Recoveries.** IRA's class tables and revenue accounts carry claims net of reinsurance only, so what insurers recover from "
        f"reinsurers cannot be measured from the returns, and the reinsurers' result on Kenyan business alone cannot be separated.",
        "",
        f"**The Cedant Scorecard.** Insurers that keep less than half their premium had a median score of {lk['Under 50%']['med']:.1f} on the "
        f"scorecard's other measures, against {lk['70% and over']['med']:.1f} for those keeping 70% or more (rank correlation {F['link_rho_ex']:.2f}, "
        f"{F['first']} to {F['last']}). It is a correlation, not a cause, and {pct(lk['Under 50%']['de'], 0)} of the low-retention years were still graded D or E.",
        END,
    ]
    return "\n".join(lines)


def page_data(F):
    cc, co, sg = read("reinsurance_class_cession.csv"), read("reinsurance_insurer_retention.csv"), read("reinsurance_size_gradient.csv")
    rc, mk, rr = read("reinsurance_retention_change.csv"), read("reinsurance_market.csv"), read("reinsurance_reinsurer_results.csv")
    ln = read("reinsurance_scorecard_link.csv")
    k = 1e3  # KSh thousands to KSh m
    market = [dict(y=int(x.year), gp=r(x.gross_premium / k, 1), ceded=r(x.ceded_premium / k, 1), cr=r(x.cession_rate), basis=x.basis,
                   med=r(x.median_change_from_prior_year), mabs=r(x.mean_abs_change_from_prior_year), acc=r(x.local_reinsurers_accepted_premium / k, 1),
                   ub=r(x.local_share_upper_bound), inw=r(x.insurers_inward_premium / k, 1), nre=int(x.local_reinsurers)) for _, x in mk.iterrows()]
    classes = {}
    for y, g in cc[cc["class"] != "All classes"].groupby("year"):
        classes[int(y)] = [dict(c=x["class"], gp=r(x.gross_premium / k, 1), ceded=r(x.ceded_premium / k, 1), cr=r(x.cession_rate),
                                sh=r(x.share_of_ceded), n=int(x.insurers)) for _, x in g.sort_values("cession_rate").iterrows()]
    insurers = {}
    for y, g in co.groupby("year"):
        insurers[int(y)] = [dict(id=x.company_id, name=short(x.company_name), sn=tiny(x.company_name), gp=r(x.gross_premium / k, 1), ret=r(x.retention),
                                 band=x.size_band, cmp=bool(x.compared)) for _, x in g.iterrows()]
    bands = {}
    for y, g in sg.groupby("year"):
        bands[int(y)] = [dict(b=x.size_band, n=int(x.insurers), med=r(x.median_retention), pooled=r(x.pooled_retention),
                              rho=r(x.spearman_retention_size, 3)) for _, x in g.iterrows()]
    y0, y1 = F["first"], F["last"]
    change = [dict(id=x.company_id, name=short(x.company_name), sn=tiny(x.company_name), r0=r(x[f"retention_{y0}"]), r1=r(x[f"retention_{y1}"]), d=r(x.change_points, 2),
                   gp0=r(x[f"gross_premium_{y0}"] / k, 1), gp1=r(x[f"gross_premium_{y1}"] / k, 1),
                   absorbed=None if pd.isna(x.absorbed) or not x.absorbed else short(x.absorbed)) for _, x in rc.iterrows()]
    re_ = {}
    tot = rr[rr["class"] == "All classes"]
    for cid, g in tot.groupby("company_id"):
        re_[cid] = dict(name="All local reinsurers" if cid == "all_local_reinsurers" else short(g.company_name.iloc[0]),
                        years=[dict(y=int(x.year), acc=r(x.accepted_premium / k, 1), nep=r(x.net_earned_premium / k, 1), uw=r(x.underwriting_result / k, 1),
                                    lr=r(x.loss_ratio), cmr=r(x.commission_ratio), er=r(x.expense_ratio), cr=r(x.combined_ratio))
                               for _, x in g.sort_values("year").iterrows()])
    L = ["accepted_premium", "net_earned_premium", "claims_incurred", "commissions", "management_expenses", "underwriting_result"]
    pc = rr[(rr.company_id == "all_local_reinsurers") & (rr["class"] != "All classes")].groupby("class")[L].sum()
    reclass = [dict(c=c, acc=r(x.accepted_premium / k, 1), uw=r(x.underwriting_result / k, 1), sh=r(x.accepted_premium / pc.accepted_premium.sum()),
                    lr=r(x.claims_incurred / x.net_earned_premium), cr=r((x.claims_incurred + x.commissions + x.management_expenses) / x.net_earned_premium))
               for c, x in pc.sort_values("underwriting_result").iterrows()]
    link = [dict(g=x.retention_group, n=int(x.insurer_years), ni=int(x.insurers), ret=r(x.median_retention), score=r(x.median_score, 2),
                 ex=r(x.median_score_without_retention, 2), de=r(x.share_graded_d_or_e)) for _, x in ln.iterrows()]
    js_f = {key: (list(v) if isinstance(v, tuple) else v) for key, v in F.items()}
    return dict(years=sorted(classes), market=market, classes=classes, insurers=insurers, bands=bands, change=change, re=re_,
                reclass=reclass, link=link, F=js_f, caveat=CAVEAT, caveat_re=CAVEAT_RE)


def clean(o):
    """Round floats and turn numpy types into plain Python, for a stable JSON."""
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if pd.isna(o) else round(float(o), 6)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def write_readme(F):
    s = open(README, encoding="utf-8").read()
    block = readme_block(F)
    if START in s:
        s = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda m: block, s, flags=re.S)
    else:
        anchor = "## See it"
        s = s.replace(anchor, block + "\n\n" + anchor, 1)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def main():
    F = facts()
    data = clean(page_data(F))
    js = json.dumps(data, separators=(",", ":"), ensure_ascii=True, sort_keys=True)
    tpl = open(os.path.join(PAGE, "reinsurance_template.html"), encoding="utf-8").read()
    body = tpl.replace("/*__DATA__*/null", js.replace("</", "<\\/"))
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>\n'
            + body + "\n</body></html>\n")
    with open(os.path.join(PAGE, "kenya-insurance-reinsurance-flows.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    write_readme(F)
    print(f"page {len(html) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
