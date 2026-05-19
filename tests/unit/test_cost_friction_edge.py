"""Unit tests for [src/skie_ninja/inference/cost_friction_edge.py](../../src/skie_ninja/inference/cost_friction_edge.py).

Per ADR-0028 §D-2 trigger semantics. Covers all three annotation values
plus the documented edge cases:
- `n/a` when cost-zero (case (i) fails)
- `absent` when cost-applied + OOS > 0 (case (ii) fails)
- `absent` when cost-applied + OOS < 0 + no zero-cost reference (case (iii) fails — no ref)
- `absent` when cost-applied + OOS < 0 + zero-cost reference is also ≤ 0 (case (iii) fails — ref non-positive)
- `present` when all 3 conditions hold (the H062 v3 vs A0 baseline canonical case)
"""

from __future__ import annotations

import pytest

from skie_ninja.inference.cost_friction_edge import (
    CostFrictionEdgeResult,
    ZeroCostReferenceCell,
    build_cost_friction_edge_block,
    cost_friction_dominated_edge_annotation,
)


class TestNaCase:
    """Condition (i) fails: cost_model is `cost-zero`."""

    def test_cost_zero_emits_n_a(self):
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-zero",
            realized_oos_basket_pct=-50.0,
            zero_cost_reference_cell=None,
        )
        assert result.annotation == "cost-friction-dominated-edge-n/a"
        assert "cost-zero" in result.rationale.lower()

    def test_cost_zero_with_positive_basket_still_n_a(self):
        # Cost-zero ALWAYS emits n/a regardless of basket sign — the annotation
        # is unevaluable without a cost-applied cell.
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-zero",
            realized_oos_basket_pct=+261.88,
            zero_cost_reference_cell=None,
        )
        assert result.annotation == "cost-friction-dominated-edge-n/a"

    def test_unrecognized_annotation_falls_to_n_a(self):
        """Defensive: unrecognized cost_model_annotation value → n/a."""
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-unknown-future-mode",
            realized_oos_basket_pct=-50.0,
            zero_cost_reference_cell=None,
        )
        assert result.annotation == "cost-friction-dominated-edge-n/a"
        assert "unrecognized" in result.rationale.lower()


class TestAbsentCase:
    """Conditions (ii) or (iii) fail."""

    def test_cost_applied_positive_basket_emits_absent(self):
        """Condition (ii) fails: cost-applied basket > 0."""
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-conservative-prior",
            realized_oos_basket_pct=+5.0,
            zero_cost_reference_cell=None,
        )
        assert result.annotation == "cost-friction-dominated-edge-absent"
        assert "net-positive" in result.rationale.lower()

    def test_cost_applied_negative_no_reference_emits_absent(self):
        """Condition (iii) fails: no zero-cost reference cell provided."""
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-conservative-prior",
            realized_oos_basket_pct=-99.9995,
            zero_cost_reference_cell=None,
        )
        assert result.annotation == "cost-friction-dominated-edge-absent"
        assert "no zero-cost reference" in result.rationale.lower()
        assert result.zero_cost_reference_provided is False

    def test_cost_applied_negative_reference_also_negative_emits_absent(self):
        """Condition (iii) fails: zero-cost reference is ≤ 0 → no gross edge."""
        ref = ZeroCostReferenceCell(
            run_id="reference_run_aaa",
            sidecar_sha_prefix16="aaaaaaaaaaaaaaaa",
            realized_oos_basket_pct=-20.0,
        )
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-conservative-prior",
            realized_oos_basket_pct=-50.0,
            zero_cost_reference_cell=ref,
        )
        assert result.annotation == "cost-friction-dominated-edge-absent"
        assert "also non-positive" in result.rationale.lower()
        assert result.zero_cost_reference_provided is True
        assert result.zero_cost_reference_run_id == "reference_run_aaa"

    def test_cost_applied_zero_basket_with_ref_emits_absent(self):
        """Edge case: cost-applied basket exactly 0 → condition (ii) fails (not <0)."""
        ref = ZeroCostReferenceCell(
            run_id="ref",
            sidecar_sha_prefix16="b" * 16,
            realized_oos_basket_pct=+10.0,
        )
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-conservative-prior",
            realized_oos_basket_pct=0.0,
            zero_cost_reference_cell=ref,
        )
        # 0.0 is NOT strictly less than 0 → condition (ii) fails.
        assert result.annotation == "cost-friction-dominated-edge-absent"


