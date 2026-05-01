"""H053 feature-factory PIT canaries — design.md §11.2 prereq 11 sub-clause c.

Wires the Cycle-4 leak-canary patterns from
[src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py)
specifically to the H053 feature factory blocks (A daily / B hourly /
C 5-15min / D mediator) plus the archetype classifier.

Three checks per design.md §3.0 + §3.6 + §11.2 prereq 11:

  (a) **Bar-set disjointness via input poisoning** (design.md §3.0 R5 + §3.6):
      The "bar set actually consumed by compute()" is observed by injecting
      sentinel values into all bars with ``ts_event > as_of``; if any output
      column carries a value derived from those sentinels, compute consumed
      a future bar. This is a faithful capability proxy adapted from
      [src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py)
      ``TracingArray`` to the Polars ``compute(panel, now)`` API shape.
      A naive set-disjointness check on the test author's own filter
      literals would be tautological (it would prove only that ``≤ x`` and
      ``> x`` are disjoint operators); the input-poisoning form measures
      the actual read-set of the compute pipeline.

  (b) **PIT-cutoff dual-fit invariance** (design.md §3.0 R5):
      ``compute(panel_truncated_at_now, now)`` ≡
      ``compute(panel_with_future_bars, now)`` to bit-exact equality
      on every output column. This is the H053 specialisation of the
      Cycle-4 dual-fit-call observer (the H053 ``compute(panel, now,
      ctx)`` API stands in for the Cycle-4 ``fit_fn(train_idx, X)``
      API).

  (c) **Boundary-anchor inclusion at exactly ``ts_event = 09:45 ET``**
      (design.md §3.0 R3-R4): the close of the 09:45 ET bar IS the
      mediator's ``C_{09:45}`` and IS in the feature set. A buggy
      implementation that excluded the boundary bar would pass dual-fit
      silently (both panels excluding the same bar) — this anchor-
      inclusion test catches that off-by-one mode.

Plus an adversarial leak-injection sub-suite that demonstrates the
canaries CATCH the failure modes documented in
[src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py)
``TracingArray`` threat model: trivial ``max(ts_event)`` leak, mean-of-
close leak (forgotten ``_pit_cutoff``), backward-fill leak.

Reference: design.md §11.2 prereq 11 sub-clause c verbatim binding to
the Cycle-4 dual-fit-call + TracingArray patterns from
[docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md](
../../docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import polars as pl
import pytest

from skie_ninja.features.h053 import (
    H053Daily,
    H053Hourly,
    H053Mediator,
    H053Microstructure5_15min,
    fit_archetype_rule,
)

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


# ---------------------------------------------------------------------------
# Multi-session synthetic panel builder
# ---------------------------------------------------------------------------


def _bar_ts_utc(session_date: pd.Timestamp, hh_et: int, mm_et: int) -> pd.Timestamp:
    et_dt = datetime.combine(session_date.date(), time(hh_et, mm_et), tzinfo=ET)
    return pd.Timestamp(et_dt).tz_convert(UTC)


def _make_full_session_panel(
    session_dates: list[pd.Timestamp],
    *,
    symbol: str = "ES",
    minutes_per_session: int = 60 * 24,
    # justify: deterministic test seed; value arbitrary, fixed for
    # reproducibility per CLAUDE.md §Reproducibility.
    seed: int = 42,
) -> pl.DataFrame:
    """Build a panel covering each session's full 24-hour 1-min grid.

    Synthetic OHLCV: open=close=mid, high=mid+0.25, low=mid-0.25, volume=100;
    mid drifts at +0.0001 per bar with small Gaussian noise.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for session_idx, sd in enumerate(session_dates):
        start_et = datetime.combine(sd.date(), time(0, 0), tzinfo=ET)
        for offset in range(minutes_per_session):
            bar_et = start_et + timedelta(minutes=offset)
            ts_utc = pd.Timestamp(bar_et).tz_convert(UTC)
            mid = 4500.0 + 100.0 * session_idx + 0.0001 * offset + rng.normal(0, 0.001)
            rows.append(
                {
                    "ts_event": ts_utc,
                    "symbol": symbol,
                    "open": float(mid),
                    "high": float(mid + 0.25),
                    "low": float(mid - 0.25),
                    "close": float(mid),
                    "volume": 100.0,
                }
            )
    df = pl.DataFrame(rows)
    df = df.with_columns(
        pl.col("ts_event").dt.replace_time_zone("UTC").cast(pl.Datetime("ns", "UTC"))
    )
    return df


