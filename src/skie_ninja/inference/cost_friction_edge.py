"""Cost-friction-dominated-edge KPI annotation per ADR-0028 §D-2.

The annotation distinguishes three cases at KPI emission time:

- `cost-friction-dominated-edge-present`: cost-applied cell is net-negative
  AND a zero-cost reference cell is net-positive at the same fixture
  (same substrate vintage + inner-CV grid + rng_seed). Cost is the dominant
  catastrophe driver.
- `cost-friction-dominated-edge-absent`: cost-applied cell is net-positive
  OR cost is applied but no positive zero-cost reference exists. Cost is a
  drag but not the dominant driver.
- `cost-friction-dominated-edge-n/a`: no cost model applied (PRE-cost
  research-only emission per operator 2026-05-08 standing directive). The
  annotation cannot be evaluated absent a cost-applied cell.

Per ADR-0028 §D-2 trigger semantics:

  Condition (i): `cost_model_annotation in {"cost-conservative-prior",
    "cost-empirical-calibrated"}` — the KPI emission applied per-trade cost
    realism (NOT `cost-zero`).
  Condition (ii): `realized_oos_basket_pct < 0.0` — the cost-applied cell
    shows a net loss.
  Condition (iii): A zero-cost reference cell exists with realized OOS basket
    %% strictly > 0 on the same fixture. The reference's `run_id` + sidecar
    SHA prefix-16 must be persisted in the sidecar's `methodological_
    annotations.cost_friction_edge_reference` block for auditability.

The empirical anchor is the H062 v3 ablation per ADR-0028 §Context:
A0 baseline (cost-OFF) basket = +261.88%; v3 all-ON basket = −99.9995%.
→ `cost-friction-dominated-edge-present`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


__all__ = [
    "ZeroCostReferenceCell",
    "CostFrictionEdgeResult",
    "cost_friction_dominated_edge_annotation",
    "build_cost_friction_edge_block",
]


CostModelAnnotation = Literal[
    "cost-zero",
    "cost-conservative-prior",
    "cost-empirical-calibrated",
]

EdgeAnnotation = Literal[
    "cost-friction-dominated-edge-present",
    "cost-friction-dominated-edge-absent",
    "cost-friction-dominated-edge-n/a",
]


@dataclass(frozen=True)
class ZeroCostReferenceCell:
    """Cross-reference metadata for a sibling zero-cost ablation cell.

    Per ADR-0028 §D-2 condition (iii), the cost-friction-dominated-edge-
    present annotation requires a zero-cost reference cell at the same
    fixture (substrate vintage + inner-CV grid + rng_seed). This dataclass
    carries the load-bearing fields cross-cited in the sidecar.
    """

    run_id: str
    sidecar_sha_prefix16: str
    realized_oos_basket_pct: float
    substrate_dataset_checksum: str | None = None
    rng_seed: int | None = None


@dataclass(frozen=True)
class CostFrictionEdgeResult:
    """Return type for the annotation primitive."""

    annotation: EdgeAnnotation
    cost_model_annotation: str
    realized_oos_basket_pct: float
    zero_cost_reference_provided: bool
    zero_cost_reference_run_id: str | None
    zero_cost_reference_sidecar_sha_prefix16: str | None
    zero_cost_reference_basket_pct: float | None
    rationale: str


def cost_friction_dominated_edge_annotation(
    *,
    cost_model_annotation: str,
    realized_oos_basket_pct: float,
    zero_cost_reference_cell: ZeroCostReferenceCell | None,
) -> CostFrictionEdgeResult:
    """Compute the ADR-0028 §D-2 cost-friction-dominated-edge annotation.

    Args:
        cost_model_annotation: One of `"cost-zero"`,
            `"cost-conservative-prior"`, `"cost-empirical-calibrated"` —
            the existing cost-model annotation per ADR-0025 §D-5.
        realized_oos_basket_pct: Signed % change of the realized OOS basket
            terminal equity vs $10K starting (e.g., -99.9995 for H062 v3).
        zero_cost_reference_cell: Optional cross-reference to a sibling
            zero-cost ablation cell at the same fixture. None if no such
            cell has been run; in that case the annotation falls back to
            `cost-friction-dominated-edge-absent` per ADR-0028 §D-2
            condition (iii) failure.

    Returns:
        CostFrictionEdgeResult carrying the annotation + provenance fields
        suitable for direct embedding in sidecar JSON.
    """
    # Condition (i): cost model applied?
    if cost_model_annotation == "cost-zero":
        # ADR-0028 §D-2 condition (i) fails → annotation is n/a.
        return CostFrictionEdgeResult(
            annotation="cost-friction-dominated-edge-n/a",
            cost_model_annotation=cost_model_annotation,
            realized_oos_basket_pct=float(realized_oos_basket_pct),
            zero_cost_reference_provided=False,
            zero_cost_reference_run_id=None,
            zero_cost_reference_sidecar_sha_prefix16=None,
            zero_cost_reference_basket_pct=None,
            rationale=(
                "Cost-model is `cost-zero` (no per-trade cost subtraction "
                "applied; PRE-cost research-only emission per operator "
                "2026-05-08 standing directive). The cost-friction-vs-"
                "edge interaction cannot be evaluated absent a cost-applied "
                "cell. Annotation = `cost-friction-dominated-edge-n/a` per "
                "ADR-0028 §D-2 condition (i) fallback."
            ),
        )

    if cost_model_annotation not in {
        "cost-conservative-prior",
        "cost-empirical-calibrated",
    }:
        # Defensive — unrecognized annotation value falls to n/a so we
        # never emit a load-bearing claim under uncertain provenance.
        return CostFrictionEdgeResult(
            annotation="cost-friction-dominated-edge-n/a",
            cost_model_annotation=cost_model_annotation,
            realized_oos_basket_pct=float(realized_oos_basket_pct),
            zero_cost_reference_provided=False,
            zero_cost_reference_run_id=None,
            zero_cost_reference_sidecar_sha_prefix16=None,
            zero_cost_reference_basket_pct=None,
            rationale=(
                f"Unrecognized `cost_model_annotation` value "
                f"{cost_model_annotation!r}; falling back to "
                f"`cost-friction-dominated-edge-n/a`. Expected one of "
                f"`cost-zero` / `cost-conservative-prior` / "
                f"`cost-empirical-calibrated` per ADR-0025 §D-5."
            ),
        )

    # Condition (ii): cost-applied cell is net-loss?
    cost_applied_loss = float(realized_oos_basket_pct) < 0.0
    if not cost_applied_loss:
        return CostFrictionEdgeResult(
            annotation="cost-friction-dominated-edge-absent",
            cost_model_annotation=cost_model_annotation,
            realized_oos_basket_pct=float(realized_oos_basket_pct),
            zero_cost_reference_provided=zero_cost_reference_cell is not None,
            zero_cost_reference_run_id=(
                zero_cost_reference_cell.run_id
                if zero_cost_reference_cell is not None else None
            ),
            zero_cost_reference_sidecar_sha_prefix16=(
                zero_cost_reference_cell.sidecar_sha_prefix16
                if zero_cost_reference_cell is not None else None
            ),
            zero_cost_reference_basket_pct=(
                zero_cost_reference_cell.realized_oos_basket_pct
                if zero_cost_reference_cell is not None else None
            ),
            rationale=(
                "Cost-applied basket is net-positive "
                f"({realized_oos_basket_pct:+.4f}%). Cost is a per-trade "
                "drag but does NOT flip the cell from positive to negative. "
                "Annotation = `cost-friction-dominated-edge-absent` per "
                "ADR-0028 §D-2 condition (ii) failure (gross-edge survives "
                "cost realism)."
            ),
        )

    # Condition (iii): zero-cost reference exists AND is net-positive?
    if zero_cost_reference_cell is None:
        return CostFrictionEdgeResult(
            annotation="cost-friction-dominated-edge-absent",
            cost_model_annotation=cost_model_annotation,
            realized_oos_basket_pct=float(realized_oos_basket_pct),
            zero_cost_reference_provided=False,
            zero_cost_reference_run_id=None,
            zero_cost_reference_sidecar_sha_prefix16=None,
            zero_cost_reference_basket_pct=None,
            rationale=(
                "Cost-applied basket is net-negative "
                f"({realized_oos_basket_pct:+.4f}%) but NO zero-cost "
                "reference cell was provided at the same fixture. "
                "Cannot conclude cost-dominance vs gross-edge absence. "
                "Annotation = `cost-friction-dominated-edge-absent` per "
                "ADR-0028 §D-2 condition (iii) failure. Operator: pass "
                "`--zero-cost-reference-run-id <run_id>` to enable the "
                "`-present` evaluation; tracked under "
                "P1-ADR-0028-ZERO-COST-REFERENCE-CELL-CONVENTION."
            ),
        )

    ref_pct = float(zero_cost_reference_cell.realized_oos_basket_pct)
    if ref_pct <= 0.0:
        return CostFrictionEdgeResult(
            annotation="cost-friction-dominated-edge-absent",
            cost_model_annotation=cost_model_annotation,
            realized_oos_basket_pct=float(realized_oos_basket_pct),
            zero_cost_reference_provided=True,
            zero_cost_reference_run_id=zero_cost_reference_cell.run_id,
            zero_cost_reference_sidecar_sha_prefix16=(
                zero_cost_reference_cell.sidecar_sha_prefix16
            ),
            zero_cost_reference_basket_pct=ref_pct,
            rationale=(
                "Cost-applied basket is net-negative "
                f"({realized_oos_basket_pct:+.4f}%) BUT zero-cost "
                f"reference (run_id {zero_cost_reference_cell.run_id}) is "
                f"also non-positive ({ref_pct:+.4f}%). Gross edge is null/"
                "negative even without cost; cost realism is not the "
                "dominant driver. Annotation = `cost-friction-dominated-"
                "edge-absent` per ADR-0028 §D-2 condition (iii) failure."
            ),
        )

    # All three conditions hold → present.
    return CostFrictionEdgeResult(
        annotation="cost-friction-dominated-edge-present",
        cost_model_annotation=cost_model_annotation,
        realized_oos_basket_pct=float(realized_oos_basket_pct),
        zero_cost_reference_provided=True,
        zero_cost_reference_run_id=zero_cost_reference_cell.run_id,
        zero_cost_reference_sidecar_sha_prefix16=(
            zero_cost_reference_cell.sidecar_sha_prefix16
        ),
        zero_cost_reference_basket_pct=ref_pct,
        rationale=(
            "Cost-applied basket is net-negative "
            f"({realized_oos_basket_pct:+.4f}%); zero-cost reference (run_id "
            f"{zero_cost_reference_cell.run_id}) is net-positive ({ref_pct:+.4f}%). "
            "Cost realism flips the cell from positive to negative — cost is "
            "the dominant driver. Annotation = "
            "`cost-friction-dominated-edge-present` per ADR-0028 §D-2 "
            "(empirical anchor: H062 v3 vs A0 baseline ablation)."
        ),
    )


def build_cost_friction_edge_block(
    result: CostFrictionEdgeResult,
) -> dict[str, object]:
    """Render the result as a sidecar-embeddable dict block.

    The block populates the §"Methodological annotations" cost-friction-edge
    sub-section per ADR-0028 §D-2 / §D-4. Operator-readable.
    """
    return {
        "annotation": result.annotation,
        "cost_model_annotation": result.cost_model_annotation,
        "realized_oos_basket_pct": result.realized_oos_basket_pct,
        "zero_cost_reference_provided": result.zero_cost_reference_provided,
        "zero_cost_reference_run_id": result.zero_cost_reference_run_id,
        "zero_cost_reference_sidecar_sha_prefix16": (
            result.zero_cost_reference_sidecar_sha_prefix16
        ),
        "zero_cost_reference_basket_pct": result.zero_cost_reference_basket_pct,
        "rationale": result.rationale,
        "spec_reference": "ADR-0028 §D-2",
    }
