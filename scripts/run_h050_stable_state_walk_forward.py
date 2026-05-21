"""H050.stable-state walk-forward orchestrator (Phase O.20).

Closes ``P1-H050-STABLE-STATE-WALK-FORWARD-ORCHESTRATOR-IMPL`` per
[H050_stable_state/design.md §5][1] + [§11.2 BLOCKING precondition][1].

The H050.stable-state hypothesis is a genetic-successor mechanism-
discrimination variant of H050 v1 per [ADR-0027 §D-4][2]. Per the parent
[INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo][3] §6.3 +
§6.6 + §7.3 Variant B, H050 v1 catastrophically underperformed on both
ES + NQ (realized OOS -81% / -84%; T_H050 LW2008 CI excluded zero on the
NEGATIVE side). The closure memo decomposed the mechanism: H-c whipsaw
was PRIMARY (30.33% forced gate transition rate on a 337,837-bar ES OOS
fold; median active-run length = 3 bars; cost-drag 1.87×-5.66× signal
magnitude) and H-b anti-selection was SECONDARY. H050.stable-state tests
the H-c sub-hypothesis empirically by ADDING an N-bar state-stability-
confirmation filter at the gate-engagement layer: the gate fires only
after the chosen state has held the modal posterior for N consecutive
bars. If H-c dominates, raising N monotonically reduces forced flips
and improves realized OOS toward neutral. If H-b dominates instead,
stabilising the state will LOCK the gate into the worse-Sharpe state
and produce monotonically WORSE realized OOS as N rises — paired with
the sibling [H050.invert][4] this discriminates the two mechanisms.

All other H050 v1 §1-§7 mechanic specifications are preserved verbatim
per ADR-0027 §D-4 "preserved infrastructure" — same substrate
(post-Phase-O.10 canonical SHA ``317429e4...``), same features (4
microstructure features), same labels (triple-barrier + Yang-Zhang
volatility), same LightGBM hyperparameter grid (3 × 2 × 2 = 12 cells +
N_draws=200 random search), same purged walk-forward splitter, same
NT8-realistic cost model, same canonical state-ordering rule
(highest-mean state per ADR-0005). The single divergence is the N-bar
state-stability filter at the gate-engagement layer.

Pre-registered N grid (per design.md §5; BLOCKING — must be exercised
at v1 production walk-forward emission per design.md §11.2):
``{3, 5, 10, 20}`` at 1-min cadence. Inner-CV selection is NOT applied:
each N is emitted as its own cell in the per-fold sidecar, and Hansen
SPA + Romano-Wolf FWER aggregate across the 4-N × 2-symbol family per
design.md §8.

This wrapper invokes the canonical H050 orchestrator one cell at a time
via ``--stable-state-n N``. Operator runs the wrapper four times (once
per N) to sweep the pre-registered grid; results are aggregated by the
operator's downstream KPI-emission cycle. The wrapper enforces
``--hypothesis H050_stable_state`` + ``--config
config/hypotheses/H050_stable_state.yaml`` invariants and requires
``--stable-state-n N`` from the caller (no default — operator must
explicitly choose N from the registered grid).

Execution model
---------------
This script is a thin CLI wrapper around the canonical H050 orchestrator
[scripts/run_walk_forward.py][5]. It invokes the underlying ``run()``
entry with ``--hypothesis H050_stable_state``, ``--config
config/hypotheses/H050_stable_state.yaml``, and ``--stable-state-n N``
forwarded from the caller. The ``--stable-state-n`` flag patches the
module-level ``_STABLE_STATE_N`` integer consumed at the single
gate-engagement site in ``_predict_fold`` (after
``filter_states_from_prior`` produces the per-bar posterior). All
other code paths (HMM fit cache, ReproLog 13-field emission, fold-
warm-start contract per ADR-0005, sidecar SHA, LW2008 differential CI,
Hansen SPA, BLAS pinning per ADR-0009, supervised-run integration per
ADR-0010/0011) are reused verbatim from H050 v1.

Other CLI flags from the H050 orchestrator pass through transparently
(``--smoke``, ``--dry-run``, ``--no-hmm-cache``, ``--symbols``,
``--lgb-seed``, etc.). The canonical smoke command (for N=5) is::

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    uv run python scripts/run_h050_stable_state_walk_forward.py \
        --stable-state-n 5 --smoke

The canonical full-production command (for N=5) is::

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    uv run python scripts/supervised_run.py \
        --hypothesis H050_stable_state \
        --config config/hypotheses/H050_stable_state.yaml \
        --extra-args "--stable-state-n 5"

Operator sweeps the pre-registered N grid by repeating the command for
N ∈ {3, 5, 10, 20}; each run emits its own sidecar JSON via
``RunContext`` per ADR-0013 §3.1 reproducibility envelope.

References
----------

[1]: research/01_hypothesis_register/H050_stable_state/design.md
[2]: docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md
[3]: research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md
[4]: research/01_hypothesis_register/H050_invert/design.md
[5]: scripts/run_walk_forward.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the canonical H050 walk-forward orchestrator. This module
# already exports the ``run()`` entry + ``_parse_args()`` helper; the
# ``--stable-state-n`` flag added in Phase O.20 is consumed at parse
# time to set the module-level ``_STABLE_STATE_N`` state. We do not
# re-implement the pipeline; we wire the stability-filter parameter
# into the canonical entry.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import scripts.run_walk_forward as _h050_orchestrator  # noqa: E402


def _resolve_h050_stable_state_argv(argv: list[str] | None) -> list[str]:
    """Resolve CLI args with H050.stable-state defaults applied.

    The wrapper enforces three invariants on the underlying H050
    orchestrator's argv:

    1. ``--hypothesis H050_stable_state`` is forced (overrides any
       caller value); operator cannot accidentally launch this script
       against an unrelated hypothesis.
    2. ``--config config/hypotheses/H050_stable_state.yaml`` is the
       default when not supplied; operator may override only to point
       at a sibling H050.stable-state config (e.g. a calibration-
       holdout variant).
    3. ``--stable-state-n N`` MUST be supplied by the caller. The
       wrapper does NOT inject a default N because each value in the
       pre-registered grid {3, 5, 10, 20} per design.md §5 is its own
       hypothesis-of-record cell and must be exercised explicitly.
       Raises ValueError if the caller did not supply ``--stable-state-n``.
    """
    if argv is None:
        argv = list(sys.argv[1:])
    else:
        argv = list(argv)

    # Verify --stable-state-n is present in caller's argv. We do NOT
    # inject a default because each N in the pre-registered grid is its
    # own cell in the 4-N family per design.md §5.
    has_stable_state_n = any(
        tok == "--stable-state-n" or tok.startswith("--stable-state-n=")
        for tok in argv
    )
    if not has_stable_state_n:
        raise ValueError(
            "scripts/run_h050_stable_state_walk_forward.py requires "
            "--stable-state-n N to be supplied explicitly. Pre-registered "
            "grid per H050.stable-state design.md §5: N in {3, 5, 10, 20} "
            "at 1-min cadence. Each N is its own cell in the 4-N family; "
            "no default is provided."
        )

    # Force --hypothesis H050_stable_state (strip caller-supplied value).
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
    out.extend(["--hypothesis", "H050_stable_state"])

    # Default --config if not supplied. Detect both space-separated and
    # equals-separated forms.
    has_config = any(
        tok == "--config" or tok.startswith("--config=") for tok in out
    )
    if not has_config:
        default_config = (
            _REPO_ROOT / "config" / "hypotheses" / "H050_stable_state.yaml"
        )
        out.extend(["--config", str(default_config)])

    return out


def run(argv: list[str] | None = None) -> Path:
    """Entry point.

    Resolves the H050.stable-state defaults + invariants, then delegates
    to the canonical H050 walk-forward orchestrator. Returns the path to
    the canonical sidecar JSON written by ``RunContext`` per ADR-0013
    §3.1 reproducibility envelope.

    Raises ValueError if the caller did not supply ``--stable-state-n``.
    """
    resolved_argv = _resolve_h050_stable_state_argv(argv)
    return _h050_orchestrator.run(resolved_argv)


if __name__ == "__main__":
    # BLAS pinning per ADR-0009 is handled inside the canonical
    # orchestrator's ``run()`` entry via the explicit env-var
    # assertion + ``threadpoolctl.threadpool_limits(1)``. The canonical
    # launch command sets OMP/MKL/OPENBLAS thread counts at the shell
    # level; the orchestrator validates them at startup.
    run()