def _poison_panel_after_cutoff(
    panel: pl.DataFrame,
    cutoff: pd.Timestamp,
) -> pl.DataFrame:
    """Replace OHLCV in every row with ``ts_event > cutoff`` with NaN.

    Per Round-2 quant-audit F-2-1: NaN-poison is a STRUCTURAL capability
    proxy — any compute() that reads a poisoned bar produces a NaN-bearing
    feature, which is dropped by the project-wide ``is_finite()`` filter
    on every H053 block's output. The downstream test asserts the
    poisoned-panel output row-count equals the truncated-panel output
    row-count; any post-cutoff read shows up as a row-count delta.

    This is structurally stronger than the Round-1 numeric-sentinel
    capability proxy (F-1-1), which was vulnerable to log-domain features
    (Daily, Hourly, Mediator log-returns) where ``log(99999999) ≈ 18.4``
    falls under any reasonable magnitude bound. NaN propagates through
    arithmetic regardless of feature codomain.

    Limitations (per Round-2 quant-audit F-2-2 / F-2-4):
    - **Block D mediator** does NOT consume any post-09:45 ET bar under
      any current implementation (the mediator-window filter restricts
      to 09:31-09:45 ET); the NaN-poison test there is structurally
      tautological — confirming this is documented in the test docstring.
    - ``ts_event`` of post-cutoff bars is NOT poisoned (dtype constraint;
      Polars Datetime("ns", "UTC") does not accept NaN). The dual-fit
      canary at ``TestPITCutoffDualFitInvariance`` is the load-bearing
      detector for ts_event-derived leaks (e.g., ``max(panel.ts_event)``).

    Cutoff semantics are inclusive (rows with ts_event == cutoff retain
    their original values; only ts_event > cutoff is poisoned), matching
    design.md §3.0 R5 inclusivity.
    """
    nan_lit = pl.lit(float("nan"))
    return panel.with_columns(
        pl.when(pl.col("ts_event") > cutoff)
        .then(nan_lit)
        .otherwise(pl.col("open"))
        .alias("open"),
        pl.when(pl.col("ts_event") > cutoff)
        .then(nan_lit)
        .otherwise(pl.col("high"))
        .alias("high"),
        pl.when(pl.col("ts_event") > cutoff)
        .then(nan_lit)
        .otherwise(pl.col("low"))
        .alias("low"),
        pl.when(pl.col("ts_event") > cutoff)
        .then(nan_lit)
        .otherwise(pl.col("close"))
        .alias("close"),
        pl.when(pl.col("ts_event") > cutoff)
        .then(nan_lit)
        .otherwise(pl.col("volume"))
        .alias("volume"),
    )


def _truncate_panel_at_or_before(
    panel: pl.DataFrame, cutoff: pd.Timestamp
) -> pl.DataFrame:
    """Return rows with ``ts_event <= cutoff`` (INCLUSIVE).

    Per quant-audit F-1-11: cutoff semantics are inclusive — boundary
    anchor ``C_i(09:45 ET)`` is in the feature set per design.md §3.0
    R3-R4. This is intentionally distinct from the Cycle-4
    fold-boundary canary at
    [src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py)
    line 60-71, which uses STRICT inequality (equality with the boundary
    is forbidden because the test fold's first observation IS the
    boundary). H053's PIT cutoff is at the close of the 09:45 ET bar,
    which IS a feature-side observation; the predictand starts at the
    09:46 ET bar (strictly later).
    """
    return panel.filter(pl.col("ts_event") <= cutoff)


