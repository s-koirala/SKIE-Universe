"""Roll-adjusted continuous-contract derivative of ``vendor_legacy_1min``.

Stitches successive front-month ES/NQ contracts into one
continuous series per root symbol. Method: **multiplicative ratio
adjustment** per de Prado 2018 *Advances in Financial Machine Learning*
ch.2 §2.4.3 ("Single Future Roll"), rolled on **volume-crossover with
persistence window** per [config/instruments.yaml](../../../../config/instruments.yaml)
``roll_rule``.

(Not to be confused with AFML §2.4.1, "The ETF Trick", which is a
P&L-accumulation method for baskets/spreads/$1-invested series and
additionally handles dividends, bid-ask, and rebalance costs — a
different construction.)

Rationale
---------

Raw front-month concatenation (the ``vendor_legacy_1min`` output)
introduces price-level discontinuities at every roll boundary because
adjacent contracts trade at different prices (contango/backwardation).
Computing returns on the raw series contaminates the return at the
roll boundary with the contract-level price differential, violating
the "adjust for corporate actions before return calc" principle
([rules/quant-project.md](../../../../.claude/rules/quant-project.md)
§Time-series integrity). Multiplicative back-adjustment preserves
**return** magnitudes across the roll boundary.

References
----------

  - **Primary (method):** de Prado 2018, *Advances in Financial Machine
    Learning* (Wiley, ISBN 978-1119482086), ch.2 §2.4.3 ("Single
    Future Roll"). Equivalent relative-form uses cumulative gap
    ratios multiplied into the historical price series.
  - **Supplementary:** Chan 2013, *Algorithmic Trading* (Wiley, ISBN
    978-1118460146), ch.2–3 on continuous-contract construction and
    the return-preservation argument.
  - **Supplementary:** Carver 2023, *Leveraged Trading* (Harriman
    House, ISBN 978-0857199546), app. "Futures data" on stitched /
    back-adjusted series.
  - **Operational convention (OHLC/volume extensions):** Uniform
    scalar adjustment of O/H/L/C and unadjusted per-contract volume
    follow the Norgate ("Continuous Contract Methodology") and CSI
    ("Perpetual Contract" whitepaper) operational convention. AFML
    §2.4.3 itself only formalizes the scalar-price adjustment;
    industry-standard OHLC tuple extension is a documentation-only
    convention, not a de Prado result.
  - **Volume vs open-interest crossover:** no peer-reviewed empirical
    comparison of volume-crossover vs OI-crossover realized slippage
    for CME equity-index futures is known as of 2026-04-23 (Evidence
    Hierarchy tier 4 at best for this choice). Practitioner
    convention (CME rollover guidance, Databento default loader)
    uses volume-crossover. Phase-1 follow-up `P1-ROLL-METHOD` will
    empirically compare the two inside the walk-forward framework.
  - **Rollover guidance:** CME rollover page retrieved 2026-04-15,
    https://www.cmegroup.com/trading/equity-index/rolldates.html
    (volume/OI migrates to back month ~8 calendar days before
    last-trade).

Algorithm (per root symbol)
---------------------------

**Step 1 — CME trading-day attribution.** Map each 1-minute UTC bar to
its CME trading-session date via the Sunday-17:00-CT boundary rule
(17:00 CT on calendar date D-1 is the start of session date D). This
matches the CME daily-settlement convention. Implementation uses a
polars native +7h shift from CME local time (Sunday 17:00 CT + 7h =
Monday 00:00 CT → session date Monday), equivalent to
``utils/clock.py::trading_day`` for non-holiday weekdays and
conservative (Fri-to-Mon) for weekend-adjacent timestamps. Holiday
adjustment is not required for front-month volume argmax because
holidays have near-zero volume and cannot change argmax outcomes.

**Step 2 — Rolling-window front-month detection (hysteresis).** For
each session date D, compute trailing-``window_days`` cumulative
volume per ``contract_symbol``. Front-month = argmax over contracts
of the windowed cumulative volume. Using a trailing window (not a
single-day argmax) suppresses one-day volume flips near roll
boundaries — the canonical failure mode that ``window_days`` in
the config exists to prevent. A contract only becomes front-month
when its cumulative ``window_days``-session volume leads.
Tie-breaking is deterministic: higher cumulative volume first, then
lexicographically-earliest contract_symbol.

**Step 3 — Roll event detection with persistence guard.** After
step 2, a raw transition at D is a session where front(D) !=
front(D-1). Raw transitions are committed as roll events only if
the new contract remains raw-winner for at least ``window_days``
consecutive sessions starting at D. This enforces the
``roll_rule.window_days`` hysteresis and rejects short oscillations
where volume briefly re-migrates to the older contract.

When persistence is confirmed, the guard **retroactively rewrites**
the effective-front-month label on every session since
``challenger_start`` (the first session the committed challenger
led by raw volume) to the challenger. Consequently, the
``roll_date`` surfaced by ``detect_roll_events`` is
``challenger_start`` — i.e., the first session the challenger
actually led, NOT the session at which the persistence threshold
was first met. The guard verifies persistence; it does not
relocate the boundary. This choice matches CME's own "roll occurs
~8 calendar days before last-trade as volume migrates" framing —
the transition moment is the first day of migration, not the day
the migration is retrospectively confirmed.

**Step 4 — Canonical AFML §2.4.3 roll anchor.** At each committed
roll event ``(roll_date D, old, new)``, compute

    ρ_k = new_open(t_first_new) / old_close(t_last_old)

where

    t_last_old = the last 1-minute bar of ``old`` on the last
                 session prior to D where ``old`` was front-month;
    t_first_new = the first 1-minute bar of ``new`` on session D
                  (its first session as front-month).

This matches AFML §2.4.3 (and mlfinlab's reference
``get_futures_roll_series``). If either bar is missing (source-data
gap), the roll is declared a ``NoOverlapError`` and the user must
repair source coverage. **No post-roll or synchronous-overlap
fallback is used — those would leak future prices into the older
segment's adjustment factor.**

**Step 5 — Cumulative back-adjustment.** Walk backward from the
newest contract (factor 1.0). Each prior contract's cumulative
multiplicative factor = product of all ρ_j for j ≥ k, where k is the
roll at which the contract rolled out of front-month. By the anchor
construction, adjusted_old_close(t_last_old) == new_open(t_first_new) —
the adjusted old-contract close equals the new-contract open at the
roll boundary, so the first return into the new contract is
return-preserving. Chain-continuity (``event_{k}.new ==
event_{k+1}.old``) is asserted.

**Step 6 — Front-month filter and output.** Filter bars so only the
effective-front-month at each session date survives — exactly one
front-month row per (symbol, ts_event) in the output. Emit
adjusted OHLC plus audit metadata (``front_contract_symbol``,
``adjustment_factor``, ``unadjusted_close``, ``roll_flag``).

Point-in-time caveat (important)
--------------------------------

The adjustment factors computed by this module use the **full sample**
roll history. As a consequence:

  - **Returns** (log-diffs of ``close``) on the adjusted series are
    point-in-time safe: a multiplicative scalar applied to both
    numerator and denominator cancels.
  - **Levels** (``open``, ``high``, ``low``, ``close`` on their own)
    are NOT point-in-time: the adjusted level of a 2021 bar is a
    retrospective rescaling that depends on 2022-2025 rolls.
    Refreshing the pipeline with new data *changes* the absolute
    adjusted levels of historical bars.

Consumers computing level-based features (moving-average distance,
Bollinger z-score, price percentile) in a walk-forward evaluation
MUST either (a) use return-based transforms only, or (b)
re-materialize this derivative within each training fold using
only rolls with roll_date <= fold_end. The provenance record
carries ``level_use_pit_safe: false`` as a machine-readable flag.

Tracked as Phase-1 follow-up ``P1-LEVEL-USE-POLICY`` — the
feature-factory contract (implementation-plan §3) will enforce
this at the PIT property-test level in Cycle 4/6.

Operational runbook for data gaps
---------------------------------

If ``NoOverlapError`` is raised on a real-data ingest:

  1. Re-fetch the raw 1-min CSV from Databento (sibling SKIE-Ninja
     repo) — the gap may be a pull-level corruption.
  2. If the gap is persistent, consult CME daily-settlement prices
     (CME Rule 813) for the two contracts on the last pre-roll
     session and substitute ``old_close`` with that settlement.
     This substitution is opt-in and NOT the default; it must be
     recorded in provenance ``ratio_anchor_override`` with a
     justification, and requires a fresh audit-remediate round.
  3. As a last resort, drop the problematic contract-pair from the
     universe for the affected calendar period and archive an
     incident report under ``docs/audits/``.

Conforms to ``IngestJob`` protocol in ``_registry.py``.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import yaml

from skie_ninja.data.ingest._registry import register
from skie_ninja.data.validation.schema import VendorLegacy1minRollAdjustedSchema
from skie_ninja.utils.hashing import frame_sha256
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

_log = logging.getLogger(__name__)

_DATASET_NAME = "vendor_legacy_1min_roll_adjusted"
_DATASET_VERSION = "0.2.0"  # bump: Round-2 remediation (anchor, persistence, PIT caveat)

_CME_TZ = "America/Chicago"
# 17:00 CT is the boundary between CME trading sessions: a trade
# timestamped 17:00 CT on calendar day D-1 belongs to session date D.
# Shifting all bars by +7h in America/Chicago then taking the date
# gives the session date directly. Matches utils/clock.py::trading_day
# for non-holiday weekday timestamps; holiday shift is irrelevant for
# front-month volume argmax (holidays have near-zero volume and cannot
# affect which contract wins the cumulative argmax).
_CME_SESSION_SHIFT_HOURS = 7


class NoOverlapError(ValueError):
    """Raised when a roll event has no valid AFML §2.4.3 anchor bars
    (either ``old`` has no bar on its last-as-front session, or
    ``new`` has no bar on its first-as-front session). Indicates
    upstream data gap; see module docstring 'Operational runbook for
    data gaps'."""


