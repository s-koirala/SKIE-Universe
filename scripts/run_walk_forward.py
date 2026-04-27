"""Walk-forward orchestrator for a pre-registered hypothesis.

Usage::

    python scripts/run_walk_forward.py \
        --hypothesis H050 \
        --config config/hypotheses/H050.yaml \
        [--dry-run] [--smoke-n 5000] [--smoke]

Pipeline (per Cycle-6 brief)
----------------------------

  1. Open :class:`~skie_ninja.utils.runcontext.RunContext`.
  2. Load panel (real data OR synthetic on ``--dry-run``).
  3. Compute features via :data:`FEATURE_REGISTRY` enumeration.
  4. Triple-barrier labels (López de Prado 2018 AFML §3.4 "The
     Triple-Barrier Method"; design.md §4 cites §3.2 — that misattribution
     is an inherited erratum from design.md line 53, preserved by Path-A
     pre-reg immutability and documented in the orchestrator-triple
     audit trail) — joint CV selection over the 27-cell
     pre-registered grid (``pt_sl × vertical_barrier × volatility_lookback``)
     per design.md §4 INSIDE each outer fold. Selection metric: the
     ungated mean inner-OOS Sharpe of the inner-CV-selected
     classifier under each candidate label config. The label-grid
     selection metric is intentionally DECOUPLED from the gated
     production metric ``T_H050 = SR_gated − SR_unconditional``
     (design.md §1): labels optimise classifier signal quality, while
     the regime gate is a separate inference-time conditioning
     component (AFML §3.4 "labels are downstream of the trading rule's
     P&L, not of any inference-time gate"). An empirical sensitivity
     study (gated vs ungated label-CV) is tracked under follow-up
     ``P1-H050-LABEL-CV-GATED-METRIC``. Ties on the Sharpe metric are
     broken by the smallest mean inner-CV log-loss to make selection
     deterministic. (P1-H050-LABEL-CV closure.)
  5. Build :class:`~skie_ninja.backtest.splits.SplitSpec` with purge
     >= ``max_label_horizon``, data-driven embargo
     (Politis-White 2004 auto block-length).
  6. Per OUTER fold: nested walk-forward inner CV
     (Varma & Simon 2006, doi:10.1186/1471-2105-7-91) selects
     LightGBM hyperparameters by mean inner-OOS log-loss
     (the training objective); 200 random-search draws by default
     (Bergstra & Bengio 2012, JMLR 13:281-305) with `--smoke`
     reducing to 5 for CI. HMM BIC selection inside the same outer
     train block. ``predict_fn`` gates classifier probability by
     warm-started ``filter_states`` regime indicator.
     P1-H050-INNER-CV closure.
  7. :class:`~skie_ninja.backtest.engine.walk_forward.WalkForwardEngine`
     executes the run PER SYMBOL declared in
     ``config.universe`` (H050.yaml line 3 = ``[ES, NQ]``).
     P1-H050-UNIVERSE-ES-ONLY closure. Per-symbol artifacts;
     cross-symbol aggregation is deferred to
     ``P1-H050-DUAL-SYMBOL-ORCHESTRATOR``.
  8. OOS PnL, Sharpe of gated vs unconditional filtered series.
  9. Opdyke 2007 CI on the Sharpe differential via stationary
     bootstrap.
 10. Hansen SPA (strategy universe = {H050} for Cycle-6).
 11. Persist artifacts under ``artifacts/runs/H050/{run_id}/{symbol}/``.
 12. :func:`with_model_hash` the ReproLog from the engine rolled-up
     hash.

Dry-run mode generates a synthetic OHLCV panel. The feature factory,
labels, splitter, engine, bootstrap, and SPA are executed on the
synthetic data so the full composition is exercised end-to-end.

The ``--smoke`` flag reduces ``lgb_n_draws`` and the inner-CV fold
count for CI tractability. Smoke values are CI-only overrides; the
production walk-forward run uses the H050.yaml-bound
``classifier.search.n_draws = 200`` per design.md §5.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import logging
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Progress logging (P1-ORCHESTRATOR-PROGRESS-LOGGING)
# ---------------------------------------------------------------------------
#
# Background. The 2026-04-26 production H050 walk-forward run-1 was
# killed at +180 min with zero per-fold or aggregate artifacts written
# and 0 bytes of stdout flushed; diagnosing the bottleneck required an
# external py-spy dump (see
# docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md).
# This helper emits matched start/done INFO markers around the
# orchestrator's load-bearing phases so a future multi-hour run is
# observable from the JSON log stream alone.
#
# Stdout buffering. ``setup_logging()`` reconfigures stdout to
# ``line_buffering=True`` (Round-2 audit-remediate Q-1-3 / R-3) so
# each JSON record reaches the consumer immediately even in non-TTY
# headless runs. The canonical headless invocation is therefore:
#     OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
#         uv run python scripts/run_walk_forward.py ...
# ``python -u`` remains an optional belt-and-braces if the script is
# invoked outside the ``__main__`` block (skipping ``setup_logging``).
class _ProgressLog:
    """INFO-level structured progress logger for the walk-forward
    orchestrator.

    Public message contract:
      ``"PROGRESS <phase> start | <kv-context>"``
      ``"PROGRESS <phase> done elapsed=<s>s | <kv-context>"``  (clean exit)
      ``"PROGRESS <phase> failed elapsed=<s>s exc=<type> | <kv-context>"``  (exception)

    Phases are short string names (``"run"``, ``"symbol"``,
    ``"label-cfg"``, ``"label-cfg-loop-step"``, ``"fold-fit"``,
    ``"hmm-fit"``, ``"inner-cv-lgb"``).

    Coverage by phase:
      - ``fold-fit``, ``hmm-fit``, ``inner-cv-lgb``,
        ``label-cfg-loop-step`` — wrapped in :meth:`phase` context
        manager (auto-emits ``failed`` on exception).
      - ``run``, ``symbol``, ``label-cfg`` — wrapped in explicit
        ``try/except`` at function entry (semantically identical to
        the context manager; uses raw :meth:`start` / :meth:`failed`
        because the function bodies were too large to refactor into
        a single :meth:`phase` block without massive indentation).

    Both patterns emit ``failed`` on any caught exception so a hung
    process and a crashed process are distinguishable in the log
    stream (Round-1 audit-remediate finding Q-1-1). ``KeyboardInterrupt``
    and ``SystemExit`` propagate without producing a ``failed`` marker
    (Round-2 audit-remediate finding Q-2-3).
    """

    def __init__(self, log: logging.Logger) -> None:
        self._log = log
        self._t0: dict[str, float] = {}

    def start(self, phase: str, **ctx: Any) -> None:
        self._t0[phase] = time.perf_counter()
        self._log.info("PROGRESS %s start | %s", phase, _kv(ctx))

    def done(self, phase: str, **ctx: Any) -> float:
        t0 = self._t0.pop(phase, time.perf_counter())
        elapsed = time.perf_counter() - t0
        self._log.info(
            "PROGRESS %s done elapsed=%.3fs | %s", phase, elapsed, _kv(ctx)
        )
        return elapsed

    def failed(self, phase: str, exc_type: str, **ctx: Any) -> float:
        t0 = self._t0.pop(phase, time.perf_counter())
        elapsed = time.perf_counter() - t0
        self._log.info(
            "PROGRESS %s failed elapsed=%.3fs exc=%s | %s",
            phase,
            elapsed,
            exc_type,
            _kv(ctx),
        )
        return elapsed

    @contextmanager
    def phase(self, phase: str, **start_ctx: Any) -> Iterator[dict[str, Any]]:
        """Context-managed phase: emits start on enter, done on clean
        exit, failed on exception. Always pops the phase t0 so the
        module-singleton _t0 dict cannot leak orphan entries (Round-1
        audit-remediate finding Q-1-2).

        Yields a mutable ``done_ctx`` dict; callers can append
        exit-time fields (e.g. ``ctx["n_folds"] = N``) before the
        block exits. On clean exit those fields are merged with the
        start kwargs and emitted in the done line; on exception the
        merged ctx is emitted in the failed line.
        """
        self.start(phase, **start_ctx)
        done_ctx: dict[str, Any] = {}
        try:
            yield done_ctx
        except Exception as exc:  # KeyboardInterrupt/SystemExit propagate (Q-2-3)
            merged = {**start_ctx, **done_ctx}
            self.failed(phase, exc_type=type(exc).__name__, **merged)
            raise
        else:
            merged = {**start_ctx, **done_ctx}
            self.done(phase, **merged)


def _kv(ctx: dict[str, Any]) -> str:
    """Render a kv-context dict as a whitespace-delimited key=value
    string. Values containing whitespace are JSON-encoded (Round-1
    audit-remediate finding Q-1-4) so a downstream `key=value`
    parser can round-trip them.
    """
    out: list[str] = []
    for k, v in ctx.items():
        s = str(v)
        if any(ch.isspace() for ch in s):
            s = json.dumps(s)
        out.append(f"{k}={s}")
    return " ".join(out)


_PROGRESS = _ProgressLog(_LOG)

# Minimum OOS return observations required to compute Sharpe CI and SPA.
# 30 is a conservative lower bound: Lo 2002 iid Sharpe CLT requires n → ∞;
# Opdyke 2007 HAC-corrected CI retains O(1/√n) error; below 30 the CI is
# too wide to be informative (residual bias O(1/√30) ≈ 18%). Not an
# arbitrary threshold — reflects the effective-sample-size floor at which
# the estimator's asymptotic approximation is defensible.
_MIN_OOS_FOR_CI: int = 30

import numpy as np
import pandas as pd
import polars as pl
import yaml

from skie_ninja.backtest.costs.nt8_es_nq_rth_v1 import NT8EsNqRthV1CostModel
from skie_ninja.backtest.engine.walk_forward import (
    WalkForwardEngine,
    ledger_path_for,
    roll_up_model_hashes,
    write_run_ledger,
)
from skie_ninja.backtest.splits import walk_forward_split
from skie_ninja.features import FEATURE_REGISTRY
from skie_ninja.features.assembly import assemble_feature_matrix
from skie_ninja.features.labels import (
    TripleBarrierConfig,
    TripleBarrierLabeler,
)
from skie_ninja.inference import choose_block_length, hansen_spa_test
from skie_ninja.inference.stats import opdyke2007_ci, sample_sharpe
from skie_ninja.models.regime import (
    GaussianHMM,
    WarmColdDiagnostic,
    select_gaussian_hmm,
    warm_cold_sidecar_path_for,
    write_warm_cold_sidecar,
)
from skie_ninja.utils.hashing import frame_sha256
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.reproducibility import with_model_hash
from skie_ninja.utils.runcontext import RunContext

# ---------------------------------------------------------------------------
# HMM-fit cache (P1-H050-SMOKE-RUNTIME-INVESTIGATE)
# ---------------------------------------------------------------------------
#
# Across the 27-cell label grid, the HMM input is the train-fold
# log-return series ``r_tr = r[train_idx]``. ``r`` is symbol-specific
# and CFG-INDEPENDENT (closes are not perturbed by label parameters);
# ``train_idx`` is fold-deterministic (engine drives outer-fold
# geometry from per-cfg ``label_horizon`` — see ``_run_symbol_label_cfg``
# Round-2 §F-2 fix). Therefore HMM input is a function of
# ``(symbol, fold_id, label_horizon)``. The cache key is exactly
# ``(symbol, fold_id, label_horizon)``: cfgs sharing a vertical_barrier
# (and hence a label_horizon) share the same outer-fold geometry and
# share HMM fits; cfgs with diverging vertical_barriers get separate
# cache entries (no collision). For the H050 27-cell grid this yields
# 3 vertical_barrier strata × N folds = 3N HMM fits (rather than 27N
# without cache or 1N with the unsafe key-collision form). The cache
# invariant (``train_idx_len`` + first/last position) is preserved as a
# defensive backstop against future refactors that decouple
# label_horizon from fold geometry; under the current splitter contract
# (purge_window = label_horizon, AFML §7.4) it never fires in normal
# operation, only on programmer error.


@dataclass(frozen=True)
class _CachedHmmFit:
    """Frozen record of one HMM fit, keyed on
    ``(symbol, fold_id, label_horizon)``.

    Carries every artifact the cache-hit path of :func:`_fit_fold`
    needs to skip ``select_gaussian_hmm`` and emit the same return
    dict as a cache miss. The fields are deliberately one-to-one with
    the keys consumed by ``_predict_fold`` (``hmm``, ``regime_high_mean``,
    ``hmm_terminal_log_alpha``, ``hmm_train_terminal_position``); plus
    cache-invariant guards (``train_idx_len`` + first/last positions)
    that defend against fold geometries diverging across cfgs.
    """

    hmm: GaussianHMM
    regime_high_mean: int
    hmm_terminal_log_alpha: np.ndarray
    hmm_train_terminal_position: int
    train_idx_len: int
    train_idx_first: int
    train_idx_last: int


@dataclass
class _HmmCacheStats:
    """Operational telemetry; not a methodological artifact.

    Reported at end-of-run only. Counts and timings are reset per
    :func:`_run_symbol` invocation (cache itself is per-symbol). The
    cache toggle ``--no-hmm-cache`` simply disables population /
    lookup; statistics are still tracked so the disabled-path baseline
    can be measured against the enabled-path speedup.
    """

    n_hits: int = 0
    n_misses: int = 0
    total_hmm_fit_time_s: float = 0.0
    total_cache_lookup_time_s: float = 0.0
    unique_keys: set[tuple[str, int, int]] = field(default_factory=set)

    @property
    def n_unique_keys(self) -> int:
        return len(self.unique_keys)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_hits": int(self.n_hits),
            "n_misses": int(self.n_misses),
            "n_unique_keys": int(self.n_unique_keys),
            "total_hmm_fit_time_s": float(self.total_hmm_fit_time_s),
            "total_cache_lookup_time_s": float(self.total_cache_lookup_time_s),
        }


def _validate_cache_invariant(
    cached: _CachedHmmFit,
    train_idx: np.ndarray,
    *,
    symbol: str,
    fold_id: int,
    label_horizon: int,
) -> None:
    """Raise if a cache key collides with a different fold geometry.

    Under the current splitter contract (``purge_window =
    label_horizon`` per AFML §7.4) the cache key
    ``(symbol, fold_id, label_horizon)`` already partitions divergent
    fold geometries into disjoint cache entries; this invariant is
    therefore expected to never fire in normal operation. It is kept as
    a defensive backstop against future refactors that decouple
    ``purge_window`` from ``label_horizon`` (e.g. an embargo-mode ADR
    promotes a separate purge knob), in which case two cfgs sharing
    ``(symbol, fold_id, label_horizon)`` could still produce different
    ``train_idx`` and silently reusing the cache would be a correctness
    violation. We raise so the caller treats the collision as a
    programmer error (e.g. fold-id + horizon sharing across two engines
    with different additional geometry levers) rather than a silent
    recompute path.
    """
    if (
        cached.train_idx_len != int(len(train_idx))
        or cached.train_idx_first != int(train_idx[0])
        or cached.train_idx_last != int(train_idx[-1])
    ):
        raise RuntimeError(
            "HMM cache invariant violated for "
            f"(symbol={symbol!r}, fold_id={fold_id}, "
            f"label_horizon={label_horizon}): cached "
            f"(train_idx_len={cached.train_idx_len}, "
            f"first={cached.train_idx_first}, "
            f"last={cached.train_idx_last}) vs requested "
            f"(len={len(train_idx)}, first={int(train_idx[0])}, "
            f"last={int(train_idx[-1])}). Two engines with different "
            "fold geometry collided on the same cache key. The cache "
            "must be reset between engine runs whose splitter "
            "geometry diverges beyond label_horizon."
        )


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunConfig:
    hypothesis_id: str
    random_seed: int
    feature_keys: tuple[str, ...]
    pt_sl_grid: tuple[float, ...]
    vertical_barrier_grid: tuple[pd.Timedelta, ...]
    volatility_lookback_grid: tuple[int, ...]
    lgb_grid: dict[str, tuple[Any, ...]]
    lgb_n_draws: int
    lgb_seed: int
    hmm_cov_types: tuple[str, ...]
    spa_n_bootstrap: int
    spa_omega_method: str  # ADR-0008: "hac" for M=1, "bootstrap" for M≥2
    cost_model_id: str
    cost_sensitivity_mult: float
    gate_alpha: float
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    val_start: pd.Timestamp
    val_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    config_resolved_sha256: str
    raw: dict[str, Any]


def _parse_vb(item: str) -> pd.Timedelta:
    # Accepts tokens like "30m", "60m", "2h".
    return pd.Timedelta(item)


def _parse_window(window: dict[str, Any]) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Parse a {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'} block into a
    (start, end_inclusive) UTC-aware Timestamp pair.

    The end date in H050.yaml is interpreted as the last calendar day
    INCLUSIVE; converting it to ``end + 1d - 1ns`` UTC keeps the upper
    bound on the same calendar day under intraday timestamps. This matches
    the pre-registration's calendar-day semantics (H050 design.md §1)
    rather than midnight-exclusive semantics.
    """
    start = pd.Timestamp(window["start"], tz="UTC")
    end_day = pd.Timestamp(window["end"], tz="UTC")
    end_inclusive = end_day + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    return start, end_inclusive


