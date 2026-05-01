"""H053 archetype classifier — design.md §4.5.1.

Fits an archetype-assignment rule on a training-fold mediator output panel
and applies it to OOS mediator outputs. The rule maps each (session,
symbol) row's mediator vector ``M_{i,t} = (m_return, m_log_range, m_volume,
m_ofi_tickrule)`` to a discrete archetype id ``∈ {0..K-1}``.

Per design.md §4.5.1, the rule is a deterministic 4-axis encoding:

  axis 1: sign of ``m_return`` (+ or −)             → 2 buckets
  axis 2: bucket of ``|m_return| / σ̂_{15min, train}`` → 3 buckets (small/medium/large)
  axis 3: bucket of ``m_log_range / σ̂_{range, train}`` → 2 buckets (narrow/wide)
  axis 4: sign of ``m_ofi_tickrule`` with null-band → 3 buckets (buy/sell/balanced)

Cross-product = 2 × 3 × 2 × 3 = 36 raw cells.

The 36 raw cells are collapsed to ``K`` archetypes via iterative sparse-
cell merging per design.md §4.5.1: at each step, the lowest-count cell
is merged into its nearest **non-sparse** neighbour by Hamming distance
over the 4-axis encoding. Non-sparseness is anchored at
``cochran_n_min = max(30, ⌈K · 5 / 0.8⌉)`` per design.md §4.5.1's
``N_min = max(30, n_min_chi2)`` clause (see ``_compute_cochran_n_min``
docstring for the n_min_chi2 derivation). When no non-sparse neighbour
exists at any Hamming distance (degenerate small-fold case), the merge
fails-safe to the largest-count active cell with a logged warning.
Iteration stops when exactly ``K`` cells remain.

Cochran's 1954 expected-cell-count rule is then *re-applied* to the
post-merge K cells as an **operational power proxy** on observed
training-fold counts. Note: Cochran's strict reading is a
small-expected-frequency guideline for χ² goodness-of-fit under H0
(Cochran 1954 §3); applied here to observed counts it is a conservative
sparse-cell guard, not the inferential anchor for the §4.5.3 bootstrap
empirical-frequency CIs (those CIs are stationary-bootstrap percentile
CIs whose adequacy criterion is per-cell sample count for the binomial
proportion CI, e.g. Brown-Cai-DasGupta 2001's ``np(1-p) ≥ 5`` for the
Wilson interval). Re-anchoring to a binomial-CI rule is tracked under
``P1-H053-ARCHETYPE-COCHRAN-OBSERVED-COUNT-REANCHOR``.

Per design.md §4.5.1, ``K`` is CV-tuned by the orchestrator from
``{3, 5, 7, 9}``; this module does NOT do the CV — it accepts ``K`` as
a fit-time parameter. Per-fold quantile thresholds and the resulting
``ArchetypeRule`` are persisted to
``logs/reproducibility/{run_id}_archetype_thresholds.json`` per
design.md §11 line 417.

References
----------
- Cochran, W. G. 1954. "Some Methods for Strengthening the Common χ²
  Tests." *Biometrics* 10(4):417-451.
  [DOI 10.2307/3001616](https://doi.org/10.2307/3001616). Source of
  the (≥5, 80%-of-cells) and (≥1, all-cells) rules; section pin to be
  verified against a primary copy under
  ``P1-H053-COCHRAN-SECTION-PIN-VERIFY``.
- Brown, L. D., Cai, T. T., & DasGupta, A. 2001. "Interval Estimation
  for a Binomial Proportion." *Statistical Science* 16(2):101-133.
  [DOI 10.1214/ss/1009213286](https://doi.org/10.1214/ss/1009213286).
  The Wilson-interval adequacy criterion is the methodologically
  appropriate anchor for the §4.5.3 empirical-frequency CIs.
- Wilson, D. R. & Martinez, T. R. 1997. "Improved Heterogeneous
  Distance Functions." *Journal of Artificial Intelligence Research*
  6:1-34. [DOI 10.1613/jair.346](https://doi.org/10.1613/jair.346).
  Background on Hamming-vs-VDM trade-offs for unordered categoricals;
  the OOD-cell nearest-Hamming fallback is an operational choice, not
  a Wilson-Martinez recommendation. Tracked under
  ``P1-H053-ARCHETYPE-OOD-FALLBACK-METRIC``.
- H053 design.md §4.5.1 + §4.5.3.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

_log = logging.getLogger(__name__)

_NAME = "h053_archetype_classifier"
_VERSION = "1.0"


# Quintile boundaries for the 4-axis encoding.
# operational-choice: "small/medium/large" 3-bucket partition uses q20 and q80
# boundaries (the lowest and highest quintiles); medium = middle 60%. design.md
# §4.5.1 names the partition "small/medium/large" with the word "Quintile" but
# does NOT specify whether to use q20/q80 (lower+upper quintile bounds) or
# q33/q67 (terciles). q20/q80 is one defensible reading; the choice is tracked
# under follow-up `P1-H053-ARCHETYPE-QUANTILE-BOUNDARY-ADDENDUM` for design.md
# binding (either by addendum pin or inner-WF Brier-score sweep).
_SIZE_Q_LO: float = 0.20
_SIZE_Q_HI: float = 0.80
# operational-choice: "narrow/wide" 2-bucket partition uses median (q50) split.
# design.md §4.5.1 says "Quintile of m_log_range / σ̂_range: narrow/wide" — the
# word "Quintile" is the 5-fold partition, but a 2-bucket partition naturally
# reads as the median split. Tracked alongside the size-axis choice above.
_WIDE_Q: float = 0.50
# operational-choice: OFI tick-rule "balanced" null-band uses |ofi| < 5% of
# training-fold σ̂_ofi as the dead-zone threshold. design.md §4.5.1 names
# "balanced (tick-rule null-band)" without a numerical bound; 5% is the
# implementation choice. For std-normal OFI, P(|X| < 0.05·σ) ≈ 4%, which puts
# the balanced bucket at near-empty mass — likely Cochran-marginal at K=9 on
# shorter training folds. The Hasbrouck 1991 (DOI 10.1111/j.1540-6261.1991.
# tb03749.x) "null-band" precedent does not pin a numerical bound either.
# Tracked under `P1-H053-ARCHETYPE-OFI-NULL-BAND-EMPIRICAL` (PROMOTED to
# BLOCKING-BEFORE-H053-LAUNCH per quant-audit F-1-5).
_OFI_NULL_BAND_FRAC: float = 0.05

# Cochran 1954 expected-cell-count rule (operational power proxy).
# justify: (≥5 for ≥80% of cells; ≥1 for all cells) is the canonical
# secondary-source statement of the rule (Conover 1999 §4.1, Agresti 2013
# §1.4). The strict primary-source reading (Cochran 1954 §3) is on
# *expected* counts under H0, not observed counts; we apply it here to
# observed training-fold counts as a conservative sparse-cell guard for
# the §4.5.3 bootstrap empirical-frequency CIs. Re-anchoring to the
# methodologically appropriate Brown-Cai-DasGupta 2001 binomial-proportion
# adequacy rule (np(1-p) ≥ 5 for Wilson interval) tracked under
# `P1-H053-ARCHETYPE-COCHRAN-OBSERVED-COUNT-REANCHOR`.
_COCHRAN_HIGH_CELL_FRAC: float = 0.80   # at least 80% of cells must have ≥5 count
_COCHRAN_HIGH_THRESHOLD: int = 5
_COCHRAN_LOW_THRESHOLD: int = 1         # all cells must have ≥1 count

# Default sparse-cell floor for non-sparseness anchoring during merging.
# justify: design.md §4.5.1 specifies `N_min = max(30, n_min_chi2)` where
# `n_min_chi2` is the Cochran-derived floor on TOTAL N for K cells. The
# "30" is the operational lower bound; n_min_chi2 dominates at larger K.
# See `_compute_cochran_n_min(K)`.
_SPARSE_CELL_FLOOR: int = 30


# 4-axis cell key: (sign_return, size_return, wide_range, sign_ofi)
# encoded as ints in {0,1} × {0,1,2} × {0,1} × {0,1,2}.
#
# Tiebreak coupling note (per quant-audit F-1-9): the merge-loop
# tiebreaks use lexicographic CellKey ordering, which by definition
# is axis-encoding order (axis 1 first, then axis 2, ...). Reordering
# axes in `_classify_axes` therefore changes archetype-fit outputs
# under tie conditions and is a breaking change to this contract.
CellKey = tuple[int, int, int, int]


def _compute_cochran_n_min(K: int) -> int:
    """Compute the design.md §4.5.1 ``N_min = max(30, n_min_chi2)`` floor.

    For the (≥5, 80%-of-cells) rule with K post-merge cells, equally
    distributed counts demand at least ``n_min_chi2 = ⌈K · 5 / 0.8⌉``
    total observations. K=5 → 32, K=7 → 44, K=9 → 57; in each case the
    Cochran-derived floor is ≥30 once K ≥ 5, so K=3 reduces to the 30 floor.

    Reference: Cochran 1954 §3 (DOI 10.2307/3001616); design.md §4.5.1
    line 220 "N_min = max(30, n_min_chi2)".
    """
    n_min_chi2 = math.ceil(K * _COCHRAN_HIGH_THRESHOLD / _COCHRAN_HIGH_CELL_FRAC)
    return max(_SPARSE_CELL_FLOOR, n_min_chi2)


def _frame_sha256_canonical(panel: pl.DataFrame) -> str:
    """Compute a deterministic SHA256 hash of the mediator training panel.

    Used to bind the fitted ``ArchetypeRule`` to the exact panel it was
    fit on, providing a defence against silent panel-drift between fit
    and apply (e.g., orchestrator wiring errors that cross PIT bounds).

    Implementation: serialise to Arrow IPC stream over a sorted-column
    schema (deterministic across Polars versions); SHA256 the bytes.
    """
    cols = sorted(panel.columns)
    canonical = panel.select(cols)
    buf = canonical.write_ipc(file=None, compression="uncompressed")
    return hashlib.sha256(buf.getvalue()).hexdigest()


@dataclass(frozen=True)
class ArchetypeRule:
    """Frozen archetype-assignment rule fitted on a training fold.

    Pre-fold reproducibility: serializable to JSON (sidecar) and re-loadable
    for OOS application without re-fitting.
    """

    K: int                              # number of archetypes after collapse
    train_sigma_15min: float            # σ̂ of |m_return| from training fold
    train_sigma_range: float            # σ̂ of m_log_range from training fold
    train_sigma_ofi: float              # σ̂ of |m_ofi_tickrule| from training fold
    abs_return_q20: float               # quintile-20 of |m_return| / σ̂_15min
    abs_return_q80: float               # quintile-80 of same
    log_range_q50: float                # median of m_log_range / σ̂_range
    cell_to_archetype: dict[str, int]   # JSON-friendly: "1,0,1,2" → archetype id
    raw_cell_counts: dict[str, int]     # raw 36-cell counts pre-merge
    n_train_sessions: int               # |training fold|
    cochran_n_min: int                  # max(30, ⌈K·5/0.8⌉) — non-sparseness anchor
    train_panel_checksum: str           # SHA256 of the training panel (PIT contract)

    def to_dict(self) -> dict:
        return asdict(self)


def _encode_cell_key(key: CellKey) -> str:
    """Encode 4-tuple as comma-separated string (JSON-friendly key)."""
    return f"{key[0]},{key[1]},{key[2]},{key[3]}"


def _decode_cell_key(s: str) -> CellKey:
    parts = s.split(",")
    return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))


def _hamming_distance(a: CellKey, b: CellKey) -> int:
    """Hamming distance over the 4-axis encoding."""
    return sum(1 for i in range(4) if a[i] != b[i])


def _classify_axes(
    mediator: pl.DataFrame,
    train_sigma_15min: float,
    train_sigma_range: float,
    train_sigma_ofi: float,
    abs_return_q20: float,
    abs_return_q80: float,
    log_range_q50: float,
) -> pl.DataFrame:
    """Encode each row's 4-axis cell key columns: _ax1..ax4."""
    return mediator.with_columns(
        # axis 1: sign of m_return (1 = positive, 0 = non-positive)
        (pl.col("m_return") > 0).cast(pl.Int32).alias("_ax1"),
        # axis 2: bucket of |m_return| / σ̂_15min using train q20/q80 boundaries
        # 0 = small (≤ q20), 1 = medium (q20 < x ≤ q80), 2 = large (> q80)
        (
            pl.when(
                (pl.col("m_return").abs() / train_sigma_15min) <= abs_return_q20
            )
            .then(0)
            .when(
                (pl.col("m_return").abs() / train_sigma_15min) <= abs_return_q80
            )
            .then(1)
            .otherwise(2)
            .alias("_ax2")
        ),
        # axis 3: bucket of m_log_range / σ̂_range using train median (q50)
        # 0 = narrow (≤ q50), 1 = wide (> q50)
        (
            pl.when((pl.col("m_log_range") / train_sigma_range) <= log_range_q50)
            .then(0)
            .otherwise(1)
            .alias("_ax3")
        ),
        # axis 4: sign of m_ofi_tickrule with null-band
        # 0 = balanced (|ofi| < null-band), 1 = buy (ofi > null-band), 2 = sell (ofi < -null-band)
        (
            pl.when(
                pl.col("m_ofi_tickrule").abs()
                < _OFI_NULL_BAND_FRAC * train_sigma_ofi
            )
            .then(0)
            .when(pl.col("m_ofi_tickrule") > 0)
            .then(1)
            .otherwise(2)
            .alias("_ax4")
        ),
    )


