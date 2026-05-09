---
title: ADR-0017 Survival-Constrained Optimization Paradigm — Audit-Remediate-Loop Trail
date: 2026-05-08
deliverables:
  - docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md (NEW)
  - src/skie_ninja/sizing/__init__.py (NEW; primitive interface contracts pending P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE)
  - src/skie_ninja/inference/calmar.py (NEW; pending P1-CALMAR-DIFFERENTIAL-CI-IMPL)
  - src/skie_ninja/inference/profit_factor.py (NEW; pending P1-PROFIT-FACTOR-CI-IMPL)
  - src/skie_ninja/inference/r_multiple.py (NEW; pending P1-R-MULTIPLE-CI-IMPL)
  - src/skie_ninja/inference/risk_of_ruin.py (NEW; pending P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE)
  - src/skie_ninja/inference/__init__.py (MODIFIED; primitive re-exports)
  - scripts/stress_test_failure_modes.py (NEW; pending P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE)
  - tests/unit/test_adr_0017_survival_primitives.py (NEW; 5 import-surface tests pass + 5 implementation tests skip pending follow-ups)
  - research/01_hypothesis_register/H055/design.md §11.1 + §11.1.1 + §11.2 + §17 (MODIFIED per Path A frozen-pre-reg amendment)
  - CLAUDE.md Phase K ledger entry (MODIFIED; appended after Phase J)
  - plan/hypothesis_backlog.md "## 2026-05-08 — ADR-0017 inheritance cascade" section (MODIFIED)
audit_pattern: audit-remediate-loop (3-round cap per ~/.claude/skills/audit-remediate-loop/SKILL.md; 2 rounds executed; 0 criticals at Round 2 → Round 3 not invoked)
auditors_round_1: [quant-auditor (a63df06b8cad5c578), literature-check (acdbaa6d503ef2f95), reproducibility-verifier (a2dadf255db011f89)]
auditors_round_2: [quant-auditor (a29622c9e5b70b0a0), literature-check (a4d7819942525f9c1), reproducibility-verifier (aa6c9cc7fdf6c8113)]
parent_directive: User 2026-05-08 — "Sharpe ratio to me seems to be arbitrary and archaic. We are here to push the limits and test boundaries... Let us reframe the paradigm to the entire SKIE-Universe project based on profit, win/loss ratio, and drawdown. ... Execute using the audit-remediate loop. apply to canon documentation. The push to main."
empirical_anchor:
  - data/external/h055_pilot_ledger/Performance.csv (171 trades 2026-05-01 → 2026-05-06; on-disk artifact; SHA256 4c5ebf85f38f2881df12335f27f2007d930e7951c71c9339d2a2d3f9735c454a)
  - 2026-05-08 226-trade extension Performance.20260508.202151.pdf (processed in-context; NOT committed per the user 2026-05-08 identity-hygiene directive on the public repo; documents the $2K → $9.4K → ~$2.2K trajectory in 5 days with dual failure mode behavioral + sizing)
  - research/01_hypothesis_register/H050/H050_kpi_report_v1.md (Sharpe-test correctly captured catastrophic outcome; T_H050 < 0 with LW2008 CI excluding zero negatively; realized -81%/-84% on ES/NQ gated arms)
  - research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md (Sharpe-test missed substantively profitable cell; NQ unconditional ORB realized OOS +10.61% with P(loss) = 18.56% but T_H052a CI covered zero — false-negative)
  - research/01_hypothesis_register/H053/H053_kpi_report_v3.md (NQ LightGBM realized OOS +10.8% with max-DD 3.7% but Sharpe-vs-passive labeled "marginal" — false-negative)
---

# ADR-0017 Survival-Constrained Optimization Paradigm — Audit-Remediate-Loop Trail

## Context

Per the user 2026-05-08 directive ("Sharpe ratio to me seems to be arbitrary and archaic... Let us reframe the paradigm to the entire SKIE-Universe project based on profit, win/loss ratio, and drawdown"), ADR-0017 reframes the project's optimization-and-promotion paradigm. Sharpe-family metrics are demoted from primary inferential anchor to secondary KPI; profit-and-drawdown-aware metrics (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) are elevated to the load-bearing position. Path A amendment per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline: each frozen design.md §1 T_H statistic preserved verbatim as secondary KPI; the amendment scope is the §3 KPI report card primary inferential layer + the §8+§10 promotion-decision-rule layer.

