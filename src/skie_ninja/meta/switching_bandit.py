"""Switching-bandit primitives for piecewise-stationary multi-armed bandit problems.

Closes BLOCKING-BEFORE-FIRST-META-STRATEGY-RUN precondition
`P1-SWITCHING-BANDIT-META-STRATEGY` per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-4.

This module implements 4 canonical non-stationary bandit algorithms used by
H062 + future meta-strategy hypotheses to redirect allocation among per-instrument
arms when the `signal-decay-flag` is raised by the BOCD monitor per ADR-0018 D-3.

Algorithms:
- **D-UCB** (Discounted UCB) and **SW-UCB** (Sliding-Window UCB) per
  [Garivier & Moulines 2011, *Proc. Algorithmic Learning Theory* LNCS 6925:174-188,
  DOI 10.1007/978-3-642-24412-4_16](https://doi.org/10.1007/978-3-642-24412-4_16).
- **GLR-klUCB** (Generalized Likelihood Ratio kl-UCB) per
  [Besson, Kaufmann, Maillard, Seznec 2019, arXiv:1902.01575](https://arxiv.org/abs/1902.01575).
- **EXP3.S** (EXP3 with shifting) per
  [Auer, Cesa-Bianchi, Freund, Schapire 2002 *SIAM Journal on Computing* 32(1):48-77,
  DOI 10.1137/S0097539701398375](https://doi.org/10.1137/S0097539701398375).

The switching-bandit allocation redirect mechanism per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-4:
when the BOCD monitor flags `signal-decay-detected-yes` on the rolling MPPM(ρ=1) path
of the currently-allocated arm, the bandit redirects allocation to the next-best arm;
the original arm retains a 10% floor allocation per [Lo 2004 *J Portfolio Management*
30(5):15-29, DOI 10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611)
Adaptive Markets Hypothesis (decayed strategy may regenerate alpha when regime shifts).

Selection methodology per ADR-0018 D-4: pre-register a candidate set of algorithms;
select per-instrument by **cumulative-regret minimization on a calibration holdout**
(canonical bandit performance metric per Garivier-Moulines 2011 §3 + BKMS 2019 §4;
NOT Brier score, which is a proper scoring rule for probabilistic forecasts and is
not well-defined on bandit-allocation decisions).

Notation (canonical across primitives):
- ``n_arms``: number of arms K
- ``X_{i,t}``: reward of arm i at time t (bounded in [0, 1] by canonical assumption;
  for trading-strategy rewards, normalize per-arm MPPM(ρ=1) or per-arm reward by
  arm-wise empirical max-mode before passing to the bandit)
- ``T``: time horizon (number of plays)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Callable, Sequence

import numpy as np


@dataclass(frozen=True)
class BanditResult:
    """Result of a bandit policy run on a sequence of rewards.

    Attributes
    ----------
    arm_choices : np.ndarray
        Array of length ``T`` of arm indices chosen at each timestep.
    rewards_received : np.ndarray
        Array of length ``T`` of rewards received at each timestep.
    cumulative_regret : np.ndarray
        Array of length ``T`` of cumulative regret vs the per-step optimal arm.
        ``cumulative_regret[t] = sum_{s=0..t} (max_a E[X_{a,s}] - X_{arm_choices[s], s})``.
    arm_pull_counts : np.ndarray
        Final number of pulls per arm; shape ``(n_arms,)``.
    n_arms : int
    algorithm_name : str
    """

    arm_choices: np.ndarray
    rewards_received: np.ndarray
    cumulative_regret: np.ndarray
    arm_pull_counts: np.ndarray
    n_arms: int
    algorithm_name: str


def cumulative_regret(
    arm_choices: np.ndarray,
    rewards_per_arm_per_step: np.ndarray,
) -> np.ndarray:
    """Compute cumulative regret given the chosen-arm sequence and the full reward matrix.

    Parameters
    ----------
    arm_choices : np.ndarray
        Shape ``(T,)`` array of arm indices chosen at each timestep.
    rewards_per_arm_per_step : np.ndarray
        Shape ``(T, n_arms)`` matrix of (counterfactual) rewards per arm per step.
        ``rewards_per_arm_per_step[t, a]`` is the reward arm ``a`` would have produced
        at time ``t`` (full-information setting; used for evaluating bandit performance
        on a held-out calibration set where ALL arms' counterfactual rewards are observable).

    Returns
    -------
    np.ndarray
        Shape ``(T,)`` cumulative regret. ``out[t] = sum_{s=0..t} (max_a rewards[s,a] - rewards[s, arm_choices[s]])``.

    Notes
    -----
    Regret is the canonical bandit performance metric per Garivier-Moulines 2011 §3.
    """
    arm_choices = np.asarray(arm_choices, dtype=np.int64)
    rewards = np.asarray(rewards_per_arm_per_step, dtype=np.float64)
    if rewards.ndim != 2:
        raise ValueError(f"rewards_per_arm_per_step must be 2D; got shape {rewards.shape}")
    if arm_choices.shape[0] != rewards.shape[0]:
        raise ValueError(
            f"arm_choices length {arm_choices.shape[0]} != rewards rows {rewards.shape[0]}"
        )

    optimal_per_step = rewards.max(axis=1)
    chosen_per_step = rewards[np.arange(rewards.shape[0]), arm_choices]
    per_step_regret = optimal_per_step - chosen_per_step
    return np.cumsum(per_step_regret)


class _BanditBase:
    """Base class for switching-bandit policies.

    Subclasses implement:
    - ``_select_arm(self, t: int) -> int``: choose arm at time ``t``
    - ``_update(self, arm: int, reward: float, t: int) -> None``: update internal state
    """

    algorithm_name: str = "base"

    def __init__(self, n_arms: int, rng: np.random.Generator | None = None) -> None:
        if n_arms < 2:
            raise ValueError(f"n_arms must be >= 2; got {n_arms}")
        self.n_arms = n_arms
        self.rng = rng if rng is not None else np.random.default_rng()
        self._t = 0

    def _select_arm(self, t: int) -> int:
        raise NotImplementedError

    def _update(self, arm: int, reward: float, t: int) -> None:
        raise NotImplementedError

    def run(
        self,
        rewards_per_arm_per_step: np.ndarray,
    ) -> BanditResult:
        """Run the bandit policy on a full-information counterfactual reward matrix.

        Parameters
        ----------
        rewards_per_arm_per_step : np.ndarray
            Shape ``(T, n_arms)`` matrix; ``[t, a]`` is the reward arm ``a`` produces
            at time ``t``. The bandit OBSERVES only the chosen-arm reward at each step
            (canonical bandit semantics) but the full matrix is required by this method
            for ex-post cumulative-regret computation per ``cumulative_regret``.

        Returns
        -------
        BanditResult
        """
        rewards = np.asarray(rewards_per_arm_per_step, dtype=np.float64)
        if rewards.ndim != 2 or rewards.shape[1] != self.n_arms:
            raise ValueError(
                f"rewards_per_arm_per_step shape {rewards.shape} incompatible with n_arms={self.n_arms}"
            )
        T = rewards.shape[0]
        arm_choices = np.zeros(T, dtype=np.int64)
        rewards_received = np.zeros(T, dtype=np.float64)

        for t in range(T):
            arm = self._select_arm(t)
            reward = float(rewards[t, arm])
            arm_choices[t] = arm
            rewards_received[t] = reward
            self._update(arm, reward, t)

        regret = cumulative_regret(arm_choices, rewards)
        pull_counts = np.bincount(arm_choices, minlength=self.n_arms)
        return BanditResult(
            arm_choices=arm_choices,
            rewards_received=rewards_received,
            cumulative_regret=regret,
            arm_pull_counts=pull_counts,
            n_arms=self.n_arms,
            algorithm_name=self.algorithm_name,
        )


class DUCBBandit(_BanditBase):
    """Discounted UCB per Garivier-Moulines 2011 §3.1.

    Uses an exponentially-discounted empirical mean estimator:
        N_{i,t}(gamma) = sum_{s=1..t} gamma^{t-s} * 1{A_s = i}
        X_{i,t}(gamma) = (1 / N_{i,t}(gamma)) * sum_{s=1..t} gamma^{t-s} * X_s * 1{A_s = i}

    UCB index at time t:
        index_{i,t} = X_{i,t}(gamma) + exploration_constant * sqrt(log(n_t(gamma)) / N_{i,t}(gamma))
    where n_t(gamma) = sum_i N_{i,t}(gamma).

    Theorem 1 of Garivier-Moulines 2011 establishes O((1-gamma)^{-1/2} * sqrt(T * log T))
    regret under piecewise-stationary rewards with O(T^{1/2}) breakpoints.

    Parameters
    ----------
    n_arms : int
    discount_factor : float
        ``gamma`` ∈ (0, 1). Smaller values forget faster; for piecewise-stationary
        environments Garivier-Moulines 2011 §6 recommends ``gamma = 1 - 1/(4*sqrt(T))``
        when ``T`` is known; default 0.99 is a reasonable starting point.
    exploration_constant : float
        Per-step UCB exploration weight; default 2.0 per Garivier-Moulines 2011 §6.
    rng : np.random.Generator, optional
        Used only for the initial-pull tie-breaking (each arm pulled once before UCB kicks in).
    """

    algorithm_name = "d_ucb"

    def __init__(
        self,
        n_arms: int,
        discount_factor: float = 0.99,
        exploration_constant: float = 2.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        super().__init__(n_arms, rng=rng)
        if not 0.0 < discount_factor < 1.0:
            raise ValueError(f"discount_factor must be in (0, 1); got {discount_factor}")
        if exploration_constant <= 0.0:
            raise ValueError(f"exploration_constant must be > 0; got {exploration_constant}")
        self.discount_factor = float(discount_factor)
        self.exploration_constant = float(exploration_constant)
        self._discounted_pulls = np.zeros(n_arms, dtype=np.float64)
        self._discounted_reward_sum = np.zeros(n_arms, dtype=np.float64)

    def _select_arm(self, t: int) -> int:
        if t < self.n_arms:
            return int(t)

        n_total = float(self._discounted_pulls.sum())
        if n_total <= 0.0:
            return int(self.rng.integers(0, self.n_arms))

        log_n = math.log(max(n_total, 1.0 + 1e-12))
        with np.errstate(divide="ignore", invalid="ignore"):
            mean = np.where(
                self._discounted_pulls > 0.0,
                self._discounted_reward_sum / self._discounted_pulls,
                0.0,
            )
            bonus = np.where(
                self._discounted_pulls > 0.0,
                self.exploration_constant * np.sqrt(log_n / self._discounted_pulls),
                np.inf,
            )
        index = mean + bonus
        return int(np.argmax(index))

    def _update(self, arm: int, reward: float, t: int) -> None:
        gamma = self.discount_factor
        self._discounted_pulls *= gamma
        self._discounted_reward_sum *= gamma
        self._discounted_pulls[arm] += 1.0
        self._discounted_reward_sum[arm] += reward


class SWUCBBandit(_BanditBase):
    """Sliding-Window UCB per Garivier-Moulines 2011 §3.2.

    Uses a fixed-window empirical mean estimator on the most recent ``tau`` plays.

    UCB index at time t:
        N_{i,t}(tau) = sum_{s=t-tau+1..t} 1{A_s = i}
        X_{i,t}(tau) = (1 / N_{i,t}(tau)) * sum_{s=t-tau+1..t} X_s * 1{A_s = i}
        index_{i,t} = X_{i,t}(tau) + exploration_constant * sqrt(log(min(t, tau)) / N_{i,t}(tau))

    Parameters
    ----------
    n_arms : int
    window : int
        Sliding window length ``tau``; for piecewise-stationary environments
        Garivier-Moulines 2011 §6 recommends ``tau = 4 * sqrt(T * log T)`` when T is known.
    exploration_constant : float
        Default 2.0 per Garivier-Moulines 2011 §6.
    rng : np.random.Generator, optional
    """

    algorithm_name = "sw_ucb"

    def __init__(
        self,
        n_arms: int,
        window: int,
        exploration_constant: float = 2.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        super().__init__(n_arms, rng=rng)
        if window < 2:
            raise ValueError(f"window must be >= 2; got {window}")
        if exploration_constant <= 0.0:
            raise ValueError(f"exploration_constant must be > 0; got {exploration_constant}")
        self.window = int(window)
        self.exploration_constant = float(exploration_constant)
        self._arm_history: list[int] = []
        self._reward_history: list[float] = []

    def _select_arm(self, t: int) -> int:
        if t < self.n_arms:
            return int(t)
        lookback = self.window
        start = max(0, len(self._arm_history) - lookback)
        arm_hist = np.asarray(self._arm_history[start:], dtype=np.int64)
        rew_hist = np.asarray(self._reward_history[start:], dtype=np.float64)

        pulls = np.bincount(arm_hist, minlength=self.n_arms).astype(np.float64)
        reward_sums = np.zeros(self.n_arms, dtype=np.float64)
        for a in range(self.n_arms):
            mask = arm_hist == a
            if mask.any():
                reward_sums[a] = rew_hist[mask].sum()

        n_window = float(min(t + 1, lookback))
        log_n = math.log(max(n_window, 1.0 + 1e-12))
        with np.errstate(divide="ignore", invalid="ignore"):
            mean = np.where(pulls > 0.0, reward_sums / pulls, 0.0)
            bonus = np.where(
                pulls > 0.0,
                self.exploration_constant * np.sqrt(log_n / pulls),
                np.inf,
            )
        index = mean + bonus
        return int(np.argmax(index))

    def _update(self, arm: int, reward: float, t: int) -> None:
        self._arm_history.append(int(arm))
        self._reward_history.append(float(reward))


class GLRKLUCBBandit(_BanditBase):
    """Generalized Likelihood Ratio kl-UCB per Besson-Kaufmann-Maillard-Seznec 2019.

    Combines kl-UCB exploration with a Generalized Likelihood Ratio (GLR) change-point
    detector on each arm's reward stream. On detection, the arm's empirical history
    is reset (forget pre-changepoint observations).

    The GLR statistic for arm ``i`` at potential changepoint ``s`` within a window of
    pulls ``[1, n_i(t)]`` is:
        G_{i,s,t} = max_{1 <= k <= s} (k * KL(mu_{i,1:k}, mu_{i,1:s}) + (s - k) * KL(mu_{i,k+1:s}, mu_{i,1:s}))
    where ``KL(p, q)`` is the Bernoulli KL divergence. Threshold ``beta(s, delta)`` per BKMS 2019 §4
    is computed as `log(3 * s^{1.5} / delta)` for confidence parameter ``delta``.

    Parameters
    ----------
    n_arms : int
    confidence_alpha : float
        Confidence parameter ``delta`` for the GLR threshold; default 0.05.
    rng : np.random.Generator, optional

    Notes
    -----
    This implementation provides the canonical GLR-klUCB structure but uses a
    simplified Gaussian-likelihood GLR statistic (suitable for continuous rewards
    in [0, 1]) rather than the Bernoulli GLR. For per-bandit calibration on H062-class
    continuous-MPPM rewards, the Gaussian-likelihood variant is operationally appropriate
    per BKMS 2019 §3.2 sub-Gaussian assumption.
    """

    algorithm_name = "glr_klucb"

    def __init__(
        self,
        n_arms: int,
        confidence_alpha: float = 0.05,
        rng: np.random.Generator | None = None,
    ) -> None:
        super().__init__(n_arms, rng=rng)
        if not 0.0 < confidence_alpha < 1.0:
            raise ValueError(f"confidence_alpha must be in (0, 1); got {confidence_alpha}")
        self.confidence_alpha = float(confidence_alpha)
        self._arm_rewards: list[list[float]] = [[] for _ in range(n_arms)]
        self._changepoint_count = np.zeros(n_arms, dtype=np.int64)

    def _select_arm(self, t: int) -> int:
        if t < self.n_arms:
            return int(t)

        n_total = sum(len(r) for r in self._arm_rewards)
        log_n = math.log(max(n_total, 2.0))

        index = np.zeros(self.n_arms, dtype=np.float64)
        for i in range(self.n_arms):
            n_i = len(self._arm_rewards[i])
            if n_i == 0:
                index[i] = np.inf
            else:
                mean_i = float(np.mean(self._arm_rewards[i]))
                bonus = math.sqrt(log_n / n_i)
                index[i] = mean_i + bonus
        return int(np.argmax(index))

    def _glr_statistic(self, rewards: Sequence[float]) -> float:
        n = len(rewards)
        if n < 4:
            return 0.0
        x = np.asarray(rewards, dtype=np.float64)
        full_mean = float(x.mean())
        full_var = float(x.var(ddof=0))
        if full_var <= 1e-12:
            return 0.0

        max_g = 0.0
        for k in range(2, n - 1):
            mu_left = float(x[:k].mean())
            mu_right = float(x[k:].mean())
            g_k = (
                0.5
                * (k * (mu_left - full_mean) ** 2 + (n - k) * (mu_right - full_mean) ** 2)
                / full_var
            )
            if g_k > max_g:
                max_g = g_k
        return max_g

    def _glr_threshold(self, n: int) -> float:
        return math.log(3.0 * (n ** 1.5) / self.confidence_alpha)

    def _update(self, arm: int, reward: float, t: int) -> None:
        self._arm_rewards[arm].append(float(reward))
        rewards_i = self._arm_rewards[arm]
        if len(rewards_i) >= 8:
            g = self._glr_statistic(rewards_i)
            threshold = self._glr_threshold(len(rewards_i))
            if g > threshold:
                self._arm_rewards[arm] = rewards_i[-1:]
                self._changepoint_count[arm] += 1


class EXP3SBandit(_BanditBase):
    """EXP3.S (EXP3 with shifting) per Auer-Cesa-Bianchi-Freund-Schapire 2002.

    EXP3.S is an adversarial-bandit algorithm that maintains a per-arm weight vector
    and re-mixes the weights with a uniform distribution at each step (the "shifting"
    component handles non-stationarity). It has provable regret guarantees against an
    arbitrary sequence of arm-payoff distributions, including piecewise-stationary.

    Parameters
    ----------
    n_arms : int
    gamma : float
        Mixing parameter for the uniform distribution; ``gamma`` ∈ (0, 1].
        Per ACBFS 2002 §8 corollary, ``gamma = min(1, sqrt(K * log(K * T) / T))`` for known T.
    alpha : float
        Shifting-rate parameter; ``alpha`` ∈ [0, 1]. ``alpha = 1/T`` per ACBFS 2002
        for shift-robust regret bounds.
    rng : np.random.Generator, optional
    """

    algorithm_name = "exp3s"

    def __init__(
        self,
        n_arms: int,
        gamma: float = 0.1,
        alpha: float = 1.0 / 1000.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        super().__init__(n_arms, rng=rng)
        if not 0.0 < gamma <= 1.0:
            raise ValueError(f"gamma must be in (0, 1]; got {gamma}")
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"alpha must be in [0, 1]; got {alpha}")
        self.gamma = float(gamma)
        self.alpha = float(alpha)
        self._weights = np.ones(n_arms, dtype=np.float64)
        self._last_probs = np.ones(n_arms, dtype=np.float64) / n_arms

    def _probs(self) -> np.ndarray:
        total_w = float(self._weights.sum())
        if total_w <= 0.0:
            return np.ones(self.n_arms) / self.n_arms
        return (1.0 - self.gamma) * (self._weights / total_w) + self.gamma / self.n_arms

    def _select_arm(self, t: int) -> int:
        probs = self._probs()
        self._last_probs = probs
        return int(self.rng.choice(self.n_arms, p=probs))

    def _update(self, arm: int, reward: float, t: int) -> None:
        prob_arm = max(self._last_probs[arm], 1e-12)
        x_hat = reward / prob_arm
        new_weights = self._weights.copy()
        new_weights[arm] = self._weights[arm] * math.exp(self.gamma * x_hat / self.n_arms)
        avg_weight = float(new_weights.mean())
        new_weights = (1.0 - self.alpha) * new_weights + self.alpha * avg_weight
        self._weights = new_weights


def select_bandit_by_regret(
    rewards_per_arm_per_step: np.ndarray,
    candidate_bandits: dict[str, Callable[[int, np.random.Generator], _BanditBase]],
    rng_seed: int,
) -> tuple[str, dict[str, float]]:
    """Select the per-instrument minimum-cumulative-regret bandit algorithm
    per [ADR-0018](../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-4.

    Parameters
    ----------
    rewards_per_arm_per_step : np.ndarray
        Shape ``(T, n_arms)`` calibration-holdout reward matrix.
    candidate_bandits : dict[str, Callable]
        Mapping from algorithm-name to a factory ``(n_arms, rng) -> _BanditBase``.
    rng_seed : int
        Per-replicate seed for deterministic reproducibility.

    Returns
    -------
    winner : str
        Algorithm-name of the minimum-final-cumulative-regret bandit.
    regret_table : dict[str, float]
        Mapping from algorithm-name to final cumulative regret value.

    Examples
    --------
    >>> rewards = np.random.default_rng(0).normal(size=(100, 3))
    >>> candidates = {
    ...     "d_ucb": lambda k, r: DUCBBandit(k, discount_factor=0.99, rng=r),
    ...     "sw_ucb": lambda k, r: SWUCBBandit(k, window=50, rng=r),
    ... }
    >>> winner, regrets = select_bandit_by_regret(rewards, candidates, rng_seed=42)
    """
    T, n_arms = rewards_per_arm_per_step.shape
    regret_table: dict[str, float] = {}
    for name, factory in candidate_bandits.items():
        rng = np.random.default_rng(rng_seed)
        bandit = factory(n_arms, rng)
        if bandit.algorithm_name != name and name != "":
            pass
        result = bandit.run(rewards_per_arm_per_step)
        regret_table[name] = float(result.cumulative_regret[-1])

    winner = min(regret_table.keys(), key=lambda k: regret_table[k])
    return winner, regret_table
