"""H053 Cycle 8 Stage-1 — mediator-only walk-forward (Gao 2018 replication).

Per [plan/h053_buildout_2026-04-28.md](../plan/h053_buildout_2026-04-28.md)
Cycle 8: walk-forward run with the H053 mediator vector
``M_{i,t} = (m_return, m_log_range, m_volume, m_ofi_tickrule)`` as the
sole regressor on the design.md §1 predictand
``y_{i,t} = log(C_i(10:30 ET, t)) − log(C_i(09:45 ET, t))``.

Replicates the [Gao, Han, Li & Zhou 2018 *JFE*](
https://doi.org/10.1016/j.jfineco.2018.05.009) market-intraday-momentum
effect (first-half-hour returns predict last-half-hour returns) on ES
and NQ at the H053 09:45→10:30 ET slice with project-grade
infrastructure.

## Method

1. **Substrate**: roll-adjusted ``vendor_legacy_1min_roll_adjusted``
   (post-Cell-I; ~3.7M ES + ~3.7M NQ rows; 2015-2025).
2. **Features**: H053 mediator block (``H053Mediator`` from §3.4) per
   (symbol, session_date_et). 4 features per session.
3. **Predictand**: log(close_10:30_ET / close_09:45_ET) per session.
   Constructed directly from substrate (does NOT pass through the
   feature factory — the predictand is design.md §1, not a Block A/B/C/D
   feature).
4. **Splits** (per design.md §6 + §10):
   - Train (IS): 2015-01-01 → 2022-12-31.
   - Test (OOS): 2024-01-01 → 2025-12-{03 ES, 19 NQ} per the post-Cell-I
     substrate envelope. Validation 2023 is skipped for Stage-1
     (mediator-only OLS has no hyperparameters).
5. **Estimator**: linear regression (OLS with intercept) of ``y`` on
   ``M``. Per-instrument fit (ES and NQ are estimated separately;
   pooling deferred to Stage-2).
6. **Strategy**: long if ``ŷ > 0``, short if ``ŷ < 0``, flat at 0
   (zero exact ties drop to flat). Realized strategy return per session
   = ``sign(ŷ_{i,t}) · y_{i,t}``.
7. **Sharpe-CI**: Opdyke 2007 / Mertens 2002 generalised iid Sharpe-CI
   per [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) §III. Paired
   Sharpe-differential vs passive-long benchmark via Ledoit-Wolf 2008
   studentised stationary-bootstrap CI per
   [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002).
8. **Categorical table v1**: archetype assignment via
   ``H053Microstructure5_15min``-independent ``fit_archetype_rule``
   (design.md §4.5.1) on the mediator-train fold; apply on the
   mediator-test fold; per-archetype ``P̂(d=+1 | A_k)`` with paired
   stationary-bootstrap percentile CI per design.md §4.5.3.
9. **Brier vs climatological prior**: BSS = 1 - BS_model / BS_clim
   where BS_clim is the per-instrument empirical-frequency baseline.

## No SPA family entry

Stage-1 is exploratory. Per design.md §8 the SPA family slots are
ex-ante reserved for Cycle 10 Arms 1+2 (and Arm 3 if it lands).

## Reproducibility

Pinned BLAS via ``OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1`` per ADR-0009. Substrate path resolves via
``--substrate-path`` flag with fallback to ``$H053_SUBSTRATE_PATH`` env
var. Sidecar JSON records git_head, substrate_dataset_checksum, and
scientific_payload_sha256 per the project ReproLog-style convention.

## Outputs

- ``runs/h053/stage1/{run_id}/sidecar.json`` — full quantitative payload.
- ``runs/h053/stage1/{run_id}/predictions.parquet`` — per-(symbol, session, ŷ, y, archetype_id) rows on the OOS fold.
- ``reports/h053/stage1_mediator_only_disposition.md`` — human-readable disposition with go/no-go recommendation.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from skie_ninja.features.h053 import (
    H053Mediator,
    apply_archetype_rule,
    fit_archetype_rule,
)
from skie_ninja.inference.bootstrap import stationary_bootstrap_indices
from skie_ninja.inference.stats import opdyke2007_ci
from skie_ninja.inference.stats.ledoit_wolf_2008 import (
    ledoit_wolf_2008_differential_ci,
)
from skie_ninja.utils.paths import ProjectPaths

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h053_stage1")


# ---------------------------------------------------------------------------
# Constants (operational pins; tracked under follow-ups for empirical
# tuning where applicable)
# ---------------------------------------------------------------------------

# justify: design.md §6 IS fold = 2015-01-01 → 2022-12-31; OOS fold =
# 2024-01-01 → 2025-12-{03 ES, 19 NQ}. Validation 2023 is skipped for
# Stage-1 since mediator-only OLS has no hyperparameters.
_IS_START = _dt.date(2015, 1, 1)
_IS_END = _dt.date(2022, 12, 31)
_OOS_START = _dt.date(2024, 1, 1)
_OOS_END_ES = _dt.date(2025, 12, 3)
_OOS_END_NQ = _dt.date(2025, 12, 19)

# justify: archetype-K grid per design.md §4.5.1; Stage-1 picks K=5 as
# the canonical mid-grid value for the table v1 deliverable. Full CV
# tuning of K deferred to Cycle 10 Stage-3.
_STAGE1_ARCHETYPE_K: int = 5

# justify: stationary-bootstrap block length anchored at the
# AR(1)-equivalent of the H053 mediator residual series. The Politis-White
# 2004 selector is canonical but on a session-grain panel of ~2,000 rows
# the data-dependent block-length is typically 5-15. Per Cycle 8 stage-1
# scope (exploratory, no SPA entry), pinning a default block length of 10
# sessions is operationally adequate; tracked under follow-up
# `P1-H053-STAGE1-BOOTSTRAP-BLOCK-EMPIRICAL` for Politis-White
# automatic-selection at Stage-3.
_STAGE1_BOOTSTRAP_BLOCK_LEN: int = 10

# justify: Bootstrap replicates for the categorical-table v1 percentile
# CIs. 1000 is the project default per design.md §4.5.3 and Hansen 2005
# bootstrap-replicate convention; Stage-1 inherits it.
_STAGE1_BOOTSTRAP_NREP: int = 1000

# justify: deterministic test seed; arbitrary value pinned for
# reproducibility per CLAUDE.md §Reproducibility.
_STAGE1_RNG_SEED: int = 42


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StrategySharpeBundle:
    """Single-instrument Sharpe-CI bundle on a strategy return series."""

    n: int
    mean_return: float
    std_return: float
    sharpe: float
    sharpe_ci_lo: float
    sharpe_ci_hi: float
    method: str = "opdyke2007"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PairedDifferentialBundle:
    """Paired Sharpe-differential CI vs benchmark."""

    n: int
    sharpe_a: float
    sharpe_b: float
    sharpe_diff: float
    ci_lo: float
    ci_hi: float
    excludes_zero: bool
    method: str = "ledoit_wolf_2008"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CategoricalTableRow:
    """A single archetype row of the v1 conditional-frequency table."""

    archetype_id: int
    n_test_sessions: int
    p_d_plus_1_hat: float       # P̂(d=+1 | A_k)
    p_d_plus_1_ci_lo: float
    p_d_plus_1_ci_hi: float
    mean_y_in_archetype: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Stage1Result:
    """Full Stage-1 result per instrument."""

    symbol: str
    n_train: int
    n_test: int
    ols_intercept: float
    ols_coefs: dict[str, float]
    strategy_sharpe: StrategySharpeBundle
    passive_long_sharpe: StrategySharpeBundle
    paired_diff: PairedDifferentialBundle
    archetype_rule_K: int
    archetype_train_panel_checksum: str
    categorical_table: list[CategoricalTableRow]
    brier_score_model: float
    brier_score_clim: float
    bss: float                     # Brier skill score vs climatological prior
    hks_benchmark_sharpe: StrategySharpeBundle
    paired_diff_vs_hks: PairedDifferentialBundle

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "n_train": self.n_train,
            "n_test": self.n_test,
            "ols_intercept": self.ols_intercept,
            "ols_coefs": self.ols_coefs,
            "strategy_sharpe": self.strategy_sharpe.to_dict(),
            "passive_long_sharpe": self.passive_long_sharpe.to_dict(),
            "paired_diff_vs_passive_long": self.paired_diff.to_dict(),
            "archetype_rule_K": self.archetype_rule_K,
            "archetype_train_panel_checksum": self.archetype_train_panel_checksum,
            "categorical_table": [r.to_dict() for r in self.categorical_table],
            "brier_score_model": self.brier_score_model,
            "brier_score_clim": self.brier_score_clim,
            "bss": self.bss,
            "hks_benchmark_sharpe": self.hks_benchmark_sharpe.to_dict(),
            "paired_diff_vs_hks": self.paired_diff_vs_hks.to_dict(),
        }


# ---------------------------------------------------------------------------
# Substrate IO
# ---------------------------------------------------------------------------


def _resolve_substrate_path(cli_arg: str | None) -> Path:
    if cli_arg:
        p = Path(cli_arg).expanduser().resolve()
    else:
        env = os.environ.get("H053_SUBSTRATE_PATH")
        if env:
            p = Path(env).expanduser().resolve()
        else:
            p = (
                ProjectPaths.discover().root
                / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
            )
    if not p.exists():
        raise FileNotFoundError(f"Substrate path {p} does not exist.")
    return p


def _load_substrate(substrate_root: Path, symbol: str) -> pl.DataFrame:
    pattern = str(substrate_root / f"symbol={symbol}" / "year=*" / "*.parquet")
    df = pl.read_parquet(pattern)
    if len(df) == 0:
        raise ValueError(f"No rows at {pattern}")
    return df


def _substrate_dataset_checksum(substrate_root: Path, symbols: list[str]) -> str:
    parts = []
    for sym in sorted(symbols):
        for path in sorted((substrate_root / f"symbol={sym}").glob("year=*/part-*.parquet")):
            with path.open("rb") as fh:
                file_sha = hashlib.sha256(fh.read()).hexdigest()
            rel = path.relative_to(substrate_root).as_posix()
            parts.append(f"{rel}:{file_sha}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Feature + predictand assembly
# ---------------------------------------------------------------------------


def _compute_mediator_features(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute H053 mediator features across all sessions of `panel`."""
    feature = H053Mediator()
    now = pd.Timestamp(panel["ts_event"].max())
    out = feature.compute(panel.lazy(), now=now).collect()
    # Strip the temporary _hour_et / _minute_et / _session_date_et helpers
    # the mediator may emit; keep only the canonical 6-column output schema.
    keep_cols = [c for c in out.columns if not c.startswith("_")]
    return out.select(keep_cols)


