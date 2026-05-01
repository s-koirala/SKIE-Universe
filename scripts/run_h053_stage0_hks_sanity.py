"""H053 Cycle 7 Stage-0 sanity — HKS 2010 intraday volatility U-shape on ES/NQ.

Per [plan/h053_buildout_2026-04-28.md](../plan/h053_buildout_2026-04-28.md)
Cycle 7: substrate-behavior validation against the
[Heston, Korajczyk & Sadka 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x)
published intraday volatility seasonality. **This is NOT a research
finding** — the HKS Figure 1 stylized fact (intraday volatility U-shape,
peak at the open and close, trough at midday) is well-established across
many primary sources (Andersen-Bollerslev 1997 *JEF* 4(2-3):115-158,
HKS 2010 §III + Figure 1, Wood-McInish-Ord 1985 *JF* 40(3):723-739).
Failure to observe a U-shape on our futures substrate would indicate a
substrate quality / time-zone / window-alignment defect, not a new
finding about H053.

## Method

For each instrument ``i ∈ {ES, NQ}``:

1. Filter to RTH bars (09:31-16:00 ET; 6.5 hours = 390 bars per session
   per the §3.0 R5 inclusive end-of-bar convention).
2. Build 13 half-hour bins per session: ``09:30-10:00``, ``10:00-10:30``,
   ..., ``15:30-16:00`` ET. Bar at ts_event ``HH:MM`` ET belongs to the
   bin ending at ``HH:MM`` (or earlier).
3. For each ``(symbol, session_date, bin_h)`` compute log-return
   ``r_{d, h} = log(close_end_of_bin / open_start_of_bin)`` where the
   start/end are §3.0 R5-compliant (start = open of the bar timestamped
   at the bin's first minute; end = close of the bar timestamped at the
   bin's last minute).
4. For each ``(symbol, bin_h)`` series across trading days, compute:
   - **Lag-1 autocorrelation**: ``ρ_{i, h} = corr(r_{d, h}, r_{d-1, h})``
     (informational; recorded but not part of the verdict).
   - **Realized volatility**: ``σ_{i, h} = std(r_{d, h})`` (in the
     log-return scale; sample std with ddof=1).

5. **HKS Figure 1 U-shape sanity**: assert ``σ_{i, 0}`` (09:30-10:00) AND
   ``σ_{i, 12}`` (15:30-16:00) both exceed the median σ across the 13
   bins by at least the operational floor. This is the canonical
   intraday-volatility-seasonality stylized fact reproduced across
   decades of primary sources.

## Verdict

PASS iff for both ES and NQ:
  (a) ``σ_{0}`` (open bin) > median(σ) by ≥ 10% (relative).
  (b) ``σ_{12}`` (close bin) > median(σ) by ≥ 10% (relative).
  (c) All 13 bin returns are finite with ``n_sessions ≥ 200`` per bin.

The 10% relative-margin floor is an operational substrate-behavior
threshold, NOT a strict statistical test. Tracked under follow-up
``P1-H053-STAGE0-USHAPE-MARGIN-EMPIRICAL`` if a more rigorous threshold
becomes desirable.

## Outputs

- ``logs/reproducibility/{run_id}_h053_stage0_hks_sanity.json``: 26
  per-bin ``ρ_{i, h}`` values + tally + verdict.
- ``reports/h053/stage0_hks_sanity.md``: human-readable disposition memo.

## Reproducibility

Pinned BLAS via ``OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1``
per ADR-0009. Substrate path resolves via ``--substrate-path`` flag with
fallback to ``$H053_SUBSTRATE_PATH`` env var, then
``paths.root / data / processed / vendor_legacy_1min_roll_adjusted``.
Sidecar SHA256 written via the project ``ReproLog`` convention.

## References

- Heston, S. L., Korajczyk, R. A., & Sadka, R. 2010. "Intraday
  Patterns in the Cross-section of Stock Returns." *Journal of Finance*
  65(4):1369-1407.
  [DOI 10.1111/j.1540-6261.2010.01573.x](https://doi.org/10.1111/j.1540-6261.2010.01573.x).
  Figure 1 documents the canonical equity intraday volatility U-shape;
  this Stage-0 verdict is grounded ONLY in Figure 1's stylized fact,
  NOT the §III cross-sectional continuation finding (which is
  informational-only and reported as a single-instrument lag-1 ACF
  diagnostic).
- Andersen, T. G. & Bollerslev, T. 1997. "Intraday Periodicity and
  Volatility Persistence in Financial Markets." *Journal of Empirical
  Finance* 4(2-3):115-158.
  [DOI 10.1016/S0927-5398(97)00004-2](https://doi.org/10.1016/S0927-5398(97)00004-2).
- Wood, R. A., McInish, T. H., & Ord, J. K. 1985. "An Investigation of
  Transactions Data for NYSE Stocks." *Journal of Finance* 40(3):723-739.
  [DOI 10.1111/j.1540-6261.1985.tb04996.x](https://doi.org/10.1111/j.1540-6261.1985.tb04996.x).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from skie_ninja.utils.paths import ProjectPaths

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h053_stage0")

# justify: HKS 2010 grid is 13 half-hour bins covering RTH 09:30-16:00 ET
# (6.5h / 0.5h = 13). Bin boundaries are inclusive-start, exclusive-end on
# bar timestamps per design.md §3.0 R5 inclusivity convention.
_BIN_STARTS_ET: list[tuple[int, int]] = [
    (9, 30), (10, 0), (10, 30), (11, 0), (11, 30), (12, 0), (12, 30),
    (13, 0), (13, 30), (14, 0), (14, 30), (15, 0), (15, 30),
]
# justify: post-RTH-close bar; exclusive upper bound for the last bin.
_RTH_END_ET: tuple[int, int] = (16, 0)
# justify: HKS Figure 1 U-shape sanity — open + close bin σ must exceed
# the median bin σ by at least 10% (relative). Operational substrate-
# behavior threshold; tracked under follow-up
# `P1-H053-STAGE0-USHAPE-MARGIN-EMPIRICAL` if a more rigorous threshold
# becomes desirable.
_HKS_USHAPE_MARGIN_FRAC: float = 0.10
# justify: minimum sessions per bin for a meaningful σ estimate. With
# ~2,500 trading days × 11 years and per-bin coverage ≥80% (based on
# substrate inspection), 200 is well below typical achievable counts;
# the floor exists to flag a degraded-substrate edge case.
_HKS_MIN_SESSIONS_PER_BIN: int = 200


@dataclass(frozen=True)
class HKSStage0Result:
    """Per-symbol Stage-0 HKS sanity output.

    Primary verdict criterion: HKS Figure 1 U-shape (open + close bins
    have higher realized volatility than the median bin). Lag-1 ACF
    values are recorded as informational diagnostics.
    """

    symbol: str
    n_sessions: int
    n_bins: int
    bin_acf_values: list[float]          # 13 lag-1 autocorr values (informational)
    bin_volatility_values: list[float]   # 13 std-of-bin-return values (load-bearing)
    bin_n_per_bin: list[int]             # 13 session counts per bin
    median_bin_volatility: float
    open_bin_vs_median_ratio: float      # σ_0 / median(σ)
    close_bin_vs_median_ratio: float     # σ_12 / median(σ)
    open_bin_passes: bool                # σ_0 > 1.10 × median(σ)
    close_bin_passes: bool               # σ_12 > 1.10 × median(σ)
    coverage_passes: bool                # all bin n ≥ 200
    verdict: str                         # "PASS" | "FAIL"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _check_blas_thread_pinning() -> None:
    """Warn if any of the BLAS thread-count env vars are not pinned to 1.

    Per ADR-0009: BLAS thread reordering of float64 reductions causes
    non-deterministic σ values. The Stage-0 verdict is byte-deterministic
    only when OMP/MKL/OPENBLAS thread counts are pinned to 1.
    """
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        val = os.environ.get(var)
        if val != "1":
            _log.warning(
                "BLAS thread-pinning contract (ADR-0009) violation: %s=%r "
                "(expected '1'). σ values may be non-deterministic across runs.",
                var, val,
            )


def _substrate_dataset_checksum(substrate_root: Path, symbols: list[str]) -> str:
    """Compute a deterministic checksum of every parquet partition the
    Stage-0 sanity will read.

    Used to record substrate provenance in the sidecar so cross-worktree
    reproducibility is content-anchored, not path-anchored. Sorted file
    list → SHA256 of concatenated ``(relative_path, file_sha256)`` pairs.

    Reference: F-1-2 quant-audit remediation. The roll-adjusted substrate
    lives outside this worktree's tree; the SHA256 records prove the
    substrate is content-equivalent to whatever a future re-run reads.
    """
    parts = []
    for sym in sorted(symbols):
        for path in sorted((substrate_root / f"symbol={sym}").glob("year=*/part-*.parquet")):
            with path.open("rb") as fh:
                file_sha = hashlib.sha256(fh.read()).hexdigest()
            rel = path.relative_to(substrate_root).as_posix()
            parts.append(f"{rel}:{file_sha}")
    aggregate = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(aggregate).hexdigest()


def _resolve_substrate_path(cli_arg: str | None) -> Path:
    """Resolve substrate path via CLI > env var > project-root fallback."""
    if cli_arg:
        p = Path(cli_arg).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Substrate path {p} does not exist.")
        return p
    env = os.environ.get("H053_SUBSTRATE_PATH")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(
                f"H053_SUBSTRATE_PATH={p} does not exist."
            )
        return p
    paths = ProjectPaths.discover()
    p = paths.root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    if not p.exists():
        raise FileNotFoundError(
            f"Substrate not found at {p}; pass --substrate-path or set "
            "H053_SUBSTRATE_PATH env var."
        )
    return p


def _load_symbol_substrate(substrate_root: Path, symbol: str) -> pl.DataFrame:
    """Load all year partitions for ``symbol`` into a single DataFrame.

    Substrate schema: ts_event (Datetime us UTC), open/high/low/close (f64),
    volume (i64), symbol (str), front_contract_symbol, adjustment_factor,
    unadjusted_close, roll_flag.
    """
    pattern = str(substrate_root / f"symbol={symbol}" / "year=*" / "*.parquet")
    df = pl.read_parquet(pattern)
    if len(df) == 0:
        raise ValueError(f"No rows found at {pattern}")
    return df


def _compute_half_hour_bin_returns(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute log-returns per (session_date, bin_idx) on RTH bars.

    Bin idx 0 = 09:30-10:00 ET, 1 = 10:00-10:30, ..., 12 = 15:30-16:00.

    Per design.md §3.0 R5: bar at ts_event = HH:MM ET represents the
    interval [HH:(MM-1), HH:MM) in clock-time. So the 09:30-10:00 ET
    bin is composed of bars timestamped 09:31..10:00 ET (30 bars).
    Bin start (open) = open of the 09:31 ET bar; bin end (close) =
    close of the 10:00 ET bar.

    Returns: DataFrame with columns
        session_date_et (Date), bin_idx (Int32), log_return (f64).
    """
    # Convert ts_event to ET wall clock + extract date + minute-of-day.
    # justify: cast _hour_et and _minute_et to Int32 immediately because
    # Polars' default i8 dtype on dt.hour()/dt.minute() overflows at
    # `(_h - 9) * 60` for h ≥ 12 (i8 max 127; e.g., (12-9)*60 = 180 ≫ 127),
    # silently scrambling bin assignment for the second half of RTH.
    panel = panel.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.date().alias("_session_date_et"),
        pl.col("_ts_et").dt.hour().cast(pl.Int32).alias("_hour_et"),
        pl.col("_ts_et").dt.minute().cast(pl.Int32).alias("_minute_et"),
    )
    # Filter to RTH-window bars: ts_event > 09:30 ET AND ts_event ≤ 16:00 ET.
    # Per §3.0 R5 inclusive-end convention: 09:31..16:00 ET bars cover
    # [09:30, 16:00) wall-clock interval. The 09:30 ET bar (which would
    # represent [09:29, 09:30)) is excluded since it's pre-RTH.
    panel = panel.filter(
        (
            ((pl.col("_hour_et") == 9) & (pl.col("_minute_et") >= 31))
            | ((pl.col("_hour_et") >= 10) & (pl.col("_hour_et") < 16))
            | ((pl.col("_hour_et") == 16) & (pl.col("_minute_et") == 0))
        )
    )
    # Assign bin index: 0 = (09:31..10:00), 1 = (10:01..10:30), ..., 12 = (15:31..16:00)
    # Computed from minute-of-day relative to 09:30 ET. The bar at HH:MM
    # belongs to bin floor((mod - 1) / 30) where mod = (hour-9.5)*60 + minute
    # — equivalent: bin_idx = floor((minute_since_0930 - 1) / 30).
    # Simpler: minute-since-0930 of the bar's ts_event, where ts_event
    # is at the bar's right edge.
    minute_since_0930 = (
        (pl.col("_hour_et") - 9) * 60 + pl.col("_minute_et") - 30
    )  # 09:31 ET → 1; 10:00 → 30; 16:00 → 390.
    # Bar at right-edge t belongs to the bin that ENDS at t (or the bin
    # containing t-1 minute), so bin_idx = ceil(minute_since_0930 / 30) - 1.
    # 09:31 (=1) → bin 0; 10:00 (=30) → bin 0; 10:01 (=31) → bin 1; 16:00 (=390) → bin 12.
    bin_idx_expr = ((minute_since_0930 - 1) // 30).cast(pl.Int32).alias("_bin_idx")
    panel = panel.with_columns(bin_idx_expr).filter(
        (pl.col("_bin_idx") >= 0) & (pl.col("_bin_idx") <= 12)
    )

    # Aggregate per (session, bin) — first open (sorted by ts_event) and
    # last close.
    agg = (
        panel.sort(["symbol", "_session_date_et", "_bin_idx", "ts_event"])
        .group_by(["_session_date_et", "_bin_idx"], maintain_order=True)
        .agg(
            pl.col("open").first().alias("bin_open"),
            pl.col("close").last().alias("bin_close"),
            pl.col("ts_event").len().alias("n_bars"),
        )
    )
    # justify: 30 1-min bars per half-hour bin under §3.0 R5.
    # Sessions with incomplete bins (<30 bars) are dropped via the
    # downstream completeness gate; partial-bin returns would bias the
    # ACF estimator with non-stationary missingness.
    agg = agg.filter(pl.col("n_bars") == 30)
    # Compute log return.
    agg = agg.with_columns(
        (pl.col("bin_close") / pl.col("bin_open")).log().alias("log_return")
    ).select(["_session_date_et", "_bin_idx", "log_return"])
    return agg


def _lag1_autocorr(values: np.ndarray) -> float:
    """Lag-1 Pearson autocorrelation; ddof=1.

    Returns NaN for series with fewer than 3 finite observations or zero
    variance.
    """
    v = np.asarray(values, dtype=np.float64)
    finite_mask = np.isfinite(v)
    v = v[finite_mask]
    if len(v) < 3:
        return float("nan")
    a = v[:-1]
    b = v[1:]
    if a.std(ddof=1) <= 0 or b.std(ddof=1) <= 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _stage0_for_symbol(
    substrate_root: Path,
    symbol: str,
) -> HKSStage0Result:
    """Compute per-symbol HKS Stage-0 sanity result."""
    _log.info("Loading %s substrate from %s …", symbol, substrate_root)
    panel = _load_symbol_substrate(substrate_root, symbol)
    _log.info("%s loaded: %d rows", symbol, len(panel))

    bin_returns = _compute_half_hour_bin_returns(panel)
    _log.info(
        "%s bin returns: %d rows across %d sessions, %d unique bins",
        symbol,
        len(bin_returns),
        bin_returns["_session_date_et"].n_unique(),
        bin_returns["_bin_idx"].n_unique(),
    )
    n_sessions = bin_returns["_session_date_et"].n_unique()

    bin_acf_values: list[float] = []
    bin_volatility_values: list[float] = []
    bin_n_per_bin: list[int] = []
    for bin_idx in range(13):
        sub = (
            bin_returns.filter(pl.col("_bin_idx") == bin_idx)
            .sort("_session_date_et")["log_return"]
            .to_numpy()
        )
        finite = np.asarray(sub)
        finite = finite[np.isfinite(finite)]
        rho = _lag1_autocorr(sub)
        sigma = float(finite.std(ddof=1)) if len(finite) >= 2 else float("nan")
        bin_acf_values.append(rho)
        bin_volatility_values.append(sigma)
        bin_n_per_bin.append(int(len(finite)))
        _log.info(
            "%s bin %02d (start=%02d:%02d ET): σ=%.6f, lag-1 ρ=%.6f (n=%d)",
            symbol, bin_idx,
            _BIN_STARTS_ET[bin_idx][0], _BIN_STARTS_ET[bin_idx][1],
            sigma, rho, len(finite),
        )

    finite_sigmas = [s for s in bin_volatility_values if np.isfinite(s)]
    median_sigma = float(np.median(finite_sigmas)) if finite_sigmas else float("nan")
    sigma_open = bin_volatility_values[0]
    sigma_close = bin_volatility_values[12]
    open_ratio = (
        sigma_open / median_sigma
        if (np.isfinite(sigma_open) and np.isfinite(median_sigma) and median_sigma > 0)
        else float("nan")
    )
    close_ratio = (
        sigma_close / median_sigma
        if (np.isfinite(sigma_close) and np.isfinite(median_sigma) and median_sigma > 0)
        else float("nan")
    )
    open_passes = bool(np.isfinite(open_ratio) and open_ratio >= 1.0 + _HKS_USHAPE_MARGIN_FRAC)
    close_passes = bool(np.isfinite(close_ratio) and close_ratio >= 1.0 + _HKS_USHAPE_MARGIN_FRAC)
    coverage_passes = all(n >= _HKS_MIN_SESSIONS_PER_BIN for n in bin_n_per_bin)
    verdict = "PASS" if (open_passes and close_passes and coverage_passes) else "FAIL"

    return HKSStage0Result(
        symbol=symbol,
        n_sessions=n_sessions,
        n_bins=len(finite_sigmas),
        bin_acf_values=bin_acf_values,
        bin_volatility_values=bin_volatility_values,
        bin_n_per_bin=bin_n_per_bin,
        median_bin_volatility=median_sigma,
        open_bin_vs_median_ratio=open_ratio,
        close_bin_vs_median_ratio=close_ratio,
        open_bin_passes=open_passes,
        close_bin_passes=close_passes,
        coverage_passes=coverage_passes,
        verdict=verdict,
    )


def _write_sidecar(
    results: list[HKSStage0Result],
    repro_log_dir: Path,
    run_id: str,
    substrate_path: str,
    substrate_checksum: str,
    git_head: str | None = None,
) -> tuple[Path, str, str]:
    """Atomic-write the HKS Stage-0 sidecar JSON.

    Returns (path, file_sha256, scientific_payload_sha256). The
    scientific-payload SHA is computed over the ``h053_stage0_hks_sanity``
    sub-object (excluding the ``_meta`` envelope which contains the
    wall-clock-dependent ``written_at``). The disposition memo and any
    downstream reproducibility check should record the
    scientific-payload SHA, NOT the file SHA — only the former is
    re-derivable across runs of the same script on the same substrate.

    Reference: Round-1 R-1 / quant F-1-6 remediation.
    """
    repro_log_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = repro_log_dir / f"{run_id}_h053_stage0_hks_sanity.json"
    scientific_payload = {
        "version": "1.0",
        "method": (
            "HKS Figure 1 intraday volatility U-shape: σ_open + σ_close > "
            "1.10 × median(σ) on half-hour bin log-returns per symbol"
        ),
        "method_reference": (
            "Heston-Korajczyk-Sadka 2010, J Finance 65(4):1369-1407, "
            "doi:10.1111/j.1540-6261.2010.01573.x Figure 1; "
            "Andersen-Bollerslev 1997 J Empirical Finance 4(2-3):115-158; "
            "Wood-McInish-Ord 1985 J Finance 40(3):723-739"
        ),
        "substrate_path": substrate_path,
        "substrate_dataset_checksum": substrate_checksum,
        "bin_starts_et": [list(b) for b in _BIN_STARTS_ET],
        "rth_end_et": list(_RTH_END_ET),
        "ushape_margin_frac": _HKS_USHAPE_MARGIN_FRAC,
        "min_sessions_per_bin": _HKS_MIN_SESSIONS_PER_BIN,
        "results": [r.to_dict() for r in results],
    }
    # Scientific-payload SHA: byte-deterministic across runs of the same
    # script on the same substrate (sorted-keys JSON dump, no wall-clock).
    scientific_bytes = json.dumps(
        scientific_payload, indent=2, sort_keys=True
    ).encode("utf-8")
    scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()

    payload = {
        "h053_stage0_hks_sanity": scientific_payload,
        "_meta": {
            "written_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "git_head": git_head,
            "scientific_payload_sha256": scientific_sha,
        },
    }
    serialised = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    tmp = sidecar_path.with_suffix(".json.tmp")
    with tmp.open("wb") as fh:
        fh.write(serialised)
    os.replace(tmp, sidecar_path)
    file_sha = hashlib.sha256(serialised).hexdigest()
    return sidecar_path, file_sha, scientific_sha


def _git_head() -> str | None:
    """Best-effort git HEAD capture for sidecar provenance. Returns None
    on any failure (no git, no .git, etc.)."""
    import subprocess
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ProjectPaths.discover().root,
            stderr=subprocess.DEVNULL, timeout=5,
        )
        return out.decode("ascii").strip()
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="H053 Stage-0 sanity: HKS half-hour periodicity sign on ES/NQ."
    )
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument(
        "--symbols", default="ES,NQ", help="Comma-separated symbols to check."
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run id for sidecar; defaults to UTC timestamp.",
    )
    args = parser.parse_args(argv)

    _check_blas_thread_pinning()
    substrate_root = _resolve_substrate_path(args.substrate_path)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    paths = ProjectPaths.discover()
    repro_log_dir = paths.logs_reproducibility
    run_id = args.run_id or f"h053_stage0_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    _log.info("Computing substrate dataset checksum (per-partition SHA256 roll-up) …")
    substrate_checksum = _substrate_dataset_checksum(substrate_root, symbols)
    _log.info("Substrate dataset_checksum=%s", substrate_checksum)
    git_head = _git_head()
    if git_head:
        _log.info("git HEAD=%s", git_head)

    results: list[HKSStage0Result] = []
    for sym in symbols:
        try:
            r = _stage0_for_symbol(substrate_root, sym)
            results.append(r)
            _log.info(
                "%s verdict=%s | open_ratio=%.4f | close_ratio=%.4f | "
                "median_σ=%.6f | n_sessions=%d",
                r.symbol, r.verdict,
                r.open_bin_vs_median_ratio, r.close_bin_vs_median_ratio,
                r.median_bin_volatility, r.n_sessions,
            )
        except Exception as exc:
            _log.exception("Symbol %s failed: %s", sym, exc)
            raise

    sidecar_path, file_sha, scientific_sha = _write_sidecar(
        results, repro_log_dir, run_id, str(substrate_root),
        substrate_checksum, git_head=git_head,
    )
    _log.info("Sidecar written: %s", sidecar_path)
    _log.info("File SHA256: %s", file_sha)
    _log.info("Scientific-payload SHA256: %s (byte-deterministic across runs)", scientific_sha)

    overall_pass = all(r.verdict == "PASS" for r in results)
    if not overall_pass:
        _log.error(
            "Stage-0 OVERALL FAIL — at least one symbol failed HKS Figure 1 U-shape."
        )
        for r in results:
            if r.verdict != "PASS":
                _log.error(
                    "  %s: open_ratio=%.4f (pass=%s), close_ratio=%.4f (pass=%s), "
                    "coverage=%s",
                    r.symbol,
                    r.open_bin_vs_median_ratio, r.open_bin_passes,
                    r.close_bin_vs_median_ratio, r.close_bin_passes,
                    r.coverage_passes,
                )
        return 1
    _log.info(
        "Stage-0 OVERALL PASS — substrate exhibits HKS Figure 1 intraday volatility U-shape."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