The empirical motivation triple (H050 Sharpe-correct + H052a/H053 Sharpe-false-negative + operator pilot ledger dual-failure-mode) is documented in ADR-0017 §Context.

## Round 0 — Production drafting

12 deliverables drafted (all uncommitted at audit time): see `deliverables` frontmatter.

ADR-0017 contents:
- §1 primary inferential vector (terminal_wealth_q05, calmar_differential, profit_factor, r_multiple_mean) with bootstrap-CI primitives
- §1.1 Sharpe demoted to secondary KPI
- §1.2 pre-registered §1 T_H statistics preserved verbatim per ADR-0013 §1-§7 immutability
- §2.1-§2.4 metric definitions with primary-source citations
- §3 KPI report card 9-table → 12-table extension (new mandatory tables 3a/3b/3c)
- §4.1 drawdown-constrained Kelly sizing primitive specification
- §4.2 risk-of-ruin Monte Carlo
- §5 8 hard kill-switch constraints K-1..K-8 (mandatory inheritance from H055 forward)
- §6 5 synthetic-failure-mode stress tests FM-1..FM-5
- Alternatives A-F with rationale
- Consequences (Adopted / Trade-offs / Residual risk)
- References (peer-reviewed primary + practitioner + project-internal)
- Follow-ups (BLOCKING + cascade + non-blocking)

H055 design.md amendments (Path A): §11.1 expanded with K-1..K-8 + H055-specific calibrated defaults; new §11.1.1 drawdown-constrained Kelly per ADR-0017 §4.1; §11.2 BLOCKING preconditions extended (7 new follow-ups); §17 amendment-ledger entry. **§1-§7 preserved verbatim.**

## Round 1 — Parallel proper-isolated triad audit

3 parallel proper-isolated subagents (single-message multi-tool dispatch).

### Round 1 — quant-auditor verdict: `proceed-with-remediation` (25 findings; 3 critical, 13 major, 9 minor)

agentId: a63df06b8cad5c578

| Finding | Severity | Issue (1-line) |
|---|---|---|
| F-1 | **critical** | sizing/__init__.py + ADR §4.1 Optimal-f vs Kelly conflation; `clamp(f_kelly_raw × 0.25, 0, 0.25)` double-applies the shrinkage |
| F-2 | **critical** | ADR §4.1 Kelly-bound formula `entry × tick_value × multiplier` is dimensionally wrong (tick_value already encodes multiplier × tick_size); correct is `entry × multiplier` |
| F-3 | **critical** | ADR §4.1 risk-budget bound similarly includes tick_value where stop-dollars-per-contract is `k × ATR × multiplier` |
| F-4 | major | ADR §1 table cell formula `(ret−ret)/max(\|DD\|,\|DD\|)` differs from §2.2 prose `Calmar_arm − Calmar_bench` (ratio-of-difference vs difference-of-ratios; pick one) |
| F-5 | major | Same as F-4 (internal consistency) |
| F-6 | major | ADR §4.2 Feller 1968 Ch. XIV cited as "formal grounding" but gambler's-ruin closed-form is for fixed-bet-size simple random walks, not multiplicative-equity processes |
| F-7 | major | ADR §4.2 ruin_threshold = 0.5 uncited; numeric magic |
| F-8 | major | ADR §5 K-1 vs K-6 interaction unanalyzed; daily breaker activates after 2 losses regardless of skill |
| F-9 | major | ADR §5 K-5 $-notional cap arithmetic ambiguous (group cap = largest single-symbol cap conflicts with K-4 sum) |
| F-10 | major | ADR §3 12-table extension changes table indexing; existing H050/H053 KPI report cards reference "Table 3" / "Table 4" by position — renumbering convention unspecified |
| F-11 | major | ADR amends_ frontmatter wording too broad re: ADR-0013 §3 (could be read as authorizing §1 modification) |
| F-12 | major | ADR §2.2 + calmar.py Calmar bootstrap: independent per-arm block-bootstrap with separate block_length_arm + block_length_bench fails to preserve cross-arm dependence on the differential statistic |
| F-13 | major | ADR §2.3 + profit_factor.py Bootstrap on per-trade P/L series ignores trade-clustering structure; per-session-aggregate level is the robust default |
| F-14 | major | ADR §4.2 + risk_of_ruin.py MC simulator signature does not accept §4.1 sizing rule callable; calling MC with fixed kelly_fraction is a different process from the §4.1 prose claims |
| F-15 | major | ADR §6 stress-test FM-3 disjunctive pass criterion ("K-1 fires OR news-calendar prevents entry") is trivially satisfiable when news-calendar is enabled |
| F-16 | major | ADR §1 inferential weight changed despite §1.2 "preserved verbatim" claim — clarifying paragraph required to distinguish computational role from promotion-decision-rule role |
| F-17 thru F-25 | minor | drop per skill triage |

