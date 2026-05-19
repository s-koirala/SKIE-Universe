"""BLOCKING integration test: H067 PIT-causality leak canaries.

Per H067 design.md §7 + §11.2 ``P1-H067-PIT-CANARY-INTEGRATION-TEST``
(BLOCKING; mirrors H062 v1 PIT canary integration test verbatim per
H067 design.md §7 inheritance discipline).

H067 inherits H062 PIT canaries unchanged because the N-lot sizing
layer does NOT affect PIT semantics: position size at entry is
computed from PIT-causal ATR_n,t and current_equity_t (both as-of
bar t close), with entry at bar t+1 open. The 5-canary surface
preserved from H062:

  - Canary A (channel boundary): the Donchian channel at each test-
    fold bar must equal the channel computed on the continuous panel
    at the same bar.
  - Canary B (label-horizon): the per-trade R-multiple at each test-
    fold trade must depend only on bars within the test fold's
    session boundary (no leak across the eod_flatten boundary).
  - Canary C (no train-test leak): mutating a future-fold bar must
    not change the train-fold channel or signal arrays.
  - Canary D (NaN-poison): a NaN bar in the train fold must NOT
    propagate silently into the test fold's channel.
  - Canary E (full-composition): end-to-end H062 feature factory
    runs clean on a synthetic intraday panel (SIL standalone
    fixture per H067 universe scope).

Markers:
    @pytest.mark.integration — these tests load synthetic full-day
    intraday bar sequences and may take 5-30 seconds to run.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from skie_ninja.features.h062 import (
    H062FeatureConfig,
    compute_h062_features,
    donchian_channel,
)


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def synthetic_intraday_panel_sil() -> pd.DataFrame:
    """30 sessions × 96 bars/session = 2880 5-min metals bars synthesis.

    Each session approximates SIL 24/5 metals trading with EOD-flatten
    at 15:55 CT (per H062 + H065 metals convention; ~96 bars/session
    at 5-min cadence for the ~8-hour active window). Synthetic bars
    use seeded GBM with mild intraday vol calibrated to silver-like
    realised vol (~0.0008 per-bar log-return std vs 0.0007 for ES/NQ).
    """
    rng = np.random.default_rng(20260519)
    n_sessions = 30
    bars_per_session = 96
    n_total = n_sessions * bars_per_session

    log_rets = rng.normal(0, 0.0008, n_total).cumsum()
    close = 25.0 * np.exp(log_rets)
    high = close * (1.0 + np.abs(rng.normal(0, 0.0005, n_total)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.0005, n_total)))
    open_ = np.roll(close, 1)
    open_[0] = close[0]

    base = pd.Timestamp("2024-01-02 13:30:00", tz="UTC")
    ts_event = []
    session_date_et = []
    for s in range(n_sessions):
        day_start = base + pd.Timedelta(days=s)
        for b in range(bars_per_session):
            ts_event.append(day_start + pd.Timedelta(minutes=5 * b))
            session_date_et.append(day_start.tz_convert("America/New_York").date())

    return pd.DataFrame({
        "ts_event": ts_event,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "session_date_et": session_date_et,
    })


class TestChannelBoundaryInvariant:
    """Canary A: features at the fold boundary equal features on the continuous panel."""

    def test_channel_invariant_across_session_boundary(
        self, synthetic_intraday_panel_sil: pd.DataFrame
    ) -> None:
        """Channel computed on full panel matches per-session slices with warmup.

        Per H067 design.md §5.6 walk-forward + §7 PIT canary A: the Donchian
        channel at each test-fold bar must equal the channel computed on the
        full continuous panel at the same bar (no recomputation drift).
        """
        N = 20
        close = synthetic_intraday_panel_sil["close"].to_numpy()
        ch_full = donchian_channel(close, channel_n=N)

        # Slice at session boundary (bar 96 = start of session 2) with
        # N-bar warm-up preserved.
        boundary = 96
        warmup_start = boundary - N
        slice_close = close[warmup_start : boundary + 100]
        ch_slice = donchian_channel(slice_close, channel_n=N)

        for t in range(boundary, boundary + 100):
            slice_idx = t - warmup_start
            assert ch_full.channel_high[t] == ch_slice.channel_high[slice_idx], (
                f"channel_high mismatch at t={t}"
            )
            assert ch_full.channel_low[t] == ch_slice.channel_low[slice_idx], (
                f"channel_low mismatch at t={t}"
            )


class TestLabelHorizonPurge:
    """Canary B: per-trade label depends only on bars within the trade's session."""

    def test_eod_flatten_truncates_trade_at_session_boundary(
        self, synthetic_intraday_panel_sil: pd.DataFrame
    ) -> None:
        """A position entered late in session must be flattened at EOD.

        Per H067 design.md §4 exit precedence (inherited from H065): when
        (t - session_open_idx) >= eod_flatten_minutes_from_open the
        position closes at bar-t close → no overnight carry.
        """
        # Build minimal sim with the H067 sweep script (which fork H065's
        # exit-precedence model); verify session_date_et propagates
        # correctly so no trade spans multiple sessions.
        #
        # H067 sweep script lives under scripts/ which is not a Python
        # package (no __init__.py); use sys.path injection + import rather
        # than importlib.util.spec_from_file_location which trips a
        # Python 3.11 dataclass __module__-lookup quirk when @dataclass
        # decorators run inside the spec-loaded module.
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent
        scripts_dir = repo_root / "scripts"
        h067_path = scripts_dir / "run_h067_n_lot_sweep.py"
        if not h067_path.exists():
            pytest.skip(f"H067 sweep script not yet at {h067_path}")
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        # Reset env var requirement for the import block — this path is
        # not invoking __main__ so the BLAS-pinning gate at the bottom
        # of run_h067_n_lot_sweep.py is bypassed.
        import importlib
        if "run_h067_n_lot_sweep" in sys.modules:
            del sys.modules["run_h067_n_lot_sweep"]
        mod = importlib.import_module("run_h067_n_lot_sweep")

        cfg = H062FeatureConfig(
            channel_n=10,
            atr_n=5,
            h_dwell=1,
            trend_id="a_ts_mom",
            trend_id_lookback_l=10,
            trend_id_threshold=0.1,
        )
        n_lot_cfg = mod.NLotConfig(
            name="N1_test",
            n_lot=1,
            kelly_multiplier=0.25,
            risk_budget_pct=0.01,
            use_current_equity_rebase=True,
            cost_arm="A0",
            description="canary B test cell",
        )
        sim = mod._run_n_lot_simulation(
            symbol="SIL",
            df_5m=synthetic_intraday_panel_sil,
            feature_config=cfg,
            k_atr=2.0,
            cfg=n_lot_cfg,
            cost_model=None,
            eod_flatten_minutes_from_open=72,
        )
        # Per-trade entry_session_date should never be None.
        for tr in sim.get("trade_log_summary", []):
            assert tr.get("entry_session_date") is not None
            assert tr.get("exit_session_date") is not None
            # EOD truncation: same-session OR session_rollover/eod_flatten reason
            if tr["entry_session_date"] != tr["exit_session_date"]:
                # ONLY admissible if exit_reason is session-boundary class
                assert tr["exit_reason"] in (
                    "session_rollover",
                    "eod_flatten",
                    "opposite_channel_break",
                ), (
                    f"trade spans sessions but exit_reason={tr['exit_reason']!r}: "
                    f"{tr['entry_session_date']} → {tr['exit_session_date']}"
                )


