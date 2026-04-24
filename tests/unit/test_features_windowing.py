"""PIT-invariant tests for :mod:`skie_ninja.features.windowing`."""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from skie_ninja.features.windowing import rolling_apply_pit


def _make_panel(n: int = 200, seed: int = 2026) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2025-01-01", periods=n, freq="1min", tz="UTC")
    return pl.DataFrame(
        {
            "ts_event": ts,
            "symbol": ["ES"] * n,
            "value": rng.standard_normal(n),
        }
    )


def test_rolling_apply_pit_matches_truncated_panel() -> None:
    panel = _make_panel(n=100)
    out_full = rolling_apply_pit(
        panel,
        column="value",
        window=10,
        fn=np.mean,
        min_periods=10,
        group_by="symbol",
        include_current=True,
        output_column="mean_10",
    ).collect()
    cutoff = 50
    truncated = panel.head(cutoff)
    out_trunc = rolling_apply_pit(
        truncated,
        column="value",
        window=10,
        fn=np.mean,
        min_periods=10,
        group_by="symbol",
        include_current=True,
        output_column="mean_10",
    ).collect()
    np.testing.assert_allclose(
        out_full.head(cutoff).get_column("mean_10").to_numpy(),
        out_trunc.get_column("mean_10").to_numpy(),
    )


def test_rolling_apply_pit_refuses_bad_min_periods() -> None:
    panel = _make_panel(n=20)
    with pytest.raises(ValueError, match="min_periods"):
        rolling_apply_pit(
            panel,
            column="value",
            window=10,
            fn=np.mean,
            min_periods=15,
            output_column="x",
        )


def test_rolling_apply_pit_refuses_bad_window() -> None:
    panel = _make_panel(n=20)
    with pytest.raises(ValueError, match="window"):
        rolling_apply_pit(
            panel,
            column="value",
            window=0,
            fn=np.mean,
            min_periods=1,
            output_column="x",
        )


@settings(max_examples=100, deadline=None)
@given(st.integers(min_value=2, max_value=80))
def test_rolling_apply_pit_truncation_invariant(cutoff: int) -> None:
    """For 100 random ``cutoff`` values in [2, 80], every row at index
    ``i < cutoff`` has the same rolling value whether computed on the
    full panel or on ``panel.head(cutoff)``.

    This is the plan §3.1 contract exercised on the windowing helper
    directly.
    """
    panel = _make_panel(n=100)
    out_full = (
        rolling_apply_pit(
            panel,
            column="value",
            window=5,
            fn=np.mean,
            min_periods=5,
            include_current=True,
            output_column="m",
        )
        .collect()
        .head(cutoff)
    )
    out_trunc = rolling_apply_pit(
        panel.head(cutoff),
        column="value",
        window=5,
        fn=np.mean,
        min_periods=5,
        include_current=True,
        output_column="m",
    ).collect()
    a = out_full.get_column("m").to_numpy()
    b = out_trunc.get_column("m").to_numpy()
    mask_a = np.isnan(a)
    mask_b = np.isnan(b)
    np.testing.assert_array_equal(mask_a, mask_b)
    np.testing.assert_allclose(a[~mask_a], b[~mask_b])


def test_exclude_current_shifts_window() -> None:
    """``include_current=False`` drops the current bar from the
    window — the row at ``t`` uses only ``{t-n, ..., t-1}``.
    """
    panel = _make_panel(n=30)
    values = panel.get_column("value").to_numpy()
    out = rolling_apply_pit(
        panel,
        column="value",
        window=5,
        fn=np.mean,
        min_periods=5,
        include_current=False,
        output_column="m",
    ).collect()
    # First 5 rows: NaN (not enough prior data). Row 5 should equal
    # mean(values[0:5]).
    m = out.get_column("m").to_numpy()
    assert np.isnan(m[:5]).all()
    np.testing.assert_allclose(m[5], values[:5].mean())
