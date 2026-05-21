"""H050.invert walk-forward orchestrator (Phase O.20).

Closes ``P1-H050-INVERT-WALK-FORWARD-ORCHESTRATOR-IMPL`` per
[H050_invert/design.md §5][1] + [§11.2 BLOCKING precondition][1].

The H050.invert hypothesis is a genetic-successor mechanism-discrimination
variant of H050 v1 per [ADR-0027 §D-4][2]. Per the parent
[INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo][3] §6.6 +
§7.3 Variant A, H050 v1 catastrophically underperformed on both ES + NQ
(realized OOS -81% / -84%; T_H050 LW2008 CI excluded zero on the
NEGATIVE side). The closure memo decomposed the mechanism: H-c whipsaw
was PRIMARY (~30% forced gate transition rate, cost-drag 1.87×-5.66×
signal magnitude) and H-b anti-selection was SECONDARY (gate selects
worse-Sharpe state on both symbols). H050.invert tests the H-b
sub-hypothesis empirically by INVERTING the HMM gate-state selection
from H050 v1's canonical highest-mean state (per ADR-0005) to the
lowest-mean state.

All other H050 v1 §1-§7 mechanic specifications are preserved verbatim
per ADR-0027 §D-4 "preserved infrastructure" — same substrate
(post-Phase-O.10 canonical SHA ``317429e4...``), same features (4
microstructure features), same labels (triple-barrier + Yang-Zhang
volatility), same LightGBM hyperparameter grid (3 × 2 × 2 = 12 cells +
N_draws=200 random search), same purged walk-forward splitter, same
NT8-realistic cost model. The single divergence is the gate-state
selection criterion at the HMM regime layer.

Execution model
---------------
This script is a thin CLI wrapper around the canonical H050 orchestrator
[scripts/run_walk_forward.py][4]. It invokes the underlying ``run()``
entry with ``--hypothesis H050.invert``, ``--config
config/hypotheses/H050_invert.yaml``, and ``--invert-gate`` forced ON.
The ``--invert-gate`` flag patches a single module-level state
(``_INVERT_HMM_GATE``) consumed at the gate-state argmax site in
``_fit_fold_body`` (line ~1616). All other code paths (HMM fit cache,
ReproLog 13-field emission, fold-warm-start contract per ADR-0005,
sidecar SHA, LW2008 differential CI, Hansen SPA, BLAS pinning per
ADR-0009, supervised-run integration per ADR-0010/0011) are reused
verbatim from H050 v1.

Other CLI flags from the H050 orchestrator pass through transparently
(``--smoke``, ``--dry-run``, ``--no-hmm-cache``, ``--symbols``,
``--lgb-seed``, etc.). The canonical smoke command is::

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    uv run python scripts/run_h050_invert_walk_forward.py --smoke

The canonical full-production command is::

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    uv run python scripts/supervised_run.py \
        --hypothesis H050_invert \
        --config config/hypotheses/H050_invert.yaml \
        --extra-args "--invert-gate"

References
----------

[1]: research/01_hypothesis_register/H050_invert/design.md
[2]: docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md
[3]: research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md
[4]: scripts/run_walk_forward.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the canonical H050 walk-forward orchestrator. This module
# already exports the ``run()`` entry + ``_parse_args()`` helper; the
# ``--invert-gate`` flag added in Phase O.20 is consumed at parse time
# to set the module-level ``_INVERT_HMM_GATE`` state. We do not
# re-implement the pipeline; we wire the inversion flag into the
# canonical entry.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import scripts.run_walk_forward as _h050_orchestrator  # noqa: E402


def _resolve_h050_invert_argv(argv: list[str] | None) -> list[str]:
    """Resolve CLI args with H050.invert defaults applied.

    The wrapper enforces three invariants on the underlying H050
    orchestrator's argv:

    1. ``--hypothesis H050_invert`` is forced (overrides any caller
       value); operator cannot accidentally launch this script against
       an unrelated hypothesis.
    2. ``--config config/hypotheses/H050_invert.yaml`` is the default
       when not supplied; operator may override only to point at a
       sibling H050.invert config (e.g. a calibration-holdout variant).
    3. ``--invert-gate`` is unconditionally appended. The whole point
       of this wrapper is to set the gate-inversion flag; removing it
       would silently revert to H050 v1 semantics. The flag is
       idempotent (``store_true``).
    """
    if argv is None:
        argv = list(sys.argv[1:])
    else:
        argv = list(argv)

    # Force --hypothesis H050_invert (strip caller-supplied value).
    out: list[str] = []
    skip = False
    for tok in argv:
        if skip:
            skip = False
            continue
        if tok == "--hypothesis":
            skip = True
            continue
        if tok.startswith("--hypothesis="):
            continue
        out.append(tok)
    out.extend(["--hypothesis", "H050_invert"])

    # Default --config if not supplied. Detect both space-separated and
    # equals-separated forms.
    has_config = any(
        tok == "--config" or tok.startswith("--config=") for tok in out
    )
    if not has_config:
        default_config = _REPO_ROOT / "config" / "hypotheses" / "H050_invert.yaml"
        out.extend(["--config", str(default_config)])

    # Append --invert-gate (idempotent).
    if "--invert-gate" not in out:
        out.append("--invert-gate")

    return out


def run(argv: list[str] | None = None) -> Path:
    """Entry point.

    Resolves the H050.invert defaults + invariants, then delegates to
    the canonical H050 walk-forward orchestrator. Returns the path to
    the canonical sidecar JSON written by ``RunContext`` per ADR-0013
    §3.1 reproducibility envelope.
    """
    resolved_argv = _resolve_h050_invert_argv(argv)
    return _h050_orchestrator.run(resolved_argv)


if __name__ == "__main__":
    # BLAS pinning per ADR-0009 is handled inside the canonical
    # orchestrator's ``run()`` entry via the explicit env-var
    # assertion + ``threadpoolctl.threadpool_limits(1)``. The canonical
    # launch command sets OMP/MKL/OPENBLAS thread counts at the shell
    # level; the orchestrator validates them at startup.
    run()
