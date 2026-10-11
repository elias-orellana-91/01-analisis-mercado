"""Tests QA: casos borde de métricas y robustez del dashboard (sin red)."""
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import data as d

ROOT = Path(__file__).resolve().parents[1]


def idx(n):
    return pd.bdate_range("2020-01-01", periods=n)


# ---------------- Matemática ----------------
def test_annualized_return_manual():
    r = pd.Series([0.01] * 126)
    # 126 días = medio año -> (1.01^126)^(252/126) - 1
    assert d.annualized_return(r) == pytest.approx(1.01 ** 252 - 1)


def test_sharpe_with_risk_free_manual():
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0.0005, 0.01, 300))
    exp = (r.mean() * 252 - 0.03) / (r.std(ddof=1) * np.sqrt(252))
    assert d.sharpe_ratio(r, 0.03) == pytest.approx(exp)


def test_max_drawdown_manual_series():
    s = pd.Series([100, 120, 60, 90, 80.0], index=idx(5))
    assert d.max_drawdown(s) == pytest.approx(-0.5)


def test_monotonic_up_has_zero_drawdown():
    s = pd.Series(np.arange(1, 11, dtype=float), index=idx(10))
    assert d.max_drawdown(s) == 0


# ---------------- Bordes ----------------
def test_single_day():
    p = pd.DataFrame({"A": [100.0]}, index=idx(1))
    assert d.daily_returns(p).empty
    assert d.cumulative_returns(p).iloc[0, 0] == 0
    assert d.max_drawdown(p)["A"] == 0
    assert d.annual_returns(p).loc[2020, "A"] == 0
    t = d.summary_table(p)  # no debe lanzar
    assert t.shape[0] == 1


def test_constant_series_sharpe_is_nan_without_warning():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # cualquier RuntimeWarning falla el test
        assert np.isnan(d.sharpe_ratio(pd.Series([0.0] * 30)))
        assert np.isnan(d.sharpe_ratio(pd.Series([0.001] * 30)))
        assert np.isnan(d.sharpe_ratio(pd.Series([np.nan] * 30)))
        df = pd.DataFrame({"A": [0.0] * 30, "B": [0.01, -0.01] * 15})
        s = d.sharpe_ratio(df)
        assert np.isnan(s["A"]) and np.isfinite(s["B"])


def test_nan_handling():
    p = pd.DataFrame({"A": [np.nan, 100, 110, np.nan, 121.0]}, index=idx(5))
    r = d.daily_returns(p)
    assert not np.isinf(r.to_numpy(dtype=float)).any()
    assert d.cumulative_returns(p)["A"].iloc[2] == pytest.approx(0.10)
    t = d.summary_table(p)
    assert np.isfinite(t.loc["A", "Retorno total"])
    assert t.loc["A", "Retorno total"] == pytest.approx(0.21)


def test_all_nan_column_does_not_break_others():
    p = pd.DataFrame({"A": [100, 110, 121.0], "B": [np.nan] * 3}, index=idx(3))
    t = d.summary_table(p)
    assert t.loc["A", "Retorno total"] == pytest.approx(0.21)
    assert np.isnan(t.loc["B", "Retorno total"])


def test_empty_prices():
    p = pd.DataFrame({"A": []}, index=pd.DatetimeIndex([]))
    with pytest.raises(Exception):
        d.cumulative_returns(p)  # documenta comportamiento: iloc[0] en vacío


def test_missing_ticker_in_download_prices_selection():
    p = pd.DataFrame({"A": [1.0, 2.0]}, index=idx(2))
    with pytest.raises(KeyError):
        p[["A", "ZZZ"]]


# ---------------- Dashboard ----------------
streamlit_testing = pytest.importorskip("streamlit.testing.v1")


def run_app(setup=None):
    at = streamlit_testing.AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    if setup:
        setup(at)
        at.run()
    return at


def test_app_default_runs():
    at = run_app()
    assert len(at.metric) == 4


def test_app_no_tickers():
    at = run_app(lambda a: a.sidebar.multiselect[1].set_value([]))
    assert not at.exception
    assert len(at.warning) >= 1


def test_app_no_sectors():
    at = run_app(lambda a: a.sidebar.multiselect[0].set_value([]))
    assert not at.exception


def test_app_single_ticker():
    at = run_app(lambda a: a.sidebar.multiselect[1].set_value(["AAPL"]))
    assert not at.exception
    assert len(at.metric) == 4


def test_app_all_sectors():
    all_s = list(d.SECTORS)
    at = run_app(lambda a: a.sidebar.multiselect[0].set_value(all_s))
    assert not at.exception


@pytest.mark.parametrize(
    "rng",
    [
        (dt.date(2020, 3, 2), dt.date(2020, 3, 2)),  # un día
        (dt.date(2020, 3, 7), dt.date(2020, 3, 8)),  # fin de semana (vacío)
        (dt.date(2020, 3, 2), dt.date(2020, 3, 4)),  # 3 días
        (dt.date(2020, 3, 2), dt.date(2020, 3, 20)),  # < ventana de 21d
    ],
)
def test_app_extreme_date_ranges(rng):
    at = run_app(lambda a: a.sidebar.date_input[0].set_value(rng))
    assert not at.exception, at.exception


def test_app_incomplete_date_range():
    at = run_app(lambda a: a.sidebar.date_input[0].set_value((dt.date(2020, 3, 2),)))
    assert not at.exception


def test_app_single_ticker_single_day():
    def setup(a):
        a.sidebar.multiselect[1].set_value(["AAPL"])
        a.sidebar.date_input[0].set_value((dt.date(2020, 3, 2), dt.date(2020, 3, 2)))

    at = run_app(setup)
    assert not at.exception


def test_app_window_extremes():
    at = run_app(lambda a: a.sidebar.slider[0].set_value(126))
    assert not at.exception