def _frames_byte_equal(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    """Compare two DataFrames for bit-exact equality on shared columns.

    Per quant-audit F-1-8: explicitly check schema (dtype + name + order)
    BEFORE values, then use ``equals`` with ``null_equal=True`` so NaN
    comparisons follow Polars' canonical reproducibility convention.
    """
    if a.shape != b.shape:
        return False
    if a.schema != b.schema:
        return False
    return a.equals(b, null_equal=True)


# ---------------------------------------------------------------------------
# Long fixture for Daily block (300+ business days lookback per daily.py:79)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def long_panel_anchor():
    """A panel spanning enough business days that H053Daily's SMA200
    warmup completes (per quant-audit F-1-6). 250 business days × 1440
    min/session ≈ 360k rows ≈ 18 MB."""
    session_dates = pd.date_range(start="2023-03-01", end="2024-03-15", freq="B").tolist()
    panel = _make_full_session_panel([pd.Timestamp(s) for s in session_dates])
    anchor = pd.Timestamp(session_dates[-1])
    as_of = _bar_ts_utc(anchor, 9, 45)
    return panel, anchor, as_of


@pytest.fixture(scope="module")
def short_panel_anchor():
    """A panel spanning ~30 business days, sized for the non-Daily blocks
    (Mediator: 0-day; Hourly: 7-day; Microstructure: 7-day)."""
    session_dates = pd.date_range(start="2024-02-01", end="2024-03-15", freq="B").tolist()
    panel = _make_full_session_panel([pd.Timestamp(s) for s in session_dates])
    anchor = pd.Timestamp(session_dates[-1])
    as_of = _bar_ts_utc(anchor, 9, 45)
    return panel, anchor, as_of


# ---------------------------------------------------------------------------
# (a) Bar-set disjointness via input-poisoning capability proxy (F-1-1, F-1-2)
# ---------------------------------------------------------------------------


def _output_rows_match_truncated(
    feature: object,
    panel_full_clean: pl.DataFrame,
    panel_full_poisoned: pl.DataFrame,
    panel_truncated: pl.DataFrame,
    as_of: pd.Timestamp,
) -> tuple[int, int, bool]:
    """Compute (rows_clean, rows_poisoned, equal) for a given feature.

    Per Round-2 quant-audit F-2-1 NaN-poison protocol:
    - ``rows_clean`` = ``compute(panel_truncated, now=as_of)`` row count.
      This is the ground-truth "what the output should look like under
      a no-leak compute".
    - ``rows_poisoned`` = ``compute(panel_full_poisoned, now=as_of)`` row
      count. Any compute read of a NaN-poisoned post-cutoff bar
      propagates NaN through to a feature column; the project-wide
      ``is_finite()`` filter then drops the row.

    A passing canary requires ``rows_poisoned == rows_clean`` AND the
    feature columns of the poisoned output have no NaN values.
    """
    out_clean = feature.compute(panel_truncated.lazy(), now=as_of).collect()
    out_poisoned = feature.compute(panel_full_poisoned.lazy(), now=as_of).collect()
    # Identify feature columns (everything except ts_event + symbol).
    feat_cols = [c for c in out_poisoned.columns if c not in ("ts_event", "symbol")]
    has_nan = False
    for c in feat_cols:
        col = out_poisoned[c]
        if col.dtype in (pl.Float64, pl.Float32):
            if col.is_nan().any() or col.null_count() > 0:
                has_nan = True
                break
    return len(out_clean), len(out_poisoned), (
        len(out_clean) == len(out_poisoned) and not has_nan
    )


class TestInputPoisonCapabilityProxy:
    """Per Round-2 quant-audit F-2-1: NaN-poison capability proxy.

    Replace OHLCV in every post-cutoff bar with NaN; assert the compute
    output row count matches the truncated-panel row count, AND no
    feature column has any NaN. NaN propagation through arithmetic is
    structural (independent of feature codomain — works for log-returns,
    GK variances, OFI sums, volume aggregates alike). Any compute read
    of a poisoned bar surfaces as either a NaN feature (dropped by the
    is_finite() filter → row-count drop) or a NaN that escapes the
    filter (caught by the no-NaN check).

    Block D mediator (``test_mediator_does_not_read_post_cutoff_bars``)
    is structurally tautological under the current implementation — the
    mediator-window filter at ``mediator.py:274-278`` restricts to
    09:31-09:45 ET regardless of PIT cutoff (Round-2 F-2-2). The test
    is retained as a regression guard against future implementations
    that loosen the window filter.
    """

    def test_mediator_does_not_read_post_cutoff_bars(self, long_panel_anchor):
        """Structurally tautological under current implementation per F-2-2;
        retained as a regression guard."""
        panel, _anchor, as_of = long_panel_anchor
        poisoned = _poison_panel_after_cutoff(panel, as_of)
        truncated = _truncate_panel_at_or_before(panel, as_of)
        feature = H053Mediator()
        rows_clean, rows_poison, ok = _output_rows_match_truncated(
            feature, panel, poisoned, truncated, as_of
        )
        assert rows_clean > 0, (
            "H053Mediator: clean (truncated) output is empty; cannot exercise canary."
        )
        assert ok, (
            f"H053Mediator: NaN-poison row-count mismatch: clean={rows_clean}, "
            f"poisoned={rows_poison}; or NaN escaped into output. "
            "Indicates compute() read past the PIT cutoff."
        )

    def test_microstructure_5_15min_does_not_read_post_cutoff_bars(
        self, long_panel_anchor
    ):
        panel, _anchor, as_of = long_panel_anchor
        poisoned = _poison_panel_after_cutoff(panel, as_of)
        truncated = _truncate_panel_at_or_before(panel, as_of)
        feature = H053Microstructure5_15min()
        rows_clean, rows_poison, ok = _output_rows_match_truncated(
            feature, panel, poisoned, truncated, as_of
        )
        assert rows_clean > 0
        assert ok, (
            f"H053Microstructure5_15min: NaN-poison row-count mismatch "
            f"clean={rows_clean} poisoned={rows_poison}, or NaN escaped."
        )

    def test_hourly_does_not_read_post_cutoff_bars(self, long_panel_anchor):
        panel, _anchor, as_of = long_panel_anchor
        poisoned = _poison_panel_after_cutoff(panel, as_of)
        truncated = _truncate_panel_at_or_before(panel, as_of)
        feature = H053Hourly()
        rows_clean, rows_poison, ok = _output_rows_match_truncated(
            feature, panel, poisoned, truncated, as_of
        )
        assert rows_clean > 0
        assert ok, (
            f"H053Hourly: NaN-poison row-count mismatch "
            f"clean={rows_clean} poisoned={rows_poison}, or NaN escaped."
        )

    def test_daily_does_not_read_post_cutoff_bars(self, long_panel_anchor):
        panel, _anchor, as_of = long_panel_anchor
        poisoned = _poison_panel_after_cutoff(panel, as_of)
        truncated = _truncate_panel_at_or_before(panel, as_of)
        feature = H053Daily()
        rows_clean, rows_poison, ok = _output_rows_match_truncated(
            feature, panel, poisoned, truncated, as_of
        )
        assert rows_clean > 0, (
            "H053Daily: clean (truncated) output is empty. SMA200 warmup "
            "may not be complete; extend long_panel_anchor lookback."
        )
        assert ok, (
            f"H053Daily: NaN-poison row-count mismatch "
            f"clean={rows_clean} poisoned={rows_poison}, or NaN escaped."
        )


# ---------------------------------------------------------------------------
# (b) PIT-cutoff dual-fit invariance — design.md §3.0 R5
# ---------------------------------------------------------------------------


class TestPITCutoffDualFitInvariance:
    """For each H053 block: compute(panel_truncated, now) ≡
    compute(panel_with_future_bars, now), bit-exact."""

    def test_mediator_pit_invariant_under_dual_fit(self, short_panel_anchor):
        panel, _anchor, as_of = short_panel_anchor
        truncated = _truncate_panel_at_or_before(panel, as_of)
        # Panel truncation must actually drop bars (otherwise the test is vacuous)
        assert truncated.shape[0] < panel.shape[0]

        feature = H053Mediator()
        out_full = feature.compute(panel.lazy(), now=as_of).collect()
        out_truncated = feature.compute(truncated.lazy(), now=as_of).collect()
        assert len(out_full) > 0 and len(out_truncated) > 0
        assert _frames_byte_equal(out_full, out_truncated), (
            "H053Mediator: compute(full_panel, now) != compute(truncated_panel, now); "
            "indicates a read past the PIT cutoff."
        )

    def test_microstructure_5_15min_pit_invariant_under_dual_fit(
        self, short_panel_anchor
    ):
        panel, _anchor, as_of = short_panel_anchor
        truncated = _truncate_panel_at_or_before(panel, as_of)
        assert truncated.shape[0] < panel.shape[0]

        feature = H053Microstructure5_15min()
        out_full = feature.compute(panel.lazy(), now=as_of).collect()
        out_truncated = feature.compute(truncated.lazy(), now=as_of).collect()
        assert len(out_full) > 0 and len(out_truncated) > 0
        assert _frames_byte_equal(out_full, out_truncated), (
            "H053Microstructure5_15min: compute(full_panel, now) != "
            "compute(truncated_panel, now); indicates a read past PIT cutoff."
        )

    def test_hourly_pit_invariant_under_dual_fit(self, short_panel_anchor):
        panel, _anchor, as_of = short_panel_anchor
        truncated = _truncate_panel_at_or_before(panel, as_of)
        assert truncated.shape[0] < panel.shape[0]

        feature = H053Hourly()
        out_full = feature.compute(panel.lazy(), now=as_of).collect()
        out_truncated = feature.compute(truncated.lazy(), now=as_of).collect()
        assert len(out_full) > 0 and len(out_truncated) > 0
        assert _frames_byte_equal(out_full, out_truncated), (
            "H053Hourly: compute(full_panel, now) != compute(truncated_panel, now); "
            "indicates a read past the PIT cutoff."
        )

    def test_daily_pit_invariant_under_dual_fit(self, long_panel_anchor):
        panel, _anchor, as_of = long_panel_anchor
        truncated = _truncate_panel_at_or_before(panel, as_of)
        assert truncated.shape[0] < panel.shape[0]

        feature = H053Daily()
        out_full = feature.compute(panel.lazy(), now=as_of).collect()
        out_truncated = feature.compute(truncated.lazy(), now=as_of).collect()
        # Per F-1-6: the Daily block requires SMA200 warmup. long_panel_anchor
        # provides ≥250 business days; output must be non-empty.
        assert len(out_full) > 0, (
            "H053Daily: out_full is empty even on the long fixture. "
            "SMA200 warmup not complete; extend long_panel_anchor."
        )
        assert len(out_truncated) > 0
        assert _frames_byte_equal(out_full, out_truncated), (
            "H053Daily: compute(full_panel, now) != compute(truncated_panel, now); "
            "indicates a read past the PIT cutoff."
        )


# ---------------------------------------------------------------------------
# (c) Boundary-anchor inclusion at exactly ts_event = 09:45 ET (F-1-3)
# ---------------------------------------------------------------------------


class TestBoundaryAnchorInclusion:
    """Per quant-audit F-1-3: dual-fit invariance is satisfied if both
    panels equally exclude the boundary bar (off-by-one bug). This test
    verifies the boundary bar IS read by setting it to a distinguishable
    value and confirming the output reflects it."""

    def test_mediator_m_return_uses_0945_close(self):
        """H053Mediator.m_return = log(C_{09:45} / O_{09:30}) where
        C_{09:45} is the close of the 09:45 ET-timestamped bar.

        Construct a panel with mid increasing 0.25/bar starting from 4500
        for bars 09:31-09:44 (close of 09:44 = 4500 + 0.25*14 = 4503.5);
        then ARTIFICIALLY set the close of 09:45 to a distinguishable
        value (4600.0). The expected m_return uses 4600.0, not 4503.5.
        If the mediator off-by-one'd to use 09:44's close, m_return would
        differ from the expected value derived from 4600.0.
        """
        sd = pd.Timestamp("2024-03-15")
        # Build a 1-session panel with mediator-window bars 09:31-09:45
        # plus the 09:30 ET prior-close reference for OFI sign.
        rows = []
        for offset in range(16):  # 09:30..09:45
            hh, mm = 9, 30 + offset
            mid = 4500.0 + 0.25 * offset
            rows.append(
                {
                    "ts_event": _bar_ts_utc(sd, hh, mm),
                    "symbol": "ES",
                    "open": mid,
                    "high": mid + 0.25,
                    "low": mid - 0.25,
                    "close": mid,
                    "volume": 100.0,
                }
            )
        # Override the 09:45 bar's close to a distinct value; bump high to
        # keep OHLC self-consistent (close ≤ high) per Round-2 F-2-3 — a
        # defensive future GK-validity guard (e.g., reject C > H rows)
        # would otherwise cause this row to drop and break the test.
        rows[15]["close"] = 4600.0
        rows[15]["high"] = 4600.25
        panel = pl.DataFrame(rows).with_columns(
            pl.col("ts_event").dt.replace_time_zone("UTC").cast(pl.Datetime("ns", "UTC"))
        )

        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=_bar_ts_utc(sd, 9, 45)).collect()
        assert len(out) == 1
        # Expected: m_return = log(4600.0 / open_of_09:31) where
        # open_of_09:31 = 4500.0 + 0.25*1 = 4500.25
        import math
        expected_m_return = math.log(4600.0 / 4500.25)
        got = out["m_return"][0]
        assert math.isclose(got, expected_m_return, rel_tol=1e-12), (
            f"H053Mediator: m_return ({got!r}) does NOT match the expected "
            f"value ({expected_m_return!r}) using the 09:45 ET bar's close "
            "(4600.0); boundary anchor inclusion violated."
        )


