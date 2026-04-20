---
name: Audit round 1 — literature-check findings
description: Citation verification against primary sources for the intraday ES/NQ lit review
type: project
status: open
date: 2026-04-15
round: 1
auditor: literature-check (subagent)
verdict: block
---

# Audit Round 1 — Literature-Check Findings

**Verdict: BLOCK.** At least four citations (L-1, L-2, L-3, L-4) are critical — DOIs resolve to entirely different papers or do not resolve at all. Pattern consistent with LLM-generated citation hallucination. Lit review must be re-derived from primary publisher landing pages before it grounds any hypothesis.

Citations checked: 18.

## CRITICAL — fabricated / misattributed DOIs

| ID | Location (:line) | Stated | Actual / fix |
|---|---|---|---|
| L-1 | lit:36 | Barbon-Beckmeyer-Buraschi-Moerke, RFS 2024, `10.1093/rfs/hhae001` | DOI resolves to a different paper (Congressional viewpoints / social media). Correct paper is a working paper: [SSRN 3925725](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3925725). Re-tag `[WP]`; remove fabricated DOI. |
| L-2 | lit:102 | Brogaard-Han-Won, RAPS 14 2024, `10.1093/rapstu/raae002` | DOI resolves to Kubitza-Pelizzon-Sherman on CCP loss-sharing. Correct Brogaard-Han-Won 0DTE paper: [SSRN 4426358](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4426358). Re-tag `[WP]`. |
| L-3 | lit:152 | Huang-Polak, QF 2023, `10.1080/14697688.2023.2218472` | DOI 404. Likely fabricated. Remove or replace with verified iceberg-detection paper. |
| L-4 | lit:153 | Frey-Sanmartin, JFM 70 2024, `10.1016/j.finmar.2024.100911` | Unresolvable. Likely fabricated. Remove until a real DOI is confirmed. |

## MAJOR — misquoted IDs/venues

| ID | Location (:line) | Issue | Fix |
|---|---|---|---|
| L-5 | lit:101 | Bandi-Fusari-Renò 0DTE: wrong SSRN ID and wrong journal | Replace with [SSRN 4503344](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4503344); venue is *Journal of Finance* forthcoming, not JFE |
| L-6 | lit:222 | Bybee-Kelly-Manela-Xiu: DOI wrong | Replace with `10.1111/jofi.13377` ([link](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13377)) |
| L-8 | lit:160 | Dobrev-Schaumburg: mismatched title / unverifiable IFDP number | Downgrade to `[WP]`, use verified working-paper title |
| L-9 | lit:69 | Hu-Murphy: SSRN 4559305 does not resolve to stated title/authors | Replace with verified ID or remove |
| L-10 | lit:101 | Bandi-Fusari-Renò venue: JFE → JoF forthcoming | Same fix as L-5 |

## MINOR

| ID | Location | Fix |
|---|---|---|
| L-7 | lit:115 | Lopez-Lira-Tang: keep `[PP]`; do not assert "JoF forthcoming" without publisher-side confirmation |
| L-11 | lit:92 | Bouchaud et al. *Trades Quotes and Prices* (CUP 2018) — textbook, not `[WP]`; cite specific chapters; Kalshi "relevance" is editorial, not a finding |
| L-12 | lit:38 | Baltussen-Terstegge-Whelan acceptably `[WP]`; must not drive parameter calibration |
| L-13 | lit:47 | Kolm 2023 paraphrase "0.56-0.58 AUC at 1-5 min" needs direct table cite or drop numeric range |

## Verified real sources (for the remediation agent to use as anchor set)

- [Barbon et al. SSRN 3925725](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3925725)
- [Kubitza et al. RAPS raae002](https://academic.oup.com/raps/article/14/2/237/7588884) (was misattributed to L-2)
- [Bybee et al. JoF 13377](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13377)
- [Bandi et al. SSRN 4503344](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4503344)
- [Kolm-Turiel-Westray Math Finance 12413](https://onlinelibrary.wiley.com/doi/abs/10.1111/mafi.12413)
- [Brogaard-Han-Won SSRN 4426358](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4426358)

## Remediation directive

The lit review cannot be trusted piecemeal — the hallucination pattern suggests many more cites may be unverified even if superficially plausible. The remediator must re-derive **every** DOI/SSRN ID by loading the publisher landing page (WebFetch) and confirming title + authors + year + venue before reinstating it. Any citation that cannot be confirmed within a reasonable effort budget must be removed or downgraded to `[UNVERIFIED]` — not allowed to drive a hypothesis into Phase 4.
