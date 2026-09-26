"""Tests for the profitability module: the arithmetic, and agreement with IRA's own PDF releases."""
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "profitability"))
import build  # noqa: E402

OUT = os.path.join(ROOT, "output")


@pytest.fixture(scope="module")
def market():
    return pd.read_csv(os.path.join(OUT, "class_market.csv"))


def test_every_class_result_adds_up():
    c = pd.read_csv(os.path.join(OUT, "class_company.csv"))
    rebuilt = c.net_earned_premium - c.claims_incurred - c.commissions - c.management_expenses
    assert ((rebuilt - c.underwriting_result).abs() <= 5).all()


def test_classes_add_to_the_market_total(market):
    parts = market[market["class"] != "All classes"].groupby("year").underwriting_result.sum()
    total = market[market["class"] == "All classes"].set_index("year").underwriting_result
    assert ((parts - total).abs() <= 5).all()


def test_matches_ira_pdf_releases_2020_to_2024(market):
    # IRA Insurance Industry Releases Q4 2023 and Q4 2024, tables 15 to 21 (KSh bn, summed 2020 to 2024)
    m = market[market.year.between(2020, 2024)].groupby("class").underwriting_result.sum() / 1e6
    assert m["Motor Private"] == pytest.approx(-19.21, abs=0.01)
    assert m["Motor Commercial"] == pytest.approx(-15.33, abs=0.01)  # includes PSV
    assert m["Workmen's Compensation"] == pytest.approx(11.01, abs=0.015)
    med = market[market["class"] == "Medical"].set_index("year").underwriting_result / 1e6
    assert med[2020] == pytest.approx(1.30, abs=0.01) and med[2024] == pytest.approx(-0.47, abs=0.01)


def test_rate_gap_formula():
    d = pd.DataFrame(dict(loss_ratio=[0.70], commission_ratio=[0.10], expense_ratio=[0.30]))
    be, ai = build.rate_gap(d, 0.10)
    assert be[0] == pytest.approx((0.70 + 0.30) / 0.90 - 1)  # combined ratio 110% needs +11.1%
    assert ai[0] == pytest.approx((0.70 + 0.30) / 1.00 - 1)  # a 10% yield target brings it to 0


def test_fisher_exact():
    assert build.fisher_two_sided(8, 2, 7, 21) == pytest.approx(0.00611, abs=1e-4)
    assert build.fisher_two_sided(5, 5, 5, 5) == pytest.approx(1.0)


def test_low_loss_ratio_list_is_consistent():
    low = pd.read_csv(os.path.join(OUT, "low_motor_loss_ratio.csv"))
    assert (low.loss_ratio < build.LOW_LR).all()
    assert (low.net_earned_premium >= build.LOW_LR_MIN_NEP).all()
    t = pd.read_csv(os.path.join(OUT, "low_motor_loss_ratio_test.csv"))
    row = t[t.threshold.round(2) == 0.40].iloc[0]
    assert row.low_insurers == low.company_id.nunique()
