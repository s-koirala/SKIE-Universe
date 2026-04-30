"""H053 bar-edge convention regression gate (design.md §3.0; §11.2 prereq 11 sub-clauses a-b).

Anchors the binding wall-clock semantics that the H053 §1 predictand definition and
the §3.4 mediator depend on. Without these tests, the boundary timestamps are
ambiguous and admit a latent same-bar leak.

The §3.0 convention enumerates six binding rules:

  R1  Every 1-min bar carries a single timestamp equal to the END of the bar.
      A bar with timestamp 09:45 ET covers trades in [09:44 ET, 09:45 ET) on
      `America/New_York` wall-clock (left-closed, right-open).
  R2  Mediator window 09:30-09:45 ET = exactly 15 bars at timestamps
      {09:31, 09:32, ..., 09:45 ET}; the 09:45 ET bar is the LAST bar of
      the mediator window.
  R3  Predictand window 09:45-10:30 ET = exactly 45 bars at timestamps
      {09:46, 09:47, ..., 10:30 ET}; the 09:45 ET bar is EXCLUDED.
  R4  C_i(09:45 ET, t) (predictand left-endpoint reference) is the close of
      the 09:45 ET-timestamped bar; this is a boundary anchor scalar shared
      between predictand and mediator definitions, NOT a feature-fit input.
  R5  O_{09:30} shorthand maps to the open of the 09:31 ET-timestamped bar
      (first trade in [09:30, 09:31)). There is NO 09:30 ET-timestamped bar
      in the convention.
  R6  Disjointness: feature_bar_set ∩ predictand_bar_set = ∅.

Sub-clause (c) of §11.2 prereq 11 (dual-fit-call observer + TracingArray
capability proxy on the H053 feature factory) is deferred to the follow-up
that lands `src/skie_ninja/features/h053/`; this file covers (a) and (b).

Reference: research/01_hypothesis_register/H053/design.md §3.0 (binding) and
§11.2 prereq 11 (the unit-test gate this file provides).
"""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

ET = ZoneInfo("America/New_York")

MEDIATOR_OPEN_ET = time(9, 30)
MEDIATOR_CLOSE_ET = time(9, 45)
PREDICTAND_OPEN_ET = time(9, 45)
PREDICTAND_CLOSE_ET = time(10, 30)

EXPECTED_MEDIATOR_BAR_COUNT = 15  # design.md §3.0 R2: bars {09:31, 09:32, ..., 09:45 ET}
EXPECTED_PREDICTAND_BAR_COUNT = 45  # design.md §3.0 R3: bars {09:46, 09:47, ..., 10:30 ET}


def _et_session_bars(session_date: pd.Timestamp, start_et: time, end_et: time) -> list[pd.Timestamp]:
    """Return the ordered list of 1-min bar timestamps in (start_et, end_et] ET.

    Bar timestamp = END of the bar (per R1). Half-open interval (start, end] is
    the equivalent expression of the rule that the bar with timestamp t covers
    [t-1min, t). The first bar after start_et is the one timestamped start_et+1min.
    """
    open_dt = datetime.combine(session_date.date(), start_et, tzinfo=ET)
    close_dt = datetime.combine(session_date.date(), end_et, tzinfo=ET)
    edges = pd.date_range(
        start=pd.Timestamp(open_dt) + pd.Timedelta(minutes=1),
        end=pd.Timestamp(close_dt),
        freq="1min",
        tz=ET,
        inclusive="both",
    )
    return list(edges)


def mediator_window_bars(session_date: pd.Timestamp) -> list[pd.Timestamp]:
    return _et_session_bars(session_date, MEDIATOR_OPEN_ET, MEDIATOR_CLOSE_ET)


def predictand_window_bars(session_date: pd.Timestamp) -> list[pd.Timestamp]:
    return _et_session_bars(session_date, PREDICTAND_OPEN_ET, PREDICTAND_CLOSE_ET)


