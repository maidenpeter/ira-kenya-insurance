"""Tests for the claims settlement module (analysis 2). They run on the committed outputs."""
import json
import os
import re

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "output")


def read(name):
    return pd.read_csv(os.path.join(OUT, name))


def test_market_ratios_are_paid_over_open():
    m = read("claims_market.csv")
    assert ((m.paid / m.actionable) - m.payment_ratio).abs().max() < 1e-6
    assert m.payment_ratio.between(0, 1).all() and m.median_payment_ratio.between(0, 1).all()
    assert (m.insurers_compared <= m.insurers).all()


def test_three_businesses_in_every_published_quarter():
    m = read("claims_market.csv")
    n = m.groupby("period").business.nunique()
    # Q1 2018 was published for life business only
    assert (n.drop("2018Q1") == 3).all() and n["2018Q1"] == 1


def test_amounts_only_from_q4_2022():
    m = read("claims_market.csv")
    has = m[m.closing_amount.notna()]
    assert has.period.min() == "2022Q4"


def test_insurer_years_add_up_to_the_market():
    m = read("claims_market.csv")
    iy = read("claims_insurer_year.csv")
    a = m.groupby(["business", "year"]).paid.sum()
    b = iy.groupby(["business", "year"]).paid.sum()
    assert (a - b).abs().max() < 0.5


def test_regulator_cases_use_quarters_before_the_action():
    rg = read("claims_regulator.csv")
    assert rg.company_id.nunique() == 5
    assert (rg.groupby("company_id").size() == 4).all()
    for _, r in rg.iterrows():
        y, q = int(r.period[:4]), int(r.period[5])
        ay, am = map(int, r.action_date.split("-"))
        assert y * 4 + q - 1 < ay * 4 + (am - 1) // 3
    assert ((rg.payment_ratio / rg.median_payment_ratio < 0.5) == rg.under_half).all()


def test_runs_are_four_slow_quarters():
    rn = read("claims_runs.csv")
    assert (rn.max_share_of_median < 0.5).all()


def test_page_carries_the_current_outputs():
    html = open(os.path.join(ROOT, "page", "kenya-claims-settlement.html"), encoding="utf-8").read()
    data = json.loads(re.search(r"const D = (\{.*?\});\n", html).group(1).replace("<\\/", "</"))
    m = read("claims_market.csv")
    x = m[(m.business == "general_liability") & (m.period == "2025Q4")].iloc[0]
    q = data["market"]["liab"][data["periods"].index("2025Q4")]
    assert q["close"] == int(x.closing) and q["pr"] == pytest.approx(x.payment_ratio, abs=1e-4)
    assert data["checks"]["sum_equals_printed_total"]["failed"] == 0


def test_readme_section_is_current():
    import importlib.util
    spec = importlib.util.spec_from_file_location("claims_build_page", os.path.join(ROOT, "src", "claims", "build_page.py"))
    build_page = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_page)
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert build_page.readme_block() in readme, "README's claims section is stale: run src/claims/build_page.py"


def test_everything_written_is_plain_ascii():
    files = [os.path.join(OUT, f) for f in os.listdir(OUT) if f.startswith("claims_")]
    files += [os.path.join(ROOT, "page", f) for f in ("claims_template.html", "kenya-claims-settlement.html")]
    files += [os.path.join(ROOT, "src", "claims", f) for f in ("build.py", "build_page.py")]
    for f in files:
        bad = {c for c in open(f, encoding="utf-8").read() if ord(c) > 127}
        assert not bad, (f, bad)
