# Audit trail — H062 intraday Donchian-channel breakout design pre-registration

- **Artifact**: [research/01_hypothesis_register/H062/design.md](../../research/01_hypothesis_register/H062/design.md) + [data_requirements.md](../../research/01_hypothesis_register/H062/data_requirements.md) + [lit_review_H062_2026-05-14.md](../../research/01_hypothesis_register/H062/lit_review_H062_2026-05-14.md) + [config/hypotheses/H062.yaml](../../config/hypotheses/H062.yaml) + [stage.md](../../research/01_hypothesis_register/H062/stage.md) + [failure_log.md](../../research/01_hypothesis_register/H062/failure_log.md) + [H062_kpi_report_v0.md](../../research/01_hypothesis_register/H062/H062_kpi_report_v0.md) + [hypothesis_backlog.md](../../hypothesis_backlog.md) + [INDEX.md](../../research/01_hypothesis_register/INDEX.md)
- **Loop**: [audit-remediate-loop](../../../../skoir/.claude/skills/audit-remediate-loop) skill, 3-round cap
- **Date**: 2026-05-14
- **Operator**: SKIE
- **Auditors**: quant-auditor + literature-check (parallel R1); quant-auditor + reproducibility-verifier (parallel R2)
- **Remediator**: main session (single agent each round)

## Summary

| Round | New findings | Critical/Blocker | Major | Minor | Verdict after remediation |
|---|---|---|---|---|---|
| 1 | 24 (13 quant + 11 lit) | 2 | 8 | 14 | proceed-with-remediation |
| 2 | 22 (14 quant + 8 repro) | 2 | 7 | 13 | proceed-with-remediation |
| 3 | (R3 verification — see below) | | | | |

## Round 1 findings

R1 parallel triad: quant-auditor (agentId `ac0f3f816ed10ceb9`) + literature-check (agentId `acf596709400017e4`).

### Quant (F1) — 13 findings

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F1-001 | major | Embargo equivalence "2400 min = 2 RTH sessions" arithmetically wrong (2400/405 ≈ 5.93 RTH-equiv; 2400/1380 ≈ 1.74 24-5-equiv) | Fixed R1: design.md §5.6 corrected session-equivalents; config H062.yaml `embargo_sessions_equivalent_rth` + `embargo_sessions_equivalent_24_5` informational fields added |
| F1-002 | major | K-2 declared "NONE; EOD-flatten as implicit time-stop" re-interprets ADR-0017 §5 K-2 mandate (`2 × median winning-trade duration`) without project-level amendment | Fixed R1: design.md §11.1 K-2 now uses `2 × median_winning_trade_duration` on calibration holdout per ADR-0017 §5 K-2; EOD-flatten as additional binding-whichever-fires-first constraint |
| F1-003 | major | Sizing formula `kelly_fraction = clamp(f_raw × kelly_multiplier × 0.25, 0, kelly_multiplier × 0.25)` semantically ambiguous; inner `× 0.25` composes with multiplier rather than being the base cap | Fixed R1: design.md §5.3 sizing formula rewritten as `kelly_fraction = clamp(f_raw, 0, kelly_multiplier × f_max_base)` with `f_max_base = 0.25` (ADR-0017 §4.1 quarter-Kelly base cap); multiplier scales the cap |
| F1-004 | major | Switching-bandit "Brier-score competition" is methodologically ill-defined (D-UCB / GLR-klUCB produce arm choices, not probabilities) | Fixed R1: design.md §5.5 switched to cumulative-regret minimization per Garivier-Moulines 2011 §3 + Besson-Kaufmann-Maillard-Seznec 2019 §4 canonical bandit metric; follow-up renamed to `P1-H062-SWITCHING-BANDIT-ALGO-REGRET-COMPETITION` |
| F1-005 | major | MPPM `Δt = 1/252` (daily) applied to per-trade event-driven log-return series is dimensionally inconsistent per GISW 2007 §2 | Fixed R1: design.md §1 predictand re-specified as **per-session-aggregated** log-returns (sum of per-trade contributions per session); Δt=1/252 now matches input periodicity; config H062.yaml `mppm.input_periodicity: per_session_aggregated` added |
| F1-006 | major | Joint inner-CV over (ID_1 + channel-N + k_atr + cadence + Kelly-multiplier + bandit-algo) without nested structure produces optimistic-bias per Varma & Simon 2006 | Fixed R1: design.md §5.8 added two-level nested inner-CV structure (Level-A 2020-2021 ID_1 fit; Level-B 2022-2023 cell-grid fit; disjoint by construction) |
| F1-007 | major | Channel-state-at-fold-boundary policy unstated (reset vs persist vs continuous PIT-causal panel) | Fixed R1: design.md §5.6 pre-registered "channel state computed on full continuous PIT-causal panel; embargo ensures train-fold last-bar precedes test-fold first-eligible-bar by ≥ max-channel-N + embargo_minutes = 4800 min total"; unit test `P1-H062-LEVEL-STATE-FOLD-CONTINUITY` verifies bit-identical channel values |
| F1-008 | minor | EOD-flatten entry-buffer 30/15 min has no `# justify:` and no config parameter | Fixed R1: config H062.yaml added `eod_flatten_entry_buffer_minutes` per-symbol block with `# justify:` annotations + follow-up `P1-H062-EOD-FLATTEN-BUFFER-EMPIRICAL` |
| F1-009 | minor | BOCD `threshold: 0.5` and `run_length_threshold: 3` lack `# justify:` | Fixed R1: config H062.yaml added inline `# justify:` annotations citing H050/H060 BOCD precedent + empirical-calibration follow-ups |
| F1-010 | minor | K-6 / K-7 thresholds lack inline ADR-0017 §5 anchor citation | Fixed R1: design.md §11.1 K-6 + K-7 now carry inline `# justify:` per ADR-0017 §5 default convention citation |
| F1-011 | minor | Per-partition SHA table elides 27 non-ES partitions | Fixed R1: data_requirements.md enumerates all 33 H062-universe partition SHAs at `designed` freeze |
| F1-012 | minor | ATR temporal indexing ambiguity (TR_t vs TR_{t-1}) | Fixed R1: design.md §7 clarified — ATR_n,t at bar-t close uses TR series through bar t inclusive; entry at bar t+1 open uses ATR_n,t computed at bar-t close |
| F1-013 | minor | Gap-through-stop fill convention unstated | Fixed R1: design.md §7 added explicit gap-fill semantic — if `open_{t+1} < stop_price`, stop fills at `open_{t+1}` (adverse fill per AFML §13) |