@dataclass(frozen=True)
class RollEvent:
    """One roll transition that has passed the persistence guard."""

    roll_date: date  # first session date where new_contract is front-month
    old_contract: str
    new_contract: str


@dataclass(frozen=True)
class RollRatio:
    """Computed ratio for a single roll event (AFML §2.4.3 anchor)."""

    event: RollEvent
    t_old_close_utc: datetime
    t_new_open_utc: datetime
    old_close: float
    new_open: float
    ratio: float  # = new_open / old_close


def _load_roll_window_days(symbol: str) -> int:
    """Read the ``window_days`` parameter from ``config/instruments.yaml``.

    Each contract's ``roll_rule.window_days`` is the persistence window
    required for a roll transition to commit. Matches the value that
    callers have already flagged ``# justify:`` in the yaml. Defaults
    to 5 if the config is not reachable (tests / synthetic fixtures).
    """
    try:
        paths = ProjectPaths.discover()
        yaml_path = paths.root / "config" / "instruments.yaml"
        cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        sym_cfg = cfg.get("instruments", {}).get(symbol, {})
        w = sym_cfg.get("roll_rule", {}).get("window_days")
        if isinstance(w, int) and w > 0:
            return int(w)
    except Exception as exc:
        _log.debug("Could not load roll_rule for %s: %s (defaulting to 5).", symbol, exc)
    return 5


