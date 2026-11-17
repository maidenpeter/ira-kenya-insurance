"""Build page/kenya-insurance-reinsurance-flows.html from output/ and page/reinsurance_template.html, and
write the README's reinsurance section from the same figures.

    python src/reinsurance/build_page.py

facts() computes every number the page's text and the README quote, from the output files only, so the
tests can recompute them without the data repository. Ratios are recomputed here from the KSh columns and
passed on unrounded, so every figure is rounded once, where it is shown.
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
SEG = "all_local_reinsurers"


def r(v):
    return None if v is None or pd.isna(v) else float(v)


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


def ratio(a, b):
    return a / b.where(b > 0)


def read(name):
    """An output file, with every ratio recomputed from its KSh columns so nothing is rounded twice."""
    d = pd.read_csv(os.path.join(OUT, name))
    if name in ("reinsurance_class_cession.csv", "reinsurance_insurer_retention.csv", "reinsurance_market.csv"):
        d["cession_rate"] = ratio(d.ceded_premium, d.gross_premium)
    if name == "reinsurance_insurer_retention.csv":
        d["retention"] = ratio(d.net_premium, d.gross_premium)
    if name == "reinsurance_class_cession.csv":
        part = d["class"] != "All classes"
        d.loc[part, "share_of_ceded"] = d[part].ceded_premium / d[part].groupby("year").ceded_premium.transform("sum")
    if name == "reinsurance_market.csv":
        d["local_share_upper_bound"] = ratio(d.local_reinsurers_accepted_premium, d.ceded_premium).clip(upper=1)
    if name == "reinsurance_reinsurer_results.csv":
        n = d.net_earned_premium
        d["loss_ratio"], d["commission_ratio"] = ratio(d.claims_incurred, n), ratio(d.commissions, n)
        d["expense_ratio"] = ratio(d.management_expenses, n)
        d["combined_ratio"] = d.loss_ratio + d.commission_ratio + d.expense_ratio
    return d


def ksh_threshold(v):
    """KSh thousands as a threshold: 500000 -> 'KSh 0.5bn'."""
    b = v / 1e6
    return f"KSh {b:g}bn"


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
    av = cc[cc["class"] == "Aviation"]
    F["aviation_pooled"] = av.ceded_premium.sum() / av.gross_premium.sum()
    F["big_risks"] = ["Fire Industrial", "Engineering", "Aviation"]

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
    a, b = co[co.year == yr - 1], co[co.year == yr]
    both = set(a.company_id) & set(b.company_id)
    cr_of = lambda d: d.ceded_premium.sum() / d.gross_premium.sum()
    F["rise_same"] = (cr_of(b[b.company_id.isin(both)]) - cr_of(a[a.company_id.isin(both)])) * 100
    F["rise_comp"] = F["rise_pts"] - F["rise_same"]
    F["rise_top_cr0"], F["rise_top_cr1"] = p["cession_rate"][yr - 1][F["rise_top_class"]], p["cession_rate"][yr][F["rise_top_class"]]
    F["rise_top_is_largest"] = bool(p["gross_premium"][yr].idxmax() == F["rise_top_class"])

    # the IFRS 17 switch in the returns: how far insurers' cession rates moved that year, against every other year
    i17 = int(mk[mk.basis.str.contains("IFRS 17")].year.min())
    moves = mk.set_index("year").mean_abs_change_from_prior_year.dropna() * 100
    others = moves.drop(i17)
    F["ifrs17_year"] = i17
    F["ifrs17_abs"], F["ifrs17_med"] = moves[i17], m.median_change_from_prior_year[i17] * 100
    F["other_abs_min"], F["other_abs_max"] = others.min(), others.max()
    F["other_abs_max_year"] = int(others.idxmax())
    F["ifrs17_largest"] = bool(moves[i17] >= moves.max())
    F["move_years"] = len(moves)
    F["ifrs17_cr_change"] = (m.cession_rate[i17] - m.cession_rate[i17 - 1]) * 100

    # insurers IRA listed without a full-year return, and the largest of them by its premium the year before
    nf = {int(y): [n.strip() for n in str(v).split(";")] for y, v in mk.set_index("year").insurers_without_full_year_return.items()
          if isinstance(v, str) and v.strip()}
    F["nonfilers"] = {y: [short(n) for n in v] for y, v in nf.items()}
    byname = co.set_index(["company_name", "year"]).gross_premium
    big = max(((n, y, byname.get((n, y - 1), 0)) for y, v in nf.items() for n in v), key=lambda t: t[2])
    F["nonfiler_big"] = (short(big[0]), big[1], big[2], big[0])

    # size
    edges = sorted({float(v) for v in pd.concat([sg.lower_ksh_000, sg.upper_ksh_000]).dropna()})
    F["min_gp"] = float(sg.compare_threshold_ksh_000.iloc[0])
    F["band_edges"] = [e for e in edges if e > 0]
    cmp_ = co[co.compared]
    bands = [b for b in sg.size_band.unique() if b != "All compared"]
    F["bands"] = bands
    F["band_med"] = {b: cmp_[(cmp_.year == y1) & (cmp_.size_band == b)].retention.median() for b in bands}
    F["band_n"] = {b: int(((cmp_.year == y1) & (cmp_.size_band == b)).sum()) for b in bands}
    rho = sg[sg.size_band == "All compared"].spearman_retention_size
    F["rho_min"], F["rho_max"] = rho.min(), rho.max()
    cmp_last = cmp_[cmp_.year == y1].sort_values("retention")
    F["compared_last"] = len(cmp_last)
    F["lowest"] = [(short(n), v) for n, v in zip(cmp_last.company_name.head(3), cmp_last.retention.head(3))]
    F["median_retention_last"] = cmp_last.retention.median()

    # change from the first year to the last
    F["chg_n"], F["chg_fell"], F["chg_rose"] = len(rc), int((rc.change_points < 0).sum()), int((rc.change_points > 0).sum())
    F["chg_median"] = rc.change_points.median()
    lo, hi = rc.sort_values("change_points").iloc[0], rc.sort_values("change_points").iloc[-1]
    F["chg_low"] = (short(lo.company_name), lo[f"retention_{y0}"], lo[f"retention_{y1}"], lo.change_points)
    F["chg_high"] = (short(hi.company_name), hi[f"retention_{y0}"], hi[f"retention_{y1}"], hi.change_points)

    # what the reinsurers that file IRA's returns could have taken
    F["acc_last"], F["ub_last"], F["nre_last"] = m.local_reinsurers_accepted_premium[y1], m.local_share_upper_bound[y1], int(m.local_reinsurers[y1])
    F["ub_max"], F["ub_max_year"] = m.local_share_upper_bound.max(), int(m.local_share_upper_bound.idxmax())
    F["acc_max"], F["acc_max_year"] = m.local_reinsurers_accepted_premium.max(), int(m.local_reinsurers_accepted_premium.idxmax())
    F["ceded_rising"] = bool(m.ceded_premium.is_monotonic_increasing)
    F["nre_by_year"] = {int(y): int(v) for y, v in m.local_reinsurers.items()}

    # the local reinsurers
    seg = rr[(rr.company_id == SEG) & (rr["class"] == "All classes")].set_index("year")
    F["re_profit_years"] = [int(y) for y in seg.index[seg.underwriting_result > 0]]
    F["re_loss_years"] = [int(y) for y in seg.index[seg.underwriting_result < 0]]
    F["re_uw_last"], F["re_cr_last"] = seg.underwriting_result[y1], seg.combined_ratio[y1]
    F["re_comm_first"], F["re_comm_last"] = seg.commission_ratio[y0], seg.commission_ratio[y1]
    F["re_lr_first"], F["re_lr_last"] = seg.loss_ratio[y0], seg.loss_ratio[y1]
    F["re_comm_rise"] = (F["re_comm_last"] - F["re_comm_first"]) * 100
    F["re_lr_fall"] = (F["re_lr_first"] - F["re_lr_last"]) * 100
    L = ["accepted_premium", "net_earned_premium", "claims_incurred", "commissions", "management_expenses", "underwriting_result"]
    pc = rr[(rr.company_id == SEG) & (rr["class"] != "All classes")].groupby("class")[L].sum()
    pc["share"] = pc.accepted_premium / pc.accepted_premium.sum()
    pc["combined_ratio"] = (pc.claims_incurred + pc.commissions + pc.management_expenses) / pc.net_earned_premium
    best, worst = pc.underwriting_result.idxmax(), pc.underwriting_result.idxmin()
    F["re_best"] = (best, pc.underwriting_result[best], pc.share[best], pc.combined_ratio[best])
    F["re_worst"] = (worst, pc.underwriting_result[worst], pc.share[worst], pc.combined_ratio[worst])
    one = rr[(rr.company_id != SEG) & (rr["class"] == "All classes")]
    first_year = one.groupby("company_name").year.min()
    F["re_names"] = sorted(short(n) for n in first_year.index)
    F["re_joined"] = {short(n): int(y) for n, y in first_year.items() if y > y0}
    big = one[one.year == y1].sort_values("accepted_premium", ascending=False).iloc[0]
    F["re_largest"] = (short(big.company_name), big.accepted_premium / seg.accepted_premium[y1], big.underwriting_result, big.combined_ratio)
    every = one.groupby("company_name").underwriting_result.apply(lambda v: bool((v > 0).all()))
    F["re_every_year"] = sorted(short(n) for n in every.index[every])
    F["re_direct"] = [(short(n), int(y)) for n, y in zip(rr[rr.filed_as_direct].company_name, rr[rr.filed_as_direct].year)]

    # Cedant Scorecard
    lk = ln.set_index("retention_group")
    groups = [g for g in ln.retention_group if g != "All scored"]
    F["groups"] = groups
    F["link"] = {g: dict(n=int(lk.insurer_years[g]), med=lk.median_score_without_retention[g], de=lk.share_graded_d_or_e[g]) for g in groups}
    F["link_rho"], F["link_rho_ex"] = lk.spearman_retention_score["All scored"], lk.spearman_retention_score_without_retention["All scored"]
    F["low_group_de_most"] = bool(lk.share_graded_d_or_e[groups[0]] >= max(lk.share_graded_d_or_e[g] for g in groups))
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


def and_list(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


WORDS = "zero one two three four five six seven eight nine ten".split()


def word(n):
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def band_text(b):
    return b[0].lower() + b[1:] if b.startswith(("Under", "Over")) else b


def check_words(F):
    """The prose says which way things point; stop the build if the data stops saying the same."""
    b, bands = F["band_med"], F["bands"]
    assert F["motor_cr"] < 0.10 and F["cls"]["Aviation"]["cr"] > 0.90, "motor keeps almost all, aviation almost none"
    assert all(F["cls"][c]["cr"] > 0.70 for c in F["big_risks"]), "the large commercial risks are mostly ceded"
    assert F["top2"] == ["Medical", "Fire Industrial"], F["top2"]
    assert F["cls"]["Medical"]["cr"] < 0.5 < F["cls"]["Fire Industrial"]["cr"], "medical mostly kept, fire industrial mostly ceded"
    assert len(bands) == 3 and b[bands[1]] < min(b[bands[0]], b[bands[2]]), "the middle band keeps the least"
    assert F["rho_max"] < 0, "larger insurers do not keep more"
    assert F["chg_fell"] > F["chg_rose"] and F["chg_median"] < 0
    assert F["rise_same"] > F["rise_comp"] > 0, "the insurers that filed in both years account for most of the rise"
    assert F["rise_top_cr1"] > F["rise_top_cr0"] and F["rise_top_is_largest"], "the class named rose, and it is the largest class"
    assert F["cls"]["Medical"]["cr"] < F["cr_last"], "only a small share of medical goes out, less than the market's"
    assert abs(F["ifrs17_med"]) < 1, "no systematic shift in the IFRS 17 year"
    assert F["re_lr_last"] < F["re_lr_first"] and F["re_comm_rise"] > F["re_lr_fall"] > 0, "commission rose by more than the loss ratio fell"
    assert F["re_uw_last"] < 0 and F["re_best"][1] > 0 > F["re_worst"][1]
    assert F["link"][F["groups"][0]]["med"] > F["link"][F["groups"][-1]]["med"] and F["link_rho_ex"] < 0
    assert F["ub_last"] < 0.5 and F["ub_max_year"] < F["last"], "more than half went elsewhere, and the ceiling fell"
    assert F["ceded_rising"], "cessions grew every year"
    return True


def ifrs17_sentence(F):
    s = (f"The returns moved to IFRS 17 statements in {F['ifrs17_year']} but kept their premium lines, and there is no systematic shift that year: "
         f"among insurers writing at least {ksh_threshold(F['min_gp'])} in both years, the median cession rate moved {F['ifrs17_med']:+.1f} points. "
         f"The average size of their moves, {F['ifrs17_abs']:.1f} points in either direction, ")
    if F["ifrs17_largest"]:
        close = F["ifrs17_abs"] - F["other_abs_max"] < 1
        return s + (f"was the largest of the {word(F['move_years'])} years"
                    + (f", though close to {F['other_abs_max_year']}'s {F['other_abs_max']:.1f}" if close else "")
                    + "; the series is treated as unbroken and the switch is marked.")
    return s + f"was within the {F['other_abs_min']:.1f} to {F['other_abs_max']:.1f} of the other years; the series is treated as unbroken and the switch is marked."


def reinsurers_text(F):
    names = [n + (f" (from {F['re_joined'][n]})" if n in F["re_joined"] else "") for n in F["re_names"]]
    return and_list(names)


def readme_block(F):
    check_words(F)
    b, bands, g, lk = F["band_med"], F["bands"], F["groups"], F["link"]
    nb = F["nonfiler_big"]
    de_others = " and ".join(f"{pct(lk[x]['de'], 0)} ({band_text(x)})" for x in g[1:])
    lines = [
        START,
        "## Reinsurance flows",
        "",
        f"From {F['first']} to {F['last']} Kenya's general insurers passed {bn(F['ceded_total'])} of premium to reinsurers. "
        f"In {F['last']} they ceded {bn(F['ceded_last'])}, {pct(F['cr_last'])} of their gross premium; the rate has stayed between "
        f"{pct(F['cr_min'])} ({F['cr_min_year']}) and {pct(F['cr_max'])} ({F['cr_max_year']}). Insurers IRA listed with an all-zero full-year return "
        f"are left out of that year, and the page names them; the largest gap is in {nb[1]}, an insurer that wrote {bn(nb[2])} in {nb[1] - 1}.",
        "",
        f"**Where it goes out.** Motor keeps almost all of its premium (insurers cede {pct(F['motor_cr'])} of it); aviation keeps almost none "
        f"({pct(F['cls']['Aviation']['cr'])} ceded) and fire industrial cedes {pct(F['cls']['Fire Industrial']['cr'])}. "
        f"{F['top2'][0]} and {F['top2'][1].lower()} together make up {pct(F['top2_share'])} of everything ceded in {F['last']}: "
        f"medical because it is the largest class, though only {pct(F['cls']['Medical']['cr'], 0)} of it is ceded, and fire industrial because most of it is.",
        "",
        f"**Who depends on it.** There is no simple size gradient. In {F['last']} insurers writing {band_text(bands[0])} kept a median "
        f"{pct(b[bands[0]], 0)} of their premium, those {band_text(bands[2])} {pct(b[bands[2]], 0)}, and those in between the least, "
        f"{pct(b[bands[1]], 0)}. The rank correlation between retention and size ran from {F['rho_min']:.2f} to {F['rho_max']:.2f} across the years, "
        "a weak relationship.",
        "",
        f"**Does it move.** Of {F['chg_n']} insurers writing at least {ksh_threshold(F['min_gp'])} in both {F['first']} and {F['last']}, {F['chg_fell']} keep "
        f"less of their premium than they did and {F['chg_rose']} keep more (median change {F['chg_median']:+.1f} points). The largest rise in the market "
        f"rate came in {F['rise_year']} (+{F['rise_pts']:.1f} points). Insurers that filed in both years account for {F['rise_same']:.1f} points of it, "
        f"and the rest reflects which insurers filed; {F['rise_top_class'].lower()}, the largest class, went from ceding {pct(F['rise_top_cr0'])} to "
        f"{pct(F['rise_top_cr1'])}. {ifrs17_sentence(F)}",
        "",
        f"**How much could go to the local reinsurers.** The {word(F['nre_last'])} reinsurers that file IRA's returns accepted {bn(F['acc_last'])} of "
        f"premium in {F['last']}, so at most {pct(F['ub_last'], 0)} of what Kenyan insurers ceded could have gone to them. It is an upper bound, not "
        "a measured flow: they also accept business from outside Kenya, and insurers also cede to reinsurers that do not file these returns "
        "(abroad, and the regional reinsurers that operate in Kenya under regional charters) and to each other.",
        "",
        f"**How the local reinsurers fare.** Together, {reinsurers_text(F)} made an underwriting profit in "
        f"{years_list(F['re_profit_years'])}, and lost money in {years_list(F['re_loss_years'])}: a loss of {bn(-F['re_uw_last'], 2)} in {F['last']}, "
        f"a combined ratio of {pct(F['re_cr_last'])}. Their loss ratio fell from {pct(F['re_lr_first'])} in {F['first']} to {pct(F['re_lr_last'])} in {F['last']}, "
        f"{F['re_lr_fall']:.1f} points, while their net commission (commission and brokerage paid, less commission received) rose from "
        f"{pct(F['re_comm_first'])} to {pct(F['re_comm_last'])} of earned premium, {F['re_comm_rise']:.1f} points. "
        f"Over {F['first']} to {F['last']} {F['re_best'][0].lower()} ({pct(F['re_best'][2], 0)} of their premium) made {bn(F['re_best'][1])} "
        f"and {F['re_worst'][0].lower()} ({pct(F['re_worst'][2], 0)}) lost {bn(-F['re_worst'][1])}, a combined ratio of {pct(F['re_worst'][3])}.",
        "",
        "**Recoveries.** IRA's class tables and revenue accounts carry claims net of reinsurance only, so what insurers recover from their "
        "reinsurers cannot be measured. Separately, the reinsurers' returns do not split their business by where it comes from, so their result "
        "on Kenyan cessions alone cannot be measured either.",
        "",
        f"**The Cedant Scorecard.** Insurers keeping {band_text(g[0])} of their premium had a median score of {lk[g[0]]['med']:.1f} on the "
        f"scorecard's other measures, against {lk[g[-1]]['med']:.1f} for those keeping {g[-1]} (rank correlation {F['link_rho_ex']:.2f}, "
        f"{F['first']} to {F['last']}). It is a correlation, not a cause, and the same group "
        + ("was also graded D or E most often: " if F["low_group_de_most"] else "was graded D or E in ")
        + f"{pct(lk[g[0]]['de'], 0)} of its insurer-years, against {de_others}.",
        END,
    ]
    return "\n".join(lines)


def page_data(F):
    cc, co, sg = read("reinsurance_class_cession.csv"), read("reinsurance_insurer_retention.csv"), read("reinsurance_size_gradient.csv")
    rc, mk, rr = read("reinsurance_retention_change.csv"), read("reinsurance_market.csv"), read("reinsurance_reinsurer_results.csv")
    ln = read("reinsurance_scorecard_link.csv")
    k = 1e3  # KSh thousands to KSh m
    market = [dict(y=int(x.year), gp=r(x.gross_premium / k), ceded=r(x.ceded_premium / k), cr=r(x.cession_rate), basis=x.basis,
                   med=r(x.median_change_from_prior_year), mabs=r(x.mean_abs_change_from_prior_year), acc=r(x.local_reinsurers_accepted_premium / k),
                   ub=r(x.local_share_upper_bound), inw=r(x.insurers_inward_premium / k), nre=int(x.local_reinsurers),
                   nf=F["nonfilers"].get(int(x.year), [])) for _, x in mk.iterrows()]
    classes = {}
    for y, g in cc[cc["class"] != "All classes"].groupby("year"):
        classes[int(y)] = [dict(c=x["class"], gp=r(x.gross_premium / k), ceded=r(x.ceded_premium / k), cr=r(x.cession_rate),
                                sh=r(x.share_of_ceded), n=int(x.insurers)) for _, x in g.sort_values(["cession_rate", "class"]).iterrows()]
    insurers = {}
    for y, g in co.groupby("year"):
        insurers[int(y)] = [dict(id=x.company_id, name=short(x.company_name), sn=tiny(x.company_name), gp=r(x.gross_premium / k), ret=r(x.retention),
                                 band=x.size_band, cmp=bool(x.compared)) for _, x in g.iterrows()]
    bands = {}
    for y, g in sg.groupby("year"):
        c = co[(co.year == y) & co.compared]
        bands[int(y)] = [dict(b=x.size_band, n=int(x.insurers),
                              med=r(c.retention.median() if x.size_band == "All compared" else c[c.size_band == x.size_band].retention.median()),
                              rho=r(x.spearman_retention_size)) for _, x in g.iterrows()]
    y0, y1 = F["first"], F["last"]
    change = [dict(id=x.company_id, name=short(x.company_name), sn=tiny(x.company_name), r0=r(x[f"retention_{y0}"]), r1=r(x[f"retention_{y1}"]),
                   d=r(x.change_points), gp0=r(x[f"gross_premium_{y0}"] / k), gp1=r(x[f"gross_premium_{y1}"] / k),
                   absorbed=None if pd.isna(x.absorbed) or not x.absorbed else short(x.absorbed)) for _, x in rc.iterrows()]
    re_ = {}
    tot = rr[rr["class"] == "All classes"]
    for cid, g in tot.groupby("company_id"):
        re_[cid] = dict(name="All local reinsurers" if cid == SEG else short(g.company_name.iloc[0]),
                        years=[dict(y=int(x.year), acc=r(x.accepted_premium / k), nep=r(x.net_earned_premium / k), uw=r(x.underwriting_result / k),
                                    lr=r(x.loss_ratio), cmr=r(x.commission_ratio), er=r(x.expense_ratio), cr=r(x.combined_ratio))
                               for _, x in g.sort_values("year").iterrows()])
    L = ["accepted_premium", "net_earned_premium", "claims_incurred", "commissions", "management_expenses", "underwriting_result"]
    pc = rr[(rr.company_id == SEG) & (rr["class"] != "All classes")].groupby("class")[L].sum()
    reclass = [dict(c=c, acc=r(x.accepted_premium / k), uw=r(x.underwriting_result / k), sh=r(x.accepted_premium / pc.accepted_premium.sum()),
                    lr=r(x.claims_incurred / x.net_earned_premium), cr=r((x.claims_incurred + x.commissions + x.management_expenses) / x.net_earned_premium))
               for c, x in pc.sort_values("underwriting_result").iterrows()]
    link = [dict(g=x.retention_group, n=int(x.insurer_years), ni=int(x.insurers), ret=r(x.median_retention), score=r(x.median_score),
                 ex=r(x.median_score_without_retention), de=r(x.share_graded_d_or_e)) for _, x in ln.iterrows()]
    js_f = {key: (list(v) if isinstance(v, tuple) else v) for key, v in F.items()}
    return dict(years=sorted(classes), market=market, classes=classes, insurers=insurers, bands=bands, change=change, re=re_,
                reclass=reclass, link=link, F=js_f, caveat=CAVEAT, caveat_re=CAVEAT_RE, ifrs17=ifrs17_sentence(F))


def clean(o):
    """Plain Python types for a stable JSON. Floats keep twelve significant figures: enough that the page rounds once."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if pd.isna(o) else float(f"{float(o):.12g}") + 0.0
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


def page_json(F):
    return json.dumps(clean(page_data(F)), separators=(",", ":"), ensure_ascii=True, sort_keys=True)


def main():
    F = facts()
    js = page_json(F)
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
