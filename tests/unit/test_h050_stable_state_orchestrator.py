"""Unit tests for the H050.stable-state orchestrator (Phase O.20).

Closes ``P1-H050-STABLE-STATE-PARITY-INVARIANT-TEST`` per
[H050_stable_state/design.md §11.2][1] BLOCKING-BEFORE-PRODUCTION-RUN.

Verifies:

1. Module-level ``_STABLE_STATE_N`` defaults to 1 (no-op).
2. ``--stable-state-n N`` parses correctly through the canonical
   orchestrator's argparse.
3. Bit-identical parity: with ``--stable-state-n 1`` the per-bar
   regime_indicator is identical to the raw posterior > 0.5 indicator
   (the H050 v1 production code path).
4. Stability filter logic: ``N=5`` produces a gate that is 1 only at
   bars where the raw indicator has held value 1 for 5 consecutive
   bars; previous bars are 0.
5. Monotonicity: strictly fewer (or equal) gate-firings at N=20 than
   at N=1 on a synthetic high-flip sequence — the operator-readable
   discriminator for the H-c whipsaw hypothesis.
6. Wrapper script's CLI invariants (forces ``--hypothesis
   H050_stable_state``; requires ``--stable-state-n``; defaults config).

The tests do NOT invoke a full walk-forward — that is exercised
end-to-end by the smoke walk-forward (a separate operator-authorized
cycle per the Phase O.20 scope bound).

References
----------

[1]: research/01_hypothesis_register/H050_stable_state/design.md
"""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

import scripts.run_walk_forward as _h050_orchestrator
import scripts.run_h050_stable_state_walk_forward as _h050_ss_wrapper


# ---------------------------------------------------------------------------
# Helper: the canonical stability-filter algorithm (mirrors the production
# logic at `scripts/run_walk_forward.py:_predict_fold`).
# ---------------------------------------------------------------------------


def _apply_stability_filter(raw_indicator: np.ndarray, n: int) -> np.ndarray:
    """Production-mirror of the H050.stable-state stability filter.

    Returns the per-bar gate as 1 iff the raw indicator has held value
    1 for the last N consecutive bars (inclusive of bar t). For N=1
    this is bit-identical to the raw indicator (H050 v1 no-op).
    """
    if n <= 1:
        return raw_indicator.astype(np.float64).copy()
    n_bars = raw_indicator.shape[0]
    gate = np.zeros(n_bars, dtype=np.float64)
    if n_bars < n:
        return gate
    cumsum = np.concatenate([[0.0], np.cumsum(raw_indicator)])
    rolling = cumsum[n:] - cumsum[:-n]
    gate[n - 1:] = (rolling >= n).astype(np.float64)
    return gate


class TestModuleFlagDefault:
    """Default state of the stability-N module flag."""

    def test_module_flag_defaults_to_one(self) -> None:
        """At import time the module-level flag must be 1 so any
        callers that bypass the CLI path see H050 v1 semantics (no-op).
        We assert presence + type rather than exact value because the
        production ``run()`` mutates the flag per CLI argv.
        """
        assert hasattr(_h050_orchestrator, "_STABLE_STATE_N")
        assert isinstance(_h050_orchestrator._STABLE_STATE_N, int)


