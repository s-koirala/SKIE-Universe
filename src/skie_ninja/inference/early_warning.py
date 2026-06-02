"""Leading early-warning detectors for strategy-decay / regime-shift onset.

Per ADR-0029 §D-2 (Thrust 1), this is the LEADING tier that complements the
LAGGING BOCD confirmation ([skie_ninja.inference.bocd][], Adams-MacKay 2007
arXiv:0710.3742). BOCD confirms a changepoint only after post-change evidence
accumulates; these precursor detectors fire while the strategy is still
nominally in-regime, feeding a pre-emptive PARTIAL de-risk (size-down, not
exit). BOCD's posterior crossing remains the full-reallocation confirmation.

Three precursor families, all read on the per-session performance INCREMENT path
(stationary returns / MPPM increments, NOT the equity level):

1. Critical-slowing-down EWS (Scheffer et al. 2009 Nature 461(7260):53-59 DOI
   10.1038/nature08227; estimator toolbox Dakos et al. 2012 PLoS ONE 7(7):e41010
   DOI 10.1371/journal.pone.0041010): rolling variance + lag-1 autocorrelation
   rise as a system approaches a critical transition; the trend is the Kendall-τ
   of the rolling-indicator series. Financial-path caveat (Guttal et al. 2016
   PLoS ONE 11(1):e0144198 DOI 10.1371/journal.pone.0144198): weight VARIANCE
   over AR(1) — on market series variance rises before crashes but lag-1 AR
   often does not, so AR(1) is reported but advisory-only by default. BOTH CSD
   trends are advisory-only by default: the Kendall-τ of an overlapping-rolling-
   window indicator is heavily autocorrelated, so a raw fixed-τ cutoff has a high
   false-positive rate (a single iid realization can show a strong apparent
   trend). Per Dakos 2012 the τ is tested against a surrogate/bootstrap null
   rather than a constant cutoff; that calibration is deferred to
   `P1-EARLY-WARNING-CSD-SURROGATE-NULL`, so by default the GATING layers are
   CUSUM + drawdown (robust) and CSD is reported-only.

2. Lower CUSUM sequential change detection (Page 1954 Biometrika 41(1-2):100-115
   DOI 10.1093/biomet/41.1-2.100): accumulates downward deviations of the
   per-session excess return from its in-regime reference mean; alarms when the
   cumulative deviation exceeds threshold h. The canonical design (reference
   value k = half the shift-to-detect, decision interval h ≈ 4-5σ) maps
   detection-delay to false-alarm rate (ARL_0).

3. Drawdown-velocity / time-under-water (Bailey & López de Prado 2015 J Risk
   18(2):61-93 DOI 10.21314/JOR.2015.317 "triple penance"): running deviation
   from the equity peak + sessions-under-water; signal-agnostic (reads the
   wealth path directly). The triple-penance closed-form quantiles are the
   calibration METHOD for the bands (deferred to `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`);
   this primitive computes the drawdown + TuW series exactly and flags against
   supplied (calibrated) bands.

All thresholds (window, Kendall-τ trigger, CUSUM k/h, drawdown/TuW bands,
de-risk fraction) are project-operational defaults flagged for empirical
calibration on a pre-OOS holdout per `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`
(BLOCKING-BEFORE-CLOSED-LOOP-RUN) and the no-magic-number rule (CLAUDE.md
§"Parameter & Prompt Selection"). The success metric is detection-LEAD relative
to the BOCD-confirmed changepoint on the holdout, NOT standalone forecast skill
(CSD is a tripwire: Diks-Hommes-Wang 2019 Empirical Economics 57(4):1201-1228
DOI 10.1007/s00181-018-1527-3 found it insignificant for the 1997/2000/2008
crises).

Implementation per `P1-EARLY-WARNING-DETECTOR-PRIMITIVE` (ADR-0029 §D-2 Thrust 1;
Phase P buildout P-2). Streaming interface follows the `skie_ninja.inference.bocd`
`init` / `update` / read-function INTERFACE SHAPE so both tiers drive off the same
per-session loop. Mutation semantics differ: `bocd_update` returns a fresh state,
whereas `early_warning_update` mutates the state in place and returns the same object.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt
from scipy import stats

__all__ = [
    "CriticalSlowingDownResult",
    "CusumResult",
    "DrawdownResult",
    "EarlyWarningConfig",
    "EarlyWarningSignal",
    "EarlyWarningState",
    "critical_slowing_down",
    "cusum_lower",
    "drawdown_under_water",
    "early_warning_update",
    "evaluate_early_warning",
    "evaluate_early_warning_path",
    "init_early_warning",
]

_MIN_WINDOW = 3  # minimum rolling window for a variance / lag-1-AR trend
_MIN_POINTS = 2  # minimum points to estimate a variance / std / CUSUM step
_SIGMA_REL_FLOOR = float(np.sqrt(np.finfo(float).eps))  # relative σ floor (F-1 audit)


@dataclass(frozen=True)
class CriticalSlowingDownResult:
    """Kendall-τ trend of rolling variance + lag-1 AR per Dakos et al. 2012.

    Attributes:
        variance_tau: Kendall-τ of the rolling-variance series vs time index, in
            [-1, 1]. Positive = variance rising (the load-bearing CSD precursor
            on financial paths per Guttal et al. 2016).
        ar1_tau: Kendall-τ of the rolling lag-1-autocorrelation series. Advisory
            only on financial paths (Guttal 2016).
        n_windows: Number of rolling windows the τ trend was computed over (= n -
            window + 1). NaN τ is returned as 0.0 when n_windows < 2.
        window: Rolling-window length used.
    """

    variance_tau: float
    ar1_tau: float
    n_windows: int
    window: int


@dataclass(frozen=True)
class CusumResult:
    """Lower-CUSUM running statistic for downward-drift detection (Page 1954).

    Attributes:
        statistic: 1-D array of the running lower-CUSUM S_t (>= 0); same length
            as the input deviation series.
        max_statistic: Maximum of `statistic` over the series.
        first_alarm_index: First index where S_t > h, or -1 if never.
        k: Reference value (slack) used.
        h: Decision interval (alarm threshold) used.
    """

    statistic: np.ndarray
    max_statistic: float
    first_alarm_index: int
    k: float
    h: float


@dataclass(frozen=True)
class DrawdownResult:
    """Running drawdown + time-under-water on a log-return path (Bailey-LdP 2015).

    Drawdown is computed in log space relative to the running peak of cumulative
    log-equity; `*_fraction` fields convert to arithmetic fraction via expm1.

    Attributes:
        drawdown_log: 1-D array of log-drawdown (<= 0) per session.
        time_under_water: 1-D int array of sessions since the last equity peak.
        max_drawdown_fraction: Worst (most negative) arithmetic drawdown fraction.
        max_time_under_water: Longest under-water run (sessions).
        current_drawdown_fraction: Arithmetic drawdown fraction at the last session.
        current_time_under_water: Under-water run length at the last session.
    """

    drawdown_log: np.ndarray
    time_under_water: np.ndarray
    max_drawdown_fraction: float
    max_time_under_water: int
    current_drawdown_fraction: float
    current_time_under_water: int


def _rolling_variance_and_ar1(values: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    n = values.size
    n_windows = n - window + 1
    var = np.empty(n_windows, dtype=float)
    ar1 = np.empty(n_windows, dtype=float)
    for i in range(n_windows):
        w = values[i : i + window]
        var[i] = float(np.var(w, ddof=1))
        wc = w - w.mean()
        denom = float(np.dot(wc, wc))
        ar1[i] = float(np.dot(wc[1:], wc[:-1]) / denom) if denom > 0.0 else 0.0
    return var, ar1


def _kendall_tau_trend(series: np.ndarray) -> float:
    if series.size < _MIN_POINTS or np.allclose(series, series[0]):
        return 0.0
    tau = stats.kendalltau(np.arange(series.size, dtype=float), series).correlation
    return 0.0 if (tau is None or np.isnan(tau)) else float(tau)


def critical_slowing_down(
    path: npt.ArrayLike,
    *,
    window: int,
) -> CriticalSlowingDownResult:
    """Kendall-τ trend of rolling variance + lag-1 AR (Scheffer 2009 / Dakos 2012).

    Args:
        path: 1-D performance-INCREMENT series (stationary returns / MPPM
            increments, NOT the equity level — EWS precursors are computed on the
            stationary observable, so no detrending of a level is needed).
        window: Rolling-window length (>= 3). Project-operational; calibrate on a
            pre-OOS holdout per `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`.

    Returns:
        CriticalSlowingDownResult with variance_tau, ar1_tau, n_windows, window.

    Raises:
        ValueError: if window < 3, or path has fewer than `window` points.
    """
    x = np.asarray(path, dtype=float).ravel()
    if window < _MIN_WINDOW:
        raise ValueError(f"window must be >= 3, got {window}.")
    if x.size < window:
        raise ValueError(f"path requires at least window={window} points, got {x.size}.")
    var_series, ar1_series = _rolling_variance_and_ar1(x, window)
    return CriticalSlowingDownResult(
        variance_tau=_kendall_tau_trend(var_series),
        ar1_tau=_kendall_tau_trend(ar1_series),
        n_windows=int(var_series.size),
        window=window,
    )


def cusum_lower(
    deviations: npt.ArrayLike,
    *,
    k: float,
    h: float,
) -> CusumResult:
    """Lower-CUSUM for a downward mean-shift in the deviation series (Page 1954).

    S_t = max(0, S_{t-1} - deviation_t - k); alarm when S_t > h. The statistic
    grows whenever deviation_t < -k (the per-session excess return falls more
    than the slack k below its in-regime reference), so it detects sustained
    decay (returns drifting below the regime mean).

    Args:
        deviations: 1-D excess-return series (the per-session return minus its
            in-regime reference mean; the caller demeans — see
            `evaluate_early_warning` for the standardized convention).
        k: Reference value (slack), in the same units as `deviations` and >= 0.
        h: Decision interval (alarm threshold), in the same units and > 0.

    Returns:
        CusumResult with the running statistic, its max, the first-alarm index
        (or -1), and the k/h used.

    Raises:
        ValueError: if deviations is empty, k < 0, or h <= 0.
    """
    d = np.asarray(deviations, dtype=float).ravel()
    if d.size == 0:
        raise ValueError("deviations must be non-empty.")
    if k < 0.0:
        raise ValueError(f"k (reference value) must be >= 0, got {k}.")
    if h <= 0.0:
        raise ValueError(f"h (decision interval) must be > 0, got {h}.")
    stat = np.empty(d.size, dtype=float)
    s = 0.0
    first_alarm = -1
    for t in range(d.size):
        s = max(0.0, s - float(d[t]) - k)
        stat[t] = s
        if first_alarm < 0 and s > h:
            first_alarm = t
    return CusumResult(
        statistic=stat,
        max_statistic=float(stat.max()),
        first_alarm_index=first_alarm,
        k=float(k),
        h=float(h),
    )


def drawdown_under_water(log_returns: npt.ArrayLike) -> DrawdownResult:
    """Running drawdown + time-under-water on a log-return path (Bailey-LdP 2015).

    Args:
        log_returns: 1-D per-session log-return series. Cumulative log-equity is
            cumsum(log_returns) relative to the start; drawdown is the deviation
            below the running peak.

    Returns:
        DrawdownResult with the drawdown_log + time_under_water series and their
        max / current summaries (arithmetic fractions via expm1).

    Raises:
        ValueError: if log_returns is empty.
    """
    r = np.asarray(log_returns, dtype=float).ravel()
    if r.size == 0:
        raise ValueError("log_returns must be non-empty.")
    equity_log = np.cumsum(r)
    running_max = np.maximum.accumulate(equity_log)
    drawdown_log = equity_log - running_max
    tuw = np.empty(r.size, dtype=int)
    count = 0
    for t in range(r.size):
        count = 0 if equity_log[t] >= running_max[t] else count + 1
        tuw[t] = count
    return DrawdownResult(
        drawdown_log=drawdown_log,
        time_under_water=tuw,
        max_drawdown_fraction=float(np.expm1(drawdown_log.min())),
        max_time_under_water=int(tuw.max()),
        current_drawdown_fraction=float(np.expm1(drawdown_log[-1])),
        current_time_under_water=int(tuw[-1]),
    )


@dataclass(frozen=True)
class EarlyWarningConfig:
    """Configuration for the composite early-warning detector.

    All threshold fields are project-operational defaults flagged for empirical
    calibration on a pre-OOS holdout per `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`
    (BLOCKING-BEFORE-CLOSED-LOOP-RUN). Defaults are documented, not arbitrary:
    CUSUM k=0.5σ / h=5σ are the canonical SPC design for detecting a 1σ shift
    (Page 1954; standard ARL_0 control); the de-risk fraction 0.5 aligns with
    ADR-0028 `K_SIZE_DOWN_FRACTION_DEFAULT` and the MacLean-Thorp-Ziemba 2010
    fractional-Kelly half-step convention.
    """

    window: int = 60  # justify: ~quarter trading-year of sessions; calibrate
    csd_variance_tau_threshold: float = 0.5  # justify: Kendall-τ strong-positive-trend; calibrate
    csd_ar1_tau_threshold: float = 0.5  # justify: advisory-only by default per Guttal 2016
    csd_variance_advisory_only: bool = (
        True  # justify: advisory by default — see class + module docstring
    )
    ar1_advisory_only: bool = True  # Guttal 2016: AR(1) does not gate on financial paths
    reference_window: int = (
        60  # justify: in-regime mean+std window for CUSUM standardization; calibrate
    )
    cusum_k_sigma: float = 0.5  # justify: canonical CUSUM reference (half a 1σ shift)
    cusum_h_sigma: float = 5.0  # justify: canonical CUSUM decision interval (~ARL_0 control)
    drawdown_fraction_threshold: float = (
        0.10  # justify: 10% peak-to-current; calibrate via Bailey-LdP triple-penance
    )
    tuw_threshold: int = 20  # justify: sessions under water; calibrate via triple-penance
    derisk_fraction: float = (
        0.5  # justify: partial de-risk multiplier; aligns ADR-0028 size-down default
    )

    def __post_init__(self) -> None:
        if self.window < _MIN_WINDOW:
            raise ValueError(f"window must be >= 3, got {self.window}.")
        if self.reference_window < _MIN_POINTS:
            raise ValueError(f"reference_window must be >= 2, got {self.reference_window}.")
        if self.cusum_k_sigma < 0.0:
            raise ValueError(f"cusum_k_sigma must be >= 0, got {self.cusum_k_sigma}.")
        if self.cusum_h_sigma <= 0.0:
            raise ValueError(f"cusum_h_sigma must be > 0, got {self.cusum_h_sigma}.")
        if self.drawdown_fraction_threshold <= 0.0:
            raise ValueError(
                f"drawdown_fraction_threshold must be > 0, got {self.drawdown_fraction_threshold}."
            )
        if self.tuw_threshold < 1:
            raise ValueError(f"tuw_threshold must be >= 1, got {self.tuw_threshold}.")
        if not (0.0 < self.derisk_fraction <= 1.0):
            raise ValueError(f"derisk_fraction must be in (0, 1], got {self.derisk_fraction}.")


@dataclass(frozen=True)
class EarlyWarningSignal:
    """Composite early-warning read at the current end of the performance path.

    Annotation grammar per ADR-0029 §Consequences: `early-warning-{armed, fired, n/a}`.
    """

    armed: bool
    fired: bool
    variance_tau: float
    ar1_tau: float
    csd_variance_fired: bool
    cusum_standardized: float
    cusum_fired: bool
    drawdown_fraction: float
    time_under_water: int
    drawdown_fired: bool
    fired_layers: tuple[str, ...]
    derisk_multiplier: float
    n_observed: int

    @property
    def annotation(self) -> str:
        if not self.armed:
            return "early-warning-n/a"
        return "early-warning-fired" if self.fired else "early-warning-armed"


@dataclass
class EarlyWarningState:
    """Mutable streaming state following the bocd init/update/read interface shape.

    Mutation semantics differ from `bocd.BOCDState` (which `bocd_update` rebuilds
    immutably): `early_warning_update` mutates this state in place. Holds the
    consumed per-session performance-increment path; `evaluate_early_warning`
    recomputes the detectors over the buffer (batch == stream parity by
    construction). Incremental-update perf is deferred to `P1-EARLY-WARNING-INCREMENTAL-UPDATE`.

    `reference_mean` / `reference_sigma` are the FROZEN in-regime baseline (mean +
    std) established at deployment / last reallocation; when set they anchor the
    CUSUM (the closed-loop-correct, estimation-noise-free reference). When None the
    CUSUM falls back to the leading-`reference_window` estimate, which carries
    reference-estimation noise and a higher false-positive rate (uncalibrated
    tripwire mode) — see `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`.
    """

    config: EarlyWarningConfig
    path: list[float] = field(default_factory=list)
    n_observed: int = 0
    reference_mean: float | None = None
    reference_sigma: float | None = None


def init_early_warning(
    config: EarlyWarningConfig | None = None,
    *,
    reference_mean: float | None = None,
    reference_sigma: float | None = None,
) -> EarlyWarningState:
    """Initialize an EarlyWarningState (empty path).

    Args:
        config: EarlyWarningConfig; defaults to project-operational defaults
            (all flagged for calibration per `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`).
        reference_mean: Optional FROZEN in-regime baseline mean for the CUSUM
            (established at deployment / last reallocation). When None, the CUSUM
            falls back to the leading-window estimate (uncalibrated tripwire mode).
        reference_sigma: Optional FROZEN in-regime baseline std for the CUSUM; must
            be supplied together with reference_mean to take effect.

    Returns:
        EarlyWarningState with an empty path and n_observed = 0.
    """
    return EarlyWarningState(
        config=config if config is not None else EarlyWarningConfig(),
        reference_mean=reference_mean,
        reference_sigma=reference_sigma,
    )


def early_warning_update(state: EarlyWarningState, x_t: float) -> EarlyWarningState:
    """Append one per-session performance increment to the state (streaming).

    Args:
        state: The EarlyWarningState to update (mutated in place and returned).
        x_t: The per-session performance increment (log-return / MPPM increment).

    Returns:
        The same EarlyWarningState with x_t appended and n_observed incremented.
    """
    state.path.append(float(x_t))
    state.n_observed += 1
    return state


def evaluate_early_warning(state: EarlyWarningState) -> EarlyWarningSignal:
    """Read the composite early-warning signal at the current end of the path.

    Gating layers (fire → partial de-risk): rising-variance CSD, lower-CUSUM,
    drawdown/TuW. AR(1) is advisory-only by default (Guttal 2016). `fired` is the
    OR of the gating layers; `derisk_multiplier` = config.derisk_fraction on fire,
    else 1.0.

    Args:
        state: The EarlyWarningState carrying the consumed performance path.

    Returns:
        EarlyWarningSignal with per-layer flags + the composite de-risk multiplier.
    """
    cfg = state.config
    x = np.asarray(state.path, dtype=float)
    n = x.size

    variance_tau = 0.0
    ar1_tau = 0.0
    csd_variance_fired = False
    if n >= cfg.window + 1:  # justify: +1 → ≥2 rolling windows, the minimum for a Kendall-τ trend
        csd = critical_slowing_down(x, window=cfg.window)
        variance_tau = csd.variance_tau
        ar1_tau = csd.ar1_tau
        csd_variance_fired = variance_tau >= cfg.csd_variance_tau_threshold

    cusum_standardized = 0.0
    cusum_fired = False
    if n >= _MIN_POINTS:
        # justify F-2 audit: anchor on the FROZEN in-regime baseline when available
        # (set at deployment / last reallocation); else fall back to the LEADING
        # window. Never the trailing window — a trailing mean absorbs the decay and
        # self-cancels the downward shift the CUSUM detects.
        if state.reference_mean is not None and state.reference_sigma is not None:
            mu_ref = float(state.reference_mean)
            sigma = float(state.reference_sigma)
        else:
            baseline = x[: cfg.reference_window] if n >= cfg.reference_window else x
            mu_ref = float(baseline.mean())
            sigma = float(np.std(baseline, ddof=1)) if baseline.size >= _MIN_POINTS else 0.0
        # justify F-1 audit: relative σ floor — a numerically-flat path has σ≈1e-18
        # from float rounding, which would otherwise blow up the standardized statistic.
        if sigma > _SIGMA_REL_FLOOR * max(abs(mu_ref), 1.0):
            cu = cusum_lower(
                x - mu_ref,
                k=cfg.cusum_k_sigma * sigma,
                h=cfg.cusum_h_sigma * sigma,
            )
            cusum_fired = bool(cu.statistic[-1] > cu.h)
            cusum_standardized = float(cu.statistic[-1] / sigma)

    drawdown_fraction = 0.0
    time_under_water = 0
    drawdown_fired = False
    if n >= 1:
        dd = drawdown_under_water(x)
        drawdown_fraction = dd.current_drawdown_fraction
        time_under_water = dd.current_time_under_water
        drawdown_fired = (
            drawdown_fraction <= -cfg.drawdown_fraction_threshold
            or time_under_water >= cfg.tuw_threshold
        )

    layers: list[str] = []
    if csd_variance_fired and not cfg.csd_variance_advisory_only:
        layers.append("csd_variance")
    if ar1_tau >= cfg.csd_ar1_tau_threshold and not cfg.ar1_advisory_only:
        layers.append("csd_ar1")
    if cusum_fired:
        layers.append("cusum")
    if drawdown_fired:
        layers.append("drawdown")

    armed = n >= _MIN_POINTS
    fired = armed and len(layers) > 0
    return EarlyWarningSignal(
        armed=armed,
        fired=fired,
        variance_tau=variance_tau,
        ar1_tau=ar1_tau,
        csd_variance_fired=csd_variance_fired,
        cusum_standardized=cusum_standardized,
        cusum_fired=cusum_fired,
        drawdown_fraction=drawdown_fraction,
        time_under_water=time_under_water,
        drawdown_fired=drawdown_fired,
        fired_layers=tuple(layers) if armed else (),
        derisk_multiplier=cfg.derisk_fraction if fired else 1.0,
        n_observed=n,
    )


def evaluate_early_warning_path(
    path: npt.ArrayLike,
    config: EarlyWarningConfig | None = None,
    *,
    reference_mean: float | None = None,
    reference_sigma: float | None = None,
) -> EarlyWarningSignal:
    """Batch entry: build a state from a full path and read the end-of-path signal.

    Equivalent to streaming `early_warning_update` over `path` then
    `evaluate_early_warning` (used by tests + holdout calibration).

    Args:
        path: 1-D per-session performance-increment series.
        config: EarlyWarningConfig; defaults to project-operational defaults.

    Returns:
        EarlyWarningSignal at the final point of `path`.
    """
    state = init_early_warning(
        config, reference_mean=reference_mean, reference_sigma=reference_sigma
    )
    for x_t in np.asarray(path, dtype=float).ravel():
        early_warning_update(state, float(x_t))
    return evaluate_early_warning(state)
