"""H055 Component 3 — level-exhaustion state machine R(L) per design.md §3 + §5.3.

State machine on swing-pivot levels:
  - Touch at t: |P_t − L| ≤ δ · ATR_n (interpretation layer; not modelled here)
  - Rejection within k bars of touch: R(L) += 1
  - Penetration within k bars: R(L) → ∞ (level killed)
  - Entry permitted while R(L) ≤ R*

Layered design (per Round-1 audit-discipline):
  This module implements the EVENT-LEVEL state machine — callers explicitly
  record rejections / penetrations against tracked levels. The bar-by-bar
  PRICE-ACTION interpretation (deciding from OHLCV + ATR + δ + γ + k whether
  a given bar constitutes a touch, rejection, or penetration) is a separate
  concern at the feature-factory layer (pending `P1-H055-FEATURE-FACTORY-IMPL`).

Fold-boundary policies (per H055 design.md §5.3):
  - **PRIMARY (reset)**: state machine clears at each fold boundary to
    eliminate forward-looking contamination (`reset()`).
  - **SECONDARY (snapshot)**: snapshot the state at the embargo's right edge
    and restore at fold[i+1].start (`snapshot()` + `restore()`); §14 robustness
    exhibit only.

Practitioner heuristic: "third test breaks" (R* ∈ {2, 3} central case).
Formal cousin: limit-order-book level memory per Bouchaud-Gefen-Potters-Wyart
2004 ([DOI 10.1080/14697680400000022](https://doi.org/10.1080/14697680400000022)).

Closes follow-up `P1-H055-LEVEL-EXHAUSTION-STATE-MACHINE-IMPL` and the 2
deferred B1 fold-continuity tests at
[tests/unit/test_h055_level_state_fold_continuity.py](../../../tests/unit/test_h055_level_state_fold_continuity.py).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Final, Literal

__all__ = [
    "LevelExhaustionStateMachine",
    "LevelState",
]

_SCHEMA_VERSION: Final[str] = "h055_level_state_v1"

_ALLOWED_SIDES: Final[frozenset[str]] = frozenset({"support", "resistance"})


@dataclass(frozen=True)
class LevelState:
    """One swing-pivot level under tracking.

    Args:
        level_id: Unique integer identifier within a state machine.
        level_value: Price (positive float).
        side: "support" if the level was formed below price (prior tape was
            on the upside) or "resistance" if formed above price.
        created_at_bar: Integer bar index at which the level was registered.
        r_count: Current value of R(L) — number of recorded rejections.
        killed: True if R(L) → ∞ (penetration occurred); no further updates.
        last_event_bar: Integer bar index of the most recent event (rejection,
            penetration, or registration). None if no events yet.
    """

    level_id: int
    level_value: float
    side: str
    created_at_bar: int
    r_count: int = 0
    killed: bool = False
    last_event_bar: int | None = None


@dataclass
class LevelExhaustionStateMachine:
    """State machine on swing-pivot levels per H055 design.md §3 Component 3.

    Methods:
        add_level: register a new swing-pivot level.
        record_rejection: R(L) += 1 on a tracked level.
        record_penetration: R(L) → ∞ on a tracked level (killed).
        is_entry_permitted_at_level: True iff R(L) ≤ R* AND level not killed.
        reset: clear all levels (PRIMARY fold-boundary policy).
        snapshot: serialise state for SECONDARY snapshot fold-boundary policy.
        restore: rehydrate from a snapshot dict.
        state_signature: deterministic SHA256 over canonical-JSON state.

    Per CLAUDE.md §Reproducibility, the H055 walk-forward orchestrator MUST
    log `state_signature()` to the per-fold ReproLog so the level-state at
    fold-boundary transitions is auditable.
    """

    _levels: dict[int, LevelState] = field(default_factory=dict)
    _next_level_id: int = 0
    _n_resets: int = 0

    def add_level(
        self,
        level_value: float,
        side: str,
        current_bar: int,
    ) -> int:
        """Register a new swing-pivot level.

        Args:
            level_value: Price; must be positive (a futures-price level).
            side: "support" or "resistance".
            current_bar: Integer bar index at registration.

        Returns:
            The new level's `level_id` (unique within this state machine
            instance; reset to 0 after `reset()`).

        Raises:
            ValueError: invalid side or non-positive level_value.
        """
        if level_value <= 0.0:
            raise ValueError(f"level_value must be positive, got {level_value}")
        if side not in _ALLOWED_SIDES:
            raise ValueError(
                f"side must be one of {sorted(_ALLOWED_SIDES)}, got {side!r}"
            )
        level_id = self._next_level_id
        self._next_level_id += 1
        self._levels[level_id] = LevelState(
            level_id=level_id,
            level_value=float(level_value),
            side=side,
            created_at_bar=int(current_bar),
            r_count=0,
            killed=False,
            last_event_bar=int(current_bar),
        )
        return level_id

    def _replace_level(self, level_id: int, **changes: Any) -> None:
        existing = self._levels.get(level_id)
        if existing is None:
            raise KeyError(f"level_id {level_id} not tracked")
        # Frozen-dataclass replacement
        from dataclasses import replace
        self._levels[level_id] = replace(existing, **changes)

    def record_rejection(self, level_id: int, current_bar: int) -> None:
        """Record a rejection event at the named level: R(L) += 1.

        Per design.md §3 Component 3: a "rejection" is the bar-pattern
        observation that, after a touch on level L, price closes beyond L
        on the same side as the prior tape AND reverts by ≥ γ · ATR_n
        within k bars. The interpretation layer (feature factory) decides
        when this condition is met; this method just increments the counter.

        Raises:
            KeyError: level_id not tracked.
            RuntimeError: level is already killed (penetration occurred).
        """
        existing = self._levels.get(level_id)
        if existing is None:
            raise KeyError(f"level_id {level_id} not tracked")
        if existing.killed:
            raise RuntimeError(
                f"level_id {level_id} already killed (penetration); cannot rejection-update"
            )
        self._replace_level(
            level_id,
            r_count=existing.r_count + 1,
            last_event_bar=int(current_bar),
        )

    def record_penetration(self, level_id: int, current_bar: int) -> None:
        """Record a penetration event: R(L) → ∞ (killed); level_id no
        longer permits entry.

        Per design.md §3 Component 3: a "penetration" is the bar-pattern
        observation that price closes through L within k bars of touch.
        Once penetrated, the level is permanently killed within this fold
        (re-eligibility requires a new swing-pivot detection at the same
        price level, which gets a fresh level_id).
        """
        existing = self._levels.get(level_id)
        if existing is None:
            raise KeyError(f"level_id {level_id} not tracked")
        if existing.killed:
            return  # idempotent: re-penetration on killed level is a no-op
        self._replace_level(level_id, killed=True, last_event_bar=int(current_bar))

    def is_entry_permitted_at_level(self, level_id: int, r_max: int) -> bool:
        """Per design.md §3 Component 3: entry permitted while R(L) ≤ R*.

        Args:
            level_id: tracked level identifier.
            r_max: R* threshold (operator-pinned per H055.yaml search domain
                R* ∈ {1, 2, 3, 4} per design.md §5.6).

        Returns:
            True iff the level is not killed AND R(L) ≤ r_max.
        """
        existing = self._levels.get(level_id)
        if existing is None:
            return False
        if existing.killed:
            return False
        return existing.r_count <= r_max

    def get_level(self, level_id: int) -> LevelState | None:
        """Return the LevelState for a given level_id, or None if not tracked."""
        return self._levels.get(level_id)

    def n_levels(self) -> int:
        """Total number of tracked levels (active + killed)."""
        return len(self._levels)

    def n_active_levels(self) -> int:
        """Number of non-killed levels."""
        return sum(1 for s in self._levels.values() if not s.killed)

    def n_resets(self) -> int:
        """Cumulative count of reset() invocations on this instance."""
        return self._n_resets

    def reset(self) -> None:
        """Clear all levels — PRIMARY fold-boundary policy per design.md §5.3.

        Increments n_resets() so a downstream auditor can verify the
        state-machine was actually reset (rather than coincidentally empty).
        """
        self._levels.clear()
        self._next_level_id = 0
        self._n_resets += 1

    def snapshot(self) -> dict[str, Any]:
        """Serialise the full state machine for SECONDARY snapshot fold policy.

        Per design.md §5.3 alternative policy: at fold[i].end the state vector
        is serialised and rehydrated at fold[i+1].start (no recomputation).
        Used in §14 robustness exhibit.

        Returns:
            JSON-serialisable dict with all levels + counters.
        """
        return {
            "schema_version": _SCHEMA_VERSION,
            "next_level_id": self._next_level_id,
            "n_resets": self._n_resets,
            "levels": [
                {
                    "level_id": s.level_id,
                    "level_value": s.level_value,
                    "side": s.side,
                    "created_at_bar": s.created_at_bar,
                    "r_count": s.r_count,
                    "killed": s.killed,
                    "last_event_bar": s.last_event_bar,
                }
                for s in sorted(
                    self._levels.values(), key=lambda s: s.level_id
                )
            ],
        }

    def restore(self, state: dict[str, Any]) -> None:
        """Rehydrate from a snapshot dict.

        Raises:
            ValueError: schema_version mismatch or malformed state.
        """
        if not isinstance(state, dict):
            raise ValueError(f"state must be a dict, got {type(state).__name__}")
        schema = state.get("schema_version")
        if schema != _SCHEMA_VERSION:
            raise ValueError(
                f"schema_version mismatch: expected {_SCHEMA_VERSION!r}, got "
                f"{schema!r}"
            )
        levels_raw = state.get("levels")
        if not isinstance(levels_raw, list):
            raise ValueError("state['levels'] must be a list")
        next_id = state.get("next_level_id")
        if not isinstance(next_id, int) or next_id < 0:
            raise ValueError(
                f"state['next_level_id'] must be a non-negative int, got "
                f"{next_id!r}"
            )
        n_resets = state.get("n_resets")
        if not isinstance(n_resets, int) or n_resets < 0:
            raise ValueError(
                f"state['n_resets'] must be a non-negative int, got {n_resets!r}"
            )

        self._levels.clear()
        for raw in levels_raw:
            level = LevelState(
                level_id=int(raw["level_id"]),
                level_value=float(raw["level_value"]),
                side=str(raw["side"]),
                created_at_bar=int(raw["created_at_bar"]),
                r_count=int(raw["r_count"]),
                killed=bool(raw["killed"]),
                last_event_bar=(
                    int(raw["last_event_bar"])
                    if raw.get("last_event_bar") is not None
                    else None
                ),
            )
            self._levels[level.level_id] = level
        self._next_level_id = next_id
        self._n_resets = n_resets

    def state_signature(self) -> str:
        """Deterministic SHA256 over canonical-JSON-encoded state.

        Used by the walk-forward orchestrator's per-fold ReproLog to bind
        the level-state at fold transitions, enabling fold-continuity audits.
        """
        payload = self.snapshot()
        serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialised.encode("utf-8")).hexdigest()

    def was_reset_at_boundary(self, expected_resets: int) -> bool:
        """Test-helper: True iff this state machine has been reset at least
        `expected_resets` times.

        Used by the B1 fold-continuity test
        `test_fold_boundary_across_cme_maintenance_break` to assert that the
        primary policy actually fired the reset() at the fold-boundary
        transition (not just coincidentally landed in an empty state).
        """
        return self._n_resets >= expected_resets
