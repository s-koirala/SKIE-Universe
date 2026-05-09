"""Unit tests for the H055 Component 3 level-exhaustion state machine.

Covers:
- LevelState dataclass: validation, immutability.
- LevelExhaustionStateMachine: add/record/permission/reset/snapshot/restore.
- Schema-version + roundtrip safety.
- state_signature determinism + change-on-mutation.
- Edge cases: penetrate-then-rejection rejected; idempotent re-penetration;
  unknown level_id.
"""

from __future__ import annotations

import pytest

from skie_ninja.features.h055.level_state import (
    LevelExhaustionStateMachine,
    LevelState,
)


# ─── LevelState dataclass ────────────────────────────────────────────────────


def test_level_state_construction() -> None:
    s = LevelState(
        level_id=0,
        level_value=5_000.0,
        side="support",
        created_at_bar=42,
    )
    assert s.r_count == 0
    assert s.killed is False
    assert s.last_event_bar is None


def test_level_state_immutable() -> None:
    s = LevelState(level_id=0, level_value=5_000.0, side="support", created_at_bar=0)
    with pytest.raises(Exception):
        s.r_count = 5  # type: ignore[misc]


# ─── LevelExhaustionStateMachine — basic API ─────────────────────────────────


def test_machine_starts_empty() -> None:
    m = LevelExhaustionStateMachine()
    assert m.n_levels() == 0
    assert m.n_active_levels() == 0
    assert m.n_resets() == 0


def test_add_level_returns_unique_ids() -> None:
    m = LevelExhaustionStateMachine()
    a = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    b = m.add_level(level_value=5_010.0, side="resistance", current_bar=1)
    assert a == 0
    assert b == 1
    assert m.n_levels() == 2
    assert m.n_active_levels() == 2


def test_add_level_rejects_invalid_side() -> None:
    m = LevelExhaustionStateMachine()
    with pytest.raises(ValueError, match="side"):
        m.add_level(level_value=5_000.0, side="middle", current_bar=0)


def test_add_level_rejects_nonpositive_value() -> None:
    m = LevelExhaustionStateMachine()
    with pytest.raises(ValueError, match="level_value"):
        m.add_level(level_value=0.0, side="support", current_bar=0)
    with pytest.raises(ValueError, match="level_value"):
        m.add_level(level_value=-100.0, side="support", current_bar=0)


# ─── Rejection / penetration counters ────────────────────────────────────────


def test_record_rejection_increments_r_count() -> None:
    m = LevelExhaustionStateMachine()
    lid = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    m.record_rejection(lid, current_bar=5)
    assert m.get_level(lid).r_count == 1
    m.record_rejection(lid, current_bar=10)
    assert m.get_level(lid).r_count == 2
    assert m.get_level(lid).last_event_bar == 10


def test_record_penetration_kills_level() -> None:
    m = LevelExhaustionStateMachine()
    lid = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    m.record_penetration(lid, current_bar=7)
    assert m.get_level(lid).killed is True
    assert m.n_active_levels() == 0


def test_record_rejection_after_penetration_raises() -> None:
    m = LevelExhaustionStateMachine()
    lid = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    m.record_penetration(lid, current_bar=5)
    with pytest.raises(RuntimeError, match="killed"):
        m.record_rejection(lid, current_bar=10)


def test_record_penetration_idempotent() -> None:
    m = LevelExhaustionStateMachine()
    lid = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    m.record_penetration(lid, current_bar=5)
    # Second penetration on already-killed level: no-op (no exception).
    m.record_penetration(lid, current_bar=10)
    assert m.get_level(lid).killed is True


def test_record_against_unknown_level_raises() -> None:
    m = LevelExhaustionStateMachine()
    with pytest.raises(KeyError):
        m.record_rejection(level_id=999, current_bar=0)
    with pytest.raises(KeyError):
        m.record_penetration(level_id=999, current_bar=0)


# ─── is_entry_permitted_at_level ─────────────────────────────────────────────


def test_entry_permitted_below_r_max() -> None:
    m = LevelExhaustionStateMachine()
    lid = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    # R(L) = 0 <= R* = 2 → permitted
    assert m.is_entry_permitted_at_level(lid, r_max=2) is True
    m.record_rejection(lid, current_bar=5)
    # R(L) = 1 <= 2 → still permitted
    assert m.is_entry_permitted_at_level(lid, r_max=2) is True
    m.record_rejection(lid, current_bar=10)
    # R(L) = 2 <= 2 → still permitted (boundary inclusive)
    assert m.is_entry_permitted_at_level(lid, r_max=2) is True


def test_entry_blocked_above_r_max() -> None:
    m = LevelExhaustionStateMachine()
    lid = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    for i in range(3):
        m.record_rejection(lid, current_bar=i + 1)
    # R(L) = 3 > 2 → blocked
    assert m.is_entry_permitted_at_level(lid, r_max=2) is False


