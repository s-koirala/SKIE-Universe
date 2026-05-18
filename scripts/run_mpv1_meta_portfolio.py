"""MPV1 meta-portfolio v1 — D-UCB switching-bandit across 5 marginal arms.

Per [research/01_meta_portfolio/MPV1/design.md](../research/01_meta_portfolio/MPV1/design.md)
+ [ADR-0020](../docs/decisions/ADR-0020-meta-portfolio-orchestrator.md)
+ [ADR-0018 D-4](../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md):
runs the D-UCB / SW-UCB / GLR-klUCB / EXP3.S bandit allocators across
5 single-strategy arms whose underlying KPI report cards are
non-significant nulls on basket-level Sharpe; tests whether the
[Grinold 1989 *JPM* 15(3):30-37 DOI 10.3905/jpm.1989.409211](https://doi.org/10.3905/jpm.1989.409211)
√breadth multiplier extracts incremental cross-arm-correlation value.

Arms:
  - H060: cross-futures TSMOM monthly daily-cadence basket
  - H062-ES: intraday Donchian ES leg
  - H062-NQ: intraday Donchian NQ leg
  - H062-MGC: intraday Donchian MGC leg
  - H062-SIL: intraday Donchian SIL leg

Per-arm reward = per-fold MPPM(ρ=1) OOS from the underlying sidecar
(consistent with ADR-0018 D-1 canonical fitness).

Output: sidecar at ``artifacts/runs/MPV1/v1_<ts>/sidecar.json`` +
KPI report card v1 at
``research/01_meta_portfolio/MPV1/MPV1_kpi_report_v1.md`` (deferred to
main session post-run).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

from skie_ninja.inference.mppm import mppm_rho_1, mppm_with_ci
from skie_ninja.meta.switching_bandit import (
    DUCBBandit,
    EXP3SBandit,
    GLRKLUCBBandit,
    SWUCBBandit,
    cumulative_regret,
    select_bandit_by_regret,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("mpv1")


# Default arm-sidecar paths (overridable via --arm).
DEFAULT_ARMS: list[dict[str, str]] = [
    {
        "arm_id": "H060",
        "source_sidecar": "artifacts/runs/H060/cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9/sidecar.json",
        "filter_symbol": None,  # basket-level
        "description": "H060 cross-futures TSMOM daily-cadence basket",
    },
    {
        "arm_id": "H062-ES",
        "source_sidecar": "artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json",
        "filter_symbol": "ES",
        "description": "H062 intraday Donchian ES leg",
    },
    {
        "arm_id": "H062-NQ",
        "source_sidecar": "artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json",
        "filter_symbol": "NQ",
        "description": "H062 intraday Donchian NQ leg",
    },
    {
        "arm_id": "H062-MGC",
        "source_sidecar": "artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json",
        "filter_symbol": "MGC",
        "description": "H062 intraday Donchian MGC leg",
    },
    {
        "arm_id": "H062-SIL",
        "source_sidecar": "artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json",
        "filter_symbol": "SIL",
        "description": "H062 intraday Donchian SIL leg",
    },
]


def _load_arm_rewards(arm: dict[str, str], repo_root: Path) -> dict[str, Any]:
    """Load per-fold MPPM(ρ=1) sequence for one arm from its sidecar."""
    p = repo_root / arm["source_sidecar"]
    with open(p, encoding="utf-8") as f:
        sc = json.load(f)
    filter_sym = arm.get("filter_symbol")
    rewards: list[float] = []
    if filter_sym is None:
        # Basket-level arm: use adr_0018_0019.fold_mppm_oos_path
        path_data = sc.get("adr_0018_0019", {}).get("fold_mppm_oos_path", [])
        rewards = [float(x) for x in path_data if x is not None and np.isfinite(x)]
    else:
        # Per-symbol arm: filter per_fold records by symbol
        per_fold = sc.get("per_fold", [])
        for r in per_fold:
            if r.get("symbol") == filter_sym:
                mppm = r.get("mppm_oos")
                if mppm is not None and np.isfinite(mppm):
                    rewards.append(float(mppm))
    return {
        "arm_id": arm["arm_id"],
        "source_sidecar": arm["source_sidecar"],
        "filter_symbol": filter_sym,
        "description": arm["description"],
        "rewards": rewards,
        "n_rewards": len(rewards),
        "reward_mean": float(np.mean(rewards)) if rewards else float("nan"),
        "reward_std": float(np.std(rewards, ddof=1)) if len(rewards) > 1 else float("nan"),
    }


def _build_reward_matrix(
    arms: list[dict[str, Any]], T: int
) -> np.ndarray:
    """Build (T, K) reward matrix; cycle-resample shorter arms to T rounds."""
    K = len(arms)
    mat = np.zeros((T, K), dtype=float)
    for k, arm in enumerate(arms):
        r = arm["rewards"]
        n = len(r)
        for t in range(T):
            mat[t, k] = r[t % n]
    return mat


def _run_bandit(
    bandit_cls,
    bandit_name: str,
    reward_matrix: np.ndarray,
    *,
    rng_seed: int,
    **kwargs,
) -> dict[str, Any]:
    """Run one bandit algorithm on the reward matrix. Returns sidecar dict.

    Uses the BanditBase.run() canonical entry point per
    [src/skie_ninja/meta/switching_bandit.py](../src/skie_ninja/meta/switching_bandit.py)
    public API.
    """
    _T, K = reward_matrix.shape
    rng = np.random.default_rng(rng_seed)
    bandit = bandit_cls(n_arms=K, rng=rng, **kwargs)
    result = bandit.run(reward_matrix)
    arm_choices_arr = np.asarray(result.arm_choices)
    rewards_arr = np.asarray(result.rewards_received)
    cum_reg = np.asarray(result.cumulative_regret)
    counts = np.bincount(arm_choices_arr, minlength=K)
    shares = counts / counts.sum() if counts.sum() > 0 else np.zeros(K)
    return {
        "bandit": bandit_name,
        "arm_choices": arm_choices_arr.tolist(),
        "realized_rewards": rewards_arr.tolist(),
        "cumulative_reward": float(rewards_arr.sum()),
        "mean_reward_per_round": float(rewards_arr.mean()) if rewards_arr.size else 0.0,
        "final_cumulative_regret": float(cum_reg[-1]) if cum_reg.size else 0.0,
        "allocation_share": shares.tolist(),
        "kwargs": kwargs,
    }


def _equal_weight_baseline(reward_matrix: np.ndarray) -> dict[str, Any]:
    """1/N equal-weight baseline per DeMiguel-Garlappi-Uppal 2009."""
    T, K = reward_matrix.shape
    # Each round: reward = mean across K arms
    eq_rewards = reward_matrix.mean(axis=1)
    return {
        "name": "1_over_N_equal_weight",
        "realized_rewards": eq_rewards.tolist(),
        "cumulative_reward": float(eq_rewards.sum()),
        "mean_reward_per_round": float(eq_rewards.mean()),
    }


def _oracle_baseline(reward_matrix: np.ndarray) -> dict[str, Any]:
    """Ex-post best-arm-by-mean (NOT tradeable; informational only)."""
    T, K = reward_matrix.shape
    arm_means = reward_matrix.mean(axis=0)
    best_arm = int(np.argmax(arm_means))
    return {
        "name": "oracle_best_arm",
        "best_arm_idx": best_arm,
        "best_arm_mean": float(arm_means[best_arm]),
        "cumulative_reward": float(reward_matrix[:, best_arm].sum()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MPV1 meta-portfolio v1")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--rng-seed", type=int, default=20260515)
    parser.add_argument(
        "--T",
        type=int,
        default=None,
        help="Number of bandit rounds (default = min arm reward count after n_min filter).",
    )
    parser.add_argument(
        "--n-min",
        type=int,
        default=10,
        help="Minimum n_rewards per arm; arms with fewer rewards are filtered out (F-1-10 fix).",
    )
    args = parser.parse_args(argv)

    # Load all arms
    arms: list[dict[str, Any]] = []
    for arm_spec in DEFAULT_ARMS:
        try:
            arm_data = _load_arm_rewards(arm_spec, _REPO_ROOT)
            if arm_data["n_rewards"] == 0:
                _log.warning("%s: 0 rewards; skipping", arm_spec["arm_id"])
                continue
            arms.append(arm_data)
            _log.info(
                "%s: %d rewards (mean=%.4f std=%.4f)",
                arm_data["arm_id"], arm_data["n_rewards"],
                arm_data["reward_mean"], arm_data["reward_std"],
            )
        except Exception as e:  # noqa: BLE001
            _log.error("%s: failed to load: %s", arm_spec["arm_id"], e)

    if len(arms) < 2:
        _log.error("Need >= 2 arms to run bandit; got %d", len(arms))
        return 1

    # F-1-1 fix (Round-1 audit-remediate-loop): drop cycle-resampling; use
    # T = min(arm_lengths) per design.md §1 v1-descriptive reframing.
    # Filter arms with n_rewards < n_min to avoid fake-confidence on tiny
    # samples (F-1-10 fix; default n_min=10 = 2 quarters of monthly walk-
    # forward folds at typical project cadence; non-binding per ADR-0013).
    n_min = max(args.n_min, 2)
    pre_filter_n = len(arms)
    arms = [a for a in arms if a["n_rewards"] >= n_min]
    if pre_filter_n != len(arms):
        _log.info(
            "F-1-10 filter: dropped %d arms with n_rewards < n_min=%d; %d arms remain",
            pre_filter_n - len(arms), n_min, len(arms),
        )
    if len(arms) < 2:
        _log.error(
            "After n_min=%d filter, %d arms remain; need >= 2", n_min, len(arms)
        )
        return 1
    if args.T:
        T = args.T
    else:
        T = min(arm["n_rewards"] for arm in arms)  # F-1-1: no cycle-resample
    _log.info("T = %d rounds × K = %d arms (NO cycle-resample; n_min=%d)",
              T, len(arms), n_min)
    reward_matrix = _build_reward_matrix(arms, T)

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else _REPO_ROOT / "artifacts" / "runs" / "MPV1"
            / f"v1_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run all 4 bandits
    bandit_specs = [
        ("DUCBBandit", DUCBBandit, {"discount_factor": 0.99, "exploration_constant": 2.0}),
        ("SWUCBBandit", SWUCBBandit, {"window": 60, "exploration_constant": 2.0}),
        ("GLRKLUCBBandit", GLRKLUCBBandit, {}),
        ("EXP3SBandit", EXP3SBandit, {}),
    ]
    bandit_results: list[dict[str, Any]] = []
    for name, cls, kw in bandit_specs:
        try:
            res = _run_bandit(cls, name, reward_matrix, rng_seed=args.rng_seed, **kw)
            bandit_results.append(res)
            _log.info(
                "%s: cum_reward=%.4f mean_per_round=%.4f cum_regret=%.4f",
                name, res["cumulative_reward"], res["mean_reward_per_round"],
                res["final_cumulative_regret"],
            )
        except Exception as e:  # noqa: BLE001
            _log.error("%s: failed: %s", name, e)

    eq_weight = _equal_weight_baseline(reward_matrix)
    oracle = _oracle_baseline(reward_matrix)
    _log.info("1/N equal-weight: cum_reward=%.4f mean=%.4f",
              eq_weight["cumulative_reward"], eq_weight["mean_reward_per_round"])
    _log.info("oracle best-arm: idx=%d (%s) cum_reward=%.4f mean=%.4f",
              oracle["best_arm_idx"], arms[oracle["best_arm_idx"]]["arm_id"],
              oracle["cumulative_reward"], oracle["best_arm_mean"])

    # F-1-2 + F-1-4 fix: paired stationary-bootstrap CI on (bandit - 1/N)
    # per-round difference. Per design.md §1 reframed (Round-1 remediation),
    # this is reported as DESCRIPTIVE strongest-finding — NOT a Sharpe-
    # promotion gate per ADR-0017 §3. Oracle baseline dropped from primary.
    from skie_ninja.inference.bootstrap import (
        choose_block_length,
        stationary_bootstrap_indices,
    )
    descriptive_diff_by_bandit: dict[str, dict[str, Any]] = {}
    for r in bandit_results:
        try:
            diff = (
                np.array(r["realized_rewards"]) - np.array(eq_weight["realized_rewards"])
            )
            if diff.size < 5:
                continue
            block_sel = choose_block_length(diff)
            block_len = float(block_sel.block_length)
            rng = np.random.default_rng(args.rng_seed + 100)
            n_bootstrap = 1000
            boot_means = np.zeros(n_bootstrap, dtype=float)
            for b in range(n_bootstrap):
                idx = stationary_bootstrap_indices(
                    n=len(diff), block_length=max(block_len, 1.0), rng=rng,
                )
                boot_means[b] = diff[idx].mean()
            ci_low = float(np.percentile(boot_means, 2.5))
            ci_high = float(np.percentile(boot_means, 97.5))
            descriptive_diff_by_bandit[r["bandit"]] = {
                "point_estimate": float(diff.mean()),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "excludes_zero": bool(ci_low > 0 or ci_high < 0),
                "block_length": block_len,
                "n_bootstrap": n_bootstrap,
            }
        except Exception as exc:  # noqa: BLE001
            _log.warning("bootstrap CI failed for %s: %s", r["bandit"], exc)

    # F-1-12 fix: cross-arm correlation matrix on UNIQUE per-fold values
    # (NOT the cycle-resampled tensor). Use the same T-truncated reward
    # matrix; n is consistent across pairs at T = min(arm_lengths).
    corr_matrix_pearson = np.corrcoef(reward_matrix.T)
    arm_ids = [a["arm_id"] for a in arms]

    payload = {
        "hypothesis_id": "MPV1",
        "experiment": "v1_meta_portfolio_d_ucb",
        "rng_seed": args.rng_seed,
        "n_rounds_T": T,
        "n_arms_K": len(arms),
        "arms": [
            {
                "arm_id": a["arm_id"],
                "description": a["description"],
                "source_sidecar": a["source_sidecar"],
                "filter_symbol": a["filter_symbol"],
                "n_rewards": a["n_rewards"],
                "reward_mean": a["reward_mean"],
                "reward_std": a["reward_std"],
            }
            for a in arms
        ],
        "bandit_results": bandit_results,
        "equal_weight_baseline": eq_weight,
        "oracle_baseline": {
            **oracle,
            "best_arm_id": arms[oracle["best_arm_idx"]]["arm_id"],
        },
        "descriptive_v1_no_inferential_claim": (
            "Per Round-1 audit-remediate-loop reframing: MPV1 v1 emits descriptive "
            "exhibits ONLY. No MPPM-promotable inferential claim. See design.md §1 "
            "reframed deliverables A-D. Sharpe-promotable inference deferred to "
            "MPV2 per P1-MPV2-PER-SESSION-RETURNS-INTEGRATION."
        ),
        "descriptive_paired_bootstrap_ci_bandit_minus_eq_weight": descriptive_diff_by_bandit,
        "correlation_matrix_pearson": corr_matrix_pearson.tolist(),
        "arm_ids": arm_ids,
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    # Pretty-print summary
    print()
    print("=" * 100)
    print(f"MPV1 META-PORTFOLIO v1 — T = {T} rounds × K = {len(arms)} arms")
    print(f"  rng_seed: {args.rng_seed}")
    print(f"  sidecar:  {sidecar_path}")
    print(f"  sha256:   {sha}")
    print("=" * 100)
    print(f"{'arm_id':<14} {'n_rewards':>10} {'reward_mean':>15} {'reward_std':>14}")
    for a in arms:
        print(f"{a['arm_id']:<14} {a['n_rewards']:>10} {a['reward_mean']:>+14.4f} {a['reward_std']:>+13.4f}")
    print()
    print(f"{'bandit':<18} {'cum_reward':>12} {'mean/round':>12} {'cum_regret':>12}  {'top arm':>12}")
    for r in bandit_results:
        top_arm_idx = int(np.argmax(r["allocation_share"]))
        top_arm = arms[top_arm_idx]["arm_id"]
        share = r["allocation_share"][top_arm_idx]
        print(
            f"{r['bandit']:<18} {r['cumulative_reward']:>+11.4f} {r['mean_reward_per_round']:>+11.4f} "
            f"{r['final_cumulative_regret']:>+11.4f}  {top_arm} ({share*100:.0f}%)"
        )
    print(f"{'1/N equal':<18} {eq_weight['cumulative_reward']:>+11.4f} {eq_weight['mean_reward_per_round']:>+11.4f}  ----")
    print(f"{'oracle best':<18} {oracle['cumulative_reward']:>+11.4f} {oracle['best_arm_mean']:>+11.4f}  ({arms[oracle['best_arm_idx']]['arm_id']})")
    print()
    # Descriptive paired bootstrap CI table
    if descriptive_diff_by_bandit:
        print()
        print("DESCRIPTIVE: paired stationary-bootstrap CI on (bandit - 1/N) per-round diff")
        print(f"  (NOT a Sharpe-promotion gate per ADR-0017 §3; v1 is descriptive-only)")
        for name, d in descriptive_diff_by_bandit.items():
            excl = "EXCLUDES ZERO" if d["excludes_zero"] else "covers zero"
            print(
                f"  {name:<18} point={d['point_estimate']:+.4f}  "
                f"CI=[{d['ci_low']:+.4f}, {d['ci_high']:+.4f}]  {excl}  "
                f"(block_len={d['block_length']:.1f})"
            )
    print("=" * 100)
    return 0


if __name__ == "__main__":
    # ADR-0009 BLAS thread-pinning carry-forward (canonical block from
    # scripts/run_h052a_walk_forward.py:915-942). Required for byte-deterministic
    # numpy/scipy results across machines; without this, bootstrap CIs +
    # MPPM/SPA/Calmar/PF/R-multiple primitives may produce non-reproducible
    # output, breaking the ReproLog contract. Closes the Phase O.2-O.9 Round-1
    # code-reviewer audit finding (BLAS pinning missing at 7 orchestrator
    # __main__ entries).
    import os as _os
    _required_thread_pinning = (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
    )
    _missing_pinning = [
        k for k in _required_thread_pinning if _os.environ.get(k) != "1"
    ]
    if _missing_pinning:
        raise RuntimeError(
            f"BLAS thread-pinning env vars {_missing_pinning!r} must be "
            "set to '1' per ADR-0009. The canonical launch path prefixes "
            "the orchestrator invocation with: "
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1"
        )
    try:
        from threadpoolctl import threadpool_limits as _threadpool_limits
    except ImportError:
        _threadpool_limits = None
    if _threadpool_limits is not None:
        _threadpool_limits(limits=1)
    sys.exit(main())
