# Audit-remediate-loop trail — 2026-Q1-Q2 sub-window simulators

**Date**: 2026-05-16
**Deliverables under audit**:
- [scripts/run_h060_2026_q1q2.py](../../scripts/run_h060_2026_q1q2.py) — new daily-cadence TSMOM 2026 sub-window simulator
- [scripts/run_h062_v1_2026_q1q2.py](../../scripts/run_h062_v1_2026_q1q2.py) — H062 v1 baseline (km=0.25) 2026 sub-window simulator wrapping production `_run_per_trade_simulation`
- [scripts/tabulate_2026_results.py](../../scripts/tabulate_2026_results.py) — pure-tabulation reader for existing sweep sidecars

**Scope**: per the [audit-remediate-loop skill](../../../.claude/skills/audit-remediate-loop), single-round audit applied to sub-window diagnostic simulators landing on the Phase O.8 expanded substrate. Verdict on cap: `accept-with-residuals` after R1 remediation.

## Round 1

### Auditors invoked (parallel)
- **quant-auditor** (agentId `a33e22603262a9e52`) — verdict `block`; 2 critical + 5 major + 2 minor
- **reproducibility-verifier** (agentId `ab44445583e67d6ef`) — verdict `proceed-with-remediation`; 3 critical + 3 major + 1 minor

### Findings + dispositions

| ID | Severity | Source | Location | Issue | Disposition |
|---|---|---|---|---|---|
| F-1-1 | critical | quant | run_h060_2026_q1q2.py:93 | TSMOM ≡ passive degenerate: passive arm scaled with same vol_target × kelly so headline "TSMOM==passive" uninterpretable | **Remediated**: added `passive_raw_bh` arm (canonical MOP 2012 §3.2 unscaled BH); kept `passive_vol_scaled` for documented degeneracy comparison; sidecar `signal_n_pos_subwin / signal_n_neg_subwin` distribution diagnostic exposes the all-long-signal cause |
| F-1-2 | critical | quant | run_h060_2026_q1q2.py:80-94 | Docstring + code disagreed on time-indexing (t vs t+1 framing) | **Remediated**: rewrote docstring to explicitly describe the causal indexing applied in code (`position_{t-1} × log_ret_t` with `signal_{t-1}` and `vol_{t-1}`) |
| F-1-3 | major | quant | run_h060_2026_q1q2.py:71 | UTC-day groupby for daily-close conflicts with CME session-date for energy/metals 24/5 | **Acknowledged caveat**: sidecar `daily_close_convention: utc_day` + `daily_close_caveat` documents the approximation; full session-date refactor tracked as new follow-up `P1-H060-2026-SUBWIN-CME-SESSION-DATE` |
| F-1-4 | major | quant | both scripts | ADR-0017 §3 + ADR-0018 D-1 primary metric vector absent | **Remediated via explicit descoping**: sidecar `kpi_report_card: False`, `scope: subwindow_diagnostic`, `descoped_kpis: {reason: ..., authorized_by: 'operator 2026-05-16', refs: [...], missing: [...]}` |
| F-1-5 | major | quant | run_h062_v1_2026_q1q2.py:96-100,186 | NQ silently dropped from results array; basket cardinality mutated from 4 to 3 | **Remediated**: all 4 symbols emit a results row with `gated_out_reason` on empty-series path; basket always denominated against 4-symbol universe |
| F-1-6 | major | quant | both scripts | ReproLog 13-field schema absent | **Partial remediation**: sidecar `provenance` block includes git_head + substrate_dataset_checksum + producing_script_path + producing_script_sha256 + rng_seed (5 of 13 fields); full RunContext wrap deferred per `P1-2026-SUBWIN-REPROLOG-FULL-WRAP` |
| F-1-7 | minor | quant | run_h060_2026_q1q2.py:91 | `pd.ewm(adjust=False).std()` biased estimator | **Documented**: inline `# justify` comment notes < 1% bias by t > vol_com; non-blocking |
| F-1-8 | minor | quant | tabulate_2026_results.py:121 | Dict-key fallback chain unsafe against None values | **Remediated**: introduced `_safe_sub_roi` helper with explicit `is None` checks |
| R-1 | minor | repro | both sha256.txt | SHA matches sidecar | pass |
| R-2 | critical | repro | both sidecars | No substrate_dataset_checksum | **Remediated** via F-1-6 fix |
| R-3 | critical | repro | both sidecars | No rng_seed | **Remediated** via F-1-6 fix |
| R-4 | critical | repro | both sidecars | No git_head | **Remediated** via F-1-6 fix |
| R-5 | major | repro | both sidecars | ADR-0017 §3 fields missing | **Remediated** via F-1-4 explicit-descoping fix |
| R-6 | major | repro | H062 sidecar | NQ row absent; ES/SIL zero rows lack reason | **Remediated** via F-1-5 fix |
| R-7 | minor | repro | both sidecars | No producing_script_path / sha | **Remediated** via F-1-6 fix |

