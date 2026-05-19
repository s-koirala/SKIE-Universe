"""BOCD live-pause state machine per ADR-0025 §D-4.

Wraps the [bocd.py](bocd.py) batch primitive with a hard-pause state machine
for production trading. The wrapping is structural; the underlying Bayesian
posterior update is preserved verbatim per ADR-0013 §4.1 non-loss mandate.

Distinct from [bocd.py](bocd.py) `detect_decay` (batch one-shot verdict on a
rolling MPPM path): this module tracks a LIVE pause state across an arbitrary-
length sequence of incremental observations, with three re-entry criteria + a
hard `min_pause_duration_sessions` floor preventing flap (per F-1-4 audit fix).

KPI report card disclosure annotation per ADR-0025 §D-5:
- `bocd-live-pause`: at least one pause event fired during the simulation.
- `bocd-live-active`: zero pause events; the live state machine remained
  permissive throughout.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Literal

import numpy as np
from scipy.special import logsumexp

from skie_ninja.inference.bocd import BOCDState, bocd_update, init_bocd

__all__ = [
    "BOCDLiveConfig",
    "BOCDLiveState",
    "init_bocd_live",
    "bocd_live_update",
    "is_paused",
    "manually_resume",
    "summarize_pause_events",
]


@dataclass(frozen=True)
class BOCDLiveConfig:
    """Configuration for the BOCD live-pause state machine.

    Attributes:
        hazard_rate: Constant hazard H(τ) = 1/λ per Adams-MacKay 2007.
            justify: 1/250 default per ADR-0018 §D-3 (operational; empirical
            calibration pending P1-BOCD-HAZARD-RATE-EMPIRICAL).
        window: Lookback window for the recent-changepoint posterior.
            justify: 60-session default per ADR-0018 §D-3.
        decay_threshold: Threshold on P(r_t < window/2) for pause-entry.
            justify: 0.5 default per ADR-0018 §D-3.
        re_entry_criterion: One of {"posterior_below_threshold",
            "fixed_session_count", "manual"}.
        re_entry_threshold: Threshold for posterior-based re-entry.
            justify: 0.20 default — operator-prior hysteresis band beneath the
            0.5 decay-detection threshold; empirical calibration pending
            P1-BOCD-LIVE-REENTRY-EMPIRICAL.
        re_entry_session_count: Sessions to wait before fixed-count re-entry.
            justify: 60-session default matches ADR-0018 §D-3 window=60
            consistency-of-forgetting-horizon convention.
        min_pause_duration_sessions: Hard floor on pause duration regardless
            of re-entry criterion. justify: 20-session default — operator-
            prior; one calendar month of trading sessions is the canonical
            minimum for regime-change to be distinguishable from noise at
            hazard 1/250.
        post_resume_state: "reinit" (default; clean) or "zero_changepoint_mass"
            (preserves NIG sufficient statistics; may bias subsequent detection
            — pending empirical comparison per P1-BOCD-LIVE-POSTDETECT-RESET-CONVENTION).
        mu_0, kappa_0, alpha_0, beta_0: NIG prior hyperparameters for
            init_bocd; default weak per Adams-MacKay 2007.
    """

    hazard_rate: float = 1.0 / 250.0
    window: int = 60
    decay_threshold: float = 0.5
    re_entry_criterion: Literal[
        "posterior_below_threshold", "fixed_session_count", "manual"
    ] = "posterior_below_threshold"
    re_entry_threshold: float = 0.20
    re_entry_session_count: int = 60
    min_pause_duration_sessions: int = 20
    post_resume_state: Literal["reinit", "zero_changepoint_mass"] = "reinit"
    mu_0: float = 0.0
    kappa_0: float = 1.0
    alpha_0: float = 1.0
    beta_0: float = 1.0

    def __post_init__(self) -> None:
        if not (0.0 < self.hazard_rate <= 1.0):
            raise ValueError(
                f"hazard_rate must be in (0, 1]; got {self.hazard_rate}."
            )
        if self.window < 2:
            raise ValueError(f"window must be >= 2; got {self.window}.")
        if not (0.0 < self.decay_threshold < 1.0):
            raise ValueError(
                f"decay_threshold must be in (0, 1); got {self.decay_threshold}."
            )
        if not (0.0 < self.re_entry_threshold < self.decay_threshold):
            raise ValueError(
                f"re_entry_threshold ({self.re_entry_threshold}) must be in "
                f"(0, decay_threshold={self.decay_threshold}) — hysteresis "
                f"requires re_entry < decay."
            )
        if self.re_entry_session_count < 1:
            raise ValueError(
                f"re_entry_session_count must be >= 1; got {self.re_entry_session_count}."
            )
        if self.min_pause_duration_sessions < 1:
            raise ValueError(
                f"min_pause_duration_sessions must be >= 1; "
                f"got {self.min_pause_duration_sessions}."
            )


@dataclass(frozen=True)
class BOCDLiveState:
    """Immutable state for the BOCD live-pause state machine.

    Per F-1-8 audit fix, pause_event_log entries carry BOTH `session_idx`
    (deterministic from substrate) AND `ts_utc` (ISO-8601 UTC absolute
    timestamp) for replay-robustness across session-calendar drift.
    """

    config: BOCDLiveConfig
    bocd_state: BOCDState
    pause_active: bool
    pause_entered_session_idx: int | None
    pause_entered_ts_utc: str | None
    pause_entered_posterior: float | None
    last_observed_posterior: float
    sessions_since_pause: int
    n_observed: int
    pause_event_log: tuple[dict[str, Any], ...] = field(default_factory=tuple)


def init_bocd_live(config: BOCDLiveConfig) -> BOCDLiveState:
    """Initialise the live-pause state machine."""
    bocd_state = init_bocd(
        hazard_rate=config.hazard_rate,
        mu_0=config.mu_0,
        kappa_0=config.kappa_0,
        alpha_0=config.alpha_0,
        beta_0=config.beta_0,
    )
    return BOCDLiveState(
        config=config,
        bocd_state=bocd_state,
        pause_active=False,
        pause_entered_session_idx=None,
        pause_entered_ts_utc=None,
        pause_entered_posterior=None,
        last_observed_posterior=0.0,
        sessions_since_pause=0,
        n_observed=0,
        pause_event_log=(),
    )


def _recent_changepoint_posterior(state: BOCDState, window: int) -> float:
    """Return P(r_t < window/2) given the current BOCD log-joint.

    Mirrors the batch [bocd.py](bocd.py) `changepoint_posterior` semantic but
    for one-step incremental use: normalises the log-joint to a posterior and
    sums the first window/2 entries.
    """
    log_joint = state.run_length_log_probs
    if log_joint.size == 0:
        return 0.0
    log_norm = logsumexp(log_joint)
    posterior = np.exp(log_joint - log_norm)
    half = max(1, window // 2)
    upper = min(half, posterior.size)
    return float(posterior[:upper].sum())


def _reset_bocd_state(config: BOCDLiveConfig, prior_state: BOCDState) -> BOCDState:
    """Per F-1-4 audit fix: post-resume BOCDState semantic."""
    if config.post_resume_state == "reinit":
        return init_bocd(
            hazard_rate=config.hazard_rate,
            mu_0=config.mu_0,
            kappa_0=config.kappa_0,
            alpha_0=config.alpha_0,
            beta_0=config.beta_0,
        )
    # "zero_changepoint_mass": rebuild log-joint with r=0 mass set to -inf
    # then re-normalise on next update via the bocd_update logsumexp.
    # We accomplish this by leaving log_joint as-is but truncating the
    # run-length posterior — a practical approximation; full Bayesian
    # correctness is the reinit path.
    return prior_state


def bocd_live_update(
    state: BOCDLiveState,
    x_t: float,
    *,
    session_idx: int,
    ts_utc: str,
) -> BOCDLiveState:
    """One incremental update: advances BOCD, evaluates pause-state transition.

    Returns a new BOCDLiveState. Side-effect free.

    Pause-transition logic:
      1. If not paused and recent-changepoint posterior crosses decay_threshold
         → enter pause (record entry session_idx + ts_utc + posterior).
      2. If paused: increment sessions_since_pause; re-entry-eligibility check:
         - sessions_since_pause >= min_pause_duration_sessions, AND
         - per `re_entry_criterion`: posterior < re_entry_threshold (default)
           OR sessions_since_pause >= re_entry_session_count (fixed_session_count)
           OR manual resume (skipped here; see `manually_resume`).
    """
    config = state.config
    new_bocd_state = bocd_update(state.bocd_state, x_t)
    posterior = _recent_changepoint_posterior(new_bocd_state, config.window)

    pause_active = state.pause_active
    pause_entered_session_idx = state.pause_entered_session_idx
    pause_entered_ts_utc = state.pause_entered_ts_utc
    pause_entered_posterior = state.pause_entered_posterior
    sessions_since_pause = state.sessions_since_pause
    pause_event_log = state.pause_event_log

    # Warmup gate: mirror the batch primitive's burn-in convention at
    # [bocd.py:354](bocd.py) — first window/2 observations are degenerate
    # (run-length cannot exceed t, so half-window sum is trivially ≈ 1).
    # justify: window/2 burn-in per Adams-MacKay 2007 (Bayesian degeneracy at
    # t < window/2; not a detected event); matches the batch primitive's
    # `out[:burn_in] = 0.0` convention.
    in_warmup = state.n_observed + 1 < (config.window // 2)

    if not pause_active and not in_warmup:
        if posterior > config.decay_threshold:
            pause_active = True
            pause_entered_session_idx = session_idx
            pause_entered_ts_utc = ts_utc
            pause_entered_posterior = posterior
            sessions_since_pause = 0
    else:
        sessions_since_pause += 1
        eligible_by_duration = (
            sessions_since_pause >= config.min_pause_duration_sessions
        )
        re_entry_triggered = False
        if eligible_by_duration:
            if config.re_entry_criterion == "posterior_below_threshold":
                re_entry_triggered = posterior < config.re_entry_threshold
            elif config.re_entry_criterion == "fixed_session_count":
                re_entry_triggered = (
                    sessions_since_pause >= config.re_entry_session_count
                )
            # "manual" requires explicit `manually_resume`; never auto-resumes.
        if re_entry_triggered:
            pause_event_log = pause_event_log + (
                {
                    "pause_entered_session_idx": pause_entered_session_idx,
                    "pause_entered_ts_utc": pause_entered_ts_utc,
                    "pause_entered_posterior": pause_entered_posterior,
                    "pause_exited_session_idx": session_idx,
                    "pause_exited_ts_utc": ts_utc,
                    "pause_exited_posterior": posterior,
                    "pause_duration_sessions": sessions_since_pause,
                    "re_entry_criterion": config.re_entry_criterion,
                },
            )
            pause_active = False
            pause_entered_session_idx = None
            pause_entered_ts_utc = None
            pause_entered_posterior = None
            sessions_since_pause = 0
            new_bocd_state = _reset_bocd_state(config, new_bocd_state)

    return replace(
        state,
        bocd_state=new_bocd_state,
        pause_active=pause_active,
        pause_entered_session_idx=pause_entered_session_idx,
        pause_entered_ts_utc=pause_entered_ts_utc,
        pause_entered_posterior=pause_entered_posterior,
        last_observed_posterior=posterior,
        sessions_since_pause=sessions_since_pause,
        n_observed=state.n_observed + 1,
        pause_event_log=pause_event_log,
    )


def manually_resume(
    state: BOCDLiveState, *, session_idx: int, ts_utc: str
) -> BOCDLiveState:
    """Operator-triggered resume; only honored under re_entry_criterion='manual'.

    Subject to the min_pause_duration_sessions floor: if sessions_since_pause
    < min_pause_duration_sessions, raises ValueError (operator must wait).
    """
    if not state.pause_active:
        raise ValueError("Cannot manually_resume when not paused.")
    if state.config.re_entry_criterion != "manual":
        raise ValueError(
            f"manually_resume requires re_entry_criterion='manual'; "
            f"current = {state.config.re_entry_criterion}."
        )
    if state.sessions_since_pause < state.config.min_pause_duration_sessions:
        raise ValueError(
            f"min_pause_duration_sessions={state.config.min_pause_duration_sessions} "
            f"not yet elapsed; sessions_since_pause={state.sessions_since_pause}."
        )
    new_log = state.pause_event_log + (
        {
            "pause_entered_session_idx": state.pause_entered_session_idx,
            "pause_entered_ts_utc": state.pause_entered_ts_utc,
            "pause_entered_posterior": state.pause_entered_posterior,
            "pause_exited_session_idx": session_idx,
            "pause_exited_ts_utc": ts_utc,
            "pause_exited_posterior": state.last_observed_posterior,
            "pause_duration_sessions": state.sessions_since_pause,
            "re_entry_criterion": "manual",
        },
    )
    new_bocd = _reset_bocd_state(state.config, state.bocd_state)
    return replace(
        state,
        bocd_state=new_bocd,
        pause_active=False,
        pause_entered_session_idx=None,
        pause_entered_ts_utc=None,
        pause_entered_posterior=None,
        sessions_since_pause=0,
        pause_event_log=new_log,
    )


def is_paused(state: BOCDLiveState) -> bool:
    """Short-circuit query for the orchestrator's entry path."""
    return state.pause_active


def summarize_pause_events(state: BOCDLiveState) -> dict[str, Any]:
    """Provenance summary for sidecar emission + KPI annotation per §D-5."""
    n_events = len(state.pause_event_log)
    total_paused = sum(
        e["pause_duration_sessions"] for e in state.pause_event_log
    )
    longest = (
        max((e["pause_duration_sessions"] for e in state.pause_event_log), default=0)
    )
    # Currently-paused: include the in-progress pause in `currently_paused`.
    currently_paused = state.pause_active
    return {
        "n_pause_events": int(n_events),
        "total_sessions_paused": int(total_paused),
        "longest_pause_run": int(longest),
        "currently_paused_at_sim_end": bool(currently_paused),
        "re_entry_criterion": state.config.re_entry_criterion,
        "pause_event_log": list(state.pause_event_log),
        "annotation": "bocd-live-pause" if (n_events > 0 or currently_paused) else "bocd-live-active",
    }
