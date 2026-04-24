"""End-to-end smoke test for the walk-forward orchestrator (dry-run)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest


# Make `scripts/` importable so we can call run(...) directly without
# shelling out (faster, and captures coverage).
_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def test_orchestrator_dry_run_produces_artifacts(tmp_path: Path) -> None:
    """--dry-run --smoke-n 2000 composes the full pipeline end-to-end
    and lands the expected artifact tree. We do not assert on specific
    Sharpe values (stochastic), only on artifact existence + finite
    numeric summary.
    """
    # Import lazily so baseline test collection is not affected by
    # lightgbm import cost.
    import run_walk_forward  # type: ignore[import-not-found]

    from skie_ninja.utils.paths import ProjectPaths

    paths = ProjectPaths.discover()
    config = paths.root / "config" / "hypotheses" / "H050.yaml"
    assert config.is_file()

    # Deliberately tiny smoke-n so the test runs fast. 2000 bars per
    # symbol is enough for the walk-forward engine to produce >= 1
    # fold with the default sizing.
    out = run_walk_forward.run(
        [
            "--hypothesis",
            "H050",
            "--config",
            str(config),
            "--dry-run",
            "--smoke-n",
            "2000",
        ]
    )
    try:
        assert out.is_dir(), f"run directory not created: {out}"
        assert (out / "reprolog.json").is_file()
        # ReproLog has valid JSON with the expected fields.
        repro = json.loads((out / "reprolog.json").read_text(encoding="utf-8"))
        assert repro["hypothesis_id"] == "H050"
        assert repro["rng_seed"] == 2026
        assert (out / "aggregate" / "metrics_summary.json").is_file()
        metrics = json.loads(
            (out / "aggregate" / "metrics_summary.json").read_text(encoding="utf-8")
        )
        # n_folds is always present regardless of which branch the
        # aggregate took.
        assert "n_folds" in metrics
        # OOS returns parquet lands regardless of whether gates ran.
        assert (out / "oos_returns.parquet").is_file()
        # Per-feature provenance written.
        prov_dir = paths.logs_reproducibility_features
        # At least four provenance files for this run_id.
        run_id = out.name
        n_prov = sum(
            1
            for p in prov_dir.glob(f"*_{run_id}.json")
            if p.is_file()
        )
        assert n_prov >= 4
        # If gates ran, check Sharpe values are finite.
        if "sharpe_gated" in metrics:
            import math

            assert math.isfinite(metrics["sharpe_gated"])
            assert math.isfinite(metrics["sharpe_unconditional"])
    finally:
        # Clean up artifacts produced by the smoke run so the test is
        # idempotent. ReproLog and ledger land under logs/ — leave
        # them to be garbage-collected by the repo's normal flow.
        if out.exists():
            shutil.rmtree(out, ignore_errors=True)
