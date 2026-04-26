"""Unit tests for the roll-adjusted continuous-contract derivative
(``vendor_legacy_1min_roll_adjusted``), Round-2 remediation.

Covers:
  - Rolling-window front-month detection by trailing cumulative volume.
  - Persistence guard rejection of short oscillations.
  - AFML §2.4.3 anchor (ρ = new_open / old_close at roll boundary).
  - Multi-roll cumulative back-adjustment chain.
  - **Return-preservation across roll boundary** — the fundamental
    invariant of ratio adjustment (de Prado 2018 ch.2 §2.4.3).
  - Schema compliance + cross-row invariants in ``validate``.
  - Deterministic tie-break when cumulative volumes tie.
  - Chain-continuity assertion for detected roll events.
  - NoOverlapError on absent anchor bars.
  - Empty input → empty schema-conformant output.
  - IngestJob protocol conformance + end-to-end write_processed +
    emit_provenance with evidence-bar flag + level-use-pit-safe flag.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandera.errors
import polars as pl
import pytest

from skie_ninja.data.ingest.vendor_legacy_1min_roll_adjusted import (
    NoOverlapError,
    RollEvent,
    VendorLegacy1minRollAdjustedIngestJob,
    _adjust_one_symbol,
    _assert_no_consecutive_year_collision,
    apply_persistence_guard,
    compute_roll_ratio_afml,
    detect_raw_front_month_by_day,
    detect_roll_events,
)
from skie_ninja.data.validation.schema import VendorLegacy1minRollAdjustedSchema

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _bar(ts: datetime, contract: str, symbol: str, price: float, volume: int) -> dict:
    """One vendor_legacy_1min-shaped row with sane OHLC around *price*."""
    return {
        "ts_event": ts,
        "rtype": 34,
        "publisher_id": 1,
        "instrument_id": 42,
        "open": price,
        "high": price + 0.25,
        "low": price - 0.25,
        "close": price + 0.05,
        "volume": volume,
        "contract_symbol": contract,
        "symbol": symbol,
    }


def _two_contract_frame(
    old: str = "ESH4",
    new: str = "ESM4",
    old_last_close: float = 4000.0,
    new_first_open: float = 4020.0,
) -> pl.DataFrame:
    """Two-contract ES fixture with one committed roll.

    Structure (all UTC times; bars outside these are omitted):
      - old-only sessions: 2024-03-01..2024-03-04 (4 sessions), old has
        high daily volume (1000 each session). New exists only on
        2024-03-05 onward.
      - Transition session: 2024-03-05 is the first session where
        ``new`` is dominant. Old contract has ZERO bars on or after
        2024-03-05 (clean hand-off).
      - ``old_last_close`` is the close of the last bar of old on
        2024-03-04 (its last-as-front session).
      - ``new_first_open`` is the open of the first bar of new on
        2024-03-05 (its first-as-front session).
      - Post-roll sessions: 2024-03-05..2024-03-11 (5 sessions) of new.

    With ``window_days=3`` persistence guard, the roll commits on
    2024-03-05 (new leads on 3 consecutive sessions 03-05, 03-06, 03-07).
    """
    rows: list[dict] = []
    # Sessions 2024-03-01..2024-03-04: old contract only, high volume.
    base_price = 3995.0
    for session_idx, day in enumerate((1, 2, 3, 4)):
        for minute in range(10):
            ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
            rows.append(
                _bar(ts, old, "ES", base_price + session_idx * 0.5 + minute * 0.1, 100)
            )
    # Replace the very last old-contract bar close with old_last_close.
    # The last bar is day=4, minute=9 → close computed by _bar is
    # price+0.05. So set price = old_last_close - 0.05.
    rows[-1]["close"] = old_last_close
    # Re-derive consistent OHLC around the hard-set close.
    rows[-1]["open"] = old_last_close - 0.05
    rows[-1]["high"] = old_last_close + 0.10
    rows[-1]["low"] = old_last_close - 0.20

    # Sessions 2024-03-05..2024-03-11: new contract, high volume (5 sessions).
    new_base = new_first_open
    for session_idx, day in enumerate((5, 6, 7, 8, 11)):  # 9,10 = weekend
        for minute in range(10):
            ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
            price = new_base + session_idx * 0.5 + minute * 0.1
            rows.append(_bar(ts, new, "ES", price, 200))

    # First bar of new on 2024-03-05, minute 0: open must equal new_first_open.
    # Locate that row (first row whose contract==new and day==5, minute==30).
    for r in rows:
        if (
            r["contract_symbol"] == new
            and r["ts_event"] == datetime(2024, 3, 5, 14, 30, tzinfo=UTC)
        ):
            r["open"] = new_first_open
            r["high"] = new_first_open + 0.25
            r["low"] = new_first_open - 0.25
            r["close"] = new_first_open + 0.05
            break

    return pl.DataFrame(rows)


class _FakeCtx:
    """Minimal RunContext-shaped stand-in."""

    class _FakePaths:
        def __init__(self, root: Path) -> None:
            self._root = root
            (root / "data_processed").mkdir(parents=True, exist_ok=True)
            (root / "shared").mkdir(parents=True, exist_ok=True)

        @property
        def data_processed(self) -> Path:
            return self._root / "data_processed"

        @property
        def shared_vendor_skie_ninja_legacy(self) -> Path:
            return self._root / "shared"

        def ensure(self, p: Path) -> Path:
            p.mkdir(parents=True, exist_ok=True)
            return p

    def __init__(self, root: Path) -> None:
        self.paths = _FakeCtx._FakePaths(root)
        self.log = None
        self._checksums: dict[str, str] = {}

    def add_dataset_checksum(self, name: str, sha256: str) -> None:
        self._checksums[name] = sha256


# ---------------------------------------------------------------------------
# Rolling-window front-month detection
# ---------------------------------------------------------------------------


class TestRawFrontMonthDetection:
    def test_window_days_rolling_sum(self) -> None:
        df = _two_contract_frame()
        raw = detect_raw_front_month_by_day(df, window_days=3)
        # Old wins 03-01..03-04; new wins 03-05 onward.
        march5 = raw.filter(pl.col("session_date") == date(2024, 3, 5))
        assert march5["front_contract_symbol"][0] == "ESM4"
        march4 = raw.filter(pl.col("session_date") == date(2024, 3, 4))
        assert march4["front_contract_symbol"][0] == "ESH4"

    def test_tie_break_lexicographic(self) -> None:
        """Equal volume → lexicographically earliest contract wins."""
        ts = datetime(2024, 3, 1, 14, 30, tzinfo=UTC)
        rows = [
            _bar(ts, "ESM4", "ES", 4000.0, 500),
            _bar(ts + timedelta(minutes=1), "ESH4", "ES", 4000.0, 500),
        ]
        df = pl.DataFrame(rows)
        raw = detect_raw_front_month_by_day(df, window_days=1)
        assert raw["front_contract_symbol"][0] == "ESH4"

    def test_permutation_invariant(self) -> None:
        """Front-month decision is invariant to input row order."""
        df = _two_contract_frame()
        r1 = detect_raw_front_month_by_day(df, window_days=3)
        r2 = detect_raw_front_month_by_day(df.sample(fraction=1.0, seed=1), window_days=3)
        assert r1["front_contract_symbol"].to_list() == r2.sort(
            ["symbol", "session_date"]
        )["front_contract_symbol"].to_list()

    def test_rejects_zero_window(self) -> None:
        with pytest.raises(ValueError, match="window_days"):
            detect_raw_front_month_by_day(_two_contract_frame(), window_days=0)


# ---------------------------------------------------------------------------
# Persistence guard
# ---------------------------------------------------------------------------


class TestPersistenceGuard:
    def test_single_clean_transition_commits(self) -> None:
        df = _two_contract_frame()
        raw = detect_raw_front_month_by_day(df, window_days=3)
        effective, rejected = apply_persistence_guard(raw, window_days=3)
        # Transition commits once ESM4 has 3 consecutive sessions as raw winner.
        # After the guard, the earlier sessions get rewritten to the
        # committed winner (ESM4) starting from its first lead date.
        march7 = effective.filter(pl.col("session_date") == date(2024, 3, 7))
        assert march7["effective_front_contract_symbol"][0] == "ESM4"
        assert rejected == []  # no oscillations in this fixture

    def test_oscillation_rejected(self) -> None:
        """Build a synthetic front-by-day sequence that oscillates
        OLD -> NEW for one session -> back to OLD -> NEW for two
        sessions -> OLD; guard with window_days=3 should commit ZERO
        rolls and record the rejections in provenance."""
        raw = pl.DataFrame(
            {
                "symbol": ["ES"] * 7,
                "session_date": [
                    date(2024, 3, 1),
                    date(2024, 3, 4),
                    date(2024, 3, 5),
                    date(2024, 3, 6),
                    date(2024, 3, 7),
                    date(2024, 3, 8),
                    date(2024, 3, 11),
                ],
                "front_contract_symbol": [
                    "ESH4", "ESM4", "ESH4", "ESM4", "ESM4", "ESH4", "ESH4",
                ],
                "cumulative_volume": [1000, 500, 1000, 500, 500, 1000, 1000],
            }
        )
        effective, rejected = apply_persistence_guard(raw, window_days=3)
        # No roll should have committed — incumbent stays ESH4 throughout.
        assert effective["effective_front_contract_symbol"].unique().to_list() == ["ESH4"]
        # At least one rejected oscillation is recorded.
        assert len(rejected) >= 1

    def test_rejects_zero_window(self) -> None:
        raw = pl.DataFrame(
            {"symbol": [], "session_date": [], "front_contract_symbol": []}
        )
        with pytest.raises(ValueError, match="window_days"):
            apply_persistence_guard(raw, window_days=0)


# ---------------------------------------------------------------------------
# AFML §2.4.3 anchor computation
# ---------------------------------------------------------------------------


class TestRollRatioAFML:
    def test_ratio_uses_canonical_anchor(self) -> None:
        df = _two_contract_frame(
            old_last_close=4000.0, new_first_open=4020.0
        )
        raw = detect_raw_front_month_by_day(df, window_days=3)
        effective, _ = apply_persistence_guard(raw, window_days=3)
        events = detect_roll_events(effective)
        assert len(events) == 1
        rr = compute_roll_ratio_afml(df, events[0], "ES", effective)
        # Anchor: old last bar on 2024-03-04 (last session as front);
        # new first bar on 2024-03-05 (first session as front).
        assert rr.t_old_close_utc == datetime(2024, 3, 4, 14, 39, tzinfo=UTC)
        assert rr.t_new_open_utc == datetime(2024, 3, 5, 14, 30, tzinfo=UTC)
        assert math.isclose(rr.old_close, 4000.0, abs_tol=1e-9)
        assert math.isclose(rr.new_open, 4020.0, abs_tol=1e-9)
        assert math.isclose(rr.ratio, 4020.0 / 4000.0, abs_tol=1e-12)

    def test_raises_when_old_anchor_missing(self) -> None:
        """Synthetic: effective_front names a contract that has zero
        bars on its last-as-front session."""
        rows = [
            _bar(datetime(2024, 3, 1, 14, 30, tzinfo=UTC), "ESM4", "ES", 4020.0, 1500),
        ]
        df = pl.DataFrame(rows)
        # Fabricate an effective_front claiming ESH4 was front on 03-01.
        effective = pl.DataFrame(
            {
                "symbol": ["ES", "ES"],
                "session_date": [date(2024, 3, 1), date(2024, 3, 4)],
                "effective_front_contract_symbol": ["ESH4", "ESM4"],
                "raw_front_contract_symbol": ["ESH4", "ESM4"],
            }
        )
        ev = RollEvent(date(2024, 3, 4), "ESH4", "ESM4")
        with pytest.raises(NoOverlapError):
            compute_roll_ratio_afml(df, ev, "ES", effective)


# ---------------------------------------------------------------------------
# Adjustment invariants
# ---------------------------------------------------------------------------


class TestAdjustmentInvariants:
    def test_newest_contract_has_factor_one(self) -> None:
        df = _two_contract_frame()
        out, _summary = _adjust_one_symbol(df, "ES", window_days=3)
        newest = out.filter(pl.col("front_contract_symbol") == "ESM4")
        assert newest["adjustment_factor"].unique().to_list() == [1.0]

    def test_older_contract_gets_ratio_factor(self) -> None:
        df = _two_contract_frame(old_last_close=4000.0, new_first_open=4020.0)
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        older = out.filter(pl.col("front_contract_symbol") == "ESH4")
        assert math.isclose(
            older["adjustment_factor"][0], 4020.0 / 4000.0, abs_tol=1e-12
        )

    def test_close_equals_unadjusted_times_factor(self) -> None:
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        for got, u, f in zip(
            out["close"].to_list(),
            out["unadjusted_close"].to_list(),
            out["adjustment_factor"].to_list(),
            strict=True,
        ):
            assert math.isclose(got, u * f, abs_tol=1e-9)

    def test_ohlc_consistency_preserved(self) -> None:
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        violations = out.filter(
            (pl.col("low") > pl.col("open"))
            | (pl.col("low") > pl.col("close"))
            | (pl.col("high") < pl.col("open"))
            | (pl.col("high") < pl.col("close"))
        )
        assert violations.height == 0

    def test_return_preservation_within_contract(self) -> None:
        """Within a single contract, raw and adjusted log-returns match
        (a global scalar cancels in log-diffs)."""
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        older_adj = out.filter(
            pl.col("front_contract_symbol") == "ESH4"
        ).sort("ts_event")
        older_raw = (
            df.filter(
                (pl.col("symbol") == "ES")
                & (pl.col("contract_symbol") == "ESH4")
            )
            .sort("ts_event")
            .filter(pl.col("ts_event").is_in(older_adj["ts_event"].implode()))
        )
        raw_ret = np.diff(np.log(older_raw["close"].to_numpy()))
        adj_ret = np.diff(np.log(older_adj["close"].to_numpy()))
        assert np.allclose(raw_ret, adj_ret, atol=1e-12)

    def test_return_preservation_across_roll_boundary(self) -> None:
        """Zero spurious return across the roll: adjusted old-close at
        the last-as-front session equals new-open at the first-as-front
        session. Log-return across the boundary is exactly 0."""
        df = _two_contract_frame(old_last_close=4000.0, new_first_open=4020.0)
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        last_old = out.filter(pl.col("front_contract_symbol") == "ESH4").tail(1)
        first_new = out.filter(pl.col("front_contract_symbol") == "ESM4").head(1)
        adj_log_ret = math.log(first_new["open"][0]) - math.log(last_old["close"][0])
        assert math.isclose(adj_log_ret, 0.0, abs_tol=1e-9)


class TestMultiRollChain:
    def test_three_contract_cumulative_product(self) -> None:
        """ESH4 → ESM4 → ESU4: cumulative factor for ESH4 must equal
        product of both ratios."""
        rows: list[dict] = []
        # Session 2024-03-01..03-04 (ESH4 front, with the last bar's
        # close = 4000.0 for the ESH4→ESM4 ratio anchor).
        for session_idx, day in enumerate((1, 4)):
            for minute in range(10):
                ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
                rows.append(_bar(ts, "ESH4", "ES", 3995.0 + session_idx + minute * 0.1, 100))
        rows[-1]["close"] = 4000.0
        rows[-1]["open"] = 3999.95
        rows[-1]["high"] = 4000.10
        rows[-1]["low"] = 3999.80

        # Sessions 03-05..06-03 with ESM4 front (volume high; last-bar
        # close = 4100.0 for the ESM4→ESU4 ratio anchor). Keep bar
        # count modest but >= window_days=3 of persistence.
        esm_days = (5, 6, 7, 8, 11)
        for session_idx, day in enumerate(esm_days):
            for minute in range(10):
                ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
                price = 4020.0 + session_idx * 10 + minute * 0.1
                # First bar of day 5 open must equal 4020.0 (ESH4→ESM4 anchor).
                if day == 5 and minute == 0:
                    rows.append(
                        {
                            "ts_event": ts,
                            "rtype": 34, "publisher_id": 1, "instrument_id": 42,
                            "open": 4020.0, "high": 4020.25, "low": 4019.75,
                            "close": 4020.05, "volume": 200,
                            "contract_symbol": "ESM4", "symbol": "ES",
                        }
                    )
                else:
                    rows.append(_bar(ts, "ESM4", "ES", price, 200))
        # Tack last-bar close of ESM4 = 4100.0 for the next anchor.
        rows[-1]["close"] = 4100.0
        rows[-1]["open"] = 4099.95
        rows[-1]["high"] = 4100.10
        rows[-1]["low"] = 4099.80

        # Sessions 03-12..03-18: ESU4 front (≥3 sessions persistence).
        esu_days = (12, 13, 14, 15, 18)
        for session_idx, day in enumerate(esu_days):
            for minute in range(10):
                ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
                price = 4130.0 + session_idx * 5 + minute * 0.1
                if day == 12 and minute == 0:
                    # First ESU4 open = 4130.0 (ESM4→ESU4 anchor).
                    rows.append(
                        {
                            "ts_event": ts,
                            "rtype": 34, "publisher_id": 1, "instrument_id": 42,
                            "open": 4130.0, "high": 4130.25, "low": 4129.75,
                            "close": 4130.05, "volume": 300,
                            "contract_symbol": "ESU4", "symbol": "ES",
                        }
                    )
                else:
                    rows.append(_bar(ts, "ESU4", "ES", price, 300))

        df = pl.DataFrame(rows)
        out, summary = _adjust_one_symbol(df, "ES", window_days=3)
        factors = summary["contract_factors"]
        # As of v0.3.0, summary keys are decade-disambiguated
        # (contract_id_full = "{contract_symbol}_{YYYY}").
        assert math.isclose(factors["ESU4_2024"], 1.0, abs_tol=1e-12)
        # ESM4 factor = ratio of roll 2 = 4130 / 4100.
        rho_2 = 4130.0 / 4100.0
        assert math.isclose(factors["ESM4_2024"], rho_2, abs_tol=1e-12)
        # ESH4 factor = ρ_1 * ρ_2 = (4020/4000) * (4130/4100).
        rho_1 = 4020.0 / 4000.0
        assert math.isclose(factors["ESH4_2024"], rho_1 * rho_2, abs_tol=1e-12)


class TestChainContinuity:
    def test_chain_continuity_holds_for_normal_sequence(self) -> None:
        df = _two_contract_frame()
        out, summary = _adjust_one_symbol(df, "ES", window_days=3)
        rolls = summary["rolls"]
        for k in range(len(rolls) - 1):
            assert rolls[k].event.new_contract == rolls[k + 1].event.old_contract


# ---------------------------------------------------------------------------
# Output schema + cross-row invariants
# ---------------------------------------------------------------------------


class TestValidateCrossRow:
    def test_schema_validates(self) -> None:
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        VendorLegacy1minRollAdjustedSchema.validate(out)

    def test_validate_catches_missing_anchor_factor(self) -> None:
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        # Rescale ALL OHLC on the anchor contract by 0.5 (along with
        # the factor) so OHLC consistency survives; then the invariant
        # check "exactly one anchor with factor==1.0" fires cleanly.
        broken = out.with_columns(
            pl.when(pl.col("adjustment_factor") == 1.0)
            .then(pl.lit(0.5))
            .otherwise(pl.col("adjustment_factor"))
            .alias("_scale"),
        )
        broken = broken.with_columns(
            (pl.col("open") * pl.col("_scale") / pl.col("adjustment_factor")).alias(
                "open"
            ),
            (pl.col("high") * pl.col("_scale") / pl.col("adjustment_factor")).alias(
                "high"
            ),
            (pl.col("low") * pl.col("_scale") / pl.col("adjustment_factor")).alias(
                "low"
            ),
            (pl.col("close") * pl.col("_scale") / pl.col("adjustment_factor")).alias(
                "close"
            ),
            pl.col("_scale").alias("adjustment_factor"),
        ).drop("_scale")
        with pytest.raises(ValueError, match="adjustment_factor==1.0"):
            VendorLegacy1minRollAdjustedIngestJob().validate(broken.lazy())

    def test_validate_catches_factor_variation_within_contract(self) -> None:
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        # Perturb one row's factor within the newest contract AND
        # rescale its OHLC to keep OHLC consistency intact (otherwise
        # the OHLC check fires first and masks the cross-row check).
        mask = out["front_contract_symbol"] == "ESM4"
        factors = out["adjustment_factor"].to_list()
        idx = mask.to_list().index(True)
        old_factor = factors[idx]
        new_factor = 1.0001
        factors[idx] = new_factor
        scale = new_factor / old_factor
        ohlc_scaled = {
            "open": out["open"].to_list(),
            "high": out["high"].to_list(),
            "low": out["low"].to_list(),
            "close": out["close"].to_list(),
        }
        for k in ohlc_scaled:
            ohlc_scaled[k][idx] = ohlc_scaled[k][idx] * scale
        broken = out.with_columns(
            pl.Series("adjustment_factor", factors),
            pl.Series("open", ohlc_scaled["open"]),
            pl.Series("high", ohlc_scaled["high"]),
            pl.Series("low", ohlc_scaled["low"]),
            pl.Series("close", ohlc_scaled["close"]),
        )
        with pytest.raises(ValueError, match="constant"):
            VendorLegacy1minRollAdjustedIngestJob().validate(broken.lazy())

    def test_unique_symbol_ts(self) -> None:
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        dup = out.group_by(["symbol", "ts_event"]).agg(pl.len().alias("n"))
        assert (dup["n"] > 1).sum() == 0


# ---------------------------------------------------------------------------
# IngestJob contract
# ---------------------------------------------------------------------------


class TestIngestJobContract:
    def test_registered(self) -> None:
        from skie_ninja.data.ingest import INGEST_REGISTRY

        assert "vendor_legacy_1min_roll_adjusted" in INGEST_REGISTRY

    def test_empty_fetch_raises_when_source_missing(self, tmp_path: Path) -> None:
        ctx = _FakeCtx(tmp_path / "ctx")
        job = VendorLegacy1minRollAdjustedIngestJob()
        with pytest.raises(FileNotFoundError):
            job.fetch(date(2020, 1, 1), date(2025, 12, 31), ctx)

    def test_fetch_symbol_scope(self, tmp_path: Path) -> None:
        """Fetch only enumerates the symbols configured on the job."""
        ctx = _FakeCtx(tmp_path / "ctx")
        src_root = ctx.paths.data_processed / "vendor_legacy_1min"
        for sym in ("ES", "NQ", "CL"):  # CL is out-of-scope
            for yr in (2020, 2021, 2022):
                p = src_root / f"symbol={sym}" / f"year={yr}"
                p.mkdir(parents=True)
                (p / "part-0000.parquet").write_bytes(b"x")
        job = VendorLegacy1minRollAdjustedIngestJob(symbols=("ES", "NQ"))
        out = job.fetch(date(2021, 1, 1), date(2022, 12, 31), ctx)
        assert len(out) == 4  # 2 symbols x 2 years
        assert all("symbol=CL" not in p.as_posix() for p in out)

    def test_parse_empty_returns_schema(self, tmp_path: Path) -> None:
        ctx = _FakeCtx(tmp_path / "ctx")
        out = (
            VendorLegacy1minRollAdjustedIngestJob()
            .parse([], ctx)
            .collect()
        )
        assert out.height == 0
        assert set(out.columns) == {
            "ts_event", "open", "high", "low", "close", "volume",
            "symbol", "front_contract_symbol", "adjustment_factor",
            "unadjusted_close", "roll_flag",
        }

    def test_validate_rejects_unknown_symbol(self) -> None:
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        broken = out.with_columns(pl.lit("XX").alias("symbol"))
        with pytest.raises(pandera.errors.SchemaError):
            VendorLegacy1minRollAdjustedIngestJob().validate(broken.lazy())

    def test_write_processed_partitioned(self, tmp_path: Path) -> None:
        ctx = _FakeCtx(tmp_path / "ctx")
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        out_dir = VendorLegacy1minRollAdjustedIngestJob().write_processed(
            out.lazy(), ctx
        )
        es_part = out_dir / "symbol=ES" / "year=2024" / "part-0000.parquet"
        assert es_part.is_file()
        VendorLegacy1minRollAdjustedSchema.validate(pl.read_parquet(es_part))

    def test_emit_provenance_carries_evidence_bar_and_pit_caveat(
        self, tmp_path: Path
    ) -> None:
        ctx = _FakeCtx(tmp_path / "ctx")
        src_root = ctx.paths.data_processed / "vendor_legacy_1min"
        (src_root / "symbol=ES" / "year=2024").mkdir(parents=True)
        fixture = _two_contract_frame()
        src_file = src_root / "symbol=ES" / "year=2024" / "part-0000.parquet"
        fixture.write_parquet(src_file)

        job = VendorLegacy1minRollAdjustedIngestJob(window_days_override=3)
        # Run adjust() so _last_run_summary is populated before
        # emit_provenance (the real pipeline does this via parse).
        job.adjust(fixture.lazy())

        out_dir = ctx.paths.data_processed / "vendor_legacy_1min_roll_adjusted"
        prov = job.emit_provenance(ctx, [src_file], out_dir)
        import json

        payload = json.loads(prov.read_text(encoding="utf-8"))
        assert payload["evidence_bar_eligible_returns"] is True
        assert payload["evidence_bar_eligible_levels"] is False
        assert payload["evidence_bar_eligible"] is True  # legacy alias
        assert payload["tier"] == "evidence_bar"
        assert payload["level_use_pit_safe"] is False
        assert "P1-LEVEL-USE-POLICY" in payload["level_use_pit_safe_note"]
        assert payload["method"] == "ratio_adjustment_volume_crossover_persistence"
        assert "§2.4.3" in payload["method_reference"]
        # run_summary carries rolls + contract_factors.
        summary = payload["run_summary"]["ES"]
        assert summary["window_days"] == 3
        assert len(summary["rolls"]) == 1
        # As of v0.3.0, RollEvent old/new_contract carry the
        # disambiguated contract_id_full key, not the 1-digit display form.
        assert summary["rolls"][0]["old_contract"] == "ESH4_2024"
        assert summary["rolls"][0]["new_contract"] == "ESM4_2024"
        # As of v0.3.0, summary keys are decade-disambiguated
        # (contract_id_full = "{contract_symbol}_{YYYY}").
        assert set(summary["contract_factors"].keys()) == {"ESH4_2024", "ESM4_2024"}

    def test_write_processed_atomic_rollback_on_schema_failure(
        self, tmp_path: Path
    ) -> None:
        """Deliberately break a partition's schema post-staging and
        confirm no partition is promoted."""
        ctx = _FakeCtx(tmp_path / "ctx")
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        # Corrupt: rename `open` → `opened` to trigger pandera strict failure.
        broken = out.rename({"open": "opened"})
        with pytest.raises(pandera.errors.SchemaError):
            VendorLegacy1minRollAdjustedIngestJob().write_processed(
                broken.lazy(), ctx
            )
        base_dir = ctx.paths.data_processed / "vendor_legacy_1min_roll_adjusted"
        # No partitions survived the rollback.
        assert not any(base_dir.rglob("*.parquet"))


# ---------------------------------------------------------------------------
# Decade-wraparound disambiguation (v0.3.0)
# ---------------------------------------------------------------------------


class TestDecadeWraparound:
    """Regression tests for the contract-symbol-collision bug fixed in
    v0.3.0. CME equity-index futures use 1-digit year suffixes (ESH5
    = March-2015 OR March-2025), so on a substrate spanning >=10
    calendar years the display ``contract_symbol`` collides between
    decades. Pre-v0.3.0 the cumulative-back-adjust loop overwrote the
    newest contract's anchor (factor 1.0) with the cumulative product
    of all rolls when traversing an older same-symbol contract. AFML
    §2.4.3 requires the newest contract to be the unique anchor."""

    def _decade_wraparound_frame(self) -> pl.DataFrame:
        """Two ESH5 contracts spanning a decade: ESH5(2015) precedes
        ESM5(2015), ESM5(2015) precedes ... eventually ESH5(2025)
        precedes ESM5(2025). We minimize to a 4-roll chain that
        exercises the collision: ESH5(2015) -> ESM5(2015) -> ESH5(2025)
        -> ESM5(2025). The two ESH5 occurrences share the display
        symbol; only the year disambiguates them.

        Each segment carries 5 sessions of 10 bars at high volume
        on its primary contract; window_days=3 commits each roll on
        the third consecutive lead. Anchors are rigged at round
        prices for easy verification."""
        rows: list[dict] = []

        def _seg(
            year: int,
            month: int,
            days: tuple[int, ...],
            contract: str,
            base_open: float,
            override_first_open: float | None,
            override_last_close: float | None,
        ) -> None:
            for session_idx, day in enumerate(days):
                for minute in range(10):
                    ts = datetime(year, month, day, 14, 30 + minute, tzinfo=UTC)
                    price = base_open + session_idx * 0.5 + minute * 0.1
                    rows.append(_bar(ts, contract, "ES", price, 500))
            if override_first_open is not None:
                rows[-len(days) * 10]["open"] = override_first_open
                rows[-len(days) * 10]["high"] = override_first_open + 0.25
                rows[-len(days) * 10]["low"] = override_first_open - 0.25
                rows[-len(days) * 10]["close"] = override_first_open + 0.05
            if override_last_close is not None:
                rows[-1]["close"] = override_last_close
                rows[-1]["open"] = override_last_close - 0.05
                rows[-1]["high"] = override_last_close + 0.10
                rows[-1]["low"] = override_last_close - 0.20

        # Segment 1: ESH5 in 2015 (March 2015 contract). Days 2-6 March.
        _seg(
            2015, 3, (2, 3, 4, 5, 6), "ESH5", 2000.0,
            override_first_open=None,
            override_last_close=2010.0,
        )
        # Segment 2: ESM5 in 2015 (June 2015 contract). Days 9-13 March.
        _seg(
            2015, 3, (9, 10, 11, 12, 13), "ESM5", 2050.0,
            override_first_open=2050.0,
            override_last_close=2060.0,
        )
        # Segment 3: ESH5 in 2025 (March 2025 contract). Days 3-7 March.
        # NOTE: same display contract_symbol "ESH5" as segment 1.
        _seg(
            2025, 3, (3, 4, 5, 6, 7), "ESH5", 5000.0,
            override_first_open=5000.0,
            override_last_close=5010.0,
        )
        # Segment 4: ESM5 in 2025 (June 2025 contract).
        _seg(
            2025, 3, (10, 11, 12, 13, 14), "ESM5", 5050.0,
            override_first_open=5050.0,
            override_last_close=None,
        )

        return pl.DataFrame(rows)

    def test_anchor_unique_across_decade_wraparound(self) -> None:
        """Pre-v0.3.0 bug: when ESH5(2015) appeared in the contract_factor
        dict, the cumulative-product loop overwrote the ESH5(2025) entry
        (which had factor==1.0) with the cumulative product. Result: zero
        contracts at factor 1.0 — validation invariant (a) failed.

        Post-fix: the newest contract (ESM5_2025) anchors at 1.0 and the
        validate() pass succeeds."""
        df = self._decade_wraparound_frame()
        out, summary = _adjust_one_symbol(df, "ES", window_days=3)

        factors = summary["contract_factors"]
        # Exactly one contract_id_full has factor == 1.0 (the anchor).
        anchored = {k: v for k, v in factors.items() if math.isclose(v, 1.0, abs_tol=1e-12)}
        assert len(anchored) == 1, (
            f"Expected exactly one anchor contract at factor 1.0; "
            f"got {anchored} from full factors {factors}"
        )
        # The anchor is the NEWEST contract (ESM5 in 2025).
        assert "ESM5_2025" in anchored

        # Both ESH5 instances are present and have DIFFERENT factors.
        assert "ESH5_2015" in factors
        assert "ESH5_2025" in factors
        assert not math.isclose(factors["ESH5_2015"], factors["ESH5_2025"])

        # The 2025 anchor is preserved end-to-end through validate().
        VendorLegacy1minRollAdjustedIngestJob().validate(out.lazy())

    def test_validate_rejects_pre_v030_collision_substrate(self) -> None:
        """A direct construction of the pre-v0.3.0 failure mode:
        if validate() is given an output where the display
        front_contract_symbol "ESH5" appears with two distinct
        factors across two calendar years, that's the LEGITIMATE
        post-fix output — the decade-disambiguated invariants
        accept it. The buggy pre-fix output would have had the
        2025 ESH5 entry overwritten and zero anchors at 1.0;
        validate() rejects that."""
        df = self._decade_wraparound_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)

        # Sanity: the (decade-disambiguated) cross-row invariants pass.
        VendorLegacy1minRollAdjustedIngestJob().validate(out.lazy())

        # Now corrupt the output to mimic the pre-fix bug: zero out
        # the anchor by rescaling all factor-1.0 rows by a factor
        # that destroys the anchor (this is how the bug manifested
        # — zero contracts at 1.0 in the output).
        broken = out.with_columns(
            pl.when((pl.col("adjustment_factor") - 1.0).abs() < 1e-12)
            .then(pl.lit(0.5))
            .otherwise(pl.col("adjustment_factor"))
            .alias("_scale"),
        ).with_columns(
            (pl.col("open") * pl.col("_scale") / pl.col("adjustment_factor")).alias("open"),
            (pl.col("high") * pl.col("_scale") / pl.col("adjustment_factor")).alias("high"),
            (pl.col("low") * pl.col("_scale") / pl.col("adjustment_factor")).alias("low"),
            (pl.col("close") * pl.col("_scale") / pl.col("adjustment_factor")).alias("close"),
            pl.col("_scale").alias("adjustment_factor"),
        ).drop("_scale")
        with pytest.raises(ValueError, match="adjustment_factor==1.0"):
            VendorLegacy1minRollAdjustedIngestJob().validate(broken.lazy())

    def test_assert_no_consecutive_year_collision_rejects_violation(self) -> None:
        """A contract whose bars span two consecutive (gap < 10y) calendar
        years violates the upstream contract-month-bounded ingest
        invariant required for contract_id_full disambiguation. Surface
        as ValueError. The 10-year gap rule permits the legitimate CME
        decade-wraparound case (ESH5 in 2015 vs ESH5 in 2025) while
        rejecting the cross-year-end contamination case (ESH6 with
        bars in both Dec 2015 and Jan 2016)."""
        rows = [
            _bar(datetime(2015, 12, 31, 22, 0, tzinfo=UTC), "ESH6", "ES", 4000.0, 100),
            # Same contract_symbol, adjacent calendar year — fabricated
            # data that the upstream ingest's per-contract month-bounded
            # windows would normally prevent.
            _bar(datetime(2016, 1, 4, 14, 30, tzinfo=UTC), "ESH6", "ES", 4001.0, 100),
        ]
        df = pl.DataFrame(rows)
        with pytest.raises(ValueError, match="consecutive"):
            _adjust_one_symbol(df, "ES", window_days=3)

    def test_assert_no_consecutive_year_collision_permits_decade_gap(self) -> None:
        """A contract whose bars genuinely span 10+ years apart (the CME
        decade-wraparound case) is the FIX target, not a bug — the
        invariant must permit it."""
        # ESH5 in 2015 and ESH5 in 2025 — a single fabricated contract
        # row family per year, just enough to verify the assertion does
        # NOT fire. The full pipeline downstream needs more bars to do
        # anything meaningful, but the invariant check is what we're
        # exercising here.
        rows = [
            _bar(datetime(2015, 3, 15, 14, 30, tzinfo=UTC), "ESH5", "ES", 2000.0, 100),
            _bar(datetime(2025, 3, 15, 14, 30, tzinfo=UTC), "ESH5", "ES", 5000.0, 100),
        ]
        df = pl.DataFrame(rows)
        # No exception — the 10y gap is the legitimate decade-wraparound case.
        _assert_no_consecutive_year_collision(df, "ES")
