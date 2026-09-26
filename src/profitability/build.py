"""Where Kenyan general insurers lose money: class by class, company by company, 2018 to 2025.

Reads the class panel and revenue panel from ira-kenya-data (IRA_DATA_DIR, default ../ira-kenya-data) and
writes to output/:

  class_market.csv       market by class and year: premium, earned premium, claims, commissions,
                         management expenses, underwriting result and the ratios on earned premium
  class_company.csv      the same for every insurer, class and year
  rate_gap.csv           the premium change each class needs to break even, pooled over 2023 to 2025
  rate_gap_company.csv   the same for each insurer's motor and medical books
  expense_scale.csv      each insurer's management expense ratio against its size, by year
  loss_concentration.csv which insurers carry the motor loss, 2018 to 2025
  low_motor_loss_ratio.csv every insurer-year that booked a motor loss ratio under 40%, with what later
                         happened to the company: regulator action (reference/regulator_actions.csv),
                         negative equity, or equity below IRA's minimum capital (the higher of KSh 600m
                         and 20% of net earned premium) in any year from 2018
  low_motor_loss_ratio_test.csv  the share of those insurers that ran into capital trouble or regulator
                         action at any point from 2018, against every other motor insurer, at four
                         thresholds, with Fisher's exact test

Full years only (Q4 year to date). Insurers only, micro insurers included, as IRA counts the market.
2016 is left out because IRA's 2016 class tables have no earned premium or expense split, and 2017 is
missing from IRA's site. Motor Commercial and Motor Commercial PSV are combined: companies move business
between the two, and in Q4 2025 Madison moved KSh 1.6bn of earned premium from PSV to Motor Commercial,
leaving PSV with negative earned premium. The combined class is unaffected.

Rate gap (the loss ratio method, Werner and Modlin, Basic Ratemaking, CAS 2016, chapter 8):
    change = (loss ratio + fixed expense ratio) / (1 - variable expense ratio - target margin) - 1
with commissions as the variable expense, management expenses as fixed, all on earned premium, and a
target margin of zero, so the answer is the change that brings the combined ratio to 100%. A second
version credits the market's investment income (as a share of earned premium, same years) as a margin
the class can give up: target combined ratio = 100% + investment yield on premium.
This is an indication of the size of the gap, not a filed rate: there is no loss trend, no development
beyond what the insurers booked, and no allowance for the cost of capital.
"""
import os
from math import comb

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.environ.get("IRA_DATA_DIR", os.path.join(ROOT, "..", "ira-kenya-data"))
OUT = os.path.join(ROOT, "output")
YEARS = list(range(2018, 2026))
GAP_YEARS = [2023, 2024, 2025]
MIN_NEP = 1_000_000  # KSh 1bn of pooled earned premium before a rate gap is shown (in KSh thousands)
MIN_NEP_COMPANY = 300_000
LOW_LR = 0.40  # a motor loss ratio under 40%, a little over half the market's, is flagged
LOW_LR_MIN_NEP = 200_000
LINES = ["gross_premium", "net_earned_premium", "claims_incurred", "commissions", "management_expenses",
         "underwriting_result"]
CLASS_MAP = {"Motor Commercial PSV": "Motor Commercial"}


def ratios(d):
    d = d.copy()
    n = d.net_earned_premium.where(d.net_earned_premium > 0)
    d["loss_ratio"] = d.claims_incurred / n
    d["commission_ratio"] = d.commissions / n
    d["expense_ratio"] = d.management_expenses / n
    d["combined_ratio"] = d.loss_ratio + d.commission_ratio + d.expense_ratio
    return d


def rate_gap(d, invest_yield=None):
    L, V, F = d.loss_ratio, d.commission_ratio, d.expense_ratio
    out = (L + F) / (1 - V) - 1
    if invest_yield is not None:
        # target combined ratio of 1 + y: (L + F) / (1 + y - V) - 1
        return out, (L + F) / (1 + invest_yield - V) - 1
    return out


def fisher_two_sided(a, b, c, d):
    """Fisher's exact test on the 2x2 table [[a, b], [c, d]]."""
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda k: comb(c1, k) * comb(n - c1, r1 - k) / comb(n, r1)
    pa = p(a)
    return sum(p(k) for k in range(max(0, r1 + c1 - n), min(r1, c1) + 1) if p(k) <= pa * (1 + 1e-9))