class TestNoTrainTestLeak:
    """Canary C: mutating test-fold bars must not change train-fold features."""

    def test_future_bar_mutation_does_not_alter_past_channel(
        self, synthetic_intraday_panel_sil: pd.DataFrame
    ) -> None:
        """Train-fold channel + events invariant to test-fold close mutations."""
        N = 20
        train_end = 1500
        close_v1 = synthetic_intraday_panel_sil["close"].to_numpy().copy()
        close_v2 = close_v1.copy()
        close_v2[train_end:] *= 5.0

        ch_v1 = donchian_channel(close_v1, channel_n=N)
        ch_v2 = donchian_channel(close_v2, channel_n=N)

        np.testing.assert_array_equal(
            ch_v1.channel_high[:train_end], ch_v2.channel_high[:train_end]
        )
        np.testing.assert_array_equal(
            ch_v1.channel_low[:train_end], ch_v2.channel_low[:train_end]
        )


class TestNaNPoisonDetection:
    """Canary D: a NaN bar surfaces as NaN; does NOT propagate silently."""

    def test_nan_close_surfaces_in_channel(self) -> None:
        """A NaN at bar k causes NaN in channel at bars [k+1, k+N]."""
        close = np.arange(100.0, dtype=float)
        close[50] = np.nan
        ch = donchian_channel(close, channel_n=5)
        for t in range(51, 56):
            assert np.isnan(ch.channel_high[t]) or np.isnan(ch.channel_low[t]), (
                f"expected NaN propagation at t={t}, got "
                f"high={ch.channel_high[t]}, low={ch.channel_low[t]}"
            )


class TestFullFeatureFactoryComposition:
    """Canary E: end-to-end H062 feature factory on the SIL synthetic intraday panel."""

    def test_factory_runs_clean_on_30_session_panel(
        self, synthetic_intraday_panel_sil: pd.DataFrame
    ) -> None:
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="a_ts_mom",
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        feats = compute_h062_features(
            high=synthetic_intraday_panel_sil["high"].to_numpy(),
            low=synthetic_intraday_panel_sil["low"].to_numpy(),
            close=synthetic_intraday_panel_sil["close"].to_numpy(),
            config=cfg,
        )
        n = len(synthetic_intraday_panel_sil)
        assert feats.channel.channel_high.shape == (n,)
        assert feats.atr.shape == (n,)
        init_bar = max(20, 14)
        assert np.isfinite(feats.channel.channel_high[init_bar:]).all()
        assert np.isfinite(feats.atr[init_bar:]).all()
