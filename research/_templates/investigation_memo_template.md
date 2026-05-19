---
investigation_id: INVESTIGATE-FAILURE-MODE-{slug}
schema_version: investigation_memo_v1
created: YYYY-MM-DD
status: pending  # pending | active | complete-successor-pre-registered | complete-adr-amended | complete-no-further-action
hypothesis_of_investigation: H{NNN}  # primary hypothesis-of-record under investigation; multi-hypothesis spans MAY use comma-separated list
parent_kpi_report_card: research/01_hypothesis_register/H{NNN}/H{NNN}_kpi_report_v{N}.md  # the KPI emission that surfaced the anomaly
---

# Investigation Memo — {one-line-investigation-title}

Per [ADR-0027](../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) §D-1, this memo is the canonical artifact class for `INVESTIGATE-FAILURE-MODE-*` follow-ups. Investigation outputs do NOT use the ADR-0014 §3.2 13-table format; this template is the alternative artifact class. Per [ADR-0013](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss, this memo is immutable post-completion; corrections produce a versioned successor (e.g., `investigation_memo_{slug}_v2.md`).

## 1. Hypothesis-of-investigation

{One-sentence statement of the empirical anomaly to be investigated. Cite the parent KPI report card + the specific KPI value or annotation that surfaced the anomaly. Example: "H062 v3 produced realized OOS basket −99.9995% on the post-Phase-O.0 substrate with all three ADR-0025 primitives ON; decompose the catastrophic outcome by primitive engagement to discriminate cost-realistic-friction from kill-switch-asymmetry from equity-rebase-current."}

## 2. Decomposition plan

{The specific ablation / mechanism-probe / cross-cell comparison to execute. Enumerate every cell. Example: "3 ablations on the existing v3 fixture (run_id 154237b3...): (a) cost-only — kill-switch + equity-rebase OFF; (b) kill-switch-only — cost + equity-rebase OFF; (c) equity-rebase-only — cost + kill-switch OFF. Report per-primitive contribution to the −99.9995% delta. Optional 4th cell: all-OFF v2 baseline for sanity. Reproduce on the canonical substrate SHA {substrate-sha-16-prefix}..."}

## 3. Termination criterion

{Explicit condition under which the investigation closes. MUST be one of the 5 acceptable forms per ADR-0027 §D-1(c):
- (i) close when {specific decomposition / ablation / mechanism-probe} completes
- (ii) close when 3 rounds of audit-remediate-loop have been applied per SKILL.md 3-round cap
- (iii) close when operator-discretionary verdict logged at [logs/promotions/...]
- (iv) close when the underlying hypothesis-of-investigation is retired via ADR-0013 §1 stage transition
- (v) close when an upstream substrate change or paradigm shift makes the investigation moot (cross-reference superseding ADR / substrate vintage)
Investigations WITHOUT a termination criterion are R1-audit blockers.}

## 4. Wall-clock soft cap

{Rough estimate for project-priority planning. Example: "~2 hr per ablation × 3 = ~6 hr; cap at 8 hr." Per ADR-0027 §D-1(d) soft cap; overrun is allowed but requires per-overrun `# justify:` annotation appended below.}

| Estimate | Actual | Delta | Justify (if overrun) |
|---|---|---|---|
| {X hr} | {Y hr; populated on close} | {Y−X} | {required if delta>0} |

## 5. Output artifact spec

{Per ADR-0027 §D-1(e), one of:
- **investigation-memo** (default; this artifact) — ~1-2 page synthesis of decomposition + finding + implication; landed in `research/01_hypothesis_register/H{NNN}/` or `docs/research_notes/`
- **new hypothesis pre-registration successor** — when investigation surfaces a successor variant worth pre-registering per ADR-0027 §D-4 genetic-successor discipline
- **ADR amendment** — when investigation surfaces a paradigm shift worth codifying; subject to ADR-0027 §D-3 empirical-before-amendment sequencing rule
Specify which:}

- Output class: {investigation-memo | successor-pre-reg | adr-amendment}
- Cross-references: {cite related KPI cards, ADRs, prior investigations}

## 6. Findings

{Populated as the investigation progresses. Per-ablation rows for the decomposition plan + a synthesis paragraph at the end. Numeric findings should be SHA-bound to a sidecar where applicable.}

| Ablation # | Configuration | Sidecar SHA | Result summary | Per-primitive contribution to anomaly |
|---|---|---|---|---|
| 1 | {describe} | {sha} | {result} | {contribution analysis} |
| 2 | ... | ... | ... | ... |

### Synthesis

{1-2 paragraphs: what the decomposition shows; does it confirm / refute / partially support the original anomaly framing; what's the next operator-actionable inference.}

## 7. Implication

{What does this investigation imply for: (a) the parent hypothesis (retire / amend §17 revision-log / spawn successor); (b) project-level ADRs (does an amendment land per ADR-0027 §D-3 — i.e., after the empirical decomposition completes, not before); (c) future hypotheses (constraints to inherit; failure modes to canary against). Per ADR-0013 §4.1 the implication recommendations are operator-discretionary inputs, not binding actions.}

## 8. Closure

- **Closure date**: {YYYY-MM-DD; populated on close}
- **Closure type**: {one of: ablation-complete, audit-loop-3-rounds-applied, operator-verdict-logged, hypothesis-retired, substrate-obsolescence}
- **Closure verdict**: {one of: complete-successor-pre-registered, complete-adr-amended, complete-no-further-action}
- **Downstream artifacts produced**: {commit SHA + path of every artifact resulting from the investigation: successor design.md, ADR amendment, KPI re-emission, code primitive landing, etc.}

## Cross-references

- Parent KPI report card: see frontmatter `parent_kpi_report_card`
- Stage tracker: `../../research/01_hypothesis_register/H{NNN}/stage.md`
- Failure log: `../../research/01_hypothesis_register/H{NNN}/failure_log.md`
- Audit-remediate-loop trails: `../../docs/audits/audit_trail_YYYY-MM-DD_*.md`
- ADR-0027 §D-1 (this template's source mandate): [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)

## Append discipline

- Sections 1-5 are frozen at investigation start (post-pre-registration of the INVESTIGATE-FAILURE-MODE-* entry); they MAY be edited only via versioned-successor pattern per ADR-0013 §4.1.
- Sections 6-8 are APPEND-as-work-completes; rows in the §6 ablation table are immutable once landed.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../scripts/_hooks/check_non_loss_deletion.py).
