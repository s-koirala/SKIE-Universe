"""Microbench — log_emission_matrix(diag) vs log_emission_matrix(full) at d=1.

Anchors the constant-factor claim in
docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md
(replaces the unattributed "~10x" estimate with a measured ratio on this
hardware + BLAS stack).

Tier: 5 (single-host empirical hand measurement) per the user-global
evidence hierarchy in ~/.claude/CLAUDE.md.  Runs are pinned to a single
BLAS thread per ADR-0009 to match the production walk-forward
configuration.

Invocation (canonical, also documented in scripts/bench/README.md):

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \\
        uv run python -u scripts/bench/bench_hmm_cov_d1.py \\
        --out logs/bench_hmm_cov_d1_<DATE>.json

The JSON is written incrementally (atomic-replace after the per-E-step
block) so a partial run still persists provenance even if the
end-to-end loop is killed.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# Pin BLAS to 1 thread BEFORE importing numpy (ADR-0009).
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # paths-guard: allow (sys.path bootstrap before pip install -e .; bench is invoked directly via `uv run python`, not as a tested module, so it cannot rely on the project being on sys.path already)
from skie_ninja.models.regime._core import log_emission_matrix  # noqa: E402
from skie_ninja.models.regime.selection import select_gaussian_hmm  # noqa: E402


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()[:12]
    except Exception:
        return "unknown"


def _uv_pip_freeze() -> str:
    try:
        return subprocess.check_output(
            ["uv", "pip", "freeze"], text=True, timeout=30
        ).strip()
    except Exception as exc:
        return f"unknown ({exc!r})"


def _numpy_show_config() -> str:
    """Capture BLAS vendor / build info for cross-host reproducibility."""
    try:
        buf = io.StringIO()
        sys.stdout, _orig = buf, sys.stdout
        try:
            np.show_config()
        finally:
            sys.stdout = _orig
        return buf.getvalue().strip()
    except Exception:
        try:
            return repr(np.__config__.blas_info)  # type: ignore[attr-defined]
        except Exception as exc:
            return f"unknown ({exc!r})"


def _bootstrap_ratio_ci(
    diag_times: list[float], full_times: list[float], n_boot: int = 2000, seed: int = 0
) -> tuple[float, float]:
    """95% percentile-bootstrap CI on the median(full)/median(diag) ratio.

    Resamples each arm independently (the two timing series are not paired
    across iterations); allows unequal arm sizes. Percentile method per
    Efron & Tibshirani 1993 §13; for the small-skew per-E-step ratios
    here the percentile method is acceptable (BCa would be the future-work
    upgrade if bench distributions become heavily skewed).
    """
    rng = np.random.default_rng(seed)
    diag_arr = np.asarray(diag_times)
    full_arr = np.asarray(full_times)
    n_d = len(diag_arr)
    n_f = len(full_arr)
    ratios = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        idx_d = rng.integers(0, n_d, size=n_d)
        idx_f = rng.integers(0, n_f, size=n_f)
        ratios[b] = float(np.median(full_arr[idx_f])) / float(np.median(diag_arr[idx_d]))
    lo, hi = np.percentile(ratios, [2.5, 97.5])
    return float(lo), float(hi)


def _run_log_emission(
    t_len: int, n_states: int, n_iter: int, sigma2: float, seed: int
) -> dict:
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((t_len, 1)).astype(np.float64) * np.sqrt(sigma2)
    means = rng.standard_normal((n_states, 1)).astype(np.float64) * 0.1 * np.sqrt(sigma2)
    var = np.full((n_states, 1), sigma2, dtype=np.float64)
    cov_full = var.reshape(n_states, 1, 1).copy()

    # warm-up
    log_emission_matrix(x, means, var, "diag")
    log_emission_matrix(x, means, cov_full, "full")

    t_diag = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        log_emission_matrix(x, means, var, "diag")
        t_diag.append(time.perf_counter() - t0)

    t_full = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        log_emission_matrix(x, means, cov_full, "full")
        t_full.append(time.perf_counter() - t0)

    log_b_diag = log_emission_matrix(x, means, var, "diag")
    log_b_full = log_emission_matrix(x, means, cov_full, "full")
    max_abs_diff = float(np.max(np.abs(log_b_diag - log_b_full)))
    bit_exact = bool(np.array_equal(log_b_diag, log_b_full))

    ci_lo, ci_hi = _bootstrap_ratio_ci(t_diag, t_full, n_boot=2000, seed=seed + 1)

    return {
        "t_len": t_len,
        "n_states": n_states,
        "n_iter": n_iter,
        "sigma2": sigma2,
        "diag_median_s": float(np.median(t_diag)),
        "diag_min_s": float(np.min(t_diag)),
        "diag_std_s": float(np.std(t_diag, ddof=1)) if len(t_diag) > 1 else 0.0,
        "full_median_s": float(np.median(t_full)),
        "full_min_s": float(np.min(t_full)),
        "full_std_s": float(np.std(t_full, ddof=1)) if len(t_full) > 1 else 0.0,
        "ratio_median": float(np.median(t_full)) / float(np.median(t_diag)),
        "ratio_ci_95_lo": ci_lo,
        "ratio_ci_95_hi": ci_hi,
        "max_abs_diff_log_density": max_abs_diff,
        "bit_exact": bit_exact,
    }


def _run_endtoend_select(t_len: int, seed: int) -> dict:
    """End-to-end select_gaussian_hmm timing, mirrors the H050
    orchestrator call site (scripts/run_walk_forward.py:788-795):
    n_states_grid=(2,), min_restarts=5, max_restarts=10. With
    P1-HMM-FULL-COV-1DIM-REDUNDANT model-class deduplication landed,
    the diag+full grid should be ~no slower than diag-only at d=1."""
    rng = np.random.default_rng(seed)
    half = t_len // 2
    r1 = rng.normal(loc=0.0, scale=1e-4, size=half)
    r2 = rng.normal(loc=0.0, scale=5e-4, size=t_len - half)
    x = np.concatenate([r1, r2]).reshape(-1, 1).astype(np.float64)

    t0 = time.perf_counter()
    sel_diag = select_gaussian_hmm(
        x,
        n_states_grid=(2,),
        covariance_types=("diag",),
        seed=seed,
        min_restarts=5,
        max_restarts=10,
    )
    t_diag = time.perf_counter() - t0

    t0 = time.perf_counter()
    sel_both = select_gaussian_hmm(
        x,
        n_states_grid=(2,),
        covariance_types=("diag", "full"),
        seed=seed,
        min_restarts=5,
        max_restarts=10,
    )
    t_both = time.perf_counter() - t0

    n_aliased = sum(1 for c in sel_both.candidates if c.n_restarts_used == 0)

    return {
        "t_len": t_len,
        "diag_only_s": float(t_diag),
        "diag_plus_full_with_dedup_s": float(t_both),
        "ratio_both_over_diag": float(t_both / t_diag),
        "n_aliased_candidates": int(n_aliased),
        "best_bic_diag_only": float(sel_diag.candidates[0].bic),
        "best_bic_diag_plus_full": float(min(c.bic for c in sel_both.candidates)),
        "bic_match": bool(
            abs(
                sel_diag.candidates[0].bic
                - min(c.bic for c in sel_both.candidates)
            )
            < 1e-9
        ),
    }


def _atomic_write_json(out_path: Path, payload: dict) -> None:
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="logs/bench_hmm_cov_d1.json",
        help="Output JSON path (atomically written; partial-run safe).",
    )
    parser.add_argument(
        "--skip-endtoend",
        action="store_true",
        help="Skip the end-to-end select_gaussian_hmm bench (fast path).",
    )
    args = parser.parse_args()
    out_path = Path(args.out)

    manifest = {
        "purpose": "Anchor the d=1 full-vs-diag constant-factor claim with measured ratios under ADR-0009 BLAS pinning.",
        "tier": 5,
        "tier_rationale": "single-host empirical hand measurement; not a published benchmark",
        "git_head": _git_head(),
        "platform": platform.platform(),
        "platform_processor": platform.processor(),
        "platform_machine": platform.machine(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "blas_pinned": {
            k: os.environ.get(k)
            for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
        },
        "numpy_show_config": _numpy_show_config(),
        "uv_pip_freeze_first_lines": "\n".join(_uv_pip_freeze().splitlines()[:30]),
        "log_emission_matrix_runs": [],
        "select_gaussian_hmm_endtoend": [],
        "runtime_status": "in_progress",
    }
    _atomic_write_json(out_path, manifest)

    print("# log_emission_matrix per-E-step bench (d=1, sigma^2=1.0)", flush=True)
    cells_unit_var = [
        (10_000, 2, 50, 1.0),
        (100_000, 2, 30, 1.0),
        (1_000_000, 2, 30, 1.0),
        (3_000_000, 2, 30, 1.0),
    ]
    for t_len, n_states, n_iter, sigma2 in cells_unit_var:
        print(f"#   T={t_len:>9} ...", flush=True, end=" ")
        rec = _run_log_emission(t_len, n_states, n_iter, sigma2, seed=2026)
        print(
            f"diag={rec['diag_median_s']*1e3:.3f}ms "
            f"full={rec['full_median_s']*1e3:.3f}ms "
            f"ratio={rec['ratio_median']:.3f}x "
            f"CI95=[{rec['ratio_ci_95_lo']:.3f}, {rec['ratio_ci_95_hi']:.3f}] "
            f"diff={rec['max_abs_diff_log_density']:.0e}",
            flush=True,
        )
        manifest["log_emission_matrix_runs"].append(rec)
        _atomic_write_json(out_path, manifest)

    print("# log_emission_matrix per-E-step bench (d=1, sigma^2=1e-8 — production-realistic)", flush=True)
    for t_len, n_states, n_iter, _ in cells_unit_var[1:]:  # skip T=10k for prod-realistic cell
        print(f"#   T={t_len:>9} ...", flush=True, end=" ")
        rec = _run_log_emission(t_len, n_states, n_iter, sigma2=1e-8, seed=2026)
        print(
            f"diag={rec['diag_median_s']*1e3:.3f}ms "
            f"full={rec['full_median_s']*1e3:.3f}ms "
            f"ratio={rec['ratio_median']:.3f}x "
            f"diff={rec['max_abs_diff_log_density']:.0e}",
            flush=True,
        )
        manifest["log_emission_matrix_runs"].append(rec)
        _atomic_write_json(out_path, manifest)

    if not args.skip_endtoend:
        print("# select_gaussian_hmm end-to-end bench", flush=True)
        for t_len in (20_000, 50_000):
            print(f"#   T={t_len:>9} ...", flush=True, end=" ")
            rec = _run_endtoend_select(t_len, seed=2026)
            print(
                f"diag-only={rec['diag_only_s']:.2f}s "
                f"both-with-dedup={rec['diag_plus_full_with_dedup_s']:.2f}s "
                f"ratio={rec['ratio_both_over_diag']:.3f}x "
                f"aliased={rec['n_aliased_candidates']} "
                f"bic_match={rec['bic_match']}",
                flush=True,
            )
            manifest["select_gaussian_hmm_endtoend"].append(rec)
            _atomic_write_json(out_path, manifest)
    else:
        manifest["select_gaussian_hmm_endtoend"] = "skipped"

    manifest["runtime_status"] = "completed"
    _atomic_write_json(out_path, manifest)
    print(f"# JSON written to {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
