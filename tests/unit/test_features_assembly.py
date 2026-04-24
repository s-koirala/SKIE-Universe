"""Purge-enforcement tests for :mod:`skie_ninja.features.assembly`."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

from skie_ninja.features.assembly import (
    apply_purge_and_partition,
    assemble_feature_matrix,
)
from skie_ninja.features.microstructure.rv_parkinson import RvParkinson


def _panel(n: int = 200, seed: int = 42) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2025-01-02", periods=n, freq="1min", tz="UTC")
    r = rng.normal(0, 0.001, n)
    close = 100.0 * np.exp(np.cumsum(r))
    open_ = np.concatenate([[close[0]], close[:-1]])
    wing = np.abs(rng.normal(0, 0.0005, n))
    high = np.maximum(open_, close) * (1.0 + wing)
    low = np.minimum(open_, close) * (1.0 - wing)
    vol = rng.integers(100, 1000, n).astype(np.int64)
    return pl.DataFrame(
        {
            "ts_event": ts,
            "symbol": ["ES"] * n,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": vol,
        }
    )


def test_assemble_writes_provenance(tmp_path: Path) -> None:
    panel = _panel()
    mod = RvParkinson(window_bars=20)
    features_dir = tmp_path / "features"
    now = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
    frame, prov = assemble_feature_matrix(
        modules=[mod],
        panel=panel.lazy(),
        now=now,
        run_id="test_run_id",
        features_dir=features_dir,
    )
    assert len(prov) == 1
    assert prov[0].name == "rv_parkinson"
    expected_json = features_dir / "rv_parkinson_1.0_test_run_id.json"
    assert expected_json.is_file()
    assert "rv_parkinson@1.0" in frame.columns


def test_apply_purge_rejects_violating_train_rows() -> None:
    n = 50
    frame = pl.DataFrame(
        {
            "_row_idx": list(range(n)),
            "feature": list(range(n)),
        }
    )
    # Purge window [20, 30). A training index inside that window must
    # be refused.
    train_idx = list(range(0, 25))  # rows 20..24 are inside the purge
    test_idx = list(range(30, 40))
    with pytest.raises(AssertionError, match="purge window"):
        apply_purge_and_partition(
            feature_matrix=frame,
            fold_purge_start=20,
            fold_purge_end=30,
            train_indices=train_idx,
            test_indices=test_idx,
        )


def test_apply_purge_accepts_clean_split() -> None:
    n = 50
    frame = pl.DataFrame(
        {
            "_row_idx": list(range(n)),
            "feature": list(range(n)),
        }
    )
    train_idx = list(range(0, 20))
    test_idx = list(range(30, 40))
    train_frame, test_frame = apply_purge_and_partition(
        feature_matrix=frame,
        fold_purge_start=20,
        fold_purge_end=30,
        train_indices=train_idx,
        test_indices=test_idx,
    )
    assert train_frame.shape[0] == 20
    assert test_frame.shape[0] == 10
    assert train_frame.get_column("_row_idx").to_list() == list(range(20))


def test_assemble_raises_on_empty_modules() -> None:
    panel = _panel(n=10)
    with pytest.raises(ValueError, match="empty"):
        assemble_feature_matrix(
            modules=[],
            panel=panel.lazy(),
            now=pd.Timestamp("2025-01-02", tz="UTC"),
            run_id="x",
            features_dir=Path("/tmp"),
        )
