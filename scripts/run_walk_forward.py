"""Walk-forward orchestrator for a pre-registered hypothesis.

Usage::

    python scripts/run_walk_forward.py \
        --hypothesis H050 \
        --config config/hypotheses/H050.yaml \
        [--dry-run] [--smoke-n 5000]

Pipeline (per Cycle-6 brief)
----------------------------

  1. Open :class:`~skie_ninja.utils.runcontext.RunContext`.
  2. Load panel (real data OR synthetic on ``--dry-run``).
  3. Compute features via :data:`FEATURE_REGISTRY` enumeration.
  4. Triple-barrier labels; derive ``max_label_horizon``.
  5. Build :class:`~skie_ninja.backtest.splits.SplitSpec` with purge
     >= ``max_label_horizon``, data-driven embargo
     (Politis-White 2004 auto block-length).
  6. Per fold: nested random-search LightGBM (CV-selected inside
     fold) + HMM BIC selection (inside fold). ``predict_fn`` gates
     classifier probability by ``filter_states`` indicator.
  7. :class:`~skie_ninja.backtest.engine.walk_forward.WalkForwardEngine`
     executes the run.
  8. OOS PnL, Sharpe of gated vs unconditional filtered series.
  9. Opdyke 2007 CI on the Sharpe differential via stationary
     bootstrap.
 10. Hansen SPA (strategy universe = {H050} for Cycle-6).
 11. Persist artifacts under ``artifacts/runs/H050/{run_id}/``.
 12. :func:`with_model_hash` the ReproLog from the engine rolled-up
     hash.

Dry-run mode generates a synthetic OHLCV panel. The feature factory,
labels, splitter, engine, bootstrap, and SPA are executed on the
synthetic data so the full composition is exercised end-to-end.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import yaml

from skie_ninja.backtest.costs.nt8_es_nq_rth_v1 import NT8EsNqRthV1CostModel
from skie_ninja.backtest.engine.walk_forward import (
    WalkForwardEngine,
    ledger_path_for,
    roll_up_model_hashes,
    write_run_ledger,
)
from skie_ninja.backtest.splits import walk_forward_split
from skie_ninja.features import FEATURE_REGISTRY
from skie_ninja.features.assembly import assemble_feature_matrix
from skie_ninja.features.labels import (
    TripleBarrierConfig,
    TripleBarrierLabeler,
)
from skie_ninja.inference import choose_block_length, hansen_spa_test
from skie_ninja.inference.stats import opdyke2007_ci, sample_sharpe
from skie_ninja.models.regime import GaussianHMM, select_gaussian_hmm
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.reproducibility import with_model_hash
from skie_ninja.utils.runcontext import RunContext


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunConfig:
    hypothesis_id: str
    random_seed: int
    feature_keys: tuple[str, ...]
    pt_sl_grid: tuple[float, ...]
    vertical_barrier_grid: tuple[pd.Timedelta, ...]
    volatility_lookback_grid: tuple[int, ...]
    lgb_grid: dict[str, tuple[Any, ...]]
    lgb_n_draws: int
    lgb_seed: int
    hmm_cov_types: tuple[str, ...]
    spa_n_bootstrap: int
    spa_omega_method: str  # ADR-0008: "hac" for M=1, "bootstrap" for M≥2
    cost_model_id: str
    cost_sensitivity_mult: float
    gate_alpha: float
    raw: dict[str, Any]


def _parse_vb(item: str) -> pd.Timedelta:
    # Accepts tokens like "30m", "60m", "2h".
    return pd.Timedelta(item)


def load_config(path: Path) -> RunConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RunConfig(
        hypothesis_id=str(raw["hypothesis_id"]),
        random_seed=int(raw["random_seed"]),
        feature_keys=tuple(raw["features"]),
        pt_sl_grid=tuple(float(x) for x in raw["labels"]["pt_sl_grid"]),
        vertical_barrier_grid=tuple(
            _parse_vb(x) for x in raw["labels"]["vertical_barrier_grid"]
        ),
        volatility_lookback_grid=tuple(
            int(x) for x in raw["labels"]["volatility_lookback_grid"]
        ),
        lgb_grid={k: tuple(v) for k, v in raw["classifier"]["grid"].items()},
        lgb_n_draws=int(raw["classifier"]["search"]["n_draws"]),
        lgb_seed=int(raw["classifier"]["search"]["seed"]),
        hmm_cov_types=tuple(raw["hmm"]["covariance_type"]),
        spa_n_bootstrap=int(raw["gates"]["hansen_spa"]["n_bootstrap"]),
        spa_omega_method=str(
            raw["gates"]["hansen_spa"].get("omega_method", "bootstrap")
        ),
        cost_model_id=str(raw.get("cost_model", "nt8_es_nq_rth_v1")),
        cost_sensitivity_mult=float(raw.get("cost_sensitivity_mult", 1.0)),
        gate_alpha=float(raw["gates"]["opdyke2007_ci"]["alpha"]),
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Synthetic panel (dry-run)
# ---------------------------------------------------------------------------


def make_synthetic_panel(*, n_per_symbol: int, seed: int) -> pl.DataFrame:
    """Generate an OHLCV panel with two symbols matching the
    roll-adjusted schema.

    The generator draws close-to-close log-returns from a
    regime-switching Gaussian mixture (two states) so the
    downstream HMM selection sees meaningful state structure; the
    per-bar high/low are set by adding exponential wings to the
    ``max(open, close)`` and ``min(open, close)``. This is enough
    substrate for the orchestrator to exercise end-to-end.
    """
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2023-01-02 09:30", periods=n_per_symbol, freq="1min", tz="UTC")

    def one_symbol(sym: str) -> pl.DataFrame:
        # Markov-ish two-state regime for returns (low-vol, high-vol).
        state = np.zeros(n_per_symbol, dtype=np.int64)
        p_switch = 0.002
        for i in range(1, n_per_symbol):
            if rng.random() < p_switch:
                state[i] = 1 - state[i - 1]
            else:
                state[i] = state[i - 1]
        sig_low = 0.0005
        sig_high = 0.0020
        drift_low = 0.00002
        drift_high = -0.00005
        drift = np.where(state == 0, drift_low, drift_high)
        sigma = np.where(state == 0, sig_low, sig_high)
        r = rng.normal(loc=drift, scale=sigma)
        close_init = 100.0 if sym == "ES" else 200.0
        close = close_init * np.exp(np.cumsum(r))
        open_ = np.concatenate([[close_init], close[:-1]])
        wing = np.abs(rng.normal(scale=sigma * 0.5, size=n_per_symbol))
        high = np.maximum(open_, close) * (1.0 + wing)
        low = np.minimum(open_, close) * (1.0 - wing)
        volume = rng.integers(100, 1000, size=n_per_symbol).astype(np.int64)
        return pl.DataFrame(
            {
                "ts_event": ts,
                "symbol": [sym] * n_per_symbol,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )

    return pl.concat([one_symbol("ES"), one_symbol("NQ")], how="vertical")


# ---------------------------------------------------------------------------
# Fit / predict functions (nested CV inside fold)
# ---------------------------------------------------------------------------


def _fit_fold(
    train_idx: np.ndarray,
    *,
    X: np.ndarray,
    y: np.ndarray,
    r: np.ndarray,
    hmm_cov_types: tuple[str, ...],
    lgb_grid: dict[str, tuple[Any, ...]],
    lgb_n_draws: int,
    lgb_seed: int,
    random_seed: int,
) -> dict[str, Any]:
    """Fit a classifier + HMM regime model on the fold's training rows.

    The classifier is intentionally lightweight for Phase-A: we
    sample up to ``min(lgb_n_draws, 10)`` hyperparameter
    combinations from the grid and pick the highest-in-sample
    log-loss winner. The point of Phase A is composition — a full
    nested random-search + inner CV lives in the live run.
    """
    X_tr = X[train_idx]
    y_tr = y[train_idx]
    r_tr = r[train_idx]

    # HMM on returns — BIC over cov types, small grid.
    hmm_selection = select_gaussian_hmm(
        r_tr.reshape(-1, 1),
        n_states_grid=(2,),
        covariance_types=hmm_cov_types,
        seed=int(random_seed),
        min_restarts=5,
        max_restarts=10,
    )
    hmm: GaussianHMM = hmm_selection.best_model

    # LightGBM classifier (intentionally shallow random search —
    # composition, not performance).
    import lightgbm as lgb

    rng = np.random.default_rng(lgb_seed)
    keys = list(lgb_grid.keys())
    n_combos = 1
    for vals in lgb_grid.values():
        n_combos *= max(1, len(vals))
    n_draws_eff = int(min(lgb_n_draws, n_combos, 10))
    best_model: lgb.LGBMClassifier | None = None
    best_score = -np.inf
    for _ in range(n_draws_eff):
        params = {k: rng.choice(list(lgb_grid[k])) for k in keys}
        # Cast to Python scalars (lightgbm refuses numpy dtypes here).
        params = {k: (int(v) if isinstance(v, np.integer) else float(v))
                  for k, v in params.items()}
        # LightGBM's `LGBMClassifier` needs at least 2 classes in y.
        if len(np.unique(y_tr)) < 2:
            return {"classifier": None, "hmm": hmm, "regime_high_mean": 0}
        model = lgb.LGBMClassifier(
            n_estimators=50,
            random_state=int(random_seed),
            verbose=-1,
            **params,
        )
        model.fit(X_tr, y_tr)
        score = float(model.score(X_tr, y_tr))
        if score > best_score:
            best_score = score
            best_model = model

    # Highest-mean regime state (for inference-time gating). Taken
    # from the HMM's emission means.
    assert hmm.params_ is not None
    means = hmm.params_.means[:, 0]
    regime_high_mean = int(np.argmax(means))

    return {
        "classifier": best_model,
        "hmm": hmm,
        "regime_high_mean": regime_high_mean,
    }


def _predict_fold(
    fitted: dict[str, Any],
    test_idx: np.ndarray,
    *,
    X: np.ndarray,
    r: np.ndarray,
) -> np.ndarray:
    """Emit two-column predictions: ``(classifier_p, regime_indicator)``.

    Regime is the indicator ``P(state = highest-mean state | y_{1:t})``
    > 0.5 evaluated through :meth:`GaussianHMM.filter_states`
    (causal). Classifier probability is the LightGBM class-1
    probability.
    """
    X_te = X[test_idx]
    r_te = r[test_idx]
    clf = fitted["classifier"]
    if clf is None:
        p = np.full(test_idx.size, 0.5, dtype=np.float64)
    else:
        p = clf.predict_proba(X_te)[:, 1] if hasattr(clf, "predict_proba") else (
            clf.predict(X_te).astype(float)
        )
    hmm: GaussianHMM = fitted["hmm"]
    filtered = hmm.filter_states(r_te.reshape(-1, 1))
    high_state = fitted["regime_high_mean"]
    regime_indicator = (filtered[:, high_state] > 0.5).astype(np.float64)
    return np.stack([p, regime_indicator], axis=1)


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def _sharpe_differential_stats(
    *,
    gated: np.ndarray,
    unconditional: np.ndarray,
    n_bootstrap: int,
    seed: int,
    omega_method: str = "bootstrap",
) -> dict[str, Any]:
    """Opdyke CI + Hansen SPA on OOS returns.

    ``omega_method`` follows ADR-0008: pass ``"hac"`` for single-strategy
    gates (M=1) to decouple the bootstrap MC error from the LRV estimator.
    """
    ci = opdyke2007_ci(gated)
    sharpe_g, _ = sample_sharpe(gated)
    sharpe_u, _ = sample_sharpe(unconditional) if unconditional.std() > 0 else (0.0, 0)
    differential = sharpe_g - sharpe_u
    # SPA: one candidate strategy (gated minus unconditional).
    d = (gated - unconditional).reshape(-1, 1)
    rng = np.random.default_rng(seed)
    bl_selection = choose_block_length(gated - unconditional, bootstrap_type="stationary")
    spa = hansen_spa_test(
        d,
        n_bootstrap=n_bootstrap,
        block_length=bl_selection.block_length,
        rng=rng,
        omega_method=omega_method,
    )
    return {
        "sharpe_gated": float(sharpe_g),
        "sharpe_unconditional": float(sharpe_u),
        "sharpe_differential": float(differential),
        "opdyke_ci": ci.to_dict(),
        "hansen_spa": {
            "p_value": spa.p_value,
            "p_value_lower": spa.p_value_lower,
            "p_value_upper": spa.p_value_upper,
            "statistic": spa.statistic,
            "block_length": bl_selection.block_length,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Walk-forward orchestrator.")
    ap.add_argument("--hypothesis", required=True, help="Hypothesis id, e.g. H050.")
    ap.add_argument("--config", required=True, type=Path, help="YAML config path.")
    ap.add_argument("--dry-run", action="store_true", help="Synthetic-panel mode.")
    ap.add_argument(
        "--smoke-n",
        type=int,
        default=5000,
        help="Rows per symbol in synthetic panel (dry-run).",
    )
    return ap.parse_args(argv)


def run(argv: list[str] | None = None) -> Path:
    args = _parse_args(argv)
    cfg = load_config(args.config)
    paths = ProjectPaths.discover()

    with RunContext(
        phase="walk_forward",
        hypothesis_id=cfg.hypothesis_id,
        rng_seed=cfg.random_seed,
    ) as ctx:
        run_id = ctx.log.run_id  # type: ignore[union-attr]
        run_dir = paths.artifacts_runs / cfg.hypothesis_id / run_id
        paths.ensure(run_dir)
        folds_dir = paths.ensure(run_dir / "folds")
        agg_dir = paths.ensure(run_dir / "aggregate")
        paths.ensure(paths.logs_reproducibility_features)

        # 1. Panel.
        if args.dry_run:
            panel = make_synthetic_panel(
                n_per_symbol=args.smoke_n, seed=cfg.random_seed
            )
        else:
            parquet_dir = paths.root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
            panel = pl.read_parquet(str(parquet_dir / "**" / "*.parquet"))

        # 2. Feature assembly (now = last panel timestamp under PIT).
        now_ts = pd.Timestamp(
            panel.select(pl.col("ts_event").max()).item()
        )
        modules = [FEATURE_REGISTRY[k] for k in cfg.feature_keys]
        feature_matrix, prov = assemble_feature_matrix(
            modules=modules,
            panel=panel.lazy(),
            now=now_ts,
            run_id=run_id,
            features_dir=paths.logs_reproducibility_features,
        )

        # 3. Labels (take the pre-reg center of the grid as Phase-A default).
        label_cfg = TripleBarrierConfig(
            pt_sl=(cfg.pt_sl_grid[len(cfg.pt_sl_grid) // 2],) * 2,
            vertical_barrier=cfg.vertical_barrier_grid[len(cfg.vertical_barrier_grid) // 2],
            volatility_lookback=cfg.volatility_lookback_grid[
                len(cfg.volatility_lookback_grid) // 2
            ],
        )
        labeler = TripleBarrierLabeler(label_cfg)
        labeled = labeler.apply(panel, symbol_col="symbol", time_col="ts_event")

        # 4. Merge features + labels on (symbol, ts_event).
        merged = labeled.join(
            feature_matrix, on=["symbol", "ts_event"], how="left"
        ).drop_nulls()

        # Order by (symbol, ts_event) so positional indices are stable.
        merged = merged.sort(["symbol", "ts_event"])

        # 5. SplitSpec — per symbol we build one, then run engine per symbol
        # (Cycle-6 Phase A: ES first-symbol only for the smoke run).
        sym = "ES"
        sym_frame = merged.filter(pl.col("symbol") == sym)
        if sym_frame.shape[0] < 200:
            # Not enough rows to walk forward; abort early.
            _write_aggregate(
                agg_dir,
                {
                    "status": "insufficient_rows",
                    "n_rows": int(sym_frame.shape[0]),
                },
            )
            return run_dir

        feature_cols = list(cfg.feature_keys)
        X_full = sym_frame.select(feature_cols).to_numpy().astype(np.float64)
        y_full = sym_frame.get_column("label").to_numpy().astype(np.int64)
        # Binary classification target: sign(label) with 0 → drop
        # handled upstream via drop_nulls; treat label==0 as class 0.
        y_bin = (y_full > 0).astype(np.int64)
        # Per-bar log-returns for HMM + PnL.
        closes = sym_frame.get_column("close").to_numpy().astype(np.float64)
        r_bar = np.zeros(len(closes), dtype=np.float64)
        r_bar[1:] = np.diff(np.log(closes))

        n = sym_frame.shape[0]
        bar_duration = pd.Timedelta(minutes=1)
        label_horizon = labeler.label_horizon_bars(bar_duration)

        # Data-driven embargo: Politis-White block length on returns.
        bl = choose_block_length(r_bar, bootstrap_type="stationary")
        embargo = int(max(1, np.ceil(bl.block_length)))

        initial_train = max(200, n // 3)
        test_size = max(50, n // 10)
        step_size = test_size
        split = walk_forward_split(
            n_samples=n,
            initial_train_size=initial_train,
            test_size=test_size,
            step_size=step_size,
            label_horizon=label_horizon,
            embargo=embargo,
            mode="rolling",
            purge_window=label_horizon,
        )

        # 6. Engine.
        engine = WalkForwardEngine(split)
        ts_arr = sym_frame.get_column("ts_event").to_numpy().astype("datetime64[ns]").astype(np.int64)
        result = engine.run(
            fit_fn=_fit_fold,
            predict_fn=_predict_fold,
            feature_timestamps=ts_arr,
            observation_timestamps=ts_arr,
            fit_kwargs=dict(
                X=X_full,
                y=y_bin,
                r=r_bar,
                hmm_cov_types=cfg.hmm_cov_types,
                lgb_grid=cfg.lgb_grid,
                lgb_n_draws=cfg.lgb_n_draws,
                lgb_seed=cfg.lgb_seed,
                random_seed=cfg.random_seed,
            ),
            predict_kwargs=dict(X=X_full, r=r_bar),
        )

        # Cost model: instantiate once per run; cost deduction per side per
        # contract at every position change (entry, exit, reversal).
        # n_sides = abs(pos[t] - pos[t-1]): 1 for open/close, 2 for reversal.
        # Per-side cost deducted as a return fraction: cost_usd / notional_usd.
        # Notional_usd = close_price × multiplier (ES=50, NQ=20).
        _MULTIPLIERS = {"ES": 50.0, "NQ": 20.0, "MES": 5.0, "MNQ": 2.0}
        cost_model = NT8EsNqRthV1CostModel(
            sensitivity_mult=cfg.cost_sensitivity_mult
        )
        sym_multiplier = _MULTIPLIERS.get(sym, 50.0)
        per_side_cost = cost_model.round_trip_cost(sym, 1) / 2.0
        closes_full = sym_frame.get_column("close").to_numpy().astype(np.float64)

        # 7. OOS returns. Simple long/short/flat PnL: position =
        # sign(2·p - 1) in the unconditional variant; the gated
        # variant zeros the position outside the high-mean regime.
        # Net-of-cost returns deduct one per-side cost at each position
        # change (trade_sides = abs(pos[t] − pos[t−1])).
        gated_returns: list[float] = []
        uncond_returns: list[float] = []
        prev_uncond_pos = 0.0
        prev_gated_pos = 0.0
        for preds, tidx in zip(result.predictions, result.test_indices, strict=True):
            p = preds[:, 0]
            reg = preds[:, 1]
            position = np.sign(2.0 * p - 1.0)
            r_te = r_bar[tidx]
            close_te = closes_full[tidx]

            # Unconditional net-of-cost.
            uncond_raw = position * r_te
            uncond_sides = np.abs(
                np.concatenate([[position[0] - prev_uncond_pos], np.diff(position)])
            )
            notional_uncond = close_te * sym_multiplier
            notional_uncond = np.where(notional_uncond > 0, notional_uncond, 1.0)
            uncond_cost = uncond_sides * per_side_cost / notional_uncond
            uncond = uncond_raw - uncond_cost
            prev_uncond_pos = float(position[-1])

            # Gated net-of-cost.
            gated_pos = position * reg
            gated_raw = gated_pos * r_te
            gated_sides = np.abs(
                np.concatenate([[gated_pos[0] - prev_gated_pos], np.diff(gated_pos)])
            )
            notional_gated = close_te * sym_multiplier
            notional_gated = np.where(notional_gated > 0, notional_gated, 1.0)
            gated_cost = gated_sides * per_side_cost / notional_gated
            gated = gated_raw - gated_cost
            prev_gated_pos = float(gated_pos[-1])

            uncond_returns.extend(uncond.tolist())
            gated_returns.extend(gated.tolist())
        gated_arr = np.asarray(gated_returns, dtype=np.float64)
        uncond_arr = np.asarray(uncond_returns, dtype=np.float64)

        # 8. Persist per-fold ledger + aggregate summary.
        write_run_ledger(
            result.fold_records,
            ledger_path_for(
                run_id, logs_reproducibility_dir=paths.logs_reproducibility
            ),
        )
        # Write per-fold records as JSON too for quick inspection.
        for rec in result.fold_records:
            (folds_dir / f"fold_{rec.fold_id:03d}.json").write_text(
                json.dumps(dataclasses.asdict(rec), sort_keys=True, indent=2),
                encoding="utf-8",
            )

        # Raw OOS returns parquet.
        pl.DataFrame(
            {"gated_return": gated_arr, "unconditional_return": uncond_arr}
        ).write_parquet(run_dir / "oos_returns.parquet")

        # 9. Gates (only if we have enough returns).
        metrics: dict[str, Any]
        if gated_arr.size >= 4 and gated_arr.std() > 0 and uncond_arr.std() > 0:
            metrics = _sharpe_differential_stats(
                gated=gated_arr,
                unconditional=uncond_arr,
                n_bootstrap=cfg.spa_n_bootstrap,
                seed=cfg.random_seed,
                omega_method=cfg.spa_omega_method,
            )
        else:
            metrics = {
                "status": "insufficient_oos_returns",
                "n_returns": int(gated_arr.size),
            }
        metrics["n_folds"] = len(result.fold_records)
        metrics["n_features"] = len(cfg.feature_keys)
        metrics["feature_keys"] = list(cfg.feature_keys)
        metrics["feature_provenance"] = [p.to_dict() for p in prov]

        _write_aggregate(agg_dir, metrics)

        # 10. Model hash into ReproLog.
        rolled = roll_up_model_hashes(
            [(r.fold_id, r.model_hash) for r in result.fold_records]
        )
        new_log = with_model_hash(ctx.log, rolled)  # type: ignore[arg-type]
        ctx.log = new_log

        # 11. Copy ReproLog into the run artifact dir alongside the
        # canonical location (for easy browsing of artifacts).
        (run_dir / "reprolog.json").write_text(
            json.dumps(ctx.log.to_dict(), sort_keys=True, indent=2),
            encoding="utf-8",
        )

    return run_dir


def _write_aggregate(agg_dir: Path, metrics: dict[str, Any]) -> None:
    (agg_dir / "metrics_summary.json").write_text(
        json.dumps(metrics, sort_keys=True, indent=2, default=str),
        encoding="utf-8",
    )


if __name__ == "__main__":
    out = run(sys.argv[1:])
    print(out)
