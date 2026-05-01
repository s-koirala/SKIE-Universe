"""H053 feature factory — Cycle 7 deliverable per
[plan/h053_buildout_2026-04-28.md](../../../../plan/h053_buildout_2026-04-28.md).

The H053 feature factory diverges from the project-wide bar-grain
``FEATURE_REGISTRY`` in
[src/skie_ninja/features/base.py](../base.py) on three dimensions:

1. **Output grain** — bar-grain features produce one row per (symbol,
   ts_event) on every minute; H053 features produce one row per
   (symbol, session) at a fixed clock-time anchor (``as_of`` per
   [research/01_hypothesis_register/H053/design.md](
   ../../../../research/01_hypothesis_register/H053/design.md) §3.0-§3.4).

2. **Window definition** — bar-grain features use rolling windows
   measured in bars; H053 features use fixed wall-clock windows in
   ``America/New_York`` ET (09:30→09:45 ET mediator; 09:45→10:30 ET
   predictand) per design.md §3.0.

3. **Registry membership** — H053 modules do NOT register in the
   project-wide ``FEATURE_REGISTRY``. They are H053-orchestrator-specific
   and consumed directly by [scripts/run_h053_*.py](../../../../scripts/)
   driver scripts (Cycle 8/9/10 deliverables).

Block-level layout per design.md §3:

- ``daily.py``      — Block A daily-timeframe features (``as_of = T-1 close``)
- ``hourly.py``     — Block B hourly-timeframe features
- ``microstructure_5_15min.py`` — Block C 5/15-min features
- ``mediator.py``   — Block D 09:30→09:45 ET mediator (this commit)
- ``archetype_classifier.py`` — §4.5.1 archetype classifier

Bar-edge convention is binding per design.md §3.0; a regression gate
at [tests/unit/test_h053_bar_edge_convention.py](
../../../../tests/unit/test_h053_bar_edge_convention.py) (21 tests, 3
DST-aware session-date parametrisations) enforces the §3.0 R1-R6 rules.
"""

from skie_ninja.features.h053.daily import H053Daily
from skie_ninja.features.h053.hourly import H053Hourly
from skie_ninja.features.h053.mediator import H053Mediator

__all__ = ["H053Daily", "H053Hourly", "H053Mediator"]