Cross-cell numerical-agreement check: §4.1 ES/MES/NQ worked-example numerics from prior draft did not exist; new worked-example required.

### Round 1 — literature-check verdict: `block` (24 findings; 2 critical, 5 major, 17 minor)

agentId: acdbaa6d503ef2f95

| Finding | Severity | Issue (1-line) |
|---|---|---|
| L-1 | **CRITICAL** | Browne 1995 J Appl Prob 32(3):759-779 DOI 10.2307/3215126 — that DOI resolves to **Asmussen & Nielsen 1995** "Ruin probabilities via local adjustment coefficients", a different paper. Actual Browne paper is *Adv Appl Prob* 30(1):216-238 (1998), DOI 10.1239/aap/1035228001. Same wrong-DOI failed-pattern as the H055 staging audit's Harvey-Liu RFS / Hsu-Hsu-Kuan / Breiman 1996 catches. |
| L-2 | **CRITICAL** | Tharp 1998 ISBN 978-0071478717 is the **2007 2nd edition**, not the 1998 1st. The 1998 1st-edition ISBN is 978-0070647626. |
| L-3 | major | Cvitanić & Karatzas 1995 "Math Finance 5(2):153-188 DOI 10.1111/j.1467-9965.1995.tb00037.x" — DOI returns 404. Actual venue is Springer IMA Volumes Vol. 65, pp. 77-88. |
| L-4 | major | Magdon-Ismail-Atiya 2004 *Risk* 17(10):99-102 is the trade-press summary, NOT the load-bearing closed-form-MaxDD source. The closed-form result is in the companion paper Magdon-Ismail-Atiya-Pratap-Abu-Mostafa 2004 *J Appl Prob* 41(1):147-161. |
| L-5 | major | "Closed-form MaxDD distribution under GBM" is imprecise — the result is for Brownian motion with drift (= log-GBM). |
| L-6 | major | Tharp 1998 over-attributed for profit-factor — PF predates Tharp; pre-1998 TradeStation system-trading literature (LeBeau / Lucas / Williams). Tharp popularized PF >= 1.5 threshold. |
| L-7 | major | "Quarter-Kelly is the practitioner-canonical floor" overstates MTZ 2010 normative content; book actually surveys [0.25, 0.5] shrinkage. |
| L-8 thru L-24 | minor | drop per skill triage |

### Round 1 — reproducibility-verifier verdict: `proceed-with-remediation` (5 findings; 1 critical, 1 major, 3 minor)

agentId: a2dadf255db011f89

| Finding | Severity | Issue (1-line) |
|---|---|---|
| R-1 | **critical** | Pseudonym/OS-username leak via `[publishing.md](../../skoir/.claude/rules/publishing.md)` (and `../skoir/...`, `../../../skoir/...`) leaks OS username `skoir` into 3 NEW commit sites: ADR-0017 §References, H055 design.md §17, CLAUDE.md Phase K. Same class as H055 staging audit F1-010 catch. The relative paths are also broken — they resolve to non-existent in-repo locations. |
| R-2 | major | docs/audits/audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md does not exist on disk; cited from 4 sites. Expected concurrent landing. |
| R-3 thru R-5 | minor | drop per skill triage |

