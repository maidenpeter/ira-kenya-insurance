"""Tests for the reinsurance flows module.

Most tests read output/ only, so they run anywhere. The rebuild test needs ira-kenya-data and
ira-kenya-reinsurance next to this repo (or IRA_DATA_DIR and IRA_REINSURANCE_DIR) and is skipped without them.
"""
import importlib.util
import json
import os

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(name):
    """Load src/reinsurance/<name>.py under its own module name: module 1 also has a build.py."""
    spec = importlib.util.spec_from_file_location("reinsurance_" + name, os.path.join(ROOT, "src", "reinsurance", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = load("build")
build_page = load("build_page")

OUT = os.path.join(ROOT, "output")
PREMIUM = ["gross_premium", "net_premium", "ceded_premium"]
RESULT = ["accepted_premium", "net_premium", "net_earned_premium", "claims_incurred", "commissions",
          "management_expenses", "underwriting_result"]
HAVE_DATA = (os.path.exists(os.path.join(build.DATA, "data", "processed", "general_by_class_panel.csv"))
             and os.path.exists(os.path.join(build.REINS, "output", "cedant_scorecard.csv")))


def read(name):
    return pd.read_csv(os.path.join(OUT, name))


def test_cession_rate_is_between_0_and_1():
    cc = read("reinsurance_class_cession.csv")
    pos = cc[cc.gross_premium > 0]
    assert pos.cession_rate.between(0, 1).all(), pos[~pos.cession_rate.between(0, 1)]
    assert not cc.outside_0_1.any()
    # an insurer whose retention falls outside 0 to 1 is kept, not clipped, and carries a note saying why
    co = read("reinsurance_insurer_retention.csv")
    odd = co[~co.retention.between(0, 1)]
    assert odd.note.fillna("").astype(str).str.len().gt(0).all()
    assert np.allclose(co.retention + co.cession_rate, 1, atol=2e-4)


def test_classes_add_to_insurers_and_market():
    cc = read("reinsurance_class_cession.csv")
    total = cc[cc["class"] == "All classes"].set_index("year")[PREMIUM].sort_index()
    parts = cc[cc["class"] != "All classes"].groupby("year")[PREMIUM].sum().sort_index()
    assert np.allclose(parts, total, atol=0.05)
    co = read("reinsurance_insurer_retention.csv")
    assert np.allclose(co.groupby("year")[PREMIUM].sum().sort_index(), total, atol=0.05)
    shares = cc[cc["class"] != "All classes"].groupby("year").share_of_ceded.sum()
    assert np.allclose(shares, 1, atol=1e-3)
    assert np.allclose(cc.ceded_premium, cc.gross_premium - cc.net_premium, atol=0.01)


def test_premium_ceded_reconciles_to_outward_reinsurance():
    co = read("reinsurance_insurer_retention.csv")
    assert co.outward_reinsurance.notna().all()
    assert (co.reconcile_gap.abs() <= build.TOL).all(), co.loc[co.reconcile_gap.abs().idxmax()]
    assert np.allclose(co.reconcile_gap, co.ceded_premium - co.outward_reinsurance, atol=0.01)


def test_reinsurer_results_add_up_like_the_insurers():
    rr = read("reinsurance_reinsurer_results.csv")
    one = rr[rr.company_id != "all_local_reinsurers"]
    cls = one[one["class"] != "All classes"]
    # earned premium less claims, commissions and expenses is the result, within KSh 5,000, as in module 1
    rebuilt = cls.net_earned_premium - cls.claims_incurred - cls.commissions - cls.management_expenses
    assert ((rebuilt - cls.underwriting_result).abs() <= 5).all()
    # classes add to each reinsurer's total, and the reinsurers add to all of them together
    tot = one[one["class"] == "All classes"].set_index(["company_id", "year"])[RESULT].sort_index()
    assert np.allclose(cls.groupby(["company_id", "year"])[RESULT].sum().sort_index(), tot, atol=0.05)
    seg = rr[(rr.company_id == "all_local_reinsurers") & (rr["class"] == "All classes")].set_index("year")[RESULT].sort_index()
    assert np.allclose(tot.groupby(level="year").sum().sort_index(), seg, atol=0.05)
    r = rr[rr.net_earned_premium > 0]
    assert np.allclose(r.combined_ratio, r.loss_ratio + r.commission_ratio + r.expense_ratio, atol=3e-4)


def test_merged_companies_are_counted_once_each_year():
    co = read("reinsurance_insurer_retention.csv")
    assert not co.duplicated(["company_id", "year"]).any()
    ee = pd.read_csv(os.path.join(ROOT, "reference", "entries_exits.csv"))
    for _, m in ee[ee.kind == "merger"].iterrows():
        late = co[(co.company_id == m.company_id) & (co.year > m.year_in_data)]
        assert late.empty, f"{m.company_id} still counted after its book passed on: {sorted(late.year)}"
    rc = read("reinsurance_retention_change.csv")
    assert not rc.company_id.isin(list(build.ABSORBED)).any()  # absorbed companies count with their buyer


def test_local_capacity_is_an_upper_bound():
    mk = read("reinsurance_market.csv")
    assert mk.local_share_upper_bound.between(0, 1).all()
    assert np.allclose(mk.local_share_upper_bound, (mk.local_reinsurers_accepted_premium / mk.ceded_premium).clip(upper=1), atol=2e-4)


def test_readme_numbers_match_a_fresh_recomputation():
    F = build_page.facts()
    block = build_page.readme_block(F)  # also checks that the data still points the way the words say
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert block in readme, "README's reinsurance section is stale: run src/reinsurance/build_page.py"


def test_page_carries_the_current_outputs():
    F = build_page.facts()
    js = json.dumps(build_page.clean(build_page.page_data(F)), separators=(",", ":"), ensure_ascii=True, sort_keys=True)
    page = open(os.path.join(ROOT, "page", "kenya-insurance-reinsurance-flows.html"), encoding="utf-8").read()
    assert js.replace("</", "<\\/") in page, "page is stale: run src/reinsurance/build_page.py"
    assert build_page.CAVEAT in js and build_page.CAVEAT_RE in js


def test_everything_written_is_plain_ascii():
    files = [os.path.join(OUT, f) for f in os.listdir(OUT) if f.startswith("reinsurance_")]
    files += [os.path.join(ROOT, "page", p) for p in ("reinsurance_template.html", "kenya-insurance-reinsurance-flows.html")]
    files += [os.path.join(ROOT, "src", "reinsurance", p) for p in ("build.py", "build_page.py")]
    for f in files:
        bad = sorted({c for c in open(f, encoding="utf-8").read() if ord(c) > 127})
        assert not bad, (f, bad)


@pytest.mark.skipif(not HAVE_DATA, reason="needs ira-kenya-data and ira-kenya-reinsurance next to this repo")
def test_outputs_are_byte_identical_on_a_rebuild(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    build.main(str(a), quiet=True)
    build.main(str(b), quiet=True)
    names = sorted(os.listdir(a))
    assert names == sorted(f for f in os.listdir(OUT) if f.startswith("reinsurance_"))
    for f in names:
        assert (a / f).read_bytes() == (b / f).read_bytes(), f"{f} differs between two runs"
        with open(os.path.join(OUT, f), "rb") as fh:
            assert (a / f).read_bytes() == fh.read(), f"output/{f} is stale: run src/reinsurance/build.py"
