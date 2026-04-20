"""F-2-20: cross-module RTH-window consistency.

Asserts the RTH window parsed from [config/instruments.yaml] matches
the hard-coded `RTH_OPEN` / `RTH_CLOSE` constants in
[src/skie_ninja/utils/clock.py] for every instrument. Catches drift
where one file is edited without the other.
"""

from __future__ import annotations

from datetime import time

from skie_ninja.utils.clock import RTH_CLOSE, RTH_OPEN
from skie_ninja.utils.instruments import load_instruments
from skie_ninja.utils.paths import ProjectPaths


def _parse_hhmm(s: str) -> time:
    hh, mm = s.strip().split(":")
    return time(int(hh), int(mm))


def _parse_session(spec: str) -> tuple[time, time]:
    # "HH:MM-HH:MM"
    open_s, close_s = spec.split("-")
    return _parse_hhmm(open_s), _parse_hhmm(close_s)


def test_rth_window_matches_clock_constants_for_all_instruments() -> None:
    paths = ProjectPaths.discover()
    registry = load_instruments(paths.root / "config" / "instruments.yaml")
    assert registry, "instruments.yaml registry came back empty"

    mismatches: list[str] = []
    for symbol, spec in registry.items():
        open_t, close_t = _parse_session(spec.session_rth)
        if open_t != RTH_OPEN or close_t != RTH_CLOSE:
            mismatches.append(
                f"{symbol}: yaml session_rth={spec.session_rth!r} "
                f"(open={open_t}, close={close_t}) vs clock.py "
                f"RTH_OPEN={RTH_OPEN}, RTH_CLOSE={RTH_CLOSE}"
            )
    assert not mismatches, "RTH window drift between config and clock:\n" + "\n".join(
        mismatches
    )
