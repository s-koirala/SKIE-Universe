"""H050 config invariants — pre-reg fidelity assertions.

These tests fail-fast if a future edit drifts H050.yaml away from the
pre-registered grid in design.md §5 without going through the proper
addendum + audit-remediate-loop process.
"""

from __future__ import annotations

from pathlib import Path

import yaml


_H050_YAML = Path(__file__).resolve().parents[2] / "config" / "hypotheses" / "H050.yaml"


def _load_h050() -> dict:
    with open(_H050_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_h050_yaml_exists() -> None:
    assert _H050_YAML.exists(), f"H050 config missing: {_H050_YAML}"


def test_hmm_covariance_grid_preserves_pre_reg_diag_full() -> None:
    """design.md §5 binds covariance_type ∈ {diag, full}. The YAML
    grid must include both. Model-class deduplication at d=1 happens
    inside select_gaussian_hmm (P1-HMM-FULL-COV-1DIM-REDUNDANT) and
    must not change the YAML.
    """
    cfg = _load_h050()
    cov_grid = cfg["hmm"]["covariance_type"]
    assert isinstance(cov_grid, list), f"hmm.covariance_type must be a list, got {cov_grid!r}"
    assert "diag" in cov_grid, f"hmm.covariance_type must include 'diag', got {cov_grid!r}"
    assert "full" in cov_grid, (
        "hmm.covariance_type must include 'full' per design.md §5; "
        "the d=1 redundancy is removed inside select_gaussian_hmm via "
        "model-class deduplication, NOT by editing the YAML grid. "
        f"Got {cov_grid!r}."
    )


def test_universe_pre_reg_es_nq() -> None:
    """design.md §2 binds universe = [ES, NQ]."""
    cfg = _load_h050()
    assert cfg["universe"] == ["ES", "NQ"], (
        f"universe must be [ES, NQ] per design.md §2, got {cfg['universe']!r}"
    )


def test_test_statistic_pre_reg() -> None:
    """design.md §1 binds T_H050 = SR_filtered_gated - SR_filtered_unconditional."""
    cfg = _load_h050()
    assert cfg["test_statistic"] == "SR_filtered_gated - SR_filtered_unconditional"


def test_random_seed_pinned() -> None:
    """random_seed must be pinned for reproducibility AND match the
    design.md §11 line 137 binding "RNG seed: 20260420".

    F-R-2 fix (Round-2 audit-remediate-loop 2026-05-03): prior YAML
    value 2026 was a 6-orders-of-magnitude drift from the pre-reg
    binding 20260420. Pre-reg fidelity invariant; do not edit without
    successor-hypothesis-ID per ADR-0013 §"Frozen pre-registration
    amendment".
    """
    cfg = _load_h050()
    assert isinstance(cfg["random_seed"], int)
    assert cfg["random_seed"] == 20260420, (
        f"random_seed must be 20260420 per design.md §11 line 137 "
        f"frozen pre-reg binding; got {cfg['random_seed']!r}. "
        "ADR-0013 §'Frozen pre-registration amendment' forbids editing "
        "§11 reproducibility commitments without a successor hypothesis "
        "ID. If a re-pin is operationally needed, open a successor "
        "hypothesis ID; do not edit this test in isolation."
    )


def test_lgb_seed_matches_design_md_binding() -> None:
    """classifier.search.seed must match the design.md §11 binding
    (20260420). F-R-2 fix consistency: both random_seed and lgb_seed
    are seed values; pre-reg binds the master to 20260420; both YAML
    seeds inherit the same value to maintain consistent stochastic
    streams across the pipeline.
    """
    cfg = _load_h050()
    lgb_seed = cfg["classifier"]["search"]["seed"]
    assert isinstance(lgb_seed, int)
    assert lgb_seed == 20260420, (
        f"classifier.search.seed must be 20260420 per F-R-2 fix; "
        f"got {lgb_seed!r}."
    )


def test_design_md_rng_seed_binding_unedited() -> None:
    """design.md §11 line 137 binds 'RNG seed: 20260420'; this test
    pins that the binding text is preserved verbatim. Any future
    successor-hypothesis-ID amendment must update both the design.md
    binding AND this test in the same commit.
    """
    design_md = (
        Path(__file__).resolve().parents[2]
        / "research"
        / "01_hypothesis_register"
        / "H050"
        / "design.md"
    )
    text = design_md.read_text(encoding="utf-8")
    assert "RNG seed: 20260420" in text, (
        "design.md §11 line 137 'RNG seed: 20260420' binding has been "
        "edited or removed. Per ADR-0013 §'Frozen pre-registration "
        "amendment' §1-§7 immutability discipline, §11 reproducibility "
        "commitments cannot be edited. If a re-pin is operationally "
        "needed, open a successor hypothesis ID."
    )
