"""Walk-forward HMM warm-vs-cold filter diagnostic.

Captures the divergence between the production warm-start posterior
(:meth:`GaussianHMM.filter_states_from_prior`, seeded from the
train-fold terminal log α propagated K transition steps per
[ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)
§"Fold-boundary state continuity") and the cold-start regression
baseline (:meth:`GaussianHMM.filter_states`, seeded from ``log π``).

Purpose
-------

The diagnostic is a *passive observer* of the production filter: at
each walk-forward fold boundary it computes both posterior paths over
the same test fold and records per-bar divergence statistics. The
production output of the orchestrator's `_predict_fold` remains the
warm-start path; the cold-start path is computed only for the
diagnostic record and is discarded after summary statistics are
extracted. The diagnostic does not enter the model output, prediction
vector, or trading signal.

Use case: detect a future regression in the warm-start invariant —
for instance, a refactor that silently re-routes the orchestrator
through `filter_states` (cold) instead of `filter_states_from_prior`
(warm), or a transition-matrix corruption that flattens the warm-cold
gap. Per-fold divergence values are emitted to
``logs/reproducibility/{run_id}_warm_cold_diagnostic.json`` so a CI /
inspection step can assert that warm-vs-cold divergence remains
non-trivial under expected slow-mixing dynamics.

Divergence metric: Hellinger
----------------------------

The diagnostic uses the **Hellinger distance** between the per-bar
warm and cold filtered posteriors (Le Cam 1986 (general Hellinger /
total variation reference; specific inequality used here is Tsybakov
2009 §2.4)). For two N-state probability vectors ``p`` and ``q``,
the Hellinger distance is

    H(p, q) = (1 / sqrt(2)) * sqrt(sum_i (sqrt(p_i) - sqrt(q_i))^2).

Properties:

  - Bounded in ``[0, 1]`` for probability vectors. ``0`` iff the two
    distributions are identical; ``1`` iff their supports are
    disjoint. The bounded range yields portable cross-run summaries
    without per-fold rescaling.
  - Proper metric (symmetric, satisfies the triangle inequality)
    on the probability simplex (Le Cam 1986, general reference).
  - Convex in each argument; well-behaved under near-deterministic
    transitions where the symmetric Kullback–Leibler divergence
    diverges to ``+∞`` and would dominate summary statistics from a
    single near-degenerate bar (Cover & Thomas 2006 §2 — KL is
    unbounded; warm-vs-cold posteriors near a fold boundary often
    lie on near-orthogonal probability vectors when the transition
    matrix is near-identity, the very regime where the warm-cold
    divergence is largest and most worth detecting).

Total-variation distance (Tsybakov 2009 §2.4)

    TV(p, q) = (1/2) * sum_i |p_i - q_i|

is emitted as a secondary metric. Tsybakov 2009 §2.4, restated under
the bounded-Hellinger normalisation used here
(``H = (1/sqrt(2)) ||sqrt(p) - sqrt(q)||_2``, so ``H ∈ [0, 1]``),
gives the upstream/downstream envelope

    H(p, q)^2  <=  TV(p, q)  <=  H(p, q) * sqrt(2 - H(p, q)^2).

Derivation: the Tsybakov 2009 §2.4 inequality uses an unnormalised
Hellinger ``H_T^2 = sum_i (sqrt(p_i) - sqrt(q_i))^2`` (so
``H_T = sqrt(2) * H``); substituting yields the bounds above. The
right-hand side is monotone increasing in ``H`` on ``[0, 1]`` and
equals ``H`` only at ``H = 1`` (disjoint supports). The bound
``TV <= H`` is *not* tight in general under the normalised Hellinger
(counter-example: ``p = (0.99, 0.01)``, ``q = (0.01, 0.99)`` has
``TV = 0.98`` and ``H ≈ 0.895``, so ``TV > H``). Earlier audit drafts
used the wrong direction; the corrected envelope above is what the
per-fold ``le_cam_envelope_holds`` flag asserts. Precise lemma /
equation pinning within Tsybakov 2009 §2.4 deferred to follow-up
``P1-HMM-WARM-COLD-TSYBAKOV-PIN-VERIFY``.

KL divergence is *not* used because near-deterministic transition
matrices, which are exactly the slow-mixing regime where the
warm-cold diagnostic is most sensitive, make KL diverge — a single
near-degenerate bar can dominate any KL aggregate (Cover & Thomas
2006 §2.3; "infinity" is not a useful warm-cold-regression signal).

Threshold rule
--------------

This iteration emits raw values without a regression-detection
threshold. ``~/.claude/CLAUDE.md`` "Parameter & Prompt Selection"
prohibits arbitrary thresholds; no published threshold rule for HMM
warm-vs-cold filter divergence was located in literature search
(Hamilton 1989; Hamilton 1994; Kim & Nelson 1999;
Frühwirth-Schnatter 2006; López de Prado 2018; Le Cam 1986;
Tsybakov 2009 — the closest precedent is Le Cam's inequality, which
is a deterministic envelope, not a regression-detection rule). A
future ADR may calibrate a per-fold null reference (no-purge K=0
agreement under shared seed yields exact equality up to floating-
point noise) and emit z-scores; for now the diagnostic publishes
raw per-fold means / max / counts and the CI consumer asserts
non-zero mean under known slow-mixing test substrate. Tracked under
follow-up `P1-HMM-WARM-COLD-THRESHOLD-ADR` if a threshold rule
becomes load-bearing.

Causality
---------

The diagnostic is causal: at each fold boundary, both the warm and
cold paths are computed using only the test-fold observations they
would normally consume (the warm path additionally reads the
train-fold terminal posterior, which is itself a function only of
the train-fold observations). No future test-fold information is
read by either path. The diagnostic does not modify the production
warm path; it observes it.

References
----------

  - Le Cam, L. M. (1986). *Asymptotic Methods in Statistical
    Decision Theory*. Springer-Verlag, ISBN 978-1-4612-9343-3.
    https://doi.org/10.1007/978-1-4612-4946-7
    General Hellinger / total variation reference; the specific
    inequality used at runtime here traces to Tsybakov 2009 §2.4.
  - Tsybakov, A. B. (2009). *Introduction to Nonparametric
    Estimation*. Springer, ISBN 978-0-387-79051-0, §2.4 "Distances
    between distributions".
    https://doi.org/10.1007/b13794
  - Cover, T. M., & Thomas, J. A. (2006). *Elements of Information
    Theory*, 2nd ed. Wiley, ISBN 978-0-471-24195-9, §2.3 "Relative
    entropy and mutual information".
    https://doi.org/10.1002/047174882X
  - Kullback, S., & Leibler, R. A. (1951). "On information and
    sufficiency". *Annals of Mathematical Statistics* 22(1):79-86.
    https://doi.org/10.1214/aoms/1177729694 (KL — discussed but not
    used as the primary metric for the reasons above).
  - Hamilton, J. D. (1989). "A new approach to the economic analysis
    of nonstationary time series and the business cycle".
    *Econometrica* 57(2):357-384, §3. https://doi.org/10.2307/1912559
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from skie_ninja.models.regime.hmm import GaussianHMM
from skie_ninja.utils.hashing import file_sha256

SCHEMA_VERSION = "warm_cold_diagnostic_v1"

# Posterior arrays are (T, N): time × n_states. Used in shape validation.
_EXPECTED_POSTERIOR_NDIM = 2


# ---------------------------------------------------------------------------
# Pointwise divergence primitives
# ---------------------------------------------------------------------------


def hellinger_distance_rows(p: npt.NDArray[np.float64], q: npt.NDArray[np.float64]) -> np.ndarray:
    """Per-row Hellinger distance between two ``(T, N)`` posterior
    arrays.

    H(p, q) = (1 / sqrt(2)) * sqrt(sum_i (sqrt(p_i) - sqrt(q_i))^2)

    Defined on the probability simplex; returns values in ``[0, 1]``.
    Le Cam 1986 (general reference); Tsybakov 2009 §2.4 (specific
    inequality used in ``le_cam_envelope_holds``).

    Parameters
    ----------
    p, q
        ``(T, N)`` arrays whose rows are probability distributions.
        Caller is responsible for normalisation; this function does
        not re-normalise.

    Returns
    -------
    ``(T,)`` Hellinger distances.
    """
    p_arr = np.asarray(p, dtype=np.float64)
    q_arr = np.asarray(q, dtype=np.float64)
    if p_arr.shape != q_arr.shape:
        raise ValueError(
            f"hellinger_distance_rows: shape mismatch p={p_arr.shape}, q={q_arr.shape}."
        )
    if p_arr.ndim != _EXPECTED_POSTERIOR_NDIM:
        raise ValueError(f"hellinger_distance_rows: expected (T, N) arrays; got {p_arr.ndim}-D.")
    # Negative entries violate the simplex assumption; clip to 0 to
    # avoid sqrt of a tiny negative produced by floating-point noise
    # in the upstream softmax-normalised log α (this is bounded by
    # numpy's float64 precision, not a tunable parameter).
    p_safe = np.clip(p_arr, 0.0, None)
    q_safe = np.clip(q_arr, 0.0, None)
    diff = np.sqrt(p_safe) - np.sqrt(q_safe)
    sq = np.einsum("tn,tn->t", diff, diff)
    return np.sqrt(0.5 * sq)


def total_variation_rows(p: npt.NDArray[np.float64], q: npt.NDArray[np.float64]) -> np.ndarray:
    """Per-row total-variation distance between two ``(T, N)`` posteriors.

    TV(p, q) = (1/2) * sum_i |p_i - q_i|

    Tsybakov 2009 §2.4 (substituted under bounded Hellinger
    normalisation ``H = (1/sqrt(2)) * ||sqrt(p) - sqrt(q)||_2``)
    yields ``H^2 <= TV <= H * sqrt(2 - H^2)``. Returned as a
    secondary metric for the per-fold ``le_cam_envelope_holds``
    sanity flag.
    """
    p_arr = np.asarray(p, dtype=np.float64)
    q_arr = np.asarray(q, dtype=np.float64)
    if p_arr.shape != q_arr.shape:
        raise ValueError(f"total_variation_rows: shape mismatch p={p_arr.shape}, q={q_arr.shape}.")
    if p_arr.ndim != _EXPECTED_POSTERIOR_NDIM:
        raise ValueError(f"total_variation_rows: expected (T, N) arrays; got {p_arr.ndim}-D.")
    return 0.5 * np.sum(np.abs(p_arr - q_arr), axis=1)


# ---------------------------------------------------------------------------
# Per-fold record + run-level sidecar
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WarmColdFoldRecord:
    """Per-fold warm-vs-cold filter divergence statistics.

    All fields are summary statistics of the row-wise Hellinger /
    total-variation arrays over the test fold. Per-row arrays are
    not persisted to keep the sidecar size bounded; the summaries
    are sufficient for regression detection.
    """

    fold_id: int
    n_test_bars: int
    n_propagation_steps: int
    train_terminal_position: int
    test_first_position: int
    n_states: int
    hellinger_mean: float
    hellinger_max: float
    hellinger_at_first_test_bar: float
    total_variation_mean: float
    total_variation_max: float
    total_variation_at_first_test_bar: float
    le_cam_envelope_holds: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "fold_id": self.fold_id,
            "n_test_bars": self.n_test_bars,
            "n_propagation_steps": self.n_propagation_steps,
            "train_terminal_position": self.train_terminal_position,
            "test_first_position": self.test_first_position,
            "n_states": self.n_states,
            "hellinger_mean": self.hellinger_mean,
            "hellinger_max": self.hellinger_max,
            "hellinger_at_first_test_bar": self.hellinger_at_first_test_bar,
            "total_variation_mean": self.total_variation_mean,
            "total_variation_max": self.total_variation_max,
            "total_variation_at_first_test_bar": (self.total_variation_at_first_test_bar),
            "le_cam_envelope_holds": self.le_cam_envelope_holds,
        }


@dataclass
class WarmColdDiagnostic:
    """Run-level collector for warm-vs-cold per-fold records.

    The orchestrator instantiates one of these per run, calls
    :meth:`observe_fold` once per fold boundary, and at run end
    serialises the collected records via :func:`write_sidecar`.
    """

    schema_version: str = SCHEMA_VERSION
    metric_primary: str = "hellinger"
    metric_secondary: str = "total_variation"
    metric_reference: str = (
        "Tsybakov 2009 Section 2.4 (doi:10.1007/b13794); "
        "Le Cam 1986 (doi:10.1007/978-1-4612-4946-7) general reference"
    )
    fold_records: list[WarmColdFoldRecord] = field(default_factory=list)

    def observe_fold(
        self,
        *,
        fold_id: int,
        warm_posterior: npt.NDArray[np.float64],
        cold_posterior: npt.NDArray[np.float64],
        n_propagation_steps: int,
        train_terminal_position: int,
        test_first_position: int,
    ) -> WarmColdFoldRecord:
        """Compute per-fold divergence summaries and append a record.

        Both posterior arrays must be ``(T, N)``-shaped, row-wise
        normalised, and over the same test fold. The function does
        not run the filters itself — the orchestrator passes in the
        already-computed posteriors so the diagnostic remains a
        passive observer of the production warm path and consumes
        the cold path only for the comparison.
        """
        warm = np.asarray(warm_posterior, dtype=np.float64)
        cold = np.asarray(cold_posterior, dtype=np.float64)
        if warm.shape != cold.shape:
            raise ValueError(f"observe_fold: warm shape {warm.shape} != cold shape {cold.shape}.")
        if warm.ndim != _EXPECTED_POSTERIOR_NDIM or warm.shape[0] == 0:
            raise ValueError(f"observe_fold: posteriors must be (T>=1, N); got {warm.shape}.")
        h = hellinger_distance_rows(warm, cold)
        tv = total_variation_rows(warm, cold)
        # Tsybakov 2009 §2.4, restated under the bounded-Hellinger
        # normalisation H = (1/sqrt(2)) * ||sqrt(p) - sqrt(q)||_2:
        #   H(p,q)^2  <=  TV(p,q)  <=  H(p,q) * sqrt(2 - H(p,q)^2).
        # Floating-point slack bounded by the float64 epsilon
        # accumulated across the (sqrt, square, sum) chain on N-state
        # vectors. Exact bound is N * machine-eps * O(1); 1e-12 is a
        # defensive cap that scales with N up to ~10^4. Not a tunable
        # threshold — a deterministic float64 sanity check.
        tol = 1e-12
        h_sq = h * h
        # Clip H^2 inside sqrt to avoid sqrt of a tiny negative under
        # float-noise when H is exactly 1 (disjoint-supports edge).
        upper = h * np.sqrt(np.clip(2.0 - h_sq, 0.0, None))
        envelope_ok = bool(np.all(h_sq <= tv + tol) and np.all(tv <= upper + tol))
        rec = WarmColdFoldRecord(
            fold_id=int(fold_id),
            n_test_bars=int(warm.shape[0]),
            n_propagation_steps=int(n_propagation_steps),
            train_terminal_position=int(train_terminal_position),
            test_first_position=int(test_first_position),
            n_states=int(warm.shape[1]),
            hellinger_mean=float(np.mean(h)),
            hellinger_max=float(np.max(h)),
            hellinger_at_first_test_bar=float(h[0]),
            total_variation_mean=float(np.mean(tv)),
            total_variation_max=float(np.max(tv)),
            total_variation_at_first_test_bar=float(tv[0]),
            le_cam_envelope_holds=envelope_ok,
        )
        self.fold_records.append(rec)
        return rec

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "metric_primary": self.metric_primary,
            "metric_secondary": self.metric_secondary,
            "metric_reference": self.metric_reference,
            "n_folds": len(self.fold_records),
            "folds": [r.to_dict() for r in self.fold_records],
        }


# ---------------------------------------------------------------------------
# Convenience: run both filters and observe in a single call
# ---------------------------------------------------------------------------


def compute_warm_cold_posteriors(
    *,
    hmm: GaussianHMM,
    test_observations: npt.NDArray[np.float64],
    log_alpha_prior: npt.NDArray[np.float64],
    n_propagation_steps: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute warm and cold posteriors for the same test fold.

    Convenience wrapper for orchestrators that prefer to delegate
    both filter calls to a single helper. The warm path is the
    production filter (``filter_states_from_prior``); the cold path
    is the regression baseline (``filter_states``, seeded from
    ``log_pi``).

    Returns
    -------
    (warm_posterior, cold_posterior)
        ``(T, N)`` arrays whose rows sum to 1.
    """
    warm = hmm.filter_states_from_prior(
        test_observations,
        log_alpha_prior=log_alpha_prior,
        n_propagation_steps=n_propagation_steps,
    )
    cold = hmm.filter_states(test_observations)
    return warm, cold


# ---------------------------------------------------------------------------
# Sidecar I/O
# ---------------------------------------------------------------------------


def sidecar_path_for(run_id: str, *, logs_reproducibility_dir: Path) -> Path:
    """Canonical sidecar location.

    ``logs/reproducibility/{run_id}_warm_cold_diagnostic.json``,
    matching the ADR-0005 sidecar naming convention.
    """
    return Path(logs_reproducibility_dir) / f"{run_id}_warm_cold_diagnostic.json"


def write_sidecar(diagnostic: WarmColdDiagnostic, path: Path) -> tuple[Path, str]:
    """Atomically write the diagnostic JSON and return ``(path, sha256)``.

    Same atomicity pattern as :func:`HMMSidecar.write_sidecar` —
    tempfile in target directory, ``fsync``, ``os.replace``. Readers
    never observe a partial file. The returned ``sha256`` is intended
    to be passed to
    :func:`skie_ninja.utils.reproducibility.with_model_hash` (or
    rolled into a multi-sidecar hash) so the diagnostic is bound to
    the run's ReproLog.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(diagnostic.to_dict(), sort_keys=True, indent=2, ensure_ascii=False).encode(
        "utf-8"
    )
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)
    return path, file_sha256(path)
