"""H055 feature factory — wick-rejection mean-reversion scalp components.

Per H055 design.md §3 (Components 1-4):
  - Component 1: deterministic trend-strength gate (TS-mom / ADX / OLS-slope-t / MA-cross)
  - Component 2: body-overlap consolidation indicator ρ_1
  - Component 3: level-exhaustion state machine R(L) — implemented at level_state.py
  - Component 4: ATR + Wilder smoothing + realized variance for Kelly sizing

Sub-modules:
  - level_state: Component 3 state machine (closes P1-H055-LEVEL-EXHAUSTION-STATE-MACHINE-IMPL)
  - features: full feature factory composition (pending P1-H055-FEATURE-FACTORY-IMPL)
"""

from skie_ninja.features.h055.level_state import (
    LevelExhaustionStateMachine,
    LevelState,
)

__all__ = [
    "LevelExhaustionStateMachine",
    "LevelState",
]
