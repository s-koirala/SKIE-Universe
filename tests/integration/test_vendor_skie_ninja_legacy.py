"""Integration test: vendor_skie_ninja_legacy ES 5-min parquet.

Gated on the local parquet existing (machine-local, skip if absent).
Asserts the schema + row/column count + timezone contract advertised
in the audit trail and provenance sidecar. Catches silent corruption
of the imported Databento-derived artifact before modeling code fails.

Also implements a permutation-shift leakage check as a partial
verification surrogate for the "positive-lag only" claim in the sibling
repo, per CLAUDE.md §Verification. Full re-derivation from raw 1-min
remains a separate follow-up.
"""

from __future__ import annotations

import json

import polars as pl
import pytest

from skie_ninja.utils.paths import ProjectPaths

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def parquet_path():
    paths = ProjectPaths.discover()
    p = paths.shared_vendor_skie_ninja_legacy / "es_5min_features_2020_2025.parquet"
    if not p.exists():
        pytest.skip(
            f"Vendor parquet not present at {p}; this test is machine-local only."
        )
    return p


@pytest.fixture(scope="module")
def sidecar(parquet_path):
    sc = parquet_path.parent / "es_5min_features_2020_2025.provenance.json"
    if not sc.exists():
        pytest.skip(f"Provenance sidecar not present at {sc}.")
    return json.loads(sc.read_text(encoding="utf-8"))


def test_row_and_column_count_match_sidecar(parquet_path, sidecar) -> None:
    df = pl.read_parquet(parquet_path)
    assert df.height == sidecar["rows"], (
        f"row count {df.height} != sidecar {sidecar['rows']}"
    )
    assert df.width == sidecar["columns"], (
        f"column count {df.width} != sidecar {sidecar['columns']}"
    )


def test_ts_event_is_utc_tz_aware(parquet_path) -> None:
    df = pl.read_parquet(parquet_path, columns=["ts_event"])
    dtype = df.schema["ts_event"]
    assert isinstance(dtype, pl.Datetime), f"expected Datetime, got {dtype}"
    assert dtype.time_zone == "UTC", (
        f"ts_event must be UTC-tz-aware, got time_zone={dtype.time_zone!r}"
    )


def test_timestamp_range_matches_sidecar(parquet_path, sidecar) -> None:
    df = pl.read_parquet(parquet_path, columns=["ts_event"])
    ts_min, ts_max = df["ts_event"].min(), df["ts_event"].max()
    sidecar_min, sidecar_max = sidecar["timestamp_range_utc"]
    # Tolerate ISO-format variants by comparing ISO strings.
    assert ts_min.isoformat() == sidecar_min, f"min {ts_min.isoformat()} != {sidecar_min}"
    assert ts_max.isoformat() == sidecar_max, f"max {ts_max.isoformat()} != {sidecar_max}"


def test_tier_is_prototype_and_not_evidence_bar(sidecar) -> None:
    # Machine-checkable guard: downstream evidence-bar runners can key on
    # evidence_bar_eligible == False to refuse this dataset. Keeps the
    # constraint out of free-text doc-only enforcement.
    assert sidecar["tier"] == "prototype"
    assert sidecar["evidence_bar_eligible"] is False


def test_source_and_dest_sha256_match(sidecar) -> None:
    # Copy-integrity was asserted at import time; sidecar records both
    # independently. If they ever diverge, bytes have been tampered with.
    assert sidecar["source_sha256"] == sidecar["dest_sha256"], (
        "source vs dest SHA256 diverged — copy corruption or post-copy tamper"
    )


def test_positive_lag_leakage_regression(parquet_path) -> None:
    """Permutation-shift leakage surrogate.

    Shift a candidate feature forward by +1 bar (leak the future into
    the present) and confirm its correlation with next-bar return
    *increases* vs. the baseline. If no increase is observed, either
    the feature has no next-bar signal at all (uninformative) or the
    baseline is already leaking; fail loud. The stronger guarantee
    (bitwise re-derivation) is deferred to post raw-1-min import.
    """
    df = pl.read_parquet(
        parquet_path, columns=["ts_event", "close", "return_lag1", "momentum_5"]
    ).sort("ts_event")

    fwd_ret = (pl.col("close").shift(-1) / pl.col("close") - 1).alias("fwd_ret")
    df = df.with_columns(fwd_ret).drop_nulls()

    # Baseline: lag-1 return vs next-bar return (should be weakly correlated).
    baseline = df.select(pl.corr("return_lag1", "fwd_ret")).item()

    # Leaky: shift the feature by +1 bar (so row t carries row t+1's feature).
    leaky = df.with_columns(pl.col("return_lag1").shift(-1).alias("leaky")).drop_nulls()
    leaky_corr = leaky.select(pl.corr("leaky", "fwd_ret")).item()

    # Leaky correlation must exceed baseline by a material margin; if not,
    # either the test setup is wrong or the baseline is already carrying
    # forward information.
    assert abs(leaky_corr) > abs(baseline) + 0.01, (
        f"permutation-shift test did not detect a leak signal: "
        f"baseline={baseline:.4f}, leaky={leaky_corr:.4f}. "
        f"Either the feature carries no next-bar signal at all, or the "
        f"baseline is already leaking (which would contradict the "
        f"sibling repo's positive-lag QC)."
    )
