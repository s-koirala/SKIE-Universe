"""Return-convention conversions: log <-> arithmetic.

Bound by H050 cross-symbol aggregation-rule addendum r2 §5.1
([research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md)):
the per-symbol per-bar log return ``r_i(t) = log(close_i[t]) - log(close_i[t-1])``
must be converted to an arithmetic per-bar return
``R_i(t) = exp(r_i(t)) - 1`` before any cross-asset weighted-sum
aggregation, because the weighted-sum portfolio identity
``R_p = w_1 R_1 + w_2 R_2`` is exact only in arithmetic-return space.

Reference
---------
Campbell, J. Y.; Lo, A. W.; MacKinlay, A. C. 1997. *The Econometrics
of Financial Markets.* Princeton University Press.
ISBN 978-0-691-04301-2; doi:10.1515/9781400830213. §1.4
"Continuously compounded returns" — log returns aggregate exactly
across time but **not** across assets, while arithmetic returns
aggregate exactly across assets but not across time.

This module is consumed by the dual-symbol orchestrator under follow-up
``P1-H050-DUAL-SYMBOL-ORCHESTRATOR`` and by the verification gate
under follow-up ``P1-H050-AGGREGATION-CONVENTION-TEST``
(addendum §5.2).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def log_to_arithmetic(r: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert a per-bar log-return series to per-bar arithmetic returns.

    For each element of ``r``, returns ``exp(r) - 1``. The transformation
    is element-wise, deterministic, and non-stochastic; with float64
    inputs the round-trip ``arithmetic_to_log(log_to_arithmetic(r))`` is
    exact to within float64 unit roundoff (~2.22e-16 per Goldberg 1991,
    *ACM Comput. Surv.* 23(1):5-48, doi:10.1145/103162.103163, §2).

    The implementation uses :func:`numpy.expm1`, which computes
    ``exp(r) - 1`` in a numerically-stable way that avoids catastrophic
    cancellation for small ``|r|`` (cf. Goldberg 1991 §3.2 on subtraction
    of nearly-equal quantities). For 1-min ES/NQ-scale log-returns
    (``|r|`` ~ 1e-3), naive ``np.exp(r) - 1`` would lose ~3 decimal
    digits of precision; ``np.expm1`` is accurate to ~1 ulp throughout
    the small-r regime.

    Parameters
    ----------
    r
        1-D float64 array of per-bar log returns.

    Returns
    -------
    NDArray[np.float64]
        1-D float64 array of per-bar arithmetic returns of identical
        shape. NaN entries propagate (``exp(NaN) - 1 = NaN``).
    """
    arr = np.asarray(r, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(
            f"log_to_arithmetic expects 1-D input; got ndim={arr.ndim}"
        )
    return np.expm1(arr)


def arithmetic_to_log(r: NDArray[np.float64]) -> NDArray[np.float64]:
    """Inverse of :func:`log_to_arithmetic`: ``log(1 + R)``.

    Parameters
    ----------
    r
        1-D float64 array of per-bar arithmetic returns. Each element
        must be > -1 (a -100% bar wipes out price; ``log(0)`` is
        undefined).

    Returns
    -------
    NDArray[np.float64]
        1-D float64 array of per-bar log returns.
    """
    arr = np.asarray(r, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(
            f"arithmetic_to_log expects 1-D input; got ndim={arr.ndim}"
        )
    return np.log1p(arr)


__all__ = ["arithmetic_to_log", "log_to_arithmetic"]
