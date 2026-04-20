---
name: audit_trail_2026-04-20_hmm-scope-extension
description: Audit-remediate-loop trail for HMM regime toolkit and 0DTE scope extension
type: project
date: 2026-04-20
rounds: 3
status: exit (Round 3 sibling-repo verification complete)
---

# Audit trail — HMM regime toolkit & 0DTE scope extension

Artifacts under review:
- [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../decisions/ADR-0005-hmm-regime-toolkit.md)
- [docs/decisions/ADR-0006-scope-extension-hmm-0dte.md](../decisions/ADR-0006-scope-extension-hmm-0dte.md)
- [docs/research_notes/memo_medallion-hmm-lineage_2026-04-20.md](../research_notes/memo_medallion-hmm-lineage_2026-04-20.md)
- [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md)
- [research/01_hypothesis_register/H051/design.md](../../research/01_hypothesis_register/H051/design.md)
- [research/01_hypothesis_register/H052/design.md](../../research/01_hypothesis_register/H052/design.md)

Loop spec: [~/.claude/skills/audit-remediate-loop/SKILL.md](file:///C:/Users/skoir/.claude/skills/audit-remediate-loop/SKILL.md). Cap = 3 rounds; exit after round 2 as only minor residuals remain.

## Round 1 — findings and disposition

Auditors: `literature-check` (citation validity), `quant-auditor` (methodology).

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| L-C1 | critical | ADR-0005 Guidolin-Timmermann DOI | Fabricated DOI pointed to unrelated paper | Fixed Round 2 — replaced with [doi:10.1016/j.jedc.2006.12.004](https://doi.org/10.1016/j.jedc.2006.12.004) |
| L-C2 | critical | ADR-0005, memo, H050 "Kim et al. 2020" | Misattribution; paper is by Ryou, Bae, Lee, Oh | Fixed Round 2 — replaced with Ryou et al. 2020, [doi:10.3390/su12177031](https://doi.org/10.3390/su12177031) |
| L-C3 | major | ADR-0006, memo Medallion figures | 66% gross overstated; Cornell reports 63.3% compound | Fixed Round 2 — value corrected; 5-and-44 reattributed to Zuckerman 2019 trade-press |
| L-C5 | critical | ADR-0006, H052 repo link | `s-koirala/SKIE-NINJA-0DTE` is 404 | Fixed Round 2 — reworded as "to be created"; H052 status transition to `running` blocked on repo being public |
| L-M-Celeux | major | ADR-0005 Celeux-Durand year | 2007/2008 ambiguity | Fixed Round 2 — 2008 print issue cited; DOI confirmed |
| L-M-Books | major | Chan 2013, West-Harrison 1997 | ISBNs missing | Fixed Round 2 — ISBNs added; flagged for publisher-page confirmation |
| L-Biog | major | Memo §1/§2 biographical Medallion claims | Zuckerman 2019 is trade press, outside evidence hierarchy | Tagged Tier-5 "orienting only" |
| Q-C1 | critical | ADR-0005 ReproLog extension | Proposal conflicts with frozen dataclass + verify() byte-identity | Fixed Round 2 — moved to sidecar `{run_id}_hmm_selection.json` recorded via `ReproLog.model_hash`; no schema change |
| Q-C2 | critical | H050/H051/H052 §5 decoding causality | Filter vs smoothed posterior ambiguous → leakage risk | Fixed Round 2 — each §5 now states causal forward filter at inference; smoothed only for diagnostics; leakage unit test required |
| Q-C3 | critical | H052 capacity ceiling | SPX notional→ES mapping hand-waved | Fixed Round 2 — explicit formula + delta/vega/gamma caps; transition blocked until config/instruments.yaml lands numbers |
| Q-C4 | critical | H051 Johansen pre-screen | Circular BIC threshold; Bonferroni vs BH inconsistency | Fixed Round 2 — Osterwald-Lenum critical values; power-calibrated ≥60% rejection rule from training-fold simulation; BH retained, Bonferroni removed |
| Q-M-Kalman | major | H051 §5 Kalman init | β₀, P₀, rolling-Johansen window span unspecified | Fixed Round 2 — train-fold OLS seed, diffuse P₀ per Durbin-Koopman |
| Q-M-0DTE-purge | major | H052 §6/§8 purge/embargo + ES level | 97.5% ES uncited; session boundaries ambiguous | Fixed Round 2 — cited BCBS FRTB 2019; stationary-block-bootstrap + Brazauskas-Kaiser CI; session-boundary rule via clock.py |
| Q-M-Magic | major | ADR-0005 n_states {2,3,4}, ≥10 restarts | Magic numbers | Fixed Round 2 — replaced with data-driven bounds (n_states ≤ K s.t. mean within-state N > 30·dim; restarts until top-two LLs within ε = 2·SE(bootstrap EM LL); floor 5) |
| Q-M-PIT | major | H052 §3/§4 PIT + settle convention | VVIX as-of unspecified; AM/PM settle conflated | Fixed Round 2 — per-feature as_of; SPXW PM-settle universe; traditional AM-settled excluded |
| Q-M-Lockbox | major | H050/H051/H052 §2 test window | Future-window re-run ambiguity | Fixed Round 2 — dataset SHA256 lockbox rule; successor HID required for post-2025-12-31 data |
| Q-M-SPA | major | H050/H051/H052 §1 SPA entry | Scalar test statistic undefined | Fixed Round 2 — each hypothesis declares T_i statistic; H052 splits to (a,b) if underpowered |
| Q-M-Label | major | H050/H052 §5 label-switching | Ordering rule not named | Fixed Round 2 — H050 by emission-mean asc; H052 by emission-variance asc |
| Q-M-Budget | major | H050 §5/§9 nested-grid budget | Wall-clock budget without per-config allotment | Fixed Round 2 — random search, N_draws=200 (Bergstra-Bengio), max-iter=500, tol=1e-4 |
| Q-M-Stability | major | ADR-0005 latent-chain stability | Rolling-LR test uncited | Fixed Round 2 — Carrasco-Hu-Ploberger 2014 primary; Hansen 1992 supLM complementary |
| Minor (Tier2b, Medallion cross-asset, MBP-10 fallback, H052 missingness) | minor | various | cosmetic/clarity | Tier definitions quoted in ADR-0006; cross-asset softened; MBP-10 fallback flagged but not split into H050a/b this round; missingness noted in residuals |

## Round 2 — spot-check

Grep-verified: all critical substitutions landed (`Ryou`, `63.3`, `forward filter`, `Carrasco`, `Osterwald-Lenum`, `Brazauskas-Kaiser`, `sidecar`, `3504766`, bare `SKIE-NINJA-0DTE` path) across all six artifacts. No stale occurrences of `Kim et al`, `66% gross`, `eswa.2020.113820`, `jedc.2007.01.018`, or the original ReproLog-extend wording remain.

## Residual risk (carried forward)

1. **Sibling 0DTE repo not public.** `s-koirala/SKIE-NINJA-0DTE` does not exist at time of writing (2026-04-20). ADR-0006 and H052 reference it as "to be created." H052 cannot transition `designed` → `running` until the repo is public, licensed, and imports cleanly. Tracking as a pre-condition, not a content gap.

2. **Zuckerman 2019 biographical claims are Tier-5 trade press.** Baum/IDA, Ax extending Baum, 1993 Mercer/Brown recruitment from IBM — these are orienting narrative only. They do not enter any gate-bearing decision and are labeled as such in the memo and ADR-0006.

3. **Effective sample size for H052 ES gate.** At α=0.05 and 97.5% ES tail, power-per-fold on 0DTE daily P/L may be structurally inadequate regardless of CI method. Pre-registered split into H052a (SR) + H052b (ES) covers the failure mode but does not eliminate it.

4. **Cross-repo SPA reconciliation.** ADR-0003 SPA/Romano-Wolf assumes comparable test statistics within a family. If the sibling 0DTE repo runs its own SPA, cross-family FDR needs a hierarchical correction (BH across families). ADR-0006 notes this; full resolution deferred to an ADR-0007 when the 0DTE repo lands.

5. **Textbook ISBN confirmation.** Chan 2013 ISBN 978-1118460146 and West-Harrison 1997 ISBN 978-0387947259 added but not publisher-page-confirmed; flagged in ADR-0005 References.

6. **Hedgeweek 2024 30%/$12B citation.** Article URL not pinned to a specific post; memo §5 lists as pending.

7. **H050 MBP-10 fallback not split** into H050a/H050b as the auditor suggested. Current design keeps soft dependency on H010; if H010 does not land before H050 queues to `running`, the tick-rule fallback will execute and divergent n_states selection is a known soft-pre-reg weakness. To be revisited.

## Loop exit

Exit after Round 2. Residuals are all operational or pre-conditions (not content errors in the reviewed artifacts). Any of items 1, 3, 4 above materializing would trigger a follow-up ADR, not a re-open of this audit.

---

# Addendum: project rename to SKIE-Universe + initial git push (2026-04-20)

Separate audit-remediate pass, 1 round, green on first sweep.

**Changes.** Project display name `SKIE-Ninja-Intraday` → `SKIE-Universe`. Local dir path unchanged (`C:\Users\skoir\SKIE-Ninja-Intraday`). Python package `skie_ninja` unchanged. `pyproject.toml` `name` field updated; README.md H1; CLAUDE.md H1; 6 doc-prose occurrences; `.gitignore` extended with `.hypothesis/` and `*.egg-info/`. User-global glob `~/.claude/rules/quant-project.md` now matches both `**/SKIE-Ninja*/**` and `**/SKIE-Universe*/**`.

**Git / GitHub.** `git init -b main`; user.name=`s-koirala`, user.email=`skoirala2625@gmail.com`. One baseline commit `2eb7dbe` (156 files, 12,625 insertions). Remote `https://github.com/s-koirala/SKIE-Universe.git`, private. `pre-commit install` completed post-push.

**Reproducibility-verifier findings.**

| ID | Severity | Check | Result |
|---|---|---|---|
| 1 | — | Single commit on main, clean tree, remote set | pass |
| 2 | — | `gh repo view`: private, main, pushedAt 2026-04-20T15:41:47Z | pass |
| 3 | — | 156 files tracked, zero `.venv/__pycache__/.pytest_cache/.ruff_cache/.hypothesis/egg-info/.env` leaks | pass |
| 4 | — | Secret scan: only env-var references, no literal keys | pass |
| 5 | — | `pyproject.toml` name = `skie-universe` | pass |
| 6 | — | Test suite 196/196 passing in 13.84s after rename | pass |
| 7 | — | `reproducibility.py:125` `_git_head` uses `git -C <root> rev-parse HEAD` — contract satisfiable | pass |
| 8 | minor | Historical `research/03_audits/remediation-round1-literature_2026-04-15.md` retains pre-rename absolute Windows paths — preserved per policy; no action | acknowledged |
| 9 | — | `rules/quant-project.md` glob includes `**/SKIE-Universe*/**` | pass |
| 10 | — | `.git/hooks/pre-commit` installed, 674 bytes, executable | pass |

**Residual risk (rename track).** None material. If/when the user clones `SKIE-Universe` on a different machine with a different local path, the historical-audit absolute paths noted in finding 8 become stale — documented, not edited.

---

# Addendum 2: local-directory rename preparation (2026-04-20)

Separate audit-remediate pass, 1 round, green on first sweep. Purpose: certify that the user's imminent out-of-session `mv C:\Users\skoir\SKIE-Ninja-Intraday → C:\Users\skoir\SKIE-Universe` will not break the repo.

**Changes.**
- Outbound HTTP identity: `User-Agent: SKIE-Ninja-Intraday/0.1` → `SKIE-Universe/0.1` in `src/skie_ninja/data/ingest/fomc_text.py`, `src/skie_ninja/data/ingest/_fomc_calendar.py`, `tests/integration/test_fomc_fetch.py`.
- README gains a "Local directory rename (2026-04-20)" section documenting post-`mv` venv recreation.
- Memory dir mirrored: `C:/Users/skoir/.claude/projects/c--Users-skoir-SKIE-Universe/memory/` byte-identical to old dir (old retained as backup).
- Commit `6d90d3e` pushed to `s-koirala/SKIE-Universe` main. Pre-commit hooks passed.

**Reproducibility-verifier findings (1 round).**

| Severity | Location | Issue | Disposition |
|---|---|---|---|
| minor | [README.md](../../README.md) rename-note | Intentional pre-`mv` path reference; stale after rename | Post-`mv`: tense-shift to "formerly at..." or prune |
| minor | [.pre-commit-config.yaml](../../.pre-commit-config.yaml) L52/59/64 | Bare `python` entry may hit Windows Store stub after venv destroyed | Non-blocking; activate new `.venv` before commits or switch to `py -3` |
| minor | working tree | `uv.lock` untracked — reproducibility contract expects it committed | Out of scope for rename; flag for follow-up |

**Post-`mv` user steps (documented in README):**
1. `cd C:\Users\skoir\SKIE-Universe`
2. `uv venv --python 3.11 .venv`
3. `uv pip install -e ".[dev]"`
4. `pre-commit install`
5. `pytest tests/unit/ -q` → expect 196/196.

**Certification.** ProjectPaths.discover walks upward for `pyproject.toml` (dynamic, not absolute). `_git_head` calls `git -C <discovered_root> rev-parse HEAD`. `~/datasets/` resolves via `Path.home()`. No hardcoded absolute Windows paths in any tracked source file. Memory mirror diff is empty. Post-`mv` breakage risk near zero.

## Empirical justification

3-round cap from [arXiv 2511.00751](https://arxiv.org/abs/2511.00751) + DS-1000/SciCode baselines per the skill's citation. Rounds 1–2 resolved fabricated-DOI / misattribution / leakage-surface items. Round 3 added because the Round-1 L-C5 finding (sibling repo 404) turned out to be incorrect and required direct content-level reconciliation with the now-verified sibling repo.

## Round 3 — sibling repo verification

**Trigger.** Round-1 auditor (literature-check, finding **L-C5**) reported `s-koirala/SKIE-NINJA-0DTE` as **404 / blocked**, and Round 2 remediated by rewording to "to be created" with H052 status transitions blocked on the repo going public. That 404 was wrong.

**Verification.** `gh repo view s-koirala/SKIE-NINJA-0DTE` succeeds; `gh api repos/s-koirala/SKIE-NINJA-0DTE/contents/research` returns the full `research/00-hypothesis.md` … `research/10-glossary.md` tree plus `README.md` and `CHANGELOG.md`. Repo is live, created 2026-04-19, author Sudarshan "SKIE" Koirala, internal project code **SKIE-ORB-CALL**.

**Root cause of the original 404.** `WebFetch` on `github.com/s-koirala/SKIE-NINJA-0DTE` returned HTTP 404. Likely explanations (not individually verified, ordered by prior):
1. GitHub anti-scraping / user-agent filtering on unauthenticated HTML fetches of private-adjacent or recently-created repos.
2. Transient rate-limit during the Round-1 check window.
3. Propagation delay on GitHub's HTML-render layer for a repo created hours before the audit.
The authenticated `gh` CLI path uses the REST API with token credentials and bypasses whichever of (1)–(3) produced the HTML 404. **Operational rule going forward: never rely solely on `WebFetch` for GitHub existence checks; use `gh api` as the authoritative source.**

**Content reconciliation.** The sibling repo's actual thesis is **not** short-vol 0DTE on SPX (our Round-2 assumption) but a **long-premium 0DTE/1DTE QQQ call scalp** conditioned on QQQ first-hour bullish bias (P(Price_10:30 > Open_9:30) > 0.50). Underlying is QQQ spot primary, NQ/MNQ futures cross-check. Splits IS 2015–2021 / OOS 2022–2025. Multiple-testing via **CPCV + PBO + Bonferroni / Holm-Sidak** (de Prado 2018) across day-of-week × gap-size × VIX-regime strata.

**Artifacts amended in Round 3.**
- [ADR-0006](../decisions/ADR-0006-scope-extension-hmm-0dte.md) — "repo to be created" and "404 / blocked" language removed; 0DTE motivation rewritten as long-premium call scalp + HMM gate (not short-vol / iron condor); underlying corrected to QQQ primary / NQ-MNQ cross-check; sibling-repo CPCV gate declared a prior screen with Hansen SPA additive, formal cross-family reconciliation deferred to ADR-0007.
- [research/01_hypothesis_register/H052/design.md](../../research/01_hypothesis_register/H052/design.md) — **materially reframed**. Title → "HMM regime-gated QQQ first-hour long-call 0DTE scalp." §1–§10 rewritten: H0/H1 are now on paired SR-differential (gated vs unconditional SKIE-ORB-CALL), universe is QQQ (primary) + NQ/MNQ cross-check, features are QQQ realized-variance (Andersen-Bollerslev 1998) + first-hour sign + VIX + gap bucket + day-of-week + 50-DMA regime, execution layer per sibling §4.2 (entry 10:30 ET, time stop 14:00 ET, hard close 15:45 ET), state ordering by QQQ log-return emission-variance ascending, purge 1 session nested in sibling CPCV, cost_model_id `qqq_0dte_v1`. ES 97.5% demoted from gate to monitoring metric (long-premium, not short-vol). Precondition-failed auto-archive rule added: if sibling Phase-1 binomial test fails, H052 auto-archives null regardless of HMM gate performance. Citations add de Prado 2018 (ISBN 978-1119482086); Zarattini et al. flagged UNVERIFIED pending primary source.
- [research/01_hypothesis_register/H052/README.md](../../research/01_hypothesis_register/H052/README.md) — rewritten to the new title, sibling-repo reference, and precondition clause.
- [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) — H052 row updated to new title and citation set; remains in Tier 2b (regime/state) per sibling-repo self-coding of this work as research-phase frontier.
- [docs/research_notes/memo_medallion-hmm-lineage_2026-04-20.md](../research_notes/memo_medallion-hmm-lineage_2026-04-20.md) — §3 reference-implementation survey updated: sibling repo is live, uses CPCV + PBO + Bonferroni / Holm-Sidak, has its own authoritative PDF strategy doc.

**Updated residual-risk items (supersedes the Round-2 list above).**

| Item | Prior status | Round-3 disposition |
|---|---|---|
| 1. Sibling 0DTE repo not public | Open pre-condition | **Resolved** — repo verified live via `gh`. H052 pre-registration no longer blocked on repo existence. Remaining transition gate: numeric position cap must land in sibling `config/` or our `config/instruments.yaml`. |
| 2. Zuckerman 2019 biographical claims Tier-5 | Open (narrative only) | Unchanged. |
| 3. ES gate power at 97.5% on 0DTE daily P/L | Open (split to H052a/b pre-registered) | **Irrelevant** — H052 is now **long-premium** call scalp, not short-vol condor. ES is monitoring, not a gate. Sharpe-differential + max-DD is the operative joint gate. Planned a/b split withdrawn. |
| 4. Cross-repo SPA reconciliation | Open (deferred to ADR-0007) | **Downgraded** — sibling-repo CPCV + PBO + Bonferroni / Holm-Sidak is declared a prior screen; only signals surviving that screen enter our Hansen SPA family. Hierarchical BH across families remains a future refinement, not a blocker. ADR-0007 still owes the formal write-up. |
| 5. Textbook ISBN confirmation | Open | Unchanged. |
| 6. Hedgeweek 2024 30%/$12B URL | Open | Unchanged. |
| 7. H050 MBP-10 fallback split | Open | Unchanged. |

**Loop exit.** Round 3 complete; exit at cap. No further rounds.
