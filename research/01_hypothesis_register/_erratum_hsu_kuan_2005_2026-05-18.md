---
type: erratum
scope: project-wide
date: 2026-05-18
affected_files:
  - research/01_hypothesis_register/H062/design.md (§1.4)
  - research/01_hypothesis_register/H062/lit_review_H062_2026-05-14.md
  - research/01_hypothesis_register/H062/H062_kpi_report_v1.md (§K-1.4 framing)
  - research/01_hypothesis_register/H065/design.md (§1.4)
  - research/01_hypothesis_register/H065/lit_review_H065_2026-05-15.md
  - research/01_hypothesis_register/H065/H065_kpi_report_v1.md (§K-1.4 framing)
  - CLAUDE.md Phase O.1 / O.6 / O.7 ledger entries (Hsu-Kuan 2005 framing references)
correction_class: misquoted-primary-source-finding
discovery: literature-check agent in post-merge audit-remediate-loop Round 1 (2026-05-18)
audit_trail: docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md
non_loss_disposition: erratum preserved; original framing in §1.4 of frozen design.md files retained verbatim per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline. The corrected framing supersedes the original for any future inferential or universe-choice reasoning.
---

# Erratum — Hsu-Kuan 2005 finding inversion across H062/H065/CLAUDE.md ledger

## Original (incorrect) framing

Variant A — H062 design.md §1.4 + lit-review (verbatim from frozen v1):

> Hsu-Kuan 2005 (DOI 10.1093/jjfinec/nbi026) — Channel breakouts survive only on small-cap (Russell 2000) under SPA correction; **FAIL on large-cap (Nasdaq Composite)**. **H062's universe is large-cap equity-index + metals, aligned with the harder-to-beat regime.**

Variant B — H065 design.md §1.4 + lit-review:

> Per Hsu-Kuan 2005 the channel-breakout family **fails SPA correction on large-cap NASDAQ** but survives on small-cap Russell 2000. The H065 ES/NQ subset of the H062 universe inherits the large-cap regime exposure.

Variant C — CLAUDE.md Phase O.1 / O.6 / O.7 ledger entries (similar inversion).

## Verified primary-source finding