Test suite: 5 import-surface tests passed + 5 implementation tests skipped with correct BLOCKING follow-up references. §1-§7 frozen-pre-reg immutability preserved on H055. Pre-commit guard passed. Git config user.email = pseudonym account.

## Round 1 — Triage + remediation

Per audit-remediate-loop skill §3 ("Drop minor findings unless the user's task specifically invites polish. critical blocks progression; major is remediated this round"):

- **Critical (4 — must remediate this round before proceeding)**: F-1 / F-2 / F-3 sizing-formula dimensional incoherence; L-1 Browne wrong-paper-DOI; L-2 Tharp wrong-ISBN; R-1 pseudonym leak (3 sites)
- **Major (~14 — remediated this round)**: F-4 / F-5 Calmar definition consistency; F-6 Feller cite demoted; F-7 ruin_threshold rationale; F-8 K-1/K-6 interaction analysis (new §5.1); F-9 K-5 worked example (new §5.2); F-10 table-renumbering convention; F-11 amends_ frontmatter tightening; F-12 Calmar paired-pairs bootstrap; F-13 profit-factor per-session-aggregate default; F-14 risk_of_ruin sizing_fn callable; F-15 FM-3 + FM-2 AND-conjunctive pass criteria; F-16 §1 inferential weight clarification; L-3 Cvitanić-Karatzas IMA Vol. 65 venue; L-4 Magdon-Ismail-Atiya-Pratap-Abu-Mostafa companion paper added; L-5 BM-with-drift language; L-6 PF attribution multi-source; L-7 quarter-Kelly soft framing
- **Deferred to follow-ups**: minor structural items per skill triage

### Round 1 remediation patches

All applied in single-file Edit operations. Selected patch summary:

- **R-1 (critical)**: removed broken `[publishing.md](../../skoir/.claude/rules/publishing.md)` link wrapper from ADR-0017 §References, H055 design.md §17, CLAUDE.md Phase K — retained prose phrase "per identity-hygiene" as self-sufficient (per H055 staging audit F1-010 closure precedent).
- **L-1 (critical)**: replaced Browne 1995 *J Appl Prob* 32(3) DOI 10.2307/3215126 with Browne 1998 *Adv Appl Prob* 30(1):216-238 DOI 10.1239/aap/1035228001 in §2.1 + §References + §"Empirical justification" + §Trade-offs (4 cite sites).
- **L-2 (critical)**: Tharp 1998 1st-edition ISBN 978-0070647626; retained note that 2007 2nd-edition ISBN is 978-0071478717.
- **F-1/F-2/F-3 (critical)**: rewrote §4.1 sizing formula. Risk-budget: `0.01·equity / (k·ATR·multiplier)`. Kelly: `kelly_fraction × equity / (entry_price × multiplier)`. Quarter-Kelly clamp: `clamp(f_kelly_raw, 0, 0.25)` (single clamp). Worked-example unit-check: ES (multiplier=50, $5000 entry, $10K equity, k=2, ATR=25) → risk-budget=0.04, Kelly=0.01 → floor(min)=0 contracts; MES (multiplier=5) → risk-budget=0.4, Kelly=0.1 → floor(min)=0. Both bounds bind to zero at $10K bankroll on a 2N-stop ES/MES trade — empirically realistic; verifies dimensional correctness.
- **F-4/F-5**: Calmar definition reconciled to `Calmar_arm − Calmar_bench` (difference-of-ratios) across §1 table + §2.2 prose.
- **F-12**: Calmar bootstrap framed as paired-pairs joint-tuple resampling with shared block-length on the joint level series; CalmarDifferentialCI dataclass single `block_length` field (replacing per-arm fields).
- **F-14**: risk_of_ruin signature gains `sizing_fn` callable parameter; default falls back to fixed-fraction-of-equity for legacy compatibility.
- **F-15**: FM-3 + FM-2 stress-test pass criteria converted to AND-conjunctive (FM-3 must satisfy news-calendar handling AND counterfactual K-1 trigger; FM-2 requires explicit session-boundary mark-to-market check).

