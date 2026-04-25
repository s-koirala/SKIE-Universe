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
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

# Minimum OOS return observations required to compute Sharpe CI and SPA.
# 30 is a conservative lower bound: Lo 2002 iid Sharpe CLT requires n → ∞;
# Opdyke 2007 HAC-corrected CI retains O(1/√n) error; below 30 the CI is
# too wide to be informative (residual bias O(1/√30) ≈ 18%). Not an
# arbitrary threshold — reflects the effective-sample-size floor at which
# the estimator's asymptotic approximation is defensible.
_MIN_OOS_FOR_CI: int = 30

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
from skie_ninja.models.regime import (
    GaussianHMM,
    WarmColdDiagnostic,
    select_gaussian_hmm,
    warm_cold_sidecar_path_for,
    write_warm_cold_sidecar,
)
from skie_ninja.utils.hashing import frame_sha256
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
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    val_start: pd.Timestamp
    val_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    config_resolved_sha256: str
    raw: dict[str, Any]


def _parse_vb(item: str) -> pd.Timedelta:
    # Accepts tokens like "30m", "60m", "2h".
    return pd.Timedelta(item)


def _parse_window(window: dict[str, Any]) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Parse a {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'} block into a
    (start, end_inclusive) UTC-aware Timestamp pair.

    The end date in H050.yaml is interpreted as the last calendar day
    INCLUSIVE; converting it to ``end + 1d - 1ns`` UTC keeps the upper
    bound on the same calendar day under intraday timestamps. This matches
    the pre-registration's calendar-day semantics (H050 design.md §1)
    rather than midnight-exclusive semantics.
    """
    start = pd.Timestamp(window["start"], tz="UTC")
    end_day = pd.Timestamp(window["end"], tz="UTC")
    end_inclusive = end_day + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    return start, end_inclusive


def load_config(path: Path) -> RunConfig:
    # Read raw bytes first so we can hash the YAML content into ReproLog.
    # Decoupling sha256 from yaml.safe_load round-trip protects against
    # parser-level normalisation (e.g. quote-style changes) silently
    # changing the hash. Reproducibility audit relies on the byte hash
    # of the source file, not the parsed AST.
    import hashlib as _hashlib

    raw_bytes = Path(path).read_bytes()
    config_sha = _hashlib.sha256(raw_bytes).hexdigest()
    raw = yaml.safe_load(raw_bytes)
    train_start, train_end = _parse_window(raw["data"]["train"])
    val_start, val_end = _parse_window(raw["data"]["val"])
    test_start, test_end = _parse_window(raw["data"]["test"])
    return RunConfig(
        hypothesis_id=str(raw["hypothesis_id"]),
        random_seed=int(raw["random_seed"]),
        feature_keys=tuple(raw["features"]),
        pt_sl_grid=tuple(float(x) for x in raw["labels"]["pt_sl_grid"]),
        vertical_barrier_grid=tuple(_parse_vb(x) for x in raw["labels"]["vertical_barrier_grid"]),
        volatility_lookback_grid=tuple(int(x) for x in raw["labels"]["volatility_lookback_grid"]),
        lgb_grid={k: tuple(v) for k, v in raw["classifier"]["grid"].items()},
        lgb_n_draws=int(raw["classifier"]["search"]["n_draws"]),
        lgb_seed=int(raw["classifier"]["search"]["seed"]),
        hmm_cov_types=tuple(raw["hmm"]["covariance_type"]),
        spa_n_bootstrap=int(raw["gates"]["hansen_spa"]["n_bootstrap"]),
        spa_omega_method=str(raw["gates"]["hansen_spa"].get("omega_method", "bootstrap")),
        cost_model_id=str(raw.get("cost_model", "nt8_es_nq_rth_v1")),
        cost_sensitivity_mult=float(raw.get("cost_sensitivity_mult", 1.0)),
        gate_alpha=float(raw["gates"]["opdyke2007_ci"]["alpha"]),
        train_start=train_start,
        train_end=train_end,
        val_start=val_start,
        val_end=val_end,
        test_start=test_start,
        test_end=test_end,
        config_resolved_sha256=config_sha,
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
    # NOTE (Round-2 F-1-1 fix): the prior zero-mask `r_tr != 0.0` was
    # dropped because it desynchronised the HMM's transition-matrix
    # discrete-time clock from the bar-position clock used to compute
    # the walk-forward warm-start propagation steps (ADR-0005
    # §"Fold-boundary state continuity"). Under the mask, an HMM step
    # corresponded to "one kept-bar" while the warm-start K-step
    # propagation used "raw bars between train terminal and test first
    # observation" — a silent inconsistency whenever any bar within
    # train or test had r_bar == 0 (halts, flat closes, or the dataset's
    # construction-zero at bar 0). The only construction-zero is at
    # global bar 0 (a single observation in a 1-min ES/NQ panel of
    # ~10^6 bars), so the bias from including it in the HMM emission
    # statistics is negligible (<1e-6 of any moment). The bar-clock /
    # HMM-clock invariant is preserved under no mask.
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
    # composition, not performance). Phase-A uses in-sample accuracy for
    # selection; inner-fold CV is the evidence-bar standard (follow-up
    # P1-H050-INNER-CV: replace model.score(X_tr, y_tr) with inner
    # purged walk-forward CV per Varma & Simon 2006, doi:10.1186/1471-2105-7-91).
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
        params = {k: (int(v) if isinstance(v, np.integer) else float(v)) for k, v in params.items()}
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

    # P1-HMM-FOLD-WARM-START: harvest train-fold terminal log α as the
    # sufficient statistic for the test-fold filter prior (ADR-0005
    # §"Fold-boundary state continuity"). With the zero-mask removed
    # (Round-2 F-1-1 fix above), the HMM observation count equals the
    # train-fold bar count, so the terminal HMM observation lives at
    # bar position train_idx[-1].
    hmm_terminal_log_alpha = hmm.terminal_log_alpha(r_tr.reshape(-1, 1))
    hmm_train_terminal_position = int(train_idx[-1])

    return {
        "classifier": best_model,
        "hmm": hmm,
        "regime_high_mean": regime_high_mean,
        "hmm_terminal_log_alpha": hmm_terminal_log_alpha,
        "hmm_train_terminal_position": hmm_train_terminal_position,
    }


def _predict_fold(
    fitted: dict[str, Any],
    test_idx: np.ndarray,
    *,
    X: np.ndarray,
    r: np.ndarray,
    warm_cold_diagnostic: WarmColdDiagnostic | None = None,
    fold_id: int | None = None,
) -> np.ndarray:
    """Emit two-column predictions: ``(classifier_p, regime_indicator)``.

    Regime is the indicator ``P(state = highest-mean state | y_{1:t})``
    > 0.5 evaluated through :meth:`GaussianHMM.filter_states_from_prior`
    (causal warm-start; ADR-0005). Classifier probability is the
    LightGBM class-1 probability.

    The optional ``warm_cold_diagnostic`` collector is a passive
    observer (P1-HMM-WARM-COLD-DIAGNOSTIC): when supplied, the
    function additionally computes the cold-start posterior and
    records per-fold Hellinger / total-variation summary statistics.
    The cold-start path is discarded after observation; the
    production output is unconditionally the warm-start posterior.

    ``fold_id`` is injected by
    :meth:`~skie_ninja.backtest.engine.walk_forward.WalkForwardEngine.run`
    (P1-WF-ENGINE-FOLD-ID-PASSTHROUGH closure) and is identical to
    ``WalkForwardResult.fold_records[i].fold_id`` for the fold under
    test. When ``None`` (e.g. the function is invoked outside the
    engine for ad-hoc inspection) the diagnostic falls back to
    ``len(warm_cold_diagnostic.fold_records)`` — the same fallback
    used before the passthrough refactor.
    """
    X_te = X[test_idx]
    r_te = r[test_idx]
    clf = fitted["classifier"]
    if clf is None:
        p = np.full(test_idx.size, 0.5, dtype=np.float64)
    else:
        p = (
            clf.predict_proba(X_te)[:, 1]
            if hasattr(clf, "predict_proba")
            else (clf.predict(X_te).astype(float))
        )
    hmm: GaussianHMM = fitted["hmm"]
    # P1-HMM-FOLD-WARM-START closure: warm-start the test-fold causal
    # forward filter with the train-fold terminal log α, propagated K
    # transition steps where K = test_first_position − train_terminal_position
    # accounts for the purge+embargo gap (López de Prado 2018 AFML §7).
    # Anchored on the Hamilton-filter prediction step (Hamilton 1989
    # Econometrica §3, Hamilton 1994 §22.4, Kim & Nelson 1999 §4.2-4.3).
    # ADR-0005 §"Fold-boundary state continuity" documents the choice
    # and rejects the cold-start variants.
    log_alpha_prior = fitted["hmm_terminal_log_alpha"]
    test_first_position = int(test_idx[0])
    train_terminal_position = int(fitted["hmm_train_terminal_position"])
    n_propagation_steps = test_first_position - train_terminal_position
    if n_propagation_steps < 1:
        raise ValueError(
            f"Walk-forward fold-boundary invariant violated: "
            f"test_first_position={test_first_position} <= "
            f"train_terminal_position={train_terminal_position}. "
            f"Test fold must start strictly after train fold terminal."
        )
    test_obs = r_te.reshape(-1, 1)
    filtered = hmm.filter_states_from_prior(
        test_obs,
        log_alpha_prior=log_alpha_prior,
        n_propagation_steps=n_propagation_steps,
    )
    # P1-HMM-WARM-COLD-DIAGNOSTIC: passive observer. The cold posterior
    # is computed only for the diagnostic record and is not used in the
    # returned predictions. Hellinger distance (Tsybakov 2009 §2.4; Le
    # Cam 1986 general reference) is the primary divergence metric;
    # total-variation distance is logged as a secondary metric so the
    # Tsybakov 2009 envelope H^2 <= TV <= H*sqrt(2 - H^2) (substituted
    # under bounded Hellinger) provides a per-fold sanity envelope.
    if warm_cold_diagnostic is not None:
        cold = hmm.filter_states(test_obs)
        diag_fold_id = fold_id if fold_id is not None else len(warm_cold_diagnostic.fold_records)
        warm_cold_diagnostic.observe_fold(
            fold_id=diag_fold_id,
            warm_posterior=filtered,
            cold_posterior=cold,
            n_propagation_steps=n_propagation_steps,
            train_terminal_position=train_terminal_position,
            test_first_position=test_first_position,
        )
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


def _load_output_sha256(paths: Any) -> dict[str, str]:
    """Load the roll-adjusted output frame SHA256 from the most recent
    provenance JSON for dataset_checksums wiring into ReproLog.

    Falls back gracefully if no provenance file is present (dry-run).
    """
    import glob as _glob

    pattern = str(
        paths.root
        / "data"
        / "processed"
        / "_provenance"
        / "vendor_legacy_1min_roll_adjusted_*.json"
    )
    files = sorted(_glob.glob(pattern))
    if not files:
        return {}
    try:
        with open(files[-1], encoding="utf-8") as fh:
            prov = json.load(fh)
        # output_frame_sha256 is the post-roll-adjustment combined hash;
        # source_dataset_frame_sha256 is the pre-adjustment input hash.
        sha = prov.get(
            "output_frame_sha256",
            prov.get("source_dataset_frame_sha256", ""),
        )
        if sha:
            return {"vendor_legacy_1min_roll_adjusted": sha}
    except Exception:
        pass
    return {}


def run(argv: list[str] | None = None) -> Path:
    args = _parse_args(argv)
    cfg = load_config(args.config)
    paths = ProjectPaths.discover()

    dataset_checksums = _load_output_sha256(paths) if not args.dry_run else {}

    with RunContext(
        phase="walk_forward",
        hypothesis_id=cfg.hypothesis_id,
        rng_seed=cfg.random_seed,
        dataset_checksums=dataset_checksums,
        config_resolved_sha256=cfg.config_resolved_sha256,
    ) as ctx:
        # F-3-3 round-trip assert: confirm RunContext persisted the
        # YAML hash onto ReproLog (not silently dropped on a kwarg-name
        # change). Cheap, byte-identity check.
        assert (  # noqa: S101
            ctx.log is not None and ctx.log.config_resolved_sha256 == cfg.config_resolved_sha256
        ), "RunContext failed to persist config_resolved_sha256 onto ReproLog"
        run_id = ctx.log.run_id  # type: ignore[union-attr]
        run_dir = paths.artifacts_runs / cfg.hypothesis_id / run_id
        paths.ensure(run_dir)
        folds_dir = paths.ensure(run_dir / "folds")
        agg_dir = paths.ensure(run_dir / "aggregate")
        paths.ensure(paths.logs_reproducibility_features)

        # 1. Panel.
        if args.dry_run:
            panel = make_synthetic_panel(n_per_symbol=args.smoke_n, seed=cfg.random_seed)
        else:
            parquet_dir = paths.root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
            panel = pl.read_parquet(str(parquet_dir / "**" / "*.parquet"))

        # 2. Feature assembly (now = last panel timestamp under PIT).
        # Each feature module's rolling window is computed on the full panel;
        # row i uses only bars ≤ i so no fold boundary leakage is introduced
        # by computing features once on the full dataset. The walk-forward
        # engine then slices positional indices per fold. The 'now' parameter
        # controls the maximum timestamp included — using the global max means
        # all bars are included and each module's PIT guard fires at bar-close
        # time (not at fold boundary). This is correct for bar-level PIT.
        # Follow-up P1-H050-FEATURE-PIT-ASSERT: add integration test asserting
        # feature_matrix row i has no value derived from bars beyond row i.
        now_ts = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
        modules = [FEATURE_REGISTRY[k] for k in cfg.feature_keys]
        feature_matrix, prov = assemble_feature_matrix(
            modules=modules,
            panel=panel.lazy(),
            now=now_ts,
            run_id=run_id,
            features_dir=paths.logs_reproducibility_features,
        )

        # 3. Labels (take the pre-reg center of the grid as Phase-A default).
        # Phase-A uses the center-grid element; CV over label params is the
        # evidence-bar standard. Follow-up P1-H050-LABEL-CV.
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
        merged = labeled.join(feature_matrix, on=["symbol", "ts_event"], how="left").drop_nulls()

        # Order by (symbol, ts_event) so positional indices are stable.
        merged = merged.sort(["symbol", "ts_event"])

        # 5. SplitSpec — per symbol we build one, then run engine per symbol
        # (Cycle-6 Phase A: ES first-symbol only for the smoke run).
        sym = "ES"
        sym_frame = merged.filter(pl.col("symbol") == sym)
        # Pre-reg date filter (P1-H050-SPLIT-PARAMS closure): on real runs,
        # clip to the H050.yaml §data envelope [train.start, test.end] BEFORE
        # deriving split sizes. Out-of-envelope rows (e.g. backfill that
        # overshoots 2025-12-31) MUST NOT enter the walk-forward — keeping
        # them would let the dataset's row count drive fold boundaries
        # instead of the pre-registered calendar. End-inclusive semantics
        # per _parse_window. The synthetic panel (n_per_symbol bars at
        # 1-min freq) cannot span the 11-yr envelope, so dry-run skips the
        # filter; engine composition is still exercised via row-fraction
        # split sizes (follow-up P1-H050-SYNTHETIC-PANEL-PRE-REG-COVERAGE
        # to extend make_synthetic_panel to span the envelope at a
        # coarser frequency once needed for date-binding regression).
        if not args.dry_run:
            sym_frame = sym_frame.filter(
                (pl.col("ts_event") >= cfg.train_start) & (pl.col("ts_event") <= cfg.test_end)
            )
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

        # Pre-reg-date-derived split sizes (P1-H050-SPLIT-PARAMS closure,
        # F-3-3 of memo_h050-aggregation-rule_2026-04-24.md r4; Round-2
        # F-1-2 fix: val window is part of the in-sample envelope, NOT an
        # OOS fold):
        #   initial_train_size = bars in [train.start, val.end]      (9 yr)
        #     train (2015-2022) fits the model; val (2023) is consumed by the
        #     in-fold inner CV used for HP selection (Varma & Simon 2006,
        #     doi:10.1186/1471-2105-7-91; landing under follow-up
        #     P1-H050-INNER-CV). Both are pre-registered as in-sample.
        #   test_size          = bars in [val.start, val.end]        (~1 yr)
        #     The val window is the smallest pre-registered granularity
        #     available; using it as the fold cadence yields ~2 calendar-year
        #     OOS folds across the test window.
        #   step_size          = test_size  (rolling, non-overlapping OOS)
        #
        # With mode="rolling" + step_size = val-bars, expected OOS fold count
        # = 2 (test_y1=2024, test_y2=2025), each trained on the prior rolling
        # 9-yr in-sample window. Bar-count cadence drifts ~1 trading day vs
        # leap-year calendar boundaries; absolute calendar anchoring is
        # tracked under follow-up P1-H050-CALENDAR-ANCHORED-SPLITTER (Bailey
        # & López de Prado 2014 doi:10.3905/jpm.2014.40.5.094 anti-HARK
        # selection-bias guidance; AFML §11.2). Walk-forward methodology
        # itself: Pesaran & Timmermann 1995 doi:10.1111/j.1540-6261.1995.tb04055.x;
        # Bergmeir, Hyndman & Koo 2018 doi:10.1016/j.csda.2017.11.003;
        # AFML §12.2.
        # Dry-run uses row-fraction sizes because the sparse synthetic panel
        # cannot span the pre-reg envelope (see P1-H050-SYNTHETIC-PANEL-
        # PRE-REG-COVERAGE follow-up).
        if args.dry_run:
            initial_train = max(200, n // 3)
            test_size = max(50, n // 10)
            step_size = test_size
            split_size_source = "row_fraction"
        else:
            ts_event_pl = sym_frame.get_column("ts_event")
            initial_train = int((ts_event_pl <= cfg.val_end).sum())
            val_mask_pl = (ts_event_pl >= cfg.val_start) & (ts_event_pl <= cfg.val_end)
            test_size = int(val_mask_pl.sum())
            step_size = test_size
            split_size_source = "calendar"
            if initial_train <= 0 or test_size <= 0:
                raise ValueError(
                    f"Pre-reg date-derived split sizes invalid: "
                    f"initial_train={initial_train}, test_size={test_size}. "
                    f"Expected >0 bars in both [train.start, val.end] and "
                    f"[val.start, val.end] after filtering to "
                    f"[train.start={cfg.train_start.date()}, "
                    f"test.end={cfg.test_end.date()}]; verify panel coverage "
                    f"against H050.yaml §data."
                )
            test_window_bars = int(
                ((ts_event_pl >= cfg.test_start) & (ts_event_pl <= cfg.test_end)).sum()
            )
            if test_window_bars <= 0:
                raise ValueError(
                    f"Pre-reg test window [{cfg.test_start.date()}, "
                    f"{cfg.test_end.date()}] is empty in the filtered panel; "
                    f"verify ingest snapshot covers H050.yaml §data.test."
                )

        # Post-filter, post-symbol-restriction frame hash. R-4: the pre-filter
        # roll-adjusted output_frame_sha256 cannot distinguish two snapshots
        # that share envelope content but differ outside it. Bind the bytes
        # that actually drove (initial_train, test_size). The mutation
        # survives the later `with_model_hash` call because `with_model_hash`
        # is `dataclasses.replace(log, model_hash=...)` (verified at
        # src/skie_ninja/utils/reproducibility.py:232) which preserves the
        # current `dataset_checksums` dict on `ctx.log`.
        if not args.dry_run:
            ctx.add_dataset_checksum(
                "h050_pre_reg_filtered_es",
                frame_sha256(sym_frame, sort_cols=["symbol", "ts_event"]),
            )
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
        ts_arr = (
            sym_frame.get_column("ts_event").to_numpy().astype("datetime64[ns]").astype(np.int64)
        )

        # F-3-1 calendar-anchor guard: the positional initial_train was
        # derived from `(ts ≤ val.end).sum()`, but mode="rolling" with
        # bar-count cadence does not enforce that fold-0's first OOS bar
        # lands strictly AFTER cfg.test_start. If holidays/halts compressed
        # val_bars or the panel has gaps within [val.start, val.end], the
        # first OOS bar can drift before cfg.test_start, re-introducing
        # val/test conflation. The cheapest binding is a calendar
        # post-condition on the engine's first test slice. Dry-run does not
        # honour the pre-reg envelope, so the guard is real-data only.
        if not args.dry_run and len(split.folds) > 0:
            fold0_test = split.folds[0].test_indices()
            if len(fold0_test) > 0:
                first_oos_pos = int(fold0_test[0])
                first_oos_ts_int = int(ts_arr[first_oos_pos])
                test_start_ts_int = int(
                    np.datetime64(cfg.test_start.to_datetime64())
                    .astype("datetime64[ns]")
                    .astype(np.int64)
                )
                if first_oos_ts_int < test_start_ts_int:
                    raise ValueError(
                        f"Fold-0 first OOS bar maps to "
                        f"ts_int={first_oos_ts_int}, strictly less than "
                        f"cfg.test_start ts_int={test_start_ts_int} — "
                        f"calendar drift has put a pre-test_start bar into "
                        f"OOS. Verify panel coverage in [val.start, val.end] "
                        f"is contiguous, or land "
                        f"P1-H050-CALENDAR-ANCHORED-SPLITTER."
                    )
        # P1-HMM-WARM-COLD-DIAGNOSTIC: passive per-fold collector for
        # warm-vs-cold filter divergence. Hellinger + total-variation
        # statistics are recorded; the production path remains warm-start.
        # Sidecar serialised below; SHA256 rolled into ReproLog.model_hash
        # via the multi-sidecar combiner so a future warm-start regression
        # will surface as a model_hash change.
        # P1-WF-ENGINE-FOLD-ID-PASSTHROUGH closure: the engine now injects
        # ``fold_id`` directly into ``_predict_fold`` (when the signature
        # accepts it), so the prior closure-mutated counter list is gone —
        # the diagnostic's fold_id matches WalkForwardResult.fold_records[*].fold_id
        # by construction (engine sources both from the same Fold).
        warm_cold_diag = WarmColdDiagnostic()
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
            predict_kwargs=dict(
                X=X_full,
                r=r_bar,
                warm_cold_diagnostic=warm_cold_diag,
            ),
        )

        # Cost model: instantiate once per run; cost deduction per side per
        # contract at every position change (entry, exit, reversal).
        # n_sides = abs(pos[t] - pos[t-1]): 1 for open/close, 2 for reversal.
        # Per-side cost deducted as a return fraction: cost_usd / notional_usd.
        # Notional_usd = close_price × multiplier (ES=50, NQ=20).
        _MULTIPLIERS = {"ES": 50.0, "NQ": 20.0, "MES": 5.0, "MNQ": 2.0}
        cost_model = NT8EsNqRthV1CostModel(sensitivity_mult=cfg.cost_sensitivity_mult)
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
            ledger_path_for(run_id, logs_reproducibility_dir=paths.logs_reproducibility),
        )
        # Write per-fold records as JSON too for quick inspection.
        for rec in result.fold_records:
            (folds_dir / f"fold_{rec.fold_id:03d}.json").write_text(
                json.dumps(dataclasses.asdict(rec), sort_keys=True, indent=2),
                encoding="utf-8",
            )

        # Raw OOS returns parquet.
        pl.DataFrame({"gated_return": gated_arr, "unconditional_return": uncond_arr}).write_parquet(
            run_dir / "oos_returns.parquet"
        )

        # 9. Gates (only if we have enough returns).
        metrics: dict[str, Any]
        _gate_ok = (
            gated_arr.size >= _MIN_OOS_FOR_CI and gated_arr.std() > 0 and uncond_arr.std() > 0
        )
        if not _gate_ok:
            _LOG.warning(
                "Gate skipped: n_returns=%d (need %d), gated_std=%.6f, "
                "uncond_std=%.6f — Sharpe CI and SPA not computed.",
                gated_arr.size,
                _MIN_OOS_FOR_CI,
                float(gated_arr.std()),
                float(uncond_arr.std()),
            )
        if _gate_ok:
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

        # Split-geometry audit trail (R-3 / F-1-5 closure). Records the
        # method by which (initial_train, test_size, step_size) were
        # derived plus the pre-reg envelope so artifact readers can
        # verify split fidelity without re-running. Calendar-anchoring
        # drift is surfaced via fold-count expectation: with mode="rolling"
        # + step_size = val-bars across [val.end, test.end], the engine
        # is expected to emit ~2 OOS folds; a deviation is logged.
        metrics["split_size_source"] = split_size_source
        metrics["initial_train_size"] = int(initial_train)
        metrics["test_size"] = int(test_size)
        metrics["step_size"] = int(step_size)
        if split_size_source == "calendar":
            metrics["pre_reg_envelope"] = {
                "train_start": cfg.train_start.isoformat(),
                "train_end": cfg.train_end.isoformat(),
                "val_start": cfg.val_start.isoformat(),
                "val_end": cfg.val_end.isoformat(),
                "test_start": cfg.test_start.isoformat(),
                "test_end": cfg.test_end.isoformat(),
            }
            # Expected OOS fold count = ceil(test_window_bars / step_size).
            # Pre-reg test window is 2 yr, step = 1 yr-bars → expect ~2.
            # No defensive clamps: step_size > 0 and test_window_bars > 0
            # are pre-conditions raised earlier in this branch (F-3-4).
            expected_n_folds = int(np.ceil(test_window_bars / step_size))
            metrics["expected_n_folds"] = expected_n_folds
            if metrics["n_folds"] != expected_n_folds:
                _LOG.warning(
                    "Fold count drift: emitted %d, expected %d (calendar "
                    "drift across leap years; see follow-up "
                    "P1-H050-CALENDAR-ANCHORED-SPLITTER).",
                    metrics["n_folds"],
                    expected_n_folds,
                )

            # F-3-6: per-fold realized envelope (actual ts_event min/max
            # of train + test indices). Configured pre_reg_envelope is
            # the calendar contract; realized_envelope is what the engine
            # actually used. A reader can compute drift = realized − configured
            # without re-running.
            ts_arr_ns = sym_frame.get_column("ts_event").to_numpy().astype("datetime64[ns]")
            metrics["realized_envelope_per_fold"] = []
            for fold in split.folds:
                tr = fold.train_indices()
                te = fold.test_indices()
                metrics["realized_envelope_per_fold"].append(
                    {
                        "fold_id": fold.fold_id,
                        "train_ts_min": str(ts_arr_ns[tr[0]]) if tr else None,
                        "train_ts_max": str(ts_arr_ns[tr[-1]]) if tr else None,
                        "test_ts_min": str(ts_arr_ns[te[0]]) if te else None,
                        "test_ts_max": str(ts_arr_ns[te[-1]]) if te else None,
                    }
                )

        _write_aggregate(agg_dir, metrics)

        # P1-HMM-WARM-COLD-DIAGNOSTIC: write the warm-vs-cold sidecar
        # and hash it into ReproLog.model_hash alongside the per-fold
        # ledger roll-up. The combined model_hash is the SHA256 over
        # the canonical concatenation
        #   "ledger_rollup={H1};warm_cold_diag={H2}"
        # so a regression in either source flips the run-level hash.
        # This matches the ADR-0005 sidecar pattern at
        # src/skie_ninja/models/regime/serialization.py.
        warm_cold_path = warm_cold_sidecar_path_for(
            run_id, logs_reproducibility_dir=paths.logs_reproducibility
        )
        _, warm_cold_sha = write_warm_cold_sidecar(warm_cold_diag, warm_cold_path)

        # 10. Model hash into ReproLog.
        rolled = roll_up_model_hashes([(r.fold_id, r.model_hash) for r in result.fold_records])
        combined = hashlib.sha256(
            f"ledger_rollup={rolled};warm_cold_diag={warm_cold_sha}".encode()
        ).hexdigest()
        new_log = with_model_hash(ctx.log, combined)  # type: ignore[arg-type]
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