# ---------------------------------------------------------------------------
# Adversarial leak-injection sub-suite — F-1-4 expanded coverage
# ---------------------------------------------------------------------------


class TestLeakInjectionDetection:
    """A 'dead canary' is one that silently passes when a leak is injected.
    These tests demonstrate the canary suite CATCHES three distinct leak
    modes from the Cycle-4 threat model (leak_canaries.py:218-228):

    1. **Trivial ts-leak**: compute returns max(panel.ts_event).
    2. **Mean-of-close leak (forgotten _pit_cutoff)**: compute returns
       mean(close) over the whole panel — mimics a real bug where a
       feature implementer forgets the PIT filter.
    3. **Backward-fill leak**: compute returns first-non-null close after
       a backward-fill — bleeds future closes into past rows."""

    def test_dual_fit_detects_trivial_ts_leak(self):
        sd = pd.Timestamp("2024-03-15")
        panel = _make_full_session_panel([sd])
        as_of = _bar_ts_utc(sd, 9, 45)
        truncated = _truncate_panel_at_or_before(panel, as_of)

        def leaky_compute(p: pl.DataFrame) -> pl.DataFrame:
            return p.select(pl.col("ts_event").max().alias("max_ts"))

        leaky_full = leaky_compute(panel)
        leaky_trunc = leaky_compute(truncated)
        assert not _frames_byte_equal(leaky_full, leaky_trunc), (
            "Dual-fit canary failed to detect a trivial ts-leak; "
            "this is the dead-canary failure mode rejected by Cycle-4."
        )

    def test_dual_fit_detects_mean_of_close_leak(self):
        """A feature that forgets to apply _pit_cutoff and computes
        mean(close) over the whole panel produces different outputs on
        truncated vs full panels — a realistic leak shape per the Cycle-4
        threat model (leak_canaries.py:218-228)."""
        sd = pd.Timestamp("2024-03-15")
        panel = _make_full_session_panel([sd])
        as_of = _bar_ts_utc(sd, 9, 45)
        truncated = _truncate_panel_at_or_before(panel, as_of)

        def leaky_mean_compute(p: pl.DataFrame) -> pl.DataFrame:
            return p.select(pl.col("close").mean().alias("mean_close"))

        leaky_full = leaky_mean_compute(panel)
        leaky_trunc = leaky_mean_compute(truncated)
        assert not _frames_byte_equal(leaky_full, leaky_trunc), (
            "Dual-fit canary failed to detect a mean-of-close leak (forgotten "
            "_pit_cutoff). Per Cycle-4 leak_canaries.py threat model this is "
            "the load-bearing detection mode."
        )

    def test_nan_poison_detects_mean_of_close_leak(self):
        """The NaN-poison capability proxy (Round-2 F-2-1) catches the
        forgotten-_pit_cutoff leak by NaN-propagation: a feature that
        averages close over the whole panel reads NaN-poisoned bars,
        producing a NaN output column."""
        sd = pd.Timestamp("2024-03-15")
        panel = _make_full_session_panel([sd])
        as_of = _bar_ts_utc(sd, 9, 45)
        poisoned = _poison_panel_after_cutoff(panel, as_of)

        def leaky_mean_compute(p: pl.DataFrame) -> pl.DataFrame:
            return p.select(pl.col("close").mean().alias("mean_close"))

        out = leaky_mean_compute(poisoned)
        mean_value = out["mean_close"][0]
        # Polars' mean() over a NaN-bearing column propagates NaN.
        # Without the leak: leaky_mean_compute(truncated) would give a
        # finite value (~4500); WITH the leak (full poisoned panel),
        # the output is NaN.
        import math
        assert math.isnan(mean_value), (
            "NaN-poison canary failed to detect a mean-of-close leak. "
            "The poisoned bars should have NaN-propagated through the mean."
        )

    def test_nan_poison_detects_single_bar_leak_on_long_fixture(
        self, long_panel_anchor
    ):
        """Per Round-2 F-2-5: positive control on the long fixture confirms
        the NaN-poison detector catches even single-bar leaks (a feature
        that reads ONE post-cutoff bar — e.g., panel.sort_by('ts_event').
        last()['close']). The structural (not magnitude) detector handles
        this case correctly."""
        panel, _anchor, as_of = long_panel_anchor
        poisoned = _poison_panel_after_cutoff(panel, as_of)

        def leaky_last_close(p: pl.DataFrame) -> pl.DataFrame:
            return p.select(
                pl.col("close").sort_by("ts_event").last().alias("last_close")
            )

        # Note: above selection uses ts_event indirectly. Simpler: take the
        # max ts_event row's close.
        def leaky_argmax_close(p: pl.DataFrame) -> pl.DataFrame:
            max_idx = p["ts_event"].arg_max()
            return p.select(pl.col("close").gather(max_idx).alias("last_close"))

        out = leaky_argmax_close(poisoned)
        last_val = out["last_close"][0]
        import math
        assert math.isnan(last_val), (
            "NaN-poison canary failed to detect a single-bar leak. The "
            "argmax-ts_event close should have been NaN-poisoned."
        )


