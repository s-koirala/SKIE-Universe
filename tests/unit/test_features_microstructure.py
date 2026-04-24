"""Contractual + analytical-case tests for the four microstructure features."""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import pytest

from skie_ninja.features.base import FeatureTestBase
from skie_ninja.features.microstructure.ofi_tickrule import OfiTickRule
from skie_ninja.features.microstructure.realized_skew import RealizedSkew
from skie_ninja.features.microstructure.rv_parkinson import RvParkinson
from skie_ninja.features.microstructure.rv_realized import RvRealized

# ---------------------------------------------------------------------------
# Shared synthetic OHLCV panel
# ---------------------------------------------------------------------------


def _synthetic_panel(
    *, n: int = 200, seed: int = 2026, constant: bool = False
) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2025-01-02", periods=n, freq="1min", tz="UTC")
    if constant:
        close = np.full(n, 100.0)
    else:
        r = rng.normal(0, 0.001, n)
        close = 100.0 * np.exp(np.cumsum(r))
    open_ = np.concatenate([[close[0]], close[:-1]])
    wing = np.abs(rng.normal(0, 0.0005, n))
    high = np.maximum(open_, close) * (1.0 + wing)
    low = np.minimum(open_, close) * (1.0 - wing)
    volume = rng.integers(100, 1000, n).astype(np.int64)
    return pl.DataFrame(
        {
            "ts_event": ts,
            "symbol": ["ES"] * n,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


# ---------------------------------------------------------------------------
# rv_parkinson
# ---------------------------------------------------------------------------


class TestRvParkinson(FeatureTestBase):
    def make_module(self):  # type: ignore[override]
        return RvParkinson(window_bars=20)

    def make_panel(self):  # type: ignore[override]
        return _synthetic_panel(n=100, seed=1).lazy()

    def test_constant_range_gives_zero(self) -> None:
        """Parkinson RV on a panel where H == L for every bar is
        identically zero (log(H/L) = 0).
        """
        panel = _synthetic_panel(n=50, seed=2)
        # Force H = L = close.
        panel = panel.with_columns(
            [pl.col("close").alias("high"), pl.col("close").alias("low")]
        )
        mod = RvParkinson(window_bars=10)
        now = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
        out = mod.compute(panel.lazy(), now, ctx=None).collect()
        col = out.get_column("rv_parkinson@1.0").to_numpy()
        valid = col[~np.isnan(col)]
        np.testing.assert_allclose(valid, 0.0, atol=1e-12)


# ---------------------------------------------------------------------------
# rv_realized
# ---------------------------------------------------------------------------


class TestRvRealized(FeatureTestBase):
    def make_module(self):  # type: ignore[override]
        return RvRealized(window_bars=20)

    def make_panel(self):  # type: ignore[override]
        return _synthetic_panel(n=100, seed=3).lazy()

    def test_constant_returns_gives_zero_rv(self) -> None:
        """Zero log-returns → zero realized variance."""
        panel = _synthetic_panel(n=80, seed=4, constant=True)
        mod = RvRealized(window_bars=20)
        now = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
        out = mod.compute(panel.lazy(), now, ctx=None).collect()
        col = out.get_column("rv_realized@1.0").to_numpy()
        valid = col[~np.isnan(col)]
        np.testing.assert_allclose(valid, 0.0, atol=1e-12)


# ---------------------------------------------------------------------------
# realized_skew
# ---------------------------------------------------------------------------


class TestRealizedSkew(FeatureTestBase):
    def make_module(self):  # type: ignore[override]
        return RealizedSkew(window_bars=30)

    def make_panel(self):  # type: ignore[override]
        return _synthetic_panel(n=200, seed=5).lazy()

    def test_symmetric_returns_have_small_skew(self) -> None:
        """Returns drawn from a symmetric distribution have realized
        skew close to zero in expectation. Check that the mean of the
        rolling skew column across a large sample is near zero.
        """
        panel = _synthetic_panel(n=1000, seed=6)
        mod = RealizedSkew(window_bars=60)
        now = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
        out = mod.compute(panel.lazy(), now, ctx=None).collect()
        col = out.get_column("realized_skew@1.0").to_numpy()
        valid = col[~np.isnan(col)]
        # Tolerance is loose — this is a stochastic check, not an
        # analytical one. Symmetric Gaussian returns should give a
        # sample mean of skew much closer to 0 than the scale of the
        # values.
        assert abs(valid.mean()) < 0.5


# ---------------------------------------------------------------------------
# ofi_tickrule
# ---------------------------------------------------------------------------


class TestOfiTickRule(FeatureTestBase):
    def make_module(self):  # type: ignore[override]
        return OfiTickRule(window_bars=20)

    def make_panel(self):  # type: ignore[override]
        return _synthetic_panel(n=100, seed=7).lazy()

    def test_monotone_up_series_gives_positive_ofi(self) -> None:
        """Strictly increasing close → every bar's sign = +1 → rolling
        sum of signed volume = sum of volumes (positive).
        """
        n = 50
        ts = pd.date_range("2025-01-02", periods=n, freq="1min", tz="UTC")
        close = 100.0 * np.exp(np.cumsum(np.full(n, 0.001)))
        vol = np.full(n, 100, dtype=np.int64)
        panel = pl.DataFrame(
            {
                "ts_event": ts,
                "symbol": ["ES"] * n,
                "open": close,
                "high": close,
                "low": close,
                "close": close,
                "volume": vol,
            }
        )
        mod = OfiTickRule(window_bars=10)
        now = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
        out = mod.compute(panel.lazy(), now, ctx=None).collect()
        col = out.get_column("ofi_tickrule@1.0").to_numpy()
        valid = col[~np.isnan(col)]
        # After normalization (signed_vol_sum / total_vol_sum):
        # The first window (bars 0..9): bar 0 has sign=0 → 9 bars signed
        # out of 10 → OFI = 9·100 / 10·100 = 0.9.
        # Every subsequent window has all 10 bars signed → OFI = 1.0.
        assert valid[0] == pytest.approx(0.9)
        np.testing.assert_allclose(valid[1:], 1.0)
