"""Microbench — numba @njit forward/backward kernels vs scipy reference.

Anchors the speedup claim in
docs/audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md
(replaces the docstring's hand-estimate with a measured ratio on this
hardware + BLAS stack).

Tier: 5 (single-host empirical hand measurement) per the user-global
evidence hierarchy in ~/.claude/CLAUDE.md. Runs are pinned to a single
BLAS thread per ADR-0009 to match the production walk-forward
configuration.

Invocation (canonical, also documented in scripts/bench/README.md):

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \\
        uv run python -u scripts/bench/bench_em_kernels.py \\
        --out logs/bench_em_kernels_<DATE>.json
"""
from __future__ import annotations

import argparse
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # paths-guard: allow (sys.path bootstrap; bench is invoked via `uv run python` not as a module)
from skie_ninja.models.regime import _em_kernels  # noqa: E402


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def _pip_freeze() -> list[str]:
    try:
        return subprocess.check_output(
            ["uv", "pip", "freeze"], text=True
        ).strip().splitlines()
    except Exception:
        return []


def bench(t_len: int, n_states: int, n_iter: int = 3) -> dict:
    rng = np.random.default_rng(seed=42)
    log_pi = np.log(rng.dirichlet(np.ones(n_states)))
    log_transmat = np.log(rng.dirichlet(np.ones(n_states), size=n_states))
    log_B = rng.standard_normal((t_len, n_states))

    # Warmup JIT once per (t_len, n_states) shape.
    _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)
    _em_kernels.backward_log_kernel(log_transmat, log_B)

    # Kernel: min-of-N timing.
    times_k: list[float] = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)
        _em_kernels.backward_log_kernel(log_transmat, log_B)
        times_k.append(time.perf_counter() - t0)
    t_kernel = min(times_k)

    # Reference: 1 iter at large T to stay under wall-clock budget.
    n_ref_iter = 1 if t_len > 50_000 else n_iter
    times_r: list[float] = []
    for _ in range(n_ref_iter):
        t0 = time.perf_counter()
        _em_kernels._forward_log_numpy_reference(log_pi, log_transmat, log_B)
        _em_kernels._backward_log_numpy_reference(log_transmat, log_B)
        times_r.append(time.perf_counter() - t0)
    t_ref = min(times_r)

    return {
        "t_len": t_len,
        "n_states": n_states,
        "t_kernel_s": t_kernel,
        "t_ref_s": t_ref,
        "speedup": t_ref / max(t_kernel, 1e-12),
        "n_iter_kernel": n_iter,
        "n_iter_ref": n_ref_iter,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--t-grid", default="10000,50000,200000",
                        help="Comma-separated T values to bench.")
    parser.add_argument("--n-grid", default="2,3,4",
                        help="Comma-separated N (n_states) values to bench.")
    parser.add_argument("--n-iter", type=int, default=3)
    args = parser.parse_args()

    print(f"NUMBA_AVAILABLE: {_em_kernels.NUMBA_AVAILABLE}", flush=True)
    if not _em_kernels.NUMBA_AVAILABLE:
        print("WARN: numba not installed — bench will compare numpy-ref to "
              "itself. Install with `uv pip install -e .[perf]`.", flush=True)

    results: list[dict] = []
    t_grid = [int(x) for x in args.t_grid.split(",")]
    n_grid = [int(x) for x in args.n_grid.split(",")]
    for t_len in t_grid:
        for n_states in n_grid:
            r = bench(t_len, n_states, args.n_iter)
            print(f"T={t_len:>8d} N={n_states} kernel={r['t_kernel_s']:.4f}s "
                  f"ref={r['t_ref_s']:.4f}s speedup={r['speedup']:.1f}x", flush=True)
            results.append(r)

    try:
        import numba
        numba_v = str(numba.__version__)
    except ImportError:
        numba_v = "unavailable"
    try:
        import llvmlite
        llvm_v = str(llvmlite.__version__)
    except ImportError:
        llvm_v = "unavailable"

    payload = {
        "git_head": _git_head(),
        "numpy_version": np.__version__,
        "numba_version": numba_v,
        "llvmlite_version": llvm_v,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "thread_pinning": {
            "OMP_NUM_THREADS": os.environ["OMP_NUM_THREADS"],
            "MKL_NUM_THREADS": os.environ["MKL_NUM_THREADS"],
            "OPENBLAS_NUM_THREADS": os.environ["OPENBLAS_NUM_THREADS"],
        },
        "pip_freeze": _pip_freeze(),
        "note": "min-of-n_iter kernel timing; min-of-1 reference for T>50k. "
                "fastmath=False, cache=True. See P1-HMM-EM-NUMBA-KERNELS audit trail.",
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