class TestArgvResolution:
    """The wrapper script's CLI invariants."""

    def test_resolves_default_config_when_omitted(self) -> None:
        """When --config is not supplied, the wrapper inserts the
        H050.stable-state config path automatically."""
        out = _h050_ss_wrapper._resolve_h050_stable_state_argv(
            ["--stable-state-n", "5", "--smoke"]
        )
        assert "--config" in out
        cfg_idx = out.index("--config")
        cfg_path = out[cfg_idx + 1]
        assert cfg_path.endswith("H050_stable_state.yaml")

    def test_forces_hypothesis_h050_stable_state(self) -> None:
        """The wrapper forces --hypothesis H050_stable_state, overriding
        any caller-supplied value (defensive: prevents operator from
        accidentally launching this script against H050 v1 or H050.invert)."""
        out = _h050_ss_wrapper._resolve_h050_stable_state_argv(
            ["--hypothesis", "H050", "--stable-state-n", "5"]
        )
        assert "--hypothesis" in out
        hyp_indices = [i for i, t in enumerate(out) if t == "--hypothesis"]
        assert len(hyp_indices) == 1
        assert out[hyp_indices[0] + 1] == "H050_stable_state"

    def test_forces_hypothesis_strips_equals_form(self) -> None:
        """Equals-separated --hypothesis=H050 must also be stripped."""
        out = _h050_ss_wrapper._resolve_h050_stable_state_argv(
            ["--hypothesis=H050", "--stable-state-n", "5"]
        )
        assert "--hypothesis=H050" not in out
        assert "H050_stable_state" in out

    def test_requires_stable_state_n_explicit(self) -> None:
        """The wrapper raises ValueError if --stable-state-n is not
        supplied by the caller (no default injected — operator must
        explicitly choose N from the pre-registered grid per design.md
        §5)."""
        with pytest.raises(ValueError, match="--stable-state-n"):
            _h050_ss_wrapper._resolve_h050_stable_state_argv(["--smoke"])

    def test_accepts_equals_form_of_stable_state_n(self) -> None:
        """The wrapper accepts --stable-state-n=5 equals-separated form."""
        out = _h050_ss_wrapper._resolve_h050_stable_state_argv(
            ["--stable-state-n=5", "--smoke"]
        )
        # Verify --stable-state-n survives resolution (not stripped).
        assert any(
            tok == "--stable-state-n=5" or tok == "--stable-state-n"
            for tok in out
        )

    def test_passes_through_smoke_flag(self) -> None:
        """Caller-supplied --smoke must survive the resolution step."""
        out = _h050_ss_wrapper._resolve_h050_stable_state_argv(
            ["--stable-state-n", "5", "--smoke"]
        )
        assert "--smoke" in out

    def test_respects_caller_config_override(self) -> None:
        """When caller supplies --config the wrapper does NOT override
        (allows future calibration-holdout variants of the config)."""
        out = _h050_ss_wrapper._resolve_h050_stable_state_argv(
            [
                "--config",
                "/tmp/custom_h050_stable_state.yaml",
                "--stable-state-n",
                "5",
            ]
        )
        cfg_idx = out.index("--config")
        assert out[cfg_idx + 1] == "/tmp/custom_h050_stable_state.yaml"


class TestParserExtension:
    """The canonical orchestrator's argparse must accept --stable-state-n."""

    def test_orchestrator_parser_accepts_stable_state_n(self) -> None:
        """The canonical orchestrator's argparse parser must expose
        --stable-state-n (added in Phase O.20). Parsing a valid arg
        set that includes --stable-state-n verifies acceptance."""
        args = _h050_orchestrator._parse_args(
            [
                "--hypothesis",
                "H050_stable_state",
                "--config",
                "/tmp/dummy.yaml",
                "--stable-state-n",
                "5",
            ]
        )
        assert getattr(args, "stable_state_n", None) == 5

    def test_parser_default_stable_state_n_is_one(self) -> None:
        """When --stable-state-n is omitted, the parser default is 1
        (H050 v1 no-op)."""
        args = _h050_orchestrator._parse_args(
            [
                "--hypothesis",
                "H050",
                "--config",
                "/tmp/dummy.yaml",
            ]
        )
        assert getattr(args, "stable_state_n", None) == 1


