---
name: Remediation round 1 — literature-check
description: Action log for the round-1 literature-check audit against [lit_intraday-ES-NQ-signals_2026-04-15.md](C:\Users\skoir\SKIE-Ninja-Intraday\research\00_literature_review\lit_intraday-ES-NQ-signals_2026-04-15.md)
type: project
status: closed-round-1
date: 2026-04-15
round: 1
remediator: remediation agent (claude-opus-4-6-1m)
verdict_input: BLOCK
verdict_output: PARTIAL — see section "Residual risk"
---

# Remediation Round 1 — Literature Review

Audit source: [audit-round1-literature_2026-04-15.md](C:\Users\skoir\SKIE-Ninja-Intraday\research\03_audits\audit-round1-literature_2026-04-15.md).

## Verification stats

- **Total citations in lit review:** ~80 (grounding sections 2-3 + methodology section 4).
- **Citations re-derived against publisher landing pages this round:** 24 (targeted at every audit-flagged entry + the auditor-supplied known-good anchors + plausibly-risky SSRN / WP IDs).
- **Citations verified clean (publisher metadata matches):** 24. Enumerated in section 6.2 of the lit review.
- **Citations removed as fabricated or resolving to a different paper:** 4
  1. Barbon et al. RFS 2024 `10.1093/rfs/hhae001` — resolved to a social-media / congressional-viewpoints paper. Substituted with SSRN 3925725.
  2. Brogaard-Han-Won RAPS `10.1093/rapstu/raae002` — resolved to Kubitza-Pelizzon-Sherman CCP loss-sharing. Substituted with SSRN 4426358.
  3. Huang-Polak iceberg QF 2023 `10.1080/14697688.2023.2218472` — DOI 404. Substituted with Zotikov 2021 QF `10.1080/14697688.2020.1813904`.
  4. Frey-Sanmartin JFM 2024 `10.1016/j.finmar.2024.100911` — author pair does not match any paper; real author is Sandås (2008 CFS WP / SSRN 1343538). Substituted.
- **Citations with wrong ID / wrong venue substituted:** 8
  1. Bandi-Fusari-Renò: SSRN 4361595 → SSRN 4503344; venue JFE → JoF forthcoming.
  2. Beckmeyer-Branger-Gayda: SSRN 4588661 → SSRN 4404704.
  3. Hu-Murphy: SSRN 4559305 → SSRN 4070056.
  4. Afonso et al.: SSRN 3778488 → SSRN 3915127 (FRBNY Staff Report 918).
  5. Bybee-Kelly-Manela-Xiu: DOI `jofi.13321` → `jofi.13377`.
  6. Dobrev-Schaumburg: IFDP 2017-1210 [P] → 2018 Atlanta Fed workshop [WP].
  7. Bouchaud et al. *Trades, Quotes, Prices*: [WP] → [TEXTBOOK]; removed from H003 Kalshi grounding.
  8. Ledoit-Wolf 2024: "JEF forthcoming" stripped → [WP] SSRN 4461030.
- **Venue / status claims stripped without substitution (unconfirmed forthcoming):** 3
  - Lopez-Lira-Tang "JoF forthcoming" → [PP] only.
  - Evans et al. "2024 forthcoming RFS" → [WP] only.
  - Copeland-Duffie-Yang "QJE forthcoming" → NBER WP only.
- **Paraphrased numerical claims tagged [PARAPHRASE]:** 3
  - H010 "0.56-0.58 AUC at 1-5 min" — dropped pending direct table check against Kolm-Turiel-Westray 2023.
  - H011 Hawkes near-iid resampling claim — tagged pending table check against Morariu-Patrichi-Pakkanen 2022.
  - H014 MOC → ES "3-5 second front-run" — tagged; not directly quantified in Bogousslavsky-Muravyev.

## Hypotheses now weakly grounded

Recommend backlog action on three IDs:

- **H030 (iceberg detection and hidden-liquidity inference):** downgrade HIGH → MED. Deep-learning framing lost with Huang-Polak removal; survives only as a survival-modeling / hidden-liquidity hypothesis.
- **H003 (Kalshi prediction-market leakage):** recommend move to `archived(null)`. Remaining grounding is Wolfers-Zitzewitz 2004/2013 priors only; no Kalshi-specific peer-reviewed empirics.
- **H044 (weekly option OI pin migration):** recommend move to `archived(null)` pending a 2024-26 peer-reviewed 0DTE pinning paper. Current anchors (Barraclough-Whaley, Ernst-Spatt OFR brief) do not support the weekly-OI-migration mechanism.

## Residual risk

Roughly 55 citations were left `[UNVERIFIED — not re-fetched this round]`. These are classical or widely-indexed entries (Newey-West, Andrews, Lo, Opdyke, Ledoit-Wolf, Gao-Han-Li-Zhou, Moreira-Muir, Garleanu-Pedersen-Poteshman, Andersen-Bollerslev-Diebold-Labys, etc.) and were not flagged by the round-1 auditor. They must be spot-checked in a round-2 pass before any of them drives a hypothesis into Phase 4 empirical work. The hallucination pattern observed in the original draft means round-1 clearance does not generalize to entries the auditor did not specifically test.

## Recommendation to parent

Proceed to round-2 audit (spot-check the 55 unverified classical cites; budget: ~1 hour). Do not promote H030 / H003 / H044 into Phase 4 until backlog reflects the tier-downgrade actions above.