def _verify_cochran_rule(cell_counts: list[int]) -> tuple[bool, str]:
    """Verify Cochran 1954 expected-cell-count rule on K final cells.

    Returns (ok, reason). reason is empty if ok=True.
    """
    K = len(cell_counts)
    if K == 0:
        return False, "Cochran check: zero cells"
    high_cells = sum(1 for c in cell_counts if c >= _COCHRAN_HIGH_THRESHOLD)
    high_frac = high_cells / K
    low_violations = [c for c in cell_counts if c < _COCHRAN_LOW_THRESHOLD]
    if low_violations:
        return False, (
            f"Cochran check: {len(low_violations)} cells with count < "
            f"{_COCHRAN_LOW_THRESHOLD}; rule requires all cells ≥ "
            f"{_COCHRAN_LOW_THRESHOLD}"
        )
    if high_frac < _COCHRAN_HIGH_CELL_FRAC:
        return False, (
            f"Cochran check: {high_cells}/{K} cells have count ≥ "
            f"{_COCHRAN_HIGH_THRESHOLD} ({high_frac:.0%}); rule requires "
            f"≥{_COCHRAN_HIGH_CELL_FRAC:.0%}"
        )
    return True, ""


def fit_archetype_rule(
    mediator_train: pl.DataFrame,
    *,
    K: int,
) -> ArchetypeRule:
    """Fit archetype rule on training-fold mediator output panel.

    The training panel must have columns ``m_return``, ``m_log_range``,
    ``m_volume``, ``m_ofi_tickrule`` (the H053Mediator output schema).
    Other columns are ignored.

    Parameters
    ----------
    mediator_train : pl.DataFrame
        Training-fold mediator panel (one row per (symbol, session)).
        PIT contract: this panel must contain only training-fold data;
        the resulting rule captures ``train_panel_checksum`` so that
        downstream OOS application via ``apply_archetype_rule`` can be
        bound to the exact training panel by orchestrator integration
        tests.
    K : int
        Target number of archetypes after sparse-cell collapsing. Must
        be in design.md §4.5.1's CV grid {3, 5, 7, 9}; the orchestrator
        selects K via OOS Brier score on inner walk-forward folds.

    Returns
    -------
    ArchetypeRule
        Frozen rule capturing all parameters needed to reproduce the
        archetype assignment on OOS data.

    Raises
    ------
    ValueError
        If the training panel is empty, has zero variance in any of
        the three mediator-scale features, has fewer than ``K``
        distinct cells, has degenerate q20==q80 (collapsed size axis),
        or the post-merge K cells fail Cochran's rule.

    Notes
    -----
    Scale-parameter convention (operational pin per quant-audit F-1-12):
    σ̂_15min = std(|m_return|) (half-normal scaling); σ̂_range = std(m_log_range)
    (m_log_range from the GK estimator is non-negative by construction);
    σ̂_ofi = std(|m_ofi_tickrule|) (half-normal scaling). This is an
    asymmetric convention vs std-of-raw on m_log_range — pinned here for
    reproducibility, tracked under
    ``P1-H053-ARCHETYPE-SIGMA-CONVENTION-RECONCILE`` for design.md amendment.
    """
    if K < 2:
        raise ValueError(f"K must be >= 2; got {K}")
    n_train = len(mediator_train)
    if n_train == 0:
        raise ValueError("Training-fold mediator panel is empty")

    # Step 1: compute training-fold scale parameters σ̂. See Notes for the
    # std-of-abs vs std-of-raw convention pin.
    sigma_15min = float(mediator_train["m_return"].abs().std(ddof=1))
    sigma_range = float(mediator_train["m_log_range"].std(ddof=1))
    sigma_ofi = float(mediator_train["m_ofi_tickrule"].abs().std(ddof=1))
    if sigma_15min <= 0 or sigma_range <= 0 or sigma_ofi <= 0:
        raise ValueError(
            "Training-fold has zero variance in one of the mediator features; "
            "cannot fit archetype rule."
        )

    # Step 2: compute quintile boundaries on standardized features.
    abs_return_std = (mediator_train["m_return"].abs() / sigma_15min)
    log_range_std = (mediator_train["m_log_range"] / sigma_range)
    abs_return_q20 = float(abs_return_std.quantile(_SIZE_Q_LO))
    abs_return_q80 = float(abs_return_std.quantile(_SIZE_Q_HI))
    log_range_q50 = float(log_range_std.quantile(_WIDE_Q))
    # Degenerate-distribution guard (quant-audit F-1-7): if q20 == q80, the
    # 3-bucket size axis collapses to ≤ 2 buckets and downstream merging
    # behaves unpredictably. Reject explicitly.
    if abs_return_q20 >= abs_return_q80:
        raise ValueError(
            f"Degenerate |m_return| distribution: q20={abs_return_q20:.6g} "
            f">= q80={abs_return_q80:.6g}; size-axis 3-bucket partition "
            "collapses. Increase training fold size or check input panel."
        )

    # Step 3: encode every training row to a 4-axis cell key.
    classified = _classify_axes(
        mediator_train,
        sigma_15min,
        sigma_range,
        sigma_ofi,
        abs_return_q20,
        abs_return_q80,
        log_range_q50,
    )
    cell_counts_df = (
        classified.group_by(["_ax1", "_ax2", "_ax3", "_ax4"], maintain_order=False)
        .len()
        .rename({"len": "count"})
    )
    # Polars group_by does not guarantee stable key ordering; sort by CellKey
    # ascending so the initial archetype-id enumeration is deterministic
    # across runs (required for reproducibility).
    sorted_rows = sorted(
        (
            (
                (int(r["_ax1"]), int(r["_ax2"]), int(r["_ax3"]), int(r["_ax4"])),
                int(r["count"]),
            )
            for r in cell_counts_df.iter_rows(named=True)
        ),
        key=lambda kv: kv[0],
    )
    raw_cell_counts: dict[CellKey, int] = {key: cnt for key, cnt in sorted_rows}

    if len(raw_cell_counts) < K:
        raise ValueError(
            f"Training fold produced {len(raw_cell_counts)} distinct cells; "
            f"cannot collapse to K={K}."
        )

    # Step 4: iteratively merge the smallest-count cell into its nearest
    # **non-sparse** neighbour until exactly K cells remain (per design.md
    # §4.5.1: "aggregating sparse cells into the nearest non-sparse cell").
    # Non-sparseness anchored at `cochran_n_min = max(30, ⌈K·5/0.8⌉)` per
    # design.md §4.5.1's `N_min = max(30, n_min_chi2)` clause.
    #
    # Fail-safe: if no non-sparse active cell exists at any Hamming distance
    # (degenerate small-fold case where every cell is sparse), the merge
    # falls back to the largest-count active cell with a logged warning.
    # This keeps the algorithm progressing toward the K-cell terminal state
    # rather than deadlocking.
    #
    # Tiebreaking: when multiple cells share the same count, the
    # lexicographically-smallest CellKey wins (deterministic across runs).
    # When multiple cells share (Hamming, count) for nearest, ascending
    # CellKey wins. Note (per quant-audit F-1-9): lex order is
    # axis-encoding order — reordering axes in `_classify_axes` is a
    # breaking change to the archetype-fit contract.
    cochran_n_min = _compute_cochran_n_min(K)

    cell_archetype: dict[CellKey, int] = {key: i for i, key in enumerate(raw_cell_counts.keys())}
    active_keys: set[CellKey] = set(cell_archetype.keys())
    active_counts = dict(raw_cell_counts)

    while len(active_keys) > K:
        # Find the cell with the smallest count (tiebreak by CellKey ascending).
        min_key = min(active_keys, key=lambda k: (active_counts[k], k))
        # Restrict candidates to non-sparse cells (count >= cochran_n_min)
        # excluding min_key itself, per design.md §4.5.1.
        non_sparse_candidates = [
            k for k in active_keys
            if k != min_key and active_counts[k] >= cochran_n_min
        ]
        if non_sparse_candidates:
            nearest = min(
                non_sparse_candidates,
                key=lambda k: (_hamming_distance(min_key, k), -active_counts[k], k),
            )
        else:
            # Fail-safe: no non-sparse neighbour exists; merge into the
            # largest-count active cell (any active cell except min_key).
            # Tiebreak: smallest CellKey for determinism.
            fallback_candidates = [k for k in active_keys if k != min_key]
            nearest = min(
                fallback_candidates,
                key=lambda k: (-active_counts[k], k),
            )
            _log.warning(
                "fit_archetype_rule: no non-sparse cell (count >= %d) "
                "available as merge target for cell %s (count %d); "
                "falling back to largest-count active cell %s (count %d). "
                "Consider lowering K or increasing training fold size.",
                cochran_n_min,
                min_key,
                active_counts[min_key],
                nearest,
                active_counts[nearest],
            )
        # Merge min_key into nearest: all rows currently assigned to min_key's
        # archetype id (which includes min_key itself plus any cells previously
        # merged into min_key's group) inherit nearest's archetype id.
        # Capture the source id BEFORE the rewrite — otherwise mid-loop the
        # comparison would flip to nearest's id and orphan downstream cells.
        old_id = cell_archetype[min_key]
        merged_id = cell_archetype[nearest]
        for key in list(cell_archetype.keys()):
            if cell_archetype[key] == old_id:
                cell_archetype[key] = merged_id
        active_counts[nearest] += active_counts[min_key]
        del active_counts[min_key]
        active_keys.remove(min_key)

    # Step 5: re-number archetype ids to be contiguous {0..K-1}
    unique_ids = sorted(set(cell_archetype.values()))
    id_remap = {old: new for new, old in enumerate(unique_ids)}
    cell_to_archetype: dict[str, int] = {
        _encode_cell_key(k): id_remap[v] for k, v in cell_archetype.items()
    }

    # Step 6: verify Cochran's rule on the final K archetype cells.
    final_cell_counts: dict[int, int] = {}
    for key, cnt in raw_cell_counts.items():
        aid = cell_to_archetype[_encode_cell_key(key)]
        final_cell_counts[aid] = final_cell_counts.get(aid, 0) + cnt
    final_counts_list = list(final_cell_counts.values())
    ok, reason = _verify_cochran_rule(final_counts_list)
    if not ok:
        raise ValueError(
            f"Post-merge K={K} cells fail Cochran 1954 expected-cell-count rule: "
            f"{reason}. Try smaller K or larger training fold."
        )

    # Step 7: capture the SHA256 checksum of the training panel for the
    # PIT contract (quant-audit F-1-8). The checksum lets downstream
    # orchestrator integration tests verify that `apply_archetype_rule`
    # is being called on a panel disjoint from the fitting panel.
    train_panel_checksum = _frame_sha256_canonical(mediator_train)

    return ArchetypeRule(
        K=K,
        train_sigma_15min=sigma_15min,
        train_sigma_range=sigma_range,
        train_sigma_ofi=sigma_ofi,
        abs_return_q20=abs_return_q20,
        abs_return_q80=abs_return_q80,
        log_range_q50=log_range_q50,
        cell_to_archetype=cell_to_archetype,
        raw_cell_counts={_encode_cell_key(k): v for k, v in raw_cell_counts.items()},
        n_train_sessions=n_train,
        cochran_n_min=cochran_n_min,
        train_panel_checksum=train_panel_checksum,
    )


