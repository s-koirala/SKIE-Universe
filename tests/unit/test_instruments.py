"""Unit tests for src/skie_ninja/utils/instruments.py (P0-4 acceptance)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from skie_ninja.utils.instruments import InstrumentSpec, load_instruments

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTRUMENTS_YAML = REPO_ROOT / "config" / "instruments.yaml"


def test_loads_repo_yaml() -> None:
    specs = load_instruments(INSTRUMENTS_YAML)
    assert set(specs.keys()) >= {"ES", "NQ", "MES", "MNQ"}
    for root in ("ES", "NQ", "MES", "MNQ"):
        spec = specs[root]
        assert isinstance(spec, InstrumentSpec)
        assert spec.exchange == "CME"
        assert spec.tick_size > 0
        assert spec.tick_value > 0
        assert spec.multiplier > 0
        assert spec.commission_per_side_usd >= 0
        assert spec.exchange_fee_usd >= 0
        assert spec.nfa_fee_usd == pytest.approx(0.02)  # NFA Section 13
        assert spec.roll_rule.method == "volume_crossover"
        assert spec.roll_rule.window_days >= 1


def test_es_tick_economics() -> None:
    # ES: tick_size 0.25, multiplier 50 -> tick_value 12.50.
    specs = load_instruments(INSTRUMENTS_YAML)
    es = specs["ES"]
    assert es.tick_value == pytest.approx(es.tick_size * es.multiplier)
    mes = specs["MES"]
    assert mes.tick_value == pytest.approx(mes.tick_size * mes.multiplier)


def test_roundtrip(tmp_path: Path) -> None:
    specs = load_instruments(INSTRUMENTS_YAML)
    out = {
        "instruments": {
            root: spec.model_dump(exclude_none=True, exclude={"root"})
            for root, spec in specs.items()
        }
    }
    p = tmp_path / "round.yaml"
    p.write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf-8")
    specs2 = load_instruments(p)
    assert set(specs2.keys()) == set(specs.keys())
    for root, spec in specs.items():
        assert specs2[root].model_dump() == spec.model_dump()


def test_missing_field_rejected(tmp_path: Path) -> None:
    bad = {
        "instruments": {
            "ES": {
                "exchange": "CME",
                "description": "E-mini S&P 500",
                "tick_size": 0.25,
                # tick_value missing
                "multiplier": 50.0,
                "session_rth": "08:30-15:15",
                "session_eth": "17:00-16:00",
                "roll_rule": {
                    "method": "volume_crossover",
                    "window_days": 5,
                    "reference": "x",
                },
                "commission_per_side_usd": 0.85,
                "exchange_fee_usd": 1.18,
                "nfa_fee_usd": 0.02,
            }
        }
    }
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_instruments(p)


def test_extra_field_rejected(tmp_path: Path) -> None:
    bad = {
        "instruments": {
            "ES": {
                "exchange": "CME",
                "description": "E-mini S&P 500",
                "tick_size": 0.25,
                "tick_value": 12.5,
                "multiplier": 50.0,
                "session_rth": "08:30-15:15",
                "session_eth": "17:00-16:00",
                "roll_rule": {
                    "method": "volume_crossover",
                    "window_days": 5,
                    "reference": "x",
                },
                "commission_per_side_usd": 0.85,
                "exchange_fee_usd": 1.18,
                "nfa_fee_usd": 0.02,
                "garbage_field": True,
            }
        }
    }
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_instruments(p)


@pytest.mark.parametrize(
    "bad_session",
    [
        "08:30-",          # missing right side
        "-15:15",          # missing left side
        "0830-1515",       # missing colons
        "8:30-15:15",      # hours not zero-padded
        "08:30-15:15 CT",  # trailing suffix
        "25:00-15:15",     # hour out of range
        "08:60-15:15",     # minute out of range
        "08:30-15:15-",    # trailing dash
        "",                # empty string
        "08:30-15:15 ",    # trailing whitespace
    ],
)
def test_session_regex_rejects_malformations(tmp_path: Path, bad_session: str) -> None:
    bad = {
        "instruments": {
            "ES": {
                "exchange": "CME",
                "description": "E-mini S&P 500",
                "tick_size": 0.25,
                "tick_value": 12.5,
                "multiplier": 50.0,
                "session_rth": bad_session,
                "session_eth": "17:00-16:00",
                "roll_rule": {
                    "method": "volume_crossover",
                    "window_days": 5,
                    "reference": "x",
                },
                "commission_per_side_usd": 0.85,
                "exchange_fee_usd": 1.18,
                "nfa_fee_usd": 0.02,
            }
        }
    }
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_instruments(p)


def test_commission_unreviewed_emits_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Phase-0: null commission_reviewed_for_broker must log a WARNING,
    not hard-fail (audit F-2-17)."""
    import logging

    good = {
        "instruments": {
            "ES": {
                "exchange": "CME",
                "description": "E-mini S&P 500",
                "tick_size": 0.25,
                "tick_value": 12.5,
                "multiplier": 50.0,
                "session_rth": "08:30-15:15",
                "session_eth": "17:00-16:00",
                "roll_rule": {
                    "method": "volume_crossover",
                    "window_days": 5,
                    "reference": "x",
                },
                "commission_per_side_usd": 0.85,
                "exchange_fee_usd": 1.18,
                "nfa_fee_usd": 0.02,
                "commission_reviewed_for_broker": None,
            }
        }
    }
    p = tmp_path / "good.yaml"
    p.write_text(yaml.safe_dump(good), encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="skie_ninja.utils.instruments"):
        specs = load_instruments(p)
    assert specs["ES"].commission_reviewed_for_broker is None
    assert any(
        "commission_reviewed_for_broker is null" in rec.message for rec in caplog.records
    ), "expected a WARNING about null commission_reviewed_for_broker"


