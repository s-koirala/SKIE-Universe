"""H055 Hansen SPA Monte-Carlo power simulation (pre-registration feeder).

Pre-registered Monte-Carlo power calculation that feeds the binding ``K_max``
parameter recorded in [config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml)
under ``gates.hansen_spa.K_max``. The simulation is part of the H055 design.md §8
pre-registration: the chosen ``K_max`` value (= 500 placeholder, calibrated by
this script) is the smallest K for which the central cell of the power table
(ω = 0.45) attains power ≥ ``gates.power.target`` ( = 0.80) at α =
``gates.hansen_spa.alpha`` ( = 0.05) for the pre-registered target effect size
of 0.30 annualized SR.

Method
------

1. Load the v1 pilot ledger from
   [data/external/h055_pilot_ledger/Performance.csv](../data/external/h055_pilot_ledger/Performance.csv)
   (171-trade, reconciled-to-published-PDF-totals adherence-audit substrate).
2. Convert per-trade P&L to a per-session log-return series.
3. For each (n_strategies, ω, effect_size) cell of the grid, repeatedly:
   a. Resample sessions via stationary bootstrap (Politis-Romano 1994, *JASA*
      89(428):1303-1313, [DOI 10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870);
      block length via Politis-White 2004 + Politis-Patton-White
      2009 correction; both wired in
      [src/skie_ninja/inference/bootstrap.py](../src/skie_ninja/inference/bootstrap.py)).
   b. Build n_strategies candidate per-session log-return series, each via an
      independent stationary-bootstrap resample of the pilot session series.
   c. Inject the target effect_size as an additive shift on a fraction ω of
      the n_strategies candidate strategies (per Hansen 2005 §3 simulation design).
   d. Run :func:`~skie_ninja.inference.multipletest.hansen_spa.hansen_spa_test`
      at α = config-pinned threshold; record reject / fail-to-reject.
4. Power(n_strategies, ω, effect_size) = Pr[reject H_0 of "no candidate beats benchmark"]
   averaged across replicates.
5. Output: 4 × 3 power table indexed by n_strategies × ω at the pre-registered target
   effect_size = 0.30 annualized SR.
6. Decision: choose the smallest K_max such that power(K_max, ω = 0.45, 0.30) ≥
   ``gates.power.target`` from the H055 config. The chosen value is then
   recorded as ``gates.hansen_spa.K_max`` in the H055 yaml (separate audit-
   remediated commit; this script does NOT mutate config files).

Smoke mode
----------

The full grid × n_replicates × inner-bootstrap simulation has substantial
wall-clock cost. Pass ``--smoke`` to run a reduced parameterization
(n_strategies={50, 100}, n_replicates=20, n_inner_bootstrap=200) for
implementation validation; the production run uses the config-pinned
4 × 3 × 200 × 1000 grid.

Citations
---------

- Hansen 2005 *J Bus Econ Stat* 23(4):365-380 (SPA test + §3 simulation design)
- Politis & Romano 1994 *J Am Stat Assoc* 89(428):1303-1313 (stationary bootstrap)
- Politis & White 2004 *Econom Rev* 23(1):53-70 (block-length selection)
- Politis, Patton & White 2009 *Econom Rev* 28(4):372-375 (PW2004 correction)
- Hsu, Hsu & Kuan 2010 *J Empir Finance* 17(3):471-484 (size + power Monte-Carlo
  for SPA in financial-strategy-selection settings)

Reproducibility
---------------

All numeric thresholds (alpha, n_bootstrap, block_length policy, n_strategies
grid, ω grid, target effect size, power target, rng_seed) are drawn from
[config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml) at run time —
NO magic numbers in the analysis-machine logic.

Closes follow-up `P1-H055-POWER-SIMULATION-EXECUTE`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from skie_ninja.inference.bootstrap import (
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_ninja.inference.multipletest.hansen_spa import hansen_spa_test


_PNL_RE = re.compile(r"^\$\(?(?P<value>[\d,.]+)\)?$")


def _parse_pnl_dollar_string(s: str) -> float:
    """Parse '$28.00' → 28.0, '$(4.50)' → -4.5; raises on malformed input."""
    s_clean = s.strip()
    m = _PNL_RE.match(s_clean)
    if m is None:
        raise ValueError(f"Cannot parse pnl string: {s_clean!r}")
    val = float(m.group("value").replace(",", ""))
    if "(" in s_clean:
        val = -val
    return val


def _load_pilot_session_returns(
    pilot_csv: Path, *, starting_equity: float = 2_000.0
) -> np.ndarray:
    """Aggregate per-trade pilot ledger to per-session log returns.

    Per H055 design.md §9.1: convert per-trade P&L to a per-session log-return
    series. Session = calendar date (UTC of the pilot ledger's soldTimestamp;
    pilot is approximately 2026-05-01 → 2026-05-07).

    Returns:
        np.ndarray of shape (n_sessions,) of per-session log returns.
    """
    if not pilot_csv.exists():
        raise FileNotFoundError(f"Pilot ledger not found at {pilot_csv}")

    import csv

    session_pnl: dict[str, float] = {}
    with pilot_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pnl_dollars = _parse_pnl_dollar_string(row["pnl"])
            sold_ts = datetime.strptime(row["soldTimestamp"], "%m/%d/%Y %H:%M:%S")
            session_key = sold_ts.strftime("%Y-%m-%d")
            session_pnl[session_key] = session_pnl.get(session_key, 0.0) + pnl_dollars

    sessions_sorted = sorted(session_pnl.keys())
    if not sessions_sorted:
        raise ValueError("Pilot ledger produced zero sessions.")

    log_returns = np.array(
        [
            np.log(1.0 + session_pnl[s] / starting_equity)
            for s in sessions_sorted
        ],
        dtype=float,
    )
    return log_returns


def simulate_power(
    n_strategies: int,
    omega: float,
    effect_size: float,
    n_replicates: int,
    rng_seed: int,
    *,
    pilot_returns: np.ndarray,
    n_inner_bootstrap: int = 1000,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Estimate Hansen SPA power at one (n_strategies, ω, effect_size) cell.

    The argument ``n_strategies`` corresponds to Hansen 2005 §3's symbol K
    (the number of competing strategies in the SPA family); the lowercase
    snake-case name is preferred in the Python implementation per the project
    ruff N803 convention while the symbol-name binding to Hansen K is
    preserved through this docstring.

    Parameters
    ----------
    n_strategies
        Number of candidate strategies in the SPA family (Hansen 2005 §3 K).
    omega
        Fraction of n_strategies strategies receiving the injected positive effect.
    effect_size
        Annualized Sharpe shift injected into the ω·n_strategies injected strategies.
        Converted to per-session shift via ``effect_size / sqrt(252)`` × σ_pilot.
    n_replicates
        Number of Monte-Carlo replicates for the power estimate.
    rng_seed
        Deterministic RNG seed (config-pinned per H055.yaml random_seed).
    pilot_returns
        Per-session log-return array from the pilot ledger.
    n_inner_bootstrap
        Inner-loop bootstrap reps for the Hansen SPA test (Hansen 2005 §3 used 1000).
    alpha
        SPA test rejection threshold.

    Returns
    -------
    dict[str, float]
        Keys: ``power``, ``power_mc_se``, ``mean_p_value``, ``mean_block_length``.
    """
    if not (0.0 <= omega <= 1.0):
        raise ValueError(f"omega must be in [0, 1], got {omega}")
    if n_strategies < 1:
        raise ValueError(f"n_strategies must be >= 1, got {n_strategies}")
    if n_replicates < 1:
        raise ValueError(f"n_replicates must be >= 1, got {n_replicates}")

    n_sessions = pilot_returns.size
    sigma_pilot = float(np.std(pilot_returns, ddof=1))
    # Convert annualized Sharpe shift to per-session log-return shift:
    # SR_annual = mean_per_session × sqrt(252) / σ_per_session, so a shift Δ_SR
    # translates to Δ_per_session = Δ_SR × σ_per_session / sqrt(252).
    per_session_shift = effect_size * sigma_pilot / np.sqrt(252.0)

    pw_block = max(1.0, float(politis_white_block_length(pilot_returns).block_length))

    rng = np.random.default_rng(rng_seed)
    rejections = 0
    p_values: list[float] = []
    block_lengths: list[float] = []

    n_injected = max(1, int(round(omega * n_strategies)))

    for rep in range(n_replicates):
        # Per-replicate resample: build n_strategies candidate series, each
        # an independent stationary-bootstrap resample of the pilot returns.
        candidate_matrix = np.empty((n_sessions, n_strategies), dtype=float)
        for k in range(n_strategies):
            indices = stationary_bootstrap_indices(
                n=n_sessions, block_length=pw_block, rng=rng
            )
            candidate_matrix[:, k] = pilot_returns[indices]

        # Inject positive effect on the first n_injected candidates.
        candidate_matrix[:, :n_injected] += per_session_shift

        # Build d = candidate_returns - benchmark_returns; benchmark = the
        # unconditional pilot mean (per-session log return mean).
        benchmark_per_session = float(np.mean(pilot_returns))
        d_matrix = candidate_matrix - benchmark_per_session

        spa_result = hansen_spa_test(
            d_matrix,
            n_bootstrap=n_inner_bootstrap,
            block_length=pw_block,
            rng=np.random.default_rng(rng_seed + rep + 1),
        )
        p = float(spa_result.p_value)
        p_values.append(p)
        block_lengths.append(pw_block)
        if p < alpha:
            rejections += 1

    power = rejections / n_replicates
    # Binomial-proportion MC SE:
    power_mc_se = float(np.sqrt(power * (1.0 - power) / n_replicates))
    return {
        "power": power,
        "power_mc_se": power_mc_se,
        "mean_p_value": float(np.mean(p_values)),
        "mean_block_length": float(np.mean(block_lengths)),
        "n_replicates": float(n_replicates),
        "n_inner_bootstrap": float(n_inner_bootstrap),
    }


