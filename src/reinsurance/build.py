"""How much risk Kenyan general insurers pass to reinsurers, who depends on it most, and how Kenya's own
reinsurers fare on what they accept. Full years 2018 to 2025.

Reads the class panel and revenue panel from ira-kenya-data (IRA_DATA_DIR, default ../ira-kenya-data),
the P&L basis from general_profit_loss.csv, and the Cedant Scorecard from ira-kenya-reinsurance
(IRA_REINSURANCE_DIR, default ../ira-kenya-reinsurance). Writes to output/:

  reinsurance_class_cession.csv     insurers, by class and year: gross premium, net premium, premium ceded,
                                    cession rate and each class's share of all premium ceded
  reinsurance_insurer_retention.csv every insurer and year: gross, net and ceded premium, retention, size
                                    band, the revenue account's outward reinsurance and the gap between them
  reinsurance_size_gradient.csv     retention by size band each year, and the rank correlation between
                                    retention and size
  reinsurance_retention_change.csv  each insurer's retention in 2018 and 2025
  reinsurance_market.csv            per year: premium ceded and cession rate for the market, the return basis
                                    (IFRS 4 or IFRS 17), how far insurers' cession rates moved from the year
                                    before, the local reinsurers' accepted premium against what insurers ceded,
                                    and the insurers IRA listed that year without a full-year return
  reinsurance_reinsurer_results.csv each local reinsurer, and all of them together, by class and year:
                                    premium accepted, earned premium, claims, commissions, expenses, result
                                    and the ratios on earned premium
  reinsurance_scorecard_link.csv    insurers grouped by retention, against the Cedant Scorecard's score and
                                    against the same score with the retention metric taken out

Definitions (all KSh thousands, Q4 year to date):
  gross premium  the class table's gross premium income, which is gross direct plus inward premium
  net premium    the class table's net premium income
  ceded          gross premium less net premium; it reconciles to the revenue account's outward reinsurance
  cession rate   ceded over gross premium; retention is net over gross premium, one less the cession rate

Insurers are the insurer segment, micro insurers included, as module 1 counts the market. Reinsurers are the
reinsurer segment. The segment is taken from the company crosswalk, not from the panels, because the class panel
tags the reinsurers' Q4 2025 gross direct and inward premium rows as insurer rows. An insurer IRA lists with an
all-zero fourth-quarter return has no full-year figures and is left out of that year; the market file names them. Motor Commercial PSV is folded into Motor Commercial, as in module 1. A company listed with
an all-zero return (it did not file, or its book had passed to another company) is left out, so a merged
company is counted once in each year.

Claims in IRA's class tables and revenue accounts are net of reinsurance (class incurred claims equal the
revenue account's net incurred claims for every company and year), and no gross claims are published. What
insurers recover from reinsurers cannot be measured from the returns, so it is not shown.

The returns moved the P&L and balance sheet to IFRS 17 lines from Q1 2024. The revenue account and class
tables kept their premium lines, so premium ceded is on one definition throughout; the market file shows
how far insurers' cession rates moved across the switch next to every other year.

Local reinsurers' accepted premium against insurers' premium ceded is an upper bound on the share those five
reinsurers could have taken, not a measured flow: they also accept business from outside Kenya, and insurers cede
to reinsurers that do not file these returns (abroad, and the regional reinsurers that operate in Kenya under
regional charters) and to each other.
"""
import importlib.util
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.environ.get("IRA_DATA_DIR", os.path.join(ROOT, "..", "ira-kenya-data"))
REINS = os.environ.get("IRA_REINSURANCE_DIR", os.path.join(ROOT, "..", "ira-kenya-reinsurance"))
OUT = os.path.join(ROOT, "output")
YEARS = list(range(2018, 2026))
CHANGE = (2018, 2025)
LINES = ["gross_premium", "net_premium", "net_earned_premium", "claims_incurred", "commissions",
         "management_expenses", "underwriting_result"]
