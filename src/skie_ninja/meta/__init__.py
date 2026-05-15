"""Meta-strategy primitives (switching-bandit, meta-portfolio, etc.).

Closes BLOCKING-BEFORE-FIRST-META-STRATEGY-RUN precondition
`P1-SWITCHING-BANDIT-META-STRATEGY` per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-4.
"""

from skie_ninja.meta.switching_bandit import (
    DUCBBandit,
    SWUCBBandit,
    GLRKLUCBBandit,
    EXP3SBandit,
    BanditResult,
    cumulative_regret,
    select_bandit_by_regret,
)

__all__ = [
    "DUCBBandit",
    "SWUCBBandit",
    "GLRKLUCBBandit",
    "EXP3SBandit",
    "BanditResult",
    "cumulative_regret",
    "select_bandit_by_regret",
]
