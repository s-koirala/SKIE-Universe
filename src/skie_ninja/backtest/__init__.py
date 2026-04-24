"""Walk-forward backtest harness — Cycle 4 deliverable.

Canonical backtest infrastructure for every H0xx hypothesis starting
with H050 at Cycle 6. Composes with the Cycle-2 HAC/Sharpe-CI
primitives ([src/skie_ninja/inference/stats/](../inference/stats/))
and the Cycle-3 HMM toolkit ([src/skie_ninja/models/regime/](../models/regime/)).

References (authoritative — AFML Ch.7 §7.4.1-.3 and Ch.12 /
Bergmeir-Benítez 2012 / Varma-Simon 2006 + Cawley-Talbot 2010) are
enumerated in the submodule docstrings.

Exports
-------
``splits`` — :class:`SplitSpec`, :class:`Fold`,
:func:`walk_forward_split`, :func:`purged_kfold_split`,
:func:`cpcv_split` (scaffold; see ``P1-BACKTEST-CPCV``).

``engine.walk_forward`` — :class:`WalkForwardEngine` orchestrator with
the nested model-selection-inside-fold hook (Varma & Simon 2006;
Cawley & Talbot 2010). Consumes a :class:`SplitSpec`, a ``fit_fn``,
and a ``predict_fn``; emits per-fold predictions plus the run-ledger
parquet under ``logs/reproducibility/``.

``leak_canaries`` — the fold-boundary invariant check called by the
engine plus three adversarial canaries (future-return feature,
label-horizon > purge-window, fit consuming test observations), with
:class:`TracingArray` as the capability-proxy strengthening of
canary (c).
"""
