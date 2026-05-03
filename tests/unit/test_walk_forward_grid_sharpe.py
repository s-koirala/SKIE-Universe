"""Tests for src/skie_ninja/backtest/walk_forward_grid_sharpe.py per plan v3-r3 §A."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.backtest.walk_forward_grid_sharpe import (
    DEFAULT_MODES,
    DEFAULT_W_TEST,
    DEFAULT_W_TRAIN_GRID,
    build_grid_cells,
    build_sensitivity_curve,
    build_spa_loss_matrix,
    evaluate_cell,
    pairwise_lw2008_cis,
    run_walk_forward_grid,
)


@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def synthetic_panel(rng):
    """Synthetic panel large enough for walk-forward evaluation."""
    n = 1500
    X = rng.normal(size=(n, 3))
    # weak signal: y = 0.1 * X[:, 0] + noise
    y = 0.1 * X[:, 0] + rng.normal(scale=0.5, size=n)
    return X, y


class TestDefaultGridConfiguration:
    """Per plan v3-r3 §A: 8-point geometric grid with floor=15·k=15·42=630, ceiling=1122."""

    def test_default_grid_is_8_points(self):
        assert len(DEFAULT_W_TRAIN_GRID) == 8

    def test_default_grid_floor_is_630(self):
        assert DEFAULT_W_TRAIN_GRID[0] == 630

    def test_default_grid_ceiling_is_1122(self):
        assert DEFAULT_W_TRAIN_GRID[-1] == 1122

    def test_default_grid_strictly_increasing(self):
        for i in range(len(DEFAULT_W_TRAIN_GRID) - 1):
            assert DEFAULT_W_TRAIN_GRID[i] < DEFAULT_W_TRAIN_GRID[i + 1]

    def test_default_w_test_is_63_sessions(self):
        # Per plan v3-r3 §A row "W_test = step_size": ~3 trading months
        assert DEFAULT_W_TEST == 63

    def test_default_modes_includes_both_rolling_and_expanding(self):
        assert "rolling" in DEFAULT_MODES
        assert "expanding" in DEFAULT_MODES


class TestBuildGridCells:
    def test_cross_product_size_is_8x2(self):
        cells = build_grid_cells()
        assert len(cells) == 16

    def test_cell_ids_unique(self):
        cells = build_grid_cells()
        assert len({c.cell_id for c in cells}) == 16

    def test_cell_ids_format(self):
        cells = build_grid_cells()
        assert all("_" in c.cell_id and (c.cell_id.endswith("_rolling") or c.cell_id.endswith("_expanding")) for c in cells)


class TestEvaluateCell:
    def test_synthetic_signal_recovers_positive_sharpe(self, synthetic_panel, rng):
        X, y = synthetic_panel
        local_rng = np.random.default_rng(123)

        def fit_predict(X_train, y_train, X_test, y_test, fold_id, w_train):
            beta = np.linalg.lstsq(X_train, y_train, rcond=None)[0]
            y_pred = X_test @ beta
            # synthetic noisy positive-mean returns so sigma > 0 and Sharpe is well-defined
            arm = 0.001 + local_rng.normal(scale=0.0005, size=len(X_test))
            bench = local_rng.normal(scale=0.0005, size=len(X_test))
            return arm, bench

        cells = build_grid_cells(w_train_grid=(800,), modes=("rolling",))
        result = evaluate_cell(
            cell=cells[0],
            X=X,
            y=y,
            fit_predict=fit_predict,
            label_horizon=1,
            embargo=0,
            w_test=63,
        )
        assert result.n_oos > 0
        assert result.sharpe_point > 0  # noisy positive returns: positive Sharpe
        assert len(result.arm_returns) == result.n_oos

    def test_insufficient_data_returns_nan_sharpe(self):
        n = 100
        X = np.zeros((n, 2))
        y = np.zeros(n)
        cells = build_grid_cells(w_train_grid=(500,), modes=("rolling",))
        result = evaluate_cell(
            cell=cells[0],
            X=X,
            y=y,
            fit_predict=lambda X_tr, y_tr, X_te, y_te, fid, wt: (np.array([]), np.array([])),
            w_test=63,
        )
        assert np.isnan(result.sharpe_point)
        assert result.n_oos == 0


class TestSensitivityCurve:
    def test_returns_per_w_train_aggregate(self, synthetic_panel, rng):
        X, y = synthetic_panel

        def fit_predict(X_train, y_train, X_test, fold_id, w_train):
            return np.full(len(X_test), 0.001), np.full(len(X_test), 0.0)

        from skie_ninja.backtest.walk_forward_grid_sharpe import CellResult, CellSpec
        results = tuple(
            CellResult(
                cell=CellSpec(cell_id=f"w{w}_rolling", w_train=w, mode="rolling"),
                n_oos=100,
                sharpe_point=float(w / 1000.0),
                sharpe_se=0.1,
                arm_returns=np.full(100, 0.001),
                benchmark_returns=np.zeros(100),
            )
            for w in (630, 743, 876, 1033)
        )
        curve = build_sensitivity_curve(results, mode_filter="rolling")
        assert curve.w_train_values == (630, 743, 876, 1033)
        assert curve.sharpe_means[0] == pytest.approx(0.630)
        assert curve.sharpe_means[-1] == pytest.approx(1.033)


class TestSPALossMatrix:
    def test_stack_construction(self):
        from skie_ninja.backtest.walk_forward_grid_sharpe import CellResult, CellSpec
        cells = tuple(
            CellResult(
                cell=CellSpec(cell_id=f"w{w}_rolling", w_train=w, mode="rolling"),
                n_oos=50,
                sharpe_point=0.1,
                sharpe_se=0.05,
                arm_returns=np.ones(50) * (w / 1000),
                benchmark_returns=np.zeros(50),
            )
            for w in (630, 743)
        )
        M, ids = build_spa_loss_matrix(cells)
        assert M.shape == (50, 2)
        assert ids == ("w630_rolling", "w743_rolling")
        # Loss = -arm_returns; smaller W_train has larger loss
        assert np.all(M[:, 0] > M[:, 1])