class VendorLegacy1minRollAdjustedIngestJob:
    """Ingest job: derive roll-adjusted continuous series from
    the already-processed raw ``vendor_legacy_1min`` partitions."""

    name: str = _DATASET_NAME
    version: str = _DATASET_VERSION

    # Track the per-symbol algorithmic detail (rolls, factors) so
    # emit_provenance can report it without re-running the pipeline.
    _last_run_summary: dict[str, dict[str, Any]]

    def __init__(
        self,
        source_dataset: str = "vendor_legacy_1min",
        symbols: tuple[str, ...] = ("ES", "NQ"),
        window_days_override: int | None = None,
    ) -> None:
        self._source_dataset = source_dataset
        self._symbols = tuple(symbols)
        self._window_days_override = window_days_override
        self._last_run_summary = {}

    # ------------------------------------------------------------------
    # fetch: list parquet files under data/processed/{source_dataset}/
    # ------------------------------------------------------------------

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        src_root = ctx.paths.data_processed / self._source_dataset
        if not src_root.is_dir():
            raise FileNotFoundError(
                f"Source dataset root not found: {src_root}. "
                f"Run `scripts/ingest.py --dataset {self._source_dataset}` first."
            )

        out: list[Path] = []
        for parquet in sorted(src_root.rglob("part-*.parquet")):
            # Partition layout: symbol=XX/year=YYYY/part-NNNN.parquet
            year_part = parquet.parent.name  # "year=YYYY"
            sym_part = parquet.parent.parent.name  # "symbol=XX"
            if not year_part.startswith("year=") or not sym_part.startswith("symbol="):
                continue
            try:
                year_val = int(year_part.split("=", 1)[1])
            except ValueError:
                continue
            sym_val = sym_part.split("=", 1)[1]
            if sym_val not in self._symbols:
                continue
            if year_val < start.year or year_val > end.year:
                continue
            out.append(parquet)

        if not out:
            _log.warning(
                "No source parquets under %s for symbols=%s years=%s..%s",
                src_root, self._symbols, start.year, end.year,
            )
        else:
            _log.info(
                "Located %d source parquets (symbols=%s years=%s..%s)",
                len(out), self._symbols, start.year, end.year,
            )
        return out

    # ------------------------------------------------------------------
    # parse: load + concatenate + sort + adjust
    # ------------------------------------------------------------------

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        del ctx
        if not raw_paths:
            return _empty_adjusted_frame().lazy()
        frames = [pl.scan_parquet(rp) for rp in raw_paths]
        source = pl.concat(frames, how="vertical").sort(
            ["symbol", "contract_symbol", "ts_event"]
        )
        return self.adjust(source)

    # ------------------------------------------------------------------
    # adjust: per-symbol dispatcher
    # ------------------------------------------------------------------

    def adjust(self, df: pl.LazyFrame) -> pl.LazyFrame:
        collected = df.collect()
        if collected.height == 0:
            return _empty_adjusted_frame().lazy()

        self._last_run_summary.clear()
        per_symbol: list[pl.DataFrame] = []
        for sym in sorted(collected["symbol"].unique(maintain_order=True).to_list()):
            sym_df = collected.filter(pl.col("symbol") == sym)
            window_days = (
                self._window_days_override
                if self._window_days_override is not None
                else _load_roll_window_days(sym)
            )
            adjusted, summary = _adjust_one_symbol(sym_df, sym, window_days)
            self._last_run_summary[sym] = summary
            per_symbol.append(adjusted)

        out = pl.concat(per_symbol, how="vertical").sort(["symbol", "ts_event"])
        return out.lazy()

    # ------------------------------------------------------------------
    # validate: schema + OHLC + monotonicity + cross-row invariants
    # ------------------------------------------------------------------

    def validate(self, df: pl.LazyFrame) -> None:
        collected = df.collect()
        VendorLegacy1minRollAdjustedSchema.validate(collected)

        # OHLC consistency on adjusted prices. Positive scalar
        # multiplication preserves ordering: low <= min(o, c) <= max(o, c) <= high.
        violations = collected.filter(
            (pl.col("low") > pl.col("open"))
            | (pl.col("low") > pl.col("close"))
            | (pl.col("low") > pl.col("high"))
            | (pl.col("high") < pl.col("open"))
            | (pl.col("high") < pl.col("close"))
        )
        if violations.height > 0:
            raise ValueError(
                f"Adjusted OHLC consistency violated on {violations.height} rows; "
                f"first: {violations.head(1).to_dicts()}"
            )

        # Monotonicity per symbol.
        sort_check = collected.sort(["symbol", "ts_event"])
        if not collected.equals(sort_check):
            raise ValueError(
                "ts_event is not monotonically increasing within each symbol."
            )

        # Audit invariant: close == unadjusted_close * adjustment_factor,
        # with tolerance derived from float64 ULP and the longest
        # ratio-product chain length. IEEE-754 double has eps ≈ 2.22e-16;
        # each multiplicative step in the cumulative factor contributes
        # at most ~eps relative rounding, so for an N-step chain the
        # bound is ~3 N eps (Higham 2002 §3.1). We use a generous
        # 10 N eps multiplied by the price magnitude for robustness.
        n_rolls = max(1, int(collected["roll_flag"].sum()))
        eps = float(np.finfo(np.float64).eps)
        max_px = float(collected["close"].abs().max() or 0.0)
        tol = 10.0 * n_rolls * eps * max_px
        recovered = collected.with_columns(
            (pl.col("unadjusted_close") * pl.col("adjustment_factor")).alias(
                "_recovered"
            )
        )
        bad = recovered.filter(
            (pl.col("close") - pl.col("_recovered")).abs() > tol
        )
        if bad.height > 0:
            raise ValueError(
                f"Audit invariant violated: close != unadjusted_close * "
                f"adjustment_factor (tol={tol:.3e}) on {bad.height} rows; "
                f"first: {bad.head(1).to_dicts()}"
            )

        # Cross-row invariant (a): exactly one contract per symbol with
        # adjustment_factor == 1.0. That's the anchor (newest) contract.
        # Use isclose rather than == to tolerate cumulative float error
        # (the newest contract itself never multiplies, but defensive).
        for sym in sorted(collected["symbol"].unique(maintain_order=True).to_list()):
            sym_rows = collected.filter(pl.col("symbol") == sym)
            anchor_rows = sym_rows.filter(
                (pl.col("adjustment_factor") - 1.0).abs() < 1e-12
            )
            n_anchor_contracts = anchor_rows["front_contract_symbol"].n_unique()
            if n_anchor_contracts != 1:
                raise ValueError(
                    f"Symbol {sym}: expected exactly one contract with "
                    f"adjustment_factor==1.0 (the newest/anchor); got "
                    f"{n_anchor_contracts}."
                )

        # Cross-row invariant (b): adjustment_factor is constant within
        # each (symbol, front_contract_symbol).
        factor_variance = (
            collected.group_by(["symbol", "front_contract_symbol"])
            .agg(pl.col("adjustment_factor").n_unique().alias("_n"))
            .filter(pl.col("_n") > 1)
        )
        if factor_variance.height > 0:
            raise ValueError(
                f"adjustment_factor is not constant within some "
                f"(symbol, front_contract_symbol) group: "
                f"{factor_variance.to_dicts()}"
            )

        # Cross-row invariant (c): roll_flag True <=> first ts_event per
        # (symbol, front_contract_symbol).
        per_contract_first = (
            collected.group_by(["symbol", "front_contract_symbol"], maintain_order=True)
            .agg(pl.col("ts_event").min().alias("_first_ts"))
        )
        marker = collected.join(
            per_contract_first, on=["symbol", "front_contract_symbol"], how="inner"
        ).with_columns(
            (pl.col("ts_event") == pl.col("_first_ts")).alias("_expected_flag")
        )
        mismatch = marker.filter(pl.col("roll_flag") != pl.col("_expected_flag"))
        if mismatch.height > 0:
            raise ValueError(
                f"roll_flag is inconsistent with first-row-per-contract on "
                f"{mismatch.height} rows; first: {mismatch.head(1).to_dicts()}"
            )

        _log.info(
            "Roll-adjusted validation passed (rows=%d, symbols=%s, rolls=%d)",
            collected.height,
            sorted(collected["symbol"].unique().to_list()),
            n_rolls,
        )

    # ------------------------------------------------------------------
    # write_processed: partitioned parquet, two-phase commit with
    # base_dir.new swap
    # ------------------------------------------------------------------

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        """Partitioned write: ``symbol={ES|NQ}/year={YYYY}/part-0000.parquet``.

        Two-phase commit: stage to ``_staging`` → re-validate every
        partition → promote with a transactional guard that records
        every promoted path so partial failures can be rolled back.
        """
        paths = ctx.paths
        base_dir = paths.data_processed / _DATASET_NAME
        staging_dir = paths.data_processed / "_staging" / _DATASET_NAME
        paths.ensure(staging_dir)

        collected = (
            df.collect()
            .with_columns(pl.col("ts_event").dt.year().alias("_year"))
        )

        staged: list[tuple[Path, Path]] = []
        for (symbol, year), part_df in collected.group_by(
            ["symbol", "_year"], maintain_order=True
        ):
            part_out = part_df.drop("_year")
            part_dir_final = base_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage = staging_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage.mkdir(parents=True, exist_ok=True)
            sp = part_dir_stage / "part-0000.parquet"
            fp = part_dir_final / "part-0000.parquet"
            part_out.write_parquet(sp)
            staged.append((sp, fp))

        # Re-validate every staged file before any promotion.
        for sp, _fp in staged:
            try:
                VendorLegacy1minRollAdjustedSchema.validate(pl.read_parquet(sp))
            except Exception:
                for bad_sp, _bfp in staged:
                    bad_sp.unlink(missing_ok=True)
                _rmtree_empty(staging_dir)
                raise

        # Snapshot pre-promotion state of targets for rollback.
        pre_existing: dict[Path, bytes | None] = {}
        for _sp, fp in staged:
            pre_existing[fp] = fp.read_bytes() if fp.is_file() else None

        promoted: list[tuple[Path, Path]] = []
        try:
            for sp, fp in staged:
                fp.parent.mkdir(parents=True, exist_ok=True)
                sp.replace(fp)
                promoted.append((sp, fp))
        except Exception:
            # Roll back every successfully promoted partition to its
            # pre-existing content.
            for _sp, fp in promoted:
                prev = pre_existing.get(fp)
                if prev is None:
                    fp.unlink(missing_ok=True)
                else:
                    fp.write_bytes(prev)
            _rmtree_empty(staging_dir)
            raise
        finally:
            _rmtree_empty(staging_dir)

        _log.info("Wrote %d adjusted partitions to %s", len(promoted), base_dir)
        return base_dir

    # ------------------------------------------------------------------
    # emit_provenance
    # ------------------------------------------------------------------

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Write atomic provenance JSON (tempfile + os.replace + fsync)
        with full roll-event / contract-factor audit detail and the
        point-in-time caveat flag for level-based use.
        """
        from skie_ninja.utils.hashing import file_sha256

        prov_dir = ctx.paths.data_processed / "_provenance"
        ctx.paths.ensure(prov_dir)

        # Keys match scripts/ingest.py::_source_unchanged contract.
        per_file_checksums = {
            sp.as_posix(): file_sha256(sp) for sp in source_paths if sp.is_file()
        }

        if source_paths:
            source_frame = (
                pl.concat(
                    [pl.scan_parquet(sp) for sp in source_paths], how="vertical"
                )
                .sort(["symbol", "contract_symbol", "ts_event"])
                .collect()
            )
            source_frame_sha = frame_sha256(
                source_frame, sort_cols=["symbol", "contract_symbol", "ts_event"]
            )
        else:
            source_frame_sha = ""

        if hasattr(ctx, "add_dataset_checksum"):
            ctx.add_dataset_checksum(self.name, source_frame_sha)

        # Serialize the per-symbol run summary captured during adjust().
        summary_serializable: dict[str, dict[str, Any]] = {}
        for sym, summary in self._last_run_summary.items():
            summary_serializable[sym] = {
                "window_days": summary.get("window_days"),
                "rolls": [
                    {
                        "roll_date": rr.event.roll_date.isoformat(),
                        "old_contract": rr.event.old_contract,
                        "new_contract": rr.event.new_contract,
                        "t_old_close_utc": rr.t_old_close_utc.isoformat(),
                        "t_new_open_utc": rr.t_new_open_utc.isoformat(),
                        "old_close": rr.old_close,
                        "new_open": rr.new_open,
                        "ratio": rr.ratio,
                    }
                    for rr in summary.get("rolls", [])
                ],
                "contract_factors": summary.get("contract_factors", {}),
                "bars_dropped_non_front": summary.get("bars_dropped_non_front", 0),
                "rejected_oscillations": summary.get("rejected_oscillations", []),
            }

        payload = {
            "dataset": self.name,
            "version": self.version,
            "source_dataset": self._source_dataset,
            "source_dataset_frame_sha256": source_frame_sha,
            "method": "ratio_adjustment_volume_crossover_persistence",
            "method_reference": (
                "de Prado 2018 AFML ch.2 §2.4.3 (Single Future Roll); "
                "supplementary Chan 2013 ch.3, Carver 2023 app. Futures data; "
                "OHLC scalar extension + unadjusted volume follow "
                "Norgate/CSI operational convention (not AFML)."
            ),
            "tier": "evidence_bar",
            # Discriminate evidence-bar tier by feature kind. Round-2
            # finding F-2-5: a single boolean was too permissive — a
            # consumer reading only `evidence_bar_eligible` could
            # silently use non-PIT levels in walk-forward CV.
            "evidence_bar_eligible_returns": True,
            "evidence_bar_eligible_levels": False,
            # Legacy single-boolean key retained for backward
            # compatibility with any consumer written against the
            # v0.1.0 provenance shape. Semantics = returns-only.
            "evidence_bar_eligible": True,
            "level_use_pit_safe": False,
            "level_use_pit_safe_note": (
                "Adjusted level columns (open/high/low/close) are "
                "retrospectively rescaled by the full-sample roll "
                "history. Walk-forward consumers using level-based "
                "features must re-materialize this derivative within "
                "each training fold, or restrict to return-based "
                "transforms. Return-based features ARE PIT-safe on "
                "this derivative. Tracked as P1-LEVEL-USE-POLICY."
            ),
            "roll_adjustment": "multiplicative ratio (cumulative back-adjust)",
            "anchor_rule": (
                "AFML §2.4.3 canonical: ρ = new_open(t_first_new) / "
                "old_close(t_last_old); no synchronous-overlap or "
                "post-roll fallback."
            ),
            "persistence_window_source": "config/instruments.yaml roll_rule.window_days",
            "known_verification_gaps": {
                "volume_vs_oi_crossover": (
                    "No peer-reviewed empirical comparison of volume- vs "
                    "OI-crossover realized-slippage for CME equity-index "
                    "futures is known as of 2026-04-23. Practitioner "
                    "convention used. Phase-1 follow-up P1-ROLL-METHOD."
                ),
                "anchor_sensitivity": (
                    "No empirical comparison of close-to-open vs "
                    "synchronous-overlap vs exchange-settlement anchor. "
                    "Phase-1 follow-up P1-ROLL-ANCHOR."
                ),
            },
            "timestamp_utc": datetime.now(tz=UTC).isoformat(),
            "source_checksums": per_file_checksums,
            "output_path": output_path.as_posix(),
            "run_id": ctx.log.run_id if ctx.log else None,
            "repro_log": ctx.log.to_dict() if ctx.log else None,
            "run_summary": summary_serializable,
        }

        date_str = datetime.now(tz=UTC).strftime("%Y%m%d")
        prov_path = prov_dir / f"{self.name}_{date_str}.json"
        _atomic_write_json(prov_path, payload)
        _log.info("Wrote provenance: %s", prov_path)
        return prov_path


# ---------------------------------------------------------------------------
# Core algorithm helpers (module-level, unit-testable)
# ---------------------------------------------------------------------------


def _session_date_expr() -> pl.Expr:
    """Polars expression mapping a UTC ``ts_event`` to CME session date.

    Rule: CME trading session D runs 17:00 CT (day D-1) through 16:00 CT
    (day D). Shifting a local (America/Chicago) timestamp by +7h aligns
    17:00 → 00:00 of the next calendar day; the date() of the shifted
    timestamp IS the session date.

    Limitations:
      - Does NOT advance past weekend / holiday boundaries (e.g., Friday
        17:01 CT maps to Saturday calendar date, not Monday session).
        This is acceptable for front-month volume argmax because
        weekends/holidays have essentially zero volume — argmax
        outcomes are unaffected. For applications needing holiday-
        aware trading-day mapping, call ``utils/clock.py::trading_day``
        explicitly.
    """
    return (
        pl.col("ts_event")
        .dt.convert_time_zone(_CME_TZ)
        .dt.offset_by(f"{_CME_SESSION_SHIFT_HOURS}h")
        .dt.date()
    )


def detect_raw_front_month_by_day(
    df: pl.DataFrame, window_days: int
) -> pl.DataFrame:
    """Per ``(symbol, session_date)``, identify the front-month contract
    as ``argmax_{contract}(trailing_window_days_cumulative_volume)``.

    Uses a trailing rolling sum of daily volume over ``window_days``
    sessions per contract, then ``argmax`` across contracts per session.
    Ties broken deterministically (higher cumulative volume first, then
    lexicographically-earliest contract_symbol).

    Returns a frame with columns
    ``(symbol, session_date, front_contract_symbol, cumulative_volume)``.
    """
    if window_days < 1:
        raise ValueError(f"window_days must be >= 1, got {window_days}.")

    daily = (
        df.with_columns(_session_date_expr().alias("session_date"))
        .group_by(["symbol", "session_date", "contract_symbol"], maintain_order=True)
        .agg(pl.col("volume").sum().alias("daily_volume"))
        .sort(["symbol", "contract_symbol", "session_date"])
    )
    # Cumulative (trailing-window) volume per (symbol, contract).
    cum = daily.with_columns(
        pl.col("daily_volume")
        .rolling_sum(window_size=window_days, min_samples=1)
        .over(["symbol", "contract_symbol"])
        .alias("cum_volume")
    )

    # argmax per (symbol, session_date) with explicit tie-break.
    winners = (
        cum.sort(
            ["symbol", "session_date", "cum_volume", "contract_symbol"],
            descending=[False, False, True, False],
        )
        .group_by(["symbol", "session_date"], maintain_order=True)
        .agg(
            pl.col("contract_symbol").first().alias("front_contract_symbol"),
            pl.col("cum_volume").first().alias("cumulative_volume"),
        )
    )
    return winners.sort(["symbol", "session_date"])


def apply_persistence_guard(
    raw_front: pl.DataFrame, window_days: int
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Require a new front-month candidate to lead for ``window_days``
    consecutive sessions before committing the roll.

    Returns ``(effective_front_month, rejected_oscillations)`` where
    ``effective_front_month`` carries the committed per-session front
    contract and ``rejected_oscillations`` lists transitions that did
    not persist (for provenance).

    Implementation: iterate per symbol in chronological order; track
    the incumbent and a pending challenger. A challenger becomes
    incumbent only after leading for ``window_days`` consecutive
    sessions.
    """
    if window_days < 1:
        raise ValueError(f"window_days must be >= 1, got {window_days}.")

    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for sym in sorted(raw_front["symbol"].unique(maintain_order=True).to_list()):
        sym_rows = raw_front.filter(pl.col("symbol") == sym).sort("session_date")
        incumbent: str | None = None
        challenger: str | None = None
        challenger_streak = 0
        challenger_start: date | None = None

        for row in sym_rows.iter_rows(named=True):
            raw = row["front_contract_symbol"]

            if incumbent is None:
                # Seed: the first session's raw winner is the incumbent
                # without needing persistence (there is no prior
                # contract to have been persisting).
                incumbent = raw
            elif raw == incumbent:
                # Challenger resets if the incumbent re-takes.
                if challenger is not None:
                    rejected.append(
                        {
                            "symbol": sym,
                            "start_date": challenger_start.isoformat()
                            if challenger_start
                            else None,
                            "end_date": row["session_date"].isoformat(),
                            "challenger": challenger,
                            "incumbent": incumbent,
                            "streak_reached": challenger_streak,
                            "window_required": window_days,
                        }
                    )
                challenger = None
                challenger_streak = 0
                challenger_start = None
            else:
                # raw != incumbent
                if raw != challenger:
                    # Reset challenger.
                    if challenger is not None:
                        rejected.append(
                            {
                                "symbol": sym,
                                "start_date": challenger_start.isoformat()
                                if challenger_start
                                else None,
                                "end_date": row["session_date"].isoformat(),
                                "challenger": challenger,
                                "incumbent": incumbent,
                                "streak_reached": challenger_streak,
                                "window_required": window_days,
                            }
                        )
                    challenger = raw
                    challenger_streak = 1
                    challenger_start = row["session_date"]
                else:
                    challenger_streak += 1

                if challenger_streak >= window_days:
                    # Commit the roll: the challenger becomes the
                    # incumbent effective at challenger_start (first
                    # session the challenger led).
                    # Rewrite prior sessions since challenger_start.
                    assert challenger_start is not None  # narrows type
                    for rec in records[::-1]:
                        if rec["symbol"] != sym:
                            continue
                        if rec["session_date"] < challenger_start:
                            break
                        rec["effective_front_contract_symbol"] = challenger
                    incumbent = challenger
                    challenger = None
                    challenger_streak = 0
                    challenger_start = None

            records.append(
                {
                    "symbol": sym,
                    "session_date": row["session_date"],
                    "effective_front_contract_symbol": incumbent,
                    "raw_front_contract_symbol": raw,
                }
            )

    if not records:
        effective = pl.DataFrame(
            schema={
                "symbol": pl.Utf8,
                "session_date": pl.Date,
                "effective_front_contract_symbol": pl.Utf8,
                "raw_front_contract_symbol": pl.Utf8,
            }
        )
    else:
        effective = pl.DataFrame(records).sort(["symbol", "session_date"])

    return effective, rejected


