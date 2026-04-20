"""Distribution-stability monitoring (plan section 2.1).

Per-day KS test vs trailing reference window. Alert when the null
hypothesis of identical distributions is rejected at a stringent
threshold, signalling potential data-quality drift or vendor change.

Multiple-testing correction: Benjamini-Hochberg (1995) FDR procedure
applied across all tested columns.

Reference:
    Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery
    rate: a practical and powerful approach to multiple testing.
    *Journal of the Royal Statistical Society: Series B*, 57(1), 289-300.
    DOI: 10.1111/j.2517-6161.1995.tb02031.x
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl
from scipy import stats

# justify: plan §2.1 "Open items for Phase 1" table (O-11);
# subject to empirical FDR calibration.
_DEFAULT_KS_THRESHOLD: float = 1e-6

# Minimum sample size for a two-sample KS test to be meaningful.
# With n < 2, the empirical CDF is degenerate and scipy.stats.ks_2samp
# returns undefined results.
_MIN_SAMPLE_SIZE = 2


@dataclass(frozen=True)
class DriftAlert:
    """Record of a distribution-stability failure."""

    column: str
    ks_statistic: float
    p_value: float
    p_value_adj: float
    threshold: float
    n_current: int
    n_reference: int


def check_distribution_stability(
    current: pl.DataFrame,
    reference: pl.DataFrame,
    numeric_cols: list[str],
    threshold: float = _DEFAULT_KS_THRESHOLD,  # plan §2.1; O-11 FDR calibration
) -> list[DriftAlert]:
    """Two-sample KS test per column with Benjamini-Hochberg FDR correction.

    For each numeric column, a two-sample Kolmogorov-Smirnov test is run
    between *current* and *reference*. Raw p-values are then adjusted
    across all tested columns using the Benjamini-Hochberg (1995) step-up
    procedure: sort p-values, compute p_adj = p * n_cols / rank, and
    compare the adjusted p against *threshold*.

    Parameters
    ----------
    current
        Today's data slice (polars DataFrame).
    reference
        Trailing reference window (e.g., 30 trading days).
    numeric_cols
        Columns to test. Non-numeric or all-null columns are skipped
        with a warning (logged, not raised).
    threshold
        BH-adjusted p-value below which a ``DriftAlert`` is emitted.

    Returns
    -------
    list[DriftAlert]
        One entry per column that failed the stability check after
        BH correction. Empty list means all columns passed.

    References
    ----------
    Benjamini, Y. & Hochberg, Y. (1995). DOI: 10.1111/j.2517-6161.1995.tb02031.x
    """
    # Collect raw KS results per column.
    raw_results: list[tuple[str, float, float, int, int]] = []

    for col in numeric_cols:
        if col not in current.columns or col not in reference.columns:
            continue

        cur_series = current[col].drop_nulls().to_list()
        ref_series = reference[col].drop_nulls().to_list()

        if len(cur_series) < _MIN_SAMPLE_SIZE or len(ref_series) < _MIN_SAMPLE_SIZE:
            continue

        ks_stat, p_val = stats.ks_2samp(cur_series, ref_series)
        raw_results.append((col, ks_stat, p_val, len(cur_series), len(ref_series)))

    if not raw_results:
        return []

    # Benjamini-Hochberg step-up procedure.
    n_tests = len(raw_results)
    # Sort by raw p-value ascending.
    sorted_results = sorted(raw_results, key=lambda r: r[2])

    # Compute adjusted p-values: p_adj = p * n_tests / rank (1-indexed).
    # Enforce monotonicity from the bottom up (cumulative minimum in reverse).
    p_adj_values: list[float] = []
    for rank_1based, (_col, _ks, p_val, _nc, _nr) in enumerate(sorted_results, 1):
        p_adj_values.append(p_val * n_tests / rank_1based)

    # Enforce monotonicity: working backwards, each p_adj must be
    # <= the one after it (step-up property).
    for i in range(len(p_adj_values) - 2, -1, -1):
        p_adj_values[i] = min(p_adj_values[i], p_adj_values[i + 1])

    # Cap at 1.0.
    p_adj_values = [min(p, 1.0) for p in p_adj_values]

    # Build alerts for columns where adjusted p < threshold.
    alerts: list[DriftAlert] = []
    for (col, ks_stat, p_val, n_cur, n_ref), p_adj in zip(
        sorted_results, p_adj_values, strict=True
    ):
        if p_adj < threshold:
            alerts.append(
                DriftAlert(
                    column=col,
                    ks_statistic=ks_stat,
                    p_value=p_val,
                    p_value_adj=p_adj,
                    threshold=threshold,
                    n_current=n_cur,
                    n_reference=n_ref,
                )
            )

    return alerts
