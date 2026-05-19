"""Shared K-1..K-8 kill-switch thresholds + session-clock function.

Per ADR-0025 §D-1 F-1-1 + F-1-7 audit fixes + `P1-KILL-SWITCH-CONSTANTS-SHARED-MODULE`,
this module is the single source of truth for kill-switch thresholds. Both the
post-hoc validator at [kill_switch_validation.py](kill_switch_validation.py) and
the runtime intervention module at [kill_switch_runtime.py](kill_switch_runtime.py)
import these constants. Drift between the two modules is detected by the parity
test at [tests/unit/test_kill_switch_runtime.py](../../../tests/unit/test_kill_switch_runtime.py).

Thresholds anchor to ADR-0017 §5 K-1..K-8 enumeration + Turtle 2N convention
per Faith 2007 *Way of the Turtle* ISBN-13 978-0071486644 (*practitioner*;
chapter pin deferred per `P1-FAITH-2007-CHAPTER-PIN-VERIFY`).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

# K-1: per-trade dollar-stop within 1.0R (Turtle 2N convention).
# justify: ADR-0017 §5 K-1; the 1.05 tolerance captures gap-through-stop events
# while flagging excess slippage per kill_switch_validation.py:116 v1 semantic.
K1_STOP_HIT_TOLERANCE_R: float = 1.05

# justify: ADR-0017 §5 K-1; the 3.0 cap on gap-through-stop = 3× adverse fill;
# matches kill_switch_validation.py:138 v1 semantic.
K1_GAP_THROUGH_TOLERANCE_R: float = 3.0

# K-6: daily circuit breaker at -2% of equity_at_session_start.
# justify: ADR-0017 §5 K-6 + ADR-0025 §D-1 F-1-7 audit fix; threshold is
# current-equity-ratcheting (tightens during drawdowns) per the survival-
# constrained-discipline interpretation. Validator migration tracked under
# P1-KILL-SWITCH-VALIDATOR-EQUITY-RATCHET-MIGRATE.
K6_DAILY_DRAWDOWN_THRESHOLD: float = -0.02

# K-7: weekly circuit breaker at -5% of equity_at_week_start.
# justify: ADR-0017 §5 K-7; same current-equity-ratcheting convention as K-6.
K7_WEEKLY_DRAWDOWN_THRESHOLD: float = -0.05

# ADR-0017 §5 K-5 correlated-instrument-pair taxonomy. The runtime SHALL raise
# a validation error if invoked on a basket containing any pair from this
# taxonomy (F-1-6 audit fix; tracked under P1-KILL-SWITCH-RUNTIME-K5-CORRELATED-EXTEND
# BLOCKING-BEFORE-H061-PROD-RUN).
# justify: enumerated per CME product specs for full-size + micro pairs and
# silver-specific full vs micro mapping per config/instruments.yaml.
K5_CORRELATED_PAIRS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"ES", "MES"}),
        frozenset({"NQ", "MNQ"}),
        frozenset({"YM", "MYM"}),
        frozenset({"GC", "MGC"}),
        frozenset({"SI", "SIL"}),
        frozenset({"CL", "MCL"}),
    }
)


def session_date_from_timestamp(ts: pd.Timestamp | datetime) -> date:
    """Return the canonical CME session-date for an arbitrary timestamp.

    Per ADR-0025 §D-1 F-1-1 audit fix, kill-switch P/L accumulators are keyed
    by CME session-date (NOT UTC calendar date) so that ETH sessions that span
    a UTC date boundary are correctly grouped into one CME trading day.

    Delegates to [skie_ninja.utils.clock.trading_day](../utils/clock.py) which
    is the canonical CME session-clock function for the project.

    Args:
        ts: Pandas Timestamp or datetime (timezone-aware or naive; naive
            interpreted as UTC per the clock.py contract).

    Returns:
        date object representing the CME trading-day to which `ts` belongs.
    """
    # Import inside function to avoid circular-import risk; clock.py imports
    # from utils.paths which itself depends on backtest in some scenarios.
    from skie_ninja.utils.clock import trading_day

    return trading_day(ts)


def iso_week_id_from_session_date(session_date: date) -> tuple[int, int]:
    """Return (iso_year, iso_week) tuple for the supplied session-date.

    Per ADR-0025 §D-1 F-1-1 audit fix, K-7 weekly P/L accumulators key on the
    ISO-week of the CME session-date (NOT the UTC timestamp's ISO-week).

    Args:
        session_date: date object produced by `session_date_from_timestamp`.

    Returns:
        (iso_year, iso_week) tuple suitable for use as a dict key.
    """
    iso = session_date.isocalendar()
    return (iso[0], iso[1])


__all__ = [
    "K1_STOP_HIT_TOLERANCE_R",
    "K1_GAP_THROUGH_TOLERANCE_R",
    "K6_DAILY_DRAWDOWN_THRESHOLD",
    "K7_WEEKLY_DRAWDOWN_THRESHOLD",
    "K5_CORRELATED_PAIRS",
    "session_date_from_timestamp",
    "iso_week_id_from_session_date",
]