class TestPresentCase:
    """All 3 conditions hold — the H062 v3 canonical case."""

    def test_h062_v3_anchor_emits_present(self):
        """The empirical anchor: H062 v3 vs A0 baseline ablation.

        Per ADR-0028 §Context table:
          - A0 baseline (zero-cost): basket = +261.88%
          - Ref-v3 (all 3 ON, conservative-prior): basket = −99.9995%
        """
        a0_ref = ZeroCostReferenceCell(
            run_id="5e52f0b7ddd94ecea3187566c0e255d0",  # ADR-0028 §Context A0
            sidecar_sha_prefix16="aaaaaaaaaaaaaaaa",  # placeholder; real SHA from sidecar
            realized_oos_basket_pct=+261.88,
            substrate_dataset_checksum="317429e4" + "9" * 56,
            rng_seed=20260514,
        )
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-conservative-prior",
            realized_oos_basket_pct=-99.9995,
            zero_cost_reference_cell=a0_ref,
        )
        assert result.annotation == "cost-friction-dominated-edge-present"
        assert "flips the cell from positive to negative" in result.rationale.lower()
        assert result.zero_cost_reference_run_id == "5e52f0b7ddd94ecea3187566c0e255d0"
        assert result.zero_cost_reference_basket_pct == 261.88

    def test_present_under_empirical_cost_calibration(self):
        """`cost-empirical-calibrated` is also condition-(i)-satisfying."""
        ref = ZeroCostReferenceCell(
            run_id="ref_zero_cost",
            sidecar_sha_prefix16="c" * 16,
            realized_oos_basket_pct=+5.0,
        )
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-empirical-calibrated",
            realized_oos_basket_pct=-3.0,
            zero_cost_reference_cell=ref,
        )
        assert result.annotation == "cost-friction-dominated-edge-present"


class TestSidecarBlockBuilder:
    """`build_cost_friction_edge_block` renders the result for sidecar embedding."""

    def test_block_contains_all_required_fields(self):
        ref = ZeroCostReferenceCell(
            run_id="ref_run",
            sidecar_sha_prefix16="d" * 16,
            realized_oos_basket_pct=+200.0,
        )
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-conservative-prior",
            realized_oos_basket_pct=-50.0,
            zero_cost_reference_cell=ref,
        )
        block = build_cost_friction_edge_block(result)
        assert block["annotation"] == "cost-friction-dominated-edge-present"
        assert block["cost_model_annotation"] == "cost-conservative-prior"
        assert block["realized_oos_basket_pct"] == -50.0
        assert block["zero_cost_reference_provided"] is True
        assert block["zero_cost_reference_run_id"] == "ref_run"
        assert block["zero_cost_reference_sidecar_sha_prefix16"] == "d" * 16
        assert block["zero_cost_reference_basket_pct"] == +200.0
        assert "rationale" in block
        assert block["spec_reference"] == "ADR-0028 §D-2"

    def test_block_n_a_serializable(self):
        """n/a case → block emittable with None reference fields."""
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-zero",
            realized_oos_basket_pct=+10.0,
            zero_cost_reference_cell=None,
        )
        block = build_cost_friction_edge_block(result)
        assert block["annotation"] == "cost-friction-dominated-edge-n/a"
        assert block["zero_cost_reference_provided"] is False
        assert block["zero_cost_reference_run_id"] is None


class TestDataclassImmutability:
    """ADR-0013 §4.1 non-loss + dataclass(frozen=True) discipline."""

    def test_zero_cost_reference_cell_frozen(self):
        ref = ZeroCostReferenceCell(
            run_id="abc",
            sidecar_sha_prefix16="e" * 16,
            realized_oos_basket_pct=+1.0,
        )
        with pytest.raises((AttributeError, Exception)):
            ref.run_id = "xyz"

    def test_cost_friction_edge_result_frozen(self):
        result = cost_friction_dominated_edge_annotation(
            cost_model_annotation="cost-zero",
            realized_oos_basket_pct=0.0,
            zero_cost_reference_cell=None,
        )
        with pytest.raises((AttributeError, Exception)):
            result.annotation = "cost-friction-dominated-edge-present"