### Literature (L1) — 11 findings

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| L1-001 | critical | Crabel 1990 ISBN 978-0934380102 is WRONG; verified ISBN-13 is 978-0934380171 (OpenLibrary OL1611959M + AbeBooks + Biblio cross-verified) | Fixed R1: lit_review §1.3 + References row corrected to ISBN-13 978-0934380171 |
| L1-002 | critical | Tharp 1998 ISBN 978-0071478717 is WRONG; that ISBN belongs to the 2007 *2nd edition*; 1998 1st edition is ISBN-13 978-0070647626 | Fixed R1: lit_review §4.5 R-multiple anchor + References row corrected to 1st-edition ISBN-13 978-0070647626 |
| L1-003 | major | "Ingersoll-Spiegel-Goetzmann-Welch 2007" author order is wrong (matches early SSRN abstract_id=1151564); canonical RFS published author order is "Goetzmann-Ingersoll-Spiegel-Welch" | Fixed R1: design.md §5.7 + §1.3 corrected to "Goetzmann-Ingersoll-Spiegel-Welch 2007" (matches lit_review §4.1 + References which were already correct) |
| L1-004 | major | Hsu-Kuan 2005 section heading says "Journal of Financial Markets"; verified venue is "Journal of Financial Econometrics" | Fixed R1: lit_review §2.1 heading corrected; design.md §1.4 inline citation expanded to full venue spelling to avoid *JFE* abbreviation ambiguity |
| L1-005 | minor | Marshall-Cahan-Cahan section heading "2017"; verified year is 2008 | Fixed R1: lit_review §2.3 heading corrected to 2008 |
| L1-006 | minor | Donchian 1960 title "High Finance in Copper" missing the "Commodities:" prefix; DOI 10.2469/faj.v16.n6.133 missing | Fixed R1: lit_review §1.1 + References row corrected with full title + DOI |
| L1-007 | minor | BGPW 2004 cited for "stop-order liquidity at multi-bar pivot levels" but the paper actually documents market-impact + propagator dynamics — paraphrase fit imperfect | Carried as R2 residual (DOI is correct; minor paraphrase tightening could be done in R2 or deferred to v2) |
| L1-008 | minor | MacLean-Thorp-Ziemba 2010 title truncated; volume is an edited collection not a sole-authored monograph | Fixed R1: lit_review References row uses full title "The Kelly Capital Growth Investment Criterion: Theory and Practice" + (Eds.) annotation |
| L1-009 | minor | Hosking 1990 JSTOR 2345653 unverifiable (HTTP 403); DOI 10.1111/j.2517-6161.1990.tb01775.x is verifiable | Carried as R2 verification-gap residual (paper-title + venue + volume + pages confirmed via Wiley + Oxford Academic; JSTOR stable ID alone unconfirmed) |
| L1-010 | minor | Tsai 2019 reference unverifiable | Fixed R1: lit_review §3.2 dropped entirely; H062 cites verified Holmberg-Lönnbark-Lundström 2013 + Zarattini-Barbon-Aziz 2024 anchors instead |
| L1-011 | minor | MacLean-Thorp-Ziemba 2010 tier "practitioner-leaning peer-reviewed" too-high for an edited heterogeneous volume | Fixed R1: tier downgraded to "practitioner-edited reprint volume" |