After remediation, all 12 module-import-surface tests still passed (5 pass + 5 skip; no collection breakage).

## Round 2 — Verification-of-remediation parallel triad audit

3 parallel proper-isolated subagents, scoped to verify Round-1 critical/major remediation closure + scan for new majors introduced.

### Round 2 — quant-auditor verdict: `proceed-with-remediation` (3 NEW major findings; 0 new criticals; 15 of 16 R1 findings closed correctly)

agentId: a29622c9e5b70b0a0

R1 findings: 15 closed-correctly + 1 closed-but-with-residual (F-12 calmar.py docstring at lines 134-135 contradicts the dataclass + §2.2 prose by stating "applied independently to each arm's level return series").

NEW findings:

| ID | Severity | Issue |
|---|---|---|
| N-1 | major | calmar.py:134-135 docstring contradicts ADR §2.2 + dataclass on independent-vs-joint block selection |
| N-2 | major | profit_factor.py ProfitFactorDifferentialCI dataclass retains separate block_length_arm/block_length_bench fields, not paired with the Calmar paired-pairs F-12 fix |
| N-3 | major | Magdon-Ismail-Atiya 2004 *Risk* duplicated in §References (one entry says "corroborates J Appl Prob"; the other says "Closed-form MaxDD distribution under GBM" — contradictorily labeled) |

Worked-example numerics in §4.1 verified by hand-calc: dimensionally coherent ✓.

### Round 2 — literature-check verdict: `accept` (all 7 R1 findings closed-correctly; 1 minor noted)

agentId: a4d7819942525f9c1

L-1 closed: DOI 10.1239/aap/1035228001 verified to redirect to Cambridge Core Browne 1998 *Adv Appl Prob* 30(1):216-238 paper.
L-2 closed: ISBN 978-0070647626 verified as 1998 1st-ed.
L-3 closed: IMA Vol. 65 pp. 77-88 verified canonical.
L-4 closed: Magdon-Ismail-Atiya-Pratap-Abu-Mostafa 2004 *J Appl Prob* 41(1):147-161 verified at Cambridge Core + Caltech authors-library.
L-5/L-6/L-7 closed: soft-framing language verified at expected lines.

Minor residual (lit-N-1): §References line 316 still contained "Closed-form MaxDD distribution under GBM" framing in the duplicate entry. Subsumed by quant-auditor N-3 above (same artifact).

### Round 2 — reproducibility-verifier verdict: `proceed-with-remediation` (1 partial-fail + 1 minor; 0 new criticals)

agentId: aa6c9cc7fdf6c8113

R-1 NEW sites in 3 modified artifacts: 0 hits ✓ (pseudonym leaks correctly removed).

Partial-fail: CLAUDE.md:338 Phase I narrative-prose retains pre-existing `[publishing.md](../../skoir/.claude/rules/publishing.md)` reference describing the H055 F1-010 erratum closure. NOT introduced by this commit; flagged as the only `skoir/.claude` site remaining in the audited tree.

Test suite: 5 pass + 5 skip ✓. Imports work ✓. §1-§7 immutability preserved ✓. Pre-commit guard passes ✓. No deletions ✓.

## Round 2 — Triage + remediation

Per skill triage:

- **Critical**: 0
- **Major (must remediate)**: N-1 calmar.py docstring contradiction; N-2 profit_factor.py dataclass parallel; N-3 duplicate Magdon-Ismail-Atiya *Risk* entry
- **Partial-fail (operationally important)**: CLAUDE.md:338 pre-existing leak — even though pre-existing, the verification scope caught it and the H055 staging audit F1-010 closure precedent supports applying the same fix here.
- **Deferred**: minor scope items (Table 5 retroactivity clarification, worked-example commentary, bottom-line prose guidance) — captured in the residual ledger but not blocking.

### Round 2 remediation patches

