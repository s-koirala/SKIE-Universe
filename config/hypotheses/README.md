# config/hypotheses/

Runtime config files for pre-registered hypotheses. One file per hypothesis ID, authored alongside the matching [research/01_hypothesis_register/{HNNN}/design.md](../../research/01_hypothesis_register/) pre-registration.

## Rationale

Keeping runtime config here (rather than inside each hypothesis folder) serves two purposes:

1. **Single import point** — `scripts/run_walk_forward.py --config config/hypotheses/H050.yaml` resolves without path games.
2. **Drift detection** — if the YAML here diverges from the pre-registration `design.md`, a pre-commit hook (TODO, tracked in [plan/buildouts/implementation-plan_2026-04-15.md](../../plan/buildouts/implementation-plan_2026-04-15.md)) flags the mismatch before a run is dispatched.

## Schema

Each file must conform to the skeleton emitted by `scripts/hypothesis_new.py` and include at minimum the `power` block per [implementation-plan §5.1](../../plan/buildouts/implementation-plan_2026-04-15.md).

## Active files

| Hypothesis | Status | Config file |
|---|---|---|
| H050 | designed | (pending — Cycle 6 deliverable) |
| H051 | designed | (pending — post-MVP-1) |
| H052a | designed | (pending — post-MVP-1) |
| H052b | designed | (vendor-gated on QQQ 0DTE chain) |