CLASS_MAP = {"Motor Commercial PSV": "Motor Commercial"}
ABSORBED = {"saham": "mua"}  # absorbed company -> the insurer that took its book, where both filed in 2018
MIN_GP = 500_000  # KSh 0.5bn, the Cedant Scorecard's peer threshold, before an insurer's retention is compared
BANDS = [(0, 3_000_000, "Under KSh 3bn"), (3_000_000, 10_000_000, "KSh 3bn to 10bn"), (10_000_000, np.inf, "Over KSh 10bn")]
RET_GROUPS = [(0, 0.5, "Under 50%"), (0.5, 0.7, "50% to 70%"), (0.7, 1.01, "70% and over")]
TOL = 5  # KSh 5,000: rounding in IRA's tables


def ratios(d):
    d = d.copy()
    n = d.net_earned_premium.where(d.net_earned_premium > 0)
    d["loss_ratio"] = d.claims_incurred / n
    d["commission_ratio"] = d.commissions / n
    d["expense_ratio"] = d.management_expenses / n
    d["combined_ratio"] = d.loss_ratio + d.commission_ratio + d.expense_ratio
    return d


def cession(d):
    d = d.copy()
    d["ceded_premium"] = d.gross_premium - d.net_premium
    g = d.gross_premium.where(d.gross_premium > 0)
    d["cession_rate"] = d.ceded_premium / g
    d["retention"] = d.net_premium / g
    return d


def band(gp):
    return next(name for lo, hi, name in BANDS if lo <= gp < hi)


def group(r):
    return next(name for lo, hi, name in RET_GROUPS if lo <= r < hi)


def load():
    cw = pd.read_csv(os.path.join(DATA, "reference", "company_crosswalk.csv")).drop_duplicates("company_id").set_index("company_id")
    names, segs = cw.company_name, cw.segment
    c = pd.read_csv(os.path.join(DATA, "data", "processed", "general_by_class_panel.csv"))
    c = c[(c.quarter == 4) & c.year.isin(YEARS) & c.table.isin(LINES) & (c.class_of_business != "Total")]
    c = c.assign(segment=c.company_id.map(segs))
    c = c.assign(**{"class": c.class_of_business.replace(CLASS_MAP)})
    cl = c.pivot_table(index=["segment", "company_id", "year", "class"], columns="table", values="ytd_ksh_000",
                       aggfunc="sum").reindex(columns=LINES).fillna(0).reset_index()
    cl = cl[cl[LINES].abs().sum(axis=1) > 0]
    rp = pd.read_csv(os.path.join(DATA, "data", "processed", "general_revenue_panel.csv"))
    rp = rp[(rp.quarter == 4) & rp.year.isin(YEARS)]
    rp = rp.assign(segment=rp.company_id.map(segs))
    rv = rp.pivot_table(index=["segment", "company_id", "year"], columns="line", values="ytd_ksh_000", aggfunc="sum")
    flags = rp.drop_duplicates(["company_id", "year"]).set_index(["company_id", "year"]).quality_flags \
        if "quality_flags" in rp.columns else None
    pl = pd.read_csv(os.path.join(DATA, "data", "processed", "general_profit_loss.csv"), usecols=["year", "quarter", "reporting_basis"])
    basis = pl[pl.quarter == 4].groupby("year").reporting_basis.agg(lambda s: "/".join(sorted(s.dropna().unique())))
    # insurers IRA listed with an all-zero fourth-quarter return, other than a company whose book had passed to another
    qf = pd.read_csv(os.path.join(DATA, "validation", "quality_flags.csv"))
    nf = qf[(qf.quarter == 4) & (qf.flag == "not_filed") & qf.year.isin(YEARS) & (qf.company_id.map(segs) == "insurer")]
    ee = pd.read_csv(os.path.join(ROOT, "reference", "entries_exits.csv"))
    gone = ee[ee.kind == "merger"].set_index("company_id").year_in_data
    nf = nf[~(nf.company_id.isin(gone.index) & (nf.year > nf.company_id.map(gone)))]
    missing = nf.groupby("year").company_id.agg(lambda s: sorted(s))
    return cl, rv, flags, names, basis, missing


def tidy(d):
    """Round floats to six places and turn -0.0 into 0.0, so the files are the same on every platform."""
    d = d.copy()
    for col in d.columns:
        if d[col].dtype.kind == "f":
            d[col] = d[col].round(6) + 0.0
    return d


