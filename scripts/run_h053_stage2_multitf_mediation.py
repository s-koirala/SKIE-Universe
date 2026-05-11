"""H053 Cycle 9 Stage-2 — multi-timeframe + mediation analysis.

Per [plan/buildouts/h053_buildout_2026-04-28.md](../plan/buildouts/h053_buildout_2026-04-28.md)
Cycle 9: ElasticNet on full X (Block A + Block B + Block C, mediator
partial-out per design.md §5.4) with partial-R² increment CI on the
``Med`` sub-fold; PC1 mediator collapse; E-value sensitivity; descriptive
NIE/NDE per Baron-Kenny / VanderWeele 2015.

Per design.md §1 critical interpretive note: the mediation block is
**descriptive decomposition**, not causal identification. A statistically
significant NIE annotates `mediation-NIE-significant` per §10.2 but does
NOT promote past the Sharpe gate.

## Method

1. **Substrate**: roll-adjusted ``vendor_legacy_1min_roll_adjusted``.
2. **Feature assembly**: Block A (5 daily features) + Block B (27 hourly
   features) + Block C (6 microstructure 5/15-min features) + Block D
   (4 mediator features) per (symbol, session_date_et). Total: ~42
   features per session. Computed via the H053 feature factory modules
   from Cycle 7.
3. **Predictand**: log(C(10:30 ET) / C(09:45 ET)) per session.
4. **Splits**:
   - Train (IS): 2015-01-01 → 2022-12-31.
   - Test (OOS): 2024-01-01 → 2025-12-{03 ES, 19 NQ}.
5. **Mediation analyses**:
   a. **Partial-R²** of multi-timeframe X (Blocks A+B+C) beyond the
      mediator-only baseline M (Block D), with paired-pairs
      stationary-bootstrap percentile CI on the OOS test fold.
   b. **PC1 collapse** of M (4-dim) per design.md §5.4.
   c. **E-value sensitivity** per VanderWeele-Ding 2017 on the partial-R²
      point + CI bound.
   d. **Descriptive Baron-Kenny NIE/NDE** decomposition with paired-pairs
      bootstrap CI.

## Out-of-scope (deferred to Cycle 10)

- ElasticNet hyperparameter tuning (Cycle 10 Stage-3 27-cell CV grid).
- Cross-fitted DML alternative (Chernozhukov et al. 2018; tracked under
  follow-up `P1-H053-CYCLE9-DML-SENSITIVITY`).
- Per-fold inner-WF cross-validation.
- Synthetic-null coverage Monte-Carlo (per design.md §11.2 prereq 3;
  unit-tested at `tests/unit/test_h053_mediation.py`; production-grade
  Monte-Carlo deferred to Stage-3).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from skie_ninja.features.h053 import (
    H053Daily,
    H053Hourly,
    H053Mediator,
    H053Microstructure5_15min,
)
from skie_ninja.inference.mediation import (
    baron_kenny_nie_nde,
    e_value,
    paired_pairs_partial_r2_ci,
    pc1_collapse,
)
from skie_ninja.utils.paths import ProjectPaths

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h053_stage2")


# justify: same IS/OOS as Stage-1 per design.md §6
_IS_START = _dt.date(2015, 1, 1)
_IS_END = _dt.date(2022, 12, 31)
_OOS_START = _dt.date(2024, 1, 1)
_OOS_END_ES = _dt.date(2025, 12, 3)
_OOS_END_NQ = _dt.date(2025, 12, 19)

_STAGE2_BOOTSTRAP_BLOCK_LEN: int = 10
_STAGE2_BOOTSTRAP_NREP: int = 1000
_STAGE2_RNG_SEED: int = 42

_MEDIATOR_COLS: tuple[str, ...] = (
    "m_return", "m_log_range", "m_volume", "m_ofi_tickrule",
)


# ---------------------------------------------------------------------------
# Substrate IO + feature assembly
# ---------------------------------------------------------------------------


def _resolve_substrate_path(cli_arg: str | None) -> Path:
    if cli_arg:
        return Path(cli_arg).expanduser().resolve()
    env = os.environ.get("H053_SUBSTRATE_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return (
        ProjectPaths.discover().root
        / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    )


def _load_substrate(substrate_root: Path, symbol: str) -> pl.DataFrame:
    pattern = str(substrate_root / f"symbol={symbol}" / "year=*" / "*.parquet")
    return pl.read_parquet(pattern)


def _substrate_dataset_checksum(substrate_root: Path, symbols: list[str]) -> str:
    parts = []
    for sym in sorted(symbols):
        for path in sorted((substrate_root / f"symbol={sym}").glob("year=*/part-*.parquet")):
            with path.open("rb") as fh:
                parts.append(f"{path.relative_to(substrate_root).as_posix()}:{hashlib.sha256(fh.read()).hexdigest()}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _add_session_date_et(df: pl.DataFrame) -> pl.DataFrame:
    """Derive session_date_et from a per-session block's ts_event.

    Each H053 block anchors at a different intraday clock-time (Daily at
    T-1 RTH close 16:15 ET; Hourly at 09:31 ET; Micro+Mediator at
    09:45 ET); they cannot be joined on ts_event but they CAN be joined
    on the session_date_et that ts_event belongs to. The Daily block's
    output is anchored at T-1 16:15 ET, so its session_date_et is
    actually the date AFTER the bar's date — we shift +1 calendar day
    for Daily; the other blocks anchor on the same session_date.
    """
    return df.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.date().alias("session_date_et")
    )


def _compute_features_per_session(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute Blocks A/B/C/D features per (symbol, session) and join.

    Each block emits a per-session row but anchored at a different
    intraday clock-time (Daily T-1 16:15 ET; Hourly 09:31 ET; Micro
    + Mediator 09:45 ET). Join is done on (symbol, session_date_et).
    The Daily block's `ts_event` is T-1's RTH close, so its
    session_date_et is the bar-date PLUS 1 calendar day to align with
    the same prediction session.
    """
    target_dtype = pl.Datetime("ns", "UTC")
    panel = panel.with_columns(pl.col("ts_event").cast(target_dtype))
    now = pd.Timestamp(panel["ts_event"].max())

    _log.info("  Block A daily …")
    daily = H053Daily().compute(panel.lazy(), now=now).collect()
    # Daily anchors at T-1 RTH close; session_date_et for the prediction
    # is the next trading day. Shift +1 day; the inner-join on
    # session_date_et below will only succeed on dates that are valid
    # trading days (the other blocks have rows only on trading days).
    daily = daily.with_columns(
        pl.col("ts_event")
        .dt.convert_time_zone("America/New_York")
        .dt.date()
        .dt.offset_by("1d")
        .alias("session_date_et")
    ).drop("ts_event")

    _log.info("  Block B hourly …")
    hourly = _add_session_date_et(
        H053Hourly().compute(panel.lazy(), now=now).collect()
    ).drop("ts_event")

    _log.info("  Block C microstructure 5/15-min …")
    micro = _add_session_date_et(
        H053Microstructure5_15min().compute(panel.lazy(), now=now).collect()
    ).drop("ts_event")

    _log.info("  Block D mediator …")
    mediator = H053Mediator().compute(panel.lazy(), now=now).collect()
    # Keep mediator's ts_event for downstream alignment with predictand
    mediator = mediator.with_columns(pl.col("ts_event").cast(target_dtype))
    mediator_with_date = _add_session_date_et(mediator)

    # Join on (symbol, session_date_et) — the per-session grain.
    out = mediator_with_date
    for df, label in [(daily, "daily"), (hourly, "hourly"), (micro, "micro")]:
        before_n = len(out)
        out = out.join(df, on=["symbol", "session_date_et"], how="inner")
        _log.info("    join %s: %d → %d sessions", label, before_n, len(out))
    return out


