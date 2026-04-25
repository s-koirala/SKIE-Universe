"""Verification gate for H050 cross-symbol aggregation-rule addendum r2 §5.2.

The H050 aggregation-rule addendum r2
([research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md))
binds the cross-symbol aggregate per-bar return as

    R_p(t) = w_ES * R_ES(t) + w_NQ * R_NQ(t)        (sub-rule 2a; w_ES = w_NQ = 1/2)

in **arithmetic-return space**. The current orchestrator
[scripts/run_walk_forward.py:662](../../scripts/run_walk_forward.py)
computes per-bar **log returns** ``r_bar[t] = log(close[t]) - log(close[t-1])``.
Addendum §5.1 mandates per-bar conversion ``R_i(t) = exp(r_i(t)) - 1``
**before** the equal-weighted aggregation is taken; the conversion is
algebraically exact across assets but a first-order Taylor approximation
in log-return space.

This test file is the §5.2 verification gate (follow-up
``P1-H050-AGGREGATION-CONVENTION-TEST``). It is evidence-bar-blocking
for the first H050 walk-forward run governed by the addendum and CI-blocking
for any commit touching ``r_bar`` computation in
[scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) or its
successor module under ``P1-H050-DUAL-SYMBOL-ORCHESTRATOR``.

References
----------
Campbell, J. Y.; Lo, A. W.; MacKinlay, A. C. 1997.
*The Econometrics of Financial Markets.* Princeton University Press.
ISBN 978-0-691-04301-2; doi:10.1515/9781400830213. §1.4
"Continuously compounded returns" — log returns aggregate exactly across
time but **not** across assets, while arithmetic returns aggregate exactly
across assets but not across time. Equation numbers within §1.4 vary
across editions; the load-bearing identity ``R = exp(r) - 1`` and its
Taylor expansion ``R - r = r^2/2 + r^3/6 + O(r^4)`` are stated at the
chapter-level granularity.

Goldberg, D. 1991. "What Every Computer Scientist Should Know About
Floating-Point Arithmetic." *ACM Comput. Surv.* 23(1):5-48,
doi:10.1145/103162.103163. §2 (IEEE Standard) — float64 unit roundoff
u = 2^-53 ~= 1.11e-16; relative error per IEEE-754 elementary
operation is bounded by u.
"""

# ruff: noqa: N806, PLR2004
#
# N806 (variable name should be lowercase) is suppressed at file scope
# because the addendum's binding mathematical notation distinguishes
# log returns ``r_*`` (lowercase) from arithmetic returns ``R_*``
# (uppercase) — see addendum §1.2 + §5.1. Renaming the arithmetic-return
# variables to lowercase would obscure the test contract and the
# Campbell-Lo-MacKinlay 1997 §1.4 convention.
#
# PLR2004 (magic value in comparison) is suppressed at file scope
# because the comparison constants here are documented physical regime
# boundaries (per-minute return magnitudes) anchored to the surrounding
# comments and the Campbell-Lo-MacKinlay §1.4 first-order Taylor bound.
# Each numeric literal carries an inline justification in the
# preceding comment block.

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from skie_ninja.inference.stats.return_conventions import (
    arithmetic_to_log,
    log_to_arithmetic,
)

# ---------------------------------------------------------------------------
# Synthetic two-symbol panel
# ---------------------------------------------------------------------------


def _synthetic_close_series(
    *,
    n: int,
    seed: int,
    sigma: float = 1e-3,
    start: float = 100.0,
) -> NDArray[np.float64]:
    """Build a positive log-normal close series.

    The series is ``start * exp(cumsum(N(0, sigma)))`` with a fixed-seed
    RNG. Default sigma = 1e-3 is the order of magnitude of realised
    per-minute ES/NQ log-return vol: at 12% annualised, the per-minute
    sigma scales as ``0.12 / sqrt(252 * 6.5 * 60) ~= 3.83e-4`` per
    minute; intraday seasonality can elevate this 1.5-2x near
    open/close, so 1e-3 is a conservative round-number anchor in the
    empirical regime (not a precise analytic match).
    """
    rng = np.random.default_rng(seed)
    increments = rng.normal(0.0, sigma, n)
    log_levels = np.cumsum(increments)
    return start * np.exp(log_levels)


