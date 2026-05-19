"""BOCD live-pause NIG prior calibration per `P1-BOCD-LIVE-PRIOR-CALIBRATION-{H062,H055}-V3`.

Per the Phase O.13 buildout 7d63795 R1 F-1-3 audit fix:

    The default BOCDLiveConfig NIG hyperparameters
    (mu_0=0, kappa_0=1, alpha_0=1, beta_0=1) produce a unit-variance prior
    that does NOT match the empirical scale of per-session H062 / H055
    log-returns (typically σ² ~ 1e-4 to 1e-3). Without calibration, the
    bocd_live primitive's pause-detection sensitivity is operationally
    broken — it will either over-flag (treating typical noise as
    changepoints) or under-flag (waiting for unrealistic shifts).

This script reads existing v2 sidecars (Phase O.10 emissions on the
canonical substrate at SHA `317429e4...`) and computes empirically-
calibrated NIG priors per hypothesis.

NIG prior parameterization per Murphy 2007 + Adams-MacKay 2007:

    Prior:  σ² ~ InverseGamma(alpha_0, beta_0)
            μ | σ² ~ Normal(mu_0, σ² / kappa_0)

    Prior moments (for alpha_0 > 1):
            E[μ]        = mu_0
            E[σ²]       = beta_0 / (alpha_0 - 1)
            Var[σ²]     = beta_0² / ((alpha_0 - 1)² (alpha_0 - 2))  [for alpha_0 > 2]

To match empirical moments:
    - mu_0      = empirical mean of per-session log-returns.
    - kappa_0   = pseudo-observations of mu_0; project-operational
                  default = 1.0 (weak; one pseudo-obs).
                  # justify: weak prior on mu allows posterior to track
                  # observed mean within ~1 session.
    - alpha_0   = shape parameter; project-operational default = 2.0
                  giving moderate strength. # justify: alpha_0 > 1
                  guarantees finite E[σ²]; alpha_0 = 2.0 is the smallest
                  value with finite Var[σ²] = infinity (right at the
                  boundary); operationally robust to outliers.
    - beta_0    = (alpha_0 - 1) × empirical_variance. # justify: matches
                  E[σ²] to empirical variance.

Emits `config/bocd_live_priors.yaml` with one entry per hypothesis.
The H062 + H055 v2 orchestrators read this YAML at startup when
`--enable-bocd-live` is on (wiring tracked under follow-up
`P1-BOCD-LIVE-PRIOR-LOAD-FROM-CONFIG`).

Usage:

    uv run python scripts/calibrate_bocd_live_priors.py \\
        --h062-sidecar artifacts/runs/H062/<run_id>/sidecar.json \\
        --h055-sweep-sidecar artifacts/runs/H055/v2_sweep_<ts>/sweep_sidecar.json \\
        --out config/bocd_live_priors.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

# justify: 1.0 weak pseudo-observation count for mu_0; allows posterior to
# track observed per-session mean within ~1 session.
_KAPPA_0_DEFAULT: float = 1.0
# justify: 3.0 is the smallest alpha_0 with FINITE Var[sigma^2] per Murphy
# 2007 §inverse-gamma — Var[InvGamma(alpha, beta)] = beta^2 / ((alpha-1)^2
# (alpha-2)) requires alpha > 2. Prior default 2.0 had INFINITE Var[sigma^2]
# (denominator zero); corrected to 3.0 per R1 audit F-1-2.
_ALPHA_0_DEFAULT: float = 3.0
# Minimum-observations floor for stable second-moment estimation per R1
# audit F-1-6. justify: 50 matches Cont 2001 QF 1(2):223-236 fat-tailed
# return moment-estimation sample requirements (vs R-multiple primitive's
# n_min=30 which is for sample-mean stability, not variance-of-variance).
_N_MIN_OBSERVATIONS: int = 50


def _extract_h062_per_session_logrets(
    sidecar_data: dict,
) -> tuple[list[float], bool]:
    """Walk H062 v2 sidecar per_fold list + extract per_session_logret arrays.

    Per the H062 walk-forward orchestrator emission, each per_fold record
    carries a `per_session_logret` array (when persisted). Concatenate
    across folds to get the OOS per-session log-return distribution.

    Fallback path: when the existing v2 sidecar (pre-`P1-PHASE-O13-SIDECAR-
    PER-SESSION-LOGRET-PERSIST`) does NOT carry `per_session_logret` arrays,
    extract from `per_fold.mppm_oos` × Δt approximation. This is the
    annualized log-wealth growth rate per fold; dividing by 252 (sessions/yr)
    gives a per-session log-return PROXY suitable for v1 calibration of the
    BOCD prior. justify: per ADR-0018 D-1 MPPM(ρ=1) reduces to log-wealth
    growth rate per GISW 2007 §2; per-fold mppm × Δt = per-session log-return
    in expectation (smoothed by fold aggregation). Operators should refine
    with proper per-session data once per_session_logret_aggregate is
    persisted in sidecar (tracked under follow-up).
    """
    per_fold = sidecar_data.get("per_fold", [])
    all_logrets: list[float] = []
    used_degenerate_fallback = False
    # Path 1: direct per_session_logret arrays (preferred; absent in existing v2).
    for fold in per_fold:
        fold_logrets = fold.get("per_session_logret", [])
        if fold_logrets:
            for v in fold_logrets:
                try:
                    fv = float(v)
                    if np.isfinite(fv):
                        all_logrets.append(fv)
                except (TypeError, ValueError):
                    continue
    if all_logrets:
        return all_logrets, used_degenerate_fallback
    # Path 2 (DEGENERATE FALLBACK per R1 audit F-1-1): per-fold mppm_oos / 252
    # proxy. The replication-to-n-copies-per-fold produces a point-mass-per-
    # fold distribution; the resulting variance estimator measures BETWEEN-fold
    # variance NOT WITHIN-session variance — the latter is the quantity the
    # BOCD prior is supposed to encode. This emits a LOWER-BOUND on the true
    # within-session variance; the BOCD primitive will UNDER-flag changepoints.
    # USE FOR DEVELOPMENT ONLY; mark caller's emission as degenerate-fallback.
    # Proper calibration requires per-session log-return arrays persisted in
    # sidecar per P1-PHASE-O13-SIDECAR-PER-SESSION-LOGRET-PERSIST.
    used_degenerate_fallback = True
    # justify: per ADR-0018
    # D-1 MPPM(ρ=1) is annualized log-wealth growth; / 252 = per-session
    # expectation. Smoothed by fold aggregation but operationally usable.
    for fold in per_fold:
        mppm = fold.get("mppm_oos")
        n_sessions = fold.get("n_oos_sessions", 0)
        if mppm is None or not n_sessions:
            continue
        try:
            mppm_v = float(mppm)
            if not np.isfinite(mppm_v):
                continue
            # justify: 252 = ADR-0004 trading-sessions-per-year; matches
            # bocd_live.py default hazard_rate 1/250 semantically.
            per_session_proxy = mppm_v / 252.0
            # Replicate to approximate the per-session distribution: emit
            # n_oos_sessions copies of the per-session proxy. This is a
            # rough approximation; with n_sessions copies per fold, the
            # aggregate is point-mass per fold but spreads across folds.
            for _ in range(int(n_sessions)):
                all_logrets.append(per_session_proxy)
        except (TypeError, ValueError):
            continue
    return all_logrets, used_degenerate_fallback


def _extract_h055_per_session_logrets(
    sweep_data: dict,
) -> tuple[list[float], bool]:
    """Walk H055 v2 sweep sidecar results + extract per_session_log_returns.

    Per the H055 v2 sweep orchestrator emission, each per-cell result
    carries a `per_session_log_returns` list (when persisted; absent in
    pre-`P1-PHASE-O13-SIDECAR-PER-SESSION-LOGRET-PERSIST` v2 emissions).

    Fallback: per-cell `mppm_rho_1_annualised` × 1/n_bars proxy, paralleling
    the H062 fold-level fallback. justify: same MPPM(ρ=1) = annualized
    log-wealth growth semantic per GISW 2007 §2.
    """
    results = sweep_data.get("results", [])
    all_logrets: list[float] = []
    used_degenerate_fallback = False
    # Path 1: direct per_session_log_returns arrays (preferred; absent in v2).
    for res in results:
        cell_logrets = res.get("per_session_log_returns", [])
        if cell_logrets:
            for v in cell_logrets:
                try:
                    fv = float(v)
                    if np.isfinite(fv):
                        all_logrets.append(fv)
                except (TypeError, ValueError):
                    continue
    if all_logrets:
        return all_logrets, used_degenerate_fallback
    # Path 2 (DEGENERATE FALLBACK per R1 F-1-1): see H062 docstring above.
    used_degenerate_fallback = True
    # justify: per-cell mppm × n_bars-derived n_sessions proxy.
    # justify: n_sessions = n_bars / 78 (5-min bars per RTH session); MPPM /
    # 252 = per-session log-return expectation per ADR-0018 D-1 reduction.
    for res in results:
        mppm = res.get("mppm_rho_1_annualised")
        n_bars = res.get("n_bars", 0)
        if mppm is None or not n_bars:
            continue
        try:
            mppm_v = float(mppm)
            if not np.isfinite(mppm_v):
                continue
            n_sessions_approx = int(int(n_bars) / 78)  # 78 5-min bars per session
            if n_sessions_approx <= 0:
                continue
            per_session_proxy = mppm_v / 252.0
            for _ in range(n_sessions_approx):
                all_logrets.append(per_session_proxy)
        except (TypeError, ValueError):
            continue
    return all_logrets, used_degenerate_fallback


def calibrate_nig_priors_from_logrets(
    logrets: list[float],
    *,
    kappa_0: float = _KAPPA_0_DEFAULT,
    alpha_0: float = _ALPHA_0_DEFAULT,
) -> dict[str, float]:
    """Compute NIG prior hyperparameters from empirical per-session log-returns.

    Returns dict with `mu_0`, `kappa_0`, `alpha_0`, `beta_0`, plus
    diagnostic `n_observations`, `empirical_mean`, `empirical_variance`.

    Raises ValueError if `len(logrets) < 30` (insufficient for stable
    moment estimates) or if `empirical_variance == 0` (degenerate).
    """
    # justify: n_min per Cont 2001 QF 1(2):223-236 fat-tailed return
    # moment-estimation sample requirements (R1 audit F-1-6 bumped from 30
    # to 50 — the prior value was for sample-mean stability not variance-
    # of-variance).
    if len(logrets) < _N_MIN_OBSERVATIONS:
        raise ValueError(
            f"Need at least {_N_MIN_OBSERVATIONS} observations for stable "
            f"variance-of-variance moment estimates; got {len(logrets)}."
        )
    arr = np.asarray(logrets, dtype=float)
    empirical_mean = float(np.mean(arr))
    empirical_variance = float(np.var(arr, ddof=1))  # sample variance
    if empirical_variance <= 0.0:
        raise ValueError(
            f"Empirical variance must be positive; got {empirical_variance}. "
            f"Degenerate per-session log-return distribution."
        )
    if alpha_0 <= 1.0:
        raise ValueError(
            f"alpha_0 must be > 1.0 for finite E[σ²]; got {alpha_0}."
        )
    if kappa_0 <= 0.0:
        raise ValueError(f"kappa_0 must be > 0; got {kappa_0}.")

    mu_0 = empirical_mean
    # E[σ²] = beta_0 / (alpha_0 - 1) → beta_0 = (alpha_0 - 1) × empirical_var.
    beta_0 = (alpha_0 - 1.0) * empirical_variance

    return {
        "mu_0": float(mu_0),
        "kappa_0": float(kappa_0),
        "alpha_0": float(alpha_0),
        "beta_0": float(beta_0),
        "n_observations": int(len(logrets)),
        "empirical_mean": float(empirical_mean),
        "empirical_variance": float(empirical_variance),
        "prior_expected_sigma_sq": float(beta_0 / (alpha_0 - 1.0)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="BOCD live-pause NIG prior calibration "
        "(P1-BOCD-LIVE-PRIOR-CALIBRATION-{H062,H055}-V3)"
    )
    parser.add_argument(
        "--h062-sidecar", type=Path, default=None,
        help="Path to H062 v2 sidecar (e.g., artifacts/runs/H062/<run_id>/sidecar.json)",
    )
    parser.add_argument(
        "--h055-sweep-sidecar", type=Path, default=None,
        help="Path to H055 v2 sweep_sidecar (e.g., artifacts/runs/H055/v2_sweep_<ts>/sweep_sidecar.json)",
    )
    parser.add_argument(
        "--out", type=Path, default=Path("config/bocd_live_priors.yaml"),
        help="Output YAML path (default: config/bocd_live_priors.yaml)",
    )
    parser.add_argument(
        "--kappa-0", type=float, default=_KAPPA_0_DEFAULT,
        help="NIG kappa_0 (default 1.0; weak prior on mu)",
    )
    parser.add_argument(
        "--alpha-0", type=float, default=_ALPHA_0_DEFAULT,
        help="NIG alpha_0 (default 3.0; smallest alpha_0 with finite Var[sigma^2])",
    )
    parser.add_argument(
        "--allow-degenerate-fallback", action="store_true",
        help="Allow emission of priors derived from the mppm_oos/252 fallback "
        "(per R1 audit F-1-1: each fold contributes n_oos_sessions COPIES of "
        "a single scalar → variance estimator is BETWEEN-fold, not WITHIN-"
        "session). Default: refuse fallback; require per_session_logret arrays "
        "in sidecar (P1-PHASE-O13-SIDECAR-PER-SESSION-LOGRET-PERSIST). "
        "Operator must explicitly acknowledge the degenerate-fallback "
        "limitation before emitting calibration YAML.",
    )
    parser.add_argument(
        "--calibration-window", type=str, default=None,
        help="Calibration window in 'YYYY-MM-DD:YYYY-MM-DD' format (per R1 "
        "F-1-3 fix: pre-OOS holdout required to prevent within-OOS leak). "
        "If omitted, YAML records 'calibration_window: unknown' as audit-"
        "discipline marker (operator must populate before v3 launch).",
    )
    args = parser.parse_args(argv)

    # Identity-hygiene + provenance helpers (defined before any use site).
    repo_root = Path(__file__).resolve().parent.parent

    def _project_relative(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(repo_root)).replace("\\", "/")
        except ValueError:
            return str(p)

    # R1 audit F-1-4 fix: ReproLog provenance fields embedded in YAML.
    def _git_head() -> str:
        import subprocess
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo_root), stderr=subprocess.DEVNULL,
            ).decode("utf-8").strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            return "unknown"

    output: dict[str, Any] = {
        "schema_version": "bocd_live_priors_v2",  # bumped per R1 F-1-7
        "ndoc": (
            "BOCD live-pause NIG prior calibration per Adams-MacKay 2007 "
            "arXiv:0710.3742 + Murphy 2007 §inverse-gamma. "
            "P1-BOCD-LIVE-PRIOR-CALIBRATION-H062-V3 + -H055-V3."
        ),
        "calibration_params": {
            "kappa_0": args.kappa_0,
            "alpha_0": args.alpha_0,
            "n_min_observations": _N_MIN_OBSERVATIONS,
        },
        "provenance": {
            "git_head": _git_head(),
            "calibration_window": (
                args.calibration_window
                if args.calibration_window is not None
                else "unknown (operator MUST populate before v3 launch per "
                "R1 audit F-1-3 within-OOS-leak concern)"
            ),
            "allow_degenerate_fallback_flag": bool(args.allow_degenerate_fallback),
        },
        "hypotheses": {},
    }

    if args.h062_sidecar is not None:
        h062_path = args.h062_sidecar.resolve()
        if not h062_path.exists():
            print(f"ERROR: H062 sidecar not found at {_project_relative(h062_path)}", file=sys.stderr)
            return 1
        h062_data = json.loads(h062_path.read_text(encoding="utf-8"))
        h062_logrets, h062_used_fallback = _extract_h062_per_session_logrets(h062_data)
        if h062_used_fallback and not args.allow_degenerate_fallback:
            print(
                "ERROR: H062 sidecar lacks per_session_logret arrays; fell back "
                "to mppm_oos/252 proxy which produces a DEGENERATE variance "
                "estimator (each fold contributes n_oos_sessions copies of a "
                "single scalar → variance is BETWEEN-fold not WITHIN-session). "
                "Refusing to emit priors. Either persist per_session_logret in "
                "sidecar (P1-PHASE-O13-SIDECAR-PER-SESSION-LOGRET-PERSIST) and "
                "re-run, OR pass --allow-degenerate-fallback to acknowledge "
                "the limitation and emit degenerate priors (NOT recommended "
                "for production v3 launch).",
                file=sys.stderr,
            )
            return 2
        if h062_logrets:
            try:
                h062_priors = calibrate_nig_priors_from_logrets(
                    h062_logrets, kappa_0=args.kappa_0, alpha_0=args.alpha_0,
                )
                output["hypotheses"]["H062"] = {
                    "source_sidecar": _project_relative(h062_path),
                    "source_run_id": h062_data.get("run_id", "unknown"),
                    "substrate_dataset_checksum": (
                        h062_data.get("dataset_checksums", {}).get(
                            "vendor_legacy_1min_roll_adjusted", "unknown"
                        )
                    ),
                    "used_degenerate_fallback": h062_used_fallback,
                    **h062_priors,
                }
                print(
                    f"H062: calibrated NIG priors from n={h062_priors['n_observations']} "
                    f"per-session log-returns "
                    f"(mu_0={h062_priors['mu_0']:.6f}, "
                    f"beta_0={h062_priors['beta_0']:.6e}, "
                    f"prior_E[sigma2]={h062_priors['prior_expected_sigma_sq']:.6e})"
                )
            except ValueError as exc:
                print(f"ERROR: H062 calibration failed: {exc}", file=sys.stderr)
                return 1
        else:
            print(
                "WARNING: H062 sidecar has no per_session_logret data; "
                "calibration skipped",
                file=sys.stderr,
            )

    if args.h055_sweep_sidecar is not None:
        h055_path = args.h055_sweep_sidecar.resolve()
        if not h055_path.exists():
            print(f"ERROR: H055 sweep_sidecar not found at {_project_relative(h055_path)}", file=sys.stderr)
            return 1
        h055_data = json.loads(h055_path.read_text(encoding="utf-8"))
        h055_logrets, h055_used_fallback = _extract_h055_per_session_logrets(h055_data)
        if h055_used_fallback and not args.allow_degenerate_fallback:
            print(
                "ERROR: H055 sweep_sidecar lacks per_session_log_returns; "
                "fell back to mppm/252 proxy. Refusing to emit priors per R1 "
                "audit F-1-1 (degenerate variance estimator). Pass "
                "--allow-degenerate-fallback to override.",
                file=sys.stderr,
            )
            return 2
        if h055_logrets:
            try:
                h055_priors = calibrate_nig_priors_from_logrets(
                    h055_logrets, kappa_0=args.kappa_0, alpha_0=args.alpha_0,
                )
                output["hypotheses"]["H055"] = {
                    "source_sidecar": _project_relative(h055_path),
                    "source_run_id": h055_data.get("run_id", "unknown"),
                    "substrate_dataset_checksum": (
                        h055_data.get("dataset_checksums", {}).get(
                            "vendor_legacy_1min_roll_adjusted", "unknown"
                        )
                    ),
                    "used_degenerate_fallback": h055_used_fallback,
                    **h055_priors,
                }
                print(
                    f"H055: calibrated NIG priors from n={h055_priors['n_observations']} "
                    f"per-session log-returns "
                    f"(mu_0={h055_priors['mu_0']:.6f}, "
                    f"beta_0={h055_priors['beta_0']:.6e}, "
                    f"prior_E[sigma2]={h055_priors['prior_expected_sigma_sq']:.6e})"
                )
            except ValueError as exc:
                print(f"ERROR: H055 calibration failed: {exc}", file=sys.stderr)
                return 1
        else:
            print(
                "WARNING: H055 sweep_sidecar has no per_session_log_returns; "
                "calibration skipped",
                file=sys.stderr,
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        yaml.safe_dump(output, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"Wrote calibrated priors to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