def _compute_predictand(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute design.md §1 predictand y_{i,t} = log(C(10:30) / C(09:45)) per session.

    Returns a DataFrame with columns: ts_event (UTC, anchored at 09:45 ET),
    symbol, session_date_et, y, c_0945, c_1030.
    """
    panel = panel.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.date().alias("_session_date_et"),
        pl.col("_ts_et").dt.hour().cast(pl.Int32).alias("_hour_et"),
        pl.col("_ts_et").dt.minute().cast(pl.Int32).alias("_minute_et"),
    )
    # 09:45 ET bar: hour=9, minute=45 (per §3.0 R5 inclusive end-of-bar)
    c_0945 = (
        panel.filter((pl.col("_hour_et") == 9) & (pl.col("_minute_et") == 45))
        .select(
            pl.col("symbol"),
            pl.col("_session_date_et").alias("session_date_et"),
            pl.col("ts_event").alias("ts_event_0945"),
            pl.col("close").alias("c_0945"),
        )
    )
    # 10:30 ET bar: hour=10, minute=30
    c_1030 = (
        panel.filter((pl.col("_hour_et") == 10) & (pl.col("_minute_et") == 30))
        .select(
            pl.col("symbol"),
            pl.col("_session_date_et").alias("session_date_et"),
            pl.col("close").alias("c_1030"),
        )
    )
    joined = c_0945.join(c_1030, on=["symbol", "session_date_et"], how="inner")
    joined = joined.with_columns(
        (pl.col("c_1030") / pl.col("c_0945")).log().alias("y")
    )
    # Sanity: y must be finite
    joined = joined.filter(pl.col("y").is_finite())
    return joined.select(
        pl.col("ts_event_0945").alias("ts_event"),
        "symbol",
        "session_date_et",
        "c_0945",
        "c_1030",
        "y",
    )


def _join_features_predictand(
    mediator: pl.DataFrame, predictand: pl.DataFrame
) -> pl.DataFrame:
    """Inner-join mediator features and predictand on (symbol, ts_event).

    The substrate's `ts_event` is Datetime("us", "UTC"); the H053 mediator
    output's `ts_event` is Datetime("ns", "UTC"). Cast both to ns-UTC
    before the join so Polars 1.40+ doesn't reject the schema mismatch.
    """
    target_dtype = pl.Datetime("ns", "UTC")
    mediator = mediator.with_columns(pl.col("ts_event").cast(target_dtype))
    predictand = predictand.with_columns(pl.col("ts_event").cast(target_dtype))
    return predictand.join(mediator, on=["symbol", "ts_event"], how="inner")


# ---------------------------------------------------------------------------
# OLS + strategy
# ---------------------------------------------------------------------------


_FEATURE_COLS = ("m_return", "m_log_range", "m_volume", "m_ofi_tickrule")


def _ols_fit_predict(
    train: pl.DataFrame, test: pl.DataFrame
) -> tuple[float, dict[str, float], np.ndarray]:
    """Fit OLS on train; return (intercept, coefs, test_predictions)."""
    X_train = np.column_stack([train[c].to_numpy() for c in _FEATURE_COLS])
    y_train = train["y"].to_numpy()
    X_test = np.column_stack([test[c].to_numpy() for c in _FEATURE_COLS])
    # OLS via numpy.linalg.lstsq: design matrix with intercept column
    X_train_aug = np.column_stack([np.ones(len(X_train)), X_train])
    beta, *_ = np.linalg.lstsq(X_train_aug, y_train, rcond=None)
    intercept = float(beta[0])
    coefs = {c: float(beta[i + 1]) for i, c in enumerate(_FEATURE_COLS)}
    X_test_aug = np.column_stack([np.ones(len(X_test)), X_test])
    y_pred = X_test_aug @ beta
    return intercept, coefs, y_pred


def _strategy_returns(y_pred: np.ndarray, y_actual: np.ndarray) -> np.ndarray:
    """Strategy return = sign(ŷ) · y_actual; flat at zero predictions."""
    sign = np.where(y_pred > 0, 1.0, np.where(y_pred < 0, -1.0, 0.0))
    return sign * y_actual


def _hks_benchmark_returns(
    train_returns: np.ndarray,
    test_y: np.ndarray,
) -> np.ndarray:
    """Time-of-day fixed-effects benchmark per design.md §8: predict the
    train mean of y as the constant signal; long if mean > 0 else short.

    For Stage-1 the predictand is at fixed-clock-time (09:45-10:30 ET),
    so the time-of-day FE collapses to a single mean across the train
    fold. Strategy return = sign(mean_y_train) · y_test.
    """
    mean_y_train = float(np.mean(train_returns))
    sign = 1.0 if mean_y_train > 0 else -1.0
    return sign * test_y


def _passive_long_returns(test_y: np.ndarray) -> np.ndarray:
    """Passive-long benchmark: always long. Strategy return = y."""
    return test_y.astype(np.float64)


# ---------------------------------------------------------------------------
# Sharpe + paired-differential CIs
# ---------------------------------------------------------------------------


def _sharpe_bundle(
    returns: np.ndarray, *, label: str = "strategy"
) -> StrategySharpeBundle:
    """Single-strategy Sharpe + Opdyke 2007 / Mertens-HAC-approx iid CI."""
    if len(returns) < 4:
        raise ValueError(f"Need ≥4 obs for Opdyke CI; got {len(returns)} ({label}).")
    ci = opdyke2007_ci(returns, confidence_level=0.95)
    return StrategySharpeBundle(
        n=len(returns),
        mean_return=float(np.mean(returns)),
        std_return=float(np.std(returns, ddof=1)),
        sharpe=ci.sharpe,
        sharpe_ci_lo=ci.lower,
        sharpe_ci_hi=ci.upper,
        method=ci.method,
    )


def _paired_differential(
    a_returns: np.ndarray,
    b_returns: np.ndarray,
    *,
    block_len: int = _STAGE1_BOOTSTRAP_BLOCK_LEN,
    n_rep: int = _STAGE1_BOOTSTRAP_NREP,
    rng_seed: int = _STAGE1_RNG_SEED,
) -> PairedDifferentialBundle:
    """Paired Sharpe-differential CI per Ledoit-Wolf 2008."""
    rng = np.random.default_rng(rng_seed)
    # Compute biased per-arm Sharpes for the bundle return; LW2008's
    # `point_estimate` is SR_a - SR_b under ddof=0 plug-in. Re-derive each
    # leg from the input series with ddof=0 to match.
    sr_a = float(np.mean(a_returns)) / (
        float(np.std(a_returns, ddof=0)) if np.std(a_returns, ddof=0) > 0 else float("nan")
    )
    sr_b = float(np.mean(b_returns)) / (
        float(np.std(b_returns, ddof=0)) if np.std(b_returns, ddof=0) > 0 else float("nan")
    )
    result = ledoit_wolf_2008_differential_ci(
        a_returns,
        b_returns,
        n_bootstrap=n_rep,
        block_length=float(block_len),
        rng=rng,
        alpha=0.05,
    )
    return PairedDifferentialBundle(
        n=len(a_returns),
        sharpe_a=sr_a,
        sharpe_b=sr_b,
        sharpe_diff=result.point_estimate,
        ci_lo=result.lower,
        ci_hi=result.upper,
        excludes_zero=(result.lower > 0.0 or result.upper < 0.0),
        method=result.method,
    )


# ---------------------------------------------------------------------------
# Categorical table v1 (per design.md §4.5.3)
# ---------------------------------------------------------------------------


def _build_categorical_table_v1(
    train_with_features: pl.DataFrame,
    test_with_features: pl.DataFrame,
    K: int,
    rng_seed: int = _STAGE1_RNG_SEED,
    n_rep: int = _STAGE1_BOOTSTRAP_NREP,
    block_len: int = _STAGE1_BOOTSTRAP_BLOCK_LEN,
) -> tuple[list[CategoricalTableRow], str, np.ndarray]:
    """Fit archetype rule on train mediator; apply on test; per-archetype
    ``P̂(d=+1 | A_k)`` with paired stationary-bootstrap percentile CI.

    Returns (table_rows, train_panel_checksum, test_archetype_ids).
    """
    rule = fit_archetype_rule(train_with_features.select(_FEATURE_COLS_FOR_ARCHETYPE), K=K)
    test_with_archetype = apply_archetype_rule(
        test_with_features.select(_FEATURE_COLS_FOR_ARCHETYPE), rule
    )
    archetype_ids = test_with_archetype["archetype_id"].to_numpy()
    y_test = test_with_features["y"].to_numpy()
    d_test = (y_test > 0).astype(np.int32)  # d=+1 iff y > 0
    # Paired stationary-bootstrap on (archetype, d) tuples.
    rng = np.random.default_rng(rng_seed)
    n = len(archetype_ids)
    # Pre-generate n_rep replicates of bootstrap indices (the helper
    # returns one replicate per call).
    boot_indices_list = [
        stationary_bootstrap_indices(n=n, block_length=float(block_len), rng=rng)
        for _ in range(n_rep)
    ]
    rows: list[CategoricalTableRow] = []
    for k in range(K):
        mask_k = archetype_ids == k
        n_k = int(mask_k.sum())
        if n_k == 0:
            rows.append(CategoricalTableRow(
                archetype_id=k, n_test_sessions=0,
                p_d_plus_1_hat=float("nan"),
                p_d_plus_1_ci_lo=float("nan"),
                p_d_plus_1_ci_hi=float("nan"),
                mean_y_in_archetype=float("nan"),
            ))
            continue
        p_hat = float(d_test[mask_k].mean())
        mean_y_k = float(y_test[mask_k].mean())
        # Bootstrap CI: per replicate b, recompute p_hat_b for archetype k
        p_boot = []
        for idx_b in boot_indices_list:
            archetype_b = archetype_ids[idx_b]
            d_b = d_test[idx_b]
            mask_kb = archetype_b == k
            if int(mask_kb.sum()) == 0:
                continue
            p_boot.append(float(d_b[mask_kb].mean()))
        if p_boot:
            p_arr = np.asarray(p_boot)
            lo = float(np.quantile(p_arr, 0.025))
            hi = float(np.quantile(p_arr, 0.975))
        else:
            lo, hi = float("nan"), float("nan")
        rows.append(CategoricalTableRow(
            archetype_id=k, n_test_sessions=n_k,
            p_d_plus_1_hat=p_hat,
            p_d_plus_1_ci_lo=lo,
            p_d_plus_1_ci_hi=hi,
            mean_y_in_archetype=mean_y_k,
        ))
    return rows, rule.train_panel_checksum, archetype_ids


# Mediator features for archetype assignment (subset of the H053 mediator output).
_FEATURE_COLS_FOR_ARCHETYPE: tuple[str, ...] = (
    "m_return", "m_log_range", "m_volume", "m_ofi_tickrule",
)


# ---------------------------------------------------------------------------
# Brier score vs climatological prior
# ---------------------------------------------------------------------------


def _brier_score_components(
    y_pred: np.ndarray, y_actual: np.ndarray, p_clim: float
) -> tuple[float, float, float]:
    """Per-archetype-not-yet-summed Brier score for binary d=+1 outcome.

    Reduce ŷ to a probabilistic prediction via a logit link approximation:
    we use the sign-of-ŷ as a hard probabilistic prediction (1.0 if ŷ>0,
    0.0 otherwise). This is the simplest scoring for Stage-1; richer
    isotonic-calibrated probabilities defer to Stage-3.

    Returns (brier_model, brier_clim, bss).
    """
    d = (y_actual > 0).astype(np.float64)
    p_model = (y_pred > 0).astype(np.float64)
    bs_model = float(np.mean((p_model - d) ** 2))
    bs_clim = float(np.mean((p_clim - d) ** 2))
    bss = 1.0 - (bs_model / bs_clim) if bs_clim > 0 else float("nan")
    return bs_model, bs_clim, bss


# ---------------------------------------------------------------------------
# Per-instrument runner
# ---------------------------------------------------------------------------


def _run_for_symbol(
    substrate_root: Path,
    symbol: str,
    oos_end: _dt.date,
) -> tuple[Stage1Result, pl.DataFrame]:
    _log.info("[%s] Loading substrate …", symbol)
    panel = _load_substrate(substrate_root, symbol)
    _log.info("[%s] %d rows loaded", symbol, len(panel))

    _log.info("[%s] Computing H053 mediator features …", symbol)
    mediator = _compute_mediator_features(panel)
    _log.info("[%s] mediator: %d sessions", symbol, len(mediator))

    _log.info("[%s] Computing predictand …", symbol)
    predictand = _compute_predictand(panel)
    _log.info("[%s] predictand: %d sessions", symbol, len(predictand))

    aligned = _join_features_predictand(mediator, predictand)
    _log.info("[%s] aligned (M, y) panel: %d sessions", symbol, len(aligned))

    # Train / test split per design.md §6
    train = aligned.filter(
        (pl.col("session_date_et") >= _IS_START)
        & (pl.col("session_date_et") <= _IS_END)
    )
    test = aligned.filter(
        (pl.col("session_date_et") >= _OOS_START)
        & (pl.col("session_date_et") <= oos_end)
    )
    _log.info("[%s] train n=%d, test n=%d", symbol, len(train), len(test))
    if len(train) < 100 or len(test) < 100:
        raise ValueError(
            f"[{symbol}] Insufficient train/test size: train={len(train)}, test={len(test)}; "
            "expected >=100 each. Substrate envelope misaligned vs design.md §6."
        )

    intercept, coefs, y_pred = _ols_fit_predict(train, test)
    _log.info(
        "[%s] OLS: intercept=%.6e, coefs=%s",
        symbol, intercept, {k: f"{v:.6e}" for k, v in coefs.items()},
    )

    y_actual = test["y"].to_numpy()
    strat_returns = _strategy_returns(y_pred, y_actual)
    passive_returns = _passive_long_returns(y_actual)

    train_y = train["y"].to_numpy()
    hks_returns = _hks_benchmark_returns(train_y, y_actual)

    strat_sharpe = _sharpe_bundle(strat_returns, label=f"{symbol}_strategy")
    passive_sharpe = _sharpe_bundle(passive_returns, label=f"{symbol}_passive_long")
    hks_sharpe = _sharpe_bundle(hks_returns, label=f"{symbol}_hks_benchmark")

    _log.info(
        "[%s] Sharpe — strategy=%.4f [%.4f, %.4f]; passive_long=%.4f [%.4f, %.4f]; hks=%.4f [%.4f, %.4f]",
        symbol,
        strat_sharpe.sharpe, strat_sharpe.sharpe_ci_lo, strat_sharpe.sharpe_ci_hi,
        passive_sharpe.sharpe, passive_sharpe.sharpe_ci_lo, passive_sharpe.sharpe_ci_hi,
        hks_sharpe.sharpe, hks_sharpe.sharpe_ci_lo, hks_sharpe.sharpe_ci_hi,
    )

    paired_passive = _paired_differential(strat_returns, passive_returns)
    paired_hks = _paired_differential(strat_returns, hks_returns)
    _log.info(
        "[%s] Paired diff vs passive_long=%.4f [%.4f, %.4f] excludes_zero=%s; vs hks=%.4f [%.4f, %.4f] excludes_zero=%s",
        symbol,
        paired_passive.sharpe_diff, paired_passive.ci_lo, paired_passive.ci_hi, paired_passive.excludes_zero,
        paired_hks.sharpe_diff, paired_hks.ci_lo, paired_hks.ci_hi, paired_hks.excludes_zero,
    )

    # Categorical table v1
    table_rows, archetype_train_checksum, test_archetype_ids = _build_categorical_table_v1(
        train, test, _STAGE1_ARCHETYPE_K,
    )

    # Brier vs climatological prior
    p_clim = float((train_y > 0).mean())
    bs_model, bs_clim, bss = _brier_score_components(y_pred, y_actual, p_clim)
    _log.info(
        "[%s] BSS=%.4f (BS_model=%.4f, BS_clim=%.4f, p_clim=%.4f)",
        symbol, bss, bs_model, bs_clim, p_clim,
    )

    # Predictions DataFrame for parquet
    predictions = test.with_columns(
        pl.Series("y_pred", y_pred),
        pl.Series("strategy_return", strat_returns),
        pl.Series("archetype_id", test_archetype_ids.astype(np.int32)),
    )

    result = Stage1Result(
        symbol=symbol,
        n_train=len(train),
        n_test=len(test),
        ols_intercept=intercept,
        ols_coefs=coefs,
        strategy_sharpe=strat_sharpe,
        passive_long_sharpe=passive_sharpe,
        paired_diff=paired_passive,
        archetype_rule_K=_STAGE1_ARCHETYPE_K,
        archetype_train_panel_checksum=archetype_train_checksum,
        categorical_table=table_rows,
        brier_score_model=bs_model,
        brier_score_clim=bs_clim,
        bss=bss,
        hks_benchmark_sharpe=hks_sharpe,
        paired_diff_vs_hks=paired_hks,
    )
    return result, predictions


# ---------------------------------------------------------------------------
# Sidecar + git_head
# ---------------------------------------------------------------------------


def _git_head() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ProjectPaths.discover().root,
            stderr=subprocess.DEVNULL, timeout=5,
        )
        return out.decode("ascii").strip()
    except Exception:
        return None


def _check_blas_thread_pinning() -> None:
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        val = os.environ.get(var)
        if val != "1":
            _log.warning(
                "BLAS thread-pinning contract (ADR-0009) violation: %s=%r "
                "(expected '1'). Sharpe values may be non-deterministic.",
                var, val,
            )


def _write_sidecar(
    results: list[Stage1Result],
    out_path: Path,
    substrate_path: str,
    substrate_checksum: str,
    git_head: str | None,
    run_id: str,
) -> tuple[Path, str, str]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scientific_payload = {
        "version": "1.0",
        "method": (
            "H053 Stage-1 mediator-only walk-forward: OLS on M_{i,t} → "
            "y_{i,t} = log(C(10:30 ET) / C(09:45 ET)); train 2015-2022 IS, "
            "test 2024-2025 OOS (per-instrument); paired Sharpe-differential "
            "vs passive-long + HKS benchmarks; categorical-table v1"
        ),
        "method_reference": (
            "design.md §1, §3.4, §4.5.3, §6, §8; "
            "Gao-Han-Li-Zhou 2018 doi:10.1016/j.jfineco.2018.05.009; "
            "Lo 2002 doi:10.2469/faj.v58.n4.2453; "
            "Ledoit-Wolf 2008 doi:10.1016/j.jempfin.2008.03.002; "
            "Heston-Korajczyk-Sadka 2010 doi:10.1111/j.1540-6261.2010.01573.x"
        ),
        "substrate_path": substrate_path,
        "substrate_dataset_checksum": substrate_checksum,
        "is_window": [_IS_START.isoformat(), _IS_END.isoformat()],
        "oos_window": [
            _OOS_START.isoformat(),
            f"per-instrument: ES={_OOS_END_ES.isoformat()}, NQ={_OOS_END_NQ.isoformat()}",
        ],
        "stage1_archetype_K": _STAGE1_ARCHETYPE_K,
        "stage1_bootstrap_block_len": _STAGE1_BOOTSTRAP_BLOCK_LEN,
        "stage1_bootstrap_n_rep": _STAGE1_BOOTSTRAP_NREP,
        "stage1_rng_seed": _STAGE1_RNG_SEED,
        "results": [r.to_dict() for r in results],
    }
    scientific_bytes = json.dumps(scientific_payload, indent=2, sort_keys=True).encode("utf-8")
    scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
    payload = {
        "h053_stage1_mediator_only": scientific_payload,
        "_meta": {
            "written_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "run_id": run_id,
            "git_head": git_head,
            "scientific_payload_sha256": scientific_sha,
        },
    }
    serialised = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    tmp = out_path.with_suffix(".json.tmp")
    with tmp.open("wb") as fh:
        fh.write(serialised)
    os.replace(tmp, out_path)
    file_sha = hashlib.sha256(serialised).hexdigest()
    return out_path, file_sha, scientific_sha


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="H053 Cycle 8 Stage-1 — mediator-only walk-forward."
    )
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--symbols", default="ES,NQ")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)

    _check_blas_thread_pinning()
    substrate_root = _resolve_substrate_path(args.substrate_path)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    paths = ProjectPaths.discover()
    run_id = args.run_id or f"h053_stage1_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir = paths.root / "runs" / "h053" / "stage1" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    _log.info("Computing substrate dataset checksum …")
    substrate_checksum = _substrate_dataset_checksum(substrate_root, symbols)
    _log.info("substrate_dataset_checksum=%s", substrate_checksum)
    git_head = _git_head()
    if git_head:
        _log.info("git HEAD=%s", git_head)

    results: list[Stage1Result] = []
    all_predictions: list[pl.DataFrame] = []
    for sym in symbols:
        oos_end = _OOS_END_ES if sym == "ES" else _OOS_END_NQ
        try:
            r, preds = _run_for_symbol(substrate_root, sym, oos_end)
            results.append(r)
            all_predictions.append(preds.with_columns(pl.lit(sym).alias("symbol_tag")))
        except Exception as exc:
            _log.exception("Symbol %s failed: %s", sym, exc)
            raise

    sidecar_path = run_dir / "sidecar.json"
    sidecar_path, file_sha, scientific_sha = _write_sidecar(
        results, sidecar_path,
        str(substrate_root), substrate_checksum, git_head, run_id,
    )
    _log.info("Sidecar: %s", sidecar_path)
    _log.info("File SHA256: %s", file_sha)
    _log.info("Scientific-payload SHA256: %s", scientific_sha)

    # Predictions parquet (per-symbol concat)
    if all_predictions:
        all_preds_df = pl.concat(all_predictions, how="vertical_relaxed")
        preds_path = run_dir / "predictions.parquet"
        all_preds_df.write_parquet(preds_path)
        _log.info("Predictions: %s (%d rows)", preds_path, len(all_preds_df))

    return 0


if __name__ == "__main__":
    sys.exit(main())
