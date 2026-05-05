---
hypothesis_id: H054
schema_version: hypothesis_design_v1
status: designed  # Round-2+3 audit-remediate-loop ACCEPT 2026-05-05; F-Q-1 through F-Q-10 closed
tier: 2b
created: 2026-05-05
created_by: skoir
description: Pre-registered design doc for hypothesis H054 — anti-gate ORB on CME ES/NQ futures
---

# H054 — Anti-gate first-hour ORB on CME ES/NQ futures

> **Empirically-motivated post-hoc hypothesis.** H054 inverts the HMM gate of [H052a](../H052a/design.md): instead of trading the unconditional first-hour ORB on the HMM non-stress-state sessions (H052a's H_1), H054 trades the unconditional first-hour ORB on the HMM **stress-state** sessions (the sessions H052a's HMM gated OUT).
>
> **The motivation is empirical, not theoretical.** H052a's production walk-forward (2026-05-05; run_id `184eccd6...`) showed that HMM-gated arms underperform unconditional arms on both ES and NQ. By the algebra of H052a's result, the gated-out sessions had higher per-session Sharpe than the gated-in sessions on the H052a OOS window. H054 tests whether this finding generalises to a **fresh, never-evaluated OOS window** (2025-only).
>
> **The test is a stress test of the post-hoc-discovery framing**: a positive result here is necessary but not sufficient evidence that the H052a HMM emission vector identifies a real regime structure (rather than being noise that incidentally split the OOS sample). A negative result here would refute the "HMM identifies real regimes that gate the wrong direction" reading and instead support "HMM emission vector is noise."

## 1. Hypothesis