_REQUIRED_MEDIATOR_COLS: tuple[str, ...] = (
    "m_return",
    "m_log_range",
    "m_volume",
    "m_ofi_tickrule",
)


def apply_archetype_rule(
    mediator: pl.DataFrame,
    rule: ArchetypeRule,
) -> pl.DataFrame:
    """Apply a fitted archetype rule to a mediator panel.

    Returns the input DataFrame with an added ``archetype_id`` column
    (Int32, ∈ {0..K-1}).

    OOD handling (per quant-audit F-1-6): rows whose 4-axis cell is
    unseen at training time are assigned the archetype_id of the
    nearest training cell by plain (unweighted) Hamming distance over
    the 4-axis encoding. This is an **operational choice**, not a
    theory-backed metric: the 4-axis encoding mixes ordinal axes (size,
    wide) with unordered axes (sign return, sign ofi); plain Hamming
    treats all axes uniformly. The Wilson & Martinez 1997 (DOI
    10.1613/jair.346) HEOM/HVDM family would be more principled for
    mixed-type categoricals but requires per-axis distance fitting; the
    nearest-Hamming choice is tracked for review under
    ``P1-H053-ARCHETYPE-OOD-FALLBACK-METRIC``.

    Raises
    ------
    ValueError
        If the input panel is missing any of the four required mediator
        columns.
    """
    missing = [c for c in _REQUIRED_MEDIATOR_COLS if c not in mediator.columns]
    if missing:
        raise ValueError(
            f"apply_archetype_rule: input panel is missing required "
            f"mediator columns {missing}; expected all of "
            f"{list(_REQUIRED_MEDIATOR_COLS)}."
        )
    classified = _classify_axes(
        mediator,
        rule.train_sigma_15min,
        rule.train_sigma_range,
        rule.train_sigma_ofi,
        rule.abs_return_q20,
        rule.abs_return_q80,
        rule.log_range_q50,
    )

    # For each row, look up the cell key and map to archetype_id; fall back
    # to nearest-training-cell-by-Hamming for unseen cells.
    train_cells = [_decode_cell_key(s) for s in rule.cell_to_archetype.keys()]

    def _lookup(ax1: int, ax2: int, ax3: int, ax4: int) -> int:
        key = (ax1, ax2, ax3, ax4)
        encoded = _encode_cell_key(key)
        if encoded in rule.cell_to_archetype:
            return rule.cell_to_archetype[encoded]
        # Out-of-distribution: nearest training cell by Hamming distance
        nearest = min(
            train_cells, key=lambda c: (_hamming_distance(key, c), c)
        )
        return rule.cell_to_archetype[_encode_cell_key(nearest)]

    archetype_ids = [
        _lookup(int(r["_ax1"]), int(r["_ax2"]), int(r["_ax3"]), int(r["_ax4"]))
        for r in classified.iter_rows(named=True)
    ]
    return mediator.with_columns(
        pl.Series("archetype_id", archetype_ids, dtype=pl.Int32)
    )


