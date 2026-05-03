"""End-to-end smoke test for the walk-forward orchestrator (dry-run)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Make `scripts/` importable so we can call run(...) directly without
# shelling out (faster, and captures coverage).
_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def test_orchestrator_dry_run_produces_artifacts(tmp_path: Path) -> None:
    """``--dry-run --smoke-n 2000 --smoke`` composes the full pipeline
    end-to-end and lands the expected per-symbol artifact tree. The
    ``--smoke`` flag reduces ``lgb_n_draws`` to a CI-friendly value
    (production runs use the H050.yaml-bound 200 per Bergstra & Bengio
    2012, JMLR 13:281-305). We do not assert on specific Sharpe values
    (stochastic), only on artifact existence + finite numeric summary.
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
    # fold with the default sizing. --smoke caps inner-CV cost.
    out = run_walk_forward.run(
        [
            "--hypothesis",
            "H050",
            "--config",
            str(config),
            "--dry-run",
            "--smoke-n",
            "2000",
            "--smoke",
        ]
    )
    try:
        assert out.is_dir(), f"run directory not created: {out}"
        assert (out / "reprolog.json").is_file()
        # ReproLog has valid JSON with the expected fields.
        repro = json.loads((out / "reprolog.json").read_text(encoding="utf-8"))
        assert repro["hypothesis_id"] == "H050"
        # F-R-2 fix Round-2 audit-remediate-loop 2026-05-03: was 2026,
        # corrected to design.md §11 line 137 binding 20260420.
        assert repro["rng_seed"] == 20260420
        # Universe is iterated per H050.yaml line 3 = [ES, NQ].
        # P1-H050-UNIVERSE-ES-ONLY closure: NQ MUST be present.
        run_summary = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
        assert run_summary["universe"] == ["ES", "NQ"], (
            f"Universe iteration failed: {run_summary['universe']!r}"
        )
        assert run_summary["smoke"] is True
        for sym in ("ES", "NQ"):
            sym_dir = out / sym
            assert sym_dir.is_dir(), f"{sym}/ not created"
            assert (sym_dir / "aggregate" / "metrics_summary.json").is_file()
            assert (sym_dir / "oos_returns.parquet").is_file()
            metrics = json.loads(
                (sym_dir / "aggregate" / "metrics_summary.json").read_text(encoding="utf-8")
            )
            assert "n_folds" in metrics
            assert metrics["symbol"] == sym
            # P1-H050-INNER-CV closure: per-fold HP is selected by inner CV.
            assert "selected_hp_per_fold" in metrics
            assert "lgb_n_draws_effective" in metrics
            assert "inner_n_folds" in metrics
            # P1-H050-LABEL-CV closure: label_cv_inner_sharpes records the
            # joint-CV trace (one entry per evaluated grid cell).
            assert "label_cv_inner_sharpes" in metrics
            assert "selected_label_cfg" in metrics
            # If gates ran, check Sharpe values are finite.
            if "sharpe_gated" in metrics:
                import math

                assert math.isfinite(metrics["sharpe_gated"])
                assert math.isfinite(metrics["sharpe_unconditional"])
        # Per-feature provenance written (one set of files per run_id).
        prov_dir = paths.logs_reproducibility_features
        run_id = out.name
        n_prov = sum(
            1
            for p in prov_dir.glob(f"*_{run_id}.json")
            if p.is_file()
        )
        assert n_prov >= 4
    finally:
        # Clean up artifacts produced by the smoke run so the test is
        # idempotent. ReproLog and ledger land under logs/ — leave
        # them to be garbage-collected by the repo's normal flow.
        if out.exists():
            shutil.rmtree(out, ignore_errors=True)
