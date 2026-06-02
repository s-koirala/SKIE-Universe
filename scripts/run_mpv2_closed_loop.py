"""MPV2 regime-switching meta-allocation closed loop (Phase P P-1 + P-4 + P-5).

Implements the ADR-0029 §D-4 falsifiable experiment per the MPV2 pre-registration
([research/01_meta_portfolio/MPV2/design.md]): a capital allocator over a
de-correlated arm library that (P-5) reallocates via the switching-bandit
([skie_ninja.meta.switching_bandit]; ADR-0018 §D-4), de-risks via the leading
early-warning layer ([skie_ninja.inference.early_warning]; ADR-0029 §D-2), and
sizes under the CPPI floor-ratchet ([skie_ninja.sizing.ergodicity]; ADR-0029
§D-3), then is compared against equal-weight 1/N ([DeMiguel-Garlappi-Uppal 2009]
DOI 10.1093/rfs/hhm075) and passive buy-and-hold on the per-session return
differential with a paired stationary-bootstrap CI ([Politis-Romano 1994] DOI
10.1080/01621459.1994.10476870; block length [Politis-White 2004] DOI
10.1081/ETC-120028836).

P-1 (reward matrix): built from each arm's `per_session_logret_aggregate` sidecar
field, inner-joined on session calendar (§3.2). The real per-session arrays are
emitted by re-running each arm's orchestrator on the canonical substrate
(`P1-MPV2-PER-SESSION-RETURNS-INTEGRATION`); until then `--synthetic` exercises
the full pipeline on a regime-structured fixture for validation.

P-4 (correlation): the cross-arm Pearson correlation matrix + effective breadth
gates the §1 pooling premise (`P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE`).

Causal-alignment invariant (§3.4): the bandit is selected on a pre-OOS calibration
head; the closed loop + benchmarks + CI run only on the disjoint evaluation tail;
the oracle is a labeled non-tradeable diagnostic.

ReproLog wiring deferred to `P1-MPV2-REPROLOG-WIRE`.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from skie_ninja.inference.bootstrap import (
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_ninja.inference.early_warning import (
    EarlyWarningConfig,
    early_warning_update,
    evaluate_early_warning,
    init_early_warning,
)
from skie_ninja.inference.mppm import mppm_rho_1
from skie_ninja.meta.switching_bandit import (
    DUCBBandit,
    EXP3SBandit,
    SWUCBBandit,
    select_bandit_by_regret,
)
from skie_ninja.sizing.ergodicity import CPPIConfig, cppi_risk_overlay

_log = logging.getLogger(__name__)

_DEFAULT_CALIBRATION_FRACTION = 0.30  # justify: pre-OOS head for §5 bandit selection; calibrate
_DEFAULT_STARTING_EQUITY = 10_000.0  # ADR-0013 §3.1 $10K baseline
_DEFAULT_N_BOOTSTRAP = 1000  # project-standard bootstrap replicate count
_MIN_ARMS = 2  # switching-bandit requires n_arms >= 2


def synthetic_regime_matrix(
    *,
    rng_seed: int,
    n_regimes: int = 4,
    regime_len: int = 120,
    n_arms: int = 4,
    winner_mean: float = 0.012,
    noise_sd: float = 0.012,
) -> np.ndarray:
    """Regime-structured (T, M) per-session return matrix for pipeline validation.

    In regime k the k-th arm carries a positive mean edge and the others are
    zero-mean noise; the dominant arm rotates each regime. An ideal switcher
    captures the rotating winner and beats 1/N on selection — the property the
    validation test asserts. NOT a model of any real market.
    """
    rng = np.random.default_rng(rng_seed)
    blocks = []
    for regime in range(n_regimes):
        winner = regime % n_arms
        means = np.zeros(n_arms)
        means[winner] = winner_mean
        block = rng.normal(loc=means, scale=noise_sd, size=(regime_len, n_arms))
        blocks.append(block)
    return np.vstack(blocks)


def build_reward_matrix_from_sidecars(
    arm_sidecar_paths: dict[str, str], repo_root: Path
) -> tuple[np.ndarray, list[str]]:
    """Build the (T, M) per-session reward matrix from arm sidecars (P-1).

    Each sidecar must carry `per_session_logret_aggregate` (Phase O.13 schema).
    Arms are inner-joined to the common length (the shortest series; full
    calendar-date alignment is `P1-MPV1-CALENDAR-ALIGNMENT`, tracked separately).

    Raises:
        FileNotFoundError: if a sidecar is missing.
        ValueError: if a sidecar lacks `per_session_logret_aggregate` (P-1 not yet
            emitted for that arm — re-run its orchestrator).
    """
    arm_ids = sorted(arm_sidecar_paths)
    series: list[np.ndarray] = []
    for arm_id in arm_ids:
        path = repo_root / arm_sidecar_paths[arm_id]
        if not path.exists():
            raise FileNotFoundError(f"arm {arm_id} sidecar not found: {path}")
        payload = json.loads(path.read_text())
        arr = payload.get("per_session_logret_aggregate")
        if arr is None:
            raise ValueError(
                f"arm {arm_id} sidecar lacks `per_session_logret_aggregate` — "
                "P-1 not yet emitted; re-run its orchestrator "
                "(P1-MPV2-PER-SESSION-RETURNS-INTEGRATION)."
            )
        series.append(np.asarray(arr, dtype=float).ravel())
    common_t = min(s.size for s in series)
    matrix = np.column_stack([s[:common_t] for s in series])
    return matrix, arm_ids


def extract_arm_per_session(spec: dict[str, Any], repo_root: Path) -> np.ndarray:
    """Extract one arm's per-session LOG-return stream from a committed artifact (P-1).

    Two source kinds let the reward matrix consume what each arm already produces:
    - {"kind": "sidecar", "path": ...}: the `per_session_logret_aggregate` field
      (H055 + H062 orchestrators emit it per the Phase O.13 schema).
    - {"kind": "parquet", "run_dir": ..., "column": ..., "symbols": [...] (optional)}:
      per-symbol `oos_returns.parquet` columns concatenated (the H050 convention —
      the `gated_return` column is LOG returns since H050 works in log space, so it is
      unit-consistent with the sidecar field's log convention; a shared reward matrix
      must keep ALL arms on the same log convention).

    Cross-symbol alignment is positional concatenation at v1; date-keyed inner-join is
    `P1-MPV1-CALENDAR-ALIGNMENT` (BLOCKING-before-real-verdict).

    Args:
        spec: the per-arm source spec (see kinds above).
        repo_root: repo root the spec paths are relative to.

    Returns:
        1-D per-session log-return array.

    Raises:
        ValueError: on an unknown `kind`, a sidecar missing the field, or a parquet
            run_dir with no per-symbol oos_returns.parquet.
        FileNotFoundError: if a sidecar / run_dir path is absent.
    """
    kind = spec.get("kind")
    if kind == "sidecar":
        path = repo_root / spec["path"]
        if not path.exists():
            raise FileNotFoundError(f"sidecar not found: {path}")
        arr = json.loads(path.read_text()).get("per_session_logret_aggregate")
        if arr is None:
            raise ValueError(
                f"sidecar {path} lacks `per_session_logret_aggregate` — re-run the arm "
                "orchestrator (P1-MPV2-PER-SESSION-RETURNS-INTEGRATION)."
            )
        return np.asarray(arr, dtype=float).ravel()
    if kind == "parquet":
        run_dir = repo_root / spec["run_dir"]
        if not run_dir.exists():
            raise FileNotFoundError(f"run_dir not found: {run_dir}")
        column = spec["column"]
        symbols = spec.get("symbols")
        files = (
            [run_dir / s / "oos_returns.parquet" for s in symbols]
            if symbols is not None
            else sorted(run_dir.glob("*/oos_returns.parquet"))
        )
        files = [f for f in files if f.exists()]
        if not files:
            raise ValueError(f"no per-symbol oos_returns.parquet under {run_dir}.")
        streams = [pl.read_parquet(f)[column].to_numpy().astype(float) for f in files]
        return np.concatenate(streams)
    raise ValueError(f"unknown spec kind {kind!r}; expected 'sidecar' or 'parquet'.")


def cross_arm_correlation(matrix: np.ndarray) -> dict[str, Any]:
    """Cross-arm Pearson correlation matrix + effective breadth (P-4, §3.3).

    `effective_breadth` is the Meucci 2009 effective-number-of-bets (eigenvalue
    entropy of the correlation matrix) — it falls toward 1 as the arms become
    perfectly correlated (no pooling lift) and approaches N when de-correlated
    (full lift, ADR-0029 §D-3.4). `mean_abs_correlation_breadth_proxy` is a
    conservative secondary heuristic that understates ENB at positive ρ.
    """
    corr = np.corrcoef(matrix, rowvar=False)
    n = corr.shape[0]
    offdiag = corr[~np.eye(n, dtype=bool)]
    mean_abs = float(np.mean(np.abs(offdiag))) if offdiag.size else 0.0
    max_abs = float(np.max(np.abs(offdiag))) if offdiag.size else 0.0
    # F-1-3 audit: canonical effective-number-of-bets via eigenvalue entropy
    # (Meucci 2009 "Managing Diversification" Risk 22(5):74-79): ENB = exp(-Σ p_i ln p_i)
    # on the normalized correlation-matrix eigenvalues. The mean-abs-correlation form
    # is retained as a conservative secondary proxy (it understates ENB at positive ρ).
    eigvals = np.clip(np.linalg.eigvalsh(corr), 0.0, None)
    total = float(eigvals.sum())
    p = eigvals / total if total > 0.0 else np.full(n, 1.0 / n)
    p = p[p > 0.0]
    enb = float(np.exp(-np.sum(p * np.log(p))))
    breadth_proxy = n / (1.0 + (n - 1) * mean_abs)
    return {
        "correlation_matrix": corr.tolist(),
        "mean_abs_offdiag": mean_abs,
        "max_abs_offdiag": max_abs,
        "effective_breadth": enb,
        "mean_abs_correlation_breadth_proxy": float(breadth_proxy),
        "n_arms": n,
    }


def _candidate_bandits(calibration_len: int) -> dict[str, Any]:
    window = max(20, calibration_len // 4)  # justify: SW-UCB window; calibrate per §5
    return {
        "d_ucb": lambda k, r: DUCBBandit(k, rng=r),
        "sw_ucb": lambda k, r, w=window: SWUCBBandit(k, window=w, rng=r),
        "exp3s": lambda k, r: EXP3SBandit(k, rng=r),
    }


def select_and_run_bandit(
    calibration_matrix: np.ndarray,
    evaluation_matrix: np.ndarray,
    rng_seed: int,
) -> tuple[str, dict[str, float], np.ndarray]:
    """Select the min-regret bandit on the calibration head (§5), run it on the
    disjoint evaluation tail to get the causal arm-choice sequence (§3.4)."""
    candidates = _candidate_bandits(calibration_matrix.shape[0])
    winner, regret_table = select_bandit_by_regret(
        calibration_matrix, candidates, rng_seed=rng_seed
    )
    factory = candidates[winner]
    bandit = factory(evaluation_matrix.shape[1], np.random.default_rng(rng_seed))
    arm_choices = bandit.run(evaluation_matrix).arm_choices
    return winner, regret_table, arm_choices


def apply_sizing_overlay(
    raw_returns: np.ndarray,
    *,
    cppi_config: CPPIConfig,
    ew_config: EarlyWarningConfig,
    reference_mean: float,
    reference_sigma: float,
    starting_equity: float,
) -> dict[str, Any]:
    """Apply the per-session CPPI × early-warning de-risk overlay to a raw return stream.

    Used IDENTICALLY on the allocator's chosen-arm stream AND on the 1/N and
    buy-and-hold benchmarks so the §1 comparison is like-for-like sized (F-1-1
    audit) — comparing a de-risked allocator against a sizing-free benchmark would
    penalize the allocator on the exposure throttle, not its selection skill.

    Args:
        raw_returns: 1-D per-session arithmetic return stream.
        cppi_config: CPPI floor-ratchet config (ADR-0029 §D-3).
        ew_config: early-warning config (ADR-0029 §D-2).
        reference_mean: FROZEN in-regime baseline mean for the early-warning CUSUM
            (computed from the calibration head — causal).
        reference_sigma: FROZEN in-regime baseline std for the early-warning CUSUM.
        starting_equity: starting bankroll.

    Returns:
        dict with `sized_returns` (1-D), `final_equity`, `derisk_session_count`.
    """
    n = raw_returns.shape[0]
    equity = starting_equity
    peak = starting_equity
    ew_state = init_early_warning(
        ew_config, reference_mean=reference_mean, reference_sigma=reference_sigma
    )
    sized_returns = np.empty(n, dtype=float)
    derisk_count = 0
    for t in range(n):
        raw_r = float(raw_returns[t])
        # justify: the early-warning layer reads the RAW per-session increment so it
        # detects decay independent of the allocator's own throttle (intentional per
        # design §4.2); causal — raw_r at t is observed at t.
        early_warning_update(ew_state, raw_r)
        signal = evaluate_early_warning(ew_state)
        overlay = cppi_risk_overlay(equity, peak, cppi_config)
        scale = overlay.sizing_scale * signal.derisk_multiplier
        if signal.fired:
            derisk_count += 1
        sized_r = scale * raw_r
        sized_returns[t] = sized_r
        equity *= 1.0 + sized_r
        peak = max(peak, equity)
    return {
        "sized_returns": sized_returns,
        "final_equity": float(equity),
        "derisk_session_count": derisk_count,
    }


def closed_loop_equity(
    evaluation_matrix: np.ndarray,
    arm_choices: np.ndarray,
    *,
    cppi_config: CPPIConfig,
    ew_config: EarlyWarningConfig,
    reference_mean: float,
    reference_sigma: float,
    starting_equity: float,
) -> dict[str, Any]:
    """Allocator closed loop: extract the chosen-arm raw stream, apply the sizing overlay.

    Args:
        evaluation_matrix: (T, M) per-session reward matrix (the OOS eval tail).
        arm_choices: length-T int array of the bandit's per-session arm indices.
        cppi_config / ew_config / reference_mean / reference_sigma / starting_equity:
            forwarded to `apply_sizing_overlay`.

    Returns:
        dict with `sized_returns`, `raw_selected_returns`, `final_equity`,
        `derisk_session_count`.

    Raises:
        ValueError: if arm_choices is not length-T or indexes outside [0, M).
    """
    n, m = evaluation_matrix.shape
    arm_choices = np.asarray(arm_choices, dtype=np.int64)
    if arm_choices.shape[0] != n:
        raise ValueError(f"arm_choices length {arm_choices.shape[0]} != n_sessions {n}.")
    if arm_choices.size and (int(arm_choices.min()) < 0 or int(arm_choices.max()) >= m):
        raise ValueError(f"arm_choices index out of range [0, {m}).")
    raw_selected = evaluation_matrix[np.arange(n), arm_choices]
    overlay = apply_sizing_overlay(
        raw_selected,
        cppi_config=cppi_config,
        ew_config=ew_config,
        reference_mean=reference_mean,
        reference_sigma=reference_sigma,
        starting_equity=starting_equity,
    )
    return {
        "sized_returns": overlay["sized_returns"],
        "raw_selected_returns": raw_selected,
        "final_equity": overlay["final_equity"],
        "derisk_session_count": overlay["derisk_session_count"],
    }


def benchmark_streams(
    evaluation_matrix: np.ndarray, passive_long: np.ndarray | None
) -> dict[str, Any]:
    """1/N (primary), buy-and-hold passive-long (if supplied), oracle (non-tradeable)."""
    one_over_n = evaluation_matrix.mean(axis=1)
    arm_means = evaluation_matrix.mean(axis=0)
    oracle_arm = int(np.argmax(arm_means))
    return {
        "one_over_n": one_over_n,
        "buy_and_hold": passive_long if passive_long is not None else None,
        "oracle_nontradeable": evaluation_matrix[:, oracle_arm],
        "oracle_arm_idx": oracle_arm,
    }


def paired_bootstrap_ci(
    diff: np.ndarray,
    *,
    n_bootstrap: int = _DEFAULT_N_BOOTSTRAP,
    confidence: float = 0.95,
    rng_seed: int = 20260602,
) -> dict[str, Any]:
    """Paired stationary-bootstrap CI on a per-session paired-difference series (§7)."""
    d = np.asarray(diff, dtype=float).ravel()
    sel = politis_white_block_length(d, bootstrap_type="stationary")
    bl = float(sel.block_length)
    rng = np.random.default_rng(rng_seed)
    boot = np.empty(n_bootstrap, dtype=float)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n=d.size, block_length=bl, rng=rng)
        boot[b] = float(d[idx].mean())
    alpha = 1.0 - confidence
    lo_one_sided = float(np.quantile(boot, alpha))  # one-sided 95% lower bound (§7 test)
    lo_two_sided = float(np.quantile(boot, alpha / 2.0))
    hi_two_sided = float(np.quantile(boot, 1.0 - alpha / 2.0))
    return {
        "mean_diff": float(d.mean()),
        "ci_lower_one_sided": lo_one_sided,
        "ci_two_sided": [lo_two_sided, hi_two_sided],
        "excludes_zero_positive": bool(lo_one_sided > 0.0),
        "block_length": bl,
        "n_bootstrap": n_bootstrap,
    }


def run_pipeline(
    matrix: np.ndarray,
    arm_ids: list[str],
    *,
    calibration_fraction: float = _DEFAULT_CALIBRATION_FRACTION,
    starting_equity: float = _DEFAULT_STARTING_EQUITY,
    rng_seed: int = 20260602,
    passive_long: np.ndarray | None = None,
) -> dict[str, Any]:
    """Run P-4 correlation + §5 bandit selection + P-5 closed loop + §7 inference.

    Args:
        matrix: (T, M) per-session reward matrix (P-1).
        arm_ids: M arm identifiers aligned with matrix columns.
        calibration_fraction: head fraction in (0, 1) for §5 bandit selection.
        starting_equity: starting bankroll (ADR-0013 §3.1 $10K baseline).
        rng_seed: deterministic seed.
        passive_long: optional full-length (T,) passive buy-and-hold per-session
            return series for the §1(b) benchmark; None → B&H undetermined.

    Returns:
        dict of the P-4 correlation diagnostic, the selected bandit + regret table,
        the closed-loop MPPM(ρ=1) time-average headline (+ ensemble-caveated final
        equity), the sized-consistent vs-1/N and vs-B&H differentials (paired
        bootstrap CIs), the secondary raw-selection differential, the tri-state
        conjunctive verdict, and the disposition.

    Raises:
        ValueError: on < 2 arms, calibration_fraction outside (0, 1), too-few
            sessions, a passive_long length mismatch, or a degenerate calibration head.
    """
    if matrix.shape[1] < _MIN_ARMS:
        raise ValueError(f"need >= {_MIN_ARMS} arms, got {matrix.shape[1]}.")
    if not 0.0 < calibration_fraction < 1.0:
        raise ValueError(f"calibration_fraction must be in (0, 1), got {calibration_fraction}.")
    t_total = matrix.shape[0]
    if passive_long is not None and np.asarray(passive_long).shape[0] != t_total:
        raise ValueError(
            f"passive_long length {np.asarray(passive_long).shape[0]} != n_sessions {t_total}."
        )
    t_cal = int(t_total * calibration_fraction)
    if t_cal < _MIN_ARMS or (t_total - t_cal) < _MIN_ARMS:
        raise ValueError(
            f"too few sessions ({t_total}) for calibration_fraction={calibration_fraction}."
        )
    calib, eval_matrix = matrix[:t_cal], matrix[t_cal:]

    correlation = cross_arm_correlation(matrix)
    winner, regret_table, arm_choices = select_and_run_bandit(calib, eval_matrix, rng_seed)

    cal_one_over_n = calib.mean(axis=1)
    if cal_one_over_n.size < _MIN_ARMS:
        raise ValueError("calibration head too short to estimate the early-warning reference.")
    reference_mean = float(cal_one_over_n.mean())
    reference_sigma = float(
        cal_one_over_n.std(ddof=1)
    )  # F-1-8 audit: raise (not silent 1.0) on degenerate head

    sizing_kwargs: dict[str, Any] = {
        "cppi_config": CPPIConfig(),
        "ew_config": EarlyWarningConfig(),
        "reference_mean": reference_mean,
        "reference_sigma": reference_sigma,
        "starting_equity": starting_equity,
    }
    closed = closed_loop_equity(eval_matrix, arm_choices, **sizing_kwargs)
    sized = closed["sized_returns"]
    raw_sel = closed["raw_selected_returns"]

    bench = benchmark_streams(
        eval_matrix, passive_long[t_cal:] if passive_long is not None else None
    )
    one_over_n = bench["one_over_n"]
    # F-1-1 audit: size the benchmarks through the IDENTICAL overlay so the §1
    # comparison is like-for-like (de-risked allocator vs de-risked benchmark).
    sized_one_over_n = apply_sizing_overlay(one_over_n, **sizing_kwargs)["sized_returns"]

    vs_1n_sized = paired_bootstrap_ci(sized - sized_one_over_n, rng_seed=rng_seed)
    vs_1n_selection = paired_bootstrap_ci(raw_sel - one_over_n, rng_seed=rng_seed)
    if bench["buy_and_hold"] is not None:
        sized_bh = apply_sizing_overlay(bench["buy_and_hold"], **sizing_kwargs)["sized_returns"]
        vs_bh = paired_bootstrap_ci(sized - sized_bh, rng_seed=rng_seed)
    else:
        vs_bh = None

    # F-1-4 audit: the §1 hypothesis is conjunctive over BOTH benchmarks, so a
    # missing B&H makes the verdict UNDETERMINED (None), not silently False.
    beat_both: bool | None = (
        None
        if vs_bh is None
        else bool(vs_1n_sized["excludes_zero_positive"] and vs_bh["excludes_zero_positive"])
    )

    return {
        "arm_ids": arm_ids,
        "n_sessions_total": t_total,
        "n_sessions_calibration": t_cal,
        "n_sessions_evaluation": int(eval_matrix.shape[0]),
        "correlation": correlation,
        "selected_bandit": winner,
        "regret_table": regret_table,
        # F-1-2 audit: headline the time-average growth (MPPM ρ=1) on the sized
        # stream per ADR-0029 §D-3.1; final_equity is the demoted ensemble quantity.
        "closed_loop_mppm_rho_1_time_average": float(mppm_rho_1(sized)),
        "one_over_n_mppm_rho_1_time_average": float(mppm_rho_1(sized_one_over_n)),
        "closed_loop_final_equity_ensemble_caveat": closed["final_equity"],
        "closed_loop_derisk_session_count": closed["derisk_session_count"],
        "closed_loop_vs_1_over_N_sized": vs_1n_sized,
        "closed_loop_vs_1_over_N_selection": vs_1n_selection,
        "closed_loop_vs_buy_and_hold": vs_bh,
        "beat_both_conjunctive": beat_both,
        "oracle_nontradeable_mean": float(bench["oracle_nontradeable"].mean()),
        "disposition": _disposition(vs_1n_sized, vs_bh),
    }


def _disposition(vs_1n: dict[str, Any], vs_bh: dict[str, Any] | None) -> str:
    if vs_bh is None:
        # F-1-4 audit: B&H not supplied → the conjunctive §1 verdict is UNDETERMINED,
        # never a completed pass/fail (the label says so to avoid mis-reading).
        clears_1n = vs_1n["excludes_zero_positive"]
        return "beat-1N-BH-not-evaluated" if clears_1n else "null-vs-1N-BH-not-evaluated"
    if vs_1n["excludes_zero_positive"] and vs_bh["excludes_zero_positive"]:
        return "beat-both-conjunctive"
    if vs_1n["excludes_zero_positive"] or vs_bh["excludes_zero_positive"]:
        return "beat-one"
    return "null"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MPV2 regime-switching closed loop")
    parser.add_argument(
        "--synthetic", action="store_true", help="run on a regime-structured synthetic fixture"
    )
    parser.add_argument("--rng-seed", type=int, default=20260602)
    parser.add_argument("--calibration-fraction", type=float, default=_DEFAULT_CALIBRATION_FRACTION)
    parser.add_argument("--starting-equity", type=float, default=_DEFAULT_STARTING_EQUITY)
    parser.add_argument("--out", type=str, default=None, help="sidecar output path")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.synthetic:
        matrix = synthetic_regime_matrix(rng_seed=args.rng_seed)
        arm_ids = [f"synthetic_arm_{i}" for i in range(matrix.shape[1])]
    else:
        raise SystemExit(
            "real-data mode requires the per-session arm arrays (P-1); pass --synthetic to "
            "validate the pipeline, or wire build_reward_matrix_from_sidecars once "
            "P1-MPV2-PER-SESSION-RETURNS-INTEGRATION has re-emitted the arm sidecars."
        )

    result = run_pipeline(
        matrix,
        arm_ids,
        calibration_fraction=args.calibration_fraction,
        starting_equity=args.starting_equity,
        rng_seed=args.rng_seed,
    )
    _log.info("selected bandit=%s disposition=%s", result["selected_bandit"], result["disposition"])
    _log.info(
        "vs 1/N (selection) mean_diff=%.5f one-sided-lower=%.5f excludes_zero=%s",
        result["closed_loop_vs_1_over_N_selection"]["mean_diff"],
        result["closed_loop_vs_1_over_N_selection"]["ci_lower_one_sided"],
        result["closed_loop_vs_1_over_N_selection"]["excludes_zero_positive"],
    )
    _log.info("effective_breadth=%.3f", result["correlation"]["effective_breadth"])

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))
        _log.info("wrote %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
