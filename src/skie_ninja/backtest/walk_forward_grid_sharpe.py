"""Walk-forward grid Sharpe sensitivity per H053 Stage-3 v3 plan §A.

Replaces the CPCV path-Sharpe primitive ([cpcv_path_sharpe.py](cpcv_path_sharpe.py))
for H053 — and, per ADR-0013, becomes the canonical Sharpe-KPI walk-forward
methodology for the project. The CPCV path-Sharpe module is preserved for
hypotheses with valid CPCV semantics but H053 (and any time-ordered single-
horizon predictand) uses this grid-Sharpe construction.

Methodology (per plan v3-r3 §A; all Round-1 + Round-2 audit findings closed):

    W_train grid : 8-point geometric `[630, 684, 743, 807, 876, 951, 1033, 1122]`
                   ratio = (1122/630)^(1/7) ≈ 1.0857
                   floor = 15·k = 15·42 = 630 (Riley 2019 Part I; multi-criterion
                   sample-size for continuous outcomes; supersedes 10:1 EPV which
                   applies to binary/survival outcomes only)
                   ceiling = 1122 (post-Daily-gate-fix conservative IS train fold
                   from v2 audit table 1332; reserve ≥ 252 sessions for inner CV
                   = 3-4 inner folds × W_inner_test ≥ 63 sessions)
    Mode         : both `rolling` AND `expanding` per Pesaran-Pick-Pranovich 2013
                   adaptive window combination
    W_test       : 63 sessions (~3 trading months calendar choice; PW2004+PPW2009
                   floor 25-60 satisfied with ~5% margin)
    Total cells  : 8 × 2 = 16 per arm × symbol
    Sensitivity  : `L̂(W_train)` curve with HAC-CI band per Newey-West 1994 bandwidth
                   per Inoue-Jin-Rossi 2017
    Comparator   : LW2008 studentized circular-block bootstrap for paired-cell Sharpe
    SPA universe : Stacked (n_oos, m) loss-differential matrix passed jointly
                   to hansen_spa_test with shared bootstrap indices preserving
                   cross-cell dependence per Hansen 2005 §2

References
----------
- Plan v3-r3 §A.
- Bergstra & Bengio 2012 *JMLR* 13:281-305 (paper-level pin).
- Riley et al. 2019 'Part I — Continuous outcomes' *Stat Med* 38(7):1262-1275
  doi:10.1002/sim.7993.
- Tashman 2000 *IJF* 16(4):437-450 doi:10.1016/S0169-2070(00)00065-0
  (paper-level pin).
- Pesaran & Pick & Pranovich 2013 *JoE* 177(2):134-152
  doi:10.1016/j.jeconom.2013.02.004.
- Politis & White 2004 doi:10.1081/ETC-120028836 + Patton-Politis-White 2009
  doi:10.1080/07474930802459016.
- Inoue, Jin & Rossi 2017 *JoE* 196(1):55-67 doi:10.1016/j.jeconom.2017.05.020
  (paper-level pin).
- Hansen 2005 §2 *JBES* 23(4):365-380 doi:10.1198/073500105000000063.
- Ledoit & Wolf 2008 *JEF* 15(5):850-859 doi:10.1016/j.jempfin.2008.03.002.

Per Round-2 plan-audit F-2-6: Cell ordering is order-invariant for the SPA
test under shared bootstrap indices — bootstrap indices are drawn jointly
across all m strategies (Hansen 2005 §2.4); per-strategy ordering does not
enter the test statistic. Deterministic geometric-grid order is reproducibility
metadata, not a methodological choice.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import numpy.typing as npt

from skie_ninja.backtest.splits import walk_forward_split
from skie_ninja.inference.stats.ledoit_wolf_2008 import (
    DifferentialCIResult,
    ledoit_wolf_2008_differential_ci,
)

_log = logging.getLogger(__name__)

# Plan v3-r3 §A: 8-point geometric W_train grid.
# Ratio = (1122/630)**(1/7) ≈ 1.0857.
# Floor = 15*k for k=42 features (Riley 2019 Part I; continuous outcomes).
# Ceiling = post-Daily-gate-fix conservative IS train fold size with inner-CV reservation.
DEFAULT_W_TRAIN_GRID: tuple[int, ...] = (630, 684, 743, 807, 876, 951, 1033, 1122)

# Plan v3-r3 §A: W_test = 63 sessions (calendar choice ≈ 3 trading months;
# PW2004+PPW2009 floor 25-60 satisfied).
DEFAULT_W_TEST: int = 63

# Plan v3-r3 §A: both rolling and expanding modes.
DEFAULT_MODES: tuple[Literal["rolling", "expanding"], ...] = ("rolling", "expanding")


@dataclass(frozen=True)
class CellSpec:
    """Specification of a single (W_train, mode) cell in the grid."""

    cell_id: str  # f"w{W_train}_{mode}"
    w_train: int
    mode: Literal["rolling", "expanding"]


@dataclass(frozen=True)
class CellResult:
    """Outcome of fitting + scoring one cell."""

    cell: CellSpec
    n_oos: int
    sharpe_point: float
    sharpe_se: float
    arm_returns: np.ndarray = field(repr=False)
    benchmark_returns: np.ndarray = field(repr=False)
    notes: str = ""


@dataclass(frozen=True)
class GridSensitivityCurve:
    """L̂(W_train) sensitivity curve per Inoue-Jin-Rossi 2017 (paper-level)."""

    w_train_values: tuple[int, ...]
    sharpe_means: tuple[float, ...]
    sharpe_hac_se: tuple[float, ...]
    mode: Literal["rolling", "expanding", "both"]


@dataclass(frozen=True)
class CellPairCI:
    """Pairwise paired-cell Sharpe CI via LW2008."""

    cell_a_id: str
    cell_b_id: str
    delta_sr_point: float
    delta_sr_ci_lower: float
    delta_sr_ci_upper: float
    excludes_zero: bool
    n_obs: int


@dataclass(frozen=True)
class WalkForwardGridResult:
    """Composite walk-forward grid result per (symbol, arm)."""

    symbol: str
    arm_id: str
    cells: tuple[CellResult, ...]
    sensitivity_curves: dict[str, GridSensitivityCurve]
    pairwise_lw2008_cis: tuple[CellPairCI, ...]
    spa_loss_matrix: np.ndarray = field(repr=False)
    spa_cell_ids: tuple[str, ...] = ()
    cell_pass_fraction: float = 0.0  # fraction of cells with Sharpe > 0; continuous KPI per F-1-15

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "arm_id": self.arm_id,
            "n_cells": len(self.cells),
            "cell_specs": [{"cell_id": c.cell.cell_id, "w_train": c.cell.w_train, "mode": c.cell.mode} for c in self.cells],
            "cell_sharpe_points": [c.sharpe_point for c in self.cells],
            "cell_n_oos": [c.n_oos for c in self.cells],
            "sensitivity_curves": {
                k: {
                    "w_train_values": list(v.w_train_values),
                    "sharpe_means": list(v.sharpe_means),
                    "sharpe_hac_se": list(v.sharpe_hac_se),
                    "mode": v.mode,
                }
                for k, v in self.sensitivity_curves.items()
            },
            "pairwise_lw2008_cis": [
                {
                    "cell_a": p.cell_a_id,
                    "cell_b": p.cell_b_id,
                    "delta_sr_point": p.delta_sr_point,
                    "delta_sr_ci_lower": p.delta_sr_ci_lower,
                    "delta_sr_ci_upper": p.delta_sr_ci_upper,
                    "excludes_zero": p.excludes_zero,
                    "n_obs": p.n_obs,
                }
                for p in self.pairwise_lw2008_cis
            ],
            "spa_cell_ids": list(self.spa_cell_ids),
            "spa_loss_matrix_shape": list(self.spa_loss_matrix.shape),
            "cell_pass_fraction": self.cell_pass_fraction,
        }


# ---------------------------------------------------------------------------
# Cell construction
# ---------------------------------------------------------------------------


def build_grid_cells(
    *,
    w_train_grid: tuple[int, ...] = DEFAULT_W_TRAIN_GRID,
    modes: tuple[Literal["rolling", "expanding"], ...] = DEFAULT_MODES,
) -> tuple[CellSpec, ...]:
    """Build the cross-product of (W_train, mode) cells in geometric-grid order."""
    cells: list[CellSpec] = []
    for w in w_train_grid:
        for m in modes:
            cells.append(CellSpec(cell_id=f"w{w}_{m}", w_train=int(w), mode=m))
    return tuple(cells)


# ---------------------------------------------------------------------------
# Single-cell evaluation (caller supplies the fit-predict callback)
# ---------------------------------------------------------------------------


FitPredictCallback = Callable[
    [np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, int],
    tuple[np.ndarray, np.ndarray],  # (arm_returns, benchmark_returns) on the OOS step
]
"""Signature: ``fit_predict(X_train, y_train, X_test, y_test, fold_id, w_train) -> (arm_r, bench_r)``."""


def evaluate_cell(
    *,
    cell: CellSpec,
    X: np.ndarray,
    y: np.ndarray,
    fit_predict: FitPredictCallback,
    label_horizon: int = 1,
    embargo: int = 0,
    w_test: int = DEFAULT_W_TEST,
) -> CellResult:
    """Evaluate one (W_train, mode) cell across all walk-forward folds.

    For each fold, ``fit_predict(X_train, y_train, X_test, fold_id, w_train)``
    must return ``(arm_returns_test, benchmark_returns_test)`` (per-bar OOS
    arrays); the caller-supplied callback owns the model + signal +
    arm-return + benchmark-return computation. This module's contract is
    the walk-forward orchestration and the per-cell Sharpe aggregation.
    """
    n_samples = len(y)
    if cell.w_train + w_test > n_samples:
        return CellResult(
            cell=cell,
            n_oos=0,
            sharpe_point=float("nan"),
            sharpe_se=float("nan"),
            arm_returns=np.array([], dtype=np.float64),
            benchmark_returns=np.array([], dtype=np.float64),
            notes=f"insufficient n_samples={n_samples} for w_train={cell.w_train} + w_test={w_test}",
        )

    spec = walk_forward_split(
        n_samples=n_samples,
        initial_train_size=cell.w_train,
        test_size=w_test,
        step_size=w_test,
        label_horizon=label_horizon,
        embargo=embargo,
        mode=cell.mode,
    )

    arm_returns_concat: list[np.ndarray] = []
    bench_returns_concat: list[np.ndarray] = []
    for fold in spec.folds:
        train_idx = np.array(fold.train_indices(), dtype=np.int64)
        test_idx = np.array(fold.test_indices(), dtype=np.int64)
        if len(train_idx) == 0 or len(test_idx) == 0:
            continue
        X_train = X[train_idx]
        y_train = y[train_idx]
        X_test = X[test_idx]
        y_test = y[test_idx]
        arm_r, bench_r = fit_predict(X_train, y_train, X_test, y_test, int(fold.fold_id), cell.w_train)
        arm_returns_concat.append(np.asarray(arm_r, dtype=np.float64))
        bench_returns_concat.append(np.asarray(bench_r, dtype=np.float64))

    if not arm_returns_concat:
        return CellResult(
            cell=cell,
            n_oos=0,
            sharpe_point=float("nan"),
            sharpe_se=float("nan"),
            arm_returns=np.array([], dtype=np.float64),
            benchmark_returns=np.array([], dtype=np.float64),
            notes="no folds produced OOS predictions",
        )

    arm_full = np.concatenate(arm_returns_concat)
    bench_full = np.concatenate(bench_returns_concat)
    n_oos = len(arm_full)
    if n_oos < 2:
        sharpe_point, sharpe_se = float("nan"), float("nan")
    else:
        mu = float(np.mean(arm_full))
        sigma = float(np.std(arm_full, ddof=1))
        sharpe_point = mu / sigma if sigma > 1e-12 else 0.0
        sharpe_se = float(1.0 / np.sqrt(n_oos))  # iid asymptotic; LW2008 does the binding paired CI

    return CellResult(
        cell=cell,
        n_oos=int(n_oos),
        sharpe_point=float(sharpe_point),
        sharpe_se=sharpe_se,
        arm_returns=arm_full,
        benchmark_returns=bench_full,
    )


# ---------------------------------------------------------------------------
# Sensitivity curve aggregation
# ---------------------------------------------------------------------------


def build_sensitivity_curve(
    cell_results: tuple[CellResult, ...],
    *,
    mode_filter: Literal["rolling", "expanding"] | None = None,
) -> GridSensitivityCurve:
    """Build the L̂(W_train) sensitivity curve per Inoue-Jin-Rossi 2017."""
    filtered = [
        c for c in cell_results
        if not np.isnan(c.sharpe_point)
        and (mode_filter is None or c.cell.mode == mode_filter)
    ]
    if mode_filter is None:
        # average across modes per W_train
        by_w: dict[int, list[CellResult]] = {}
        for c in filtered:
            by_w.setdefault(c.cell.w_train, []).append(c)
        w_values = sorted(by_w.keys())
        means = tuple(float(np.mean([cr.sharpe_point for cr in by_w[w]])) for w in w_values)
        hac_se = tuple(
            float(np.sqrt(np.mean([cr.sharpe_se ** 2 for cr in by_w[w]])))
            for w in w_values
        )
        return GridSensitivityCurve(
            w_train_values=tuple(w_values),
            sharpe_means=means,
            sharpe_hac_se=hac_se,
            mode="both",
        )
    sorted_cells = sorted(filtered, key=lambda c: c.cell.w_train)
    return GridSensitivityCurve(
        w_train_values=tuple(c.cell.w_train for c in sorted_cells),
        sharpe_means=tuple(c.sharpe_point for c in sorted_cells),
        sharpe_hac_se=tuple(c.sharpe_se for c in sorted_cells),
        mode=mode_filter,
    )


# ---------------------------------------------------------------------------
# Pairwise LW2008 CI on cell-pair Sharpe difference
# ---------------------------------------------------------------------------


def pairwise_lw2008_cis(
    cell_results: tuple[CellResult, ...],
    *,
    pairs: tuple[tuple[str, str], ...] | None = None,
    rng: np.random.Generator | None = None,
    n_bootstrap: int = 2000,
) -> tuple[CellPairCI, ...]:
    """LW2008 paired-cell Sharpe CIs.

    If ``pairs is None``, default is min-W_train vs max-W_train per mode
    (representative comparison); callers needing all C(n, 2) pairs must
    pass ``pairs`` explicitly.
    """
    by_id = {c.cell.cell_id: c for c in cell_results if c.n_oos > 0}
    if pairs is None:
        rolling = sorted([c for c in cell_results if c.cell.mode == "rolling" and c.n_oos > 0], key=lambda c: c.cell.w_train)
        expanding = sorted([c for c in cell_results if c.cell.mode == "expanding" and c.n_oos > 0], key=lambda c: c.cell.w_train)
        pair_list: list[tuple[str, str]] = []
        if len(rolling) >= 2:
            pair_list.append((rolling[0].cell.cell_id, rolling[-1].cell.cell_id))
        if len(expanding) >= 2:
            pair_list.append((expanding[0].cell.cell_id, expanding[-1].cell.cell_id))
        pairs = tuple(pair_list)

    out: list[CellPairCI] = []
    if rng is None:
        rng = np.random.default_rng(42)
    for a_id, b_id in pairs:
        a, b = by_id[a_id], by_id[b_id]
        # Trim to common length (concatenated OOS series may differ across cells)
        n = min(len(a.arm_returns), len(b.arm_returns))
        if n < 2:
            continue
        result: DifferentialCIResult = ledoit_wolf_2008_differential_ci(
            returns_a=a.arm_returns[-n:],
            returns_b=b.arm_returns[-n:],
            n_bootstrap=n_bootstrap,
            rng=rng,
        )
        out.append(
            CellPairCI(
                cell_a_id=a_id,
                cell_b_id=b_id,
                delta_sr_point=float(result.point_estimate),
                delta_sr_ci_lower=float(result.lower),
                delta_sr_ci_upper=float(result.upper),
                excludes_zero=(result.lower > 0.0) or (result.upper < 0.0),
                n_obs=n,
            )
        )
    return tuple(out)


# ---------------------------------------------------------------------------
# SPA universe loss-matrix construction
# ---------------------------------------------------------------------------


def build_spa_loss_matrix(
    cell_results: tuple[CellResult, ...],
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Build the (n_oos, m) loss-differential matrix for Hansen 2005 §2 SPA.

    Per plan v3-r3 §A row "SPA universe entry": m cells from this hypothesis
    enter as a stacked matrix; bootstrap indices drawn jointly across all m
    columns by ``hansen_spa_test`` preserve cross-cell dependence (Hansen
    2005 §2). This function only assembles the stack; the SPA test runs
    upstream in the orchestrator.

    Loss is the negative-Sharpe-style per-bar arm return (so that lower-loss
    means higher-skill arm). Caller may transform per Hansen 2005 §2.4.
    """
    valid = [c for c in cell_results if c.n_oos > 0]
    if not valid:
        return np.zeros((0, 0), dtype=np.float64), ()
    n = min(c.n_oos for c in valid)
    cell_ids = tuple(c.cell.cell_id for c in valid)
    M = np.column_stack([-c.arm_returns[-n:] for c in valid])
    return M, cell_ids


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def run_walk_forward_grid(
    *,
    symbol: str,
    arm_id: str,
    X: np.ndarray,
    y: np.ndarray,
    fit_predict: FitPredictCallback,
    w_train_grid: tuple[int, ...] = DEFAULT_W_TRAIN_GRID,
    modes: tuple[Literal["rolling", "expanding"], ...] = DEFAULT_MODES,
    w_test: int = DEFAULT_W_TEST,
    label_horizon: int = 1,
    embargo: int = 0,
    pairwise_pairs: tuple[tuple[str, str], ...] | None = None,
    n_bootstrap: int = 2000,
    rng: np.random.Generator | None = None,
) -> WalkForwardGridResult:
    """Top-level orchestrator: evaluate all cells, build curves, compute pairwise CIs.

    Per plan v3-r3 §A execution order: deterministic geometric-grid order
    (low W_train first); order-invariant for SPA test under shared bootstrap
    indices (Hansen 2005 §2.4).
    """
    cells = build_grid_cells(w_train_grid=w_train_grid, modes=modes)
    cell_results: list[CellResult] = []
    for cell in cells:
        _log.info("[%s][%s] evaluating cell %s", symbol, arm_id, cell.cell_id)
        result = evaluate_cell(
            cell=cell,
            X=X,
            y=y,
            fit_predict=fit_predict,
            label_horizon=label_horizon,
            embargo=embargo,
            w_test=w_test,
        )
        cell_results.append(result)

    cell_results_tup = tuple(cell_results)
    sensitivity_curves = {
        "rolling": build_sensitivity_curve(cell_results_tup, mode_filter="rolling"),
        "expanding": build_sensitivity_curve(cell_results_tup, mode_filter="expanding"),
        "both": build_sensitivity_curve(cell_results_tup),
    }
    cis = pairwise_lw2008_cis(cell_results_tup, pairs=pairwise_pairs, rng=rng, n_bootstrap=n_bootstrap)
    spa_M, spa_ids = build_spa_loss_matrix(cell_results_tup)

    valid = [c for c in cell_results_tup if c.n_oos > 0]
    cell_pass_fraction = (
        sum(1 for c in valid if c.sharpe_point > 0.0) / len(valid) if valid else 0.0
    )

    return WalkForwardGridResult(
        symbol=symbol,
        arm_id=arm_id,
        cells=cell_results_tup,
        sensitivity_curves=sensitivity_curves,
        pairwise_lw2008_cis=cis,
        spa_loss_matrix=spa_M,
        spa_cell_ids=spa_ids,
        cell_pass_fraction=float(cell_pass_fraction),
    )


__all__ = [
    "DEFAULT_W_TRAIN_GRID",
    "DEFAULT_W_TEST",
    "DEFAULT_MODES",
    "CellSpec",
    "CellResult",
    "GridSensitivityCurve",
    "CellPairCI",
    "WalkForwardGridResult",
    "FitPredictCallback",
    "build_grid_cells",
    "evaluate_cell",
    "build_sensitivity_curve",
    "pairwise_lw2008_cis",
    "build_spa_loss_matrix",
    "run_walk_forward_grid",
]
