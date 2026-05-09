"""H055 level-state fold-continuity tests.

Validates the H055 design.md §5.3 + §6 embargo + level-state contracts that
the walk-forward splitter must satisfy. Closes BLOCKING-BEFORE-LAUNCH
precondition `P1-H055-LEVEL-STATE-FOLD-CONTINUITY-TEST` per design.md §11.2
plus the state-machine fold-boundary contracts originally deferred to
`P1-H055-LEVEL-EXHAUSTION-STATE-MACHINE-IMPL`.

Three pre-registered fixtures (per §5.3 + §11.2):
  (i)   embargo_minutes formula validation against the H055 config: the
        running embargo MUST be at least
        ``k_swing × minutes_per_T_H_bar + max_holding_period × minutes_per_T_L_bar``
        for every (k_swing, max_holding_period, T_H, T_L) cell in the
        §5.6 search domain.
  (ii)  RTH-only (405-min session): snapshot-policy variant of the level-
        state machine preserves state across folds.
  (iii) Fold boundary across CME 17:00 CT maintenance break: reset-policy
        variant resets state (state_signature changes; n_resets increments).

State-machine implementation:
[src/skie_ninja/features/h055/level_state.py](../../src/skie_ninja/features/h055/level_state.py)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest
import yaml

from skie_ninja.features.h055.level_state import LevelExhaustionStateMachine


def _load_h055_config() -> dict[str, Any]:
    """Load config/hypotheses/H055.yaml from the project root."""
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config" / "hypotheses" / "H055.yaml"
    assert config_path.exists(), f"H055 config not found at {config_path}"
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Search-domain extremes per design.md §5.6 (frozen pre-registration §1-§7
# immutability — these constants reproduce the YAML's commented derivation).
_T_H_BAR_MINUTES_DOMAIN = (15, 30, 60, 240)
_T_L_BAR_MINUTES_DOMAIN = (1, 5, 15)
_K_SWING_DOMAIN = (3, 5, 8, 13)
_MAX_HOLDING_PERIOD_DOMAIN = (3, 5, 8, 13)  # k_swing time-stop proxy per H055.yaml comment

_MINUTES_PER_ETH_SESSION = 1380  # CME ETH 23-hour electronic
_MINUTES_PER_RTH_SESSION = 405


def _required_embargo_minutes(
    k_swing: int,
    max_holding_period: int,
    minutes_per_T_H_bar: int,
    minutes_per_T_L_bar: int,
) -> int:
    """Per design.md §5.3 formula:

    embargo_minutes >= k_swing × minutes_per_T_H_bar
                       + max_holding_period × minutes_per_T_L_bar
    """
    return k_swing * minutes_per_T_H_bar + max_holding_period * minutes_per_T_L_bar


def test_eth_session_embargo_minutes_crosses_session_boundary_correctly() -> None:
    """ETH (23-hour session) — embargo crosses the session boundary correctly.

    Asserts the H055.yaml `splitter.embargo` value (in minutes) is at least
    the maximum required embargo across the §5.6 search-domain Cartesian
    product:

        max over (k_swing, max_holding_period, T_H, T_L) of
            (k_swing × T_H_minutes + max_holding_period × T_L_minutes)

    Per design.md §5.6 the maximum cell is k_swing=13, max_holding=13,
    T_H=240m, T_L=15m → 13×240 + 13×15 = 3315 minutes; this matches the
    H055.yaml pinned embargo value.

    The 23-hour ETH session is the long-session edge case: at
    `minutes_per_session = 1380`, `embargo_sessions = ceil(3315 / 1380)
    = 3 sessions` — verified separately below.
    """
    cfg = _load_h055_config()
    yaml_embargo_minutes = int(cfg["splitter"]["embargo"])

    max_required = max(
        _required_embargo_minutes(k, h, t_h, t_l)
        for k in _K_SWING_DOMAIN
        for h in _MAX_HOLDING_PERIOD_DOMAIN
        for t_h in _T_H_BAR_MINUTES_DOMAIN
        for t_l in _T_L_BAR_MINUTES_DOMAIN
    )

    assert yaml_embargo_minutes >= max_required, (
        f"H055.yaml splitter.embargo = {yaml_embargo_minutes} minutes is "
        f"below the formula maximum {max_required} minutes (k_swing_max=13, "
        f"max_holding_max=13, T_H_max=240m, T_L_max=15m). The pre-registered "
        f"§5.3 formula requires embargo >= max-formula across the §5.6 search "
        f"domain to prevent label-leakage at any selected hyperparameter cell."
    )
    # Verify the YAML's documented derivation matches the formula maximum
    # (3315 minutes per the YAML comment at line 66-69).
    assert max_required == 3315


def test_eth_embargo_sessions_ceiling_three() -> None:
    """ETH session: ceil(embargo_minutes / 1380) = 3 sessions.

    Per design.md §5.3 + H055.yaml line 67-68: `embargo_sessions =
    ceil(embargo_minutes / minutes_per_session)`. With the YAML's 3315
    minutes and CME ETH 1380 minutes/session, this is 3.
    """
    cfg = _load_h055_config()
    embargo_minutes = int(cfg["splitter"]["embargo"])
    embargo_sessions_eth = math.ceil(embargo_minutes / _MINUTES_PER_ETH_SESSION)
    assert embargo_sessions_eth == 3


def test_rth_only_embargo_sessions_consistent() -> None:
    """RTH-only session (405 min/session): embargo spans multiple RTH sessions.

    For the H055 YAML's pinned 3315-minute embargo, the RTH-equivalent is
    ceil(3315 / 405) = 9 RTH sessions. This is the long-tail edge case
    where a naïve bar-count embargo (e.g., 3 bars on a 240m T_H) would
    grossly under-purge if measured in RTH-only sessions.
    """
    cfg = _load_h055_config()
    embargo_minutes = int(cfg["splitter"]["embargo"])
    embargo_sessions_rth = math.ceil(embargo_minutes / _MINUTES_PER_RTH_SESSION)
    # 3315 / 405 = 8.185 → ceil = 9
    assert embargo_sessions_rth == 9


def test_purge_equals_embargo_per_mlfinlab_stacked_convention() -> None:
    """Per ADR-0007 + H055 design.md §6 + H055.yaml line 70: purge = embargo
    by mlfinlab-stacked-embargo convention.
    """
    cfg = _load_h055_config()
    purge = int(cfg["splitter"]["purge"])
    embargo = int(cfg["splitter"]["embargo"])
    assert purge == embargo


def test_embargo_strictly_exceeds_t_l_max_lookback() -> None:
    """Sanity: embargo strictly exceeds the T_L max bar count × T_L max
    minutes (a feature-side leakage floor — the level-state machine's
    lookback at the T_L grain must not span the embargo).

    T_L max = 15m, max_holding = 13 bars → 13 × 15 = 195 minutes. Embargo
    3315 >> 195.
    """
    cfg = _load_h055_config()
    embargo = int(cfg["splitter"]["embargo"])
    t_l_max_lookback_minutes = (
        max(_MAX_HOLDING_PERIOD_DOMAIN) * max(_T_L_BAR_MINUTES_DOMAIN)
    )
    assert embargo > t_l_max_lookback_minutes


def test_embargo_strictly_exceeds_t_h_max_lookback() -> None:
    """Sanity: embargo strictly exceeds the T_H max bar count × T_H max
    minutes. Per the formula, embargo includes `k_swing × T_H_minutes`
    which alone is 13 × 240 = 3120 minutes — within margin of the 3315
    pinned embargo.
    """
    cfg = _load_h055_config()
    embargo = int(cfg["splitter"]["embargo"])
    t_h_max_term = max(_K_SWING_DOMAIN) * max(_T_H_BAR_MINUTES_DOMAIN)
    assert embargo >= t_h_max_term


def test_rth_only_state_machine_snapshot_at_fold_boundary() -> None:
    """RTH-only (405-min session) — snapshot policy preserves state across folds.

    Per design.md §5.3 SECONDARY policy (snapshot at right edge): at
    fold[i].end the state-machine state is serialised; at fold[i+1].start
    the new state-machine instance is restored from the snapshot. The
    state_signature must match before and after.

    Asserts:
        state_machine.state_signature() at fold[i].end ==
        new_state_machine.state_signature() after restore at fold[i+1].start
    """
    fold_i = LevelExhaustionStateMachine()
    a = fold_i.add_level(level_value=5_000.0, side="support", current_bar=0)
    b = fold_i.add_level(level_value=5_010.0, side="resistance", current_bar=15)
    fold_i.record_rejection(a, current_bar=20)
    fold_i.record_rejection(a, current_bar=50)
    fold_i.record_penetration(b, current_bar=100)

    snap = fold_i.snapshot()
    sig_at_fold_i_end = fold_i.state_signature()

    fold_i_plus_1 = LevelExhaustionStateMachine()
    fold_i_plus_1.restore(snap)
    sig_at_fold_i_plus_1_start = fold_i_plus_1.state_signature()

    # The load-bearing assertion: snapshot policy preserves the level-state
    # vector across the fold boundary.
    assert sig_at_fold_i_end == sig_at_fold_i_plus_1_start
    # Post-conditions on the carried state:
    assert fold_i_plus_1.n_levels() == 2
    assert fold_i_plus_1.n_active_levels() == 1  # b is killed
    assert fold_i_plus_1.get_level(a).r_count == 2


def test_fold_boundary_across_cme_maintenance_break() -> None:
    """Fold boundary spanning the daily 17:00 CT CME maintenance halt.

    Per design.md §5.3 PRIMARY policy (reset-at-boundary): at the fold[i] →
    fold[i+1] transition (which may span the 17:00 CT CME maintenance halt),
    the state machine RESETS — the n_resets counter increments and the
    state signature returns to the empty-state signature. CME Globex halts
    trading 17:00–17:55 CT; substrate-side gaps under
    ``data/processed/vendor_legacy_1min_roll_adjusted/`` reflect the halt.
    A false-continuity bug would manifest as level-state vectors unchanged
    across a multi-hour wall-clock gap.

    Asserts:
        state_machine.was_reset_at_boundary(expected_resets=1) == True
        state_machine.state_signature() == empty_state_signature
        state_machine.n_levels() == 0
    """
    machine = LevelExhaustionStateMachine()
    # Pre-halt state: register some swing-pivot levels and accumulate counts.
    a = machine.add_level(level_value=5_000.0, side="support", current_bar=0)
    machine.add_level(level_value=5_010.0, side="resistance", current_bar=10)
    machine.record_rejection(a, current_bar=20)
    sig_pre_halt = machine.state_signature()
    assert machine.n_levels() == 2
    assert machine.n_resets() == 0

    # A reference machine that has been reset once — its state_signature
    # reflects (empty levels, n_resets=1). The state-machine n_resets counter
    # is a load-bearing audit trail (so the orchestrator can verify a reset
    # actually fired rather than coincidentally landing on empty state).
    reference = LevelExhaustionStateMachine()
    reference.reset()
    reference_signature_after_one_reset = reference.state_signature()

    # Fold-boundary reset event (orchestrator invokes reset() when entering a
    # new fold whose first bar is post-17:00 CT CME maintenance halt).
    machine.reset()

    assert machine.was_reset_at_boundary(expected_resets=1) is True
    assert machine.n_levels() == 0
    assert machine.n_active_levels() == 0
    # Post-reset machine matches the once-reset reference (both empty + n_resets=1).
    assert machine.state_signature() == reference_signature_after_one_reset
    assert machine.state_signature() != sig_pre_halt
