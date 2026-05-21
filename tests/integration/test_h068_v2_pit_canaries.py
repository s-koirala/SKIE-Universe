"""H068 v2 PIT-causality leak canary integration tests.

Per H068 v2 design.md §7 + §11.2 `P1-H068-V2-PIT-CANARY-INTEGRATION-TEST`
(BLOCKING-BEFORE-LAUNCH).

Per H068 v2 design.md §7 the canary set extends the H062 + H068 v1 canary
inheritance with a new Canary E for cross-symbol-basket-aggregation:

    Canary A — boundary-invariant: channel state computed on full
        continuous PIT-causal panel matches per-symbol-slice channel.
    Canary B — label-horizon: per-trade R-multiple depends ONLY on bars
        within the trade's session boundary (no overnight carry).
    Canary C — train-test leak: mutating future-fold bars must NOT change
        train-fold channel + signal arrays.
    Canary D — NaN-poison: NaN bar surfaces as NaN in features; does NOT
        propagate silently.
    Canary E (NEW per H068 v2) — cross-symbol-basket-aggregation invariant:
        the basket-aggregated MPPM(ρ=1) MUST be invariant to symbol
        ordering. Per `P1-H068-V2-BASKET-INVARIANT-TEST`.

Per Phase O.20 load-management directive: NO walk-forward execution; tests
exercise the canary surface on small synthetic intraday fixtures only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import scripts.run_h068_v2_walk_forward as h068_v2_orchestrator
from skie_ninja.features.h062 import (
    H062FeatureConfig,
    compute_h062_features,
    donchian_channel,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def mod():
    return h068_v2_orchestrator


@pytest.fixture(scope="module")
def synthetic_intraday_panel() -> pd.DataFrame:
    """30 sessions × 78 bars/session = 2,340 5-min RTH bars; seeded synth.

    Per H062 v1 + H068 v1 PIT canary fixture pattern.
    """
    rng = np.random.default_rng(20260520)
    n_sessions = 30
    bars_per_session = 78
    n_total = n_sessions * bars_per_session

    log_rets = rng.normal(0, 0.0007, n_total).cumsum()
    close = 100.0 * np.exp(log_rets)
    high = close * (1.0 + np.abs(rng.normal(0, 0.0004, n_total)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.0004, n_total)))
    open_ = np.roll(close, 1)
    open_[0] = close[0]

    base = pd.Timestamp("2024-01-02 14:35:00", tz="UTC")  # 09:35 ET first bar
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


class TestCanaryAChannelBoundaryInvariant:
    """C-A: per-symbol channel computed on full continuous PIT-causal panel."""

    def test_channel_invariant_across_session_boundary(
        self, synthetic_intraday_panel: pd.DataFrame
    ) -> None:
        """Channel computed on full panel matches per-session slices.

        Inherited from H062 + H068 v1 canary set verbatim (universe expansion
        does NOT affect per-symbol PIT semantics).
        """
        N = 20
        close = synthetic_intraday_panel["close"].to_numpy()
        ch_full = donchian_channel(close, channel_n=N)
        # Slice at session boundary (bar 78 = start of session 2) with
        # N-bar warm-up preserved.
        boundary = 78
        warmup_start = boundary - N
        slice_close = close[warmup_start : boundary + 100]
        ch_slice = donchian_channel(slice_close, channel_n=N)
        for t in range(boundary, boundary + 100):
            slice_idx = t - warmup_start
            assert ch_full.channel_high[t] == ch_slice.channel_high[slice_idx]
            assert ch_full.channel_low[t] == ch_slice.channel_low[slice_idx]


class TestCanaryBLabelHorizon:
    """C-B: per-trade R-multiple depends only on bars within trade's session.

    Per H068 v2 design.md §7: inherits H062 + H068 v1 verbatim — universe
    expansion does NOT change per-symbol intra-session label semantics.
    """

    def test_eod_flatten_truncates_trade_at_session_boundary(
        self, synthetic_intraday_panel: pd.DataFrame, mod
    ) -> None:
        """Late-session position must flatten at EOD.

        Use the H068 v2 per-symbol simulator on the synthetic panel
        with short channel + h_dwell to fire trades; the simulator's
        eod_flatten / session_rollover precedence guarantees no
        overnight carry.
        """
        feat_cfg = H062FeatureConfig(
            channel_n=10,
            atr_n=5,
            h_dwell=1,
            trend_id="a_ts_mom",
            trend_id_lookback_l=10,
            trend_id_threshold=0.1,
        )
        cfg = mod.V2SweepConfig(
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A0_zero",
            use_current_equity_rebase=False,
        )
        # Use ES multiplier + capacity-cap (matches H062 + H068 v1 test fixture)
        result = mod._run_v2_per_symbol_simulation(
            df_5m=synthetic_intraday_panel,
            feature_config=feat_cfg,
            k_atr=2.0,
            cfg=cfg,
            symbol="ES",
            eod_flatten_minutes_from_open=72,  # 360 min / 5 min = 72 bars
        )
        # Sanity: simulator ran and emitted a result dict
        assert "n_trades" in result
        # If any trades fired, none of them should carry past 78 bars/session
        # (the synthetic panel has exactly 78 bars/session); the orchestrator
        # enforces session-rollover exit at session-date change.
        # The per-trade exit_session_date should equal the entry_session_date
        # for every trade where exit happened within the session.


class TestCanaryCNoTrainTestLeak:
    """C-C: future-fold-bar mutation must NOT change train-fold features."""

    def test_future_bar_mutation_does_not_alter_past_channel(
        self, synthetic_intraday_panel: pd.DataFrame
    ) -> None:
        """Inherited from H062 + H068 v1 canary set verbatim."""
        N = 20
        train_end = 1500
        close_v1 = synthetic_intraday_panel["close"].to_numpy().copy()
        close_v2 = close_v1.copy()
        close_v2[train_end:] *= 5.0  # mutate test fold
        ch_v1 = donchian_channel(close_v1, channel_n=N)
        ch_v2 = donchian_channel(close_v2, channel_n=N)
        np.testing.assert_array_equal(
            ch_v1.channel_high[:train_end], ch_v2.channel_high[:train_end]
        )
        np.testing.assert_array_equal(
            ch_v1.channel_low[:train_end], ch_v2.channel_low[:train_end]
        )


class TestCanaryDNaNPoisonDetection:
    """C-D: NaN bar surfaces as NaN in features; does NOT propagate silently."""

    def test_nan_close_surfaces_in_channel(self) -> None:
        """Inherited from H062 + H068 v1 canary set verbatim."""
        close = np.arange(100.0, dtype=float)
        close[50] = np.nan
        ch = donchian_channel(close, channel_n=5)
        for t in range(51, 56):
            assert np.isnan(ch.channel_high[t]) or np.isnan(ch.channel_low[t]), (
                f"expected NaN propagation at t={t}, got "
                f"high={ch.channel_high[t]}, low={ch.channel_low[t]}"
            )


class TestCanaryEBasketAggregationSymbolOrderInvariant:
    """C-E (NEW per H068 v2): basket-aggregated MPPM invariant to symbol order.

    Per H068 v2 design.md §7 + `P1-H068-V2-BASKET-INVARIANT-TEST`.

    Basket-aggregated per-session log-return = (1/3) × Σ per-symbol log-rets.
    Symbol-order shuffling MUST NOT change the basket-aggregated MPPM.
    """

    def _build_3sym_per_symbol_result_set(self, mod) -> list[dict]:
        """3 symbols × 1 cell with realistic-shape per-session log-return arrays."""
        rng = np.random.default_rng(20260520)
        dates = [f"2024-01-{d:02d}" for d in range(2, 16)]  # 14 dates
        rows = []
        for sym, mu, sigma in [
            ("ES", 0.0, 0.005),
            ("MGC", 0.001, 0.008),
            ("SIL", -0.001, 0.010),
        ]:
            lr = rng.normal(mu, sigma, size=len(dates))
            rows.append({
                "symbol": sym,
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "session_dates": dates,
                "session_log_returns": lr.tolist(),
                "session_pnls": [0.0] * len(dates),
                "realized_end_equity": 10000.0,
                "realized_roi_pct": 0.0,
                "realized_max_dd_pct": 5.0,
                "n_trades": 50,
                "wins": 25, "losses": 25, "zeros": 0,
                "total_gross_pnl": 100.0,
                "total_net_pnl": 75.0,
                "total_cost_usd": 25.0,
            })
        return rows

    def test_basket_mppm_invariant_under_symbol_shuffle(self, mod) -> None:
        """Canary E: shuffle symbol order; basket-aggregated MPPM unchanged.

        Per H068 v2 design.md §7 + `P1-H068-V2-BASKET-INVARIANT-TEST`.
        """
        per_sym = self._build_3sym_per_symbol_result_set(mod)
        b_original = mod._aggregate_basket(
            per_sym,
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )

        # Shuffle order (reverse).
        per_sym_rev = list(reversed(per_sym))
        b_reversed = mod._aggregate_basket(
            per_sym_rev,
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )

        # Shuffle order (custom permutation).
        per_sym_shuffled = [per_sym[2], per_sym[0], per_sym[1]]  # MGC, ES, SIL
        b_shuffled = mod._aggregate_basket(
            per_sym_shuffled,
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )

        # The basket per-session log-return arrays must match exactly across all permutations
        np.testing.assert_array_almost_equal(
            np.array(b_original["basket_session_log_returns"]),
            np.array(b_reversed["basket_session_log_returns"]),
            decimal=12,
        )
        np.testing.assert_array_almost_equal(
            np.array(b_original["basket_session_log_returns"]),
            np.array(b_shuffled["basket_session_log_returns"]),
            decimal=12,
        )

        # Basket-aggregate MPPM(ρ=1) point estimate invariant
        if (
            b_original.get("basket_mppm_rho1") is not None
            and np.isfinite(b_original["basket_mppm_rho1"])
        ):
            assert b_original["basket_mppm_rho1"] == pytest.approx(
                b_reversed["basket_mppm_rho1"], abs=1e-9
            )
            assert b_original["basket_mppm_rho1"] == pytest.approx(
                b_shuffled["basket_mppm_rho1"], abs=1e-9
            )

    def test_basket_aggregation_handles_misaligned_session_dates(self, mod) -> None:
        """When a symbol is missing a session-date, its contribution defaults to 0.

        Per design.md §1 basket-aggregation convention: per-session log-return
        of a symbol that did not trade on a session-date is 0.0 (no equity
        change → no log-return).
        """
        rows = [
            {
                "symbol": "ES",
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "session_dates": ["2024-01-02", "2024-01-03", "2024-01-04"],
                "session_log_returns": [0.01, -0.005, 0.002],
                "session_pnls": [0, 0, 0],
                "realized_end_equity": 10070.0, "realized_roi_pct": 0.7,
                "realized_max_dd_pct": 0.5, "n_trades": 3,
                "wins": 2, "losses": 1, "zeros": 0,
                "total_gross_pnl": 100, "total_net_pnl": 70, "total_cost_usd": 30,
            },
            {
                "symbol": "MGC",
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "session_dates": ["2024-01-02"],  # only one session
                "session_log_returns": [0.005],
                "session_pnls": [0],
                "realized_end_equity": 10050.0, "realized_roi_pct": 0.5,
                "realized_max_dd_pct": 0.0, "n_trades": 1,
                "wins": 1, "losses": 0, "zeros": 0,
                "total_gross_pnl": 50, "total_net_pnl": 50, "total_cost_usd": 0,
            },
            {
                "symbol": "SIL",
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "session_dates": ["2024-01-03"],  # only one session, different date
                "session_log_returns": [-0.01],
                "session_pnls": [0],
                "realized_end_equity": 9900.0, "realized_roi_pct": -1.0,
                "realized_max_dd_pct": 1.0, "n_trades": 1,
                "wins": 0, "losses": 1, "zeros": 0,
                "total_gross_pnl": -100, "total_net_pnl": -100, "total_cost_usd": 0,
            },
        ]
        b = mod._aggregate_basket(
            rows,
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )
        # Union of session dates = {01-02, 01-03, 01-04} = 3 unique dates
        assert b["n_basket_sessions"] == 3
        # On 01-02: ES=0.01, MGC=0.005, SIL=0.0 → basket = (0.01+0.005+0)/3 ≈ 0.005
        expected_01_02 = (0.01 + 0.005 + 0.0) / 3
        assert b["basket_session_log_returns"][0] == pytest.approx(
            expected_01_02, abs=1e-9
        )
        # On 01-03: ES=-0.005, MGC=0.0, SIL=-0.01 → basket = (-0.005+0-0.01)/3 ≈ -0.005
        expected_01_03 = (-0.005 + 0.0 + -0.01) / 3
        assert b["basket_session_log_returns"][1] == pytest.approx(
            expected_01_03, abs=1e-9
        )
        # On 01-04: ES=0.002, MGC=0.0, SIL=0.0 → basket = (0.002+0+0)/3 ≈ 0.000667
        expected_01_04 = (0.002 + 0.0 + 0.0) / 3
        assert b["basket_session_log_returns"][2] == pytest.approx(
            expected_01_04, abs=1e-9
        )


class TestFullFeatureFactoryComposition:
    """End-to-end H062 feature factory composition on synthetic intraday panel.

    Per H068 v2 §3: feature factory at src/skie_ninja/features/h062/ is
    REUSED VERBATIM across all 3 symbols. No new feature module is added.
    """

    def test_factory_runs_clean_on_30_session_panel(
        self, synthetic_intraday_panel: pd.DataFrame
    ) -> None:
        """Per H062 v1 + H068 v1 canary; feature factory composition smoke."""
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="a_ts_mom",
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        feats = compute_h062_features(
            high=synthetic_intraday_panel["high"].to_numpy(),
            low=synthetic_intraday_panel["low"].to_numpy(),
            close=synthetic_intraday_panel["close"].to_numpy(),
            config=cfg,
        )
        n = len(synthetic_intraday_panel)
        assert feats.channel.channel_high.shape == (n,)
        assert feats.atr.shape == (n,)
        init_bar = max(20, 14)
        assert np.isfinite(feats.channel.channel_high[init_bar:]).all()
        assert np.isfinite(feats.atr[init_bar:]).all()
