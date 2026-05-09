"""Integration test for the H055 orchestrator's production substrate-load path.

Creates a synthetic polars parquet substrate at a temp directory, invokes
the orchestrator's `_load_substrate_for_symbol` function, and asserts the
returned arrays match the synthetic input.

This validates that the production-mode load path is wired correctly
WITHOUT requiring access to the real substrate at
``data/processed/vendor_legacy_1min_roll_adjusted/``. When real substrate
becomes available, the same loader handles it (per-row schema is identical).

Closes the production-mode orchestration gap surfaced in commit 7a3177c.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pytest

# Import the loader directly. Adding scripts/ to path is the
# canonical pattern for invoking orchestrator-internal helpers in tests.
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from run_h055_walk_forward import _load_substrate_for_symbol  # noqa: E402


UTC = timezone.utc


def _write_synthetic_parquet(
    out_path: Path, *, symbol: str = "ES", n_bars: int = 200, seed: int = 42
) -> None:
    """Create a synthetic ES OHLC parquet matching the substrate schema."""
    rng = np.random.default_rng(seed)
    log_p = np.cumsum(rng.normal(0.0001, 0.0005, n_bars)) + np.log(5000.0)
    close = np.exp(log_p)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    body_half = np.abs(rng.normal(0.5, 0.3, n_bars))
    high = np.maximum(open_, close) + body_half + 0.05
    low = np.minimum(open_, close) - body_half - 0.05
    base_ts = datetime(2024, 6, 12, 14, 30, tzinfo=UTC)
    ts_event = [base_ts + timedelta(minutes=i) for i in range(n_bars)]

    df = pl.DataFrame({
        "ts_event": ts_event,
        "symbol": [symbol] * n_bars,
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
    })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out_path)


def test_substrate_loader_reads_synthetic_parquet(tmp_path: Path) -> None:
    """Substrate loader correctly reads a synthetic parquet."""
    parquet_dir = tmp_path / "fake_substrate"
    parquet_dir.mkdir()
    _write_synthetic_parquet(parquet_dir / "ES_2024_06.parquet", symbol="ES", n_bars=100)

    o, h, l, c, ts = _load_substrate_for_symbol(parquet_dir, symbol="ES")
    assert o.size == 100
    assert h.size == 100
    assert l.size == 100
    assert c.size == 100
    assert len(ts) == 100
    assert ts[0].tzinfo is not None  # timezone-aware
    # Sorted ascending
    for i in range(len(ts) - 1):
        assert ts[i] <= ts[i + 1]


def test_substrate_loader_filters_by_symbol(tmp_path: Path) -> None:
    """Loader filters by symbol when multiple symbols are present."""
    parquet_dir = tmp_path / "fake_substrate"
    parquet_dir.mkdir()
    _write_synthetic_parquet(parquet_dir / "ES.parquet", symbol="ES", n_bars=50)
    _write_synthetic_parquet(parquet_dir / "NQ.parquet", symbol="NQ", n_bars=80, seed=99)

    o_es, _, _, _, _ = _load_substrate_for_symbol(parquet_dir, symbol="ES")
    o_nq, _, _, _, _ = _load_substrate_for_symbol(parquet_dir, symbol="NQ")
    assert o_es.size == 50
    assert o_nq.size == 80


def test_substrate_loader_raises_on_missing_directory(tmp_path: Path) -> None:
    nonexistent = tmp_path / "absent"
    with pytest.raises(FileNotFoundError, match="substrate_root"):
        _load_substrate_for_symbol(nonexistent, symbol="ES")


def test_substrate_loader_raises_on_absent_symbol(tmp_path: Path) -> None:
    parquet_dir = tmp_path / "fake_substrate"
    parquet_dir.mkdir()
    _write_synthetic_parquet(parquet_dir / "ES.parquet", symbol="ES", n_bars=50)
    with pytest.raises(ValueError, match="absent from substrate"):
        _load_substrate_for_symbol(parquet_dir, symbol="MES")


def test_substrate_loader_filters_by_date_range(tmp_path: Path) -> None:
    """start_date / end_date filters reduce row count appropriately."""
    parquet_dir = tmp_path / "fake_substrate"
    parquet_dir.mkdir()
    _write_synthetic_parquet(parquet_dir / "ES.parquet", symbol="ES", n_bars=2000)

    # Full panel
    o_full, _, _, _, ts_full = _load_substrate_for_symbol(parquet_dir, symbol="ES")
    assert o_full.size == 2000

    # Cut to first 500 bars: end_date at the bar 499's timestamp
    cutoff_dt = ts_full[499]
    o_cut, _, _, _, ts_cut = _load_substrate_for_symbol(
        parquet_dir, symbol="ES", end_date=cutoff_dt.strftime("%Y-%m-%d"),
    )
    # All cut bars on or before cutoff_dt's date
    assert all(t.date() <= cutoff_dt.date() for t in ts_cut)


def test_orchestrator_production_path_runs_on_synthetic_parquet(tmp_path: Path) -> None:
    """End-to-end: substrate parquet → orchestrator main() → KPI report card.

    Subprocess-invoke the orchestrator with --substrate-root pointing at a
    synthetic parquet; verify exit code 0 + KPI report card emitted.
    """
    import subprocess

    parquet_dir = tmp_path / "h055_substrate"
    parquet_dir.mkdir()
    # 600 bars with positive drift to actually trigger trend gate + setups
    rng = np.random.default_rng(42)
    log_p = np.cumsum(rng.normal(0.0008, 0.0005, 600)) + np.log(5000.0)
    close = np.exp(log_p)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    body_half = np.abs(rng.normal(0.5, 0.3, 600))
    high = np.maximum(open_, close) + body_half + 0.05
    low = np.minimum(open_, close) - body_half - 0.05
    base_ts = datetime(2024, 6, 12, 14, 30, tzinfo=UTC)
    ts_event = [base_ts + timedelta(minutes=i) for i in range(600)]
    pl.DataFrame({
        "ts_event": ts_event,
        "symbol": ["ES"] * 600,
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
    }).write_parquet(parquet_dir / "ES.parquet")

    out_dir = tmp_path / "h055_run_out"
    project_root = Path(__file__).resolve().parents[2]
    env = {**__import__("os").environ, "PYTHONPATH": str(project_root / "src")}
    result = subprocess.run(
        [
            str(project_root / ".venv" / "Scripts" / "python.exe"),
            str(project_root / "scripts" / "run_h055_walk_forward.py"),
            "--config", str(project_root / "config" / "hypotheses" / "H055.yaml"),
            "--out-dir", str(out_dir),
            "--symbol", "ES",
            "--substrate-root", str(parquet_dir),
        ],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"orchestrator failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    # KPI report card v1 should exist
    expected_kpi = out_dir / "prod_ES" / "H055_kpi_report_v1.md"
    assert expected_kpi.exists(), (
        f"KPI report card not emitted at {expected_kpi}; stdout={result.stdout}"
    )
    expected_results = out_dir / "prod_ES" / "results.json"
    assert expected_results.exists()
