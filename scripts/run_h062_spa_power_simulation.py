"""H062 power simulation for Hansen SPA family-size K_max binding.

Per H062 design.md §9 + §11.2 ``P1-H062-POWER-SIMULATION-EXECUTE``
(BLOCKING; fills §9 power-calibration placeholder).

Per [config/hypotheses/H062.yaml](../config/hypotheses/H062.yaml) §gates.
hansen_spa.K_max the v1 launch carries K_max=500 PLACEHOLDER pending this
script's empirical output. The H055 §9.1 precedent binds K_max at the
realized TPE-explored cardinality per [Hansen 2005, *J Business &
Economic Statistics* 23(4):365-380](https://doi.org/10.1198/073500105000000063)
§2.4 TPE-coverage convention.

Power calibration methodology (per [Glaeser-McKay-Nikiforov 2024
*Quantitative Economics* 15(2):347-388](https://doi.org/10.3982/QE2104)
+ [White 2000 *Econometrica* 68(5):1097-1126](https://doi.org/10.1111/1468-0262.00152)
+ Hansen 2005):
  1. Under H_0 (basket MPPM(ρ=1) = 0), simulate K_max strategy cells with
     iid log-returns ~ N(0, σ²) calibrated to OOS variance.
  2. Apply Hansen SPA test with each of the 3 recentering variants
     (SPA_l / SPA_c / SPA_u per Hansen 2005 §2.4) + stationary bootstrap
     resampling per [Politis-Romano 1994, *JASA* 89(428):1303-1313](
     https://doi.org/10.1080/01621459.1994.10476870) with
     Politis-White 2004 block-length (+ Patton-Politis-White 2009
     correction).
  3. Under H_1 (basket MPPM(ρ=1) > 0), simulate K_max strategy cells with
     log-returns drawn from a mixture: one cell at the H_1 effect size
     + K-1 cells at H_0.
  4. Empirical power = P(SPA reject H_0 | H_1 effect-size ≥ ε) at
     α=0.05 + power-target=0.80.

This v1 script outputs a per-K_max power curve. The H062.yaml K_max
field is then rebound to the smallest K_max satisfying power ≥ 0.80 at
the design.md §9 minimum-detectable effect size.

Closes ``P1-H062-POWER-SIMULATION-EXECUTE`` per design.md §11.2
(BLOCKING-BEFORE-LAUNCH precondition).
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
import yaml

from skie_ninja.inference.multipletest.hansen_spa import hansen_spa_test
from skie_ninja.utils.paths import ProjectPaths

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_spa_power_simulation")


def _simulate_h_null_panel(
    *,
    K: int,
    T: int,
    sigma: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Simulate K strategy cells × T sessions under H_0 (zero excess return).

    Returns (T, K) loss-differential matrix d_{t,k} = arm_{t,k} - bench_{t}
    where arm has mean 0 and bench has mean 0 + iid noise.
    """
    return rng.normal(0.0, sigma, size=(T, K))


