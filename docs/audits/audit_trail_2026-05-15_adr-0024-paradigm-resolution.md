# Audit trail — ADR-0024 paradigm resolution + README rewrite + Best-OOS showcase

**Date**: 2026-05-15
**Skill**: `audit-remediate-loop` (3-round cap per SKILL.md, anchored on [arXiv 2511.00751](https://arxiv.org/abs/2511.00751) operational cost/coverage choice)
**Final verdict**: ACCEPT (R3 zero findings)
**Deliverables**:
- [docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md](../decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) (new ADR)
- [docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md](../decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) (front-matter `status: proposed` → `accepted`)
- [README.md](../../README.md) (rewritten)
- [BEST_OOS.md](../../BEST_OOS.md) (new, auto-generated)
- [scripts/showcase_best_oos.py](../../scripts/showcase_best_oos.py) (new generator)
- [research/01_hypothesis_register/_oos_showcase_data.yaml](../../research/01_hypothesis_register/_oos_showcase_data.yaml) (new machine-readable cache)
- [.githooks/pre-push](../../.githooks/pre-push) (new pre-push hook)
- [research/01_hypothesis_register/H062/design.md](../../research/01_hypothesis_register/H062/design.md) §11.3 (drift correction)

## Round 1

### Parallel auditors

| Agent | Verdict | Findings |
|---|---|---|
| `quant-auditor` (agentId `a707b061662982cd6`) | block | 2 critical + 4 major + 5 minor |
| `literature-check` (agentId `af3f5c83eb4452756`) | accept | 0 findings (13 citations verified clean) |
| `reproducibility-verifier` (agentId `a3bd2165ad2e6726c`) | block | 1 critical + 2 major + 2 minor |

### Findings dispositioned

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| F1-001 | critical | `_oos_showcase_data.yaml` H050 entry | "Strongest cell" labeled ES unconditional (-43.69%) but the least-negative cell is NQ unconditional (-25.60%); ranking-semantic violation | Fixed: strongest_cell → "NQ unconditional"; strongest_cell_pct → -25.60 |
| F1-002 | critical | `_oos_showcase_data.yaml` H050 entry | forward_projection.p_loss_pct=100.0 (hmm_gated value) doesn't match labeled strongest cell | Fixed jointly with F1-001: p_loss_pct → 64.9 (NQ unconditional per H050 KPI §6) |
| R1-001 | critical | `_oos_showcase_data.yaml` H050 + H052a entries | strongest_cell_max_dd_pct: null violates the YAML's stated fidelity contract; KPI report cards report 45.02% (H050 ES uncond), 35.05% (H050 NQ uncond), 7.95% (H052a NQ uncond ORB) | Fixed: H050 strongest_cell_max_dd_pct → 35.05 (NQ unconditional per H050 KPI §2); H052a → 7.95 |
| F1-003 | major | `README.md` H062 row | "18 open BLOCKING preconditions" stale claim; actual count is 14 open / 27 total | Fixed: "14 open BLOCKING preconditions per design.md §11.2 (13 closed of 27 total)" |
| F1-004 | major | `ADR-0024` §"Empirical motivation" | "22 preconditions ... 13 remained open" did not match the H062 §11.2 table | Fixed: rewrote paragraph to "27 rows total: 13 closed, 14 open" + reconciled with CLAUDE.md ledger drift claim |
| F1-005 | major | `ADR-0024` Alternative C | "preserves ADR-0014 unchanged" contradicted the same ADR's front-matter `amends: ADR-0014 §3.2` | Fixed: Alternative C now correctly enumerates ADR-0014 in the amends list |
| F1-006 | major | `_oos_showcase_data.yaml` schema | hypothesis_of_record_arm_pct cherry-picks one symbol when arm spans two | Fixed: YAML header documents the "same-symbol-as-strongest_cell" convention; H050 + H052a values aligned |
| R1-002 | major | `scripts/showcase_best_oos.py:348` | `write_text` produced CRLF on Windows, breaking cross-platform byte-determinism | Fixed: added `newline="\n"` argument; verified LF-only via hexdump |
| R1-003 | major | `.githooks/pre-push:2` | Comment falsely claimed `bootstrap_env.py` installs hooksPath | Fixed: comment now correctly states manual one-time install step + cross-link to README §"Environment setup" |
| F1-007 | minor | `_oos_showcase_data.yaml` H050 oos_sessions | Joint with F1-001 | Fixed: 866 → 1726 (NQ session count) |
| F1-008 | minor | `scripts/showcase_best_oos.py:_rank_key` | Tie-break not documented | Fixed: rank_key now returns tuple `(pct, hypothesis_id, version)` with sorted(reverse=True) semantic documented in docstring |
| F1-009 | minor | `scripts/showcase_best_oos.py:_load_cards` | paradigm field not enum-validated | Fixed: added `_VALID_PARADIGMS = frozenset({...})` + post-load assertion |
| F1-010 | minor | `scripts/showcase_best_oos.py:_rank_key` | MPPM cutover branch not implemented | Fixed: docstring notes deferral to `P1-BEST-OOS-MPPM-RANKING-CUTOVER` |
| F1-011 | minor | `_oos_showcase_data.yaml` schema | paradigm-tag emission-time vs current semantic ambiguity | Fixed: schema header notes paradigm = emission-time |
| R1-004 | minor | `scripts/showcase_best_oos.py:42` | Missing `paths-guard: allow` marker per project convention | Fixed: marker added |
| R1-005 | minor | `.githooks/pre-push:26` | `2>/dev/null` suppressed script stderr | Fixed: stderr passes through to operator |

## Round 2

### Parallel auditors

| Agent | Verdict | Findings |
|---|---|---|
| `quant-auditor` (agentId `adc8cbdb22a7989ba`) | block | 1 critical + 3 major + 3 minor (downstream propagation gaps from R1) |
| `reproducibility-verifier` (agentId `ab42084e4e53a914c`) | accept | 0 findings (all R1 repro remediations verified) |

### Findings dispositioned

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| F2-001 | critical | `README.md:49` H050 row prose | Still quoted "ES unconditional ($10K → $5,631; −43.69%)" — F1-001's downstream propagation to README missed | Fixed: prose updated to "NQ unconditional ($10K → $7,440; −25.60%; max-DD 35.05%; forward P(loss) 64.9%)" + HoR arm disclosure |
| F2-002 | major | `ADR-0024:237` §"Empirical justification" | Still quoted "22 preconditions ... 13 remained open" (stale; F1-004 fixed §Context but not §Empirical-justification) | Fixed: rewrote to match line 45 count (27 / 13 closed / 14 open) |
| F2-003 | major | `BEST_OOS.md` all-cards table | Missing HoR-arm-OOS column despite ADR-0024 D-8 mandating "per-row mandatory disclosure of hypothesis-of-record arm vs strongest cell" | Fixed: extended `_render_table` to emit "HoR arm OOS" column; regenerated BEST_OOS.md now surfaces the H050 (−25.60% strongest vs −84.20% HoR) + H052a (+10.61% strongest vs +3.39% HoR) asymmetries |
| F2-004 | major | `H062 design.md §11.3` | Contradicted §11.2 row 319 (FM stress test CLOSED) by claiming "P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE — OPEN per Phase L Thread A" | Fixed: §11.3 reconciled with §11.2; FM stress test marked CLOSED; remaining residual (`P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`) noted as the only Phase L Thread A residual + ADR-0024 D-3 supersedence of the "BLOCKED" framing |
| F2-005 | minor | `ADR-0024:55` empirical motivation | Quoted "README §Current state table (line 32) labels H050 as Catastrophic" — line number stale; framing pre-amendment | Fixed: past-tense reframe + commit-SHA reference to HEAD `2f56bed3285a` (pre-this-ADR commit) |
| F2-006 | minor | `BEST_OOS.md:5` timestamp | Second-precision timestamp produced spurious 1-line diff on every push | Fixed: changed to date-only `%Y-%m-%d`; idempotent across same-day pushes verified (two consecutive runs produce byte-identical output) |
| F2-007 | minor | `ADR-0024:166` H050 reframing-table row | H050 "New framing" cell omitted strongest-cell datum; H052a/H053 rows did include it (asymmetric) | Fixed: appended "Strongest cell on this run: NQ unconditional −25.60% (max-DD 35.05%)" + AMH-relevant signal note |

## Round 3 (verification)

### Verifier

| Agent | Verdict | Findings |
|---|---|---|
| `quant-auditor` (agentId `aa0a94a2fd8d45adf`) | **accept** | **0** |

All R2 remediations verified at claimed locations. Internal cross-references reconcile (README ↔ BEST_OOS.md ↔ ADR-0024 §Context line 45 ↔ §Empirical-justification line 237 ↔ §Reframing line 166). Idempotency confirmed: two consecutive `uv run python scripts/showcase_best_oos.py` invocations produce byte-identical output (date-only timestamp). HoR column populated from YAML for all 5 live rows. No new inconsistencies introduced by R2 remediations.

## Final residual risk

Three project-level forward-work follow-ups remain registered (NOT residuals of this loop; pre-existing or registered concurrent with this ADR):

- `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE-EXTEND` (Phase O.1 follow-on) — systematic enumeration of CLAUDE.md ledger entries marked OPEN vs disk reality; the H062 22→27 / 13→14 count drift was symptomatic. Sweep across all 11 phase ledgers + per-hypothesis design.md §17 logs.
- `P1-BEST-OOS-MPPM-RANKING-CUTOVER` (ADR-0024 §Follow-ups) — implement the MPPM(ρ=1) ranking primary cutover in `scripts/showcase_best_oos.py` once MPPM is uniformly reported across all live KPI cards; currently only H060 reports MPPM(ρ=1).
- `P1-ADR-0024-DESIGN-MD-CASCADE` (ADR-0024 §Follow-ups, BLOCKING-BEFORE-NEXT-STAGE-3-RUN) — per-hypothesis design.md §10 + §11 cascade reframing across H050/H051/H052a/H052b/H053/H054/H055/H060/H062 to align with ADR-0024 D-1..D-7 + the new annotation grammar.

Cross-platform line-ending determinism verified on Windows (LF-only). Citation correctness verified by literature-check R1 (all 13 primary peer-reviewed sources resolve cleanly: Lo 2004 AMH, GISW 2007 MPPM, Kelly 1956, Adams-MacKay 2007 BOCD, Garivier-Moulines 2011, Besson-Kaufmann-Maillard-Seznec 2019, Auer-Cesa-Bianchi-Freund-Schapire 2002 EXP3, Ledoit-Wolf 2008, Hansen 2005, Lo 2002, Opdyke 2007, Holmberg-Lönnbark-Lundström 2013, López de Prado 2018 AFML §7.4).

ADR-0013 §4.1 non-loss mandate respected: ADR-0017 + ADR-0018 are preserved verbatim; ADR-0017's K-1..K-8 + FM-1..FM-5 + risk-of-ruin primitives at [src/skie_ninja/sizing/](../../src/skie_ninja/sizing/) + [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) + [scripts/stress_test_failure_modes.py](../../scripts/stress_test_failure_modes.py) preserved as opt-in tooling. ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability respected: all hypothesis design.md §1-§7 untouched; H062 §11.3 amendment is §11 (project-level amendable per the ADR-0017 §5 + ADR-0024 D-2/D-3 precedent).
