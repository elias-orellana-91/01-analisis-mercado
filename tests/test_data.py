"""Tests de las métricas con datos sintéticos (sin red)."""
import numpy as np
import pandas as pd
import pytest

from src import data as d


@pytest.fixture
def prices():
    idx = pd.bdate_range("2020-01-01", periods=6)
    return pd.DataFrame(
        {"A": [100, 110, 99, 99, 120, 108], "B": [50, 50, 50, 50, 50, 50]},
        index=idx,
        dtype=float,
    )


def test_daily_returns(prices):
    r = d.daily_returns(prices)
    assert len(r) == len(prices) - 1
    assert r["A"].iloc[0] == pytest.approx(0.10)
    assert r["A"].iloc[1] == pytest.approx(-0.10)
    assert (r["B"] == 0).all()


def test_cumulative_returns(prices):
    c = d.cumulative_returns(prices)
    assert c["A"].iloc[0] == 0
    assert c["A"].iloc[-1] == pytest.approx(0.08)
    assert (c["B"] == 0).all()


def test_cumulative_returns_series_with_leading_nan():
    s = pd.Series([np.nan, 10.0, 20.0], index=pd.bdate_range("2020-01-01", periods=3))
    assert d.cumulative_returns(s).iloc[-1] == pytest.approx(1.0)


def test_rolling_volatility_constant_is_zero(prices):
    vol = d.rolling_volatility(d.daily_returns(prices)["B"], window=3)
    assert vol.dropna().eq(0).all()


def test_rolling_volatility_annualization():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0, 0.01, 500))
    vol = d.rolling_volatility(r, window=21)
    assert vol.iloc[:20].isna().all()
    assert vol.iloc[-1] == pytest.approx(r.iloc[-21:].std() * np.sqrt(252))


def test_max_drawdown(prices):
    mdd = d.max_drawdown(prices)
    assert mdd["A"] == pytest.approx(99 / 110 - 1)
    assert mdd["B"] == 0
    assert (d.drawdown_series(prices) <= 0).all().all()


def test_annual_returns():
    idx = pd.to_datetime(["2020-06-01", "2020-12-31", "2021-06-01", "2021-12-31"])
    s = pd.Series([100.0, 120.0, 130.0, 90.0], index=idx)
    ar = d.annual_returns(s)
    assert ar.loc[2020] == pytest.approx(0.20)  # desde el primer precio
    assert ar.loc[2021] == pytest.approx(90 / 120 - 1)


def test_sharpe_ratio_and_annualized():
    r = pd.Series([0.01, -0.01] * 50)
    expected = r.mean() * 252 / (r.std() * np.sqrt(252))
    assert d.sharpe_ratio(r) == pytest.approx(expected)
    assert d.sharpe_ratio(r) == pytest.approx(0.0)
    assert d.annualized_return(pd.Series([0.0] * 10)) == 0


def test_summary_table_shape(prices):
    t = d.summary_table(prices)
    assert list(t.index) == ["A", "B"]
    assert {"Retorno total", "Volatilidad", "Max drawdown", "Sharpe"} <= set(t.columns)


def test_load_prices_uses_cache(tmp_path):
    p = tmp_path / "c.parquet"
    df = pd.DataFrame({"X": [1.0, 2.0]}, index=pd.bdate_range("2020-01-01", periods=2))
    df.to_parquet(p)
    out = d.load_prices(p)  # no debe tocar la red
    pd.testing.assert_frame_equal(out, df, check_freq=False)


def test_sectors_cover_tickers():
    assert len(d.TICKERS) == 16 and "SPY" in d.TICKERS
    assert d.TICKER_TO_SECTOR["JPM"] == "Bancos"