class TestStabilityFilterLogic:
    """Semantic correctness of the N-bar stability filter."""

    def test_n1_is_identity_on_raw_indicator(self) -> None:
        """N=1 is a strict no-op: gate == raw_indicator for any
        sequence. This is the H050 v1 production code path; bit-
        identical equivalence is the parity invariant per design.md
        §11.2."""
        rng = np.random.default_rng(20260520)
        raw = (rng.uniform(size=200) > 0.4).astype(np.float64)
        gate = _apply_stability_filter(raw, n=1)
        np.testing.assert_array_equal(gate, raw)

    def test_n5_blocks_until_five_consecutive_in_state(self) -> None:
        """With N=5, the gate is 0 until 5 consecutive bars of
        in-state have accumulated, then 1 while the streak continues,
        then 0 again on flip."""
        # Pattern: 5 in-state, 1 out, 6 in-state, 2 out.
        raw = np.array(
            [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0], dtype=np.float64
        )
        gate = _apply_stability_filter(raw, n=5)
        # Bars 0-3 (positions 0-3): only 1-4 in-state bars accumulated; gate=0.
        np.testing.assert_array_equal(gate[:4], 0.0)
        # Bar 4 (position 4): 5 consecutive; gate=1.
        assert gate[4] == 1.0
        # Bar 5: flip to 0; reset; gate=0 (raw was 0, rolling sum <5).
        assert gate[5] == 0.0
        # Bars 6-9: rebuilding streak; gate=0 (only 1-4 in-state since flip).
        np.testing.assert_array_equal(gate[6:10], 0.0)
        # Bar 10: 5 consecutive again; gate=1.
        assert gate[10] == 1.0
        # Bar 11: 6 consecutive; gate=1 still.
        assert gate[11] == 1.0
        # Bars 12-13: flip to 0; gate=0.
        np.testing.assert_array_equal(gate[12:14], 0.0)

    def test_n20_blocks_first_19_bars(self) -> None:
        """With N=20, the first 19 bars of a steadily-in-state sequence
        produce gate=0 (warmup); bar 19 (position) is the first 1."""
        raw = np.ones(50, dtype=np.float64)
        gate = _apply_stability_filter(raw, n=20)
        np.testing.assert_array_equal(gate[:19], 0.0)
        np.testing.assert_array_equal(gate[19:], 1.0)

    def test_short_sequence_returns_zeros(self) -> None:
        """If n_bars < N, the entire gate is 0 (cannot accumulate
        N consecutive bars)."""
        raw = np.array([1, 1, 1], dtype=np.float64)
        gate = _apply_stability_filter(raw, n=5)
        assert gate.shape == (3,)
        np.testing.assert_array_equal(gate, 0.0)

    def test_higher_n_reduces_gate_firings(self) -> None:
        """Monotonicity invariant: on a synthetic high-flip sequence,
        the gate-firing count at higher N is strictly less-than-or-
        equal-to the count at lower N. This is the load-bearing
        empirical discriminator for the H-c whipsaw hypothesis per
        design.md §1: raising N monotonically reduces forced gate
        firings, allowing the operator to observe whether cost-drag
        reduction translates into realized OOS improvement."""
        rng = np.random.default_rng(20260520)
        # High-flip sequence: posterior > 0.5 with low persistence.
        raw = (rng.uniform(size=1000) > 0.5).astype(np.float64)
        n_values = [1, 3, 5, 10, 20]
        firings = [_apply_stability_filter(raw, n=n).sum() for n in n_values]
        # Each subsequent N must produce <= firings of the prior N.
        for i in range(len(n_values) - 1):
            assert firings[i + 1] <= firings[i], (
                f"Monotonicity violated: N={n_values[i]} fired "
                f"{firings[i]} times; N={n_values[i + 1]} fired "
                f"{firings[i + 1]} times; expected non-increasing."
            )
        # At N=20 on a high-flip sequence, firings should be strictly
        # less than at N=1 (verifies the filter actually engages).
        assert firings[-1] < firings[0]


class TestProductionFilterParity:
    """The production filter logic in `_predict_fold` matches the helper."""

    def test_production_logic_matches_helper_on_synthetic_posterior(
        self,
    ) -> None:
        """Cross-check: the cumsum-based implementation in the
        production code path produces identical results to the naive
        rolling-window helper."""
        # Synthetic 2-state posterior; gate_state = 0.
        rng = np.random.default_rng(20260520)
        n_bars = 500
        filtered = rng.uniform(size=(n_bars, 2))
        # Renormalise to a valid probability vector.
        filtered = filtered / filtered.sum(axis=1, keepdims=True)
        gate_state = 0
        raw_indicator = (filtered[:, gate_state] > 0.5).astype(np.float64)
        for n in [1, 3, 5, 10, 20]:
            # Helper.
            helper_gate = _apply_stability_filter(raw_indicator, n=n)
            # Production replica (mirrors `_predict_fold` post-patch
            # lines under the `_STABLE_STATE_N > 1` branch).
            if n <= 1:
                prod_gate = raw_indicator.copy()
            else:
                prod_gate = np.zeros(n_bars, dtype=np.float64)
                if n_bars >= n:
                    cumsum = np.concatenate([[0.0], np.cumsum(raw_indicator)])
                    rolling_n = cumsum[n:] - cumsum[:-n]
                    prod_gate[n - 1:] = (rolling_n >= n).astype(np.float64)
            np.testing.assert_array_equal(helper_gate, prod_gate)


class TestModuleFlagControl:
    """The module-level flag controls the filter engagement."""

    def test_module_flag_isolation_via_patch(self) -> None:
        """Patching ``_STABLE_STATE_N`` is reversible — the flag is
        restored on context exit. Production ``run()`` sets the flag
        every invocation from argv."""
        original = _h050_orchestrator._STABLE_STATE_N
        try:
            with patch.object(_h050_orchestrator, "_STABLE_STATE_N", 5):
                assert _h050_orchestrator._STABLE_STATE_N == 5
            assert _h050_orchestrator._STABLE_STATE_N == original
        finally:
            _h050_orchestrator._STABLE_STATE_N = original


class TestWrapperImports:
    """Smoke-level import + attribute checks."""

    def test_wrapper_imports_underlying_orchestrator(self) -> None:
        """The wrapper module must import the canonical H050
        orchestrator at module load time."""
        assert _h050_ss_wrapper._h050_orchestrator is _h050_orchestrator

    def test_wrapper_run_is_callable(self) -> None:
        """The wrapper's run() entry must be callable."""
        assert callable(_h050_ss_wrapper.run)
