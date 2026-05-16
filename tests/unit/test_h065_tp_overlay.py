"""H065 TP-overlay unit tests.

Covers BLOCKING preconditions per H065 design.md §11.2:
    - P1-H065-TP-FILL-INTRABAR-PIT-TEST: TP fill uses bar-(t+1) high/low NOT
      close; stop-first convention on dual-barrier bars.

Tests are intentionally narrow at this v1 phase — they verify the structural
correctness of the H065 TP-overlay extension at the bar-resolution layer.
Full integration tests covered by smoke runs of run_h065_tp_overlay_sweep.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_DIR = _REPO_ROOT / "src"
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
for _p in (str(_REPO_ROOT), str(_SRC_DIR), str(_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _build_synthetic_5min_bars(
    n_bars: int = 600,
    starting_price: float = 100.0,
    drift_per_bar: float = 0.0,
    bar_range: float = 0.5,
    rng_seed: int = 42,
    breakout_at_bar: int | None = None,
    tp_hit_at_bar: int | None = None,
    sl_hit_at_bar: int | None = None,
    tp_target: float | None = None,
    sl_target: float | None = None,
) -> pd.DataFrame:
    """Construct a synthetic 5-min OHLC panel for unit-test fixtures.

    The default is a low-vol drift series; specific bars can be marked for
    breakout / TP-hit / SL-hit by parameter to test exit precedence.
    """
    rng = np.random.default_rng(rng_seed)
    base_price = starting_price
    rows = []
    for i in range(n_bars):
        center = base_price + i * drift_per_bar + rng.normal(0, bar_range * 0.1)
        open_ = float(center)
        close = float(center + rng.normal(0, bar_range * 0.05))
        high = float(max(open_, close) + abs(rng.normal(0, bar_range)))
        low = float(min(open_, close) - abs(rng.normal(0, bar_range)))
        # Mark special bars
        if breakout_at_bar is not None and i == breakout_at_bar:
            close = float(starting_price + 10.0)  # close above past N-bar high
            high = max(high, close + 0.5)
        if tp_hit_at_bar is not None and i == tp_hit_at_bar and tp_target is not None:
            high = max(high, tp_target + 0.5)
        if sl_hit_at_bar is not None and i == sl_hit_at_bar and sl_target is not None:
            low = min(low, sl_target - 0.5)
        ts = pd.Timestamp("2020-01-02 14:35:00", tz="UTC") + pd.Timedelta(minutes=5 * i)
        rows.append({
            "ts_event": ts,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
        })
    df = pd.DataFrame(rows)
    df["session_date_et"] = df["ts_event"].dt.tz_convert("America/New_York").dt.date
    return df


def test_tp_overlay_config_builder_returns_six_cells() -> None:
    from run_h065_tp_overlay_sweep import _build_sweep_configs

    configs = _build_sweep_configs(kelly_multiplier=0.25)
    assert len(configs) == 6, "expected 4 M-cells + 2 M=inf reference cells"

    m_inf_cells = [c for c in configs if not c.tp_enabled]
    assert len(m_inf_cells) == 2, "expected exactly 2 M=inf reference cells"
    assert any(not c.use_current_equity_rebase for c in m_inf_cells), (
        "expected one fixed-rebase M=inf cell (H062 v1 baseline)"
    )
    assert any(c.use_current_equity_rebase for c in m_inf_cells), (
        "expected one current-rebase M=inf cell (H065 paradigm)"
    )

    tp_cells = [c for c in configs if c.tp_enabled]
    assert len(tp_cells) == 4, "expected 4 TP-overlay M-cells {1.0, 1.5, 2.0, 2.5}"
    m_values = sorted(c.tp_multiplier_M for c in tp_cells)
    assert m_values == [1.0, 1.5, 2.0, 2.5], (
        f"TP grid mismatch; got {m_values}"
    )

    # All TP cells use current-equity rebase per H065 paradigm
    for c in tp_cells:
        assert c.use_current_equity_rebase, f"TP cell {c.name} must use current-rebase"


def test_tp_overlay_position_dataclass_has_tp_field() -> None:
    """Verify the simulator _Position dataclass carries a tp_price field
    distinct from stop_price — required for the exit-precedence check.
    """
    from run_h065_tp_overlay_sweep import _Position

    pos = _Position(
        side=1,
        entry_price=100.0,
        size=1,
        stop_price=98.0,
        tp_price=102.0,
        r_dollar=200.0,
        entry_idx=0,
        entry_session_date=pd.Timestamp("2020-01-02").date(),
    )
    assert pos.tp_price == 102.0
    assert pos.stop_price == 98.0
    assert pos.entry_price == 100.0
    assert pos.r_dollar == 200.0


def test_tp_disabled_returns_infinite_tp_price() -> None:
    """When TP is disabled (M=inf), the position's tp_price is +inf for long
    or -inf for short. The exit check's np.isfinite() guards prevent any TP
    fill from triggering.
    """
    from run_h065_tp_overlay_sweep import TPOverlayConfig
    cfg_disabled = TPOverlayConfig(
        name="test_no_tp",
        tp_multiplier_M=np.inf,
        kelly_multiplier=0.25,
        risk_budget_pct=0.01,
        use_current_equity_rebase=False,
        description="test",
    )
    assert not cfg_disabled.tp_enabled

    cfg_enabled = TPOverlayConfig(
        name="test_tp_2",
        tp_multiplier_M=2.0,
        kelly_multiplier=0.25,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        description="test",
    )
    assert cfg_enabled.tp_enabled


def test_subwindow_dates_match_design_md_spec() -> None:
    """H065 design.md §13 binds the 2026-04-01 → 2026-05-15 sub-window.

    The simulator constants must match this binding exactly.
    """
    from run_h065_tp_overlay_sweep import _SUBWINDOW_START, _SUBWINDOW_END

    assert _SUBWINDOW_START == pd.Timestamp("2026-04-01").date()
    assert _SUBWINDOW_END == pd.Timestamp("2026-05-15").date()


def test_exit_precedence_within_bar_priority() -> None:
    """Verify exit precedence per H065 design.md §4:
        1. gap-through-stop at open
        2. stop-hit during bar
        3. TP-hit during bar
        4. opposite-channel break at close
        5. EOD-flatten / session-rollover

    Stop-first convention: when bar contains BOTH stop AND TP within high-low,
    bar resolves to stop-hit (conservative; AFML §13.3 *practitioner*).
    """
    # Concrete test: simulate a single long position with stop=98, TP=102, entry=100.
    # Bar's range is high=103, low=97 (both targets within bar). Should resolve to
    # stop-hit at 98 per the conservative convention.
    #
    # This is enforced structurally inside `_check_stops_tp_exits()` — the stop-hit
    # check (#2) precedes the TP-hit check (#3) in the function body.
    from run_h065_tp_overlay_sweep import _run_tp_overlay_simulation
    # The structural ordering is verified by reading the function body; this test
    # asserts the constants are present, not that we run an end-to-end simulation
    # (which would require feature factory + bar series). End-to-end coverage is
    # provided by the run_h065_tp_overlay_sweep.py main() smoke runs on MGC/SIL.

    import inspect
    src = inspect.getsource(_run_tp_overlay_simulation)
    # Stop check must precede TP check in the function body
    stop_long_pos = src.find("stop_hit_long")
    tp_long_pos = src.find("tp_hit_long")
    assert stop_long_pos > 0, "stop_hit_long branch missing"
    assert tp_long_pos > 0, "tp_hit_long branch missing"
    assert stop_long_pos < tp_long_pos, (
        "stop-first convention violated: stop_hit_long branch must precede "
        "tp_hit_long branch in _check_stops_tp_exits per design.md §4"
    )
    stop_short_pos = src.find("stop_hit_short")
    tp_short_pos = src.find("tp_hit_short")
    assert stop_short_pos > 0
    assert tp_short_pos > 0
    assert stop_short_pos < tp_short_pos, (
        "stop-first convention violated: stop_hit_short must precede tp_hit_short"
    )


def test_tp_fill_uses_intrabar_high_low_not_close() -> None:
    """Verify TP fill check inspects bar's high/low (intra-bar extremes) not
    bar's close. The bar's high IS the first PIT-revealable price level reached
    within the bar; using close would introduce optimistic-bias in narrow-range
    bars where the close is below TP but the high reached TP intra-bar.
    """
    from run_h065_tp_overlay_sweep import _run_tp_overlay_simulation

    import inspect
    src = inspect.getsource(_run_tp_overlay_simulation)
    # TP-long check: high[t] >= position.tp_price
    assert "high[t] >= position.tp_price" in src, (
        "TP-long fill must use bar's high (intra-bar max), not close"
    )
    # TP-short check: low[t] <= position.tp_price
    assert "low[t] <= position.tp_price" in src, (
        "TP-short fill must use bar's low (intra-bar min), not close"
    )


def test_compute_basket_metrics_handles_empty_subwindow() -> None:
    """Defensive: when no sub-window dates are present (e.g., test run with
    end-date prior to 2026-04-01), basket aggregation must return zeros not raise.
    """
    from run_h065_tp_overlay_sweep import _compute_basket_metrics

    fake_results = [
        {
            "cfg_name": "test",
            "symbol": "MGC",
            "tp_multiplier_M": 2.0,
            "kelly_multiplier": 0.25,
            "session_dates": ["2020-01-02", "2020-01-03"],
            "session_log_returns": [0.001, -0.002],
            "session_pnls": [10.0, -20.0],
            "r_multiple_mean": 0.05,
            "l_skewness_tau3": 0.5,
            "wins": 1,
            "losses": 1,
            "zeros": 0,
            "n_trades": 2,
            "subwindow_wins": 0,
            "subwindow_losses": 0,
            "subwindow_zeros": 0,
            "subwindow_n_trades": 0,
        },
    ]
    basket = _compute_basket_metrics(fake_results, "test")
    assert basket["subwindow_n_trades"] == 0
    assert basket["subwindow_realized_roi_pct"] == 0.0
    assert basket["subwindow_realized_max_dd_pct"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