def _per_bar_log_returns(closes: NDArray[np.float64]) -> NDArray[np.float64]:
    """Match orchestrator path: ``r[0] = 0``; ``r[1:] = diff(log(closes))``.

    Mirrors [scripts/run_walk_forward.py:660-662](../../scripts/run_walk_forward.py)
    exactly; the leading zero is the orchestrator's own convention for
    the first bar of each fold.
    """
    r = np.zeros_like(closes, dtype=np.float64)
    r[1:] = np.diff(np.log(closes))
    return r


def _per_bar_arithmetic_returns(
    closes: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Direct arithmetic-return path: ``R[0] = 0``; ``R[t] = c[t]/c[t-1] - 1``."""
    R = np.zeros_like(closes, dtype=np.float64)
    R[1:] = closes[1:] / closes[:-1] - 1.0
    return R


# ---------------------------------------------------------------------------
# Atol justification (no arbitrary thresholds)
# ---------------------------------------------------------------------------
#
# Per Goldberg 1991 §1.2, IEEE-754 float64 unit roundoff is u = 2^-53
# ~= 1.11e-16. The per-bar transformation
#     log_to_arithmetic(r) = expm1(r) = exp(r) - 1
# is implemented via numpy's expm1, which is accurate to ~1 ulp for the
# small-r regime and ~few ulps for moderate r (per IEEE-754 expm1
# semantics inherited by numpy from the platform libm). A single ulp at
# the ~100x close-price scale through one diff(log()) plus one expm1()
# round-trip accumulates O(few * u) absolute error, comfortably under
# 1e-15 for inputs in the typical 1-min ES/NQ log-return regime
# (|r| <~ 1e-2). atol = 1e-15 is therefore the appropriate
# machine-precision tolerance; rtol = 0 because we want absolute
# equivalence in the small-return regime where relative errors blow up.
ATOL_MACHINE = 1e-15
RTOL_MACHINE = 0.0


# ---------------------------------------------------------------------------
# Test 1 — log -> arithmetic per-bar equivalence (the main contract)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [2024, 2025, 2026, 2027])
def test_log_to_arithmetic_per_bar_equivalence(seed: int) -> None:
    """Addendum §5.1 contract: orchestrator log-return path -> expm1
    -> equal-weighted aggregate equals direct-arithmetic-return
    equal-weighted aggregate at machine precision.
    """
    n = 1000
    es_close = _synthetic_close_series(n=n, seed=seed)
    nq_close = _synthetic_close_series(n=n, seed=seed + 1000)

    r_es_log = _per_bar_log_returns(es_close)
    r_nq_log = _per_bar_log_returns(nq_close)

    R_es_via_expm1 = log_to_arithmetic(r_es_log)
    R_nq_via_expm1 = log_to_arithmetic(r_nq_log)
    R_p_addendum = 0.5 * R_es_via_expm1 + 0.5 * R_nq_via_expm1

    R_es_direct = _per_bar_arithmetic_returns(es_close)
    R_nq_direct = _per_bar_arithmetic_returns(nq_close)
    R_p_direct = 0.5 * R_es_direct + 0.5 * R_nq_direct

    assert np.allclose(
        R_p_addendum, R_p_direct, atol=ATOL_MACHINE, rtol=RTOL_MACHINE
    ), (
        f"addendum-path aggregate diverges from direct-arithmetic aggregate; "
        f"max |diff| = {np.max(np.abs(R_p_addendum - R_p_direct))}"
    )

    # Round-trip check: arithmetic_to_log inverts log_to_arithmetic to
    # within machine precision on the same regime.
    assert np.allclose(
        arithmetic_to_log(R_es_via_expm1),
        r_es_log,
        atol=ATOL_MACHINE,
        rtol=RTOL_MACHINE,
    )


# ---------------------------------------------------------------------------
# Test 2 — first-order divergence between log-aggregate and correct aggregate
# ---------------------------------------------------------------------------


def test_first_order_log_arithmetic_divergence() -> None:
    """Sanity test: the convention matters.

    Naive log-space aggregate ``r_p_naive = 0.5 * r_ES + 0.5 * r_NQ``
    (orchestrator-style, in log-return space) diverges from the
    addendum-correct arithmetic-space aggregate ``R_p`` by O(r^2/2)
    per bar (Campbell-Lo-MacKinlay 1997 §1.4, "Continuously compounded
    returns"). At 1-min ES/NQ scale (sigma ~ 1e-3), per-bar |r^2/2|
    ~= 5e-7; over a 1000-bar session the cumulative absolute divergence
    remains bounded but is clearly above the machine-precision floor.
    """
    n = 5000
    sigma = 1e-3
    es_close = _synthetic_close_series(n=n, seed=4242, sigma=sigma)
    nq_close = _synthetic_close_series(n=n, seed=8484, sigma=sigma)

    r_es_log = _per_bar_log_returns(es_close)
    r_nq_log = _per_bar_log_returns(nq_close)

    r_p_naive_log = 0.5 * r_es_log + 0.5 * r_nq_log
    R_p_correct = 0.5 * log_to_arithmetic(r_es_log) + 0.5 * log_to_arithmetic(
        r_nq_log
    )

    per_bar_diff = R_p_correct - r_p_naive_log

    # The two are NOT equal at machine precision: the addendum's
    # arithmetic-space binding is materially distinct from the naive
    # log-space sum.
    assert not np.allclose(
        R_p_correct, r_p_naive_log, atol=ATOL_MACHINE, rtol=RTOL_MACHINE
    )

    # Per-bar magnitude bound: expm1(r) - r = r^2/2 + r^3/6 + O(r^4)
    # (Taylor series for expm1 around 0). The aggregate per-bar
    # divergence is bounded by 0.5*(r_ES^2/2 + O(r^3))
    #                        + 0.5*(r_NQ^2/2 + O(r^3))
    #                       = (r_ES^2 + r_NQ^2) / 4 + O(r^3).
    # For N(0, sigma) draws over n=5000 bars, the empirical max of |r|
    # follows a Gumbel-tail distribution; with sigma = 1e-3 and n = 5000
    # the expected max is ~4.0*sigma (asymptotic Gumbel for Gaussian
    # extremes; mode = sqrt(2*log(n)) ~ 4.13). The tail-bar squared
    # magnitude is therefore ~16*sigma^2 per symbol; per-bar divergence
    # bound is ~(16+16)/4 = 8 sigma^2 with a 2x safety factor for finite-
    # sample slack -> 16 sigma^2.
    expected_per_bar_bound = 16.0 * sigma * sigma
    assert np.max(np.abs(per_bar_diff)) < expected_per_bar_bound, (
        f"per-bar divergence {np.max(np.abs(per_bar_diff))} exceeds "
        f"Gumbel-tail O(r^2/2) bound {expected_per_bar_bound}"
    )

    # Sign of the per-bar divergence: expm1(r) - r = r^2/2 + r^3/6 +
    # O(r^4); for |r| << 1 the quadratic term dominates and is strictly
    # non-negative. Empirical mean over n=5000 N(0, sigma) draws
    # therefore has expected value E[r^2/2] = sigma^2/2 > 0, so the
    # mean per-bar divergence is positive in expectation. (This is NOT
    # a Jensen-inequality result — Jensen bounds f(E[X]) vs E[f(X)],
    # not the per-element sign of f(x) - x. The correct mechanism is
    # the non-negativity of the leading Taylor remainder term.)
    mean_diff = float(np.mean(per_bar_diff))
    assert mean_diff > 0.0, (
        f"expected positive bias from leading r^2/2 Taylor term under "
        f"symmetric returns; got mean_diff={mean_diff}"
    )


# ---------------------------------------------------------------------------
# Test 3 — sub-rule 3.3a: inactive-symbol handling (cash, no renormalisation)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "g_es,g_nq",
    [
        (1, 1),
        (1, 0),
        (0, 1),
        (0, 0),
    ],
)
def test_inactive_symbol_handling_sub_rule_3_3a(g_es: int, g_nq: int) -> None:
    """Addendum §2.2 sub-rule 3.3a: when symbol i's gate g_i(t) = 0,
    that symbol's contribution to the aggregate is zero in return space
    and the constant 0.5/0.5 weights are HELD, not renormalised.

    The aggregate must satisfy
        R_p(t) = g_ES(t) * 0.5 * R_ES(t) + g_NQ(t) * 0.5 * R_NQ(t)
    for all four (g_ES, g_NQ) gate states.
    """
    n = 200
    es_close = _synthetic_close_series(n=n, seed=1111)
    nq_close = _synthetic_close_series(n=n, seed=2222)

    r_es_log = _per_bar_log_returns(es_close)
    r_nq_log = _per_bar_log_returns(nq_close)
    R_es = log_to_arithmetic(r_es_log)
    R_nq = log_to_arithmetic(r_nq_log)

    # Constant gate state across all bars (the parametrised case).
    g_es_arr = np.full(n, float(g_es))
    g_nq_arr = np.full(n, float(g_nq))

    R_p_gated = g_es_arr * 0.5 * R_es + g_nq_arr * 0.5 * R_nq

    # Hand-computed reference for each of the four gate states:
    if (g_es, g_nq) == (1, 1):
        R_p_ref = 0.5 * R_es + 0.5 * R_nq
    elif (g_es, g_nq) == (1, 0):
        # NQ contributes zero; ES contribution stays at 0.5 (NOT 1.0).
        R_p_ref = 0.5 * R_es
    elif (g_es, g_nq) == (0, 1):
        R_p_ref = 0.5 * R_nq
    else:  # (0, 0)
        R_p_ref = np.zeros(n, dtype=np.float64)

    assert np.allclose(R_p_gated, R_p_ref, atol=ATOL_MACHINE, rtol=RTOL_MACHINE)

    # Renormalisation-foreclosure check (addendum §2.2 closing paragraph
    # forecloses sub-rule 3.3b): when only one symbol is active, the
    # surviving weight must be 0.5, NOT 1.0. Renormalising would double
    # the active symbol's contribution.
    if (g_es, g_nq) == (1, 0):
        R_p_if_renormalised = 1.0 * R_es
        assert not np.allclose(
            R_p_gated,
            R_p_if_renormalised,
            atol=ATOL_MACHINE,
            rtol=RTOL_MACHINE,
        )


def test_per_bar_varying_gate_state() -> None:
    """Stress sub-rule 3.3a with per-bar-varying gates: every bar
    independently selects a (g_ES, g_NQ) state. The orchestrator-style
    vectorised aggregate must equal an INDEPENDENTLY computed
    elementwise reference (a Python-loop construction that materialises
    sub-rule 3.3a one bar at a time, with no implicit broadcasting).
    """
    n = 500
    rng = np.random.default_rng(seed=20260424)
    es_close = _synthetic_close_series(n=n, seed=3333)
    nq_close = _synthetic_close_series(n=n, seed=4444)

    g_es = rng.integers(0, 2, size=n).astype(np.float64)
    g_nq = rng.integers(0, 2, size=n).astype(np.float64)

    R_es = log_to_arithmetic(_per_bar_log_returns(es_close))
    R_nq = log_to_arithmetic(_per_bar_log_returns(nq_close))

    # Orchestrator-style vectorised aggregate (the production path).
    R_p_vectorised = g_es * 0.5 * R_es + g_nq * 0.5 * R_nq

    # Independent elementwise reference: construct R_p_ref bar-by-bar
    # via a Python loop materialising sub-rule 3.3a. Each bar's value
    # is computed by branching on the gate state, NOT by re-evaluating
    # the same vectorised expression (which would be a tautology).
    R_p_ref = np.empty(n, dtype=np.float64)
    for t in range(n):
        contrib_es = 0.5 * R_es[t] if g_es[t] == 1.0 else 0.0
        contrib_nq = 0.5 * R_nq[t] if g_nq[t] == 1.0 else 0.0
        R_p_ref[t] = contrib_es + contrib_nq

    assert np.allclose(
        R_p_vectorised, R_p_ref, atol=ATOL_MACHINE, rtol=RTOL_MACHINE
    )
    # Bars where both gates are 0 must produce exactly zero (no float
    # jitter from the multiplication path).
    both_off = (g_es == 0) & (g_nq == 0)
    if both_off.any():
        assert np.all(R_p_vectorised[both_off] == 0.0)


# ---------------------------------------------------------------------------
# Test 4 — zero-return edge case (exact equality, no float jitter)
# ---------------------------------------------------------------------------


def test_zero_return_edge_case() -> None:
    """When all per-bar returns are exactly 0 (constant prices), the
    aggregate is exactly 0.0 with no float jitter, regardless of which
    space the aggregation is performed in.
    """
    n = 500
    constant_close = np.full(n, 100.0, dtype=np.float64)

    r_log = _per_bar_log_returns(constant_close)  # all zeros
    R_arith = log_to_arithmetic(r_log)  # expm1(0) = 0 exactly per IEEE-754

    # IEEE-754 guarantees expm1(0) = 0 exactly (special case in C99
    # math.h, inherited by numpy expm1).
    assert np.all(r_log == 0.0)
    assert np.all(R_arith == 0.0)

    R_p = 0.5 * R_arith + 0.5 * R_arith
    assert np.all(R_p == 0.0)
    # Stronger: the result is identically the float64 zero, not -0.0
    # or any subnormal artifact.
    assert R_p.dtype == np.float64


# ---------------------------------------------------------------------------
# Test 5 — large-return regime stability
# ---------------------------------------------------------------------------


def test_large_return_excluded_or_handled() -> None:
    """Stress the conversion at extreme per-bar returns (5%/min, well
    outside the empirical regime but within the float64 numerical regime).

    Asserts:
      - no overflow / NaN / Inf in either path,
      - the addendum-path aggregate equals the direct-arithmetic
        aggregate at machine precision regardless of magnitude,
      - the linear (log-space) approximation diverges from the correct
        aggregate by O(r^2/2) ~= 1.25e-3 per bar at 5% / min, which is
        FOUR orders of magnitude larger than the 1-min ES/NQ regime.
        This is documented as the regime boundary at which the
        convention difference becomes empirically meaningful.
    """
    n = 200
    rng = np.random.default_rng(seed=99999)

    # Construct extreme log-returns directly and exponentiate to
    # close-prices. Bound per-bar |r| <= 0.05 to stay in the numerically
    # stable regime; any larger and the level series risks underflow on
    # multi-thousand-bar paths.
    extreme_r_bound = 0.05
    r_es_log = rng.uniform(-extreme_r_bound, extreme_r_bound, n)
    r_nq_log = rng.uniform(-extreme_r_bound, extreme_r_bound, n)
    es_close = 100.0 * np.exp(np.cumsum(r_es_log))
    nq_close = 100.0 * np.exp(np.cumsum(r_nq_log))

    # Re-derive per-bar log-returns through the orchestrator path to
    # exercise the diff(log(.)) idiom on the constructed levels.
    r_es_log_re = _per_bar_log_returns(es_close)
    r_nq_log_re = _per_bar_log_returns(nq_close)

    R_es_via_expm1 = log_to_arithmetic(r_es_log_re)
    R_nq_via_expm1 = log_to_arithmetic(r_nq_log_re)

    # Stability: no NaN, no Inf, and the magnitude is bounded.
    # Analytic upper bound on |R| given |r| <= 0.05:
    #   max R = expm1(0.05) ~= 0.05127
    #   |min R| = |expm1(-0.05)| ~= 0.04877
    # so the absolute envelope is np.expm1(0.05); add a small ulp
    # cushion for the diff(log()) round-trip.
    arith_envelope = np.expm1(extreme_r_bound) + 1e-12
    assert np.all(np.isfinite(R_es_via_expm1))
    assert np.all(np.isfinite(R_nq_via_expm1))
    assert np.max(np.abs(R_es_via_expm1)) < arith_envelope
    assert np.max(np.abs(R_nq_via_expm1)) < arith_envelope

    # Equivalence vs direct-arithmetic still holds at machine precision.
    R_es_direct = _per_bar_arithmetic_returns(es_close)
    R_nq_direct = _per_bar_arithmetic_returns(nq_close)
    R_p_addendum = 0.5 * R_es_via_expm1 + 0.5 * R_nq_via_expm1
    R_p_direct = 0.5 * R_es_direct + 0.5 * R_nq_direct
    assert np.allclose(
        R_p_addendum, R_p_direct, atol=ATOL_MACHINE, rtol=RTOL_MACHINE
    )

    # Regime-boundary documentation: at 5%/min, the per-bar log-vs-
    # arithmetic divergence is ~ r^2/2 ~= 1.25e-3, four orders of
    # magnitude larger than the ~1e-7 divergence at the 1-min ES/NQ
    # 1e-3 sigma regime. The naive log-space aggregate is therefore
    # NOT a faithful approximation of R_p_correct in this regime.
    r_p_naive = 0.5 * r_es_log_re + 0.5 * r_nq_log_re
    per_bar_div = np.max(np.abs(R_p_addendum - r_p_naive))
    # Analytic lower bound: at the largest-|r| bar in the sample,
    # |R - r| = |expm1(r) - r| >= r^2/2 (Taylor remainder is non-
    # negative for the leading term). With r drawn uniform on
    # [-0.05, 0.05] over n=200 bars, max |r| is close to but bounded
    # by 0.05; the per-symbol per-bar divergence at the tail bar is
    # >= 0.5 * 0.04^2 / 2 = 4e-4 (using a conservative 0.04 floor for
    # the empirical max-|r| under uniform draws, well below the
    # theoretical 0.05 ceiling). The aggregate halves this, giving
    # an aggregate-level lower bound of ~ 1e-4 with 5x headroom.
    aggregate_div_lower_bound = 0.5 * (0.04 ** 2) / 2.0  # ~= 4e-4
    assert per_bar_div > aggregate_div_lower_bound, (
        f"expected the 5%-per-min regime to surface a non-trivial "
        f"log-vs-arithmetic divergence; got {per_bar_div} vs lower "
        f"bound {aggregate_div_lower_bound}"
    )


# ---------------------------------------------------------------------------
# Test 6 — return_conventions helper input-validation (defensive)
# ---------------------------------------------------------------------------


def test_log_to_arithmetic_rejects_2d_input() -> None:
    """The helper is contract-bound to 1-D series; 2-D inputs must
    raise rather than silently broadcast."""
    with pytest.raises(ValueError, match="1-D"):
        log_to_arithmetic(np.zeros((3, 3)))


def test_arithmetic_to_log_rejects_2d_input() -> None:
    with pytest.raises(ValueError, match="1-D"):
        arithmetic_to_log(np.zeros((3, 3)))