def scorecard_rules():
    """The Cedant Scorecard's metric weights and pillars, read from its own code so they cannot drift."""
    spec = importlib.util.spec_from_file_location("score", os.path.join(REINS, "src", "scorecard", "score.py"))
    sm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sm)
    return sm


def main(out=OUT, quiet=False):
    cl, rv, flags, names, basis, missing = load()
    ins = cl[cl.segment == "insurer"].drop(columns="segment")
    re_ = cl[cl.segment == "reinsurer"].drop(columns="segment")

    # 1. cession by class and year, insurers
    cc = cession(ins.groupby(["year", "class"])[["gross_premium", "net_premium"]].sum().reset_index())
    allc = cession(ins.groupby("year")[["gross_premium", "net_premium"]].sum().reset_index().assign(**{"class": "All classes"}))
    cc["insurers"] = ins[ins.gross_premium > 0].groupby(["year", "class"]).company_id.nunique() \
        .reindex(pd.MultiIndex.from_frame(cc[["year", "class"]])).fillna(0).astype(int).values
    allc["insurers"] = ins[ins.gross_premium > 0].groupby("year").company_id.nunique().reindex(allc.year).values
    cc["share_of_ceded"] = cc.ceded_premium / cc.groupby("year").ceded_premium.transform("sum")
    allc["share_of_ceded"] = 1.0
    cc = pd.concat([cc, allc], ignore_index=True)[["year", "class", "insurers", "gross_premium", "net_premium",
                                                   "ceded_premium", "cession_rate", "share_of_ceded"]]
    cc["outside_0_1"] = (cc.gross_premium > 0) & ~cc.cession_rate.between(0, 1)

    # 2. every insurer and year, reconciled to the revenue account
    co = cession(ins.groupby(["company_id", "year"])[["gross_premium", "net_premium"]].sum().reset_index())
    co = co[co.gross_premium > 0]
    r = rv.xs("insurer", level="segment")
    co["outward_reinsurance"] = r.outward_reinsurance.reindex(pd.MultiIndex.from_frame(co[["company_id", "year"]])).values
    co["reconcile_gap"] = co.ceded_premium - co.outward_reinsurance
    idx = pd.MultiIndex.from_frame(co[["company_id", "year"]])
    co["revenue_gross_premium"] = (r.gross_direct_premium.fillna(0) + r.inward_reinsurance.fillna(0)).reindex(idx).values
    co["revenue_net_premium"] = r.net_premium_written.reindex(idx).values
    co["size_band"] = co.gross_premium.map(band)
    co["compared"] = co.gross_premium >= MIN_GP
    if flags is not None:
        co["quality_flags"] = flags.reindex(pd.MultiIndex.from_frame(co[["company_id", "year"]])).values
    co.insert(1, "company_name", co.company_id.map(names))
    co["note"] = np.where(~co.retention.between(0, 1), "retention outside 0 to 1: net premium above gross or below zero", "")
    co = co.sort_values(["year", "gross_premium"], ascending=[True, False])

    # 3. size gradient
    sg = []
    for y, g in co[co.compared].groupby("year"):
        for _, _, b in BANDS:
            h = g[g.size_band == b]
            if len(h):
                sg.append(dict(year=y, size_band=b, insurers=len(h), median_retention=h.retention.median(),
                               pooled_retention=h.net_premium.sum() / h.gross_premium.sum(), gross_premium=h.gross_premium.sum()))
        sg.append(dict(year=y, size_band="All compared", insurers=len(g), median_retention=g.retention.median(),
                       pooled_retention=g.net_premium.sum() / g.gross_premium.sum(), gross_premium=g.gross_premium.sum(),
                       spearman_retention_size=g.retention.rank().corr(g.gross_premium.rank())))
    sg = pd.DataFrame(sg)
    edges = {name: (lo, hi) for lo, hi, name in BANDS}
    sg["lower_ksh_000"] = sg.size_band.map(lambda b: edges.get(b, (MIN_GP, None))[0])
    sg["upper_ksh_000"] = sg.size_band.map(lambda b: edges.get(b, (None, np.inf))[1]).replace(np.inf, np.nan)
    sg["compare_threshold_ksh_000"] = MIN_GP

    # 4. retention 2018 against 2025, pro forma where an insurer absorbed one that filed in 2018
    a, b = CHANGE
    pf = co.assign(company_id=co.company_id.replace(ABSORBED)).groupby(["company_id", "year"])[["gross_premium", "net_premium"]].sum()
    pf = cession(pf.reset_index())
    w = pf.pivot(index="company_id", columns="year", values=["gross_premium", "retention"])
    rc = pd.DataFrame({"gross_premium_" + str(a): w["gross_premium"][a], "gross_premium_" + str(b): w["gross_premium"][b],
                       "retention_" + str(a): w["retention"][a], "retention_" + str(b): w["retention"][b]}).dropna()
    rc = rc[(rc["gross_premium_" + str(a)] >= MIN_GP) & (rc["gross_premium_" + str(b)] >= MIN_GP)]
    rc["change_points"] = (rc["retention_" + str(b)] - rc["retention_" + str(a)]) * 100
    rc["absorbed"] = [", ".join(names[k] for k, v in ABSORBED.items() if v == i) for i in rc.index]
    rc = rc.reset_index()
    rc.insert(1, "company_name", rc.company_id.map(names))
    rc = rc.sort_values("change_points")

    # 5. market by year: cession, basis, movement, and the local reinsurers' capacity
    mk = allc[["year", "gross_premium", "net_premium", "ceded_premium", "cession_rate"]].copy()
    mk["basis"] = mk.year.map(basis)
    piv = co[co.compared].pivot(index="company_id", columns="year", values="cession_rate")
    mv = {y: (piv[y] - piv[y - 1]).dropna() for y in YEARS[1:]}
    mk["insurers_both_years"] = mk.year.map(lambda y: len(mv[y]) if y in mv else np.nan)
    mk["median_change_from_prior_year"] = mk.year.map(lambda y: mv[y].median() if y in mv else np.nan)
    mk["mean_abs_change_from_prior_year"] = mk.year.map(lambda y: mv[y].abs().mean() if y in mv else np.nan)
    ri = rv.xs("insurer", level="segment").groupby(level="year").inward_reinsurance.sum()
    rr = rv.xs("reinsurer", level="segment")
    acc = (rr.gross_direct_premium.fillna(0) + rr.inward_reinsurance.fillna(0)).groupby(level="year").sum()
    mk["insurers_inward_premium"] = mk.year.map(ri)
    mk["local_reinsurers"] = mk.year.map(rr.groupby(level="year").size())
    mk["local_reinsurers_accepted_premium"] = mk.year.map(acc)
    mk["local_share_upper_bound"] = (mk.local_reinsurers_accepted_premium / mk.ceded_premium).clip(upper=1)
    mk["insurers_without_full_year_return"] = mk.year.map(lambda y: "; ".join(names.get(i, i) for i in missing.get(y, [])))

    # 6. local reinsurers: by reinsurer, class and year, and all of them together
    rcl = re_.copy()
    rcl_tot = rcl.groupby(["company_id", "year"])[LINES].sum().reset_index().assign(**{"class": "All classes"})
    seg = rcl.groupby(["year", "class"])[LINES].sum().reset_index().assign(company_id="all_local_reinsurers")
    seg_tot = rcl.groupby("year")[LINES].sum().reset_index().assign(company_id="all_local_reinsurers", **{"class": "All classes"})
    res = ratios(pd.concat([rcl, rcl_tot, seg, seg_tot], ignore_index=True))
    res.insert(1, "company_name", res.company_id.map(names).fillna("All local reinsurers"))
    res = res[["company_id", "company_name", "year", "class"] + LINES + ["loss_ratio", "commission_ratio", "expense_ratio", "combined_ratio"]]
    res = res.rename(columns={"gross_premium": "accepted_premium"}).sort_values(["company_id", "year", "class"])
    # a reinsurer that filed its inward premium as direct premium (the revenue account shows which)
    direct = set(rr[(rr.gross_direct_premium.fillna(0) > 0) & (rr.inward_reinsurance.fillna(0) == 0)].index)
    res["filed_as_direct"] = [(c, y) in direct and k == "All classes" for c, y, k in zip(res.company_id, res.year, res["class"])]

    # 7. Cedant Scorecard: retention against the score, and the score without its retention metric
    sc = pd.read_csv(os.path.join(REINS, "output", "cedant_scorecard.csv"))
    sc = sc[sc.year.isin(YEARS)].copy()
    sm = scorecard_rules()
    pillars = list(sm.PILLARS)
    pw = {p: sum(wt for _, pp, wt, _ in sm.METRICS if pp == p) for p in pillars}
    # business profile without retention: scale and diversification only, at their own weights
    bp = [(n, wt) for n, pp, wt, _ in sm.METRICS if pp == "business_profile" and n != "retention"]
    num = sum(sc["pct_" + n].fillna(0) * wt for n, wt in bp)
    den = sum(sc["pct_" + n].notna() * wt for n, wt in bp)
    bp_ex = num / den.replace(0, np.nan)
    pw_ex = dict(pw, business_profile=pw["business_profile"] - next(wt for n, _, wt, _ in sm.METRICS if n == "retention"))
    pil = {p: (bp_ex if p == "business_profile" else sc["pillar_" + p]) for p in pillars}
    sc["score_without_retention"] = sum(pil[p].fillna(0) * pw_ex[p] for p in pillars) / sum(pil[p].notna() * pw_ex[p] for p in pillars)
    sc["retention_group"] = sc.retention.map(group)
    sc["d_or_e"] = sc.grade.isin(["D", "E"])
    link = []
    for gname in [g for _, _, g in RET_GROUPS]:
        h = sc[sc.retention_group == gname]
        link.append(dict(retention_group=gname, insurer_years=len(h), insurers=h.company_id.nunique(),
                         median_retention=h.retention.median(), median_score=h.score.median(),
                         median_score_without_retention=h.score_without_retention.median(), share_graded_d_or_e=h.d_or_e.mean()))
    link.append(dict(retention_group="All scored", insurer_years=len(sc), insurers=sc.company_id.nunique(),
                     median_retention=sc.retention.median(), median_score=sc.score.median(),
                     median_score_without_retention=sc.score_without_retention.median(), share_graded_d_or_e=sc.d_or_e.mean(),
                     spearman_retention_score=sc.retention.rank().corr(sc.score.rank()),
                     spearman_retention_score_without_retention=sc.retention.rank().corr(sc.score_without_retention.rank())))
    link = pd.DataFrame(link)
    link["years"] = f"{YEARS[0]} to {YEARS[-1]}"
    link["retention_weight"] = next(wt for n, _, wt, _ in sm.METRICS if n == "retention")
    link["total_weight"] = sum(wt for _, _, wt, _ in sm.METRICS)
    link["scorecard_metrics"] = len(sm.METRICS)

    os.makedirs(out, exist_ok=True)
    kw = dict(index=False, lineterminator="\n", float_format="%.6f")
    for frame, name in [(cc, "class_cession"), (co, "insurer_retention"), (sg, "size_gradient"), (rc, "retention_change"),
                        (mk, "market"), (res, "reinsurer_results"), (link, "scorecard_link")]:
        tidy(frame).to_csv(os.path.join(out, f"reinsurance_{name}.csv"), **kw)

    if quiet:
        return
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    print(mk.assign(ceded_premium=mk.ceded_premium / 1e6, accepted=mk.local_reinsurers_accepted_premium / 1e6)
          [["year", "basis", "ceded_premium", "cession_rate", "median_change_from_prior_year", "mean_abs_change_from_prior_year",
            "accepted", "local_share_upper_bound"]].round(4).to_string(index=False))
    last = cc[cc.year == YEARS[-1]].sort_values("cession_rate")
    print(last[["class", "gross_premium", "cession_rate", "share_of_ceded"]].round(4).to_string(index=False))
    print(sg[sg.year == YEARS[-1]].round(4).to_string(index=False))
    print(link.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