### Pre-remediation vs post-remediation behavior

| Diagnostic | Pre-remediation | Post-remediation |
|---|---|---|
| H060 ES TSMOM vs passive | "+2.17% vs passive +2.17%" (degenerate) | TSMOM +2.17% vs passive_vol_scaled +2.17% (degenerate-by-construction; documented) vs **passive_raw_bh +14.13%** (canonical) |
| H060 NQ TSMOM vs passive | "+2.74% vs passive +2.74%" | TSMOM +2.74% vs passive_raw_bh **+23.50%** — TSMOM captures ~12% of long-only return after vol-target × kelly de-levering |
| H062 v1 basket cardinality | 3-symbol avg = +2.68% (NQ silently dropped) | 4-symbol basket = +2.01%; NQ row present with `gated_out_reason` |
| Provenance | sidecar has no git_head, substrate SHA, rng_seed, script_sha | full 5-field provenance block on sidecar root |
| Scope flagging | implicit (researchers must infer) | explicit `kpi_report_card: false` + `scope: subwindow_diagnostic` + `descoped_kpis` block |

### Critical interpretive finding surfaced by F-1-1 remediation

**H060 TSMOM underperforms raw buy-and-hold by 10-21 percentage points on the 2026-04-01 → 2026-05-15 sub-window across 3 of 4 symbols** (ES, NQ, SIL). Signal was 100% long across the entire 6-week window on all 4 symbols (sig+/sig- = 38/0 ES NQ, 37/0 MGC SIL) — TSMOM and "passive long" represent the SAME directional bet. The vol_target=10% × kelly_multiplier=0.25 scaling **de-levered the long position** below 1.0× so TSMOM captured only a fraction of the long-only return. Original ledger framing "TSMOM ties passive" was true only against the scaled-passive arm; against canonical raw BH, TSMOM materially underperforms via vol-targeting drag.

This is a substantive operator-facing finding that the F-1-1 remediation surfaced.

## Exit verdict

**Round 1 verdict**: `accept-with-residuals`. All critical findings remediated. 2 major findings dispositioned with documented caveats + new follow-ups. Skill-cap residuals:

- `P1-H060-2026-SUBWIN-CME-SESSION-DATE` (carry from F-1-3): refactor daily-close resampling to CME session-date convention; non-blocking for sub-window diagnostic scope.
- `P1-2026-SUBWIN-REPROLOG-FULL-WRAP` (carry from F-1-6): wrap both scripts in `src/skie_ninja/utils/runcontext.py` `RunContext` so full 13-field ReproLog is emitted alongside sidecar; non-blocking — 5 of 13 fields already present in provenance block.
- `P1-H060-2026-SUBWIN-VOL-TARGET-EMPIRICAL-CALIBRATION` (new from F-1-1 interpretive finding): the headline-level vol-target=10% × km=0.25 produces ~3-4% effective exposure post-scaling — empirical anchoring of vol_target on the {ES, NQ, MGC, SIL} basket would resolve whether this de-levering is operationally desirable or an artifact.

## Re-run artifacts

- H060 post-remediation: [artifacts/runs/H060/v1_2026_q1q2_20260516T215115Z/sidecar.json](../../artifacts/runs/H060/v1_2026_q1q2_20260516T215115Z/sidecar.json) (sha256 `bc7383c3...`)
- H062 v1 post-remediation: [artifacts/runs/H062/v1_baseline_2026_q1q2_20260516T215119Z/sidecar.json](../../artifacts/runs/H062/v1_baseline_2026_q1q2_20260516T215119Z/sidecar.json) (sha256 `19390ea9...`)

Pre-remediation sidecars preserved per ADR-0013 §4.1 non-loss mandate:
- [artifacts/runs/H060/v1_2026_q1q2_20260516T214032Z/sidecar.json](../../artifacts/runs/H060/v1_2026_q1q2_20260516T214032Z/sidecar.json)
- [artifacts/runs/H062/v1_baseline_2026_q1q2_20260516T214139Z/sidecar.json](../../artifacts/runs/H062/v1_baseline_2026_q1q2_20260516T214139Z/sidecar.json)

## References

- [audit-remediate-loop skill](../../../.claude/skills/audit-remediate-loop/SKILL.md) — 3-round cap; this audit used 1 round.
- Moskowitz-Ooi-Pedersen 2012 *JFE* 104(2):228-250 [DOI 10.1016/j.jfineco.2011.11.003](https://doi.org/10.1016/j.jfineco.2011.11.003) — TSMOM benchmark anchor.
- ADR-0013 permanent-exploration §4.1 non-loss mandate.
- ADR-0017 survival-constrained paradigm §3 primary metric vector.
- ADR-0018 regime-conditional aggressive-growth D-1 MPPM(ρ=1) primary fitness.
- `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` — the audit-remediate-loop discipline that flagged the pre-remediation degeneracy as a substantive interpretive risk.
