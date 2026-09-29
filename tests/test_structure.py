"""Tests for the market structure module."""
import os

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "output")


def read(name):
    return pd.read_csv(os.path.join(OUT, name))


def test_shares_add_to_one_and_hhi_matches():
    s = read("structure_shares.csv")
    m = read("structure_market.csv").set_index("year")
    for y, g in s.groupby("year"):
        assert g.share.sum() == pytest.approx(1, abs=1e-3)
        assert (g.share ** 2).sum() * 1e4 == pytest.approx(m.loc[y, "hhi"], rel=1e-3)
        assert m.loc[y, "equivalent_insurers"] == pytest.approx(1e4 / m.loc[y, "hhi"], rel=1e-3)


def test_market_premium_matches_the_data_repo_readme():
    # gross premium (gross direct plus inward) in the ira-kenya-data README, KSh bn
    readme = {2016: 121.7, 2018: 129.0, 2019: 131.1, 2020: 130.8, 2021: 152.4, 2022: 168.9, 2023: 191.3, 2024: 204.1, 2025: 227.2}
    m = read("structure_market.csv").set_index("year")
    for y, v in readme.items():
        assert m.loc[y, "written_premium"] / 1e6 == pytest.approx(v, abs=0.05)


def test_pro_forma_shares_add_to_one():
    s = read("structure_share_shift.csv")
    assert s.share_2020.sum() == pytest.approx(1, abs=1e-3)
    assert s.share_2025.sum() == pytest.approx(1, abs=1e-3)
    assert not s.company_id.isin(["saham", "allianz_kenya", "sanlam_general"]).any()


def test_class_mix_adds_to_one():
    m = read("structure_class_mix.csv")
    assert np.allclose(m.groupby("year").share_of_market.sum(), 1, atol=1e-3)


def test_fragmentation_arithmetic():
    f = read("structure_fragmentation.csv")
    assert np.allclose(f.extra_expense, f.rest_expenses - f.rest_expected_at_top5_rates, atol=1)
    assert ((f.rest_share > 0) & (f.rest_share < 1)).all()


def test_growth_split_is_against_market_growth():
    g = read("structure_growth_results.csv")
    assert (g.gained_share == (g.growth_a_year > g.market_growth_a_year)).all()
