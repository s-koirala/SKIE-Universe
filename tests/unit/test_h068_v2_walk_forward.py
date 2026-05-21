"""H068 v2 walk-forward orchestrator unit tests.

Per H068 v2 design.md §11.2 `P1-H068-V2-WALK-FORWARD-ORCHESTRATOR-IMPL` +
`P1-H068-V2-BASKET-INVARIANT-TEST` + `P1-H068-V2-PER-SYMBOL-MPPM-CI-EMIT`.

Scope:
    - V2SweepConfig structure + grid construction (smoke vs full).
    - Per-symbol multiplier + capacity-cap dictionary.
    - Basket-aggregation helper: equal-weighted (1/3) sum across symbols
      + invariance to symbol ordering (Canary E per design.md §7).
    - Cost-friction-edge annotation propagation through per-symbol breakeven.
    - Cost-arm cost-model integration smoke (A0 zero-cost ≡ no subtraction).

Per Phase O.20 load-management directive: NO walk-forward execution; tests
exercise the orchestrator's public/internal helpers on small synthetic
fixtures only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import scripts.run_h068_v2_walk_forward as h068_v2_orchestrator


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def mod():
    return h068_v2_orchestrator


class TestV2SweepConfig:
    """V2SweepConfig dataclass + grid construction."""

    def test_v2_sweep_config_name_pattern(self, mod) -> None:
        cfg = mod.V2SweepConfig(
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
            use_current_equity_rebase=False,
        )
        assert cfg.name == "slip0.50_kelly0.25_A1_conservative_prior"
        assert cfg.is_a0_zero is False

    def test_v2_sweep_config_a0_zero_flag(self, mod) -> None:
        cfg = mod.V2SweepConfig(
            sensitivity_mult=1.0,
            kelly_multiplier=2.5,
            cost_arm="A0_zero",
            use_current_equity_rebase=False,
        )
        assert cfg.is_a0_zero is True

    def test_build_v2_sweep_configs_full_grid_cardinality(self, mod) -> None:
        """Full sweep = 3 slip × 6 Kelly × 2 arms = 36 cells PER SYMBOL.

        Per design.md §5 cardinality table.
        """
        cfgs = mod._build_v2_sweep_configs(smoke=False)
        assert len(cfgs) == 36
        # Check unique slip/Kelly/arm tuples are exactly the cross product
        triples = {(c.sensitivity_mult, c.kelly_multiplier, c.cost_arm) for c in cfgs}
        assert len(triples) == 36

    def test_build_v2_sweep_configs_smoke_grid_cardinality(self, mod) -> None:
        """Smoke sweep = 3 slip × 1 Kelly (=0.25) × 2 arms = 6 cells per symbol."""
        cfgs = mod._build_v2_sweep_configs(smoke=True)
        assert len(cfgs) == 6
        # All Kelly multipliers should be 0.25 in smoke mode
        assert {c.kelly_multiplier for c in cfgs} == {0.25}


class TestPerSymbolMultiplier:
    """Per-symbol multiplier + capacity caps."""

    def test_multiplier_dict_es_per_cme_spec(self, mod) -> None:
        """ES multiplier $50/pt per CME ES product spec (matches H068 v1)."""
        assert mod._PER_SYMBOL_MULTIPLIER["ES"] == 50.0

    def test_multiplier_dict_mgc_per_cme_spec(self, mod) -> None:
        """MGC multiplier $10/pt per CME Micro Gold product spec."""
        assert mod._PER_SYMBOL_MULTIPLIER["MGC"] == 10.0

    def test_multiplier_dict_sil_per_cme_spec(self, mod) -> None:
        """SIL multiplier $5/pt per CME Micro Silver product spec."""
        assert mod._PER_SYMBOL_MULTIPLIER["SIL"] == 5.0

    def test_capacity_cap_es_adr_0001(self, mod) -> None:
        """ES retail-tier cap = 20 per ADR-0001."""
        assert mod._PER_SYMBOL_CAPACITY_CAP["ES"] == 20

    def test_capacity_cap_micro_effectively_unbounded(self, mod) -> None:
        """MGC + SIL micro-class effectively unbounded at retail per design.md §11.1."""
        assert mod._PER_SYMBOL_CAPACITY_CAP["MGC"] == 999
        assert mod._PER_SYMBOL_CAPACITY_CAP["SIL"] == 999

    def test_symbols_tuple_3_assets_no_nq(self, mod) -> None:
        """v2 universe = {ES, MGC, SIL} per design.md §2; NQ excluded."""
        assert mod._SYMBOLS == ("ES", "MGC", "SIL")
        assert "NQ" not in mod._SYMBOLS


class TestBasketAggregationInvariance:
    """Canary E per design.md §7: symbol-order invariance of basket aggregation.

    Per `P1-H068-V2-BASKET-INVARIANT-TEST` (BLOCKING-BEFORE-LAUNCH).
    """

    def _build_synthetic_per_symbol_results(self, mod) -> list[dict]:
        """3 symbols × 1 (slip, kelly, arm) cell with known per-session log-returns."""
        # Use simple synthetic session dates and log-returns that allow easy
        # validation of the basket-aggregation result.
        dates_es = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
        dates_mgc = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
        dates_sil = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
        lr_es = [0.01, -0.02, 0.005, 0.015]
        lr_mgc = [0.005, 0.01, -0.005, 0.002]
        lr_sil = [-0.01, 0.005, 0.02, -0.003]

        def _build_row(symbol, dates, log_rets):
            return {
                "symbol": symbol,
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "session_dates": dates,
                "session_log_returns": log_rets,
                "session_pnls": [0.0] * len(dates),
                "realized_end_equity": 10100.0,
                "realized_roi_pct": 1.0,
                "realized_max_dd_pct": 2.0,
                "n_trades": 5,
                "wins": 3,
                "losses": 2,
                "zeros": 0,
                "total_gross_pnl": 100.0,
                "total_net_pnl": 100.0,
                "total_cost_usd": 25.0,
            }

        return [
            _build_row("ES", dates_es, lr_es),
            _build_row("MGC", dates_mgc, lr_mgc),
            _build_row("SIL", dates_sil, lr_sil),
        ]

    def test_basket_aggregate_equal_weight_sum(self, mod) -> None:
        """Per design.md §1: basket per-session log-return = (1/3) Σ per-symbol log-rets."""
        per_sym = self._build_synthetic_per_symbol_results(mod)
        b = mod._aggregate_basket(
            per_sym,
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )
        # Expected basket lr on 2024-01-02 = (0.01 + 0.005 + -0.01) / 3 ≈ 0.001667
        expected_lr_01_02 = (0.01 + 0.005 + -0.01) / 3
        # The basket_session_log_returns are in sorted-date order
        actual_lr_01_02 = b["basket_session_log_returns"][0]
        assert actual_lr_01_02 == pytest.approx(expected_lr_01_02, abs=1e-9)
        # 4 unique dates → 4 basket session log-returns
        assert len(b["basket_session_log_returns"]) == 4
        # n_symbols field reflects 3 contributing symbols
        assert b["n_symbols"] == 3

    def test_basket_aggregate_invariant_to_symbol_order(self, mod) -> None:
        """Canary E: shuffle symbol order; basket-aggregated MPPM must be invariant.

        Per design.md §7 Canary E `P1-H068-V2-BASKET-INVARIANT-TEST`.
        """
        per_sym = self._build_synthetic_per_symbol_results(mod)
        b1 = mod._aggregate_basket(
            per_sym,
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )
        # Reverse symbol order
        per_sym_rev = list(reversed(per_sym))
        b2 = mod._aggregate_basket(
            per_sym_rev,
            sensitivity_mult=0.5,
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )
        # The basket per-session log-return arrays must match exactly (sorted dates)
        np.testing.assert_array_almost_equal(
            np.array(b1["basket_session_log_returns"]),
            np.array(b2["basket_session_log_returns"]),
            decimal=12,
        )
        # basket realized ROI invariant
        assert b1["basket_realized_roi_pct"] == pytest.approx(
            b2["basket_realized_roi_pct"], abs=1e-9
        )

    def test_basket_aggregate_missing_cell_returns_error(self, mod) -> None:
        """When no per-symbol rows match the cell, aggregator returns an _error."""
        per_sym = self._build_synthetic_per_symbol_results(mod)
        # Try a (slip, kelly, arm) tuple not in per_sym
        b = mod._aggregate_basket(
            per_sym,
            sensitivity_mult=2.0,  # not in any row
            kelly_multiplier=0.25,
            cost_arm="A1_conservative_prior",
        )
        assert b["n_symbols"] == 0
        assert "_error" in b


class TestPerSymbolBreakevenAnnotation:
    """Per-symbol cost-friction-breakeven ratio + annotation per ADR-0028 §D-2."""

    def _build_a0_a1_pair(
        self, symbol: str, a0_roi: float, a1_roi: float, a0_gross: float, a1_cost: float
    ) -> list[dict]:
        """Build A0 + A1 cell rows at modal Kelly=0.25 + slip=0.5 cell."""
        return [
            {
                "symbol": symbol,
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A0_zero",
                "realized_roi_pct": a0_roi,
                "n_trades": 100,
                "total_gross_pnl": a0_gross,
                "total_cost_usd": 0.0,
            },
            {
                "symbol": symbol,
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "realized_roi_pct": a1_roi,
                "n_trades": 100,
                "total_gross_pnl": a0_gross,
                "total_cost_usd": a1_cost,
            },
        ]

    def test_breakeven_ratio_present_annotation(self, mod) -> None:
        """A0 ROI > 0 + A1 ROI < 0 + ratio ≥ 2 → cost-friction-dominated-edge-present.

        gross_edge_bps = 4000/100/10000*10000 = 4 bps; cost_bps = 1000/100/10000*10000 = 1 bps;
        ratio = 4 ≥ 2 → present.
        """
        rows = self._build_a0_a1_pair(
            "ES", a0_roi=+5.0, a1_roi=-1.0, a0_gross=4000.0, a1_cost=1000.0,
        )
        be = mod._compute_per_symbol_breakeven_ratio(
            rows, symbol="ES", sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert be["edge_annotation"] == "cost-friction-dominated-edge-present"
        assert be["ratio"] == pytest.approx(4.0, abs=1e-6)
        assert be["crosses_threshold"] is True

    def test_breakeven_ratio_absent_annotation_when_a1_does_not_flip(self, mod) -> None:
        """A0 ROI > 0 + A1 ROI ≥ 0 → cost-friction-dominated-edge-absent."""
        rows = self._build_a0_a1_pair(
            "MGC", a0_roi=+3.0, a1_roi=+2.5, a0_gross=3000.0, a1_cost=500.0,
        )
        be = mod._compute_per_symbol_breakeven_ratio(
            rows, symbol="MGC", sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert be["edge_annotation"] == "cost-friction-dominated-edge-absent"

    def test_breakeven_ratio_na_when_a0_missing(self, mod) -> None:
        """Missing A0 cell → cost-friction-dominated-edge-n/a."""
        rows = [
            {
                "symbol": "SIL",
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "realized_roi_pct": -1.0,
                "n_trades": 50,
                "total_gross_pnl": 1000.0,
                "total_cost_usd": 200.0,
            },
        ]
        be = mod._compute_per_symbol_breakeven_ratio(
            rows, symbol="SIL", sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert be["edge_annotation"] == "cost-friction-dominated-edge-n/a"


class TestEvaluateBasketH1:
    """Per-slip H_1 conjunctive criterion evaluation across the basket."""

    def _build_h1_fixture(self, mod, *, h1a: bool, h1b_excl: bool, h1c_clear: int) -> tuple:
        """Build a fixture for evaluate_basket_h_1.

        h1a: basket A1 ROI > 0
        h1b_excl: basket MPPM CI excludes zero positively
        h1c_clear: number of per-symbol cells that clear cost-friction ratio threshold
        """
        # Per-symbol rows for ES + MGC + SIL at slip=0.5 km=0.25
        per_sym = []
        for i, sym in enumerate(("ES", "MGC", "SIL")):
            # For symbols that clear threshold: large gross > small cost.
            if i < h1c_clear:
                a0_gross, a1_cost = 6000.0, 1000.0  # ratio = 6
                a0_roi, a1_roi = +5.0, -1.0  # A0 positive, A1 negative
            else:
                a0_gross, a1_cost = 200.0, 1000.0  # ratio = 0.2
                a0_roi, a1_roi = +0.1, +0.1  # absent class
            per_sym.append({
                "symbol": sym,
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A0_zero",
                "realized_roi_pct": a0_roi,
                "n_trades": 100,
                "total_gross_pnl": a0_gross,
                "total_cost_usd": 0.0,
                "session_dates": [], "session_log_returns": [],
            })
            per_sym.append({
                "symbol": sym,
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "realized_roi_pct": a1_roi,
                "n_trades": 100,
                "total_gross_pnl": a0_gross,
                "total_cost_usd": a1_cost,
                "session_dates": [], "session_log_returns": [],
            })
        basket = [
            {
                "sensitivity_mult": 0.5,
                "kelly_multiplier": 0.25,
                "cost_arm": "A1_conservative_prior",
                "basket_realized_roi_pct": (10.0 if h1a else -5.0),
                "basket_mppm_rho1_excludes_zero": h1b_excl,
                "basket_mppm_rho1": (0.5 if h1b_excl else 0.0),
            }
        ]
        return per_sym, basket

    def test_h_1_all_three_met(self, mod) -> None:
        """All 3 conjunctive criteria → h_1_conjunctive_met=True."""
        per_sym, basket = self._build_h1_fixture(
            mod, h1a=True, h1b_excl=True, h1c_clear=3
        )
        h1 = mod._evaluate_basket_h_1(
            per_sym, basket, sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert h1["h_1_conjunctive_met"] is True
        assert h1["h_1_a_meets"] is True
        assert h1["h_1_b_basket_mppm_excludes_zero_pos"] is True
        assert h1["h_1_c_meets"] is True
        assert h1["h_1_c_n_symbols_clear_threshold"] == 3

    def test_h_1_c_threshold_at_2_of_3_meets(self, mod) -> None:
        """2 of 3 symbols clearing ratio threshold → h_1_c_meets=True."""
        per_sym, basket = self._build_h1_fixture(
            mod, h1a=True, h1b_excl=True, h1c_clear=2
        )
        h1 = mod._evaluate_basket_h_1(
            per_sym, basket, sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert h1["h_1_c_meets"] is True
        assert h1["h_1_conjunctive_met"] is True

    def test_h_1_c_threshold_at_1_of_3_fails(self, mod) -> None:
        """Only 1 of 3 symbols clearing → h_1_c_meets=False."""
        per_sym, basket = self._build_h1_fixture(
            mod, h1a=True, h1b_excl=True, h1c_clear=1
        )
        h1 = mod._evaluate_basket_h_1(
            per_sym, basket, sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert h1["h_1_c_meets"] is False
        assert h1["h_1_conjunctive_met"] is False

    def test_h_1_b_ci_includes_zero_fails(self, mod) -> None:
        """MPPM CI covers zero → h_1_b fails → conjunctive fails."""
        per_sym, basket = self._build_h1_fixture(
            mod, h1a=True, h1b_excl=False, h1c_clear=3
        )
        h1 = mod._evaluate_basket_h_1(
            per_sym, basket, sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert h1["h_1_b_basket_mppm_excludes_zero_pos"] is False
        assert h1["h_1_conjunctive_met"] is False

    def test_h_1_a_basket_roi_negative_fails(self, mod) -> None:
        """Basket ROI < 0 → h_1_a fails → conjunctive fails."""
        per_sym, basket = self._build_h1_fixture(
            mod, h1a=False, h1b_excl=True, h1c_clear=3
        )
        h1 = mod._evaluate_basket_h_1(
            per_sym, basket, sensitivity_mult=0.5, kelly_multiplier=0.25
        )
        assert h1["h_1_a_meets"] is False
        assert h1["h_1_conjunctive_met"] is False


class TestRunContextHookSurface:
    """The orchestrator main() uses RunContext to emit canonical ReproLog.

    Per `P1-H068-V2-REPROLOG-WIRE` BLOCKING-BEFORE-V2-EMISSION. This test
    verifies the integration surface only — full main() execution is the
    operator-authorized walk-forward cycle per Phase O.20 load directive.
    """

    def test_main_function_exists_and_is_callable(self, mod) -> None:
        """The main() entrypoint must exist + be callable from outside __main__."""
        assert callable(mod.main)

    def test_blas_pin_check_in_main_module(self, mod) -> None:
        """The orchestrator carries the canonical ADR-0009 BLAS-pinning guard.

        We verify the constants are imported correctly; full guard execution
        runs at `__main__` only (not during module import).
        """
        # Sanity: the orchestrator source contains the canonical pinning vars
        src = (
            _REPO_ROOT / "scripts" / "run_h068_v2_walk_forward.py"
        ).read_text(encoding="utf-8")
        assert "OMP_NUM_THREADS" in src
        assert "MKL_NUM_THREADS" in src
        assert "OPENBLAS_NUM_THREADS" in src
        assert "ADR-0009" in src

    def test_repro_log_wire_invokes_run_context(self, mod) -> None:
        """Verify the main() function instantiates RunContext per `P1-H068-V2-REPROLOG-WIRE`."""
        src = (
            _REPO_ROOT / "scripts" / "run_h068_v2_walk_forward.py"
        ).read_text(encoding="utf-8")
        assert "RunContext(" in src
        # The hypothesis_id field is the load-bearing binding
        assert 'hypothesis_id="H068_v2"' in src


class TestSubwindowDates:
    """ADR-0026 §D-1 §0 3-component header component 2: 2026-04-01 → 2026-05-15."""

    def test_subwindow_start_2026_04_01(self, mod) -> None:
        import pandas as pd
        assert mod._SUBWINDOW_START == pd.Timestamp("2026-04-01", tz="UTC").date()

    def test_subwindow_end_2026_05_15(self, mod) -> None:
        import pandas as pd
        assert mod._SUBWINDOW_END == pd.Timestamp("2026-05-15", tz="UTC").date()


class TestCostFrictionEdgeAnnotationFlow:
    """ADR-0028 §D-2 cost-friction-edge annotation flows from CLI flags to sidecar."""

    def test_zero_cost_reference_cli_flags_present_in_source(self, mod) -> None:
        """The 3 ADR-0028 §D-2 CLI flags are present in the orchestrator argparse."""
        src = (
            _REPO_ROOT / "scripts" / "run_h068_v2_walk_forward.py"
        ).read_text(encoding="utf-8")
        assert "--zero-cost-reference-run-id" in src
        assert "--zero-cost-reference-basket-pct" in src
        assert "--zero-cost-reference-sidecar-sha-prefix16" in src

    def test_adr_0025_opt_in_cli_flags_present_in_source(self, mod) -> None:
        """The 3 ADR-0025 opt-in CLI flags are present per design.md §11.1."""
        src = (
            _REPO_ROOT / "scripts" / "run_h068_v2_walk_forward.py"
        ).read_text(encoding="utf-8")
        assert "--enable-kill-switch-runtime" in src
        assert "--enable-equity-rebase-current" in src
        assert "--cost-model" in src

    def test_cost_friction_edge_primitive_imported(self, mod) -> None:
        """Cost-friction-edge primitive from src/skie_ninja/inference/cost_friction_edge.py."""
        assert hasattr(mod, "cost_friction_dominated_edge_annotation")
        assert hasattr(mod, "build_cost_friction_edge_block")


class TestRngSeedAndBootstrapConstants:
    """Per design.md §12: rng_seed=20260520 + n_bootstrap=1000."""

    def test_rng_seed_is_20260520(self, mod) -> None:
        assert mod._RNG_SEED == 20260520

    def test_n_bootstrap_is_1000(self, mod) -> None:
        assert mod._N_BOOTSTRAP_CI == 1000

    def test_n_min_trades_guard_per_symbol_50(self, mod) -> None:
        """Per design.md §9 + Tharp 1998 *practitioner* n ≥ 30."""
        assert mod._N_MIN_TRADES_GUARD_PER_SYMBOL == 50

    def test_n_min_trades_guard_basket_150(self, mod) -> None:
        """Per design.md §9: basket-level n_min = 3 × 50 = 150."""
        assert mod._N_MIN_TRADES_GUARD_BASKET == 150

    def test_cost_friction_threshold_is_2(self, mod) -> None:
        """Per ADR-0028 §D-2 cost-friction-dominated-edge-present ratio threshold."""
        assert mod._COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD == 2.0


class TestSlipKellyCostArmGrids:
    """v2 cell-grid axes per design.md §5."""

    def test_slip_cells_3_values(self, mod) -> None:
        """3 slip cells {0.25, 0.5, 1.0}."""
        assert mod._SLIP_CELLS == (0.25, 0.5, 1.0)

    def test_kelly_cells_6_values(self, mod) -> None:
        """6 Kelly multiplier cells {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}."""
        assert mod._KELLY_CELLS == (0.25, 0.5, 1.0, 1.5, 2.0, 2.5)

    def test_cost_arms_2_values(self, mod) -> None:
        """2 cost arms: A0 zero + A1 conservative-prior."""
        assert mod._COST_ARMS == ("A0_zero", "A1_conservative_prior")
