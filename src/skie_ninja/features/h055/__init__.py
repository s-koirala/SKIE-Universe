"""H055 feature factory — wick-rejection mean-reversion scalp components.

Per H055 design.md §3 (Components 1-4):
  - Component 1: deterministic trend-strength gate (TS-mom / ADX / OLS-slope-t / MA-cross)
                 — pending `P1-H055-COMPONENT-1-TREND-IDENTIFIERS-IMPL`
  - Component 2: body-overlap consolidation indicator ρ_1 — body_overlap.py
  - Component 3: level-exhaustion state machine R(L) — level_state.py
  - Component 4: ATR + Wilder smoothing — atr.py
                 (realized variance for Kelly sizing pending separate primitive)

Sub-modules:
  - atr: Component 4 ATR + Wilder smoothing (Wilder 1978)
  - body_overlap: Component 2 ρ_1 closed-form Jaccard mean
  - level_state: Component 3 R(L) state machine
  - features: full feature factory composition (pending `P1-H055-FEATURE-FACTORY-IMPL`)
"""

from skie_ninja.features.h055.atr import atr_wilder, true_range
from skie_ninja.features.h055.body_overlap import (
    body_interval,
    body_overlap_rho_1,
    pairwise_jaccard,
)
from skie_ninja.features.h055.level_state import (
    LevelExhaustionStateMachine,
    LevelState,
)

__all__ = [
    "LevelExhaustionStateMachine",
    "LevelState",
    "atr_wilder",
    "body_interval",
    "body_overlap_rho_1",
    "pairwise_jaccard",
    "true_range",
]