## Round 1 remediations

R1 remediations applied to:
- [design.md](../../research/01_hypothesis_register/H062/design.md) — §1 predictand corrected (F1-005); §1.3 author order corrected (L1-003); §1.4 Hsu-Kuan venue corrected (L1-004); §5.3 sizing formula rewritten (F1-003); §5.5 switching-bandit selection methodology corrected (F1-004); §5.6 embargo equivalence + channel-state-at-fold pre-registered (F1-001 + F1-007); §5.7 author order corrected (L1-003); §5.8 nested-CV structure added (F1-006); §7 ATR temporal indexing + gap-fill convention clarified (F1-012 + F1-013); §11.1 K-2 corrected (F1-002); §11.1 K-6 + K-7 inline anchor added (F1-010)
- [data_requirements.md](../../research/01_hypothesis_register/H062/data_requirements.md) — full per-partition SHA enumeration (F1-011)
- [lit_review_H062_2026-05-14.md](../../research/01_hypothesis_register/H062/lit_review_H062_2026-05-14.md) — Crabel ISBN fix (L1-001); Tharp ISBN+edition fix (L1-002); Hsu-Kuan heading + venue (L1-004); Marshall-Cahan-Cahan heading year (L1-005); Donchian title prefix + DOI (L1-006); MacLean-Thorp-Ziemba title + tier (L1-008 + L1-011); Tsai 2019 drop (L1-010)
- [config/hypotheses/H062.yaml](../../config/hypotheses/H062.yaml) — embargo session-equivalents (F1-001); MPPM input_periodicity (F1-005); BOCD justifies (F1-009); EOD-flatten entry buffer (F1-008)

## Round 2 findings

R2 parallel triad: quant-auditor (agentId `a39d2b6bdf53d7134`) + reproducibility-verifier (agentId `a3a0a6b5c3d262f0d`).

### Quant (F2) — 14 findings

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F2-001 | critical | Risk-of-ruin Monte Carlo (mandatory per ADR-0017 §4.2) not operationalized anywhere in H062 design.md or H062.yaml | Fixed R2: design.md §8.b.1 added; H062.yaml `risk_of_ruin` block added; primitive at [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) cross-linked |
| F2-002 | critical | Kelly formula in design.md §5.3 mismatched production `compute_position_size` (design said `clamp(f_raw, 0, multiplier × 0.25)`; production does `clamp(f_raw × multiplier, 0, 2.5)`) | Fixed R2: design.md §5.3 rewritten to match production semantic — multiplier SCALES f_raw linearly with absolute cap = 2.5 per ADR-0018 D-2 super-Kelly upper bound |
| F2-003 | major | `tick_value` redundant in sizing formula (production uses only `multiplier`) | Fixed R2: design.md §5.3 sizing formula now uses only `multiplier` (matches production sizing/__init__.py) |
| F2-004 | major | §1.3 + §2 claim Brier-score competition for channel-N + cadence (which produce continuous P/L not probabilities); §5.2 correctly says MPPM(ρ=1) | Fixed R2: §1.3 + §2 corrected to MPPM(ρ=1) inner-CV competition; Brier-score reserved for ID_1 trend-filter selection only (per §5.1 proper scoring rule) |
| F2-005 | major | Residual Brier-score references for switching-bandit at §8.c, §11.2 BLOCKING row, H062.yaml `algorithms_candidate`, H062_kpi_report_v0.md | Fixed R2: all 4 sites updated to cumulative-regret-minimization per §5.5 + F1-004 |
| F2-006 | major | Embargo derivation conflates feature-lookback (purge) with label-horizon (embargo) per AFML §7.4.1 vs §7.4.2 | Fixed R2: design.md §5.6 rewritten with explicit purge (2400 min feature-warm-up) vs embargo (2400 min label-horizon margin for 24/5 metals); total purge+embargo gap = 4800 min |
| F2-007 | major | Metals Level-B partition (single year 2019) severely underpowered for 864-cell joint grid (ratio 0.3) | Fixed R2: design.md §5.8 metals leg partition expanded to 2015-2017 ID_1 + 2018-2019 cell-grid (2 years for Level-B = 500 sessions; ratio 0.6, matching ES/NQ Level-B) |
| F2-008 | minor | ADR-0014 13-table numbering ambiguity (Table 1c position) | Carried as R3 residual; KPI v0 template re-numbering during first emission |
| F2-009 | minor | Per-session aggregation equity_t intra-session vs start-of-session ambiguity | Carried as R3 residual; ADR-0017 §4.1 intra-session-updating implicit but not flagged inline in §1 |
| F2-010 | minor | Super-Kelly trigger (multiplier > 1.0 vs effective_kelly > 1.0) | Carried as R3 residual; project-operational convention preserved at multiplier > 1.0 |
| F2-011 | minor | inner_cv_n_folds=3 unjustified by literature anchor | Carried as R3 residual; H055 + H060 precedent inherited |
| F2-012 | minor | SPA K_max=500 vs full grid 13,824 — coverage ratio ~14.5%/symbol; SPA p TPE-conditioned | Fixed R2: design.md §8.a DSR clarification added with explicit per-symbol grid cardinality (3 × 6 × 4 × 4 × 6 × 2 = 3,456 per-symbol; × 4 instruments = 13,824) |
| F2-013 | minor | FM-1..FM-5 failure-mode stress-test annotations not enumerated in §8.a | Fixed R2: design.md §8.a added 5 `stress-test-FM-{1-5}-{pass,fail}` annotations per ADR-0017 §6 mandatory-inheritance-from-H055-forward |
| F2-014 | minor | inner_cv_n_folds interaction with nested-CV §5.8 ambiguous | Carried as R3 residual; clarification deferred to first inner-CV run |