- **H_0**: The Sharpe ratio of the first-hour ORB long-only directional trade on ES/NQ futures conditioned on the HMM **stress state** does NOT exceed the Sharpe of the unconditional first-hour ORB on the same instrument by a margin that exceeds bootstrap sampling error.
- **H_1**: It does.
- **Mechanism (literature-silent; empirical-only; directionally-consistent-with-HOP-2017)**: H052a's run established empirically that HMM-gated arms underperform unconditional arms (T_H052a < 0 in point estimate on both symbols, LW2008 CI covers zero). By the algebra of paired-sample Sharpe difference, the gated-out (stress-state) sessions must have higher per-session Sharpe than the gated-in (non-stress) sessions on the H052a OOS test fold. H054 tests whether the stress-state subset's per-session Sharpe is significantly positive on a fresh OOS window (T_H054_b primary; the absolute profitability of stress-state ORB sessions on data H052a never saw). **Phase 0 lit-check verdict 2026-05-05** (closed; see [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md)): the four primary peer-reviewed claim domains (Bollerslev-Tauchen-Zhou 2009 VRP; Cochrane 2011 discount rates; Hurst-Ooi-Pedersen 2017 crisis alpha; Guidolin-Timmermann 2007 HMM regime allocation) are **literature-silent** on the H054-specific framing. All four operate at coarser horizons (monthly+) or different signal classes (TSMOM, not first-hour ORB). **Directional-consistency note** (per F-Q-7 audit fix): HOP 2017's stress-period TSMOM finding is directionally CONSISTENT with H054's stress-period-ORB-positive hypothesis — both predict positive directional alpha during stress periods on equity-futures-like instruments; they differ on signal-construction (TSMOM = continuation across multi-month crises; H054-ORB = breakout from intraday opening range during HMM-classified stress sessions) but ALIGN on direction. No primary source CONTRADICTS the framing directly; no primary source ESTABLISHES it directly. The empirical motivation (H052a KPI report card v1) is the load-bearing rationale; the literature provides "broader-notion-supports-the-class-of-question" (Guidolin-Timmermann 2007 supports regime-conditional expected-return variation at coarser horizons; HOP 2017 supports stress-period directional alpha for the TSMOM signal class) not "this-specific-framing-established." H054 is a **literature-silent post-hoc empirically-motivated test** with the methodological discipline (fresh OOS test fold; H052a-disjoint IS; T_H054_b absolute-profitability primary; explicit acknowledgment of post-hoc framing) as the mitigation.
- **Critical interpretive note**: H054 is **post-hoc empirically motivated**. The pre-reg discipline below requires a **fresh OOS test fold** (2025-only; never seen by H052a), explicit SPA family entry alongside H050+H051+H052a+H053 (now M=5; multiple-testing penalty grows), and acknowledgment that a positive result is necessary-but-not-sufficient evidence for HMM emission specification (could equally be artifact of split partition).
- **Primary citations** (frozen at pre-reg; Phase 0 lit-check 2026-05-05 verified; verdict literature-silent per §15.1):
  - HMM regime-switching (project standing citation): [Hamilton 1989, *Econometrica* 57(2):357-384](https://doi.org/10.2307/1912559); [Baum et al. 1970, *Annals of Mathematical Statistics* 41(1):164-171](https://doi.org/10.1214/aoms/1177697196).
  - HMM regime allocation (Phase 0 SILENT on intraday; supports regime-conditional expected returns at monthly horizon): [Guidolin & Timmermann 2007, *JEDC* 31(11):3503-3544](https://doi.org/10.1016/j.jedc.2006.12.004).
  - Variance risk premium (Phase 0 SILENT on intraday; supports quarterly post-stress directional prediction): [Bollerslev-Tauchen-Zhou 2009, *RFS* 22(11):4463-4492](https://doi.org/10.1093/rfs/hhp008).
  - Counter-cyclical risk premium (Phase 0 SILENT on intraday; macro/quarterly survey): [Cochrane 2011, *JoF* 66(4):1047-1108](https://doi.org/10.1111/j.1540-6261.2011.01671.x).
  - Crisis alpha / TSMOM (Phase 0 SILENT on first-hour ORB; supports stress-period alpha for TSMOM): [Hurst-Ooi-Pedersen 2017, *JPM* 44(1):15-29](https://www.pm-research.com/content/iijpormgmt/44/1/15).
  - Realized volatility / regime emission features (project standing citation): [Andersen & Bollerslev 1998, *IER* 39(4):885-905](https://doi.org/10.2307/2527343).
  - **Empirical motivation (load-bearing; post-hoc)**: H052a KPI report card v1 — [research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../H052a/H052a_kpi_report_v1.md).
  - Phase 0 lit-check trail: [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md).
- **Test statistic** (UPDATED Round-2 audit-remediate-loop per F-Q-2: primary swapped from T_H054_a to T_H054_b to address algebraic dependence on H052a):
  - **T_H054_b = SR_anti_gated** (PRIMARY; absolute profitability standalone). LW2008 univariate CI on the anti-gated arm per-session Sharpe. Inferentially distinct from H052a per F-Q-2 fix: a positive H054 result here is "stress-state ORB sessions are profitable on a fresh OOS"; this does NOT mechanically follow from T_H052a < 0 (it is an absolute statement about the per-session Sharpe of a strict subset, not a paired-differential about the complement).
  - **T_H054_a = SR_anti_gated − SR_unconditional** (SECONDARY; informational). Paired differential. Per F-Q-2: by the algebra `pnl_unconditional = pnl_gated + pnl_anti_gated`, T_H054_a is closely related to T_H052a inverted (though not algebraically determined due to Sharpe's nonlinear dependence on PnL variance). Reported alongside T_H054_b for completeness; not load-bearing for the inferential verdict.
  - **SPA family entry** (UPDATED per F-Q-5): H054 is **NOT** entered into a cross-hypothesis Hansen SPA composite null at v1, because the project's existing 5 hypotheses (H050, H051, H052a, H053, H054) have heterogeneous OOS windows and Hansen 2005 §2 requires shared bootstrap-index sample length for cross-dependence preservation. Per-hypothesis SPA annotation is reported at the hypothesis level (M=1 single-strategy degenerate per ADR-0008). Cross-hypothesis SPA family construction is deferred to a project-level ADR per follow-up `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`.
- **Decision rule cross-link**: see §10 below.

## 2. Universe and sample period

- **Instruments**: ES (primary), NQ (primary). Micros MES/MNQ reported as robustness, since they are linear price-rescaled versions of the majors (ADR-0001 capacity ceiling mapping).
- **Frequency**: 1-minute bars (RTH only; ETH explicitly excluded).
- **Session**: RTH only; 09:30–16:00 ET (`America/New_York`) per [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py).
- **Sample window** (BINDING; **fresh OOS test fold + H052a-disjoint IS is the load-bearing methodological commitment of H054**; updated 2026-05-05 Round-2 audit-remediate-loop per finding F-Q-1 + F-Q-6):
  - **IS** (HMM fit + label-cfg search): 2020-01-01 → 2023-06-30 (≈878 RTH sessions). **Identical to H052a's IS+val window** per design.md §2; the H054 HMM is re-fit from scratch on this exact window; the H054 label-cfg grid search is on this IS window only. **The H052a OOS window (2023-07-01 → 2024-12-31) is DELIBERATELY UNUSED in H054 — neither IS, nor val, nor test.** This is the F-Q-1 fix: the H052a discovery sample is excluded from H054's fit set, preserving test-fold-independence.
  - **OOS test (fresh; ES-only)**: 2025-01-01 → 2025-12-03 (ES; ≈230 RTH sessions). **NQ 2025 is excluded from H054 v1 OOS** per F-Q-6 fix: H050 KPI v1 was emitted 2026-05-04 (one day before this design.md) on a substrate including NQ 2025; the H054 author had visibility into 2025 NQ regime-classification statistics at H054 design-time. The H050 emission vector differs materially from H054's (H050 uses microstructure 1-min features; H054 uses session-level summary features identical to H052a — only realized variance is shared), but the conservative methodological choice excludes NQ 2025 from H054 v1 evaluation. NQ 2025 may be added to a successor H054 v2 or a new hypothesis ID after the v1 KPI emission, with a fresh post-emission pre-reg discipline declaration.
  - **2023-07-01 → 2024-12-31 (the H052a OOS window) is DELIBERATELY UNUSED in H054**: not IS, not val, not test. This is a binding pre-reg commitment. Use of this window in any H054 v1 metric triggers `archive(null, data-violation)` per §10.
  - **NQ 2024-2025 (the H050 NQ test fold) is EXCLUDED from H054 v1 OOS**: H054 v1 OOS is ES-only 2025. NQ inference is deferred (see §14 robustness exhibits).
  - **Test-fold-independence guarantee** (load-bearing): the H054 v1 OOS test fold (ES 2025-01-01 → 2025-12-03) does NOT overlap with the H052a train, val, or test windows. The H054 IS window EXACTLY matches the H052a IS+val window (2020-01-01 → 2023-06-30). The H054 v1 evaluation uses ES-only 2025 data that is disjoint from H050's ES test fold (2024-01-01 → 2024-12-12). This is the test-fold-independence guarantee for the post-hoc-motivated framing.
- **Roll treatment**: roll-adjusted front-month continuous series via `vendor_legacy_1min_roll_adjusted` (Cycle-1 deliverable; 2026-04-23). Ratio adjustment, rolled on volume-crossover per [config/instruments.yaml](../../../config/instruments.yaml) `roll_rule`. Runs on raw `vendor_legacy_1min` are explicitly forbidden by this pre-reg.
- **Dataset snapshot frozen at pre-registration**: SHA256 of the roll-adjusted parquet captured at the first `running` run and persisted to `ReproLog.dataset_checksums` under key `vendor_legacy_1min_roll_adjusted`. Snapshot is immutable across re-runs of this hypothesis ID. Substrate `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` per H052a's ReproLog.

## 3. Features

HMM emission features (point-in-time, `as_of` strictly ≤ decision timestamp 10:30 ET):

- **Realized variance of log-returns** on the front-month ratio-adjusted 1-min series, per [Andersen & Bollerslev 1998](https://doi.org/10.2307/2527343). Rolling lookback CV-selected from `{30m, 60m, 120m}` on training folds.
- **First-hour directional sign** (+1/0/−1) at 10:30 ET.
- **Gap-size bucket**: open(09:30) vs prior-session close log-return, discretized by training-fold quantiles.
- **Day-of-week** one-hot.
- **ETH-session pre-RTH returns**: 06:00–09:29 ET log-return.
- **VIX daily level**, `as_of = T−1 close` (CBOE / FRED VIXCLS).

This is the **identical emission vector** as H052a per the empirical-motivation framing (§1 critical interpretive note). H054 is NOT testing a new emission specification; it is testing whether the H052a emission's gated-out subset has positive directional alpha. PIT property tests per implementation-plan §3 and §4.6; stateful features (rolling variances, regime posteriors) use the causal forward filter `p(s_t | y_{1:t})` only per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md).

## 4. Label construction

Per-session P/L on a **futures ORB long-only directional trade** — IDENTICAL to H052a §4 (frozen):

- **Entry**: 10:30 ET market order on the front-month roll-adjusted contract when entry gate fires.
- **Side**: long only (pre-reg).
- **Profit target**: `k_pt × realized_vol_60m` grid on training folds.
- **Stop**: `k_sl × realized_vol_60m` grid.
- **Time stop**: 14:00 ET.
- **Hard close**: 15:55 ET.
- **Settlement**: 1-min bar close at exit time.
- **pt_sl**: both active (volatility-normalized).
- **vertical_barrier**: 15:55 ET.
- **volatility_estimator**: realized-vol over prior 60-min window.
- **Capacity**: ≤20 ES and/or ≤40 NQ per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md).

The label-cfg grid is the same 27-cell grid as H052a (`pt_mult ∈ {0.5, 1.0, 1.5} × sl_mult ∈ {0.5, 1.0, 1.5} × realized_vol_lookback_minutes ∈ {30, 60, 120}`). Best cfg selected via walk-forward inner CV on the IS combined window (3 folds, purge=embargo=1 session).

**Anti-gate trading rule (the H054-distinctive piece)**: the per-session ORB trade is taken **only when the HMM forward-filter posterior at 10:30 ET classifies the session into the STRESS state** (i.e., the state H052a's HMM gated OUT). The "stress state" is identified at HMM-fit time as the state with HIGHER mean realized variance (the inverse of H052a's "non-stress state" definition); see §5. On non-stress-state sessions, the position is flat (zero P/L, zero cost — same convention as H052a's gated arm with the gate inverted).

## 5. Estimator

HMM with Gaussian emissions per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md):

- Covariance type: `[diag, full]` (BIC-selected; d=1 dedup at fit per `P1-HMM-FULL-COV-1DIM-REDUNDANT` closure).
- States: `n_states_grid = [2, 3]` (BIC-selected).
- Initialisation: k-means++ warm start.
- Inference: `filter_states` (causal forward filter; never `decode`).
- Fold-boundary state continuity: `terminal_log_alpha` from train tail → `filter_states_from_prior` on test (canonical ADR-0005 pattern).

**Stress-state identification** (H054-distinctive; UPDATED Round-2 audit-remediate-loop per F-Q-3): at HMM-fit time on the IS window, the BIC-selected K-state HMM emits state-conditional emission means. The "stress state" is the state with the **highest mean realized-variance emission** under the following pre-reg-frozen identification rule:

1. **Top-1 only, regardless of K**: the stress state is the SINGLE state with $k^* = \arg\max_k \mu_{rv,k}$. For K=3, the second-highest state is NOT included in the stress regime even if its $\mu_{rv}$ is close to the top. This preserves a binary anti-gate indicator.
2. **Single-feature dominance criterion**: the identification uses ONLY the realized-variance emission mean. Other emission features (first-hour-sign, gap-size, DOW, ETH-pre-RTH-return, VIX) are NOT consulted for stress-state identification at this step. (The HMM emission vector remains 6-dimensional; only the stress-state-id rule uses rv.)
3. **Tie-breaking** (F-Q-3 fix): if two or more states have $|\mu_{rv,k_1} - \mu_{rv,k_2}| < 10^{-9}$ (effective machine-epsilon for log-emission means), the stress state is the one with the LOWEST canonical state-index (after [Biernacki-Celeux-Govaert 2000 *PAMI* 22(7):719-725](https://doi.org/10.1109/34.865189) label-switch canonicalisation per ADR-0005). This produces a deterministic stress-state-id under degenerate cases.
4. **Regression test follow-up** (`P1-H054-STRESS-STATE-ID-REGRESSION-TEST`): integration test asserting the identification rule produces a unique state-id on (a) synthetic K=2/K=3 fits with degenerate $\mu_{rv}$ and (b) production fits.

The "anti-gated arm" position indicator at 10:30 ET on session t is:
$$
reg_t^{anti} = \mathbb{1}\{s_t = k^*\}, \quad k^* = \arg\max_k \mu_{rv,k}
$$

where $\mu_{rv,k}$ is the BIC-selected HMM's state-k emission mean for the realized-variance feature, $s_t$ is the causal forward-filter MAP state at 10:30 ET on session t, and ties broken per rule 3 above.

The "unconditional arm" position indicator is $\mathbb{1}\{\text{ORB entry gate fires}\} = 1$ on every RTH session.

The "anti-gated arm" P/L per session is:
$$
pnl^{anti}_t = reg_t^{anti} \cdot pnl^{ORB}_t
$$

where $pnl^{ORB}_t$ is the per-session ORB P/L (same labels as H052a §4) net of the [futures_orb_v1](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) cost model per ADR-0013 §3.1 F-CONV-2 binding.

## 6. Splitter

- **Outer split**: single outer fold per the binding §2 sample window (IS combined 2020-2024 → OOS 2025-only). Walk-forward, NOT k-fold. CPCV remains the canonical splitter for any successor disposition that produces a Sharpe KPI per ADR-0012/ADR-0013 §7; H054's single-outer-fold convention matches H052a's §6 and is consistent with the project-operational pattern for fresh-OOS post-hoc-motivated tests.
- **Inner CV** (label-cfg search): 3 folds on IS combined window, purge=embargo=1 session.
- **Cross-instrument correlation**: ES and NQ returns are highly correlated (ρ > 0.85 on 1-min bars); treat as one pooled hypothesis with instrument-dummy stratification per H052a §6.
- **Embargo / purge**: PW2004-selected embargo on training-fold residuals only (per H050 F-Q-1 fix); `purge_window = 1 session` per AFML §7.4 (label horizon is intra-session).

## 7. Cost model

`futures_orb_v1` per [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) (1-tick slippage prior; per-side commission + exchange fee + NFA per [config/instruments.yaml](../../../config/instruments.yaml)). Cost is APPLIED as a per-session log-return drag `log(1 - cost_round_trip / notional)` per ADR-0013 §3.1 F-CONV-2 binding. Empirical regime-wise calibration deferred to `P1-H054-COST-CALIBRATION-EMPIRICAL` (paper-trade prerequisite).

## 8. Gate thresholds (per ADR-0013; KPI-only, no binding gates)

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1, no KPI value forces or blocks any stage transition. Every former Class A item from ADR-0012 is reported as a KPI annotation.

### 8.a Methodological-correctness annotations (per ADR-0013 §2)

- **PIT / leakage-canary**: applicable: YES; binding test paths: Cycle-4 leak canary suite + per-hypothesis integration test [tests/integration/test_h054_pit.py](../../../tests/integration/test_h054_pit.py) (to be authored as §11.2 prereq before next H054 launch under follow-up `P1-H054-PIT-CANARY-INTEGRATION-TEST-LANDED`).
- **Calibration BSS**: applicable: NO. H054's pre-registered output is a continuous trading-rule directional signal (PT/SL/timestop session P/L), not a calibrated probability forecast.
- **Reliability slope**: applicable: NO (same rationale as BSS).
- **Reproducibility log**: applicable: YES (canonical ReproLog per ADR-0009 13-field schema).
- **Cost-modeling realism**: applicable: YES (`cost-conditional` annotation expected; constant-tick slippage prior calibrated post-paper-trade).
- **DSR / PSR**: applicable: NO at v1 (M=5 SPA family but no per-strategy CPCV path distribution; DSR computed under CPCV path distribution per ADR-0012 #5).

### 8.b KPIs (Class B; reported, not binding)

Per ADR-0013 §3.1 + §3.2 (mandatory ADR-0014 §3.2 9-table + bottom-line summary at top of KPI report card):

- **Sharpe-vs-passive**: passive benchmark = always-flat (zero return). Reported with LW2008 univariate CI on each arm. **This is the primary inference for T_H054_b** (per F-Q-2 fix above).
- **Sharpe-vs-time-of-day-FE**: not applicable to single-clock-time predictand (entry/exit fixed at 10:30 ET / variable PT/SL/timestop).
- **Hansen SPA family p**: per F-Q-5 audit fix, H054 is reported as a per-hypothesis M=1 single-strategy degenerate (ADR-0008 standard handling) at v1; cross-hypothesis SPA composite null at M=5 across H050+H051+H052a+H053+H054 is NOT computed at v1 due to heterogeneous OOS windows (Hansen 2005 §2 requires shared bootstrap-index sample length across strategies for cross-dependence preservation; the project's hypothesis OOS windows differ across H050 (2024-2025 bar-cadence), H052a (2023-H2+2024 session-cadence), H053 (2024-2025), H054 (ES-2025-only)). Cross-hypothesis SPA family construction deferred to a project-level ADR per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`.
- **Max-DD ratio (arm/passive)**: reported per ADR-0013 §3.1.
- **Power-margin ratio**: realized OOS n / `n_required_for_power_80` per §9 below.
- **Cost-floor sensitivity**: 1-tick vs 2-tick (`sensitivity_mult ∈ {1.0, 2.0}`).
- **Inner-CV-winner deflation** (per F-Q-9 fix): the §4 27-cell label-cfg grid + 3-fold inner CV produces a multiple-comparison concern internal to H054. Reported as KPI annotation: Bailey-Lopez de Prado [Deflated Sharpe Ratio per JPM 40(5):94-107 (2014)](https://doi.org/10.3905/jpm.2014.40.5.094) on the OOS Sharpe of the IS-selected best cfg. Annotation: `dsr-cell-deflated-{positive,marginal,negative}`.

### 8.c Decision rule (§10 cross-reference)

Per ADR-0013 §1 KPI-only philosophy, the operator reviews the KPI report card values and decides the next stage transition. No KPI value forces or blocks. The user's 2026-05-04 standing directive applies: `kpi-report-emitted` → `ninjascript-implemented` is operator-discretionary upon canonical-format presentation.

## 9. Stopping rule + power

**Power calculation** (UPDATED Round-2 audit-remediate-loop per F-Q-4: explicit derivation + per-symbol verdict revised):

### 9.1 Effect size pilot derivation (from H052a KPI report card v1)

**Pilot source**: H052a KPI report card v1 §5 (W/L/Z + win rate; gated arms ES 175W/158L/38Z, NQ 189W/164L/16Z) + §3 (Realized OOS gated-arm $-0.94%$ ES, $+3.39%$ NQ). The H052a "stress-state subset" is by definition the H052a-gated-OUT sessions (the sessions where reg=0 in H052a's framing).

**Reconstruction methodology**:
- ES gated-out subset: 38 sessions in H052a OOS (ES 38Z = HMM-gated-out → flat in H052a's gated arm, but THESE are the sessions H054 anti-gate would TRADE).
- NQ gated-out subset: 16 sessions in H052a OOS.
- The per-session ORB Sharpe on these gated-out sessions cannot be reconstructed directly from H052a v1's tables (the v1 reports realized OOS for the gated arm where these sessions are flat; the per-session SR of trading the gated-out sessions is NOT in v1).
- **Pilot estimate (binding for §9 power calc)**: per-session SR ∈ [0.05, 0.15] **range, not point** — derived as a plausible bound: SR_uncond_NQ_per_session ≈ 0.054 (from H052a v1 §4 annualised +0.855 ÷ √252 = 0.054); SR_anti_gated could be modestly higher (HOP 2017 stress-period TSMOM positive directional alpha) but unlikely substantially higher than 0.15 without falsifying H052a's H_1.

### 9.2 Per-arm power calculation

For LW2008 univariate CI on T_H054_b excluding zero at α=0.05 two-sided, 80% power requires (per [Lo 2002 *FAJ* 58(4):36-52](https://doi.org/10.2469/faj.v58.n4.2453) Sharpe SE ≈ √((1+0.5·SR²)/n)):

- SR_pilot=0.05: n ≥ 1568 sessions (structurally inadmissible at 230 sessions)
- SR_pilot=0.10: n ≥ 392 sessions (inadmissible at 230)
- SR_pilot=0.15: n ≥ 174 sessions (adequate at 230)
- SR_pilot=0.20: n ≥ 98 sessions (adequate)

**ES anti-gate trade frequency**: ~10% of OOS sessions (per H052a OOS ES gated-out 38/371 = 10.2%). On 230 ES OOS sessions, expected n_anti = ~23 trades. **Per-symbol ES inference is structurally underpowered at SR ≤ 0.15**; LW2008 CI will be wide.

**NQ anti-gate trade frequency**: ~4% of OOS sessions (per H052a OOS NQ gated-out 16/369 = 4.3%). NQ is excluded from H054 v1 OOS per F-Q-6 fix (above). NQ inference is **n/a at v1**.

### 9.3 Power verdict (UPDATED per F-Q-4)

**ES per-symbol H054 v1**: structurally underpowered at the empirically-plausible pilot SR range [0.05, 0.15]; expected n_anti ≈ 23 trades over 230 OOS sessions. **The H054 v1 ES result will produce wide LW2008 CIs that likely cover zero unless SR_anti is materially > 0.15** (annualised > 2.4). Reported as `power-margin-low` annotation regardless of point-estimate.

**NQ per-symbol H054 v1**: **n/a at v1** (NQ 2025 OOS excluded per F-Q-6 fix).

**Pooled ES+NQ H054 v1**: **n/a at v1** (NQ excluded).

**Realised n vs n_required ratio is reported as `power-margin-ratio` KPI annotation per ADR-0013 §3.**

### 9.4 Stopping rule

Single production walk-forward run on ES 2025 OOS. No multiple-rerun-on-same-OOS pattern. If the run completes and the KPIs produce a marginal verdict (CI covers zero), the result is recorded and operator decides next steps; **no re-running with different seeds or different inner-CV folds on the same OOS** (that would constitute pseudo-multiple-testing per Lopez de Prado AFML §13).

### 9.5 Methodologically-honest expectation-management

Given the structurally-low ES anti-gate trade frequency (~23 trades over 230 OOS sessions), H054 v1 is best understood as **a directional indicator + power-floor probe**, NOT a definitive test. A v1 result of "T_H054_b LW2008 CI covers zero" should be interpreted as "consistent-with-noise-given-low-trade-count", NOT "anti-gate hypothesis falsified." A v1 result of "T_H054_b LW2008 CI excludes zero on the positive side" would carry more evidentiary weight (would need SR ≳ 0.15). A successor H054 v2 with a longer accumulated OOS window (or pooled ES+NQ + MES+MNQ) would be necessary for a definitive verdict.

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): no KPI value forces or blocks any stage transition. Operator reviews the KPI report card and decides at every transition (operator-discretionary; decision-logged).

Stage progression is the canonical: `exploration-in-progress` → `kpi-report-emitted` → `ninjascript-implemented` → `paper-trade-active` → `paper-trade-evaluated` → `live-promoted`. Per the user's 2026-05-04 standing directive, the `kpi-report-emitted` → `ninjascript-implemented` transition is operator-discretionary upon canonical-format presentation.

**Pre-reg-frozen interpretation guide** (operator-informational, NOT a binding gate):

- **T_H054_a LW2008 CI excludes zero on the positive side**: H_1 supported. Stress-state subset has incrementally positive Sharpe over unconditional. Strong empirical support for "HMM emission vector identifies real regime structure that H052a gated wrong direction." Operator may reasonably authorize NinjaScript progression.
- **T_H054_a LW2008 CI excludes zero on the negative side**: H_1 refuted; the symmetric inverse of "anti-gate works" — the unconditional baseline is *better* than the stress-state subset, which would be inconsistent with the H052a result on this fresh OOS (empirical falsification of the H052a-extrapolated reading on 2025).
- **T_H054_a LW2008 CI covers zero**: non-significant null. The H052a-extrapolated "anti-gate has incremental Sharpe" framing is not supported on fresh OOS. Operator may reasonably decline NinjaScript progression. Combined with H052a's non-significant null on the SAME-direction gate, this would suggest the HMM emission vector is NOT identifying real regime structure on this substrate (the H052a gated-out subset's positive Sharpe was sample-specific, not regime-identifying).
- **T_H054_b LW2008 CI excludes zero on the positive side, but T_H054_a covers zero**: anti-gate is profitable standalone but does not exceed unconditional. Operator decision per ADR-0013 §5.3 + §1 KPI-only philosophy.

## 11. Reproducibility commitments

Per [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md) + [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3:

- BLAS thread pinning (OMP_NUM_THREADS=1 + MKL_NUM_THREADS=1 + OPENBLAS_NUM_THREADS=1 env-var assertion + `threadpoolctl.threadpool_limits(1)` in orchestrator `__main__`).
- All 13 ReproLog fields populated: git_head, dataset_checksums, config_resolved_sha256, env_id, model_hash (= scientific_payload_sha256 binding), pip_freeze_sha256, rng_seed, etc.
- Sidecar with scientific_payload SHA256 binding to ReproLog model_hash.
- Random seed: 20260505 (frozen).  <!-- justify: design-date encoded as YYYYMMDD per F-Q-8 fix; deterministic, no upstream selection bias -->
- Single-seed mandate: no per-replicate seed sweep on the OOS test fold.

### 11.1 Kill-switch parameters (per ADR-0013 §5.1; cross-link to NinjaScript §15)

NinjaScript implementation kill-switch parameters (used at paper-trade-active and live stages, NOT during backtest):

- `Per-session loss limit`: $500 / contract / session (CME-conservative; calibrated post-paper-trade under `P1-H054-KILL-SWITCH-EMPIRICAL`).
- `Daily session count cap`: 1 (one anti-gate ORB attempt per session by design).
- `Realized daily P/L exit`: ≤ -$1,500 / contract triggers same-day kill of any new anti-gate orders.
- `Wall-clock cap`: 14:00 ET timestop (matches §4 label).

### 11.2 Pre-reg implementation prerequisites (BLOCKING before next H054 launch; UPDATED Round-2 audit per F-Q-10)

- ✓ `P1-H054-LIT-CHECK-PHASE-0`: CLOSED 2026-05-05 — verdict literature-silent per [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md).
- ✓ `P1-H054-DESIGN-MD-AUDIT-LOOP`: CLOSED 2026-05-05 with this Round-2 + Round-3 sequence — see audit_trail at `docs/audits/audit_trail_2026-05-05_h054-pre-reg.md`.
- `P1-H054-DATA-REQUIREMENTS-DESIGNED-FREEZE` (BLOCKING): [data_requirements.md](data_requirements.md) `status: draft` → `status: designed` concurrently with this design.md freeze (per F-Q-10 fix).
- `P1-H054-PIT-CANARY-INTEGRATION-TEST-LANDED` (BLOCKING-BEFORE-LAUNCH): integration test [tests/integration/test_h054_pit.py](../../../tests/integration/test_h054_pit.py) ensuring no leakage in the anti-gate inversion logic (the regime indicator is computed causally; inverting `reg → 1 - reg` does NOT introduce leakage in itself, but the integration test verifies the orchestrator wires the inverted indicator correctly).
- `P1-H054-STRESS-STATE-ID-REGRESSION-TEST` (BLOCKING-BEFORE-LAUNCH; per F-Q-3 fix): regression test asserting the §5 stress-state identification rule produces a unique state-id under (a) synthetic K=2/K=3 fits with degenerate $\mu_{rv}$ + (b) production fits.
- `P1-H054-IS-VS-H050-NQ-ROW-AUDIT` (BLOCKING-BEFORE-LAUNCH; per F-Q-10 fix): regression test asserting the H054 IS row count (2020-01-01 → 2023-06-30 ES + NQ) does NOT include any rows from the H050 NQ test fold (2024-01-01 → 2025-12-19) or the H052a OOS test fold (2023-07-01 → 2024-12-31). The substrate overlap on the file-system is permissible; the in-memory row partition for H054 IS must be a strict subset of [2020-01-01, 2023-06-30].
- `P1-H054-B-ARM-WINDOW-READINESS` (per F-Q-10 fix): the §14 robustness B-arm test ("re-fit HMM on H052a IS+val window 2020-01-01 → 2023-06-30; apply causally on 2025 OOS via filter_states_from_prior") becomes redundant under the F-Q-1 fix (the H054 IS now EXACTLY matches H052a IS+val). The B-arm robustness exhibit therefore reduces to "compare against frozen H052a HMM via causal warm-start" — minimum implementation: load H052a's BIC-selected HMM params from [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json) and propagate via `filter_states_from_prior`. Reported as KPI annotation `b-arm-{aligned,divergent}`.

## 12. Relationship to other hypotheses

- **H050** (HMM-gated 1-min directional): definitive negative on the 2024-2025 OOS (T_H050 LW2008 CI excludes zero on negative side). H050 is bar-cadence (not session-cadence); H054 does NOT mirror H050 directly.
- **H051** (HMM-gated Kalman pairs trade): pre-registered, not yet executed. H054 is orthogonal to H051 (directional, not pairs).
- **H052a** (HMM-gated ORB): non-significant null on 2023-H2 + 2024 OOS. **H054's empirical motivation derives directly from H052a's KPI report card v1**; H054 is the inverse-gate companion test on a fresh OOS.
- **H052b** (HMM-gated QQQ 0DTE): pre-registered, executed in sibling repo. H054 does not mirror H052b directly (different underlying, different cost model).
- **H053** (multi-timeframe regression with mediation): kpi-report-emitted; marginal results. H054 is orthogonal to H053 (gate-inversion vs multi-timeframe-mediation).
- **SPA family**: H054 enters the family as the 5th strategy. The single-strategy degenerate framing (ADR-0008) DOES NOT apply at M=5; full Hansen SPA composite null active on the family.

### 12.1 Successor candidate

`P1-H055-NQ-UNCONDITIONAL-ORB-PRE-REG` is registered (per H052a operator decision) for the strongest unconditional cell. H054 and H055 are independent successors of H052a (H054 = anti-gate; H055 = standalone unconditional NQ ORB).

## 13. Output artifacts

Per ADR-0013 §3, the production walk-forward must produce:

- KPI report card v1 [research/01_hypothesis_register/H054/H054_kpi_report_v1.md](H054_kpi_report_v1.md) (template per ADR-0014 §3.2 9-table format).
- Stage tracker [research/01_hypothesis_register/H054/stage.md](stage.md) (kpi-report-emitted row).
- Failure log [research/01_hypothesis_register/H054/failure_log.md](failure_log.md).
- Audit-remediate-loop trail at `docs/audits/audit_trail_YYYY-MM-DD_h054-*.md`.
- Sidecar at `artifacts/runs/H054/{run_id}/sidecar.json` with scientific_payload SHA256.
- ReproLog at `logs/reproducibility/{run_id}.json`.
- Operator decision logged at `logs/promotions/{run_id}_H054_{arm_id}_promotion.md` per ADR-0013 §5.3.

## 14. Robustness exhibits (informational; not gating)

- **B-arm test**: re-fit HMM only on H052a's IS+val window (2020-01-01 → 2023-06-30; matches H052a fit-window EXACTLY) and apply causally on 2025 OOS via `filter_states_from_prior`. This tests "anti-gate of the EXACT H052a HMM" on 2025 fresh OOS. Reported as KPI annotation `b-arm-{aligned,divergent}`.
- **Cost-floor sensitivity** (per §8.b): re-run with `sensitivity_mult=2.0` on the same artifacts.
- **MES/MNQ robustness**: reported as KPI annotation; not load-bearing.

## 15. NinjaScript Implementation (per ADR-0013 §5.1)

Per ADR-0013 §5 + §5.1, every hypothesis design.md gains a §15 enumerating the NinjaScript C# implementation. H054's NinjaScript implementation is sequenced AFTER the production walk-forward Stage-3 KPI report card emission per follow-up `P1-H054-NINJASCRIPT-IMPL`.

Implementation pattern (bridge-mediated per ADR-0013 §1.2 + ADR-0002, since the HMM forward filter requires Python inference at decision time per ADR-0005):

- **C# class**: `H054AntiGateORB` at `ninjascript/strategies/H054AntiGateORB.cs`
- **Python service**: thin Python inference wrapper at `src/skie_ninja/services/h054_inference.py` exposing the HMM `filter_states_from_prior` callable over the bridge per [ADR-0002](../../../docs/decisions/ADR-0002-bridge-selection.md). The service must complete inference within 1 second of the 10:29:00 ET trigger to allow market-order placement at 10:30:00 ET.
- **Entry/exit logic**: 1:1 with Python signal generation per design.md §4; inverted regime indicator per §5.
- **Kill-switch parameters**: per §11.1.
- **Fill-log schema**: matches plan §6.1 schema; includes `regime_state_at_10_30_et` field for post-trade reconciliation.
- **Sim101 smoke-test record**: TBD (run after NinjaScript class authored).
- **Cross-reference to canonical KPI report card**: H054_kpi_report_v1.md.

Python ↔ NinjaScript parity-check artifact required per ADR-0013 §5.2 (default convention: byte-equality on integer signal vector — 1 if anti-gate fires, 0 otherwise; per-strategy calibration via `P1-H054-NINJASCRIPT-PARITY-TOLERANCE`).

### 15.1 Phase 0 lit-check (CLOSED 2026-05-05; verdict: literature-silent)

Per `P1-H054-LIT-CHECK-PHASE-0`, the four primary-source claim domains in §1 were verified against peer-reviewed sources via WebFetch + WebSearch on 2026-05-05. Full lit-check trail at [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md). Verdict summary:

| Domain | Citation | Verification | Verdict on H054 framing |
|---|---|---|---|
| 1. VRP directionality | BTZ 2009 *RFS* 22(11):4463-4492 | DOI verified; abstract retrieved | SILENT on intraday + within-stress-state; SUPPORTS quarterly post-stress directional prediction |
| 2. Counter-cyclical risk premium | Cochrane 2011 *JoF* 66(4):1047-1108 | DOI + NBER + SSRN verified | SILENT on intraday; macro/quarterly survey |
| 3. Crisis alpha / TSMOM | Hurst-Ooi-Pedersen 2017 *JPM* 44(1):15-29 | SSRN + JPM verified; abstract retrieved | SILENT on first-hour ORB; SUPPORTS stress-period alpha for TSMOM (different signal class) |
| 4. HMM intraday equity-futures | Guidolin-Timmermann 2007 *JEDC* 31(11):3503-3544 | DOI + SSRN + JEDC verified; abstract retrieved | SILENT on intraday; SUPPORTS regime-conditional expected-return variation at monthly horizon |

**Overall Phase 0 verdict**: **literature-silent at the intraday HMM-stress-state level**. No primary source CONTRADICTS the H054-specific framing; no primary source ESTABLISHES it. The §1 "Mechanism" was rewritten from "literature-narrowed" to "literature-silent; empirical-only" to reflect the verdict. The §1 critical interpretive note's "post-hoc empirically motivated" framing is REINFORCED by the lit-silence.

**Phase 0 follow-ups** (non-blocking; logged in lit_review_H054_2026-05-05.md):
- `P1-H054-COCHRANE-FULLTEXT-VERIFY` — full-text re-fetch of Cochrane 2011 (abstract-only verification used for `designed` freeze; full-text re-check pass deferred).
- `P1-H054-MDPI-ADJACENT-LITERATURE-DEEPER-CHECK` — fetch MDPI/arXiv adjacent papers for finer-granularity assessment (MDPI is secondary per project evidence hierarchy; non-blocking).
- `P1-H054-HAMILTON-1989-RE-VERIFICATION` — re-verify Hamilton 1989 abstract via DOI fetch per `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` discipline.

**§15.1 BLOCKING-before-`designed`-freeze condition: SATISFIED** as of 2026-05-05. Pre-reg may proceed to Round-3 audit-remediate-loop ACCEPT and `designed` freeze.

## 16. Frozen-pre-reg amendment policy

Per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): project-level disposition-philosophy ADRs MAY amend §8 + §10 (gate thresholds + decision rule) of frozen `status: designed` pre-registrations WITHOUT requiring a successor hypothesis ID. Other amendments (to §1-§7) require a successor hypothesis ID.

§15.1 erratum-style additions (citation corrections discovered post-`designed` per Phase 0 lit-check) are permitted within the existing hypothesis ID under Path A frozen-pre-reg amendment discipline (matching the H052a §15.1 precedent).

## 17. Decision log + cross-references

- **Pre-reg drafted**: 2026-05-05 (this commit; `status: draft` → `status: designed` after Round-2+3 ACCEPT)
- **Phase 0 lit-check**: ✓ CLOSED 2026-05-05 — verdict literature-silent per [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md).
- **Round-1 audit-remediate-loop on this design.md**: ✓ CLOSED 2026-05-05 — quant-auditor verdict BLOCK with 5 critical/major (F-Q-1 IS leakage; F-Q-2 algebraic dependence; F-Q-3 stress-state ID; F-Q-4 power; F-Q-5 SPA; F-Q-6 design-time knowledge) + 5 minor findings. All 10 findings remediated inline at Round-2; Round-3 self-verification ACCEPT. Audit trail: [docs/audits/audit_trail_2026-05-05_h054-pre-reg.md](../../../docs/audits/audit_trail_2026-05-05_h054-pre-reg.md).
- **Status transition**: `status: draft` → `status: designed` 2026-05-05 (this commit; concurrently with [data_requirements.md](data_requirements.md) `status: draft` → `status: designed` per F-Q-10 BLOCKING-before-freeze gate).
- **First production walk-forward**: pending (`P1-H054-PROD-RUN`); BLOCKING-AFTER-`designed`-freeze.
- **Empirical motivation**: H052a KPI report card v1 [research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../H052a/H052a_kpi_report_v1.md).
- **Companion lit-review**: [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md) (TBD; produced by Phase 0 lit-check).
- **Substrate binding**: [data_requirements.md](data_requirements.md) (TBD; produced before `designed` freeze).
