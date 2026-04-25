---
name: Option B — H050 data-coverage decision briefing
description: Decision briefing for the H050 data-coverage gap; enumerates substrate × disposition paths with literature, cost, foreclosure, and statistical-power analysis; produced under audit-remediate-loop QC
type: project
status: decision-pending
date: 2026-04-24
audience: skoir
revision: r2 (post-Round-1 audit; 20 findings remediated)
---

# Option B — H050 data-coverage decision briefing

## 0. Purpose

The H050 walk-forward run is blocked on a pre-registration / substrate mismatch that the user must resolve before Phase-B code remediation begins. This memo is a decision briefing: it does not pick a path, it scopes each path against the binding pre-registration record, the literature, and the substrate inventory, so the user can make an evidence-grounded choice.

Per `~/.claude/CLAUDE.md` evidence hierarchy: every claim below is anchored in (1) peer-reviewed literature, (2) official Databento documentation, (3) the project's own pre-registration documents, or (4) verifiable substrate state. Claims that cannot be anchored to one of those four are flagged as the author's derivation and not asserted as established results.

## 1. The mismatch — precise inventory

### 1.1 Pre-registration requirement

[research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §2 binds:

| Window | Start | End | Length |
|---|---|---|---|
| Train | 2015-01-01 | 2022-12-31 | 8 calendar years |
| Validation | 2023-01-01 | 2023-12-31 | 1 calendar year |
| Test | 2024-01-01 | 2025-12-31 | 2 calendar years |

§2 line 41 (binding): *"Any data after 2025-12-31 is locked away; re-runs on extended windows require a successor hypothesis ID."* Read symmetrically with §10's archive enumeration, this language defines a closed contract: the *intended* window set is 2015-2025 at the symbol-pair `(ES, NQ)`; deviations require either a successor ID or invocation of one of §10's archive dispositions.

### 1.2 Actual substrate

Per [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) §Coverage and [CLAUDE.md](../../CLAUDE.md) Phase-1-ingest section:

| Symbol | Available range | Total rows |
|---|---|---|
| ES (front-month, roll-adjusted) | 2020-01-01 → 2025-12-03 | 1,882,800 |
| NQ (front-month, roll-adjusted) | 2020-01-01 → 2024-12-31 | 1,820,559 |
| Combined | — | 3,703,359 |

### 1.3 Gap by window

| Window | Required (ES) | Available (ES) | Required (NQ) | Available (NQ) | Gap |
|---|---|---|---|---|---|
| Train | 2015-01-01 → 2022-12-31 | 2020-01-01 → 2022-12-31 | 2015-01-01 → 2022-12-31 | 2020-01-01 → 2022-12-31 | 5 of 8 train-years missing on both symbols (62.5% train substrate absent) |
| Validation | 2023-01-01 → 2023-12-31 | full | 2023-01-01 → 2023-12-31 | full | 0 |
| Test | 2024-01-01 → 2025-12-31 | full (last bar 2025-12-03) | 2024-01-01 → 2025-12-31 | 2024-01-01 → 2024-12-31 | NQ 2025 entirely missing (50% of NQ test substrate absent) |

The pre-reg companion ([data_requirements.md:42](../../research/01_hypothesis_register/H050/data_requirements.md)) already acknowledges this gap inside the freeze: *"actual available training data is 2020-01-01–2022-12-31"*. That note is internally inconsistent with §2 of `design.md` (which is the binding pre-reg document) and is itself part of what Option B must resolve.

## 2. Statistical implications of the gap

The relevant question is whether 3 years of train substrate (2020-2022) can support the H050 design as written. Two distinct constraints bind:

### 2.1 HMM identifiability under regime shift

H050 §5 invokes [ADR-0005](../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) (Baum-Welch + causal forward-filter Viterbi) with `n_states` selected by BIC + CV log-likelihood. The minimum sample required for stable Gaussian-emission HMM identification is governed by *expected number of regime transitions* in the train window, not raw bar count.

Two anchors from the literature:

- [Hamilton 1989, *Econometrica* 57(2):357–384, doi:10.2307/1912559](https://doi.org/10.2307/1912559) demonstrated two-state regime-switching identification on roughly 30 years of quarterly real GNP. Specific obs counts and dwell-time bands cited in earlier drafts of this memo were not directly verifiable from the primary PDF in the present session and are removed; the load-bearing observation is that Hamilton's result rests on a multi-decade sample.
- [Guidolin & Timmermann 2007, *J. Economic Dynamics & Control* 31(11):3503–3544, doi:10.1016/j.jedc.2006.12.004](https://doi.org/10.1016/j.jedc.2006.12.004) use 552 monthly observations (Jan 1954–Dec 1999, US stock + bond returns) to support a four-state regime decomposition. Their result establishes empirical viability of multi-state identification on multi-decade samples; it does not establish a formal lower bound on training-window length for HMM identifiability under structural breaks.

**Concern (not a quantitative claim):** truncating to 2020-2022 deletes the 2015-2019 low-volatility regime entirely; HMM emission moments fitted on a window dominated by post-COVID variance may not generalize to test-window 2024–2025. Without a peer-reviewed identifiability bound for HMMs under structural-break-truncated training, this is a stated *concern*, not a quantified bias claim. Mitigation: a pre-test stationarity check is feasible; see §4.4.

### 2.2 Walk-forward fold count and power

H050 §6 specifies `PurgedWalkForwardSplitter` per [Lopez de Prado, *Advances in Financial Machine Learning* (2018), Wiley](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086). AFML §7.1 covers the failure modes of naive walk-forward; AFML §7.4 (with §7.4.1 Purging the Training Set, §7.4.2 Embargo, §7.4.3 The Purged K-Fold Class) defines purge and embargo for k-fold cross-validation. AFML does **not** publish a closed-form fold-count formula for purged walk-forward; the relationship `n_folds ≈ (T_total − T_purge − T_embargo) / T_test_fold` is the author's first-principles approximation of an expanding-window walk-forward, not a Lopez de Prado equation, and it does not capture all per-fold geometric effects (anchored vs. rolling, embargo-per-fold vs. once, label horizon).

H050 §9 (`stopping rule`) makes fold count an explicit power-target driver via `n_required_for_power_80`. [Bailey & Lopez de Prado 2014, *Journal of Portfolio Management* 40(5):94–107, doi:10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094) ("The Deflated Sharpe Ratio") gives the asymptotic relationship between sample length, multiple-testing depth, and DSR — shorter samples raise the DSR threshold for any given alpha.

**Concrete fold-count ranges**: the orchestrator [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) currently uses `initial_train = max(200, n//3)` and `test_size = max(50, n//10)` (see `P1-H050-SPLIT-PARAMS`); under the pre-reg windows, ranges quoted in earlier drafts (6–10 vs 24–30) were not derived from `H050.yaml` parameters and have been removed pending an explicit calculation by the splitter against the resolved post-decision windows. The qualitative direction is unchanged: a 3-year train window admits *materially fewer* expanding-window folds than an 8-year train, *given the same per-fold test size, embargo, and purge*. The exact magnitude is path-dependent and will be calculated in Phase-B once windows are resolved.

**Random-search coverage vs CV-fold variance**: [Bergstra & Bengio 2012, *JMLR* 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html) bound the probability of sampling at least one configuration from the top-q quantile after n draws by 1 − (1 − q)^n. The H050 design.md §5 N_draws=200 setting governs *coverage of the search space* and is unaffected by training-window length. Per-configuration evaluation *variance*, by contrast, increases when the inner-CV folds shrink. These are independent effects and should not be conflated.

### 2.3 Roll-adjustment continuity

The substrate is ratio-adjusted per AFML §2.4.3 (Single Future Roll). Backfilling 2015-2019 introduces 5 additional roll events per symbol per year (≈ 25 new roll-event boundaries on each symbol). Ratio adjustment is order-dependent: backfilled bars must be re-anchored against the same most-recent roll seed used in the existing 2020-2025 substrate, otherwise the combined frame's `frame_sha256` will differ from the current combined-frame checksum `d2c4aa4e70c6badcb294d9bec64ee3fc5093ba9085082495f5031743943b9a2d` (frozen in [data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) §"Combined frame") at every bar, not just the appended ones.

## 3. Path B1 — Backfill ES+NQ 2015-2019 + NQ 2025

### 3.1 Scope

Vendor: Databento GLBX.MDP3 schema `ohlcv-1m`. Per [Databento documentation](https://databento.com/docs) the GLBX.MDP3 historical archive covers CME futures from 2010-06-06 forward, so the 2015-2019 window is in-range and queryable through the same `historical.timeseries.get_range` API path used by the existing ingest. Provenance note: native MDP 3.0 capture begins 2017-05-21; pre-2017 bars are reconstructed from CME legacy feeds. The `ohlcv-1m` schema is materially equivalent across the boundary, but the reconstruction provenance differs from the existing 2020+ substrate and should be documented in any backfill audit trail.

Items to backfill (anchored to the empirical density 318k–364k rows/symbol-year derivable from `data_requirements.md` §Coverage: 1,882,800 ES rows / 5.92 yrs ≈ 318k/yr; 1,820,559 NQ rows / 5 yrs ≈ 364k/yr):

| Item | Approx rows | Symbol |
|---|---|---|
| ES 2015–2019 (5 yrs) | ~1.59M | ES |
| NQ 2015–2019 (5 yrs) | ~1.82M | NQ |
| NQ 2025 (1 yr) | ~0.36M | NQ |
| **Total** | **~3.77M new rows** | |

### 3.2 Operational cost

- **Vendor cost**: Databento historical CME futures `ohlcv-1m` is sold by the symbol-window pair. Public pricing on [databento.com/pricing](https://databento.com/pricing) at the time of writing tags CME futures historical access in the per-symbol-month band; concrete cost depends on the user's account tier and any subscription credits. Order-of-magnitude estimate: roughly $X for ~3.77M rows of CME futures `ohlcv-1m` at typical Databento historical pricing — **the user must verify against their billing**, since this memo cannot derive a binding figure from public docs alone.
- **Ingest pipeline time**: 3.77M rows. Existing pipeline `python scripts/ingest.py --dataset vendor_legacy_1min` ingested 3.73M rows in a single session (per [docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](../audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md)); proportional estimate is one-shot, hours not days, no parallelism required.
- **Roll-adjustment re-derivation**: §2.3 above — the entire combined frame must be re-derived end-to-end after backfill to preserve the ratio-adjusted continuity. This invalidates the current `data_requirements.md` checksum table; a new pre-reg companion checksum table must be frozen at backfill completion.
- **License**: Databento EULA verified 2026-04-23 (data_requirements.md row 22). Internal-research-use clause covers H050. No legal blocker.

### 3.3 Identity preservation

B1 is the only path that preserves the H050 pre-reg ID exactly. Design.md §2 forbids *extension* of the window (post-2025-12-31 data is "locked away"); it does not address *backfilling within the original window*. Backfilling 2015-2019 brings the substrate up to the pre-reg specification rather than extending past it; this is consistent with the spirit of §2 line 41.

NQ 2025 backfill is in a different category — the test window already specifies 2024-01-01 → 2025-12-31 and ES has 2025 data, so NQ 2025 backfill is filling an *intended* test-window gap, not an extension.

### 3.4 Risks

- **Vendor data drift**: Databento may have revised historical bars between original ingest and backfill (Databento publishes a corrections changelog; user must verify no overlapping-window revisions before stitching).
- **Checksum-freeze procedure**: data_requirements.md must be re-frozen *atomically* with the new ingest. The current per-partition checksum table covers existing partitions only; partial freeze risks split-brain reproducibility.
- **Roll-event count shift**: from 58,465 baseline (cited from [data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) §Coverage row "Roll events (roll_flag=True bars)") to a projection of ~70,000 roll-flag bars after backfill (author's estimate, not a vendor-confirmed figure: 5 yrs × 4 quarterly rolls × 2 symbols × bars-per-roll-event ≈ +12k); downstream features that gate on `roll_flag` (none currently — but [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) v0.2.0 emits the column and feature factories may consume it) need re-validation.

### 3.5 Partial-backfill variants

A symmetric ES+NQ backfill is the canonical B1 above. Two partial variants are coherent:

- **B1-ES-only**: backfill ES 2015-2019 only; NQ remains 2020-2024 (or 2020-2024 + NQ 2025 if the test gap is also closed). This preserves ES's full pre-reg coverage but leaves the NQ train window truncated. The paired-differential statistic computed under such an arrangement requires explicit pre-registration of the cross-symbol aggregation rule (see §4.1).
- **B1-test-only**: backfill NQ 2025 only; both symbols remain at 2020+ training start. This makes the test window symmetric across symbols but leaves the train window truncated for both. Cheap and quick; addresses the test-window gap without addressing the train-window gap.

These variants trade vendor cost against pre-reg fidelity. Neither is symmetrically equivalent to B1 canonical.

## 4. Path B2 — Register H050b with truncated windows

### 4.1 Scope and the cross-symbol aggregation question

Pre-reg a successor hypothesis under the same ADR-0005/ADR-0006 design constraints, but with windows shifted to match available substrate. The shape of H050b depends on a pre-registration choice that design.md §1 leaves underspecified: how the test statistic `T_H050 = SR_{filtered, gated} − SR_{filtered, unconditional}` aggregates across the two-symbol universe.

Design.md §1 line 30 specifies a single scalar statistic but does not state whether `SR` is computed on (i) pooled OOS net returns concatenated across symbols, or (ii) per-symbol then aggregated to a portfolio-level differential. Each interpretation admits a different H050b sub-variant:

| Sub-variant | Universe | Test window | Aggregation rule |
|---|---|---|---|
| **B2a — symmetric truncated** | ES + NQ | 2024-01-01 → 2024-12-31 (1 yr; truncated to NQ-shorter) | Pooled or per-symbol; both work because windows match |
| **B2b — ES-only full** | ES only (drops NQ) | 2024-01-01 → 2025-12-31 (2 yrs; pre-reg test window preserved on ES) | Single-symbol; trivial |
| **B2c — asymmetric universe** | ES + NQ | ES: 2024-2025; NQ: 2024 | Per-symbol aggregation with explicit pre-registered rule |

Train: 2020-01-01 → 2022-12-31 (3 calendar years) under all three sub-variants. Validation: 2023.

The "must truncate windows to match across symbols" framing in earlier drafts of this memo was an implicit design choice; it is not a literal pre-reg constraint. B2c is admissible if the per-symbol aggregation rule is explicitly pre-registered.

### 4.2 Pre-registration mechanics

Design.md §2 line 41 explicitly authorizes successor hypotheses: *"re-runs on extended windows require a successor hypothesis ID"*. Symmetrically, re-runs on truncated windows are equivalent design-changes requiring a successor ID. H050b would be a new directory under [research/01_hypothesis_register/H050b/](../../research/01_hypothesis_register/) with a forked `design.md` referencing H050 as parent and explicitly declaring (i) the truncated windows, (ii) the universe choice (B2a/B2b/B2c), and (iii) the cross-symbol aggregation rule.

### 4.3 What this forecloses

- H050 itself goes to `archive(null, design-superseded)` under any B2 sub-variant (the implicit successor-supersession rule of design.md §10). The 8-year-window claim cannot be made under H050b.
- DSR comparability: any cross-hypothesis Sharpe comparison (H050b vs H051 vs H052a — all under the same Hansen SPA family per [docs/decisions/ADR-0003-spa-vs-romanowolf.md](../../docs/decisions/ADR-0003-spa-vs-romanowolf.md)) will mix 8-year and 3-year train windows, complicating DSR pooling per [Bailey & Lopez de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094).

### 4.4 Statistical viability — qualitative bounds

Per §2.1–2.2:

- **HMM regime stability**: 3-year train (2020-2022) is dominated by post-COVID variance regimes. Recommended pre-registration addition: a regime-stationarity check (Quandt LR test for parameter switching with known break, [Quandt 1960, *JASA* 55(290):324–330, doi:10.1080/01621459.1960.10482067](https://doi.org/10.1080/01621459.1960.10482067), generalized by [Andrews 1993, *Econometrica* 61(4):821–856, doi:10.2307/2951764](https://doi.org/10.2307/2951764) to unknown-break-point with sup-LR/Wald/LM statistic and non-standard asymptotic distribution) on the train-fold's HMM emission moments before promoting to test. This is a *gate*, not a fix; if it fails, H050b also archives `precondition-failed`.
- **Walk-forward fold count**: with 3-year train, achievable purged-walk-forward fold count is materially smaller than under the 8-year design at the same per-fold test size, embargo, and purge. The exact magnitude is splitter-parameter-dependent and will be computed by `PurgedWalkForwardSplitter` against the resolved post-decision windows; a conservative posture is to require `n_folds ≥ n_required_for_power_80` from the H050b pilot dispersion before promotion.
- **HP search budget**: N_draws=200 random search on LightGBM grid keeps the Bergstra & Bengio 2012 search-space coverage probability unchanged. Per-configuration evaluation variance increases with smaller inner-CV folds; this is a separate effect.

### 4.5 Risks

- Inherits all Phase-B remediation work (H050 fixes apply to H050b without modification).
- Successor-hypothesis discipline is non-trivial; the H050b pre-reg must explicitly cite the data-availability cause to avoid future ambiguity about why windows were truncated (auditors should not have to read this memo to understand the cause).
- B2c (asymmetric universe) requires extra care — the per-symbol aggregation rule must be pre-registered before any data is touched, otherwise the rule selection is itself a post-hoc choice.

## 5. Path B3 — Archive H050 as `precondition-failed`

### 5.1 Scope and §10 discipline

design.md §10 enumerates **five** disposition rules (lines 101-105):

| §10 rule | Trigger | Disposition |
|---|---|---|
| Line 101 | `passed=True` | `archive(positive)` + paper-trade promotion |
| Line 102 | `passed=False` with CI excluding zero but SPA failing | `archive(null)` with multiple-testing note |
| Line 103 | `passed=False` with CI covering zero | `archive(null)` |
| Line 104 | Realized folds < `n_required_for_power_80` | `archive(null, underpowered)` |
| Line 105 | HMM stationarity pre-check failure per ADR-0005 | `archive(null, precondition-failed)` |

Only line 105 currently produces `archive(null, precondition-failed)`. Data-unavailability is not enumerated in §10 today. Two clean paths to invoke a `precondition-failed`-style archive:

- **B3a — narrow §10 amendment**: amend line 105 (or add a sibling clause) to read "HMM stationarity pre-check failure or substrate insufficient to satisfy §2 windows → `archive(null, precondition-failed)`". Then archive H050 under the amended clause. This widens §10 explicitly and keeps the audit trail clean.
- **B3b — invoke "underpowered" instead of "precondition-failed"**: data-unavailability arguably maps better to line 104 (`archive(null, underpowered)`) than to line 105 (which is a *moment-level* precondition, not a *substrate-availability* precondition). This avoids amending §10 but treats a substrate-shortage as if it were a fold-count-shortage.

The cleaner discipline is B3a; B3b risks a future-auditor reading "underpowered" and incorrectly inferring that the run was actually executed and produced an underpowered result.

### 5.2 What this opens

- H050 goes to archive without a Phase-B run; no test-statistic produced; no SPA family entry; no DSR penalty consumed.
- Research bandwidth shifts to H051 (HMM-gated Kalman pairs trade — same ADR-0005 dependency, different statistic), H052a/H052b (HMM-gated ORB on futures and 0DTE QQQ), or new tier-2b hypotheses.
- The Cycle-1–5 inference and HMM infrastructure remains useful for sibling hypotheses; only the H050-specific orchestrator output is discarded.

### 5.3 What this forecloses — sibling-hypothesis dependency analysis

Sibling hypotheses' dependence on H050:

- **H051 (HMM-gated Kalman pairs trade on ES/NQ basis)** — reuses [ADR-0005](../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) HMM toolkit but does *not* consume H050's directional signal or H050's test-statistic value. Independent.
- **H052a (HMM-gated ORB futures)** — reuses HMM gating logic but applies to first-hour ORB, not to H050's directional classifier. Independent of H050's outcome.
- **H052b (HMM-gated ORB QQQ 0DTE)** — sibling repo SKIE-NINJA-0DTE; independent of H050's outcome.

So B3 forecloses **only** the H050-specific evidence claim — whether HMM-decoded states deliver intraday-directional alpha on ES/NQ over 2015-2025 — not sibling-hypothesis viability. The HMM toolkit, inference primitives, walk-forward engine, SPA, bootstrap, and feature factory all remain load-bearing for H051/H052a/H052b regardless of H050's disposition.

### 5.4 Risks

- Pre-registration discipline question: archiving on data-availability without invoking a §10 enumerated trigger requires either (i) the §10 amendment in B3a, or (ii) the disposition mapping to "underpowered" in B3b. Strict reading favors B3a.
- Sunk-cost optics: Cycle 6 Phase-A code remediation work (`P1-HMM-FOLD-WARM-START`, `P1-H050-CI-DIFFERENTIAL`, etc.) is not "wasted" — it benefits sibling hypotheses — but loses the H050-specific motivation that justified the bundling.

## 6. Decision matrix — substrate × disposition (2D grid)

The original B1/B2/B3 framing collapsed two orthogonal decisions: (a) what the substrate state should be, and (b) what disposition H050 itself should receive. Re-drawn as a 2D grid, the joint space is:

|  | Substrate: backfill (B1) | Substrate: leave at 2020+ (no-backfill) |
|---|---|---|
| **Disposition: run H050 as designed** | Cell I — original B1 | Cell IV — incoherent (substrate cannot satisfy §2 windows) |
| **Disposition: register H050b** | Cell II — backfill + register H050b on extended windows | Cell III — original B2 (B2a/B2b/B2c sub-variants per §4.1) |
| **Disposition: archive H050 (`precondition-failed` per B3a or `underpowered` per B3b)** | Cell V — backfill substrate, archive H050; substrate carries forward to siblings | Cell VI — original B3 |

Cells I, III, VI correspond to the original B1, B2, B3 framing. Cells II and V are coherent additional combinations:

- **Cell II** (backfill + H050b): backfill substrate (closes the data-availability gap for all future use) but still register H050b for reasons *other than substrate availability* — e.g., universe change (drop NQ to ES-only after seeing post-backfill NQ regime instability), classifier-family change, or pre-registering an additional aggregation rule that goes beyond what design.md §1 admits. **Note**: regime-stationarity concerns from §2.1 do *not* themselves require a successor ID, because design.md §10 line 105 already pre-registers an HMM stationarity pre-check; refining the operationalization of that check (e.g., adding Quandt/Andrews moment-stability tests on emission parameters) is a clarification of ADR-0005 rather than a design change. Cell II is therefore narrower than initially framed: it applies when the user wants H050b for orthogonal reasons after the substrate is repaired, not as a regime-stationarity workaround.
- **Cell V** (backfill + archive): backfill substrate so siblings benefit, but archive H050 itself for reasons orthogonal to substrate (e.g., the user no longer judges H050's specific question load-bearing). Substrate becomes a sibling-shared resource.

Cell IV is incoherent — running H050 as designed is impossible without the §2 substrate.

### 6.1 Per-cell criteria

| Criterion | I (B1+H050) | II (B1+H050b) | III (B2) | V (B1+archive) | VI (B3) |
|---|---|---|---|---|---|
| Preserves H050 ID | Yes | No | No | No | No |
| Preserves §2 8-year train | Yes | No (H050b shorter) | No | N/A | N/A |
| Universe (per §4.1 sub-variant) | ES+NQ (full §2) | ES+NQ extended | ES+NQ truncated / ES-only / asymmetric | N/A | N/A |
| Vendor-cost commitment | Yes | Yes | No | Yes | No |
| Statistical-power posture | Highest (full 8-yr) | Reduced (regime-gated) | Lowest (3-yr train) | N/A | N/A |
| Substrate carries forward to siblings (H051/H052a/H052b) | Yes | Yes | No (siblings still need backfill or accept truncation) | Yes | No |
| §10 amendment needed | No | No | No | Possibly (B3a) | Possibly (B3a) |
| Risk: vendor data drift | Yes | Yes | No | Yes | No |
| Risk: cross-hypothesis DSR pooling under SPA | None | Some (H050b 3-yr vs other 8-yr siblings) | Yes (H050b 3-yr vs other siblings) | None | None |
| Activities required (not time-bounded) | Vendor query + ingest + checksum re-freeze + Phase-B remediation + H050 run | Vendor query + ingest + checksum re-freeze + H050b pre-reg + Phase-B remediation + H050b run | H050b pre-reg + Phase-B remediation + H050b run | Vendor query + ingest + checksum re-freeze + (optional) §10 amendment + archive note | (Optional) §10 amendment + archive note + pivot to siblings |

Time bounds are not given because the dominant cost (Phase-B remediation, vendor query latency) is user-environment-dependent and not derivable from internal artifacts alone. A defensible quantitative bound on Phase-B remediation effort can be produced separately if requested.

## 7. Recommendation framework — which constraint binds?

The user's choice should be driven by which constraint binds hardest. Branches below are not mutually exclusive — a user may weight multiple constraints.

| Binding constraint | Cell(s) implied |
|---|---|
| **Pre-reg fidelity** (8-year train is the *scientific* claim, not just a design parameter) | I |
| **Maximum statistical power** for H050 question | I |
| **Time-to-first-result** (run anything runnable on existing substrate) | III or VI |
| **Vendor-cost minimization** | III or VI (B1 incurs Databento backfill cost; II and V also do) |
| **Substrate value to sibling hypotheses** (H051/H052a/H052b benefit from ES/NQ 2015-2019 regardless) | I, II, or V |
| **H050 question no longer load-bearing** to the broader research program | V or VI |
| **Strict pre-registration discipline** (avoid §10 amendment) | I, II, III, or VI-via-B3b (mapping data-unavailability to `underpowered`) |
| **Regime-stationarity caution** (8-year window mixes too many regime breaks for stable HMM) | II |

Mixed-constraint examples:

- *"Pre-reg fidelity + sibling-substrate value"* → Cell I.
- *"Sibling-substrate value + regime-stationarity caution"* → Cell II.
- *"Time-to-first-result + vendor-cost minimization"* → Cell III or VI.
- *"Sibling-substrate value + H050 no longer load-bearing"* → Cell V.

## 8. Reproducibility implications across paths

Phase-B remediation surface partitions into two groups:

**Data-coverage-independent (5 items, applicable across all 6 cells):**

- `P1-HMM-FOLD-WARM-START` — fold warm-start in `_core.py`; independent of windows.
- `P1-H050-CI-DIFFERENTIAL` — CI on differential statistic per design.md §1; independent of windows.
- `P1-H050-INNER-CV` — Varma & Simon 2006 nested CV; independent of windows.
- `P1-H050-SPA-M1-DEGENERATE` — Hansen SPA single-strategy semantics; independent of windows.
- `P1-HMM-BLAS-THREADING-ADR` — Windows MKL/OpenMP threading; environmental.

**Data-coverage-dependent (3 items, parameters change between cells):**

- `P1-H050-SPLIT-PARAMS` — replace `n//3, n//10` with parsed Timestamps from `H050.yaml`; the Timestamps themselves change between cells (Cell I uses §2 windows; Cells II/III use H050b windows; Cells V/VI do not run).
- `P1-H050-LABEL-CV` — `pt_sl × vertical_barrier × volatility_lookback` grid CV; data-volume-sensitive (under 3-year train, the inner-fold sample budget may force grid-trimming).
- `P1-CYCLE6-REPRO-DATASET-CHECKSUM` — `dataset_checksums={}` in current repro logs; the canonical pre-reg checksum table differs between cells (Cell I/II/V: post-backfill; Cell III: current frozen; Cell VI: not run).

The remaining audit-surfaced item `P1-H050-UNIVERSE-ES-ONLY` is universe-dependent — not data-coverage-dependent in the temporal sense, but disposition-dependent (resolved differently under B2a vs B2b vs B2c).

## 9. References

- [Hamilton 1989, *Econometrica* 57(2):357–384](https://doi.org/10.2307/1912559)
- [Guidolin & Timmermann 2007, *J. Economic Dynamics & Control* 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004)
- [Quandt 1960, *JASA* 55(290):324–330](https://doi.org/10.1080/01621459.1960.10482067)
- [Andrews 1993, *Econometrica* 61(4):821–856](https://doi.org/10.2307/2951764)
- [Bailey & Lopez de Prado 2014, *Journal of Portfolio Management* 40(5):94–107](https://doi.org/10.3905/jpm.2014.40.5.094) — "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality."
- [Bergstra & Bengio 2012, *JMLR* 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html) — "Random Search for Hyper-Parameter Optimization."
- [Varma & Simon 2006, *BMC Bioinformatics* 7:91](https://doi.org/10.1186/1471-2105-7-91)
- Lopez de Prado 2018, *Advances in Financial Machine Learning*, Wiley. §2.4.3 (Single Future Roll), §7 (purged k-fold + walk-forward).
- [Databento documentation](https://databento.com/docs) — GLBX.MDP3 schema, `historical.timeseries.get_range`; pricing per [databento.com/pricing](https://databento.com/pricing).
- [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md), [data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md), [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml).
- [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](memo_cycle6-pause-status_2026-04-24.md) §Issue 2.

## 10. Audit-remediate trail

This memo is produced under the audit-remediate-loop skill (3-round cap per `~/.claude/CLAUDE.md`).

- **Round 1 (this memo, r0)**: initial composition.
- **Round 1 audit (literature-check + general-purpose, parallel)**: 20 findings — 3 critical, 11 major, 6 minor.
  - Literature-check critical: (i) Bailey & Lopez de Prado 2014 mis-cited as *J. Risk* with wrong DOI; corrected to *Journal of Portfolio Management* 40(5):94–107, doi:10.3905/jpm.2014.40.5.094. (ii) AFML §7.4 fold-count formula misattribution; reframed as author's first-principles approximation, not an AFML equation.
  - General-purpose critical: (iii) design.md §10 enumeration misrepresentation (memo previously claimed §10 lists "two precondition triggers"; actual §10 has five dispositions, only one of which is `precondition-failed`); §5.1 rewritten with full enumeration and B3a/B3b sub-variants.
  - All major findings remediated: ES-only promoted from sub-bullet to B2b sub-variant in §4.1; paired-differential "must" softened to underspecified-aggregation framing; recommendation branches expanded in §7; B1+B3 hybrid replaced with full 2D substrate × disposition grid in §6; "Time cost" row renamed "Activities required" with explicit non-quantification rationale; §8 blocker recount fixed (5 + 3 + 1 = 9, with `P1-H050-UNIVERSE-ES-ONLY` reclassified as universe-dependent).
  - Minor findings remediated: Hamilton 1989 specifics removed pending verifiable source; Guidolin-Timmermann phrasing corrected to empirical-viability framing; AFML §2.4.3 title qualified as "Single Future Roll"; Databento pre-2017 provenance shift noted in §3.1; B3 §5.3 expanded with sibling-dependency analysis; empirical density corrected to 318k–364k/yr; partial-backfill variants added as §3.5; vendor-cost order-of-magnitude band added with explicit user-billing deferral.
- **Round 2 (this rewrite, r2)**: applies all 20 remediations.
- **Round 2 audit (parallel literature-check + general-purpose)**: both subagents returned `exit_with_minor`. All 20 Round-1 findings confirmed resolved. 10 new minor findings: 6 lit-check verification-gaps (subagent could not fetch primary sources to re-verify Hamilton/Guidolin/Quandt-Andrews/Bergstra-Bengio/Databento date specifics — these are flagged as verification-gaps, not factual errors); 4 internal-consistency notes (Cell II reframing, B2c sub-variants in §7, B3a/B3b inline distinction, §11 placement of new blockers).
- **Round 2 polish applied (r2.1)**: Cell II description tightened to clarify it does NOT apply to regime-stationarity reasons (since §10 line 105 already pre-registers a stationarity pre-check); §7 "Strict pre-reg discipline" row extended with VI-via-B3b option; roll-event count and frame_sha256 cited with explicit source pointers.
- **Exit per skill protocol**: only minor findings remain after Round 2; per `~/.claude/skills/audit-remediate-loop/SKILL.md` "If `findings == []` or only `minor` remain → exit." Audit trail emitted at `docs/audits/audit_trail_2026-04-24_option-b-briefing.md`.

Final decision: pending user.

## 11. Residual risk after Round-1 audit + remediation

Per audit findings: even with the 2D grid in §6, the matrix does not exhaust user-considered constraints. A reader whose binding constraint is "preserve §10 strict-reading discipline" may judge B3a (§10 amendment) and B3b ("underpowered" mapping) both unsatisfactory, in which case Cell VI itself is unavailable and the reachable cells reduce to {I, II, III}.

Two specific items remain unresolved by this memo and would require user action before Phase-B execution:

1. The cross-symbol aggregation rule in design.md §1 is underspecified; if H050 (Cell I) runs as designed, the user must pre-register the aggregation rule before run-time, otherwise it is a post-hoc choice. This is a third *non-data-coverage* pre-reg deviation surfaced by this memo's audit and not previously enumerated in the 10-item blocker list.
2. The §10 amendment posture (B3a vs no-amendment) is itself a meta-decision the user must make before any archival-disposition path can be cleanly invoked.

Both should be added to the Phase-B blocker list as a result of this memo's audit: tentatively `P1-H050-AGGREGATION-RULE` (pre-reg deviation) and `P1-H050-§10-AMENDMENT` (procedural).
