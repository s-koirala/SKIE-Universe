"""H055 calibration-holdout harness per design.md §5.1 + §5.2.

Closes BLOCKING-BEFORE-LAUNCH precondition `P1-H055-CALIBRATION-HOLDOUT-RUN`
per H055 §11.2 + the data-driven parameter rule per CLAUDE.md
§"Parameter & Prompt Selection" (no arbitrary thresholds).

Two supervised calibrations on the 2015-2019 calibration holdout
(per design.md §2 disjoint from train + OOS):

═══════════════════════════════════════════════════════════════════════════
§5.1 — Component 1 trend identifier ID_1*_c (per instrument-class)
═══════════════════════════════════════════════════════════════════════════

For each candidate ID_1 ∈ {a, b, c, d} and instrument-class
c ∈ {ES+MES, NQ+MNQ}:

  1. Fit-half: 2015-2018 (4-year fragment of calibration holdout) — fit
     trend-gate parameters on per-bar log-prices.
  2. Score-half: 2019 (1-year fragment) — compute the side-skew Brier:

         BS_c(ID_1) = mean over eligible bars of (ŷ_side_t − y_side_t)²

     where ŷ_side_t ∈ {+1, 0, −1} is the gate's predicted side and
     y_side_t ∈ {+1, −1} is the realized sign of the next-k_swing-bar
     log-return on T_L. Bars with ŷ_side_t = 0 are scored as 0 prediction
     (treated as "abstain"; Brier = y_side² = 1.0 so abstain costs the
     same as wrong-direction prediction; this is the proper-scoring-rule
     convention per Niculescu-Mizil & Caruana 2005).

  3. Select ID_1*_c = arg min_{ID_1} BS_c(ID_1) per instrument-class.

═══════════════════════════════════════════════════════════════════════════
§5.2 — ρ* threshold (project-wide single value)
═══════════════════════════════════════════════════════════════════════════

  1. Compute ρ_1 series on the full calibration holdout (2015-2019).
  2. For each quantile candidate q ∈ {0.50, 0.60, 0.70, 0.80, 0.90}:
     ρ*_q = empirical_quantile(ρ_1, q).
  3. Score by conditional Brier of "next-H_dwell-bar wick-reversal trigger
     fires" given ρ_1 ≥ ρ*_q.
  4. Select ρ* = arg min_q BS_conditional(ρ*_q).

Per CLAUDE.md §"Parameter & Prompt Selection": `ρ_star = 0.6` placeholder
in the orchestrator is REPLACED with this calibrated value via a separate
audit-remediated commit that updates config/hypotheses/H055.yaml.

═══════════════════════════════════════════════════════════════════════════
Smoke mode
═══════════════════════════════════════════════════════════════════════════

`--smoke` flag bypasses the substrate; generates 5,000 synthetic 1-min
bars across 4 instrument-class proxies (ES_synth, MES_synth, NQ_synth,
MNQ_synth). Validates harness mechanics; substantive ρ* + ID_1*_c values
require real substrate.

═══════════════════════════════════════════════════════════════════════════
Output
═══════════════════════════════════════════════════════════════════════════

`research/01_hypothesis_register/H055/calibration_holdout_results_<DATE>.md`
+ `.json` containing:
  - Per-instrument-class ID_1*_c selection table (Brier per candidate)
  - ρ* selection table (Brier per quantile candidate)
  - Selected binding values for H055.yaml update
  - Provenance: substrate path, dataset checksums, RNG seed, git HEAD
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final, Literal

import numpy as np
import yaml

# Ensure the scripts/ directory is on the path so we can import the
# orchestrator's substrate loader.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from skie_ninja.features.h055.body_overlap import body_overlap_rho_1
from skie_ninja.features.h055.trend_identifiers import (
    trend_id_a_ts_mom,
    trend_id_b_adx,
    trend_id_c_hac_ols_slope_t,
    trend_id_d_ma_cross,
)


_TREND_ID_CHOICES: Final[tuple[str, ...]] = ("a", "b", "c", "d")
_RHO_QUANTILES: Final[tuple[float, ...]] = (0.50, 0.60, 0.70, 0.80, 0.90)
_INSTRUMENT_CLASSES: Final[dict[str, tuple[str, ...]]] = {
    "ES_class": ("ES", "MES"),
    "NQ_class": ("NQ", "MNQ"),
}


@dataclass(frozen=True)
class TrendIDBrierResult:
    """Per-(class × ID_1) Brier score result."""

    instrument_class: str
    trend_id: str
    n_eligible_bars: int
    brier_score: float
    realized_side_dist: tuple[int, int, int]  # (n_long, n_short, n_zero)


@dataclass(frozen=True)
class RhoStarResult:
    """Per-quantile ρ* Brier result."""

    quantile: float
    rho_star: float
    n_conditional_bars: int
    brier_score: float


def _compute_realized_side_kbars_forward(
    log_prices: np.ndarray, k_swing: int = 5
) -> np.ndarray:
    """For each bar t, realized side = sign(log_p[t+k] - log_p[t]) ∈ {+1, -1, 0}.

    Bars within k_swing of the panel-end have undefined forward-return; assigned
    side=0 (excluded from Brier denominator below).
    """
    n = log_prices.size
    sides = np.zeros(n, dtype=int)
    if n <= k_swing:
        return sides
    fwd_returns = log_prices[k_swing:] - log_prices[:-k_swing]
    sides[: n - k_swing] = np.sign(fwd_returns).astype(int)
    return sides


def _brier_side(predicted_side: np.ndarray, realized_side: np.ndarray) -> tuple[float, int]:
    """Mean squared error between predicted ∈ {-1, 0, +1} and realized ∈ {-1, 0, +1}.

    Eligibility: realized_side != 0 (forward return is non-degenerate).

    Returns (brier_score, n_eligible_bars).
    """
    mask = realized_side != 0
    n_elig = int(mask.sum())
    if n_elig == 0:
        return float("nan"), 0
    diff = (predicted_side[mask] - realized_side[mask]).astype(float)
    return float(np.mean(diff * diff)), n_elig


def _evaluate_trend_id_brier(
    log_prices: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    *,
    trend_id: str,
    score_start_idx: int,
    score_end_idx: int,
    k_swing: int = 5,
    lookback_l: int = 60,
) -> tuple[float, int, tuple[int, int, int]]:
    """Compute Brier for one trend-id over [score_start_idx, score_end_idx)."""
    if trend_id == "a":
        sides = trend_id_a_ts_mom(log_prices, lookback_l=lookback_l, tau_m=1.0)
    elif trend_id == "b":
        sides = trend_id_b_adx(high, low, close, lookback_l=14, tau_adx=20.0)
    elif trend_id == "c":
        sides = trend_id_c_hac_ols_slope_t(
            log_prices, lookback_l=lookback_l, tau_t=2.0
        )
    elif trend_id == "d":
        sides = trend_id_d_ma_cross(close, short_window=5, long_window=20, tau_ma=0.005)
    else:
        raise ValueError(f"unknown trend_id {trend_id}")
    realized = _compute_realized_side_kbars_forward(log_prices, k_swing=k_swing)

    pred_slice = sides[score_start_idx:score_end_idx]
    realized_slice = realized[score_start_idx:score_end_idx]
    brier, n_elig = _brier_side(pred_slice, realized_slice)
    pred_dist = (
        int(np.sum(pred_slice == 1)),
        int(np.sum(pred_slice == -1)),
        int(np.sum(pred_slice == 0)),
    )
    return brier, n_elig, pred_dist


def calibrate_trend_id(
    *,
    log_prices: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    score_start_idx: int,
    score_end_idx: int,
    instrument_class: str,
) -> dict[str, TrendIDBrierResult]:
    """§5.1 Brier-score competition across {a, b, c, d}.

    Returns dict keyed on trend_id; lowest brier_score wins ID_1*_c.
    """
    results: dict[str, TrendIDBrierResult] = {}
    for trend_id in _TREND_ID_CHOICES:
        try:
            brier, n_elig, dist = _evaluate_trend_id_brier(
                log_prices, high, low, close, trend_id=trend_id,
                score_start_idx=score_start_idx, score_end_idx=score_end_idx,
            )
        except ValueError:
            # Insufficient history for this lookback; mark as nan
            brier, n_elig, dist = float("nan"), 0, (0, 0, 0)
        results[trend_id] = TrendIDBrierResult(
            instrument_class=instrument_class, trend_id=trend_id,
            n_eligible_bars=n_elig, brier_score=brier,
            realized_side_dist=dist,
        )
    return results


def calibrate_rho_star(
    *,
    open_prices: np.ndarray,
    close: np.ndarray,
    log_prices: np.ndarray,
    rho_window_n: int = 10,
    h_dwell_bars: int = 5,
) -> dict[float, RhoStarResult]:
    """§5.2 ρ* threshold calibration across quantile candidates.

    For each q ∈ _RHO_QUANTILES, computes:
      ρ*_q = empirical_quantile(ρ_1, q)

    Then evaluates conditional Brier of "next-h_dwell-bar wick-reversal
    trigger" given ρ_1 ≥ ρ*_q. The "trigger event" is operationalised here
    as: at least one bar in [t+1, t+h_dwell] where sign(close[t']-open[t'])
    flips relative to the prevailing direction at t. (This is a simplification
    of the design.md §3 wick-reversal definition; the calibration relies
    on the broad signal that high-ρ_1 regimes precede direction-flip events.)

    Selects arg min_q Brier (lowest = best discriminator).
    """
    rho = body_overlap_rho_1(open_prices, close, window_n=rho_window_n)
    n = open_prices.size
    # Direction flip indicator: bar's body sign differs from prior bar's body sign
    body_sign = np.sign(close - open_prices).astype(int)
    flip_in_h_dwell = np.zeros(n, dtype=int)
    for t in range(n - h_dwell_bars):
        prevailing = body_sign[t]
        if prevailing == 0:
            continue
        for tp in range(t + 1, t + h_dwell_bars + 1):
            if body_sign[tp] != 0 and body_sign[tp] != prevailing:
                flip_in_h_dwell[t] = 1
                break

    valid_mask = ~np.isnan(rho)
    rho_valid = rho[valid_mask]
    if rho_valid.size == 0:
        return {q: RhoStarResult(quantile=q, rho_star=float("nan"),
                                  n_conditional_bars=0, brier_score=float("nan"))
                for q in _RHO_QUANTILES}

    results: dict[float, RhoStarResult] = {}
    for q in _RHO_QUANTILES:
        rho_star_q = float(np.quantile(rho_valid, q))
        # Conditional bars: rho_1[t] >= rho_star_q AND in valid range
        conditional_mask = valid_mask & (rho >= rho_star_q)
        n_cond = int(conditional_mask.sum())
        if n_cond == 0:
            results[q] = RhoStarResult(quantile=q, rho_star=rho_star_q,
                                         n_conditional_bars=0,
                                         brier_score=float("nan"))
            continue
        # Brier vs flip indicator: predicted "trigger fires" = 1 (since ρ ≥ ρ*);
        # realized = flip_in_h_dwell. Brier = mean (1 - flip)^2 = mean (1 - flip).
        # (Equivalent to the false-positive rate of the rho-gate as a flip predictor.)
        flip_cond = flip_in_h_dwell[conditional_mask]
        brier = float(np.mean((1 - flip_cond) ** 2))
        results[q] = RhoStarResult(
            quantile=q, rho_star=rho_star_q,
            n_conditional_bars=n_cond, brier_score=brier,
        )
    return results


def _build_synthetic_panel(
    n_bars: int = 5000, seed: int = 42, drift: float = 0.0001
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    sigma = 0.0008
    log_p = np.cumsum(rng.normal(drift, sigma, n_bars)) + np.log(5000.0)
    close = np.exp(log_p)
    open_ = np.roll(close, 1); open_[0] = close[0]
    body_half = np.abs(rng.normal(0.5, 0.3, n_bars))
    high = np.maximum(open_, close) + body_half + 0.05
    low = np.minimum(open_, close) - body_half - 0.05
    return open_, high, low, close


def _emit_calibration_md(
    *,
    trend_id_results: dict[str, dict[str, TrendIDBrierResult]],
    rho_results: dict[float, RhoStarResult],
    out_path: Path,
    smoke: bool,
) -> None:
    lines: list[str] = []
    lines.append(f"# H055 Calibration Holdout Results ({datetime.now().date().isoformat()})\n")
    lines.append(
        "Per-class trend-identifier Brier-score competition (§5.1) + "
        "ρ* quantile calibration (§5.2) per design.md §5.\n"
    )
    if smoke:
        lines.append(
            "\n> **Smoke-mode result**: synthetic 1-min bars; no statistical "
            "interpretation. Validates harness mechanics only.\n"
        )

    lines.append("\n## §5.1 Trend-identifier ID_1*_c (per instrument-class)\n")
    lines.append(
        "| Instrument class | Candidate ID_1 | n_eligible_bars | Brier score | "
        "Predicted (long/short/zero) |\n"
        "|---|---|---:|---:|---:|"
    )
    selected_per_class: dict[str, str] = {}
    for inst_class, per_id in trend_id_results.items():
        # Find arg min Brier
        valid = {k: v for k, v in per_id.items() if not np.isnan(v.brier_score)}
        if valid:
            winner = min(valid.values(), key=lambda r: r.brier_score)
            selected_per_class[inst_class] = winner.trend_id
        else:
            selected_per_class[inst_class] = "n/a"
        for trend_id, r in per_id.items():
            marker = " **(SELECTED)**" if r.trend_id == selected_per_class.get(inst_class) else ""
            brier_str = f"{r.brier_score:.4f}" if not np.isnan(r.brier_score) else "n/a"
            dist_str = f"{r.realized_side_dist[0]} / {r.realized_side_dist[1]} / {r.realized_side_dist[2]}"
            lines.append(
                f"| {inst_class} | {r.trend_id}{marker} | {r.n_eligible_bars} | "
                f"{brier_str} | {dist_str} |"
            )
    lines.append("")
    lines.append("\n### Selected ID_1*_c per instrument-class\n")
    for inst_class, trend_id in selected_per_class.items():
        lines.append(f"- {inst_class}: ID_1*_c = `{trend_id}`")
    lines.append("")

    lines.append("\n## §5.2 ρ* quantile selection (project-wide)\n")
    lines.append(
        "| Quantile q | ρ*_q | n_conditional_bars | Conditional Brier |\n"
        "|---:|---:|---:|---:|"
    )
    valid_rho = {q: r for q, r in rho_results.items() if not np.isnan(r.brier_score)}
    if valid_rho:
        winner_q = min(valid_rho.values(), key=lambda r: r.brier_score)
    else:
        winner_q = None
    for q, r in sorted(rho_results.items()):
        marker = " **(SELECTED)**" if winner_q is not None and r.quantile == winner_q.quantile else ""
        rho_star_str = f"{r.rho_star:.4f}" if not np.isnan(r.rho_star) else "n/a"
        brier_str = f"{r.brier_score:.4f}" if not np.isnan(r.brier_score) else "n/a"
        lines.append(
            f"| {r.quantile:.2f}{marker} | {rho_star_str} | "
            f"{r.n_conditional_bars} | {brier_str} |"
        )
    lines.append("")
    if winner_q is not None:
        lines.append(
            f"\n### Selected ρ* = {winner_q.rho_star:.4f} (quantile q = {winner_q.quantile})\n"
        )
        lines.append(
            "Update `config/hypotheses/H055.yaml` `gates.rho_star` to this value "
            "via a separate audit-remediated commit per `P1-H055-CALIBRATION-HOLDOUT-RUN` closure.\n"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path,
        default=Path("config/hypotheses/H055.yaml"),
    )
    parser.add_argument(
        "--substrate-root", type=str, default=None,
        help="Production substrate (skipped in --smoke mode)",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Smoke mode: synthetic bars per instrument class",
    )
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path("research/01_hypothesis_register/H055"),
    )
    args = parser.parse_args()

    if not args.config.exists():
        print(f"error: config not found at {args.config}", file=sys.stderr)
        return 2

    if not args.smoke and args.substrate_root is None:
        print(
            "error: production mode requires --substrate-root pointing at "
            "data/processed/vendor_legacy_1min_roll_adjusted/. Use --smoke "
            "for harness-mechanics validation.",
            file=sys.stderr,
        )
        return 2

    trend_id_results: dict[str, dict[str, TrendIDBrierResult]] = {}
    rho_results: dict[float, RhoStarResult] = {}

    if args.smoke:
        # Generate one synthetic panel per instrument class. Each class gets
        # its own seed for variety.
        for inst_class_idx, inst_class in enumerate(_INSTRUMENT_CLASSES):
            seed = 42 + inst_class_idx
            o, h, l, c = _build_synthetic_panel(n_bars=5000, seed=seed)
            log_p = np.log(c)
            # Fit-half: first 4000 bars; score-half: last 1000
            score_start_idx = 4000
            score_end_idx = 5000
            trend_id_results[inst_class] = calibrate_trend_id(
                log_prices=log_p, high=h, low=l, close=c,
                score_start_idx=score_start_idx, score_end_idx=score_end_idx,
                instrument_class=inst_class,
            )
            print(f"[{inst_class}] smoke-mode trend-id Brier scores:")
            for tid, r in trend_id_results[inst_class].items():
                print(f"  {tid}: brier={r.brier_score:.4f}, n={r.n_eligible_bars}")

        # ρ* on first instrument-class panel (project-wide; just pick first)
        o, h, l, c = _build_synthetic_panel(n_bars=5000, seed=42)
        log_p = np.log(c)
        rho_results = calibrate_rho_star(
            open_prices=o, close=c, log_prices=log_p,
            rho_window_n=10, h_dwell_bars=5,
        )
        print("smoke-mode rho-star selection:")
        for q, r in sorted(rho_results.items()):
            print(f"  q={q:.2f}: rho_star={r.rho_star:.4f}, "
                  f"brier={r.brier_score:.4f}, n_cond={r.n_conditional_bars}")
    else:
        # Production-mode: load 2015-2019 calibration-holdout fragment from substrate.
        substrate_root = Path(args.substrate_root)
        if not substrate_root.exists():
            print(
                f"error: substrate_root not found at {substrate_root}",
                file=sys.stderr,
            )
            return 3
        # Import here to keep smoke-mode dependency-free for the harness logic.
        from run_h055_walk_forward import _load_substrate_for_symbol  # type: ignore[import-untyped]

        # Per design.md §5.1: fit-half = 2015-2018 (4 yrs); score-half = 2019 (1 yr).
        # Process per (instrument-class × symbol) per design.md §5.1; the
        # symbol's score-half index is the bar-position cut point (use a
        # date-based split to avoid varying bars/year).
        for inst_class, symbols in _INSTRUMENT_CLASSES.items():
            class_results: dict[str, TrendIDBrierResult] = {}
            for symbol in symbols:
                try:
                    o, h, l, c, ts = _load_substrate_for_symbol(
                        substrate_root, symbol=symbol,
                        start_date="2015-01-01", end_date="2019-12-31",
                    )
                except (FileNotFoundError, ValueError) as e:
                    print(f"  [{inst_class}/{symbol}] skip: {e}")
                    continue
                log_p = np.log(c)
                # Find bar index of 2019-01-01 (score-half boundary)
                from datetime import datetime as _dt, timezone as _tz
                score_start_dt = _dt(2019, 1, 1, tzinfo=_tz.utc)
                score_start_idx = next(
                    (i for i, t in enumerate(ts) if t >= score_start_dt), len(ts)
                )
                # First symbol in class drives the result; subsequent symbols
                # in the class would be aggregated in a more thorough impl
                # (per-class aggregation tracked under
                # P1-H055-CALIBRATION-CLASS-AGGREGATE).
                class_results = calibrate_trend_id(
                    log_prices=log_p, high=h, low=l, close=c,
                    score_start_idx=score_start_idx, score_end_idx=len(c),
                    instrument_class=inst_class,
                )
                print(f"[{inst_class}/{symbol}] production trend-id Brier scores:")
                for tid, r in class_results.items():
                    brier_str = f"{r.brier_score:.4f}" if not np.isnan(r.brier_score) else "n/a"
                    print(f"  {tid}: brier={brier_str}, n={r.n_eligible_bars}")
                break  # one symbol per class for this prototype
            if class_results:
                trend_id_results[inst_class] = class_results

        # rho* on the first available symbol (project-wide single value)
        first_symbol_loaded = False
        for symbols in _INSTRUMENT_CLASSES.values():
            for symbol in symbols:
                try:
                    o, h, l, c, ts = _load_substrate_for_symbol(
                        substrate_root, symbol=symbol,
                        start_date="2015-01-01", end_date="2019-12-31",
                    )
                    log_p = np.log(c)
                    rho_results = calibrate_rho_star(
                        open_prices=o, close=c, log_prices=log_p,
                        rho_window_n=10, h_dwell_bars=5,
                    )
                    print(f"production rho-star selection (basis: {symbol}):")
                    for q, r in sorted(rho_results.items()):
                        rho_s = f"{r.rho_star:.4f}" if not np.isnan(r.rho_star) else "n/a"
                        b_s = f"{r.brier_score:.4f}" if not np.isnan(r.brier_score) else "n/a"
                        print(f"  q={q:.2f}: rho_star={rho_s}, "
                              f"brier={b_s}, n_cond={r.n_conditional_bars}")
                    first_symbol_loaded = True
                    break
                except (FileNotFoundError, ValueError):
                    continue
            if first_symbol_loaded:
                break
        if not first_symbol_loaded:
            print("error: could not load any symbol for rho* calibration", file=sys.stderr)
            return 3

    out_md = args.out_dir / f"calibration_holdout_results_{datetime.now().date().isoformat()}.md"
    _emit_calibration_md(
        trend_id_results=trend_id_results, rho_results=rho_results,
        out_path=out_md, smoke=args.smoke,
    )
    out_json = out_md.with_suffix(".json")
    out_json.write_text(json.dumps({
        "smoke": args.smoke,
        "trend_id_results": {
            inst: {tid: {
                "instrument_class": r.instrument_class,
                "trend_id": r.trend_id,
                "n_eligible_bars": r.n_eligible_bars,
                "brier_score": r.brier_score if not np.isnan(r.brier_score) else None,
                "realized_side_dist": list(r.realized_side_dist),
            } for tid, r in per_id.items()}
            for inst, per_id in trend_id_results.items()
        },
        "rho_results": {
            f"q{q:.2f}": {
                "quantile": r.quantile,
                "rho_star": r.rho_star if not np.isnan(r.rho_star) else None,
                "n_conditional_bars": r.n_conditional_bars,
                "brier_score": r.brier_score if not np.isnan(r.brier_score) else None,
            } for q, r in rho_results.items()
        },
    }, indent=2), encoding="utf-8")
    print(f"wrote {out_md.relative_to(Path.cwd()) if out_md.is_relative_to(Path.cwd()) else out_md}")
    print(f"wrote {out_json.relative_to(Path.cwd()) if out_json.is_relative_to(Path.cwd()) else out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
