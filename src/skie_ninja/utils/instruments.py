"""Instruments registry loader.

Implements P0-4 per plan/buildouts/implementation-plan_2026-04-15.md §P0-4.

Pydantic-validated specs for CME equity-index front-month contracts
(ES, NQ, MES, MNQ). Loader rejects missing fields.

Pre-live checklist (MUST enforce before any live-capital run):
    - `commission_reviewed_for_broker` set to the broker identifier
      actually used for execution (never null at that point).
    - `commission_per_side_usd` matches that broker's executed-contract
      rate sheet on file.

Phase-0 intentionally permits `commission_reviewed_for_broker: null`
and only emits a stdlib-`logging` WARNING, because no live broker is
yet bound. See audit finding F-2-17.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_logger = logging.getLogger(__name__)

_SESSION_RE = re.compile(r"^[0-2]\d:[0-5]\d-[0-2]\d:[0-5]\d$")


class RollRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["volume_crossover", "open_interest_crossover"]
    # justify: lower bound 1 = tick-level crossover permitted;
    # no evidence-based upper bound (Phase-1 follow-up
    # P1-ROLL-WINDOW will calibrate from OI/volume persistence
    # empirics on ES/NQ front-to-back transitions).
    window_days: int = Field(..., ge=1)
    reference: str


class FeeTier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tier_name: str
    monthly_volume_min: int
    monthly_volume_max: int | None = None
    exchange_fee_usd: float
    source: str


class InstrumentSpec(BaseModel):
    """One CME equity-index futures contract spec.

    Field set fixed by plan P0-4 acceptance criteria. `extra="forbid"`
    ensures any typo in YAML raises at load time.
    """

    model_config = ConfigDict(extra="forbid")

    root: str = Field(..., min_length=1, max_length=8)
    exchange: Literal["CME"]
    description: str
    tick_size: float = Field(..., gt=0)
    tick_value: float = Field(..., gt=0)
    multiplier: float = Field(..., gt=0)
    session_rth: str  # "HH:MM-HH:MM" CT
    session_eth: str
    roll_rule: RollRule
    commission_per_side_usd: float = Field(..., ge=0)
    exchange_fee_usd: float = Field(..., ge=0)
    nfa_fee_usd: float = Field(..., ge=0)
    micro_ratio: float | None = Field(default=None, gt=0)
    fee_tiers: list[FeeTier] | None = None
    data_vendor_symbol_databento: str | None = None
    commission_reviewed_for_broker: str | None = None
    notes: str | None = None

    @field_validator("session_rth", "session_eth")
    @classmethod
    def _validate_session_format(cls, v: str) -> str:
        if not _SESSION_RE.fullmatch(v):
            raise ValueError(
                "session string must match HH:MM-HH:MM (24h, zero-padded), "
                f"got {v!r}"
            )
        # Reject hour >= 24.
        left, right = v.split("-")
        for part in (left, right):
            hh = int(part[:2])
            if hh > 23:
                raise ValueError(
                    f"session hour must be in 00-23, got {part!r} in {v!r}"
                )
        return v

    @model_validator(mode="after")
    def _warn_if_commission_unreviewed(self) -> "InstrumentSpec":
        if self.commission_reviewed_for_broker is None:
            _logger.warning(
                "instrument %s: commission_reviewed_for_broker is null; "
                "pre-live checklist MUST bind this to a real broker id "
                "before any live-capital run (audit F-2-17).",
                self.root,
            )
        return self


def load_instruments(path: Path) -> dict[str, InstrumentSpec]:
    """Load and validate instruments YAML.

    Returns a mapping of root-symbol -> InstrumentSpec. Raises
    `pydantic.ValidationError` on any missing or malformed field.
    """
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "instruments" not in raw:
        raise ValueError(f"{path}: expected top-level 'instruments:' mapping")
    out: dict[str, InstrumentSpec] = {}
    for root, body in raw["instruments"].items():
        if not isinstance(body, dict):
            raise ValueError(f"{path}: instrument {root!r} body must be a mapping")
        spec = InstrumentSpec.model_validate({"root": root, **body})
        out[root] = spec
    return out


__all__ = ["FeeTier", "InstrumentSpec", "RollRule", "load_instruments"]


def _main(argv: list[str]) -> int:
    """Validate a YAML instruments file. Returns shell exit code."""
    from pydantic import ValidationError  # local import keeps module import cheap

    if len(argv) > 1:
        path = Path(argv[1])
    else:
        # Default: repo-layout config/instruments.yaml relative to this file.
        path = Path(__file__).resolve().parents[3] / "config" / "instruments.yaml"

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        specs = load_instruments(path)
    except (ValidationError, ValueError, OSError) as exc:
        _logger.error("validation failed for %s: %s", path, exc)
        return 1
    _logger.info("validated %d instruments from %s: %s", len(specs), path, sorted(specs))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