def test_entry_blocked_after_penetration() -> None:
    m = LevelExhaustionStateMachine()
    lid = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    m.record_penetration(lid, current_bar=5)
    assert m.is_entry_permitted_at_level(lid, r_max=2) is False


def test_entry_blocked_for_unknown_level() -> None:
    m = LevelExhaustionStateMachine()
    assert m.is_entry_permitted_at_level(level_id=999, r_max=2) is False


# ─── reset (PRIMARY fold-boundary policy) ────────────────────────────────────


def test_reset_clears_state_and_increments_counter() -> None:
    m = LevelExhaustionStateMachine()
    m.add_level(level_value=5_000.0, side="support", current_bar=0)
    m.add_level(level_value=5_010.0, side="resistance", current_bar=1)
    assert m.n_levels() == 2
    sig_before = m.state_signature()

    m.reset()
    assert m.n_levels() == 0
    assert m.n_active_levels() == 0
    assert m.n_resets() == 1
    assert m.state_signature() != sig_before


def test_reset_preserves_n_resets_across_invocations() -> None:
    m = LevelExhaustionStateMachine()
    m.reset()
    m.reset()
    m.reset()
    assert m.n_resets() == 3


def test_reset_resets_level_id_counter() -> None:
    m = LevelExhaustionStateMachine()
    m.add_level(level_value=5_000.0, side="support", current_bar=0)
    m.add_level(level_value=5_010.0, side="resistance", current_bar=1)
    m.reset()
    new_id = m.add_level(level_value=4_990.0, side="support", current_bar=2)
    assert new_id == 0  # counter restarts after reset


# ─── snapshot / restore (SECONDARY fold-boundary policy) ─────────────────────


def test_snapshot_restore_roundtrip_preserves_state_signature() -> None:
    m = LevelExhaustionStateMachine()
    a = m.add_level(level_value=5_000.0, side="support", current_bar=0)
    b = m.add_level(level_value=5_010.0, side="resistance", current_bar=1)
    m.record_rejection(a, current_bar=5)
    m.record_rejection(a, current_bar=8)
    m.record_penetration(b, current_bar=12)

    snap = m.snapshot()
    sig_before = m.state_signature()

    m2 = LevelExhaustionStateMachine()
    m2.restore(snap)
    assert m2.state_signature() == sig_before
    assert m2.n_levels() == 2
    assert m2.n_active_levels() == 1  # b is killed
    assert m2.get_level(a).r_count == 2


def test_restore_rejects_unknown_schema_version() -> None:
    m = LevelExhaustionStateMachine()
    with pytest.raises(ValueError, match="schema_version"):
        m.restore({"schema_version": "future_v9999", "levels": [], "next_level_id": 0, "n_resets": 0})


def test_restore_rejects_malformed_state() -> None:
    m = LevelExhaustionStateMachine()
    with pytest.raises(ValueError):
        m.restore({"schema_version": "h055_level_state_v1"})  # missing fields
    with pytest.raises(ValueError):
        m.restore({
            "schema_version": "h055_level_state_v1",
            "levels": "not-a-list",
            "next_level_id": 0,
            "n_resets": 0,
        })


def test_snapshot_is_json_serialisable() -> None:
    import json

    m = LevelExhaustionStateMachine()
    m.add_level(level_value=5_000.0, side="support", current_bar=0)
    snap = m.snapshot()
    # Round-trip via JSON
    s = json.dumps(snap)
    parsed = json.loads(s)
    m2 = LevelExhaustionStateMachine()
    m2.restore(parsed)
    assert m2.state_signature() == m.state_signature()


# ─── state_signature determinism + change-on-mutation ────────────────────────


def test_state_signature_deterministic_under_identical_history() -> None:
    a = LevelExhaustionStateMachine()
    a.add_level(level_value=5_000.0, side="support", current_bar=0)
    a.record_rejection(0, current_bar=3)

    b = LevelExhaustionStateMachine()
    b.add_level(level_value=5_000.0, side="support", current_bar=0)
    b.record_rejection(0, current_bar=3)

    assert a.state_signature() == b.state_signature()


def test_state_signature_changes_under_rejection() -> None:
    m = LevelExhaustionStateMachine()
    m.add_level(level_value=5_000.0, side="support", current_bar=0)
    sig_before = m.state_signature()
    m.record_rejection(0, current_bar=3)
    assert m.state_signature() != sig_before


def test_state_signature_changes_under_penetration() -> None:
    m = LevelExhaustionStateMachine()
    m.add_level(level_value=5_000.0, side="support", current_bar=0)
    sig_before = m.state_signature()
    m.record_penetration(0, current_bar=3)
    assert m.state_signature() != sig_before


def test_was_reset_at_boundary_helper() -> None:
    m = LevelExhaustionStateMachine()
    assert m.was_reset_at_boundary(expected_resets=1) is False
    m.reset()
    assert m.was_reset_at_boundary(expected_resets=1) is True
    assert m.was_reset_at_boundary(expected_resets=2) is False
    m.reset()
    assert m.was_reset_at_boundary(expected_resets=2) is True