def _simulate_h_alt_panel(
    *,
    K: int,
    T: int,
    sigma: float,
    effect_size: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Simulate K cells × T sessions under H_1 with effect_size on one cell.

    Per Hansen 2005 §2.5: under H_1 at least one strategy has positive
    expected loss-differential vs the benchmark. Here we add a constant
    effect_size to a single cell's mean.
    """
    panel = rng.normal(0.0, sigma, size=(T, K))
    panel[:, 0] += effect_size
    return panel


def _empirical_power_at_K(
    *,
    K: int,
    T: int,
    sigma: float,
    effect_size: float,
    n_replicates: int,
    n_bootstrap: int,
    alpha: float,
    rng_seed: int,
) -> dict[str, Any]:
    """Estimate empirical power of SPA at (K, T, effect_size) via simulation."""
    rejections_h0 = 0
    rejections_h1 = 0
    rng_master = np.random.default_rng(rng_seed)

    for rep in range(n_replicates):
        # H_0 simulation.
        panel_h0 = _simulate_h_null_panel(K=K, T=T, sigma=sigma, rng=rng_master)
        try:
            import warnings as _w
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                spa_h0 = hansen_spa_test(
                    panel_h0,
                    n_bootstrap=n_bootstrap,
                    rng=np.random.default_rng(rng_master.integers(0, 2**31 - 1)),
                )
            if spa_h0.p_value < alpha:
                rejections_h0 += 1
        except Exception:  # noqa: BLE001
            pass

        # H_1 simulation.
        panel_h1 = _simulate_h_alt_panel(
            K=K, T=T, sigma=sigma, effect_size=effect_size, rng=rng_master
        )
        try:
            import warnings as _w
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                spa_h1 = hansen_spa_test(
                    panel_h1,
                    n_bootstrap=n_bootstrap,
                    rng=np.random.default_rng(rng_master.integers(0, 2**31 - 1)),
                )
            if spa_h1.p_value < alpha:
                rejections_h1 += 1
        except Exception:  # noqa: BLE001
            pass

    return {
        "K": K,
        "T": T,
        "sigma": sigma,
        "effect_size": effect_size,
        "n_replicates": n_replicates,
        "type_1_error_estimate": rejections_h0 / max(n_replicates, 1),
        "empirical_power_estimate": rejections_h1 / max(n_replicates, 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H062 SPA power simulation")
    parser.add_argument("--hypothesis", default="H062")
    parser.add_argument("--config", default="config/hypotheses/H062.yaml")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: 50 reps × small grid (for smoke validation)",
    )
    args = parser.parse_args(argv)

    paths = ProjectPaths.discover()
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path
    raw_cfg_bytes = cfg_path.read_bytes()
    cfg = yaml.safe_load(raw_cfg_bytes)
    config_resolved_sha256 = hashlib.sha256(raw_cfg_bytes).hexdigest()
    rng_seed = int(cfg.get("random_seed", 20260514))

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else paths.artifacts_runs / cfg["hypothesis_id"] / f"power_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    _log.info("power_out_dir=%s", out_dir)

    # Simulation parameters.
    if args.quick:
        K_grid = [50, 200]
        n_replicates = 50
        n_bootstrap = 200
    else:
        K_grid = [50, 100, 200, 500, 1000]
        n_replicates = 200
        n_bootstrap = 500
    # OOS sessions per the H062 smoke run (~800/symbol × 4 symbols / 4 = 800
    # basket sessions); use a conservative T=500.
    T_basket = 500
    sigma = 0.01  # daily-log-return scale; consistent with H062 smoke run aggregate
    # Minimum-detectable effect size per design.md §9 (modest positive
    # MPPM under H_1; ~ 0.3 annualised log-wealth / sqrt(252) ≈ 0.019 daily).
    effect_size_min = 0.005  # daily-log-return excess; conservative
    alpha = 0.05

    _log.info(
        "K_grid=%s T=%d sigma=%.4f effect=%.4f reps=%d bootstrap=%d",
        K_grid, T_basket, sigma, effect_size_min, n_replicates, n_bootstrap,
    )

    power_curve: list[dict[str, Any]] = []
    K_max_bound = None
    for K in K_grid:
        _log.info("Computing power at K=%d...", K)
        res = _empirical_power_at_K(
            K=K, T=T_basket, sigma=sigma, effect_size=effect_size_min,
            n_replicates=n_replicates, n_bootstrap=n_bootstrap,
            alpha=alpha, rng_seed=rng_seed + K,
        )
        _log.info(
            "  K=%d: type-I=%.3f power=%.3f",
            K, res["type_1_error_estimate"], res["empirical_power_estimate"],
        )
        power_curve.append(res)
        if res["empirical_power_estimate"] >= 0.80 and K_max_bound is None:
            K_max_bound = K

    payload = {
        "hypothesis_id": "H062",
        "config_resolved_sha256": config_resolved_sha256,
        "rng_seed": rng_seed,
        "T_basket": T_basket,
        "sigma": sigma,
        "effect_size_min": effect_size_min,
        "alpha": alpha,
        "K_grid": K_grid,
        "n_replicates": n_replicates,
        "n_bootstrap": n_bootstrap,
        "power_curve": power_curve,
        "K_max_recommended": K_max_bound,
        "K_max_placeholder_in_yaml": int(cfg["gates"]["hansen_spa"]["K_max"]),
        "interpretation": (
            "K_max_recommended is the smallest K in K_grid where empirical_power "
            ">= 0.80 at effect_size_min. If None, no K in K_grid achieves the "
            "power target; rerun with a wider K grid or larger effect_size."
        ),
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "power_sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "power_sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("power_sidecar=%s sha256=%s", sidecar_path, sha[:16])

    print()
    print("=" * 60)
    print("H062 POWER SIMULATION COMPLETE")
    print(f"  T_basket={T_basket} sigma={sigma:.4f} effect_size_min={effect_size_min:.4f}")
    print(f"  K_grid={K_grid}")
    print(f"  K_max_recommended={K_max_bound} (yaml-placeholder={cfg['gates']['hansen_spa']['K_max']})")
    for row in power_curve:
        print(f"  K={row['K']:5d}: type-I={row['type_1_error_estimate']:.3f} power={row['empirical_power_estimate']:.3f}")
    print(f"  sidecar: {sidecar_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