def write_archetype_rule_sidecar(
    rule: ArchetypeRule,
    repro_log_dir: Path,
    run_id: str,
) -> tuple[Path, str]:
    """Persist the ArchetypeRule as JSON sidecar; return ``(path, sha256)``.

    Per H053 design.md §11 line 417, the sidecar lives at
    ``logs/reproducibility/{run_id}_archetype_thresholds.json``. The
    in-module docstring previously referred to it as
    ``ReproLog.archetype_thresholds_{run_id}.json``; the canonical
    spelling is now the design.md §11 line 417 form.

    Returns the path written AND the SHA256 of the canonical payload so
    callers can wire it into ``ReproLog.model_hash`` via the project
    ``with_model_hash`` helper (mirrors the H050 cycle-3 + cycle-4
    sidecar pattern). Orchestrator integration is tracked under
    ``P1-H053-ARCHETYPE-SIDECAR-MODEL-HASH-WIRING``.

    Atomic write: payload first written to ``.tmp`` sibling, then
    ``os.replace``-d to final path.
    """
    import os

    repro_log_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = repro_log_dir / f"{run_id}_archetype_thresholds.json"
    tmp_path = sidecar_path.with_suffix(".json.tmp")
    payload = {
        "archetype_rule": rule.to_dict(),
        "_meta": {
            "written_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
        },
    }
    # Binary-mode write: avoids Windows CRLF translation, so the SHA256 of
    # the in-memory serialised payload matches the SHA256 of the on-disk
    # bytes byte-for-byte.
    serialised_bytes = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    with tmp_path.open("wb") as fh:
        fh.write(serialised_bytes)
    os.replace(tmp_path, sidecar_path)
    sidecar_sha256 = hashlib.sha256(serialised_bytes).hexdigest()
    return sidecar_path, sidecar_sha256


__all__ = [
    "ArchetypeRule",
    "apply_archetype_rule",
    "fit_archetype_rule",
    "write_archetype_rule_sidecar",
]