Hsu, Po-Hsuan and Chung-Ming Kuan (2005). "Reexamining the Profitability of Technical Analysis with Data Snooping Checks." *Journal of Financial Econometrics* 3(4):606-628 ([DOI 10.1093/jjfinec/nbi026](https://doi.org/10.1093/jjfinec/nbi026)).

**Verified abstract text** (per academic.oup.com + IDEAS-RePEc + SSRN preprint metadata cross-references):

> "[…] significantly profitable simple rules and complex trading strategies do exist in the data from relatively young markets (NASDAQ Composite **AND** Russell 2000) but not in the data from relatively mature markets (DJIA and S&P 500)."

The distinction is **market maturity** (young vs mature), NOT **market capitalization** (large-cap vs small-cap). NASDAQ Composite — the closest published-paper analog to the SKIE-Universe NQ (Nasdaq-100, a large-cap subset of the NASDAQ market) — is in the **SURVIVES-SPA category**, not the FAILS-SPA category. Russell 2000 (small-cap) is **also** in the SURVIVES-SPA category, alongside NASDAQ Composite. The DJIA and S&P 500 (large-cap mature markets) are in the FAILS-SPA category.

## Implication for H062 universe-choice rationale

The original §1.4 framing concluded that H062's universe (ES = S&P 500 e-mini futures + NQ = Nasdaq-100 e-mini futures + MGC = Micro Gold + SIL = Micro Silver) is "aligned with the harder-to-beat regime." This is **empirically backwards**:
- ES (S&P 500) **is** in Hsu-Kuan's FAILS-SPA category (mature market). The framing is partially correct for ES.
- NQ (Nasdaq-100) tracks NASDAQ Composite which is in the **SURVIVES-SPA category** (young market). The framing inverts the empirical anchor for NQ.
- MGC + SIL are commodities futures, outside Hsu-Kuan's equity-index universe entirely. Hsu-Kuan 2005 supplies NO direct evidence on commodity futures profitability under SPA. The closest peer-reviewed anchor for metals/commodities channel-breakout decay is [Marshall-Cahan-Cahan 2008 *JBF* 32(9):1810-1819 DOI 10.1016/j.jbankfin.2007.12.011](https://doi.org/10.1016/j.jbankfin.2007.12.011) (7846 trading rules on commodity futures 1984-2005; NO rule generates statistically significant profits after Romano-Wolf 2005 stepwise FWER correction) which DOES point in the harder-to-beat direction for commodities.

## Corrected framing (project-canonical going forward)

Replace any reference to "channel breakouts fail on large-cap Nasdaq per Hsu-Kuan 2005" with the verified anchor:

> Hsu-Kuan 2005 (DOI 10.1093/jjfinec/nbi026) finds profitable simple rules and complex strategies survive SPA correction in **young markets** (NASDAQ Composite + Russell 2000) but **not in mature markets** (DJIA + S&P 500). For the H062/H065 universe, this implies:
> - **ES (S&P 500 e-mini)**: Hsu-Kuan FAILS-SPA mature-market regime; consistent with expected decay.
> - **NQ (Nasdaq-100 e-mini)**: closest Hsu-Kuan analog is NASDAQ Composite which is in the SURVIVES-SPA young-market regime; modest positive prior-art expectation for NQ channel-breakout profitability.
> - **MGC + SIL (Micro Gold + Micro Silver)**: outside Hsu-Kuan's equity universe. Direct primary anchor is [Marshall-Cahan-Cahan 2008 *JBF* 32(9):1810-1819 DOI 10.1016/j.jbankfin.2007.12.011](https://doi.org/10.1016/j.jbankfin.2007.12.011) on commodity futures (no rule survives RW2005 SPA-equivalent FWER correction); harder-to-beat prior-art expectation.

Net implication for H_1 framing: the partial-decay caveat **stands** (multiple peer-reviewed anchors document material decay in the channel-breakout family post-publication), but the **universe-choice rationale** flips per-instrument:
- ES + commodities: consistent with the original "aligned with harder-to-beat regime" expectation.
- **NQ specifically**: original framing was empirically backwards. NQ tracks the **SURVIVES-SPA category** in Hsu-Kuan 2005; the prior-art expectation for NQ is **modestly positive** for channel-breakout profitability, not "harder-to-beat."

The H062/H065 v1 KPI emissions are not affected by this correction in their numerical claims (the inferential CIs hold per the underlying data). The correction reframes the *interpretation* of post-hoc OOS findings on NQ specifically: a positive NQ realized OOS on H062/H065 is consistent with the SURVIVES-SPA prior-art expectation, NOT a surprising-success finding under the original (inverted) framing.

## Audit-discipline lesson

This is the **third** documented instance of the `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` regression class (paper-says-X-but-cite-says-Y misattribution at the literature-anchor level). Prior instances:
- Phase J: Breiman 1996 cited as *Annals of Statistics* DOI 10.1214/aos/1032181158 ("Stacked Regressions"); actual DOI resolves to "Heuristics of instability and stabilization"; correct cite is *Machine Learning* 24:49-64 DOI 10.1007/BF00117832.
- Phase J: Easley-López de Prado-O'Hara 2012 cited as *RFS* for volume-clock construction; RFS paper is VPIN ("Flow Toxicity"); volume-clock is the separate *JPM* Fall 2012 paper.
- Phase O.2-O.9 (this erratum): Hsu-Kuan 2005 finding inversion.

The pattern: secondary-source paraphrases of primary-paper findings get re-paraphrased in design.md / lit-review / CLAUDE.md ledger entries, and the directional / categorical content of the original finding gets flipped or mis-categorized. Recommend the `literature-check` audit agent be extended to **verify the direction / categorical content** of primary-source findings, not just resolve DOIs.

New non-blocking follow-up: `P1-LITERATURE-CHECK-DIRECTIONAL-FINDING-VERIFY` — extend literature-check agent scope to assert paper-finding-direction matches cite-claim-direction (e.g., "fails on X" vs "succeeds on X"; "young vs mature" vs "small-cap vs large-cap").

## Cross-references

Each affected file carries either an inline cross-link to this erratum (lit-reviews; edited in place) or a §17 revision-log entry pointing here (design.md; §1.4 frozen per ADR-0013 §1-§7 immutability discipline). The original §1.4 framing in H062/H065 design.md is preserved verbatim; this erratum is the canonical correction-of-record.

The two affected v1 KPI report cards (H062_kpi_report_v1.md, H065_kpi_report_v1.md) embed the inverted framing in their bottom-line interpretive narrative. Per ADR-0013 §4.1 non-loss, the v1 cards are preserved verbatim; this erratum supplies the corrected interpretive framing for downstream readers + future v2+ KPI emissions.

CLAUDE.md Phase O.1 / O.6 / O.7 ledger entries are preserved verbatim per the append-only ledger discipline; a forward Phase O.10 ledger entry (this audit-remediate-loop session) supplies the corrected framing.