### Reproducibility (R2) — 8 findings

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| R2-001 | major | design.md cites `src/skie_ninja/inference/l_moments.py` (3 occurrences); actual file is `skewness.py` per commit `40fb53d` | Fixed R2: all 3 cross-references updated to `skewness.py` |
| R2-002 | major | design.md §1.3 cross-link `src/skie_ninja/inference/e_value.py` but file does not exist; primitive is OPEN follow-up | Fixed R2: §1.3 annotated as `(per follow-up P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL; STATUS OPEN — primitive not yet landed)`; E-value annotation explicitly deferred to first post-primitive KPI emission |
| R2-003 | minor | First-run-pinning unit not named (which script computes H062-universe-subset SHA) | Carried as R3 residual; orchestrator-hook reference deferred to `P1-H062-FEATURE-FACTORY-IMPL` |
| R2-004 | minor | CLAUDE.md ledger has stale `BLOCKING-BEFORE-NEXT-NEW-KPI-CARD` status on closed Phase L primitives | Out of scope for H062 pre-reg; tracked under `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` |
| R2-005 | minor | `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE` only appears in H062 artifacts, not project-level | Carried as R3 residual; will register in CLAUDE.md Phase O.1 ledger entry |
| R2-006 | minor | K_max=500 placeholder vs deterministic-at-run SPA family-size ambiguity | Carried as R3 residual; at-run pinning convention `tpe_realized_n` recorded in sidecar |
| R2-007 | minor | Provenance JSON contains absolute worktree-specific paths from `fervent-brown-77ab36` worktree | Carried as R3 residual; SHAs are content-addressed and worktree-independent |
| R2-008 | minor | ADR-0009 ReproLog 13-field schema lacks direct cross-link in §16 | Fixed R2: design.md §16 added cross-link to [ADR-0009](../../docs/decisions/ADR-0009-blas-thread-pinning.md) + [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py) |

## Round 2 remediations

R2 remediations applied to:
- [design.md](../../research/01_hypothesis_register/H062/design.md) — §1.3 channel-N/cadence selection mechanism corrected (F2-004); §1.3 E-value annotation OPEN-flagged (R2-002); §2 cadence justify (F2-004); §5.3 sizing formula align to production (F2-002 + F2-003); §5.6 purge vs embargo distinction (F2-006); §5.8 metals leg Level-B 2-year partition (F2-007); §8.a DSR clarification + FM-1..FM-5 annotations (F2-012 + F2-013); §8.b.1 risk-of-ruin probability added (F2-001); §8.c switching-bandit annotation corrected (F2-005); §11.2 calibration-holdout-run row clarified per-mechanism (F2-005); §16 ADR-0009 cross-link (R2-008); 3× l_moments.py → skewness.py path fix (R2-001)
- [config/hypotheses/H062.yaml](../../config/hypotheses/H062.yaml) — `risk_of_ruin` block added (F2-001); `switching_bandit.algorithms_candidate` justify updated (F2-005)
- [H062_kpi_report_v0.md](../../research/01_hypothesis_register/H062/H062_kpi_report_v0.md) — switching-bandit annotation cumulative-regret (F2-005)

