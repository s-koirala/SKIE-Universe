"""H055 Hansen SPA Monte-Carlo power simulation (pre-registration feeder).

Pre-registered Monte-Carlo power calculation that feeds the binding ``K_max``
parameter recorded in [config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml)
under ``gates.hansen_spa.K_max``. The simulation is part of the H055 design.md §8
pre-registration: the chosen ``K_max`` value (= 500) is the smallest K for which
the central cell of the power table (ω = 0.45) attains power ≥ ``gates.power.target``
( = 0.80) at α = ``gates.hansen_spa.alpha`` ( = 0.05) for the pre-registered
target effect size of 0.30 annualized SR.

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
   b. Inject the target effect_size as an additive shift on a fraction ω of
      the n_strategies candidate strategies (per Hansen 2005 §3 simulation design).
   c. Run :func:`~skie_ninja.inference.multipletest.hansen_spa.hansen_spa_test`
      at α = config-pinned threshold; record reject / fail-to-reject.
4. Power(n_strategies, ω, effect_size) = Pr[reject H_0 of "no candidate beats benchmark"]
   averaged across replicates.
5. Output: 4 × 3 power table indexed by n_strategies × ω at the pre-registered target
   effect_size = 0.30 annualized SR.
6. Decision: choose the smallest K_max such that power(K_max, ω = 0.45, 0.30) ≥
   ``gates.power.target`` from the H055 config. The chosen value (500) is then
   recorded as ``gates.hansen_spa.K_max`` in the H055 yaml.

Grid (frozen at design-time per [config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml))
---------------------------------------------------------------------------

- n_strategies (Hansen 2005 §3 K) ∈ {100, 250, 500, 1000}
- ω ∈ {0.30, 0.45, 0.60} (fraction of injected candidate strategies)
- effect_size ∈ {0.30} annualized SR (the pre-reg target only; sensitivity
  outside this point is an out-of-scope follow-up under
  ``P1-H055-SPA-POWER-EFFECT-SIZE-SENSITIVITY``)

Citations
---------

- Hansen 2005 *J Bus Econ Stat* 23(4):365-380 (SPA test + §3 simulation design)
- Hsu, Hsu & Kuan 2010 *J Empir Finance* 17(3):471-484 (size + power Monte-Carlo
  for SPA in financial-strategy-selection settings)
- Politis & Romano 1994 *J Am Stat Assoc* 89(428):1303-1313, DOI
  10.1080/01621459.1994.10476870 (stationary bootstrap)
- Politis & White 2004 *Econom Rev* 23(1):53-70 (block-length selection)
- Politis, Patton & White 2009 *Econom Rev* 28(4):372-375 (PW2004 correction)

Reproducibility
---------------

All numeric thresholds (alpha, n_bootstrap, block_length policy, n_strategies grid,
ω grid, target effect size, power target, rng_seed) are drawn from
[config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml) at run time —
NO magic numbers in this script.

Body pending follow-up ``P1-H055-POWER-SIMULATION-EXECUTE`` (analysis machine
implementation; raises ``NotImplementedError`` until then).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def simulate_power(
    n_strategies: int,
    omega: float,
    effect_size: float,
    n_replicates: int,
    rng_seed: int,
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
    n_replicates
        Number of Monte-Carlo replicates for the power estimate.
    rng_seed
        Deterministic RNG seed (config-pinned per H055.yaml random_seed).

    Returns
    -------
    dict[str, float]
        Keys: ``power`` (in [0, 1]), ``power_mc_se`` (Monte-Carlo SE under
        the binomial-proportion approximation), ``mean_p_value``, and
        ``mean_block_length`` (PW2004-selected block length averaged across
        replicates).

    Notes
    -----
    The function loads the H055 yaml and the pilot ledger only inside
    :func:`main`; this signature is the unit-of-work that
    ``P1-H055-POWER-SIMULATION-EXECUTE`` will fill in.
    """

    raise NotImplementedError(
        "Body pending follow-up P1-H055-POWER-SIMULATION-EXECUTE; "
        "analysis machine implementation"
    )


def main() -> None:
    """Run the full 4 × 3 n_strategies × ω power grid + emit the binding K_max decision.

    Pipeline
    --------

    1. Parse ``--config`` (path to
       [config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml)),
       ``--pilot-ledger``, ``--output-dir``.
    2. Load the H055 yaml; extract ``gates.hansen_spa.alpha``,
       ``gates.hansen_spa.n_bootstrap``, ``gates.power.target``, the n_strategies + ω
       grids (constants in this docstring; sourced from yaml at execution
       time per ``P1-H055-POWER-SIMULATION-EXECUTE``), and ``random_seed``.
    3. Load the 171-trade pilot ledger, convert to per-session log returns.
    4. Iterate the 4 × 3 grid; per cell call :func:`simulate_power`.
    5. Emit a power table (markdown + JSON) under
       ``research/01_hypothesis_register/H055/power_simulation_2026-05-06/``
       containing per-cell power, Monte-Carlo SE, and the binding K_max
       decision (smallest n_strategies for which central-cell ω = 0.45 power ≥ target).
    6. Append the chosen K_max to the H055 yaml only via a separate audit-
       remediated commit; this script does NOT mutate config files.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to config/hypotheses/H055.yaml (source of all numeric thresholds).",
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
    parser.parse_args()

    raise NotImplementedError(
        "Body pending follow-up P1-H055-POWER-SIMULATION-EXECUTE; "
        "analysis machine implementation"
    )


if __name__ == "__main__":
    main()