def _compute_predictand(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute design.md §1 predictand y_{i,t} per (symbol, session)."""
    panel = panel.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.date().alias("_session_date_et"),
        pl.col("_ts_et").dt.hour().cast(pl.Int32).alias("_hour_et"),
        pl.col("_ts_et").dt.minute().cast(pl.Int32).alias("_minute_et"),
    )
    c_0945 = (
        panel.filter((pl.col("_hour_et") == 9) & (pl.col("_minute_et") == 45))
        .select(
            pl.col("symbol"),
            pl.col("_session_date_et").alias("session_date_et"),
            pl.col("ts_event").alias("ts_event"),
            pl.col("close").alias("c_0945"),
        )
    )
    c_1030 = (
        panel.filter((pl.col("_hour_et") == 10) & (pl.col("_minute_et") == 30))
        .select(
            pl.col("symbol"),
            pl.col("_session_date_et").alias("session_date_et"),
            pl.col("close").alias("c_1030"),
        )
    )
    joined = c_0945.join(c_1030, on=["symbol", "session_date_et"], how="inner")
    return joined.with_columns(
        (pl.col("c_1030") / pl.col("c_0945")).log().alias("y")
    ).filter(pl.col("y").is_finite()).select("ts_event", "symbol", "session_date_et", "y")


# ---------------------------------------------------------------------------
# Per-symbol Stage-2 runner
# ---------------------------------------------------------------------------


@dataclass
class Stage2Result:
    symbol: str
    n_train: int
    n_test: int
    n_full_features: int
    n_baseline_features: int
    partial_r2: dict[str, Any]
    pc1: dict[str, Any]
    e_value: dict[str, Any]
    mediation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_for_symbol(
    substrate_root: Path,
    symbol: str,
    oos_end: _dt.date,
) -> Stage2Result:
    _log.info("[%s] Loading substrate …", symbol)
    panel = _load_substrate(substrate_root, symbol)
    _log.info("[%s] %d rows loaded", symbol, len(panel))

    _log.info("[%s] Computing feature blocks A/B/C/D …", symbol)
    features = _compute_features_per_session(panel)
    target_dtype = pl.Datetime("ns", "UTC")
    features = features.with_columns(pl.col("ts_event").cast(target_dtype))
    _log.info("[%s] features: %d sessions × %d cols", symbol, len(features), len(features.columns))

    _log.info("[%s] Computing predictand …", symbol)
    predictand = _compute_predictand(panel).with_columns(pl.col("ts_event").cast(target_dtype))

    aligned = predictand.join(features, on=["symbol", "ts_event"], how="inner")
    _log.info("[%s] aligned (X, M, y) panel: %d sessions", symbol, len(aligned))

    # Train / test split
    train_filter = (pl.col("session_date_et") >= _IS_START) & (pl.col("session_date_et") <= _IS_END)
    test_filter = (pl.col("session_date_et") >= _OOS_START) & (pl.col("session_date_et") <= oos_end)
    train = aligned.filter(train_filter)
    test = aligned.filter(test_filter)
    _log.info("[%s] train n=%d, test n=%d", symbol, len(train), len(test))
    # justify: Stage-2 exploratory scope; Block A SMA200 + 60-day RV
    # warmup eats ~300 calendar days from IS, leaving ~150-200 train rows.
    # design.md §6 inner-WF floor of 200 is for the orchestrator's
    # walk-forward CV; for Stage-2's single-fold OLS the 100-row floor
    # is a more realistic operational cutoff.
    if len(train) < 100 or len(test) < 50:
        raise ValueError(
            f"[{symbol}] Insufficient train/test: train={len(train)}, test={len(test)}; "
            "expected train ≥ 100, test ≥ 50."
        )

    # Identify feature columns (numeric float only; exclude axis + y)
    skip = {"ts_event", "symbol", "session_date_et", "y", "c_0945", "c_1030"}
    all_feature_cols = [
        c for c in train.columns
        if c not in skip
        and not c.startswith("_")
        and not c.endswith("_right")
        and train[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
    ]
    mediator_cols = [c for c in all_feature_cols if c in _MEDIATOR_COLS]
    multitf_cols = [c for c in all_feature_cols if c not in _MEDIATOR_COLS]
    _log.info(
        "[%s] feature cols: %d total (%d mediator, %d multi-tf)",
        symbol, len(all_feature_cols), len(mediator_cols), len(multitf_cols),
    )

    # Drop rows with any non-finite feature value (warmup periods etc.)
    aligned_clean = aligned.with_columns(
        pl.fold(
            acc=pl.lit(True), function=lambda acc, x: acc & x.is_finite(),
            exprs=[pl.col(c) for c in all_feature_cols],
        ).alias("_all_finite")
    ).filter(pl.col("_all_finite")).drop("_all_finite")
    train = aligned_clean.filter(train_filter)
    test = aligned_clean.filter(test_filter)
    _log.info(
        "[%s] post-finite-filter train n=%d, test n=%d",
        symbol, len(train), len(test),
    )
    if len(train) < 100 or len(test) < 50:
        raise ValueError(
            f"[{symbol}] Post-filter sample too small: train={len(train)}, test={len(test)}; "
            "expected train ≥ 100, test ≥ 50."
        )

    # Build matrices on the test fold (paired-pairs CI computes partial-R² on test)
    X_baseline = test.select(mediator_cols).to_numpy()
    X_full = test.select(all_feature_cols).to_numpy()
    y_test = test["y"].to_numpy()

    _log.info("[%s] Computing partial-R² + paired-pairs CI on OOS test fold …", symbol)
    rng = np.random.default_rng(_STAGE2_RNG_SEED)
    pr2_ci = paired_pairs_partial_r2_ci(
        X_baseline, X_full, y_test,
        n_replicates=_STAGE2_BOOTSTRAP_NREP, block_length=_STAGE2_BOOTSTRAP_BLOCK_LEN,
        rng=rng,
    )
    _log.info(
        "[%s] partial-R² point=%.4f, CI=[%.4f, %.4f] excludes_zero=%s",
        symbol, pr2_ci.point_estimate, pr2_ci.ci_lo, pr2_ci.ci_hi, pr2_ci.excludes_zero,
    )

    # PC1 collapse on the train mediator block
    M_train = train.select(mediator_cols).to_numpy()
    pc1_result, _ = pc1_collapse(M_train)
    _log.info(
        "[%s] PC1 mediator: variance_explained=%.4f, loadings=%s",
        symbol, pc1_result.variance_explained,
        [f"{v:.3f}" for v in pc1_result.loadings],
    )

    # E-value sensitivity
    ev_result = e_value(pr2_ci.point_estimate, pr2_ci.ci_lo, pr2_ci.ci_hi)
    _log.info(
        "[%s] E-value point=%.4f, CI-bound=%.4f",
        symbol, ev_result.e_value_point, ev_result.e_value_ci_bound,
    )

    # Descriptive Baron-Kenny mediation
    _log.info("[%s] Computing descriptive Baron-Kenny NIE/NDE …", symbol)
    rng2 = np.random.default_rng(_STAGE2_RNG_SEED + 1)
    M_test = test.select(mediator_cols).to_numpy()
    X_test = test.select(multitf_cols).to_numpy()
    mediation = baron_kenny_nie_nde(
        y_test, M_test, X_test,
        n_replicates=_STAGE2_BOOTSTRAP_NREP, block_length=_STAGE2_BOOTSTRAP_BLOCK_LEN,
        rng=rng2,
    )
    _log.info(
        "[%s] NIE=%.4e CI=[%.4e, %.4e], NDE=%.4e CI=[%.4e, %.4e], NIE_excludes_zero=%s",
        symbol, mediation.nie, mediation.nie_ci_lo, mediation.nie_ci_hi,
        mediation.nde, mediation.nde_ci_lo, mediation.nde_ci_hi,
        mediation.nie_excludes_zero,
    )

    return Stage2Result(
        symbol=symbol,
        n_train=len(train),
        n_test=len(test),
        n_full_features=len(all_feature_cols),
        n_baseline_features=len(mediator_cols),
        partial_r2=pr2_ci.to_dict(),
        pc1=pc1_result.to_dict(),
        e_value=ev_result.to_dict(),
        mediation=mediation.to_dict(),
    )


# ---------------------------------------------------------------------------
# Sidecar
# ---------------------------------------------------------------------------


def _git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ProjectPaths.discover().root,
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode("ascii").strip()
    except Exception:
        return None


def _write_sidecar(
    results: list[Stage2Result],
    out_path: Path,
    substrate_path: str,
    substrate_checksum: str,
    git_head: str | None,
    run_id: str,
) -> tuple[Path, str, str]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scientific_payload = {
        "version": "1.0",
        "method": (
            "H053 Stage-2 multi-timeframe + descriptive mediation: partial-R² "
            "of (Blocks A+B+C+D) over (Block D) on OOS test fold via paired-pairs "
            "stationary-bootstrap; PC1 mediator collapse; E-value sensitivity; "
            "descriptive Baron-Kenny NIE/NDE"
        ),
        "method_reference": (
            "design.md §1 (descriptive interpretive note), §3, §4, §5.4, §6, §10.2; "
            "VanderWeele 2015 (OUP, ISBN 978-0199325870) §1.4 + Ch. 2; "
            "VanderWeele-Ding 2017 doi:10.7326/M16-2607; "
            "Imai-Keele-Tingley 2010 doi:10.1037/a0020761; "
            "MacKinnon-Lockwood-Williams 2004 doi:10.1207/s15327906mbr3901_4; "
            "Politis-Romano 1994 (paired-pairs bootstrap)"
        ),
        "substrate_path": substrate_path,
        "substrate_dataset_checksum": substrate_checksum,
        "is_window": [_IS_START.isoformat(), _IS_END.isoformat()],
        "oos_window": [_OOS_START.isoformat(), f"per-instrument: ES={_OOS_END_ES.isoformat()}, NQ={_OOS_END_NQ.isoformat()}"],
        "stage2_bootstrap_block_len": _STAGE2_BOOTSTRAP_BLOCK_LEN,
        "stage2_bootstrap_n_rep": _STAGE2_BOOTSTRAP_NREP,
        "stage2_rng_seed": _STAGE2_RNG_SEED,
        "results": [r.to_dict() for r in results],
    }
    scientific_bytes = json.dumps(scientific_payload, indent=2, sort_keys=True).encode("utf-8")
    scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
    payload = {
        "h053_stage2_multitf_mediation": scientific_payload,
        "_meta": {
            "written_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "run_id": run_id,
            "git_head": git_head,
            "scientific_payload_sha256": scientific_sha,
        },
    }
    serialised = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    tmp = out_path.with_suffix(".json.tmp")
    with tmp.open("wb") as fh:
        fh.write(serialised)
    os.replace(tmp, out_path)
    return out_path, hashlib.sha256(serialised).hexdigest(), scientific_sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="H053 Cycle 9 Stage-2 — multi-timeframe + mediation."
    )
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--symbols", default="ES,NQ")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)

    substrate_root = _resolve_substrate_path(args.substrate_path)
    if not substrate_root.exists():
        raise FileNotFoundError(f"Substrate path {substrate_root} does not exist.")
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    paths = ProjectPaths.discover()
    run_id = args.run_id or f"h053_stage2_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir = paths.root / "runs" / "h053" / "stage2" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    _log.info("Computing substrate dataset checksum …")
    substrate_checksum = _substrate_dataset_checksum(substrate_root, symbols)
    git_head = _git_head()
    _log.info("substrate_dataset_checksum=%s, git_head=%s", substrate_checksum, git_head)

    results: list[Stage2Result] = []
    for sym in symbols:
        oos_end = _OOS_END_ES if sym == "ES" else _OOS_END_NQ
        try:
            r = _run_for_symbol(substrate_root, sym, oos_end)
            results.append(r)
        except Exception as exc:
            _log.exception("Symbol %s failed: %s", sym, exc)
            raise

    sidecar_path, file_sha, scientific_sha = _write_sidecar(
        results, run_dir / "sidecar.json",
        str(substrate_root), substrate_checksum, git_head, run_id,
    )
    _log.info("Sidecar: %s", sidecar_path)
    _log.info("Scientific-payload SHA256: %s", scientific_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