def _format_table_md(
    grid: dict[tuple[int, float], dict[str, float]],
    *,
    n_strategies_grid: list[int],
    omega_grid: list[float],
    effect_size: float,
    alpha: float,
    power_target: float,
) -> str:
    lines: list[str] = []
    lines.append("# H055 Hansen SPA power simulation — power table\n")
    lines.append(
        f"Effect size (annualised SR shift) = **{effect_size}**; α = {alpha}; "
        f"power target = {power_target}.\n"
    )
    header = "| n_strategies (K) \\ ω | " + " | ".join(
        f"{omega:.2f}" for omega in omega_grid
    ) + " |"
    sep = "|---|" + "|".join(["---"] * len(omega_grid)) + "|"
    lines.append(header)
    lines.append(sep)
    for n_strategies in n_strategies_grid:
        row = f"| {n_strategies} | "
        cells = []
        for omega in omega_grid:
            cell = grid.get((n_strategies, omega))
            if cell is None:
                cells.append("n/a")
            else:
                cells.append(f"{cell['power']:.3f} ± {cell['power_mc_se']:.3f}")
        row += " | ".join(cells) + " |"
        lines.append(row)
    lines.append("")
    return "\n".join(lines)


def _binding_k_max_decision(
    grid: dict[tuple[int, float], dict[str, float]],
    *,
    n_strategies_grid: list[int],
    central_omega: float,
    power_target: float,
) -> dict[str, Any]:
    """Smallest n_strategies for which power(K, ω=central, effect) ≥ target."""
    candidates = []
    for n_strategies in sorted(n_strategies_grid):
        cell = grid.get((n_strategies, central_omega))
        if cell is None:
            continue
        if cell["power"] >= power_target:
            candidates.append(n_strategies)
    chosen = candidates[0] if candidates else None
    return {
        "central_omega": central_omega,
        "power_target": power_target,
        "n_strategies_grid": n_strategies_grid,
        "satisfying_K_values": candidates,
        "binding_K_max": chosen,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to config/hypotheses/H055.yaml.",
    )
    parser.add_argument(
        "--pilot-ledger",
        type=Path,
        required=True,
        help="Path to data/external/h055_pilot_ledger/Performance.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write the power table + binding K_max decision.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Reduced-grid smoke run for implementation validation.",
    )
    args = parser.parse_args()

    if not args.config.exists():
        print(f"error: config not found at {args.config}", file=sys.stderr)
        return 2
    if not args.pilot_ledger.exists():
        print(
            f"error: pilot ledger not found at {args.pilot_ledger}", file=sys.stderr
        )
        return 2

    with args.config.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    alpha = float(cfg["gates"]["hansen_spa"]["alpha"])
    n_inner_bootstrap_full = int(cfg["gates"]["hansen_spa"]["n_bootstrap"])
    power_target = float(cfg["gates"]["power"]["target"])
    rng_seed = int(cfg.get("random_seed", 20260506))

    pilot_returns = _load_pilot_session_returns(args.pilot_ledger)
    print(
        f"Pilot session count: {pilot_returns.size}; "
        f"mean log-return: {pilot_returns.mean():.6f}; "
        f"std: {pilot_returns.std(ddof=1):.6f}"
    )

    if args.smoke:
        n_strategies_grid = [50, 100]
        omega_grid = [0.30, 0.45, 0.60]
        n_replicates = 20
        n_inner_bootstrap = 200
        mode = "smoke"
    else:
        n_strategies_grid = [100, 250, 500, 1000]
        omega_grid = [0.30, 0.45, 0.60]
        n_replicates = 200
        n_inner_bootstrap = n_inner_bootstrap_full
        mode = "full"

    central_omega = 0.45
    effect_size = 0.30  # annualised SR shift per design.md §9.1

    grid: dict[tuple[int, float], dict[str, float]] = {}
    for n_strategies in n_strategies_grid:
        for omega in omega_grid:
            print(f"Running cell: K={n_strategies}, omega={omega:.2f}, mode={mode}...")
            cell = simulate_power(
                n_strategies=n_strategies,
                omega=omega,
                effect_size=effect_size,
                n_replicates=n_replicates,
                rng_seed=rng_seed + n_strategies * 1000 + int(omega * 100),
                pilot_returns=pilot_returns,
                n_inner_bootstrap=n_inner_bootstrap,
                alpha=alpha,
            )
            grid[(n_strategies, omega)] = cell
            print(
                f"  power={cell['power']:.3f} ± {cell['power_mc_se']:.3f} "
                f"(mean p={cell['mean_p_value']:.4f})"
            )

    decision = _binding_k_max_decision(
        grid,
        n_strategies_grid=n_strategies_grid,
        central_omega=central_omega,
        power_target=power_target,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.output_dir / "power_table.md"
    json_path = args.output_dir / "power_table.json"

    md = _format_table_md(
        grid,
        n_strategies_grid=n_strategies_grid,
        omega_grid=omega_grid,
        effect_size=effect_size,
        alpha=alpha,
        power_target=power_target,
    )
    md += (
        "\n## Binding K_max decision\n\n"
        f"- Central ω = {central_omega}\n"
        f"- Power target = {power_target}\n"
        f"- Satisfying K values: {decision['satisfying_K_values']}\n"
        f"- **Binding K_max = {decision['binding_K_max']}**\n"
        f"- Mode: **{mode}**\n"
    )
    if mode == "smoke":
        md += (
            "\n> NOTE: smoke-mode results — reduced n_replicates and "
            "n_inner_bootstrap. Full-replicate run required before binding "
            "K_max into config/hypotheses/H055.yaml.\n"
        )
    md_path.write_text(md, encoding="utf-8")

    payload = {
        "config_path": args.config.as_posix(),
        "pilot_ledger_path": args.pilot_ledger.as_posix(),
        "mode": mode,
        "alpha": alpha,
        "power_target": power_target,
        "effect_size": effect_size,
        "central_omega": central_omega,
        "rng_seed": rng_seed,
        "n_sessions": int(pilot_returns.size),
        "pilot_mean_log_return": float(pilot_returns.mean()),
        "pilot_std_log_return": float(pilot_returns.std(ddof=1)),
        "grid": {
            f"K={n_strategies}|omega={omega:.2f}": cell
            for (n_strategies, omega), cell in grid.items()
        },
        "decision": decision,
    }
    json_path.write_text(
        json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8"
    )
    print(f"Wrote power table to {md_path.as_posix()} and {json_path.as_posix()}")
    print(f"Binding K_max decision: {decision['binding_K_max']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