@pytest.fixture(
    params=[
        pd.Timestamp("2024-03-15"),  # arbitrary RTH session, no DST transition
        pd.Timestamp("2024-03-11"),  # first US RTH session after DST spring-forward (2024-03-10 Sun)
        pd.Timestamp("2024-11-04"),  # first US RTH session after DST fall-back (2024-11-03 Sun)
    ],
    ids=["mid-march-no-dst", "post-spring-forward", "post-fall-back"],
)
def session_date(request) -> pd.Timestamp:
    return request.param


def test_r1_bar_timestamp_is_end_of_interval(session_date: pd.Timestamp) -> None:
    """R1: bar with timestamp 09:45 ET covers trades in [09:44 ET, 09:45 ET).

    Positive half-open-interval assertion: for any bar at timestamp `t`, the
    interval the bar covers starts at `t - 1min` and ends just before `t` (left-
    closed, right-open). Anchoring this directly catches a regression that
    flipped to start-of-bar timestamping, which the size+endpoint assertions
    in R2/R3 alone would only catch indirectly.
    """
    bars = mediator_window_bars(session_date)
    assert bars[0].time() == time(9, 31), "first mediator bar must be 09:31 ET (R1+R5)"
    assert bars[-1].time() == time(9, 45), "last mediator bar must be 09:45 ET (R2)"
    assert all(b.tzinfo is ET for b in bars), "bars must carry America/New_York tz (R1)"

    # R1 positive: bar at 09:45 ET covers [09:44 ET, 09:45 ET).
    # Equivalent assertion: the bar's interval START = bar_ts - 1min.
    last_bar = bars[-1]
    interval_start = last_bar - pd.Timedelta(minutes=1)
    assert interval_start.time() == time(9, 44), (
        "R1: bar with timestamp 09:45 ET must cover [09:44 ET, 09:45 ET); "
        "regression check on end-of-bar timestamping convention"
    )
    # And the first bar 09:31 ET covers [09:30 ET, 09:31 ET): the start of
    # the mediator window 09:30 ET is the LEFT endpoint of the first bar's
    # interval, not a bar timestamp itself (R5).
    first_bar = bars[0]
    assert (first_bar - pd.Timedelta(minutes=1)).time() == time(9, 30), (
        "R1+R5: bar 09:31 ET must cover [09:30 ET, 09:31 ET); 09:30 ET is "
        "an interval boundary, not a bar timestamp"
    )


def test_r2_mediator_window_size_and_endpoints(session_date: pd.Timestamp) -> None:
    """R2: mediator window = exactly 15 bars at {09:31, ..., 09:45 ET}; 09:45 ET is LAST."""
    bars = mediator_window_bars(session_date)
    assert len(bars) == EXPECTED_MEDIATOR_BAR_COUNT, (
        f"mediator window must contain exactly {EXPECTED_MEDIATOR_BAR_COUNT} bars; got {len(bars)}"
    )
    assert bars[-1].time() == time(9, 45), "09:45 ET must be the LAST bar of the mediator window"
    assert bars[0].time() == time(9, 31), "first mediator bar must be 09:31 ET"
    times = [b.time() for b in bars]
    expected_times = [time(9, m) for m in range(31, 46)]
    assert times == expected_times, "mediator timestamps must be {09:31..09:45 ET} exactly"


def test_r3_predictand_window_size_and_endpoints(session_date: pd.Timestamp) -> None:
    """R3: predictand window = exactly 45 bars at {09:46, ..., 10:30 ET}; 09:45 ET is EXCLUDED."""
    bars = predictand_window_bars(session_date)
    assert len(bars) == EXPECTED_PREDICTAND_BAR_COUNT, (
        f"predictand window must contain exactly {EXPECTED_PREDICTAND_BAR_COUNT} bars; got {len(bars)}"
    )
    assert bars[0].time() == time(9, 46), "first predictand bar must be 09:46 ET"
    assert bars[-1].time() == time(10, 30), "last predictand bar must be 10:30 ET"
    assert all(b.time() != time(9, 45) for b in bars), (
        "09:45 ET bar must NOT appear in the predictand window (R3)"
    )