# ---------------------------------------------------------------------------
# Archetype classifier PIT contract (F-1-5: clarified scope)
# ---------------------------------------------------------------------------


class TestArchetypeClassifierPITContract:
    """Per quant-audit F-1-5: the archetype classifier's
    ``train_panel_checksum`` field is a SIDECAR-ONLY contract for
    ReproLog auditability. It is NOT enforced at apply-time — apply
    accepts any panel with the four required mediator columns. The
    PIT contract on the orchestrator side is enforced by walk-forward
    fold partitioning (the orchestrator hands disjoint train/OOS
    panels to fit and apply respectively).

    This test verifies the SIDECAR-RECORDING property: the checksum
    changes when the training panel changes, so a downstream auditor
    inspecting the ReproLog can detect orchestrator wiring drift.
    Wiring of the checksum into ``ReproLog.model_hash`` via
    ``with_model_hash`` is tracked under
    ``P1-H053-ARCHETYPE-SIDECAR-MODEL-HASH-WIRING`` (orchestrator-side
    follow-up).
    """

    def test_train_checksum_distinguishes_clean_vs_oos_polluted_panels(self):
        # justify: deterministic test seed; value arbitrary, fixed for
        # reproducibility per CLAUDE.md §Reproducibility.
        rng = np.random.default_rng(123)
        n = 200
        train_only = pl.DataFrame(
            {
                "ts_event": [pd.Timestamp("2024-01-02 14:45", tz="UTC")] * n,
                "symbol": ["ES"] * n,
                "m_return": rng.normal(0.0, 0.005, size=n),
                "m_log_range": np.abs(rng.normal(0.0, 0.003, size=n)),
                "m_volume": rng.normal(1500.0, 300.0, size=n),
                "m_ofi_tickrule": rng.normal(0.0, 800.0, size=n),
            }
        ).with_columns(pl.col("ts_event").cast(pl.Datetime("ns", "UTC")))
        oos_extra = pl.DataFrame(
            {
                "ts_event": [pd.Timestamp("2024-06-01 14:45", tz="UTC")] * 50,
                "symbol": ["ES"] * 50,
                "m_return": rng.normal(0.0, 0.005, size=50),
                "m_log_range": np.abs(rng.normal(0.0, 0.003, size=50)),
                "m_volume": rng.normal(1500.0, 300.0, size=50),
                "m_ofi_tickrule": rng.normal(0.0, 800.0, size=50),
            }
        ).with_columns(pl.col("ts_event").cast(pl.Datetime("ns", "UTC")))
        leaky = pl.concat([train_only, oos_extra])

        rule_clean = fit_archetype_rule(train_only, K=5)
        rule_leaky = fit_archetype_rule(leaky, K=5)
        assert rule_clean.train_panel_checksum != rule_leaky.train_panel_checksum, (
            "Archetype-classifier sidecar contract failed: train_panel_checksum "
            "did not change when OOS rows were included in the training panel. "
            "Downstream ReproLog auditor cannot detect orchestrator wiring drift."
        )
        # Round-2 F-2-7: two-sided sidecar contract — idempotency on
        # bit-identical inputs catches a regression where fit_archetype_rule
        # injected non-seeded entropy into the checksum.
        rule_clean_redo = fit_archetype_rule(train_only, K=5)
        assert rule_clean.train_panel_checksum == rule_clean_redo.train_panel_checksum, (
            "Archetype-classifier sidecar contract failed: train_panel_checksum "
            "differs across two fits on the SAME panel; non-deterministic "
            "checksum injection regression."
        )
