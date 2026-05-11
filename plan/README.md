# plan/

Operational planning artifacts: phase plans, engineering specs, hypothesis-specific buildouts, successor roadmaps. Distinct from the project-canonical **[hypothesis_backlog.md](../hypothesis_backlog.md)** (repo root) which catalogs every signal/transform/angle under research and is the single source of truth for what gets attempted.

## Layout

```
plan/
├── README.md                            # this file
└── buildouts/                           # dated buildout + roadmap artifacts
    ├── phases.md                        # 8-phase living execution plan (P0–P8)
    ├── implementation-plan_2026-04-15.md   # Phase-0/1 engineering spec with acceptance criteria
    ├── tier2b_buildout_2026-04-23.md    # 6-cycle critical path to H050 MVP-1
    ├── h053_buildout_2026-04-28.md      # H053 6-cycle buildout (Stages 0–3 → paper-trade)
    └── h055_successor_tree_2026-05-06.md   # H056–H059 + parallel-track roadmap
```

## Conventions

- **Dated buildouts**: filename pattern `{scope}_{description}_{YYYY-MM-DD}.md`. The date is the freeze date, not the last-edit date.
- **Successor versioning**: per [ADR-0013](../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4 non-loss mandate, supersession of a buildout produces a versioned successor (e.g., `h055_successor_tree_v2_YYYY-MM-DD.md`) that references the prior memo verbatim. The prior memo is never deleted or overwritten.
- **Status flips**: each buildout's per-cycle status (✓ done / [~] in-progress / [ ] pending) is updated in place; cycle-row content remains immutable once a stage transition lands.

## What's NOT in plan/

- **`hypothesis_backlog.md`** — promoted to repo root 2026-05-11 (project-canonical, broader scope than buildouts).
- **Per-hypothesis design.md + KPI report cards** — under [`research/01_hypothesis_register/{HID}/`](../research/01_hypothesis_register/).
- **Architecture decisions** — under [`docs/decisions/`](../docs/decisions/) (see [ADR index](../docs/decisions/README.md)).
- **Audit-remediate-loop trails** — under [`docs/audits/`](../docs/audits/) (append-only; protected by [`scripts/_hooks/check_non_loss_deletion.py`](../scripts/_hooks/check_non_loss_deletion.py)).
- **Research memos** — under [`docs/research_notes/`](../docs/research_notes/) (dated; postmortems, reassessments, retrospectives).

## Cross-references

- Active research front: [hypothesis_backlog.md](../hypothesis_backlog.md) §"At-a-glance status"
- Per-hypothesis stage tracker: [research/01_hypothesis_register/INDEX.md](../research/01_hypothesis_register/INDEX.md)
- Emitted KPI report cards: [research/01_hypothesis_register/RESULTS_INDEX.md](../research/01_hypothesis_register/RESULTS_INDEX.md)