def detect_roll_events(effective_front: pl.DataFrame) -> list[RollEvent]:
    """Identify committed roll events from the effective (post-persistence)
    front-month series."""
    events: list[RollEvent] = []
    if effective_front.height == 0:
        return events
    for sym in sorted(
        effective_front["symbol"].unique(maintain_order=True).to_list()
    ):
        sym_rows = effective_front.filter(pl.col("symbol") == sym).sort("session_date")
        prev_contract: str | None = None
        for row in sym_rows.iter_rows(named=True):
            current = row["effective_front_contract_symbol"]
            if prev_contract is not None and current != prev_contract:
                events.append(
                    RollEvent(
                        roll_date=row["session_date"],
                        old_contract=prev_contract,
                        new_contract=current,
                    )
                )
            prev_contract = current
    return events


def compute_roll_ratio_afml(
    df: pl.DataFrame,
    event: RollEvent,
    symbol: str,
    effective_front: pl.DataFrame,
) -> RollRatio:
    """AFML §2.4.3 anchor: ρ = new_open(t_first_new) / old_close(t_last_old).

    ``t_last_old`` = last 1-min bar of ``old`` on its last session as
    effective front-month (= session immediately before ``event.roll_date``).
    ``t_first_new`` = first 1-min bar of ``new`` on its first session as
    effective front-month (= ``event.roll_date``).

    Raises ``NoOverlapError`` if either anchor bar is missing.
    """
    # Find the old contract's last-as-effective-front session date.
    old_sessions = (
        effective_front.filter(
            (pl.col("symbol") == symbol)
            & (pl.col("effective_front_contract_symbol") == event.old_contract)
        )["session_date"]
        .sort()
    )
    if old_sessions.len() == 0:
        raise NoOverlapError(
            f"Roll {symbol} {event.old_contract}->{event.new_contract}: "
            f"old contract never held effective-front status."
        )
    old_last_session = old_sessions.to_list()[-1]

    old_bars = (
        df.filter(
            (pl.col("symbol") == symbol)
            & (pl.col("contract_symbol") == event.old_contract)
            & (_session_date_expr() == old_last_session)
        )
        .sort("ts_event")
    )
    if old_bars.height == 0:
        raise NoOverlapError(
            f"Roll {symbol} {event.old_contract}->{event.new_contract} "
            f"on {event.roll_date}: no bar for old contract on "
            f"{old_last_session} (its last-as-front session)."
        )
    old_last = old_bars.tail(1).to_dicts()[0]

    new_bars = (
        df.filter(
            (pl.col("symbol") == symbol)
            & (pl.col("contract_symbol") == event.new_contract)
            & (_session_date_expr() == event.roll_date)
        )
        .sort("ts_event")
    )
    if new_bars.height == 0:
        raise NoOverlapError(
            f"Roll {symbol} {event.old_contract}->{event.new_contract} "
            f"on {event.roll_date}: no bar for new contract on its "
            f"first-as-front session."
        )
    new_first = new_bars.head(1).to_dicts()[0]

    old_close = float(old_last["close"])
    new_open = float(new_first["open"])
    ratio = new_open / old_close

    return RollRatio(
        event=event,
        t_old_close_utc=old_last["ts_event"],
        t_new_open_utc=new_first["ts_event"],
        old_close=old_close,
        new_open=new_open,
        ratio=ratio,
    )


