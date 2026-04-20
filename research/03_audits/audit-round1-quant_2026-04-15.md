---
name: Audit round 1 — quant-auditor findings
description: Independent statistical audit of plan/implementation-plan_2026-04-15.md and related
type: project
status: open
date: 2026-04-15
round: 1
auditor: quant-auditor (subagent)
---

# Audit Round 1 — Quant-Auditor Findings

Verdict: **proceed-with-remediation**. CRITICAL items must land in `GateReport` before any hypothesis reaches Phase 4.

## CRITICAL

1. **FDR supplement missing for 50+ backlog.** SPA controls FWER; power decays with universe size. Add Benjamini-Hochberg q-values ([Benjamini-Hochberg 1995 JRSS-B](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)), Storey q-values under dependence ([Storey 2002](https://doi.org/10.1111/1467-9868.00346)), and Romano-Wolf stepwise ([Romano-Wolf 2005, Econometrica](https://doi.org/10.1111/j.1468-0262.2005.00615.x)). Extend `GateReport` with `romano_wolf_pvalue`, `bh_qvalue`, `storey_qvalue`.
2. **Power analysis absent.** No minimum-sample sizing for intraday Sharpe≈1 at α=0.05, 80% power, realistic AR(1) ρ∈[0.05, 0.15] and excess kurtosis. Naïve iid formula understates required N by factor (1+2ρ/(1-ρ)). Add pre-registered power calc per hypothesis config; gate refuses underpowered designs.
3. **Deflated Sharpe Ratio not computed.** With exhaustive search, raw Sharpe CI overstates. DSR/PSR per [Bailey-Lopez de Prado 2014 JPM 40:94](https://doi.org/10.3905/jpm.2014.40.5.094) is the correct post-selection quantity. Add to `GateReport`.

## HIGH (Phase 1)

4. **Embargo 1% and purge = label horizon are arbitrary.** Violates no-magic-numbers rule. Replace with data-driven embargo from residual-return PACF decay or optimal block length ([Politis-White 2004](https://doi.org/10.1081/ETC-120028836)).
5. **Cost-model split is single-shot, not walk-forward.** §6.3 "fit first 60%, test last 40%" contradicts project rule. Use expanding-window walk-forward for slippage recalibration.
6. **Full-sample normalization path not closed.** Feature contract §3 guarantees PIT at compute, but scalers/encoders can still fit on full panel before splitter. Add injection test: feature whose mean depends on future data must fail pipeline+splitter.
7. **SPA universe-snapshot logic statistically weak.** SPA requires common OOS across candidates. Sequential appending with heterogeneous OOS violates null construction. Either (a) re-run all historical strategies on common OOS when adding, or (b) prefer Romano-Wolf stepwise. Document the choice in ADR.
8. **Lo-2002 redundant for intraday.** Intraday ES shows ρ₁ ≈ -0.03 to -0.08 (bid-ask bounce), kurtosis ≫ 3. Lo assumes stationary iid-ish with finite 4th moment. Keep Opdyke 2007 as primary, Lo diagnostic-only. Consider HAC-adjusted Opdyke or studentized circular-block bootstrap as primary.
9. **Almgren-Chriss/Tóth √-impact overspecified at retail size.** 20 ES vs 1.5M ADV → qty/ADV ≈ 1.3e-5; √ term numerically indistinguishable from zero. Identification problem. Replace with linear-in-spread + latency-conditional slippage; retain √ prior only as regularized Bayesian mean.

## MEDIUM

10. `GateReport` missing: MaxDD CI ([Burghardt-Duncan-Liu 2003]), Ulcer Index, turnover SE, Calmar, PSR.
11. Magic numbers to justify empirically: 20 ES / 40 NQ caps, 5× latency anomaly, 2000 ms RTH staleness, KS p<1e-6, 3× bridge-fail, quarterly recalibration.
12. Bootstrap reps = 10_000 — cite MC SE target (SE≈√(p(1-p)/B)).
13. CPCV `n_groups=6, n_test_groups=2` hard-coded — parameterize and log selection rationale (AFML §12).
14. Triple-barrier `pt_sl`, vertical barrier, vol estimator all need pre-registration per hypothesis.
15. CME exchange fees tier with volume — document even if immaterial at retail.
16. MBP-10 / depth schema missing in §2.1 — H010 deep-OFI cannot run without it.

## LOW

17. Verify Opdyke 2007 DOI resolves; cross-check formula against [Mertens 2002] correction.
18. `StrategyUniverse` append-only parquet needs signed hash / write-once ACL.
19. Add *leaked-feature canary* (future return as feature) alongside §4.4 shuffled-label canary.
20. SPA null-uniformity test: increase n to ≥10_000 or use Anderson-Darling.
21. Adopt [Harvey-Liu-Zhu 2016 RFS](https://doi.org/10.1093/rfs/hhv059) haircut framework for final Sharpe reporting.
22. ADR-0002 latency study: push to ≥10k messages per option for robust p99.
