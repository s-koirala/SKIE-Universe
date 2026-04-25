"""Unit tests for the HMM walk-forward warm-vs-cold filter diagnostic.

Closes follow-up ``P1-HMM-WARM-COLD-DIAGNOSTIC``. The diagnostic is a
passive observer of the production warm-start filter
(:meth:`GaussianHMM.filter_states_from_prior`) versus the cold-start
regression baseline (:meth:`GaussianHMM.filter_states`); see
[ADR-0005](../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)
§"Fold-boundary state continuity" and the audit trail at
[docs/audits/audit_trail_2026-04-24_hmm-warm-cold-diagnostic.md].

Coverage
--------

  - Pointwise Hellinger and TV against published closed-form values
    (orthogonal supports; uniform vs delta; identical distributions).
  - Le Cam 1986 Lemma 15.1 inequality ``H(p,q)^2 / 2 <= TV(p,q) <=
    H(p,q)`` over a randomised property test.
  - Zero-divergence collapse: when the prior is set to ``log_pi`` and
    ``n_propagation_steps=0``, warm and cold filter outputs are
    bit-identical (zero Hellinger).
  - Non-zero divergence under a slow-mixing (near-identity)
    transition matrix and a non-stationary prior.
  - Monotonicity of mean Hellinger in K under slow-mixing transitions
    (a small-K sanity check; not a global monotonicity claim).
  - Determinism under fixed seed across two runs.
  - Sidecar SHA256 round-trip and ReproLog ``model_hash`` integration
    pattern.

References (full bibliographic entries)
---------------------------------------

  - Le Cam, L. M. (1986). *Asymptotic Methods in Statistical Decision
    Theory*. Springer-Verlag, ISBN 978-1-4612-9343-3, §15.
    https://doi.org/10.1007/978-1-4612-4946-7
  - Tsybakov, A. B. (2009). *Introduction to Nonparametric
    Estimation*. Springer, ISBN 978-0-387-79051-0, §2.4.
    https://doi.org/10.1007/b13794
  - Kullback, S., & Leibler, R. A. (1951). *Ann. Math. Stat.*
    22(1):79-86. https://doi.org/10.1214/aoms/1177729694
  - Hamilton, J. D. (1989). *Econometrica* 57(2):357-384, §3.
    https://doi.org/10.2307/1912559
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest
from scipy.special import logsumexp

from skie_ninja.models.regime import GaussianHMM
from skie_ninja.models.regime._core import (
    forward_log,
    forward_log_from_prior,
    log_emission_matrix,
)
from skie_ninja.models.regime.diagnostics import (
    SCHEMA_VERSION,
    WarmColdDiagnostic,
    WarmColdFoldRecord,
    compute_warm_cold_posteriors,
    hellinger_distance_rows,
    sidecar_path_for,
    total_variation_rows,
    write_sidecar,
)
from skie_ninja.utils.reproducibility import ReproLog, with_model_hash

# Numeric constants used in test assertions. Defined at module top to keep
# call sites free of magic-number lint flags (PLR2004).

# First-bar Hellinger lower bound under the slow-mixing weakly-separated
# fixture. Calibrated empirically: a regression that flattens warm-cold
# divergence to floating-point noise (~1e-12) clears this floor by 10
# orders of magnitude. Not a tunable threshold — a pure sanity floor
# separating "diagnostic is recording a real warm-cold gap" from
# "diagnostic is silently zero".
_FIRST_BAR_HELLINGER_FLOOR = 1e-2

# SHA256 hex digest length (bits=256, hex chars per byte=2 → 64).
_SHA256_HEX_LEN = 64

# Expected fold count for diagnostics built by ``_make_diag_for_run``
# (which iterates ``range(3)``).
_DIAG_RUN_N_FOLDS = 3

# ---------------------------------------------------------------------------
# Pointwise divergence primitives
# ---------------------------------------------------------------------------


def test_hellinger_zero_on_identical_rows() -> None:
    p = np.array([[0.6, 0.4], [0.1, 0.9]])
    np.testing.assert_allclose(hellinger_distance_rows(p, p), np.zeros(2), atol=1e-15)
    np.testing.assert_allclose(total_variation_rows(p, p), np.zeros(2), atol=1e-15)


def test_hellinger_orthogonal_supports_attains_unity() -> None:
    """Disjoint-support distributions: H = 1.

    For ``p = (1, 0)`` and ``q = (0, 1)``,
        H = sqrt(0.5 * ((1 - 0)^2 + (0 - 1)^2)) = 1.
    Le Cam 1986 §15 / Tsybakov 2009 §2.4 closed-form check.
    """
    p = np.array([[1.0, 0.0]])
    q = np.array([[0.0, 1.0]])
    np.testing.assert_allclose(hellinger_distance_rows(p, q), [1.0], atol=1e-15)
    np.testing.assert_allclose(total_variation_rows(p, q), [1.0], atol=1e-15)


def test_hellinger_uniform_vs_delta_closed_form() -> None:
    """Uniform on N=2 vs delta on state 0:
        p = (1, 0); q = (0.5, 0.5)
        H^2 = 0.5 * ((1 - sqrt(0.5))^2 + (0 - sqrt(0.5))^2)
            = 0.5 * (1 - 2 * sqrt(0.5) + 0.5 + 0.5)
            = 1 - sqrt(0.5)
        H   = sqrt(1 - 1/sqrt(2)).
    Hand-derived from Le Cam 1986 §15.
    """
    p = np.array([[1.0, 0.0]])
    q = np.array([[0.5, 0.5]])
    expected = np.sqrt(1.0 - 1.0 / np.sqrt(2.0))
    np.testing.assert_allclose(hellinger_distance_rows(p, q), [expected], atol=1e-12)
    # TV(uniform, delta) = 0.5 * (|1 - 0.5| + |0 - 0.5|) = 0.5.
    np.testing.assert_allclose(total_variation_rows(p, q), [0.5], atol=1e-15)


def test_tsybakov_inequality_holds_property() -> None:
    """Tsybakov 2009 Lemma 2.3 (eq. 2.20), restated under the
    normalised Hellinger ``H = (1/sqrt(2)) ||sqrt(p) - sqrt(q)||_2``:

        H^2 <= TV <= H * sqrt(2 - H^2).

    Property test over Dirichlet draws including a near-disjoint pair
    that breaks the naive ``TV <= H`` bound (counter-example:
    ``p = (0.99, 0.01)``, ``q = (0.01, 0.99)`` has TV ≈ 0.98 and
    H ≈ 0.895, so ``TV > H``).
    """
    rng = np.random.default_rng(2026_04_24)
    n_samples, n_states = 200, 5
    p = rng.dirichlet(np.ones(n_states), size=n_samples)
    q = rng.dirichlet(np.ones(n_states), size=n_samples)
    # Append the near-disjoint counter-example as a sanity case.
    p = np.vstack([p, np.array([[0.99, 0.01, 0.0, 0.0, 0.0]])])
    q = np.vstack([q, np.array([[0.01, 0.99, 0.0, 0.0, 0.0]])])
    h = hellinger_distance_rows(p, q)
    tv = total_variation_rows(p, q)
    h_sq = h * h
    upper = h * np.sqrt(np.clip(2.0 - h_sq, 0.0, None))
    assert np.all(h_sq <= tv + 1e-12)
    assert np.all(tv <= upper + 1e-12)


def test_pointwise_metrics_reject_shape_mismatch() -> None:
    p = np.zeros((3, 2))
    q = np.zeros((3, 3))
    with pytest.raises(ValueError, match="shape mismatch"):
        hellinger_distance_rows(p, q)
    with pytest.raises(ValueError, match="shape mismatch"):
        total_variation_rows(p, q)


def test_pointwise_metrics_reject_non_2d() -> None:
    p = np.zeros(5)
    q = np.zeros(5)
    with pytest.raises(ValueError, match="2-D|expected"):
        hellinger_distance_rows(p, q)


# ---------------------------------------------------------------------------
# Filter equivalence under canonical cold-start match
# ---------------------------------------------------------------------------


def _fitted_two_state_hmm(seed: int = 11) -> tuple[GaussianHMM, np.ndarray]:
    """Two-state HMM on a simulated regime-switching process.

    Switches with probability ``p_switch=0.02`` so dwell time is
    O(50) bars — slow-mixing in the warm-vs-cold sense.
    """
    rng = np.random.default_rng(seed)
    n = 600
    state = np.zeros(n, dtype=np.int64)
    p_switch = 0.02
    for i in range(1, n):
        state[i] = state[i - 1] if rng.random() > p_switch else 1 - state[i - 1]
    means = np.array([0.0, 3.0])
    variances = np.array([0.4, 0.4])
    obs = rng.normal(loc=means[state], scale=np.sqrt(variances[state])).reshape(-1, 1)
    hmm = GaussianHMM(n_states=2, covariance_type="diag")
    hmm.fit(obs, seed=seed, min_restarts=5, max_restarts=5)
    return hmm, obs


def test_zero_divergence_when_warm_seeded_with_log_pi_and_k_zero() -> None:
    """When the warm prior is the fitted ``log_pi`` and
    ``n_propagation_steps=0``, ``filter_states_from_prior`` reduces
    to the same recursion as ``filter_states`` over the test slice.
    Hellinger over the resulting posteriors must be ~0 (float-noise).
    """
    hmm, obs = _fitted_two_state_hmm(seed=37)
    test_obs = obs[400:]
    assert hmm.params_ is not None
    cold = hmm.filter_states(test_obs)
    warm = hmm.filter_states_from_prior(
        test_obs,
        log_alpha_prior=hmm.params_.log_pi.copy(),
        n_propagation_steps=0,
    )
    h = hellinger_distance_rows(warm, cold)
    np.testing.assert_allclose(h, np.zeros_like(h), atol=1e-12)


def test_non_zero_divergence_under_slow_mixing_warm_start() -> None:
    """Slow-mixing transitions + weakly separated emissions + a
    non-stationary prior produce material warm-vs-cold divergence
    at the first test bar (where the prior dominates). The
    first-bar Hellinger must be non-trivial — the regression we
    want to detect would push this back to floating-point noise.

    Setup: near-identity transition matrix (dwell time O(100)), low
    emission separation (mean gap 1.0 with std 1.0 → Bayes-error ~30%
    per bar), strongly biased warm prior. The cold filter starts from
    the fitted ``log_pi`` (≈ uniform) while the warm filter starts
    from the strongly biased prior; the warm-cold gap takes O(dwell)
    bars to close, so the first-bar Hellinger is large.
    """
    log_pi = np.log(np.array([0.5, 0.5]))
    transmat = np.array([[0.99, 0.01], [0.01, 0.99]])
    log_transmat = np.log(transmat)
    means = np.array([[0.0], [1.0]])
    variances = np.array([[1.0], [1.0]])
    rng = np.random.default_rng(2026_04_24 + 1)
    test = rng.normal(loc=0.5, scale=1.0, size=(50, 1))

    log_b_test = log_emission_matrix(test, means, variances, "diag")
    biased_prior = np.array([-50.0, 0.0])  # all mass on state 1
    log_alpha_warm, _ = forward_log_from_prior(
        log_alpha_prior=biased_prior,
        log_transmat=log_transmat,
        log_B=log_b_test,
        n_propagation_steps=10,
    )
    warm = np.exp(log_alpha_warm - logsumexp(log_alpha_warm, axis=1, keepdims=True))
    log_alpha_cold, _ = forward_log(log_pi, log_transmat, log_b_test)
    cold = np.exp(log_alpha_cold - logsumexp(log_alpha_cold, axis=1, keepdims=True))
    h = hellinger_distance_rows(warm, cold)
    assert float(h[0]) > _FIRST_BAR_HELLINGER_FLOOR, (
        f"expected non-trivial first-bar warm-cold divergence under "
        f"slow-mixing weakly-separated emissions; got H[0]={h[0]:.3e}."
    )


def test_mean_hellinger_monotonic_in_k_for_slow_mixing() -> None:
    """At small K, increasing the propagation steps with a fixed
    non-stationary prior should NOT decrease mean Hellinger faster
    than the convergence rate of A^K toward the stationary
    distribution. Concretely: under near-identity ``A``, the warm
    prior decays toward the stationary distribution slowly with K,
    so the warm-cold gap monotonically diminishes only after K
    exceeds the dwell-time scale. The test asserts the *direction*
    holds at small K (warm prior far from stationary): mean
    Hellinger at K=1 >= mean Hellinger at K=200 within a single
    fold's observations on a near-identity transition. This is a
    sanity sign-check, not a strict global monotonicity claim.
    """
    log_pi = np.log(np.array([0.5, 0.5]))
    transmat = np.array([[0.99, 0.01], [0.01, 0.99]])
    log_transmat = np.log(transmat)
    means = np.array([[0.0], [3.0]])
    variances = np.array([[0.5], [0.5]])
    rng = np.random.default_rng(101)
    test = rng.normal(loc=0.0, scale=1.0, size=(50, 1))

    log_b_test = log_emission_matrix(test, means, variances, "diag")
    # Strongly biased prior: all mass on state 1.
    biased_prior = np.array([-50.0, 0.0])

    # K matches ADR-0005 §"Fold-boundary state continuity" notation
    # (n_propagation_steps for the (A^K) prior-propagation operator).
    def _filter_warm(K: int) -> np.ndarray:  # noqa: N803 — ADR-0005 K-step convention
        log_alpha, _ = forward_log_from_prior(
            log_alpha_prior=biased_prior,
            log_transmat=log_transmat,
            log_B=log_b_test,
            n_propagation_steps=K,
        )
        return np.exp(log_alpha - logsumexp(log_alpha, axis=1, keepdims=True))

    # Cold path: filter_states-equivalent over the test slice (no prior).
    log_alpha_cold, _ = forward_log(log_pi, log_transmat, log_b_test)
    cold = np.exp(log_alpha_cold - logsumexp(log_alpha_cold, axis=1, keepdims=True))

    h_low = float(np.mean(hellinger_distance_rows(_filter_warm(1), cold)))
    h_high = float(np.mean(hellinger_distance_rows(_filter_warm(200), cold)))
    assert h_low >= h_high, (
        f"slow-mixing monotonicity sign-check failed: "
        f"H(K=1)={h_low:.4e}, H(K=200)={h_high:.4e}; expected H(1) >= H(200) "
        f"as A^K converges toward the stationary distribution."
    )


def test_observe_fold_records_cumulate_in_order() -> None:
    diag = WarmColdDiagnostic()
    rng = np.random.default_rng(2026)
    for fid in (3, 5, 7):  # non-contiguous fold ids
        warm = rng.dirichlet(np.ones(2), size=12)
        cold = rng.dirichlet(np.ones(2), size=12)
        diag.observe_fold(
            fold_id=fid,
            warm_posterior=warm,
            cold_posterior=cold,
            n_propagation_steps=2 + fid,
            train_terminal_position=100 * fid,
            test_first_position=100 * fid + 2 + fid,
        )
    assert [r.fold_id for r in diag.fold_records] == [3, 5, 7]
    assert all(r.le_cam_envelope_holds for r in diag.fold_records)


def test_observe_fold_rejects_shape_mismatch() -> None:
    diag = WarmColdDiagnostic()
    warm = np.zeros((4, 2))
    cold = np.zeros((4, 3))
    with pytest.raises(ValueError, match="warm shape"):
        diag.observe_fold(
            fold_id=0,
            warm_posterior=warm,
            cold_posterior=cold,
            n_propagation_steps=1,
            train_terminal_position=0,
            test_first_position=1,
        )


def test_observe_fold_rejects_empty_test_fold() -> None:
    diag = WarmColdDiagnostic()
    warm = np.zeros((0, 2))
    cold = np.zeros((0, 2))
    with pytest.raises(ValueError, match="must be"):
        diag.observe_fold(
            fold_id=0,
            warm_posterior=warm,
            cold_posterior=cold,
            n_propagation_steps=1,
            train_terminal_position=0,
            test_first_position=1,
        )


# ---------------------------------------------------------------------------
# Determinism + sidecar round-trip + ReproLog model_hash integration
# ---------------------------------------------------------------------------


def _make_diag_for_run(seed: int) -> WarmColdDiagnostic:
    diag = WarmColdDiagnostic()
    rng = np.random.default_rng(seed)
    for fid in range(3):
        warm = rng.dirichlet(np.ones(2), size=20)
        cold = rng.dirichlet(np.ones(2), size=20)
        diag.observe_fold(
            fold_id=fid,
            warm_posterior=warm,
            cold_posterior=cold,
            n_propagation_steps=fid + 1,
            train_terminal_position=100 * fid,
            test_first_position=100 * fid + fid + 1,
        )
    return diag


def test_diagnostic_deterministic_under_fixed_seed() -> None:
    d1 = _make_diag_for_run(seed=42)
    d2 = _make_diag_for_run(seed=42)
    assert d1.to_dict() == d2.to_dict()


def test_compute_warm_cold_posteriors_returns_consistent_shapes() -> None:
    hmm, obs = _fitted_two_state_hmm(seed=19)
    train = obs[:400]
    test = obs[400:]
    prior = hmm.terminal_log_alpha(train)
    warm, cold = compute_warm_cold_posteriors(
        hmm=hmm,
        test_observations=test,
        log_alpha_prior=prior,
        n_propagation_steps=3,
    )
    assert warm.shape == cold.shape == (test.shape[0], 2)
    np.testing.assert_allclose(warm.sum(axis=1), 1.0, atol=1e-10)
    np.testing.assert_allclose(cold.sum(axis=1), 1.0, atol=1e-10)


def test_sidecar_round_trip_and_sha256(tmp_path) -> None:
    diag = _make_diag_for_run(seed=7)
    out_path = sidecar_path_for(run_id="test_run_001", logs_reproducibility_dir=tmp_path)
    written, sha = write_sidecar(diag, out_path)
    assert written.exists()
    assert len(sha) == _SHA256_HEX_LEN
    raw = json.loads(written.read_text(encoding="utf-8"))
    assert raw["schema_version"] == SCHEMA_VERSION
    assert raw["n_folds"] == _DIAG_RUN_N_FOLDS
    assert raw["metric_primary"] == "hellinger"
    assert raw["metric_secondary"] == "total_variation"
    # Re-write same content → same sha (deterministic JSON canonicalisation).
    out_path2 = sidecar_path_for(run_id="test_run_002", logs_reproducibility_dir=tmp_path)
    _, sha2 = write_sidecar(diag, out_path2)
    assert sha == sha2


def test_sidecar_changes_hash_on_warm_cold_regression(tmp_path) -> None:
    """A simulated 'regression' that flattens warm-cold divergence to
    zero (e.g. a future refactor accidentally re-routing through
    ``filter_states`` for both paths) MUST flip the sidecar SHA256.
    This is the core regression-detection contract.
    """
    rng = np.random.default_rng(17)
    diag_normal = WarmColdDiagnostic()
    warm = rng.dirichlet(np.ones(2), size=20)
    cold = rng.dirichlet(np.ones(2), size=20)
    diag_normal.observe_fold(
        fold_id=0,
        warm_posterior=warm,
        cold_posterior=cold,
        n_propagation_steps=2,
        train_terminal_position=0,
        test_first_position=2,
    )
    diag_regressed = WarmColdDiagnostic()
    diag_regressed.observe_fold(
        fold_id=0,
        warm_posterior=warm,
        cold_posterior=warm.copy(),  # regression: warm == cold
        n_propagation_steps=2,
        train_terminal_position=0,
        test_first_position=2,
    )
    p1, sha_normal = write_sidecar(
        diag_normal,
        sidecar_path_for(run_id="r_normal", logs_reproducibility_dir=tmp_path),
    )
    p2, sha_regressed = write_sidecar(
        diag_regressed,
        sidecar_path_for(run_id="r_regressed", logs_reproducibility_dir=tmp_path),
    )
    assert sha_normal != sha_regressed, (
        "regression scenario produced an identical sidecar hash; "
        "diagnostic cannot detect a future warm-cold collapse."
    )


def test_with_model_hash_round_trip_into_reprolog(tmp_path) -> None:
    """End-to-end: build a diagnostic, write the sidecar, combine the
    SHA into ``ReproLog.model_hash`` via the ``with_model_hash``
    helper, round-trip through ``ReproLog.write`` / ``read``, and
    verify the persisted ``model_hash`` matches the combined value.
    Exercises the same multi-sidecar combiner pattern used by the
    walk-forward orchestrator.
    """
    diag = _make_diag_for_run(seed=2026)
    sidecar_path = sidecar_path_for(run_id="run_ABC", logs_reproducibility_dir=tmp_path)
    _, warm_cold_sha = write_sidecar(diag, sidecar_path)
    fake_ledger_rollup = "0" * 64
    combined = hashlib.sha256(
        f"ledger_rollup={fake_ledger_rollup};warm_cold_diag={warm_cold_sha}".encode()
    ).hexdigest()

    log = ReproLog(
        run_id="run_ABC",
        phase="walk_forward",
        hypothesis_id="H050",
        timestamp_utc="2026-04-24T00:00:00.000000+00:00",
        git_head="deadbeef",
        pip_freeze_sha256="0" * 64,
        pip_freeze_path="logs/reproducibility/env/0.txt",
        dataset_checksums={},
        rng_seed=42,
        model_hash=None,
        config_resolved_sha256="abcd",
        host={"os": "Test", "python": "3.11", "cpu": "x86_64"},
        env_id="test-env",
    )
    log = with_model_hash(log, combined)
    log_path = tmp_path / "run_ABC.json"
    log.write(log_path)
    round_tripped = ReproLog.read(log_path)
    assert round_tripped.model_hash == combined


def test_warm_cold_fold_record_to_dict_keys_stable() -> None:
    rec = WarmColdFoldRecord(
        fold_id=0,
        n_test_bars=10,
        n_propagation_steps=2,
        train_terminal_position=100,
        test_first_position=102,
        n_states=2,
        hellinger_mean=0.1,
        hellinger_max=0.2,
        hellinger_at_first_test_bar=0.15,
        total_variation_mean=0.05,
        total_variation_max=0.10,
        total_variation_at_first_test_bar=0.075,
        le_cam_envelope_holds=True,
    )
    expected_keys = {
        "fold_id",
        "n_test_bars",
        "n_propagation_steps",
        "train_terminal_position",
        "test_first_position",
        "n_states",
        "hellinger_mean",
        "hellinger_max",
        "hellinger_at_first_test_bar",
        "total_variation_mean",
        "total_variation_max",
        "total_variation_at_first_test_bar",
        "le_cam_envelope_holds",
    }
    assert set(rec.to_dict().keys()) == expected_keys