def _adjust_one_symbol(
    sym_df: pl.DataFrame,
    symbol: str,
    window_days: int,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Full roll-adjustment pipeline for one root symbol.

    Returns ``(adjusted_frame, summary_dict)`` where ``summary_dict``
    carries rolls / contract-factors / rejected-oscillations / bars
    dropped — consumed by ``emit_provenance`` for audit traceability.
    """
    summary: dict[str, Any] = {
        "window_days": window_days,
        "rolls": [],
        "contract_factors": {},
        "bars_dropped_non_front": 0,
        "rejected_oscillations": [],
    }
    if sym_df.height == 0:
        return _empty_adjusted_frame(), summary

    raw_front = detect_raw_front_month_by_day(sym_df, window_days)
    effective_front, rejected = apply_persistence_guard(raw_front, window_days)
    summary["rejected_oscillations"] = rejected

    events = detect_roll_events(effective_front)
    ratios: list[RollRatio] = [
        compute_roll_ratio_afml(sym_df, ev, symbol, effective_front)
        for ev in events
    ]
    summary["rolls"] = ratios

    # Chain-continuity assertion: event_{k}.new == event_{k+1}.old.
    for k in range(len(ratios) - 1):
        nk = ratios[k].event.new_contract
        ok = ratios[k + 1].event.old_contract
        if nk != ok:
            raise ValueError(
                f"Roll-chain discontinuity for symbol {symbol} at "
                f"event index {k}: event[{k}].new={nk!r} != "
                f"event[{k+1}].old={ok!r}."
            )

    # Derive newest contract from the effective front-month series
    # (the last session's effective front). Assert consistency with
    # the last roll event (if any).
    last_effective = (
        effective_front.filter(pl.col("symbol") == symbol)
        .sort("session_date")
        .tail(1)
    )
    if last_effective.height == 0:
        # No effective front-month data (single-contract with no rolls
        # and empty guard output). Fall back to raw-front's last session.
        last_row = raw_front.filter(pl.col("symbol") == symbol).tail(1)
        newest = last_row["front_contract_symbol"][0] if last_row.height else None
    else:
        newest = last_effective["effective_front_contract_symbol"][0]
    if ratios and newest is not None and newest != ratios[-1].event.new_contract:
        raise ValueError(
            f"Newest-contract inconsistency for symbol {symbol}: "
            f"effective-front last session = {newest!r}, "
            f"but ratios[-1].new_contract = {ratios[-1].event.new_contract!r}."
        )

    # Cumulative multiplicative factors. Newest = 1.0; older contracts
    # get product of ρ_k for every roll newer than them.
    contract_factor: dict[str, float] = {}
    if not ratios:
        only_contracts = (
            effective_front.filter(pl.col("symbol") == symbol)[
                "effective_front_contract_symbol"
            ]
            .unique(maintain_order=True)
            .to_list()
        )
        for c in only_contracts:
            contract_factor[c] = 1.0
    else:
        if newest is not None:
            contract_factor[newest] = 1.0
        cum = 1.0
        for rr in reversed(ratios):
            cum *= rr.ratio
            contract_factor[rr.event.old_contract] = cum
    summary["contract_factors"] = dict(contract_factor)

    # Front-month filter + factor attach + OHLC adjust.
    front_map = effective_front.filter(pl.col("symbol") == symbol).select(
        pl.col("session_date"),
        pl.col("effective_front_contract_symbol").alias("front_contract_symbol"),
    )
    sym_with_date = sym_df.with_columns(_session_date_expr().alias("_session_date"))
    total_raw = sym_with_date.height
    front_only = sym_with_date.join(
        front_map,
        left_on=["_session_date", "contract_symbol"],
        right_on=["session_date", "front_contract_symbol"],
        how="inner",
    )
    summary["bars_dropped_non_front"] = total_raw - front_only.height

    factor_rows = pl.DataFrame(
        {
            "contract_symbol": list(contract_factor.keys()),
            "adjustment_factor": list(contract_factor.values()),
        }
    )
    enriched = front_only.join(factor_rows, on="contract_symbol", how="inner")

    first_session = (
        enriched.group_by("contract_symbol", maintain_order=True).agg(
            pl.col("_session_date").min().alias("_first_session")
        )
    )
    enriched = enriched.join(first_session, on="contract_symbol", how="inner")

    adjusted = enriched.with_columns(
        (pl.col("open") * pl.col("adjustment_factor")).alias("_open_adj"),
        (pl.col("high") * pl.col("adjustment_factor")).alias("_high_adj"),
        (pl.col("low") * pl.col("adjustment_factor")).alias("_low_adj"),
        (pl.col("close") * pl.col("adjustment_factor")).alias("_close_adj"),
        pl.col("close").alias("unadjusted_close"),
        (pl.col("_session_date") == pl.col("_first_session")).alias("roll_flag"),
        pl.col("contract_symbol").alias("front_contract_symbol"),
    ).select(
        pl.col("ts_event"),
        pl.col("_open_adj").alias("open"),
        pl.col("_high_adj").alias("high"),
        pl.col("_low_adj").alias("low"),
        pl.col("_close_adj").alias("close"),
        pl.col("volume"),
        pl.col("symbol"),
        pl.col("front_contract_symbol"),
        pl.col("adjustment_factor"),
        pl.col("unadjusted_close"),
        pl.col("roll_flag"),
    )

    return adjusted.sort(["symbol", "ts_event"]), summary


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _empty_adjusted_frame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "ts_event": pl.Datetime("us", "UTC"),
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Int64,
            "symbol": pl.Utf8,
            "front_contract_symbol": pl.Utf8,
            "adjustment_factor": pl.Float64,
            "unadjusted_close": pl.Float64,
            "roll_flag": pl.Boolean,
        }
    )


def _rmtree_empty(path: Path) -> None:
    if not path.is_dir():
        return
    for child in path.iterdir():
        if child.is_dir():
            _rmtree_empty(child)
    with contextlib.suppress(OSError):
        path.rmdir()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomic JSON write: tempfile in the same directory, fsync, os.replace."""
    payload_bytes = (
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n"
    ).encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(payload_bytes)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)


def _json_default(obj: Any) -> Any:
    """json.dumps default: dataclass → dict; date/datetime → isoformat."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError(f"Not JSON-serializable: {type(obj).__name__}")


# Self-register at import time.
register(VendorLegacy1minRollAdjustedIngestJob())