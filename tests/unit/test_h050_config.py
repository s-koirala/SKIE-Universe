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
    """random_seed must be pinned for reproducibility."""
    cfg = _load_h050()
    assert isinstance(cfg["random_seed"], int)
    assert cfg["random_seed"] == 2026