def test_r6_mediator_predictand_disjointness(session_date: pd.Timestamp) -> None:
    """R6: feature_bar_set ∩ predictand_bar_set = ∅.

    The mediator window is the only feature window that touches the predictand's
    left endpoint; if the two are disjoint, no other feature block can violate
    disjointness because all other feature blocks are constrained to as_of ≤
    09:45 ET (design.md §3.1-§3.3) and thus produce bars timestamped ≤ 09:45 ET,
    which the mediator window already covers at its right edge.
    """
    mediator = set(mediator_window_bars(session_date))
    predictand = set(predictand_window_bars(session_date))
    assert mediator.isdisjoint(predictand), (
        f"mediator ∩ predictand must be empty; overlap = {mediator & predictand}"
    )


def test_r4_boundary_anchor_is_single_shared_timestamp(session_date: pd.Timestamp) -> None:
    """R4: C_i(09:45 ET, t) is the close of the 09:45 ET bar — boundary anchor scalar.

    The 09:45 ET timestamp belongs to the mediator window (R2), not the predictand
    window (R3). When the predictand is computed as
        y_{i,t} = log(C_i(10:30 ET, t)) − log(C_i(09:45 ET, t))
    the C_i(09:45 ET, t) reference is a boundary anchor scalar — it does NOT make
    the 09:45 ET bar a member of the predictand_bar_set. The bar-set membership
    is preserved (mediator only); the scalar is read by reference.

    This test asserts the binding semantic: the 09:45 ET timestamp is in mediator,
    not predictand.
    """
    boundary = pd.Timestamp(
        datetime.combine(session_date.date(), time(9, 45), tzinfo=ET)
    )
    assert boundary in mediator_window_bars(session_date), (
        "09:45 ET boundary anchor MUST be in mediator window (R4 + R2)"
    )
    assert boundary not in predictand_window_bars(session_date), (
        "09:45 ET boundary anchor must NOT be in predictand window (R4 + R3)"
    )


def test_r5_no_0930_bar_in_convention(session_date: pd.Timestamp) -> None:
    """R5: there is NO 09:30 ET-timestamped bar; O_{09:30} shorthand = open of 09:31 ET bar.

    Per R1, a bar at timestamp 09:30 would represent trades in [09:29, 09:30) —
    pre-RTH for an ET-anchored RTH session. The 09:30 ET wall-clock instant is
    the START of the mediator interval, not the timestamp of any bar in the
    convention. The first bar of the mediator window is 09:31 ET, covering
    [09:30, 09:31) — this is the bar whose OPEN is the first RTH trade and to
    which the O_{09:30} shorthand refers.
    """
    bars = mediator_window_bars(session_date)
    pre_open = pd.Timestamp(
        datetime.combine(session_date.date(), time(9, 30), tzinfo=ET)
    )
    assert pre_open not in bars, "09:30 ET must NOT be a bar timestamp in the convention (R5)"
    assert bars[0] == pd.Timestamp(
        datetime.combine(session_date.date(), time(9, 31), tzinfo=ET)
    ), "O_{09:30} shorthand must resolve to the 09:31 ET-timestamped bar (R5)"


def test_concatenated_window_has_no_overlap_at_boundary(session_date: pd.Timestamp) -> None:
    """Boundary edge-case: concatenating mediator + predictand bars yields a
    contiguous, gap-free, overlap-free 60-bar sequence covering 09:31-10:30 ET.

    Catches the most likely regression: a future implementation that includes
    09:45 ET in BOTH windows (would produce 16 + 45 = 61 bars with a duplicate
    at 09:45 ET), or that includes 09:30 ET (would produce 16 + 45 = 61 bars
    with a duplicate at the front edge).
    """
    mediator = mediator_window_bars(session_date)
    predictand = predictand_window_bars(session_date)
    combined = mediator + predictand
    assert len(combined) == EXPECTED_MEDIATOR_BAR_COUNT + EXPECTED_PREDICTAND_BAR_COUNT
    assert len(set(combined)) == len(combined), (
        f"concatenated mediator+predictand must contain no duplicates; "
        f"duplicate count = {len(combined) - len(set(combined))}"
    )
    deltas = pd.Series(combined).diff().dropna().unique()
    assert list(deltas) == [pd.Timedelta(minutes=1)], (
        f"concatenated bars must be contiguous at 1-min spacing; got deltas {deltas}"
    )