def main():
    c = pd.read_csv(os.path.join(DATA, "data", "processed", "general_by_class_panel.csv"))
    c = c[(c.quarter == 4) & (c.segment == "insurer") & c.year.isin(YEARS) & c.table.isin(LINES)
          & (c.class_of_business != "Total")]
    c["class"] = c.class_of_business.replace(CLASS_MAP)
    names = pd.read_csv(os.path.join(DATA, "reference", "company_crosswalk.csv")).drop_duplicates("company_id") \
        .set_index("company_id").company_name
    comp = c.pivot_table(index=["company_id", "year", "class"], columns="table", values="ytd_ksh_000",
                         aggfunc="sum").reindex(columns=LINES).fillna(0).reset_index()
    comp = comp[comp[LINES].abs().sum(axis=1) > 0]
    comp.insert(1, "company_name", comp.company_id.map(names))
    comp = ratios(comp)
    mk = ratios(comp.groupby(["year", "class"])[LINES].sum().reset_index())
    tot = ratios(comp.groupby("year")[LINES].sum().reset_index().assign(**{"class": "All classes"}))
    mk = pd.concat([mk, tot], ignore_index=True)

    # investment yield on earned premium, market, same years (revenue panel)
    rp = pd.read_csv(os.path.join(DATA, "data", "processed", "general_revenue_panel.csv"))
    rp = rp[(rp.quarter == 4) & (rp.segment == "insurer") & rp.year.isin(GAP_YEARS)]
    inv = rp[rp.line == "investment_income"].ytd_ksh_000.sum()
    nep = rp[rp.line == "net_earned_premium"].ytd_ksh_000.sum()
    y = inv / nep

    pool = ratios(comp[comp.year.isin(GAP_YEARS)].groupby("class")[LINES].sum().reset_index())
    pool = pd.concat([pool, ratios(pool[LINES].sum().to_frame().T.assign(**{"class": "All classes"}))], ignore_index=True)
    pool["rate_change_to_break_even"], pool["rate_change_after_investment_income"] = rate_gap(pool, y)
    pool["investment_yield_on_premium"] = y
    pool["shown"] = pool.net_earned_premium >= MIN_NEP
    pool = pool.sort_values("underwriting_result")

    cc = comp[comp.year.isin(GAP_YEARS)]
    cc = cc.assign(book=np.where(cc["class"].str.startswith("Motor"), "Motor", cc["class"]))
    cc = cc[cc.book.isin(["Motor", "Medical"])]
    pc = ratios(cc.groupby(["company_id", "company_name", "book"])[LINES].sum().reset_index())
    pc["rate_change_to_break_even"] = rate_gap(pc)
    pc["years"] = cc.groupby(["company_id", "book"]).year.nunique().reindex(
        pd.MultiIndex.from_frame(pc[["company_id", "book"]])).values
    pc["shown"] = (pc.net_earned_premium >= MIN_NEP_COMPANY) & (pc.years == len(GAP_YEARS))

    # expense scale: management expenses over gross premium (not earned premium, which retention distorts)
    es = comp.groupby(["company_id", "company_name", "year"])[LINES].sum().reset_index()
    es = ratios(es)
    es = es[es.gross_premium > 100_000]
    es["expense_to_gross_premium"] = es.management_expenses / es.gross_premium
    es["log_gross_premium"] = np.log(es.gross_premium)

    # motor loss concentration, cumulative 2018 to 2025
    mo = comp[comp["class"].str.startswith("Motor")].groupby(["company_id", "company_name"])[LINES].sum().reset_index()
    mo = ratios(mo).sort_values("underwriting_result")
    total_loss = mo.underwriting_result[mo.underwriting_result < 0].sum()
    mo["share_of_motor_losses"] = np.where(mo.underwriting_result < 0, mo.underwriting_result / total_loss, np.nan)
    mo["cumulative_share"] = mo.share_of_motor_losses.cumsum()
    mo["market_share_motor_premium"] = mo.gross_premium / mo.gross_premium.sum()

    # motor loss ratios too low to believe, and what happened next
    mm = comp[comp["class"].str.startswith("Motor")].groupby(["company_id", "company_name", "year"])[LINES].sum().reset_index()
    mm = ratios(mm)
    mkt = ratios(mm.groupby("year")[LINES].sum().reset_index()).set_index("year").loss_ratio
    low = mm[(mm.net_earned_premium >= LOW_LR_MIN_NEP) & (mm.loss_ratio < LOW_LR)].copy()
    low["market_motor_loss_ratio"] = low.year.map(mkt)
    bs = pd.read_csv(os.path.join(DATA, "data", "processed", "general_balance_sheets.csv"))
    b4 = bs[(bs.quarter == 4) & (bs.year >= 2018)]
    filed = b4[b4.line_item == "Total Assets"].groupby(["company_id", "year"]).value_ksh_000.sum()
    eq = b4[b4.line_item == "Total Equity"].groupby(["company_id", "year"]).value_ksh_000.sum()
    eq = eq[filed.reindex(eq.index).fillna(0) > 0]  # a company listed with an all-zero balance sheet did not file
    nep_all = rp_all = pd.read_csv(os.path.join(DATA, "data", "processed", "general_revenue_panel.csv"))
    nep_all = nep_all[(nep_all.quarter == 4) & (nep_all.line == "net_earned_premium")].groupby(["company_id", "year"]).ytd_ksh_000.sum()
    cap = pd.concat([eq.rename("equity"), nep_all.rename("nep")], axis=1).dropna(subset=["equity"])
    cap["floor"] = np.maximum(600_000, 0.2 * cap.nep.fillna(0))
    neg = cap[cap.equity < 0].reset_index().groupby("company_id").year.apply(lambda s: ", ".join(map(str, sorted(s))))
    below = cap[(cap.equity >= 0) & (cap.equity < cap.floor)].reset_index().groupby("company_id").year.apply(
        lambda s: ", ".join(map(str, sorted(s))))
    ra = pd.read_csv(os.path.join(ROOT, "reference", "regulator_actions.csv")).set_index("company_id")
    low["regulator_action"] = low.company_id.map(ra.action + " " + ra.date)
    low["negative_equity_years"] = low.company_id.map(neg)
    low["below_capital_floor_years"] = low.company_id.map(below)
    ra_year = low.company_id.map(ra.date.str[:4].astype(int))
    trouble_years = {}
    for cid in low.company_id.unique():
        ys = set(cap.loc[cid][cap.loc[cid].equity < cap.loc[cid].floor].index) if cid in cap.index.get_level_values(0) else set()
        trouble_years[cid] = ys
    low["trouble_same_year_or_later"] = [
        (pd.notna(ry) and ry >= y) or any(t >= y for t in trouble_years[cid])
        for cid, y, ry in zip(low.company_id, low.year, ra_year)]
    low = low.sort_values("loss_ratio")

    # does a very low motor loss ratio go with capital trouble? compare with every other motor insurer
    trouble = set(cap[cap.equity < cap.floor].index.get_level_values(0)) | set(ra.index)
    books = mm[mm.net_earned_premium >= LOW_LR_MIN_NEP]
    everyone = set(books.company_id)
    test = []
    for t in (0.35, 0.40, 0.45, 0.50):
        lw = set(books[books.loss_ratio < t].company_id)
        ot = everyone - lw
        a, b, c_, d = len(lw & trouble), len(lw - trouble), len(ot & trouble), len(ot - trouble)
        test.append(dict(threshold=t, low_insurers=len(lw), low_with_trouble=a, other_insurers=len(ot),
                         other_with_trouble=c_, share_low=a / len(lw), share_other=c_ / len(ot),
                         fisher_p=fisher_two_sided(a, b, c_, d)))
    test = pd.DataFrame(test)

    os.makedirs(OUT, exist_ok=True)
    kw = dict(index=False, lineterminator="\n", float_format="%.4f")
    comp.to_csv(os.path.join(OUT, "class_company.csv"), **kw)
    mk.to_csv(os.path.join(OUT, "class_market.csv"), **kw)
    pool.to_csv(os.path.join(OUT, "rate_gap.csv"), **kw)
    pc.to_csv(os.path.join(OUT, "rate_gap_company.csv"), **kw)
    es.to_csv(os.path.join(OUT, "expense_scale.csv"), **kw)
    mo.to_csv(os.path.join(OUT, "loss_concentration.csv"), **kw)
    low.to_csv(os.path.join(OUT, "low_motor_loss_ratio.csv"), **kw)
    test.to_csv(os.path.join(OUT, "low_motor_loss_ratio_test.csv"), **kw)

    pd.set_option("display.width", 220)
    show = pool[["class", "net_earned_premium", "underwriting_result", "loss_ratio", "commission_ratio",
                 "expense_ratio", "combined_ratio", "rate_change_to_break_even", "rate_change_after_investment_income", "shown"]]
    print(f"investment yield on earned premium {GAP_YEARS[0]}-{GAP_YEARS[-1]}: {y:.1%}")
    print(show.assign(net_earned_premium=show.net_earned_premium / 1e6, underwriting_result=show.underwriting_result / 1e6).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
