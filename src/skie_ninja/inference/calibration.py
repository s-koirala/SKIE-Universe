"""H053 calibration: binary BSS gate + reliability slope + multinomial KPI + cost-aware KPI + beta KPI.

Per [plan/h053_stage3_v3_plan_2026-05-03.md](../../../plan/h053_stage3_v3_plan_2026-05-03.md) §B
+ [research/01_hypothesis_register/H053/design.md](../../../research/01_hypothesis_register/H053/design.md) §4.5.3.

Binding gates (Class A under ADR-0012; bootstrap CI replaces v2 point thresholds per plan v3-r3 §B):
- ``binary_bss_lower_ci > 0`` vs climatological prior (paired stationary bootstrap; CI lower bound > 0)
- ``reliability_slope_ci_covers_one`` (paired stationary bootstrap; 1.0 ∈ [CI_lower, CI_upper])

Class B KPI exhibits (non-binding per ADR-0012):
- Multinomial K_arch × 3 Brier with global BSS bootstrap CI
- Cost-aware binary `d_c = 1 if y > c` for 1-tick + 2-tick c per symbol
- Beta calibration (Kull et al. 2017) comparison vs the binding isotonic/Platt
- Inner-fold seed-sensitivity exhibit (caller-side; this module exposes the
  per-fit calibrator API used in the loop)

Calibrator selection (design.md §4.5.3 binding rule, immutable §1-§7):
- Isotonic primary
- Platt fallback at N_cal < 500
- 3-way selection (Platt vs isotonic vs beta) with parsimony tie-break is
  EXPLICITLY rejected per Round-1 plan-audit F-1-7 closure (NM&C 2005 Figure 4
  shows isotonic dominates at large n; the parsimony ordering inverted
  the empirical finding)

References
----------
- design.md §4.5.3 — binding calibration spec.
- ADR-0012 — disposition philosophy (Class A vs Class B).
- Brier, G. W. 1950. "Verification of Forecasts Expressed in Terms of
  Probability." *Monthly Weather Review* 78(1):1-3.
  https://doi.org/10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2
- Murphy, A. H. 1973. "A New Vector Partition of the Probability Score."
  *Journal of Applied Meteorology* 12(4):595-600.
- Gneiting, T. & Raftery, A. E. 2007. "Strictly Proper Scoring Rules,
  Prediction, and Estimation." *JASA* 102(477):359-378. — strict-properness
  of multinomial Brier (paper-level pin; Theorem-3.2 §-pin not verified
  in plan-audit budget).
- Niculescu-Mizil, A. & Caruana, R. 2005. "Predicting good probabilities
  with supervised learning." *ICML 2005*. doi:10.1145/1102351.1102430.
- Kull, M.; Silva Filho, T. M.; Flach, P. 2017. "Beta calibration: a
  well-founded and easily implemented improvement on logistic
  calibration for binary classifiers." *EJS* 11(2):5052-5080.
  doi:10.1214/17-EJS1338SI.
- Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap."
  *JASA* 89(428):1303-1313. doi:10.2307/2290993.
- Bröcker, J. & Smith, L. A. 2007. "Increasing the Reliability of
  Reliability Diagrams." *Weather and Forecasting* 22(3):651-661.
  doi:10.1175/WAF993.1.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from skie_ninja.inference.bootstrap import choose_block_length, stationary_bootstrap_indices

_EPS = float(np.finfo(np.float64).eps)
_PLATT_FALLBACK_NCAL_THRESHOLD = 500  # design.md §4.5.3 binding rule


@dataclass(frozen=True)
class BSSResult:
    """Binary Brier Skill Score with bootstrap CI."""

    bss_point: float
    bss_ci_lower: float
    bss_ci_upper: float
    n_obs: int
    n_bootstrap: int
    block_length: float
    binding_gate_passed: bool  # bss_ci_lower > 0


@dataclass(frozen=True)
class ReliabilitySlopeResult:
    """Reliability slope with bootstrap CI; binding gate = CI covers 1.0."""

    slope_point: float
    intercept_point: float
    slope_ci_lower: float
    slope_ci_upper: float
    n_obs: int
    n_bootstrap: int
    block_length: float
    binding_gate_passed: bool  # 1.0 ∈ [slope_ci_lower, slope_ci_upper]


@dataclass(frozen=True)
class MultinomialBSSResult:
    """Multinomial K_arch × 3 Brier with global BSS bootstrap CI (Class B KPI)."""

    bss_point: float
    bss_ci_lower: float
    bss_ci_upper: float
    n_obs: int
    k_cells: int
    n_bootstrap: int
    block_length: float


@dataclass(frozen=True)
class CalibratorChoice:
    """Outcome of design.md §4.5.3 calibrator selection."""

    name: str  # "isotonic" or "platt"
    n_cal: int
    fallback_triggered: bool


@dataclass(frozen=True)
class CalibrationReport:
    """Composite calibration report for a single (symbol, arm) cell."""

    binary_bss: BSSResult
    reliability_slope: ReliabilitySlopeResult
    calibrator: CalibratorChoice
    multinomial_bss_kpi: MultinomialBSSResult | None = None
    cost_aware_binary_bss_kpi: dict[str, BSSResult] = field(default_factory=dict)
    beta_calibration_kpi_log_loss: float | None = None
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Binary Brier Skill Score
# ---------------------------------------------------------------------------


def binary_brier_score(p: npt.ArrayLike, y: npt.ArrayLike) -> float:
    """Binary Brier score: mean of (p - y)² for binary outcomes y ∈ {0, 1}."""
    p_arr = np.asarray(p, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    if p_arr.shape != y_arr.shape:
        raise ValueError(f"shape mismatch: p {p_arr.shape} vs y {y_arr.shape}")
    return float(np.mean((p_arr - y_arr) ** 2))


def binary_brier_skill_score(p: npt.ArrayLike, y: npt.ArrayLike) -> float:
    """Binary Brier Skill Score vs climatological prior P(y=1) = mean(y).

    BSS = 1 - BS_model / BS_climatology

    Per Brier 1950 + design.md §4.5.3: BSS > 0 indicates the model has
    skill over the climatological reference. The reference is the
    constant predictor p̂_clim = ȳ (sample mean of binary outcomes).
    """
    y_arr = np.asarray(y, dtype=np.float64)
    n = len(y_arr)
    if n == 0:
        return 0.0
    y_bar = float(np.mean(y_arr))
    bs_model = binary_brier_score(p, y_arr)
    bs_clim = float(np.mean((y_bar - y_arr) ** 2))
    if bs_clim < _EPS:
        return 0.0  # degenerate (all y identical)
    return 1.0 - bs_model / bs_clim


def binary_bss_bootstrap_ci(
    p: npt.ArrayLike,
    y: npt.ArrayLike,
    *,
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
    block_length: float | None = None,
    rng: np.random.Generator | None = None,
) -> BSSResult:
    """Paired stationary bootstrap CI on binary BSS (binding-gate primitive).

    Per plan v3-r3 §B + design.md §4.5.3:
    - Paired stationary bootstrap on (p_oof, y) tuples (preserves
      forecast-outcome dependence + serial dependence in y)
    - B = 2000 replicates
    - Block length: PW2004+PPW2009 automatic on the y series (chosen
      because it carries the dependence; auto-derived if not supplied)
    - 95% percentile CI

    Binding-gate: ``BSS_lower_CI > 0`` (procedurally stricter than
    design.md §4.5.3 "BSS > 0" point-test; flagged as §10 procedural
    amendment in ADR-0013 within ADR-0012 carve-out).
    """
    p_arr = np.asarray(p, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    n = len(y_arr)
    if n != len(p_arr):
        raise ValueError(f"shape mismatch: p {p_arr.shape} vs y {y_arr.shape}")
    if rng is None:
        rng = np.random.default_rng(42)
    if block_length is None:
        sel = choose_block_length(y_arr, bootstrap_type="stationary")
        block_length = float(sel.block_length)

    bss_point = binary_brier_skill_score(p_arr, y_arr)
    boot_bss = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=block_length, rng=rng)
        boot_bss[b] = binary_brier_skill_score(p_arr[idx], y_arr[idx])

    alpha = (1.0 - ci_level) / 2.0
    ci_lower = float(np.percentile(boot_bss, 100.0 * alpha))
    ci_upper = float(np.percentile(boot_bss, 100.0 * (1.0 - alpha)))
    return BSSResult(
        bss_point=float(bss_point),
        bss_ci_lower=ci_lower,
        bss_ci_upper=ci_upper,
        n_obs=n,
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
        binding_gate_passed=ci_lower > 0.0,
    )


# ---------------------------------------------------------------------------
# Reliability slope (Bröcker-Smith 2007) with bootstrap CI
# ---------------------------------------------------------------------------


def reliability_slope_point(
    p: npt.ArrayLike,
    y: npt.ArrayLike,
    *,
    n_bins: int = 10,
) -> tuple[float, float]:
    """Compute reliability-diagram slope + intercept from binned conditional means.

    For ``n_bins`` equal-frequency bins of forecast ``p``, compute the
    bin midpoint ``p̄_b`` and the empirical conditional mean ``ȳ_b``,
    then OLS-fit ``ȳ_b = α + β · p̄_b``. Slope ``β = 1`` indicates
    perfect reliability (Bröcker-Smith 2007 §3).

    Bins with zero observations are skipped (operational floor on the
    OLS regression sample size).
    """
    p_arr = np.asarray(p, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    n = len(p_arr)
    if n == 0 or n_bins < 2:
        return 1.0, 0.0  # vacuous; slope=1 is the no-skill-no-bias reference

    quantiles = np.quantile(p_arr, np.linspace(0.0, 1.0, n_bins + 1))
    quantiles = np.unique(quantiles)
    if len(quantiles) < 3:
        return 1.0, 0.0  # too few unique forecast values for a meaningful slope

    bin_p = []
    bin_y = []
    for i in range(len(quantiles) - 1):
        lo, hi = quantiles[i], quantiles[i + 1]
        if i == len(quantiles) - 2:
            mask = (p_arr >= lo) & (p_arr <= hi)
        else:
            mask = (p_arr >= lo) & (p_arr < hi)
        if np.sum(mask) < 1:
            continue
        bin_p.append(float(np.mean(p_arr[mask])))
        bin_y.append(float(np.mean(y_arr[mask])))

    if len(bin_p) < 2:
        return 1.0, 0.0
    bin_p_arr = np.array(bin_p)
    bin_y_arr = np.array(bin_y)
    var_p = float(np.var(bin_p_arr))
    if var_p < _EPS:
        return 1.0, 0.0
    cov_py = float(np.cov(bin_p_arr, bin_y_arr, ddof=0)[0, 1])
    slope = cov_py / var_p
    intercept = float(np.mean(bin_y_arr) - slope * np.mean(bin_p_arr))
    return float(slope), intercept


def reliability_slope_bootstrap_ci(
    p: npt.ArrayLike,
    y: npt.ArrayLike,
    *,
    n_bins: int = 10,
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
    block_length: float | None = None,
    rng: np.random.Generator | None = None,
) -> ReliabilitySlopeResult:
    """Paired stationary bootstrap CI on reliability slope (binding-gate primitive).

    Per plan v3-r3 §B: binding test = ``1.0 ∈ [slope_ci_lower, slope_ci_upper]``.
    Bröcker-Smith 2007 §3 framework with stationary-bootstrap CI substituted
    for their consistency-bars construction (consistent with the project's
    canonical PW2004+PPW2009 block-bootstrap stack).
    """
    p_arr = np.asarray(p, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    n = len(y_arr)
    if n != len(p_arr):
        raise ValueError(f"shape mismatch: p {p_arr.shape} vs y {y_arr.shape}")
    if rng is None:
        rng = np.random.default_rng(42)
    if block_length is None:
        sel = choose_block_length(y_arr, bootstrap_type="stationary")
        block_length = float(sel.block_length)

    slope_point, intercept_point = reliability_slope_point(p_arr, y_arr, n_bins=n_bins)
    boot_slopes = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=block_length, rng=rng)
        s_b, _ = reliability_slope_point(p_arr[idx], y_arr[idx], n_bins=n_bins)
        boot_slopes[b] = s_b

    alpha = (1.0 - ci_level) / 2.0
    ci_lower = float(np.percentile(boot_slopes, 100.0 * alpha))
    ci_upper = float(np.percentile(boot_slopes, 100.0 * (1.0 - alpha)))
    return ReliabilitySlopeResult(
        slope_point=float(slope_point),
        intercept_point=float(intercept_point),
        slope_ci_lower=ci_lower,
        slope_ci_upper=ci_upper,
        n_obs=n,
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
        binding_gate_passed=ci_lower <= 1.0 <= ci_upper,
    )


# ---------------------------------------------------------------------------
# Multinomial Brier (Class B KPI exhibit)
# ---------------------------------------------------------------------------


def multinomial_brier_score(P: npt.ArrayLike, Y: npt.ArrayLike) -> float:
    """Multinomial Brier score: mean over rows of sum_k (P_{r,k} - Y_{r,k})².

    Per Brier 1950 R-class formulation (mutually-exclusive categories,
    sum-to-one). For K = 2 reduces to 2 · binary Brier.

    P : (n, K) probability matrix (each row sums to 1)
    Y : (n, K) one-hot indicator matrix
    """
    P_arr = np.asarray(P, dtype=np.float64)
    Y_arr = np.asarray(Y, dtype=np.float64)
    if P_arr.shape != Y_arr.shape:
        raise ValueError(f"shape mismatch: P {P_arr.shape} vs Y {Y_arr.shape}")
    return float(np.mean(np.sum((P_arr - Y_arr) ** 2, axis=1)))


def multinomial_bss_kpi(
    P: npt.ArrayLike,
    Y: npt.ArrayLike,
    *,
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
    block_length: float | None = None,
    rng: np.random.Generator | None = None,
) -> MultinomialBSSResult:
    """Multinomial K-cell Brier Skill Score with bootstrap CI (Class B KPI).

    Reference distribution = marginal frequencies P_clim_k = mean(Y_k)
    (constant predictor of marginal class probabilities). Per
    Gneiting-Raftery 2007 the multinomial Brier is strictly proper,
    so a non-trivial BSS > 0 indicates skill above marginal prediction.

    Class B KPI per plan v3-r3 §B (NOT binding gate; multinomial-as-binding
    was rejected in Round-1 plan-audit F-1-12 as exceeding ADR-0012
    §"Frozen pre-registration amendment" carve-out scope).
    """
    P_arr = np.asarray(P, dtype=np.float64)
    Y_arr = np.asarray(Y, dtype=np.float64)
    n = len(Y_arr)
    K = Y_arr.shape[1] if Y_arr.ndim == 2 else 1
    if rng is None:
        rng = np.random.default_rng(42)
    if block_length is None:
        # Use class-1 marginal as the bandwidth-derivation series
        sel = choose_block_length(Y_arr[:, 0] if Y_arr.ndim == 2 else Y_arr, bootstrap_type="stationary")
        block_length = float(sel.block_length)

    # Climatological reference: each row predicts the marginal class frequencies
    Y_marg = np.mean(Y_arr, axis=0, keepdims=True)
    P_clim = np.broadcast_to(Y_marg, Y_arr.shape).copy()

    bs_model = multinomial_brier_score(P_arr, Y_arr)
    bs_clim = multinomial_brier_score(P_clim, Y_arr)
    bss_point = 1.0 - bs_model / bs_clim if bs_clim > _EPS else 0.0

    boot_bss = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=block_length, rng=rng)
        bs_b = multinomial_brier_score(P_arr[idx], Y_arr[idx])
        # Recompute climatological reference under resample for honest CI
        Y_marg_b = np.mean(Y_arr[idx], axis=0, keepdims=True)
        P_clim_b = np.broadcast_to(Y_marg_b, Y_arr.shape).copy()
        bs_clim_b = multinomial_brier_score(P_clim_b, Y_arr[idx])
        boot_bss[b] = 1.0 - bs_b / bs_clim_b if bs_clim_b > _EPS else 0.0

    alpha = (1.0 - ci_level) / 2.0
    return MultinomialBSSResult(
        bss_point=float(bss_point),
        bss_ci_lower=float(np.percentile(boot_bss, 100.0 * alpha)),
        bss_ci_upper=float(np.percentile(boot_bss, 100.0 * (1.0 - alpha))),
        n_obs=n,
        k_cells=int(K),
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
    )


# ---------------------------------------------------------------------------
# Calibrator selection (design.md §4.5.3 binding rule)
# ---------------------------------------------------------------------------


def select_calibrator(n_cal: int) -> CalibratorChoice:
    """design.md §4.5.3 binding rule: isotonic primary; Platt fallback at N_cal < 500."""
    if n_cal < _PLATT_FALLBACK_NCAL_THRESHOLD:
        return CalibratorChoice(name="platt", n_cal=n_cal, fallback_triggered=True)
    return CalibratorChoice(name="isotonic", n_cal=n_cal, fallback_triggered=False)


def fit_calibrator(
    raw_scores: npt.ArrayLike,
    binary_outcomes: npt.ArrayLike,
    *,
    choice: CalibratorChoice | None = None,
):
    """Fit the design.md §4.5.3 calibrator on held-out CV-fold (raw_scores, y).

    Returns a fitted calibrator with a ``predict(raw_scores)`` API.
    """
    raw = np.asarray(raw_scores, dtype=np.float64).ravel()
    y = np.asarray(binary_outcomes, dtype=np.int64).ravel()
    if choice is None:
        choice = select_calibrator(len(y))
    if choice.name == "isotonic":
        model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        model.fit(raw, y.astype(np.float64))
        return model
    # platt
    model = LogisticRegression(C=1e9, solver="lbfgs", max_iter=1000)
    model.fit(raw.reshape(-1, 1), y)
    return model


def predict_calibrated(model, raw_scores: npt.ArrayLike) -> np.ndarray:
    """Uniform predict-calibrated-probability API across {isotonic, platt}."""
    raw = np.asarray(raw_scores, dtype=np.float64).ravel()
    if isinstance(model, IsotonicRegression):
        return np.asarray(model.predict(raw), dtype=np.float64)
    if isinstance(model, LogisticRegression):
        return np.asarray(model.predict_proba(raw.reshape(-1, 1))[:, 1], dtype=np.float64)
    raise TypeError(f"unsupported calibrator type: {type(model).__name__}")


# ---------------------------------------------------------------------------
# Beta calibration (Class B KPI exhibit, per Kull et al. 2017)
# ---------------------------------------------------------------------------


def fit_beta_calibration(
    raw_scores: npt.ArrayLike,
    binary_outcomes: npt.ArrayLike,
) -> tuple[float, float, float]:
    """Beta calibration per Kull et al. 2017 §3 (KPI exhibit only).

    Fits ``logit(p_calib) = a · log(s) + b · log(1 - s) + c`` via
    logistic regression on transformed features. Returns (a, b, c).

    Class B KPI per plan v3-r3 §B; not binding (design.md §4.5.3
    binding rule selects between isotonic and Platt only).
    """
    raw = np.asarray(raw_scores, dtype=np.float64).ravel()
    y = np.asarray(binary_outcomes, dtype=np.int64).ravel()
    eps = 1e-12
    raw_clipped = np.clip(raw, eps, 1.0 - eps)
    f1 = np.log(raw_clipped)
    f2 = np.log(1.0 - raw_clipped)
    X = np.column_stack([f1, f2])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = LogisticRegression(C=1e9, solver="lbfgs", max_iter=2000)
        model.fit(X, y)
    a, b = float(model.coef_[0, 0]), float(model.coef_[0, 1])
    c = float(model.intercept_[0])
    return a, b, c


def predict_beta_calibration(
    raw_scores: npt.ArrayLike, a: float, b: float, c: float
) -> np.ndarray:
    """Predict calibrated probabilities under the beta calibration model."""
    raw = np.asarray(raw_scores, dtype=np.float64).ravel()
    eps = 1e-12
    raw_clipped = np.clip(raw, eps, 1.0 - eps)
    logit = a * np.log(raw_clipped) + b * np.log(1.0 - raw_clipped) + c
    return 1.0 / (1.0 + np.exp(-logit))


def beta_calibration_log_loss(
    raw_scores_train: npt.ArrayLike,
    y_train: npt.ArrayLike,
    raw_scores_test: npt.ArrayLike,
    y_test: npt.ArrayLike,
) -> float:
    """Held-out log-loss for the beta-calibration KPI exhibit."""
    a, b, c = fit_beta_calibration(raw_scores_train, y_train)
    p_test = predict_beta_calibration(raw_scores_test, a, b, c)
    p_test = np.clip(p_test, 1e-12, 1.0 - 1e-12)
    y_test_arr = np.asarray(y_test, dtype=np.float64).ravel()
    return float(-np.mean(y_test_arr * np.log(p_test) + (1.0 - y_test_arr) * np.log(1.0 - p_test)))


# ---------------------------------------------------------------------------
# Cost-aware binary BSS (Class B KPI exhibit)
# ---------------------------------------------------------------------------


def cost_aware_binary_bss_kpi(
    p: npt.ArrayLike,
    y_continuous: npt.ArrayLike,
    *,
    cost_c: float,
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
    block_length: float | None = None,
    rng: np.random.Generator | None = None,
) -> BSSResult:
    """Cost-aware binary BSS KPI: ``d_c = 1 if y > c`` (Class B per plan §B).

    At c ≈ 1 bps (well below per-session predictand σ ~ 50-100 bps),
    this is essentially the binding ``d = 1 if y > 0`` test. The KPI
    documents marginal sensitivity to cost-floor assumptions.
    """
    y_arr = np.asarray(y_continuous, dtype=np.float64).ravel()
    d_c = (y_arr > cost_c).astype(np.float64)
    return binary_bss_bootstrap_ci(
        p,
        d_c,
        n_bootstrap=n_bootstrap,
        ci_level=ci_level,
        block_length=block_length,
        rng=rng,
    )


__all__ = [
    "BSSResult",
    "ReliabilitySlopeResult",
    "MultinomialBSSResult",
    "CalibratorChoice",
    "CalibrationReport",
    "binary_brier_score",
    "binary_brier_skill_score",
    "binary_bss_bootstrap_ci",
    "reliability_slope_point",
    "reliability_slope_bootstrap_ci",
    "multinomial_brier_score",
    "multinomial_bss_kpi",
    "select_calibrator",
    "fit_calibrator",
    "predict_calibrated",
    "fit_beta_calibration",
    "predict_beta_calibration",
    "beta_calibration_log_loss",
    "cost_aware_binary_bss_kpi",
]