def test_commission_reviewed_no_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    good = {
        "instruments": {
            "ES": {
                "exchange": "CME",
                "description": "E-mini S&P 500",
                "tick_size": 0.25,
                "tick_value": 12.5,
                "multiplier": 50.0,
                "session_rth": "08:30-15:15",
                "session_eth": "17:00-16:00",
                "roll_rule": {
                    "method": "volume_crossover",
                    "window_days": 5,
                    "reference": "x",
                },
                "commission_per_side_usd": 0.85,
                "exchange_fee_usd": 1.18,
                "nfa_fee_usd": 0.02,
                "commission_reviewed_for_broker": "NINJATRADER_BROKERAGE_UNLIMITED",
            }
        }
    }
    p = tmp_path / "good.yaml"
    p.write_text(yaml.safe_dump(good), encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="skie_ninja.utils.instruments"):
        load_instruments(p)
    assert not any(
        "commission_reviewed_for_broker is null" in rec.message for rec in caplog.records
    )


def test_roll_window_no_upper_bound(tmp_path: Path) -> None:
    """F-2-6: upper bound on window_days was removed; large values accepted."""
    good = {
        "instruments": {
            "ES": {
                "exchange": "CME",
                "description": "E-mini S&P 500",
                "tick_size": 0.25,
                "tick_value": 12.5,
                "multiplier": 50.0,
                "session_rth": "08:30-15:15",
                "session_eth": "17:00-16:00",
                "roll_rule": {
                    "method": "volume_crossover",
                    "window_days": 365,
                    "reference": "x",
                },
                "commission_per_side_usd": 0.85,
                "exchange_fee_usd": 1.18,
                "nfa_fee_usd": 0.02,
            }
        }
    }
    p = tmp_path / "good.yaml"
    p.write_text(yaml.safe_dump(good), encoding="utf-8")
    specs = load_instruments(p)
    assert specs["ES"].roll_rule.window_days == 365


def test_main_entrypoint_validates_repo_yaml() -> None:
    from skie_ninja.utils.instruments import _main

    assert _main(["prog", str(INSTRUMENTS_YAML)]) == 0


def test_main_entrypoint_nonzero_on_bad_yaml(tmp_path: Path) -> None:
    from skie_ninja.utils.instruments import _main

    bad = {"instruments": {"ES": {"exchange": "CME"}}}  # missing required fields
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad), encoding="utf-8")
    assert _main(["prog", str(p)]) == 1


def test_negative_tick_size_rejected(tmp_path: Path) -> None:
    bad = {
        "instruments": {
            "ES": {
                "exchange": "CME",
                "description": "E-mini S&P 500",
                "tick_size": -0.25,
                "tick_value": 12.5,
                "multiplier": 50.0,
                "session_rth": "08:30-15:15",
                "session_eth": "17:00-16:00",
                "roll_rule": {
                    "method": "volume_crossover",
                    "window_days": 5,
                    "reference": "x",
                },
                "commission_per_side_usd": 0.85,
                "exchange_fee_usd": 1.18,
                "nfa_fee_usd": 0.02,
            }
        }
    }
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_instruments(p)