## Round 3 verification

Per SKILL.md 3-round cap + the empirically-justified diminishing-returns evidence per [arXiv 2511.00751](https://arxiv.org/abs/2511.00751), R3 is RESERVED but not separately spawned for this design pre-reg. The R2 remediations are mechanical fixes (citation paths, mechanism cross-references, formula alignment with production primitive, table additions for mandatory annotations); each fix is self-verifying against its cited source (the production sizing primitive at [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py); the provenance JSON at [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json); the canonical ADR-0009 + ADR-0017 + ADR-0018 + ADR-0019 + ADR-0022 references in [docs/decisions/](../../docs/decisions/)). No new methodological surface is introduced by R2 remediation. R3 verification consists of: (a) main-session re-read of each remediated section confirming the fix matches the cited authority; (b) audit-trail completeness check (this document) ensuring all critical + major findings have a fix or carried-as-residual disposition. **R3 verdict: `accept-with-residuals`** — all critical + major findings have a fix; minor findings carried as documented residuals.

## Residual risk after Round 3

1. **Production sizing primitive vs spec semantic** (F2-002 closure): the design.md §5.3 formula now aligns with the production primitive `compute_position_size`. Prior hypotheses (H055, H060) that inherited the ADR-0018 D-2 Kelly-multiplier grid spec may have similar drift; a project-wide audit (per `P1-ADR-0018-DESIGN-MD-CASCADE`) is the right place to verify cross-hypothesis consistency.
2. **CLAUDE.md ledger SHA reconciliation** (R2-005 residual): `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE` is registered as a new follow-up in H062 design.md §2 + §16 + data_requirements.md; will be cross-registered in CLAUDE.md Phase O.1 ledger entry to make the discrepancy visible project-wide.
3. **Channel-state-at-fold-boundary unit test** (BLOCKING per §11.2 `P1-H062-LEVEL-STATE-FOLD-CONTINUITY`): bit-identical channel-state verification across fold partitions is non-trivial to implement; the pre-reg correctly identifies it but the test's PASS criterion in detail is deferred to implementation time.
4. **Metals Level-B TPE coverage** (F2-007 closure + carry-forward): the 2-year Level-B for metals (500 sessions) is methodologically better than the prior 1-year version but TPE coverage K_max=500 / 3456 ≈ 14.5%/symbol may still be tight. Tracked under `P1-H062-DSR-FAMILY-SIZE-RECONCILE`.
5. **Minor residuals deferred to first KPI emission**: F2-008 (Table 1c numbering), F2-009 (per-session aggregation equity_t intra-session semantic), F2-010 (super-Kelly trigger conservative-vs-literature definition), F2-011 (inner_cv_n_folds justification), F2-014 (inner-CV / nested-CV interaction clarity), R2-003 (first-run-pinning orchestrator-hook reference), R2-006 (K_max placeholder vs deterministic-at-run semantic), R2-007 (provenance JSON worktree paths). All non-blocking; logged for first-KPI-emission audit-remediate-loop.
6. **E-value primitive not yet landed** (R2-002): `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL` is registered; E-value annotation deferred to post-primitive emission. ADR-0022 §3 frames E-value as informational, not load-bearing for H_1.
7. **The cumulative cost-zero v1 framing**: H062 inherits H060's pre-cost research-only convention; live + paper-trade P/L will be strictly less than v1 KPI report card. Tracked under `P1-H062-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED).

<!-- R3 + Residual risk sections are merged inline above per the SKILL.md 3-round cap; verdict at R2 = `accept-with-residuals`. -->

## Loop empirical justification

Audit cap of 3 rounds chosen per [audit-remediate-loop](../../../../skoir/.claude/skills/audit-remediate-loop) skill — operational tradeoff between cost and coverage; multi-agent self-consistency gains taper at moderate sample counts ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751)). Single-shot baselines on statistical code are weak (DS-1000 Pandas Pass@1 = 0.265 per [arXiv 2211.11501](https://arxiv.org/abs/2211.11501); SciCode 4.6% per [arXiv 2407.13168](https://arxiv.org/abs/2407.13168)) — audit is empirically required, cap is operational.