def load_config(path: Path) -> RunConfig:
    # Read raw bytes first so we can hash the YAML content into ReproLog.
    # Decoupling sha256 from yaml.safe_load round-trip protects against
    # parser-level normalisation (e.g. quote-style changes) silently
    # changing the hash. Reproducibility audit relies on the byte hash
    # of the source file, not the parsed AST.
    import hashlib as _hashlib

    raw_bytes = Path(path).read_bytes()
    config_sha = _hashlib.sha256(raw_bytes).hexdigest()
    raw = yaml.safe_load(raw_bytes)
    train_start, train_end = _parse_window(raw["data"]["train"])
    val_start, val_end = _parse_window(raw["data"]["val"])
    test_start, test_end = _parse_window(raw["data"]["test"])
    return RunConfig(
        hypothesis_id=str(raw["hypothesis_id"]),
        random_seed=int(raw["random_seed"]),
        feature_keys=tuple(raw["features"]),
        pt_sl_grid=tuple(float(x) for x in raw["labels"]["pt_sl_grid"]),
        vertical_barrier_grid=tuple(_parse_vb(x) for x in raw["labels"]["vertical_barrier_grid"]),
        volatility_lookback_grid=tuple(int(x) for x in raw["labels"]["volatility_lookback_grid"]),
        lgb_grid={k: tuple(v) for k, v in raw["classifier"]["grid"].items()},
        lgb_n_draws=int(raw["classifier"]["search"]["n_draws"]),
        lgb_seed=int(raw["classifier"]["search"]["seed"]),
        hmm_cov_types=tuple(raw["hmm"]["covariance_type"]),
        spa_n_bootstrap=int(raw["gates"]["hansen_spa"]["n_bootstrap"]),
        spa_omega_method=str(raw["gates"]["hansen_spa"].get("omega_method", "bootstrap")),
        cost_model_id=str(raw.get("cost_model", "nt8_es_nq_rth_v1")),
        cost_sensitivity_mult=float(raw.get("cost_sensitivity_mult", 1.0)),
        gate_alpha=float(raw["gates"]["opdyke2007_ci"]["alpha"]),
        train_start=train_start,
        train_end=train_end,
        val_start=val_start,
        val_end=val_end,
        test_start=test_start,
        test_end=test_end,
        config_resolved_sha256=config_sha,
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Synthetic panel (dry-run)
# ---------------------------------------------------------------------------


def make_synthetic_panel(*, n_per_symbol: int, seed: int) -> pl.DataFrame:
    """Generate an OHLCV panel with two symbols matching the
    roll-adjusted schema.

    The generator draws close-to-close log-returns from a
    regime-switching Gaussian mixture (two states) so the
    downstream HMM selection sees meaningful state structure; the
    per-bar high/low are set by adding exponential wings to the
    ``max(open, close)`` and ``min(open, close)``. This is enough
    substrate for the orchestrator to exercise end-to-end.
    """
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2023-01-02 09:30", periods=n_per_symbol, freq="1min", tz="UTC")

    def one_symbol(sym: str) -> pl.DataFrame:
        # Markov-ish two-state regime for returns (low-vol, high-vol).
        state = np.zeros(n_per_symbol, dtype=np.int64)
        p_switch = 0.002
        for i in range(1, n_per_symbol):
            if rng.random() < p_switch:
                state[i] = 1 - state[i - 1]
            else:
                state[i] = state[i - 1]
        sig_low = 0.0005
        sig_high = 0.0020
        drift_low = 0.00002
        drift_high = -0.00005
        drift = np.where(state == 0, drift_low, drift_high)
        sigma = np.where(state == 0, sig_low, sig_high)
        r = rng.normal(loc=drift, scale=sigma)
        close_init = 100.0 if sym == "ES" else 200.0
        close = close_init * np.exp(np.cumsum(r))
        open_ = np.concatenate([[close_init], close[:-1]])
        wing = np.abs(rng.normal(scale=sigma * 0.5, size=n_per_symbol))
        high = np.maximum(open_, close) * (1.0 + wing)
        low = np.minimum(open_, close) * (1.0 - wing)
        volume = rng.integers(100, 1000, size=n_per_symbol).astype(np.int64)
        return pl.DataFrame(
            {
                "ts_event": ts,
                "symbol": [sym] * n_per_symbol,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )

    return pl.concat([one_symbol("ES"), one_symbol("NQ")], how="vertical")


# ---------------------------------------------------------------------------
# Fit / predict functions (nested CV inside fold)
# ---------------------------------------------------------------------------

# Default inner-walk-forward fold count for nested CV (Varma & Simon 2006,
# doi:10.1186/1471-2105-7-91). Choice rationale (López de Prado 2018 AFML §7):
# 3 inner folds balances per-draw compute against per-fold variance for an
# outer train block of ~9 calendar years of 1-min bars. With 3 inner folds
# and step_size = test_size, each inner fold sees ~25% of the outer-train
# block as inner-test — large enough that the inner-OOS log-loss estimator
# has acceptable variance, small enough that 27 (label grid) × N_draws
# inner-CV evaluations per outer fold remain tractable.
_DEFAULT_INNER_N_FOLDS: int = 3
# Smoke override: 2 inner folds for CI tractability. Documented as
# CI-only; production runs use _DEFAULT_INNER_N_FOLDS.
_SMOKE_INNER_N_FOLDS: int = 2
# Smoke override for N_draws. The production setting is bound by
# H050.yaml `classifier.search.n_draws = 200` per design.md §5.
# Bergstra & Bengio 2012 (JMLR 13:281-305) §2.2 derives the volume
# argument: N i.i.d. uniform draws from the search space miss a region
# of relative volume v with probability (1 − v)^N, so N ≥ ceil(log(1−p)/
# log(1−v)) draws cover a v-volume "good" region with probability ≥ p.
# For (v=0.05, p=0.95) the threshold is N ≥ 59 (the canonical "60-trial"
# B&B result). The argument is dimension-INDEPENDENT (it is a statement
# about volume measure on the search space, not on its intrinsic
# dimensionality). The H050 LightGBM grid is a 12-cell discrete product
# (3 × 2 × 2 = num_leaves × learning_rate × min_data_in_leaf — see
# H050.yaml `classifier.grid`); N=200 over 12 cells is heavy
# oversampling rather than a B&B-dictated coverage requirement. The
# N=200 binding from H050.yaml `classifier.search.n_draws` predates the
# discrete-grid analysis and is preserved here under pre-reg fidelity;
# an empirical N_draws calibration on the actual 12-cell discrete grid
# is tracked under follow-up `P1-H050-LGB-N-DRAWS-EMPIRICAL`.
# Smoke uses 5 to keep the CI fixture tractable; this value is NOT a
# production setting.
_SMOKE_LGB_N_DRAWS: int = 5
# Smoke override for the label grid: take only the center cell so smoke
# exercises the joint-CV plumbing without paying the 27-cell cost.
# Production walk-forward uses the full 27-cell grid per design.md §4.
_SMOKE_LABEL_GRID_LIMIT: int = 1


def _build_inner_folds(
    n_train_outer: int,
    *,
    label_horizon: int,
    embargo: int,
    n_inner_folds: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Build an inner walk-forward CV split inside one outer training block.

    Returns a list of ``(inner_train_local_idx, inner_test_local_idx)``
    tuples where indices are LOCAL positions into the outer train block
    (``0..n_train_outer-1``). The caller adds the outer block's offset to
    map back into the global panel.

    The inner split honours the same purge/embargo discipline as the
    outer engine (López de Prado 2018 AFML §7.4); we delegate to
    :func:`walk_forward_split` with ``mode="rolling"`` and
    ``step_size = inner_test_size`` so inner test blocks are disjoint.
    """
    if n_train_outer < 4 * n_inner_folds:
        # Too few rows to build n_inner_folds disjoint test blocks plus a
        # non-degenerate initial training block. Caller should treat this
        # as "single inner fold = full train" — handled at call site.
        return []
    inner_test_size = max(2, n_train_outer // (n_inner_folds + 2))
    inner_initial = max(inner_test_size, n_train_outer - n_inner_folds * inner_test_size)
    if inner_initial + inner_test_size > n_train_outer:
        return []
    inner_split = walk_forward_split(
        n_samples=n_train_outer,
        initial_train_size=inner_initial,
        test_size=inner_test_size,
        step_size=inner_test_size,
        label_horizon=label_horizon,
        embargo=embargo,
        mode="rolling",
        purge_window=label_horizon,
        max_folds=n_inner_folds,
    )
    return [
        (
            np.asarray(f.train_indices(), dtype=np.int64),
            np.asarray(f.test_indices(), dtype=np.int64),
        )
        for f in inner_split.folds
    ]


def _logistic_loss_safe(y_true: np.ndarray, p_pred: np.ndarray, eps: float = 1e-15) -> float:
    """Mean cross-entropy between Bernoulli targets and predicted prob.

    Standard scikit-learn `log_loss` formulation; eps clipping prevents
    `log(0)` blow-ups when the classifier saturates (probability
    arbitrarily close to 0 or 1). Lower is better.
    """
    p_clipped = np.clip(p_pred, eps, 1.0 - eps)
    return float(-np.mean(y_true * np.log(p_clipped) + (1.0 - y_true) * np.log(1.0 - p_clipped)))


def _strategy_sharpe_simple(p_pred: np.ndarray, r_te: np.ndarray) -> float:
    """Cost-free directional Sharpe of position = sign(2p − 1) on r_te.

    Used for label-grid selection within the inner CV: the labels and
    HP are jointly chosen by the downstream Sharpe of the candidate
    classifier on inner-OOS bars. Cost deduction is intentionally
    omitted at the inner-CV level — the production cost model
    (`nt8_es_nq_rth_v1`) is applied at the outer-fold OOS evaluation
    only, so the label-grid selection criterion is the cost-free signal
    quality. Sample-size guard: insufficient variance in the strategy
    return → -inf so this config loses any tie-break.
    """
    pos = np.sign(2.0 * p_pred - 1.0)
    s = pos * r_te
    if s.size < 2 or s.std() <= 0:  # noqa: PLR2004
        return -np.inf
    return float(s.mean() / s.std())


def _draw_random_lgb_params(
    rng: np.random.Generator,
    grid: dict[str, tuple[Any, ...]],
    n_draws: int,
) -> list[dict[str, Any]]:
    """Sample distinct random LightGBM hyperparameter configurations.

    Bergstra & Bengio 2012 (JMLR 13:281-305) — random search; with
    n_draws bounded above by the grid's combinatorial size, sampling
    without replacement is equivalent to a permutation of the full grid.
    Above that cap, we sample with replacement (the design intent of
    random search is breadth over the surface, not coverage of every
    cell).
    """
    keys = list(grid.keys())
    n_combos = 1
    for vals in grid.values():
        n_combos *= max(1, len(vals))
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for _ in range(n_draws):
        # Try unique sampling first; if exhausted, fall through to with-replacement.
        for _retry in range(20):
            params = {k: rng.choice(list(grid[k])) for k in keys}
            sig = tuple(params[k] for k in keys)
            if sig not in seen or len(seen) >= n_combos:
                break
        seen.add(sig)
        # Cast to Python scalars (lightgbm refuses numpy dtypes here).
        params_cast = {
            k: (int(v) if isinstance(v, np.integer) else float(v)) for k, v in params.items()
        }
        out.append(params_cast)
    return out


def _inner_cv_select_hp(
    *,
    X_train_outer: np.ndarray,
    y_train_outer: np.ndarray,
    r_train_outer: np.ndarray,
    lgb_grid: dict[str, tuple[Any, ...]],
    lgb_n_draws: int,
    lgb_seed: int,
    random_seed: int,
    label_horizon: int,
    embargo: int,
    n_inner_folds: int,
) -> tuple[dict[str, Any] | None, float, float]:
    """Inner walk-forward CV over LightGBM HP draws.

    Returns ``(best_params, best_inner_logloss, best_inner_sharpe)``.

    Per Varma & Simon 2006 (doi:10.1186/1471-2105-7-91), model
    selection is performed STRICTLY on inner-OOS folds — never on the
    inner-training data. The selection metric is mean inner-OOS
    logistic loss (matches the LightGBM training objective per
    design.md §5). The inner-OOS Sharpe is also returned so the
    caller can use it for label-grid selection (P1-H050-LABEL-CV).
    """
    import lightgbm as lgb

    inner_folds = _build_inner_folds(
        n_train_outer=X_train_outer.shape[0],
        label_horizon=label_horizon,
        embargo=embargo,
        n_inner_folds=n_inner_folds,
    )
    if not inner_folds:
        return None, np.inf, -np.inf

    rng = np.random.default_rng(lgb_seed)
    draws = _draw_random_lgb_params(rng, lgb_grid, lgb_n_draws)

    best_params: dict[str, Any] | None = None
    best_logloss = np.inf
    best_sharpe = -np.inf
    for params in draws:
        fold_loglosses: list[float] = []
        fold_sharpes: list[float] = []
        for inner_tr, inner_te in inner_folds:
            X_in_tr = X_train_outer[inner_tr]
            y_in_tr = y_train_outer[inner_tr]
            X_in_te = X_train_outer[inner_te]
            y_in_te = y_train_outer[inner_te]
            r_in_te = r_train_outer[inner_te]
            if len(np.unique(y_in_tr)) < 2 or len(np.unique(y_in_te)) < 2:  # noqa: PLR2004
                continue
            model = lgb.LGBMClassifier(
                n_estimators=50,
                random_state=int(random_seed),
                verbose=-1,
                **params,
            )
            model.fit(X_in_tr, y_in_tr)
            if hasattr(model, "predict_proba"):
                p_te = model.predict_proba(X_in_te)[:, 1]
            else:
                p_te = model.predict(X_in_te).astype(float)
            fold_loglosses.append(_logistic_loss_safe(y_in_te, p_te))
            fold_sharpes.append(_strategy_sharpe_simple(p_te, r_in_te))
        if not fold_loglosses:
            continue
        mean_logloss = float(np.mean(fold_loglosses))
        finite_sharpes = [s for s in fold_sharpes if np.isfinite(s)]
        mean_sharpe = float(np.mean(finite_sharpes)) if finite_sharpes else -np.inf
        if mean_logloss < best_logloss:
            best_logloss = mean_logloss
            best_sharpe = mean_sharpe
            best_params = params

    return best_params, best_logloss, best_sharpe


def _label_panel_for_cfg(
    panel_for_symbol: pl.DataFrame,
    feature_matrix: pl.DataFrame,
    *,
    pt_sl: float,
    vertical_barrier: pd.Timedelta,
    volatility_lookback: int,
    feature_keys: tuple[str, ...],
    train_start_ts: pd.Timestamp | None,
    test_end_ts: pd.Timestamp | None,
    apply_pre_reg_filter: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, pl.DataFrame]:
    """Apply triple-barrier labels for a single label config and join features.

    Returns ``(X, y_bin, r_bar, ts_int, sym_frame)``. ``y_bin`` is the
    binary classification target ``label > 0``; ``r_bar`` is the per-bar
    log return used for HMM emissions and PnL. The pre-reg date filter
    is honoured per design.md §2 / P1-H050-SPLIT-PARAMS — clip to
    ``[train.start, test.end]`` BEFORE deriving split sizes.
    """
    label_cfg = TripleBarrierConfig(
        pt_sl=(pt_sl, pt_sl),
        vertical_barrier=vertical_barrier,
        volatility_lookback=volatility_lookback,
    )
    labeler = TripleBarrierLabeler(label_cfg)
    labeled = labeler.apply(panel_for_symbol, symbol_col="symbol", time_col="ts_event")
    merged = labeled.join(feature_matrix, on=["symbol", "ts_event"], how="left").drop_nulls()
    merged = merged.sort(["symbol", "ts_event"])
    if apply_pre_reg_filter and train_start_ts is not None and test_end_ts is not None:
        merged = merged.filter(
            (pl.col("ts_event") >= train_start_ts) & (pl.col("ts_event") <= test_end_ts)
        )
    if merged.shape[0] == 0:
        return (
            np.zeros((0, len(feature_keys)), dtype=np.float64),
            np.zeros(0, dtype=np.int64),
            np.zeros(0, dtype=np.float64),
            np.zeros(0, dtype=np.int64),
            merged,
        )
    X = merged.select(list(feature_keys)).to_numpy().astype(np.float64)
    y_full = merged.get_column("label").to_numpy().astype(np.int64)
    y_bin = (y_full > 0).astype(np.int64)
    closes = merged.get_column("close").to_numpy().astype(np.float64)
    r_bar = np.zeros(len(closes), dtype=np.float64)
    r_bar[1:] = np.diff(np.log(closes))
    ts_int = merged.get_column("ts_event").to_numpy().astype("datetime64[ns]").astype(np.int64)
    return X, y_bin, r_bar, ts_int, merged


def _fit_fold(  # noqa: PLR0912, PLR0915
    train_idx: np.ndarray,
    *,
    X: np.ndarray,
    y: np.ndarray,
    r: np.ndarray,
    hmm_cov_types: tuple[str, ...],
    lgb_grid: dict[str, tuple[Any, ...]],
    lgb_n_draws: int,
    lgb_seed: int,
    random_seed: int,
    label_horizon: int,
    embargo: int,
    n_inner_folds: int,
    fold_id: int | None = None,
    symbol: str | None = None,
    hmm_cache: dict[tuple[str, int, int], _CachedHmmFit] | None = None,
    hmm_cache_stats: _HmmCacheStats | None = None,
) -> dict[str, Any]:
    """Fit the classifier + HMM on the outer fold's training rows.

    HP selection uses a nested walk-forward inner CV over
    ``lgb_n_draws`` random search draws (Varma & Simon 2006,
    doi:10.1186/1471-2105-7-91; Bergstra & Bengio 2012, JMLR
    13:281-305). The selection metric is mean inner-OOS logistic loss
    — matches the LightGBM training objective per H050 design.md §5.

    The HMM is fit on all train-fold rows (no inner CV — model
    selection happens via BIC over covariance types per ADR-0005).
    """
    return _fit_fold_with_progress(
        train_idx,
        X=X, y=y, r=r,
        hmm_cov_types=hmm_cov_types,
        lgb_grid=lgb_grid,
        lgb_n_draws=lgb_n_draws,
        lgb_seed=lgb_seed,
        random_seed=random_seed,
        label_horizon=label_horizon,
        embargo=embargo,
        n_inner_folds=n_inner_folds,
        fold_id=fold_id,
        symbol=symbol,
        hmm_cache=hmm_cache,
        hmm_cache_stats=hmm_cache_stats,
    )


def _fit_fold_with_progress(  # noqa: PLR0912, PLR0915
    train_idx: np.ndarray,
    *,
    X: np.ndarray,
    y: np.ndarray,
    r: np.ndarray,
    hmm_cov_types: tuple[str, ...],
    lgb_grid: dict[str, tuple[Any, ...]],
    lgb_n_draws: int,
    lgb_seed: int,
    random_seed: int,
    label_horizon: int,
    embargo: int,
    n_inner_folds: int,
    fold_id: int | None = None,
    symbol: str | None = None,
    hmm_cache: dict[tuple[str, int, int], _CachedHmmFit] | None = None,
    hmm_cache_stats: _HmmCacheStats | None = None,
) -> dict[str, Any]:
    """Body of _fit_fold; wrapped by the public _fit_fold entry to
    emit the PROGRESS fold-fit start/done/failed markers via the
    _ProgressLog context manager (Round-1 audit-remediate finding
    Q-1-1 — exception path must emit a failed marker rather than
    leaking an orphan start)."""
    with _PROGRESS.phase(
        "fold-fit",
        sym=symbol,
        fold_id=fold_id,
        train_size=len(train_idx),
        label_horizon=label_horizon,
    ) as _fold_done_ctx:
        return _fit_fold_body(
            train_idx,
            X=X, y=y, r=r,
            hmm_cov_types=hmm_cov_types,
            lgb_grid=lgb_grid,
            lgb_n_draws=lgb_n_draws,
            lgb_seed=lgb_seed,
            random_seed=random_seed,
            label_horizon=label_horizon,
            embargo=embargo,
            n_inner_folds=n_inner_folds,
            fold_id=fold_id,
            symbol=symbol,
            hmm_cache=hmm_cache,
            hmm_cache_stats=hmm_cache_stats,
            _fold_done_ctx=_fold_done_ctx,
        )


def _fit_fold_body(  # noqa: PLR0912, PLR0915
    train_idx: np.ndarray,
    *,
    X: np.ndarray,
    y: np.ndarray,
    r: np.ndarray,
    hmm_cov_types: tuple[str, ...],
    lgb_grid: dict[str, tuple[Any, ...]],
    lgb_n_draws: int,
    lgb_seed: int,
    random_seed: int,
    label_horizon: int,
    embargo: int,
    n_inner_folds: int,
    fold_id: int | None,
    symbol: str | None,
    hmm_cache: dict[tuple[str, int, int], _CachedHmmFit] | None,
    hmm_cache_stats: _HmmCacheStats | None,
    _fold_done_ctx: dict[str, Any],
) -> dict[str, Any]:
    """Inner body — original _fit_fold logic, no instrumentation
    other than mutating ``_fold_done_ctx`` for exit-time fields."""
    X_tr = X[train_idx]
    y_tr = y[train_idx]
    r_tr = r[train_idx]

    # HMM on returns — BIC over cov types, small grid.
    # NOTE (Round-2 F-1-1 fix): the prior zero-mask `r_tr != 0.0` was
    # dropped because it desynchronised the HMM's transition-matrix
    # discrete-time clock from the bar-position clock used to compute
    # the walk-forward warm-start propagation steps (ADR-0005
    # §"Fold-boundary state continuity"). Under the mask, an HMM step
    # corresponded to "one kept-bar" while the warm-start K-step
    # propagation used "raw bars between train terminal and test first
    # observation" — a silent inconsistency whenever any bar within
    # train or test had r_bar == 0 (halts, flat closes, or the dataset's
    # construction-zero at bar 0). The only construction-zero is at
    # global bar 0 (a single observation in a 1-min ES/NQ panel of
    # ~10^6 bars), so the bias from including it in the HMM emission
    # statistics is negligible (<1e-6 of any moment). The bar-clock /
    # HMM-clock invariant is preserved under no mask.
    #
    # P1-H050-SMOKE-RUNTIME-INVESTIGATE: amortise HMM fit across the
    # 27-cell label grid. The HMM input ``r_tr`` is a function of
    # ``(symbol, train_idx)`` only — label cfg perturbs ``y`` (and the
    # outer-fold geometry through ``label_horizon``-derived
    # ``purge_window``) but not the close-derived returns. When
    # ``hmm_cache`` is supplied and a hit is found, we skip
    # ``select_gaussian_hmm`` entirely.
    #
    # F-PLV-1 (Round-2 post-loop verification): the cache key is
    # ``(symbol, fold_id, label_horizon)``. Cfgs sharing a
    # vertical_barrier (and hence label_horizon) share their HMM fits;
    # cfgs with diverging vertical_barriers get separate cache entries
    # and never collide. On the H050 27-cell grid this delivers
    # 3 vertical_barrier strata × N folds = 3N HMM fits, ~9× faster
    # than the cache-disabled path. The earlier 2-tuple key
    # ``(symbol, fold_id)`` was unsafe: with per-cfg purge_window driven
    # by label_horizon (Round-2 §F-2 fix), divergent vertical_barriers
    # produced different ``train_idx`` for the same fold_id — the
    # invariant guard would have raised on the first cross-stratum cfg
    # transition, terminating the orchestrator. The 3-tuple key
    # eliminates that collision.
    cache_key: tuple[str, int, int] | None
    if hmm_cache is not None and symbol is not None and fold_id is not None:
        cache_key = (str(symbol), int(fold_id), int(label_horizon))
    else:
        cache_key = None

    cached: _CachedHmmFit | None = None
    if cache_key is not None and hmm_cache is not None:
        _t_lookup_0 = time.perf_counter()
        cached = hmm_cache.get(cache_key)
        if hmm_cache_stats is not None:
            hmm_cache_stats.total_cache_lookup_time_s += (
                time.perf_counter() - _t_lookup_0
            )

    if cached is not None:
        _validate_cache_invariant(
            cached,
            train_idx,
            symbol=str(symbol),
            fold_id=int(fold_id) if fold_id is not None else -1,
            label_horizon=int(label_horizon),
        )
        hmm: GaussianHMM = cached.hmm
        hmm_terminal_log_alpha_cached = cached.hmm_terminal_log_alpha
        hmm_train_terminal_position_cached = cached.hmm_train_terminal_position
        regime_high_mean_cached: int | None = cached.regime_high_mean
        if hmm_cache_stats is not None:
            hmm_cache_stats.n_hits += 1
    else:
        with _PROGRESS.phase(
            "hmm-fit",
            sym=symbol,
            fold_id=fold_id,
            train_size=len(train_idx),
            cov_grid=",".join(hmm_cov_types),
        ) as _hmm_done_ctx:
            _t_fit_0 = time.perf_counter()
            hmm_selection = select_gaussian_hmm(
                r_tr.reshape(-1, 1),
                n_states_grid=(2,),
                covariance_types=hmm_cov_types,
                seed=int(random_seed),
                min_restarts=5,
                max_restarts=10,
            )
            hmm = hmm_selection.best_model
            if hmm_cache_stats is not None:
                hmm_cache_stats.total_hmm_fit_time_s += time.perf_counter() - _t_fit_0
                hmm_cache_stats.n_misses += 1
                if cache_key is not None:
                    hmm_cache_stats.unique_keys.add(cache_key)
            hmm_terminal_log_alpha_cached = None
            hmm_train_terminal_position_cached = None
            regime_high_mean_cached = None
            _hmm_done_ctx["best_cov"] = hmm_selection.best_covariance_type
            _hmm_done_ctx["best_n_states"] = hmm_selection.best_n_states

    # P1-H050-INNER-CV: nested walk-forward CV per Varma & Simon 2006
    # (doi:10.1186/1471-2105-7-91). model.score(X_tr, y_tr) is REMOVED;
    # selection metric is mean inner-OOS logistic loss across
    # `n_inner_folds` purged+embargoed inner walk-forward folds.
    import lightgbm as lgb

    if len(np.unique(y_tr)) < 2:  # noqa: PLR2004
        # Reuse cached scalars when available so the no-classifier
        # branch never recomputes the forward pass on a hit.
        if regime_high_mean_cached is not None:
            rhm_short = regime_high_mean_cached
        else:
            rhm_short = int(np.argmax(hmm.params_.means[:, 0])) if hmm.params_ else 0
        if hmm_terminal_log_alpha_cached is not None:
            tla_short = hmm_terminal_log_alpha_cached
        else:
            tla_short = hmm.terminal_log_alpha(r_tr.reshape(-1, 1))
        if hmm_train_terminal_position_cached is not None:
            ttp_short = hmm_train_terminal_position_cached
        else:
            ttp_short = int(train_idx[-1])
        if (
            cached is None
            and cache_key is not None
            and hmm_cache is not None
        ):
            hmm_cache[cache_key] = _CachedHmmFit(
                hmm=hmm,
                regime_high_mean=int(rhm_short),
                hmm_terminal_log_alpha=tla_short,
                hmm_train_terminal_position=int(ttp_short),
                train_idx_len=int(len(train_idx)),
                train_idx_first=int(train_idx[0]),
                train_idx_last=int(train_idx[-1]),
            )
        _fold_done_ctx["classifier"] = "skipped-degenerate-y"
        return {
            "classifier": None,
            "hmm": hmm,
            "regime_high_mean": int(rhm_short),
            "hmm_terminal_log_alpha": tla_short,
            "hmm_train_terminal_position": int(ttp_short),
            "selected_hp": None,
            "inner_cv_logloss": np.inf,
            "inner_cv_sharpe": -np.inf,
        }

    with _PROGRESS.phase(
        "inner-cv-lgb",
        sym=symbol,
        fold_id=fold_id,
        n_draws=lgb_n_draws,
        n_inner_folds=n_inner_folds,
    ) as _inner_cv_done_ctx:
        best_params, best_logloss, best_sharpe = _inner_cv_select_hp(
            X_train_outer=X_tr,
            y_train_outer=y_tr,
            r_train_outer=r_tr,
            lgb_grid=lgb_grid,
            lgb_n_draws=lgb_n_draws,
            lgb_seed=lgb_seed,
            random_seed=random_seed,
            label_horizon=label_horizon,
            embargo=embargo,
            n_inner_folds=n_inner_folds,
        )
        _inner_cv_done_ctx["best_logloss"] = f"{best_logloss:.4g}"
        _inner_cv_done_ctx["best_sharpe"] = f"{best_sharpe:.4g}"

    # Refit the selected HP on the FULL outer-train block. Inner CV
    # used disjoint inner-test blocks for selection only; the
    # production model is trained on all outer-train rows — the
    # standard nested-CV refit step (Varma & Simon 2006 §3).
    if best_params is None:
        # Fallback — inner CV produced no usable folds (e.g. tiny
        # train block in dry-run). Train a single model with the grid
        # midpoint to keep the pipeline alive without selecting on
        # in-sample data.
        midpoint = {k: list(lgb_grid[k])[len(lgb_grid[k]) // 2] for k in lgb_grid}
        midpoint = {
            k: (int(v) if isinstance(v, np.integer) else float(v)) for k, v in midpoint.items()
        }
        best_params = midpoint
    final_model = lgb.LGBMClassifier(
        n_estimators=50,
        random_state=int(random_seed),
        verbose=-1,
        **best_params,
    )
    final_model.fit(X_tr, y_tr)

    # Highest-mean regime state (for inference-time gating). Taken
    # from the HMM's emission means.
    assert hmm.params_ is not None
    if regime_high_mean_cached is not None:
        regime_high_mean = int(regime_high_mean_cached)
    else:
        means = hmm.params_.means[:, 0]
        regime_high_mean = int(np.argmax(means))

    # P1-HMM-FOLD-WARM-START: harvest train-fold terminal log α as the
    # sufficient statistic for the test-fold filter prior (ADR-0005
    # §"Fold-boundary state continuity"). With the zero-mask removed
    # (Round-2 F-1-1 fix above), the HMM observation count equals the
    # train-fold bar count, so the terminal HMM observation lives at
    # bar position train_idx[-1]. Cache hit reuses the cached forward
    # pass; cache miss recomputes once and stores for subsequent cfgs.
    if hmm_terminal_log_alpha_cached is not None:
        hmm_terminal_log_alpha = hmm_terminal_log_alpha_cached
    else:
        hmm_terminal_log_alpha = hmm.terminal_log_alpha(r_tr.reshape(-1, 1))
    if hmm_train_terminal_position_cached is not None:
        hmm_train_terminal_position = int(hmm_train_terminal_position_cached)
    else:
        hmm_train_terminal_position = int(train_idx[-1])

    if cached is None and cache_key is not None and hmm_cache is not None:
        hmm_cache[cache_key] = _CachedHmmFit(
            hmm=hmm,
            regime_high_mean=int(regime_high_mean),
            hmm_terminal_log_alpha=hmm_terminal_log_alpha,
            hmm_train_terminal_position=int(hmm_train_terminal_position),
            train_idx_len=int(len(train_idx)),
            train_idx_first=int(train_idx[0]),
            train_idx_last=int(train_idx[-1]),
        )

    _fold_done_ctx["regime_high_mean"] = regime_high_mean
    return {
        "classifier": final_model,
        "hmm": hmm,
        "regime_high_mean": regime_high_mean,
        "hmm_terminal_log_alpha": hmm_terminal_log_alpha,
        "hmm_train_terminal_position": hmm_train_terminal_position,
        "selected_hp": best_params,
        "inner_cv_logloss": best_logloss,
        "inner_cv_sharpe": best_sharpe,
    }


def _predict_fold(
    fitted: dict[str, Any],
    test_idx: np.ndarray,
    *,
    X: np.ndarray,
    r: np.ndarray,
    warm_cold_diagnostic: WarmColdDiagnostic | None = None,
    fold_id: int | None = None,
) -> np.ndarray:
    """Emit two-column predictions: ``(classifier_p, regime_indicator)``.

    Regime is the indicator ``P(state = highest-mean state | y_{1:t})``
    > 0.5 evaluated through :meth:`GaussianHMM.filter_states_from_prior`
    (causal warm-start; ADR-0005). Classifier probability is the
    LightGBM class-1 probability.

    The optional ``warm_cold_diagnostic`` collector is a passive
    observer (P1-HMM-WARM-COLD-DIAGNOSTIC): when supplied, the
    function additionally computes the cold-start posterior and
    records per-fold Hellinger / total-variation summary statistics.
    The cold-start path is discarded after observation; the
    production output is unconditionally the warm-start posterior.

    ``fold_id`` is injected by
    :meth:`~skie_ninja.backtest.engine.walk_forward.WalkForwardEngine.run`
    (P1-WF-ENGINE-FOLD-ID-PASSTHROUGH closure) and is identical to
    ``WalkForwardResult.fold_records[i].fold_id`` for the fold under
    test. When ``None`` (e.g. the function is invoked outside the
    engine for ad-hoc inspection) the diagnostic falls back to
    ``len(warm_cold_diagnostic.fold_records)`` — the same fallback
    used before the passthrough refactor.
    """
    X_te = X[test_idx]
    r_te = r[test_idx]
    clf = fitted["classifier"]
    if clf is None:
        p = np.full(test_idx.size, 0.5, dtype=np.float64)
    else:
        p = (
            clf.predict_proba(X_te)[:, 1]
            if hasattr(clf, "predict_proba")
            else (clf.predict(X_te).astype(float))
        )
    hmm: GaussianHMM = fitted["hmm"]
    # P1-HMM-FOLD-WARM-START closure: warm-start the test-fold causal
    # forward filter with the train-fold terminal log α, propagated K
    # transition steps where K = test_first_position − train_terminal_position
    # accounts for the purge+embargo gap (López de Prado 2018 AFML §7).
    # Anchored on the Hamilton-filter prediction step (Hamilton 1989
    # Econometrica §3, Hamilton 1994 §22.4, Kim & Nelson 1999 §4.2-4.3).
    # ADR-0005 §"Fold-boundary state continuity" documents the choice
    # and rejects the cold-start variants.
    log_alpha_prior = fitted["hmm_terminal_log_alpha"]
    test_first_position = int(test_idx[0])
    train_terminal_position = int(fitted["hmm_train_terminal_position"])
    n_propagation_steps = test_first_position - train_terminal_position
    if n_propagation_steps < 1:
        raise ValueError(
            f"Walk-forward fold-boundary invariant violated: "
            f"test_first_position={test_first_position} <= "
            f"train_terminal_position={train_terminal_position}. "
            f"Test fold must start strictly after train fold terminal."
        )
    test_obs = r_te.reshape(-1, 1)
    filtered = hmm.filter_states_from_prior(
        test_obs,
        log_alpha_prior=log_alpha_prior,
        n_propagation_steps=n_propagation_steps,
    )
    # P1-HMM-WARM-COLD-DIAGNOSTIC: passive observer. The cold posterior
    # is computed only for the diagnostic record and is not used in the
    # returned predictions. Hellinger distance (Tsybakov 2009 §2.4; Le
    # Cam 1986 general reference) is the primary divergence metric;
    # total-variation distance is logged as a secondary metric so the
    # Tsybakov 2009 envelope H^2 <= TV <= H*sqrt(2 - H^2) (substituted
    # under bounded Hellinger) provides a per-fold sanity envelope.
    if warm_cold_diagnostic is not None:
        cold = hmm.filter_states(test_obs)
        diag_fold_id = fold_id if fold_id is not None else len(warm_cold_diagnostic.fold_records)
        warm_cold_diagnostic.observe_fold(
            fold_id=diag_fold_id,
            warm_posterior=filtered,
            cold_posterior=cold,
            n_propagation_steps=n_propagation_steps,
            train_terminal_position=train_terminal_position,
            test_first_position=test_first_position,
        )
    high_state = fitted["regime_high_mean"]
    regime_indicator = (filtered[:, high_state] > 0.5).astype(np.float64)
    return np.stack([p, regime_indicator], axis=1)


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def _sharpe_differential_stats(
    *,
    gated: np.ndarray,
    unconditional: np.ndarray,
    n_bootstrap: int,
    seed: int,
    omega_method: str = "bootstrap",
) -> dict[str, Any]:
    """Opdyke CI + Hansen SPA on OOS returns.

    ``omega_method`` follows ADR-0008: pass ``"hac"`` for single-strategy
    gates (M=1) to decouple the bootstrap MC error from the LRV estimator.
    """
    ci = opdyke2007_ci(gated)
    sharpe_g, _ = sample_sharpe(gated)
    sharpe_u, _ = sample_sharpe(unconditional) if unconditional.std() > 0 else (0.0, 0)
    differential = sharpe_g - sharpe_u
    # SPA: one candidate strategy (gated minus unconditional).
    d = (gated - unconditional).reshape(-1, 1)
    rng = np.random.default_rng(seed)
    bl_selection = choose_block_length(gated - unconditional, bootstrap_type="stationary")
    spa = hansen_spa_test(
        d,
        n_bootstrap=n_bootstrap,
        block_length=bl_selection.block_length,
        rng=rng,
        omega_method=omega_method,
    )
    return {
        "sharpe_gated": float(sharpe_g),
        "sharpe_unconditional": float(sharpe_u),
        "sharpe_differential": float(differential),
        "opdyke_ci": ci.to_dict(),
        "hansen_spa": {
            "p_value": spa.p_value,
            "p_value_lower": spa.p_value_lower,
            "p_value_upper": spa.p_value_upper,
            "statistic": spa.statistic,
            "block_length": bl_selection.block_length,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Walk-forward orchestrator.")
    ap.add_argument("--hypothesis", required=True, help="Hypothesis id, e.g. H050.")
    ap.add_argument("--config", required=True, type=Path, help="YAML config path.")
    ap.add_argument("--dry-run", action="store_true", help="Synthetic-panel mode.")
    ap.add_argument(
        "--smoke-n",
        type=int,
        default=5000,
        help="Rows per symbol in synthetic panel (dry-run).",
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help=(
            "CI-only override: reduce lgb_n_draws to "
            f"{_SMOKE_LGB_N_DRAWS}, label-grid coverage to "
            f"{_SMOKE_LABEL_GRID_LIMIT} cell (center), and inner-CV "
            f"folds to {_SMOKE_INNER_N_FOLDS}. Production runs use "
            "H050.yaml-bound n_draws=200 + the full 27-cell label grid + "
            f"{_DEFAULT_INNER_N_FOLDS} inner folds."
        ),
    )
    ap.add_argument(
        "--no-hmm-cache",
        action="store_true",
        help=(
            "Disable the per-symbol HMM-fit cache (P1-H050-SMOKE-RUNTIME-"
            "INVESTIGATE). Default: enabled. The cache amortises the "
            "BIC-selected GaussianHMM fit across the 27-cell label grid "
            "since HMM input r_tr is cfg-independent for a given "
            "(symbol, fold). The disabled path is the legacy code path "
            "and is exposed for byte-identical-output regression "
            "verification."
        ),
    )
    return ap.parse_args(argv)


def _load_output_sha256(paths: Any) -> dict[str, str]:
    """Load the roll-adjusted output frame SHA256 from the most recent
    provenance JSON for dataset_checksums wiring into ReproLog.

    Falls back gracefully if no provenance file is present (dry-run).
    """
    import glob as _glob

    pattern = str(
        paths.root
        / "data"
        / "processed"
        / "_provenance"
        / "vendor_legacy_1min_roll_adjusted_*.json"
    )
    files = sorted(_glob.glob(pattern))
    if not files:
        return {}
    try:
        with open(files[-1], encoding="utf-8") as fh:
            prov = json.load(fh)
        # output_frame_sha256 is the post-roll-adjustment combined hash;
        # source_dataset_frame_sha256 is the pre-adjustment input hash.
        sha = prov.get(
            "output_frame_sha256",
            prov.get("source_dataset_frame_sha256", ""),
        )
        if sha:
            return {"vendor_legacy_1min_roll_adjusted": sha}
    except Exception:
        pass
    return {}


def _build_label_grid(
    cfg: RunConfig, *, smoke: bool
) -> list[tuple[float, pd.Timedelta, int]]:
    """Enumerate the pre-registered 27-cell label grid (or smoke subset).

    design.md §4 binds:
        pt_sl              ∈ {1.0, 1.5, 2.0}
        vertical_barrier   ∈ {30m, 60m, 120m}
        volatility_lookback ∈ {20, 60, 120}

    Production walk-forward enumerates the full Cartesian product (27
    cells); ``smoke`` reduces to the center cell only (Phase-A semantics)
    so the CI fixture exercises the joint-CV plumbing without paying the
    27× cost.
    """
    if smoke:
        return [
            (
                cfg.pt_sl_grid[len(cfg.pt_sl_grid) // 2],
                cfg.vertical_barrier_grid[len(cfg.vertical_barrier_grid) // 2],
                cfg.volatility_lookback_grid[len(cfg.volatility_lookback_grid) // 2],
            )
        ]
    grid: list[tuple[float, pd.Timedelta, int]] = []
    for pt_sl in cfg.pt_sl_grid:
        for vb in cfg.vertical_barrier_grid:
            for vl in cfg.volatility_lookback_grid:
                grid.append((float(pt_sl), vb, int(vl)))
    return grid


def _run_symbol_label_cfg(  # noqa: PLR0915
    sym: str,
    panel_for_symbol: pl.DataFrame,
    feature_matrix: pl.DataFrame,
    *,
    cfg: RunConfig,
    args: argparse.Namespace,
    pt_sl: float,
    vertical_barrier: pd.Timedelta,
    volatility_lookback: int,
    lgb_n_draws: int,
    n_inner_folds: int,
    hmm_cache: dict[tuple[str, int, int], _CachedHmmFit] | None = None,
    hmm_cache_stats: _HmmCacheStats | None = None,
) -> dict[str, Any] | None:
    """Run the engine for one symbol × one label cfg.

    Returns a dict with keys ``result``, ``inner_cv_sharpe_mean``,
    ``inner_cv_logloss_mean``, ``sym_frame``, ``X_full``, ``y_bin``,
    ``r_bar``, ``ts_arr``, ``label_horizon``, ``embargo``,
    ``warm_cold_diag``, ``initial_train``, ``test_size``, ``step_size``,
    ``split_size_source``, ``test_window_bars``, ``label_cfg_summary``,
    ``selected_hp_per_fold``, ``splitter_purge_window``.
    Returns ``None`` when the symbol has insufficient rows to walk forward.

    Purge-window discipline (Round-2 §F-2 fix).
    -------------------------------------------
    Both the OUTER walk-forward split and the INNER nested-CV split
    use the SAME per-cfg ``label_horizon`` as the splitter
    ``purge_window``. Per López de Prado 2018 *AFML* §7.4 ("Purging the
    Training Set"), the purge window must equal the label horizon —
    the maximum number of bars over which a label can be co-determined
    by future training observations. Each label cfg has its OWN
    horizon (derived from ``vertical_barrier`` per
    ``TripleBarrierLabeler.label_horizon_bars``); using the GLOBAL
    grid-max (Round-1's behaviour) inflated purge for all cfgs to
    accommodate the longest horizon, breaking apples-to-apples across
    cfgs because shorter-horizon cfgs paid for purge they did not need.
    The fix is per-cfg: the outer-split purge equals THIS cfg's
    horizon; the inner-split purge does the same. Outer fold geometry
    therefore varies slightly per cfg, which is correct — each cfg has
    its own causal-leak envelope and the splitter must reflect that.
    A regression test ``test_outer_inner_purge_window_matches_per_cfg``
    asserts the invariant.
    """
    # Round-2 audit-remediate Q-2-2: explicit try/except so an
    # exception inside the body emits PROGRESS label-cfg failed
    # rather than silently leaking the start marker.
    _label_cfg_phase_ctx = {
        "sym": sym,
        "pt_sl": pt_sl,
        "vb": str(vertical_barrier),
        "vl": volatility_lookback,
    }
    _PROGRESS.start("label-cfg", **_label_cfg_phase_ctx)
    try:
        return _run_symbol_label_cfg_body(
            sym,
            panel_for_symbol,
            feature_matrix,
            cfg=cfg,
            args=args,
            pt_sl=pt_sl,
            vertical_barrier=vertical_barrier,
            volatility_lookback=volatility_lookback,
            lgb_n_draws=lgb_n_draws,
            n_inner_folds=n_inner_folds,
            hmm_cache=hmm_cache,
            hmm_cache_stats=hmm_cache_stats,
        )
    except Exception as exc:
        _PROGRESS.failed(
            "label-cfg",
            exc_type=type(exc).__name__,
            **_label_cfg_phase_ctx,
        )
        raise


def _run_symbol_label_cfg_body(  # noqa: PLR0915
    sym: str,
    panel_for_symbol: pl.DataFrame,
    feature_matrix: pl.DataFrame,
    *,
    cfg: RunConfig,
    args: argparse.Namespace,
    pt_sl: float,
    vertical_barrier: pd.Timedelta,
    volatility_lookback: int,
    lgb_n_draws: int,
    n_inner_folds: int,
    hmm_cache: dict[tuple[str, int, int], _CachedHmmFit] | None = None,
    hmm_cache_stats: _HmmCacheStats | None = None,
) -> dict[str, Any] | None:
    """Inner body of `_run_symbol_label_cfg`. The thin wrapper above
    handles the start/failed PROGRESS markers; this function emits
    the success-path `done` markers explicitly before each return."""
    label_cfg_obj = TripleBarrierConfig(
        pt_sl=(pt_sl, pt_sl),
        vertical_barrier=vertical_barrier,
        volatility_lookback=volatility_lookback,
    )
    labeler = TripleBarrierLabeler(label_cfg_obj)
    labeled = labeler.apply(panel_for_symbol, symbol_col="symbol", time_col="ts_event")
    merged = labeled.join(feature_matrix, on=["symbol", "ts_event"], how="left").drop_nulls()
    merged = merged.sort(["symbol", "ts_event"])
    sym_frame = merged.filter(pl.col("symbol") == sym)
    if not args.dry_run:
        sym_frame = sym_frame.filter(
            (pl.col("ts_event") >= cfg.train_start) & (pl.col("ts_event") <= cfg.test_end)
        )
    if sym_frame.shape[0] < 200:  # noqa: PLR2004
        _PROGRESS.done(
            "label-cfg",
            sym=sym,
            status="skipped-insufficient-rows",
            n_rows=sym_frame.shape[0],
        )
        return None

    feature_cols = list(cfg.feature_keys)
    X_full = sym_frame.select(feature_cols).to_numpy().astype(np.float64)
    y_full = sym_frame.get_column("label").to_numpy().astype(np.int64)
    y_bin = (y_full > 0).astype(np.int64)
    closes = sym_frame.get_column("close").to_numpy().astype(np.float64)
    r_bar = np.zeros(len(closes), dtype=np.float64)
    r_bar[1:] = np.diff(np.log(closes))

    n = sym_frame.shape[0]
    bar_duration = pd.Timedelta(minutes=1)
    label_horizon = labeler.label_horizon_bars(bar_duration)

    bl = choose_block_length(r_bar, bootstrap_type="stationary")
    embargo = int(max(1, np.ceil(bl.block_length)))

    if args.dry_run:
        initial_train = max(200, n // 3)
        test_size = max(50, n // 10)
        step_size = test_size
        split_size_source = "row_fraction"
        test_window_bars = 0
    else:
        ts_event_pl = sym_frame.get_column("ts_event")
        initial_train = int((ts_event_pl <= cfg.val_end).sum())
        val_mask_pl = (ts_event_pl >= cfg.val_start) & (ts_event_pl <= cfg.val_end)
        test_size = int(val_mask_pl.sum())
        step_size = test_size
        split_size_source = "calendar"
        if initial_train <= 0 or test_size <= 0:
            raise ValueError(
                f"Pre-reg date-derived split sizes invalid for sym={sym}: "
                f"initial_train={initial_train}, test_size={test_size}. "
                f"Expected >0 bars in both [train.start, val.end] and "
                f"[val.start, val.end] after filtering to "
                f"[train.start={cfg.train_start.date()}, "
                f"test.end={cfg.test_end.date()}]; verify panel coverage "
                f"against H050.yaml §data."
            )
        test_window_bars = int(
            ((ts_event_pl >= cfg.test_start) & (ts_event_pl <= cfg.test_end)).sum()
        )
        if test_window_bars <= 0:
            raise ValueError(
                f"Pre-reg test window [{cfg.test_start.date()}, "
                f"{cfg.test_end.date()}] is empty in the filtered panel "
                f"for sym={sym}; verify ingest snapshot covers "
                f"H050.yaml §data.test."
            )

    # Round-2 §F-2 fix: outer purge == per-cfg label_horizon, matching
    # the inner-CV purge in `_build_inner_folds`. AFML §7.4 mandates
    # purge_window == label horizon to remove training labels that are
    # co-determined by post-test observations.
    split = walk_forward_split(
        n_samples=n,
        initial_train_size=initial_train,
        test_size=test_size,
        step_size=step_size,
        label_horizon=label_horizon,
        embargo=embargo,
        mode="rolling",
        purge_window=label_horizon,
    )

    engine = WalkForwardEngine(split)
    ts_arr = (
        sym_frame.get_column("ts_event").to_numpy().astype("datetime64[ns]").astype(np.int64)
    )

    if not args.dry_run and len(split.folds) > 0:
        fold0_test = split.folds[0].test_indices()
        if len(fold0_test) > 0:
            first_oos_pos = int(fold0_test[0])
            first_oos_ts_int = int(ts_arr[first_oos_pos])
            test_start_ts_int = int(
                np.datetime64(cfg.test_start.to_datetime64())
                .astype("datetime64[ns]")
                .astype(np.int64)
            )
            if first_oos_ts_int < test_start_ts_int:
                raise ValueError(
                    f"Fold-0 first OOS bar maps to "
                    f"ts_int={first_oos_ts_int}, strictly less than "
                    f"cfg.test_start ts_int={test_start_ts_int} — "
                    f"calendar drift has put a pre-test_start bar into "
                    f"OOS. Verify panel coverage in [val.start, val.end] "
                    f"is contiguous, or land "
                    f"P1-H050-CALENDAR-ANCHORED-SPLITTER."
                )
    warm_cold_diag = WarmColdDiagnostic()
    result = engine.run(
        fit_fn=_fit_fold,
        predict_fn=_predict_fold,
        feature_timestamps=ts_arr,
        observation_timestamps=ts_arr,
        fit_kwargs=dict(
            X=X_full,
            y=y_bin,
            r=r_bar,
            hmm_cov_types=cfg.hmm_cov_types,
            lgb_grid=cfg.lgb_grid,
            lgb_n_draws=lgb_n_draws,
            lgb_seed=cfg.lgb_seed,
            random_seed=cfg.random_seed,
            label_horizon=label_horizon,
            embargo=embargo,
            n_inner_folds=n_inner_folds,
            symbol=sym,
            hmm_cache=hmm_cache,
            hmm_cache_stats=hmm_cache_stats,
        ),
        predict_kwargs=dict(
            X=X_full,
            r=r_bar,
            warm_cold_diagnostic=warm_cold_diag,
        ),
        keep_fitted=True,
    )

    inner_sharpes = [
        f.get("inner_cv_sharpe", -np.inf)
        for f in result.fitted_models
        if isinstance(f, dict)
    ]
    finite_inner = [s for s in inner_sharpes if np.isfinite(s)]
    inner_cv_sharpe_mean = float(np.mean(finite_inner)) if finite_inner else -np.inf

    # Inner-CV log-loss mean is the deterministic tie-breaker on the
    # ungated Sharpe metric used for label-grid selection (see
    # `_run_symbol` docstring "Tie-breaker on the Sharpe metric").
    # Lower is better; np.inf when no fold produced a valid logloss.
    inner_loglosses = [
        f.get("inner_cv_logloss", np.inf)
        for f in result.fitted_models
        if isinstance(f, dict)
    ]
    finite_logloss = [ll for ll in inner_loglosses if np.isfinite(ll)]
    inner_cv_logloss_mean = float(np.mean(finite_logloss)) if finite_logloss else np.inf

    selected_hp_per_fold = [
        f.get("selected_hp") for f in result.fitted_models if isinstance(f, dict)
    ]

    _PROGRESS.done(
        "label-cfg",
        sym=sym,
        n_folds=len(result.fold_records),
        inner_cv_sharpe=f"{inner_cv_sharpe_mean:.4g}",
        inner_cv_logloss=f"{inner_cv_logloss_mean:.4g}",
    )
    return {
        "result": result,
        "split": split,
        "splitter_purge_window": int(label_horizon),
        "inner_cv_sharpe_mean": inner_cv_sharpe_mean,
        "inner_cv_logloss_mean": inner_cv_logloss_mean,
        "sym_frame": sym_frame,
        "X_full": X_full,
        "y_bin": y_bin,
        "r_bar": r_bar,
        "ts_arr": ts_arr,
        "label_horizon": label_horizon,
        "embargo": embargo,
        "warm_cold_diag": warm_cold_diag,
        "initial_train": initial_train,
        "test_size": test_size,
        "step_size": step_size,
        "split_size_source": split_size_source,
        "test_window_bars": test_window_bars,
        "label_cfg_summary": {
            "pt_sl": pt_sl,
            "vertical_barrier_seconds": float(vertical_barrier.total_seconds()),
            "volatility_lookback": volatility_lookback,
        },
        "selected_hp_per_fold": selected_hp_per_fold,
    }


def _run_symbol(  # noqa: PLR0912, PLR0915
    sym: str,
    panel_for_symbol: pl.DataFrame,
    feature_matrix: pl.DataFrame,
    *,
    cfg: RunConfig,
    args: argparse.Namespace,
    run_id: str,
    run_dir: Path,
    paths: ProjectPaths,
    ctx: RunContext,
    feature_provenance: list[Any],
    label_grid: list[tuple[float, pd.Timedelta, int]],
    lgb_n_draws: int,
    n_inner_folds: int,
) -> dict[str, Any]:
    """End-to-end per-symbol pipeline (label-grid CV → engine → gates).

    P1-H050-LABEL-CV closure: enumerate the pre-reg 27-cell label
    grid; for each cell run the walk-forward engine with nested
    inner-CV HP selection (P1-H050-INNER-CV); pick the cell whose
    mean inner-OOS Sharpe (UNGATED, via :func:`_strategy_sharpe_simple`
    on the inner-test bars) across outer folds is highest. The
    selected cell's engine result drives all downstream artifacts.
    Inner-OOS Sharpe — not outer-OOS — is the selection criterion to
    avoid using held-out test data for label selection.

    Design choice: ungated label-CV metric (decoupled from the
    production gated metric).
    --------------------------------------------------------------
    The production target ``T_H050 = SR_filtered_gated −
    SR_filtered_unconditional`` (design.md §1) is a regime-conditioned
    differential. The label-grid selection metric here is the UNGATED
    classifier Sharpe (``np.sign(2p − 1) · r``) on inner-OOS bars,
    NOT the gated differential. This decoupling is deliberate:

    - Labels (López de Prado 2018 AFML §3.4 "The Triple-Barrier
      Method") are a label-engineering hyperparameter — they govern
      which directional signal the classifier is trained against;
      AFML §3.4 frames labels as downstream of the trading rule's
      P&L, not of any inference-time gate.
    - The HMM regime gate is a separate inference-time conditioning
      component (ADR-0005) applied AFTER classifier inference.
    - Selecting labels on the GATED metric would entangle two
      independent design components: the gate's regime sensitivity
      would perturb label-grid selection in a way that is hard to
      attribute back to either component.

    Selecting labels on the ungated Sharpe optimises classifier signal
    quality independent of the gate; the gate's marginal lift is then
    measured cleanly at the outer-fold OOS evaluation as the
    differential ``SR_gated − SR_unconditional``. An empirical
    sensitivity study (gated vs ungated label-CV; whether the
    selected cell flips when the metric changes) is tracked under
    follow-up ``P1-H050-LABEL-CV-GATED-METRIC``. If the sensitivity
    is non-trivial the design choice will be revisited via a
    successor hypothesis ID per design.md §2 line 41
    ("re-runs on extended windows require a successor hypothesis ID").

    Tie-breaker on the Sharpe metric.
    --------------------------------
    When two label cells produce the same mean inner-OOS Sharpe (e.g.
    on degenerate dry-run data where all cells produce identical
    near-zero Sharpe), selection is broken by the SMALLEST mean
    inner-CV log-loss across outer folds. Log-loss is the LightGBM
    training objective (design.md §5) so the tie-breaker preserves
    the design.md §5 hierarchy (training objective < gate-level
    Sharpe). Determinism is required for reproducibility-log
    stability; without a tie-breaker, Python's ``sorted(...)`` would
    fall through to insertion order, producing run-to-run drift on
    metric ties.
    """
    # Round-2 audit-remediate Q-2-2: explicit try/except so an
    # exception inside the body emits PROGRESS symbol failed rather
    # than silently leaking the start marker.
    _symbol_phase_ctx = {
        "sym": sym,
        "n_label_cfgs": len(label_grid),
        "lgb_n_draws": lgb_n_draws,
        "n_inner_folds": n_inner_folds,
    }
    _PROGRESS.start("symbol", **_symbol_phase_ctx)
    try:
        return _run_symbol_body(
            sym,
            panel_for_symbol,
            feature_matrix,
            cfg=cfg,
            args=args,
            run_id=run_id,
            run_dir=run_dir,
            paths=paths,
            ctx=ctx,
            feature_provenance=feature_provenance,
            label_grid=label_grid,
            lgb_n_draws=lgb_n_draws,
            n_inner_folds=n_inner_folds,
        )
    except Exception as exc:
        _PROGRESS.failed(
            "symbol", exc_type=type(exc).__name__, **_symbol_phase_ctx
        )
        raise


def _run_symbol_body(  # noqa: PLR0912, PLR0915
    sym: str,
    panel_for_symbol: pl.DataFrame,
    feature_matrix: pl.DataFrame,
    *,
    cfg: RunConfig,
    args: argparse.Namespace,
    run_id: str,
    run_dir: Path,
    paths: ProjectPaths,
    ctx: RunContext,
    feature_provenance: list[Any],
    label_grid: list[tuple[float, pd.Timedelta, int]],
    lgb_n_draws: int,
    n_inner_folds: int,
) -> dict[str, Any]:
    """Inner body of `_run_symbol`. The thin wrapper above handles
    the start/failed PROGRESS markers; this function emits the
    success-path `done` markers explicitly before each return."""
    sym_dir = paths.ensure(run_dir / sym)
    folds_dir = paths.ensure(sym_dir / "folds")
    agg_dir = paths.ensure(sym_dir / "aggregate")

    # Round-2 §F-2: per-cfg purge_window — both the outer and inner
    # walk-forward splits use the cfg's `label_horizon` as the purge
    # (AFML §7.4). The Round-1 grid-max (`ceil(max(vb)/60)`) is removed
    # so each cfg pays only its own purge; the geometry varies slightly
    # per cfg, which is correct.
    #
    # P1-H050-SMOKE-RUNTIME-INVESTIGATE: per-symbol HMM-fit cache. The
    # cache is keyed on (symbol, fold_id, label_horizon) (F-PLV-1 fix)
    # and is reset between symbols (each symbol has its own return
    # series; bleed-through would be a correctness violation). With the
    # 3-tuple key, cfgs sharing a vertical_barrier value share fits and
    # cfgs with divergent vertical_barriers populate disjoint cache
    # entries — eliminating the cross-stratum collision that the
    # 2-tuple key would have triggered on the H050 27-cell grid. The
    # cache invariant in `_validate_cache_invariant` is retained as a
    # defensive backstop. With the cache enabled, the dominant per-cfg
    # cost (HMM BIC selection over a multi-restart EM grid) is paid
    # once per (fold, label_horizon) stratum instead of 27× — a 9×
    # speedup on the H050 grid (3 strata × 9 cfgs/stratum).
    use_cache: bool = not bool(getattr(args, "no_hmm_cache", False))
    hmm_cache: dict[tuple[str, int, int], _CachedHmmFit] | None = (
        {} if use_cache else None
    )
    hmm_cache_stats = _HmmCacheStats()
    candidate_runs: list[tuple[tuple[float, pd.Timedelta, int], dict[str, Any]]] = []
    for cfg_idx, (pt_sl, vb, vl) in enumerate(label_grid, start=1):
        # Round-2 audit-remediate Q-2-1 fix: wrap the actual cell
        # execution so `elapsed` reflects per-cell wall-clock (the
        # earlier back-to-back start/done emitted elapsed=0 and
        # defeated the operator-visibility intent).
        with _PROGRESS.phase(
            "label-cfg-loop-step",
            sym=sym,
            cfg_idx=cfg_idx,
            n_cfgs=len(label_grid),
            pt_sl=pt_sl,
            vb=str(vb),
            vl=vl,
        ) as _step_done_ctx:
            candidate = _run_symbol_label_cfg(
                sym,
                panel_for_symbol,
                feature_matrix,
                cfg=cfg,
                args=args,
                pt_sl=pt_sl,
                vertical_barrier=vb,
                volatility_lookback=vl,
                lgb_n_draws=lgb_n_draws,
                n_inner_folds=n_inner_folds,
                hmm_cache=hmm_cache,
                hmm_cache_stats=hmm_cache_stats,
            )
            _step_done_ctx["status"] = (
                "ok" if candidate is not None else "skipped"
            )
        if candidate is None:
            continue
        candidate_runs.append(((pt_sl, vb, vl), candidate))

    if not candidate_runs:
        _write_aggregate(
            agg_dir,
            {"status": "insufficient_rows_all_label_cfgs", "symbol": sym},
        )
        _PROGRESS.done("symbol", sym=sym, status="insufficient_rows")
        return {"status": "insufficient_rows", "sym_dir": sym_dir}

    # Sort: primary key = mean inner-OOS Sharpe (descending);
    # tie-breaker = mean inner-CV log-loss (ascending; smaller is better).
    # Python's `sorted` is stable, so we sort by the secondary key first
    # and then by the primary key, yielding the lexicographic order
    # (Sharpe desc, logloss asc).
    candidate_runs.sort(key=lambda kv: kv[1]["inner_cv_logloss_mean"])
    candidate_runs.sort(key=lambda kv: kv[1]["inner_cv_sharpe_mean"], reverse=True)
    best_label_cfg, best_run = candidate_runs[0]

    label_cv_log: list[dict[str, Any]] = []
    for (pt_sl, vb, vl), candidate in candidate_runs:
        label_cv_log.append(
            {
                "pt_sl": pt_sl,
                "vertical_barrier_seconds": float(vb.total_seconds()),
                "volatility_lookback": vl,
                "inner_cv_sharpe_mean": candidate["inner_cv_sharpe_mean"],
                "inner_cv_logloss_mean": candidate["inner_cv_logloss_mean"],
                "n_folds": len(candidate["result"].fold_records),
            }
        )

    sym_frame = best_run["sym_frame"]
    r_bar = best_run["r_bar"]
    result = best_run["result"]
    split = best_run["split"]
    warm_cold_diag = best_run["warm_cold_diag"]
    initial_train = best_run["initial_train"]
    test_size = best_run["test_size"]
    step_size = best_run["step_size"]
    split_size_source = best_run["split_size_source"]
    test_window_bars = best_run["test_window_bars"]

    if not args.dry_run:
        ctx.add_dataset_checksum(
            f"h050_pre_reg_filtered_{sym.lower()}",
            frame_sha256(sym_frame, sort_cols=["symbol", "ts_event"]),
        )

    _MULTIPLIERS = {"ES": 50.0, "NQ": 20.0, "MES": 5.0, "MNQ": 2.0}
    cost_model = NT8EsNqRthV1CostModel(sensitivity_mult=cfg.cost_sensitivity_mult)
    sym_multiplier = _MULTIPLIERS.get(sym, 50.0)
    per_side_cost = cost_model.round_trip_cost(sym, 1) / 2.0
    closes_full = sym_frame.get_column("close").to_numpy().astype(np.float64)

    gated_returns: list[float] = []
    uncond_returns: list[float] = []
    prev_uncond_pos = 0.0
    prev_gated_pos = 0.0
    for preds, tidx in zip(result.predictions, result.test_indices, strict=True):
        p = preds[:, 0]
        reg = preds[:, 1]
        position = np.sign(2.0 * p - 1.0)
        r_te = r_bar[tidx]
        close_te = closes_full[tidx]

        uncond_raw = position * r_te
        uncond_sides = np.abs(
            np.concatenate([[position[0] - prev_uncond_pos], np.diff(position)])
        )
        notional_uncond = close_te * sym_multiplier
        notional_uncond = np.where(notional_uncond > 0, notional_uncond, 1.0)
        uncond_cost = uncond_sides * per_side_cost / notional_uncond
        uncond = uncond_raw - uncond_cost
        prev_uncond_pos = float(position[-1])

        gated_pos = position * reg
        gated_raw = gated_pos * r_te
        gated_sides = np.abs(
            np.concatenate([[gated_pos[0] - prev_gated_pos], np.diff(gated_pos)])
        )
        notional_gated = close_te * sym_multiplier
        notional_gated = np.where(notional_gated > 0, notional_gated, 1.0)
        gated_cost = gated_sides * per_side_cost / notional_gated
        gated = gated_raw - gated_cost
        prev_gated_pos = float(gated_pos[-1])

        uncond_returns.extend(uncond.tolist())
        gated_returns.extend(gated.tolist())
    gated_arr = np.asarray(gated_returns, dtype=np.float64)
    uncond_arr = np.asarray(uncond_returns, dtype=np.float64)

    sym_run_id = f"{run_id}_{sym}"
    write_run_ledger(
        result.fold_records,
        ledger_path_for(sym_run_id, logs_reproducibility_dir=paths.logs_reproducibility),
    )
    for rec in result.fold_records:
        (folds_dir / f"fold_{rec.fold_id:03d}.json").write_text(
            json.dumps(dataclasses.asdict(rec), sort_keys=True, indent=2),
            encoding="utf-8",
        )

    pl.DataFrame(
        {"gated_return": gated_arr, "unconditional_return": uncond_arr}
    ).write_parquet(sym_dir / "oos_returns.parquet")

    metrics: dict[str, Any]
    _gate_ok = (
        gated_arr.size >= _MIN_OOS_FOR_CI and gated_arr.std() > 0 and uncond_arr.std() > 0
    )
    if not _gate_ok:
        _LOG.warning(
            "Gate skipped (sym=%s): n_returns=%d (need %d), gated_std=%.6f, "
            "uncond_std=%.6f; Sharpe CI and SPA not computed.",
            sym,
            gated_arr.size,
            _MIN_OOS_FOR_CI,
            float(gated_arr.std()),
            float(uncond_arr.std()),
        )
    if _gate_ok:
        metrics = _sharpe_differential_stats(
            gated=gated_arr,
            unconditional=uncond_arr,
            n_bootstrap=cfg.spa_n_bootstrap,
            seed=cfg.random_seed,
            omega_method=cfg.spa_omega_method,
        )
    else:
        metrics = {
            "status": "insufficient_oos_returns",
            "n_returns": int(gated_arr.size),
        }
    metrics["symbol"] = sym
    metrics["n_folds"] = len(result.fold_records)
    metrics["n_features"] = len(cfg.feature_keys)
    metrics["feature_keys"] = list(cfg.feature_keys)
    metrics["feature_provenance"] = [pp.to_dict() for pp in feature_provenance]

    metrics["selected_label_cfg"] = {
        "pt_sl": best_label_cfg[0],
        "vertical_barrier_seconds": float(best_label_cfg[1].total_seconds()),
        "volatility_lookback": best_label_cfg[2],
    }
    metrics["label_cv_inner_sharpes"] = label_cv_log
    metrics["label_grid_size_evaluated"] = len(label_cv_log)
    metrics["lgb_n_draws_effective"] = lgb_n_draws
    metrics["inner_n_folds"] = n_inner_folds
    metrics["selected_hp_per_fold"] = best_run["selected_hp_per_fold"]

    metrics["split_size_source"] = split_size_source
    metrics["initial_train_size"] = int(initial_train)
    metrics["test_size"] = int(test_size)
    metrics["step_size"] = int(step_size)
    if split_size_source == "calendar":
        metrics["pre_reg_envelope"] = {
            "train_start": cfg.train_start.isoformat(),
            "train_end": cfg.train_end.isoformat(),
            "val_start": cfg.val_start.isoformat(),
            "val_end": cfg.val_end.isoformat(),
            "test_start": cfg.test_start.isoformat(),
            "test_end": cfg.test_end.isoformat(),
        }
        expected_n_folds = int(np.ceil(test_window_bars / step_size))
        metrics["expected_n_folds"] = expected_n_folds
        if metrics["n_folds"] != expected_n_folds:
            _LOG.warning(
                "Fold count drift (sym=%s): emitted %d, expected %d (calendar "
                "drift across leap years; see follow-up "
                "P1-H050-CALENDAR-ANCHORED-SPLITTER).",
                sym,
                metrics["n_folds"],
                expected_n_folds,
            )

        ts_arr_ns = sym_frame.get_column("ts_event").to_numpy().astype("datetime64[ns]")
        metrics["realized_envelope_per_fold"] = []
        for fold in split.folds:
            tr = fold.train_indices()
            te = fold.test_indices()
            metrics["realized_envelope_per_fold"].append(
                {
                    "fold_id": fold.fold_id,
                    "train_ts_min": str(ts_arr_ns[tr[0]]) if tr else None,
                    "train_ts_max": str(ts_arr_ns[tr[-1]]) if tr else None,
                    "test_ts_min": str(ts_arr_ns[te[0]]) if te else None,
                    "test_ts_max": str(ts_arr_ns[te[-1]]) if te else None,
                }
            )

    _write_aggregate(agg_dir, metrics)

    warm_cold_path = warm_cold_sidecar_path_for(
        sym_run_id, logs_reproducibility_dir=paths.logs_reproducibility
    )
    _, warm_cold_sha = write_warm_cold_sidecar(warm_cold_diag, warm_cold_path)

    rolled = roll_up_model_hashes(
        [(r.fold_id, r.model_hash) for r in result.fold_records]
    )
    combined = hashlib.sha256(
        f"ledger_rollup={rolled};warm_cold_diag={warm_cold_sha}".encode()
    ).hexdigest()

    # P1-H050-SMOKE-RUNTIME-INVESTIGATE: emit per-symbol cache stats.
    # Operational telemetry only — not a methodological artifact, not
    # included in the model hash. INFO-level so production runs surface
    # the speedup figure without the user opting into DEBUG.
    _LOG.info(
        "HMM cache stats sym=%s: hits=%d, misses=%d, unique_keys=%d, "
        "fit_time_s=%.3f, lookup_time_s=%.6f, enabled=%s",
        sym,
        hmm_cache_stats.n_hits,
        hmm_cache_stats.n_misses,
        hmm_cache_stats.n_unique_keys,
        hmm_cache_stats.total_hmm_fit_time_s,
        hmm_cache_stats.total_cache_lookup_time_s,
        hmm_cache is not None,
    )

    _PROGRESS.done(
        "symbol",
        sym=sym,
        n_folds=len(result.fold_records),
        best_label_cfg=str(best_label_cfg),
        hmm_cache_hits=hmm_cache_stats.n_hits,
        hmm_cache_misses=hmm_cache_stats.n_misses,
    )
    return {
        "status": "ok",
        "sym_dir": sym_dir,
        "n_folds": len(result.fold_records),
        "model_hash_combined": combined,
        "metrics": metrics,
        "hmm_cache_stats": hmm_cache_stats.to_dict(),
        "hmm_cache_enabled": hmm_cache is not None,
    }


def run(argv: list[str] | None = None) -> Path:
    """Top-level orchestrator entrypoint.

    Wrapped in try/except so any unhandled exception emits a
    ``PROGRESS run failed`` marker (Round-1 audit-remediate finding
    Q-1-1) — distinguishes a crashed run from a hung run in the
    JSON log stream. The exception is re-raised so the caller's
    error handling is unchanged.
    """
    args = _parse_args(argv)
    cfg = load_config(args.config)
    paths = ProjectPaths.discover()
    _run_start_ctx = {
        "config": str(args.config),
        "smoke": bool(args.smoke),
        "dry_run": bool(args.dry_run),
        "no_hmm_cache": bool(getattr(args, "no_hmm_cache", False)),
    }
    _PROGRESS.start("run", **_run_start_ctx)
    try:
        return _run_inner(args, cfg, paths)
    except BaseException as exc:
        _PROGRESS.failed(
            "run", exc_type=type(exc).__name__, **_run_start_ctx
        )
        raise


def _run_inner(args: argparse.Namespace, cfg: RunConfig, paths: ProjectPaths) -> Path:

    dataset_checksums = _load_output_sha256(paths) if not args.dry_run else {}

    with RunContext(
        phase="walk_forward",
        hypothesis_id=cfg.hypothesis_id,
        rng_seed=cfg.random_seed,
        dataset_checksums=dataset_checksums,
        config_resolved_sha256=cfg.config_resolved_sha256,
    ) as ctx:
        assert (  # noqa: S101
            ctx.log is not None and ctx.log.config_resolved_sha256 == cfg.config_resolved_sha256
        ), "RunContext failed to persist config_resolved_sha256 onto ReproLog"
        run_id = ctx.log.run_id  # type: ignore[union-attr]
        run_dir = paths.artifacts_runs / cfg.hypothesis_id / run_id
        paths.ensure(run_dir)
        paths.ensure(paths.logs_reproducibility_features)

        if args.dry_run:
            panel = make_synthetic_panel(n_per_symbol=args.smoke_n, seed=cfg.random_seed)
        else:
            parquet_dir = paths.root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
            panel = pl.read_parquet(str(parquet_dir / "**" / "*.parquet"))

        now_ts = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
        modules = [FEATURE_REGISTRY[k] for k in cfg.feature_keys]
        feature_matrix, prov = assemble_feature_matrix(
            modules=modules,
            panel=panel.lazy(),
            now=now_ts,
            run_id=run_id,
            features_dir=paths.logs_reproducibility_features,
        )

        universe = [str(s) for s in cfg.raw.get("universe", ["ES"])]
        if not universe:
            raise ValueError(
                f"H050.yaml universe must be non-empty; got {universe!r}."
            )

        label_grid = _build_label_grid(cfg, smoke=args.smoke)
        lgb_n_draws = _SMOKE_LGB_N_DRAWS if args.smoke else int(cfg.lgb_n_draws)
        n_inner_folds = _SMOKE_INNER_N_FOLDS if args.smoke else _DEFAULT_INNER_N_FOLDS

        per_symbol_results: dict[str, dict[str, Any]] = {}
        per_symbol_combined_hashes: list[tuple[int, str]] = []
        for sym_idx, sym in enumerate(universe):
            panel_sym = panel.filter(pl.col("symbol") == sym)
            if panel_sym.shape[0] == 0:
                _LOG.warning(
                    "Symbol %s absent from panel; skipping. Per design.md "
                    "the substrate must cover [2015-01-01, 2025-12-31]; NQ "
                    "currently truncates to 2020-2024 (P1-H050-DATA-COVERAGE).",
                    sym,
                )
                per_symbol_results[sym] = {
                    "status": "absent_from_panel",
                    "n_folds": 0,
                }
                continue
            sym_outcome = _run_symbol(
                sym,
                panel_sym,
                feature_matrix,
                cfg=cfg,
                args=args,
                run_id=run_id,
                run_dir=run_dir,
                paths=paths,
                ctx=ctx,
                feature_provenance=prov,
                label_grid=label_grid,
                lgb_n_draws=lgb_n_draws,
                n_inner_folds=n_inner_folds,
            )
            per_symbol_results[sym] = sym_outcome
            if sym_outcome.get("status") == "ok":
                per_symbol_combined_hashes.append(
                    (sym_idx, sym_outcome["model_hash_combined"])
                )

        if per_symbol_combined_hashes:
            combined_universe = roll_up_model_hashes(per_symbol_combined_hashes)
        else:
            combined_universe = "no-symbol-ran"

        new_log = with_model_hash(ctx.log, combined_universe)  # type: ignore[arg-type]
        ctx.log = new_log

        (run_dir / "reprolog.json").write_text(
            json.dumps(ctx.log.to_dict(), sort_keys=True, indent=2),
            encoding="utf-8",
        )

        run_summary = {
            "hypothesis_id": cfg.hypothesis_id,
            "run_id": run_id,
            "universe": universe,
            "label_grid_size": len(label_grid),
            "lgb_n_draws_effective": lgb_n_draws,
            "inner_n_folds": n_inner_folds,
            "smoke": bool(args.smoke),
            "hmm_cache_enabled": not bool(args.no_hmm_cache),
            "per_symbol_status": {
                k: {
                    "status": v.get("status"),
                    "n_folds": v.get("n_folds", 0),
                    "hmm_cache_stats": v.get("hmm_cache_stats"),
                }
                for k, v in per_symbol_results.items()
            },
        }
        (run_dir / "run_summary.json").write_text(
            json.dumps(run_summary, sort_keys=True, indent=2, default=str),
            encoding="utf-8",
        )

    _PROGRESS.done(
        "run",
        run_id=run_id,
        run_dir=str(run_dir),
        n_symbols_ok=sum(
            1 for v in per_symbol_results.values() if v.get("status") == "ok"
        ),
        n_symbols_total=len(per_symbol_results),
    )
    return run_dir


def _write_aggregate(agg_dir: Path, metrics: dict[str, Any]) -> None:
    (agg_dir / "metrics_summary.json").write_text(
        json.dumps(metrics, sort_keys=True, indent=2, default=str),
        encoding="utf-8",
    )


if __name__ == "__main__":
    # P1-ORCHESTRATOR-PROGRESS-LOGGING: attach the project's JSON
    # handler so PROGRESS log lines surface on stdout. setup_logging
    # also reconfigures stdout to line_buffering=True so headless
    # runs flush per-line without `python -u` (Round-2 Q-1-3 / R-3).
    from skie_ninja.utils.logging_setup import setup_logging

    setup_logging()
    out = run(sys.argv[1:])
    print(out)