- **N-1**: rewrote calmar.py:134-138 docstring to align with ADR §2.2 + dataclass — "Block length is selected ... on the JOINT (r_arm_t, r_bench_t) level series, then applied as a shared block length to the paired-pairs resampling."
- **N-2**: replaced profit_factor.py ProfitFactorDifferentialCI per-arm block_length fields with single shared `block_length` + added `pf_arm` / `pf_bench` fields; docstring documents paired-pairs joint per-session-aggregate resampling per the parallel reasoning to Calmar.
- **N-3**: removed the duplicate Magdon-Ismail-Atiya 2004 *Risk* entry from ADR-0017 §References at line 316 (the pre-L-5 "GBM" wording entry); retained only the line 306 entry with corrected BM-with-drift framing.
- **R2-1**: removed CLAUDE.md:338 broken `[publishing.md](../../skoir/.claude/rules/publishing.md)` link wrapper, retained prose `publishing.md identity-hygiene` (per H055 staging F1-010 closure precedent). Cross-platform pseudonym hygiene now at zero-leak across the entire artifact set.

After remediation: test suite 5 pass + 5 skip ✓; zero `skoir/.claude` matches across all 6 modified files (ADR-0017 + H055 design.md + CLAUDE.md + sizing/__init__.py + calmar.py + profit_factor.py).

## Round 2 verdict — accept (post-remediation)

After Round-2 remediation patches landed, the verdict is `accept`:
- All Round-1 critical findings (4) and major findings (~14) closed.
- All Round-2 new major findings (3) and partial-fail (1) closed.
- Test suite green; imports clean; pseudonym hygiene zero-leak; non-loss preserved; pre-commit guard passes; §1-§7 frozen-pre-reg immutability preserved on H055.

Round 3 not invoked — 0 critical or major residuals remaining; SKILL.md 3-round cap allows early termination at no-residual closure.

## Residual minor findings (deferred to follow-ups)

- ADR-0017 §3 Table 5 new-mandatory-column retroactivity clarification (whether existing v1/v2/v3 KPI cards are non-compliant or apply forward; per ADR-0013 §4.1 non-loss the answer is "apply forward via v{N+1} cascade", but worth explicit ADR sentence) → tracked under `P1-ADR-0017-TABLE-5-RETROACTIVITY-CLARIFY` (operational; lands in next ADR amendment cycle if the operator surfaces ambiguity).
- §4.1 worked-example commentary that "Kelly bound binds, NOT risk-budget bound" → tracked under `P1-ADR-0017-WORKED-EXAMPLE-COMMENTARY` (non-blocking).
- Bottom-line prose guidance under ADR-0014 ≤ 8-sentence constraint cross-link → tracked under `P1-ADR-0017-BOTTOM-LINE-PROSE-GUIDANCE` (non-blocking).
- §References line 305 Magdon-Ismail-Atiya-Pratap-Abu-Mostafa annotation could surface BM-with-drift framing more explicitly → tracked under `P1-ADR-0017-REFS-BM-DRIFT-ANNOTATION` (non-blocking; minor polish).

## Cross-references

- [ADR-0013](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — Path A frozen-pre-reg amendment discipline preserved.
- [ADR-0014](../decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — 9-table → 12-table extension authorized.
- [ADR-0017](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md) — this ADR.
- [H055 design.md](../../research/01_hypothesis_register/H055/design.md) — §11.1 + §11.1.1 + §11.2 + §17 amendments per Path A.
- [CLAUDE.md](../../CLAUDE.md) — Phase K ledger entry.
- [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) — ADR-0017 inheritance cascade section.
- [data/external/h055_pilot_ledger/Performance.csv](../../data/external/h055_pilot_ledger/Performance.csv) — empirical anchor (171 trades on-disk).

## AI-assistance disclosure

This audit-remediate-loop trail was authored by a general-purpose Claude Code agent (Opus 4.7) under operator review. Round-1 + Round-2 audits used proper-isolated parallel quant-auditor + literature-check + reproducibility-verifier subagents (6 total agentIds enumerated in frontmatter). All audit findings dispositioned in single Edit-tool patches; no batch refactors. Per [ICMJE Recommendations January 2026](https://www.icmje.org/recommendations/) AI cannot be an author; AI-assistance use is disclosed; reproducibility log path = this file plus the test-suite output captured inline above.

This trail is the canonical Round-1+Round-2 audit-remediate-loop record for ADR-0017's adoption. Preserved verbatim per ADR-0013 §4.1 non-loss mandate.
