---
template_name: phase_performance_report
template_version: 1.0
authoritative_per: docs/decisions/ADR-0014-never-archive-profitable-strategies.md §9
canonical_computation: scripts/analyze_h053_v3_arm2_performance.py
template_required_when: any phase produces trading returns (a Cycle completion, a production run, a diagnostic informing operator decision, a remediation loop)
---

# Phase performance report — TEMPLATE

> **PURPOSE**: per ADR-0014 §9, every phase that produces strategy returns MUST emit this report at phase-end. Disposition-class labels alone (e.g., "calibration-failed; paper_trade_eligible=False") are INSUFFICIENT — operator needs the strategy-performance numbers below to make promotion decisions.

> **USAGE**: copy this file into the phase's report directory (e.g., `reports/h0XX/<phase>_performance.md`) and fill in the blanks. The canonical computation script `scripts/analyze_h053_v3_arm2_performance.py` produces a JSON output with all the required fields; copy values from that JSON.

---

## Phase identifier

- **Hypothesis**: `H0XX`
- **Phase**: `<Cycle N | Stage X | Diagnostic | Remediation Round>`
- **Run id**: `<runs/h0XX/.../<run_id>>`
- **Sidecar SHA-256**: `<scientific_payload_sha256>`
- **Substrate dataset checksum**: `<bc06b...>`
- **Git HEAD**: `<commit-sha>`
- **Wall-clock**: `<HH:MM duration>`
- **Date**: `YYYY-MM-DD`

## Disposition (technical state per ADR-0012)

- **disposition_class**: `<paper-trade-eligible | leakage-detected | reproducibility-incomplete | calibration-failed | prerequisite-not-met | archive(complete) | archive(null, <reason>)>`
- **paper_trade_eligible (auto)**: `<True | False>`
- **lifecycle_state per ADR-0014**: `<paper-trade-eligible | active-investigation | archived>`
- **lifecycle_state reason**: `<...>`

> **NOTE per ADR-0014 §1**: `disposition_class` is a STATE label per ADR-0012. The ONLY archive labels are `archive(complete)` and `archive(null, <reason>)`. Other disposition_class values are remediation-pending states, NOT archive decisions. Per ADR-0014 §8, `lifecycle_state = archived` is set ONLY by explicit operator decision (`compose_disposition(explicit_archive=True)`); Claude SHALL NOT pass that argument autonomously.

## Strategy performance (REQUIRED per ADR-0014 §9)

### Per-arm × per-symbol metrics

For each `(symbol, arm)` cell that produces trading returns, fill in this block:

| Metric | Value | Notes |
|---|---:|---|
| Test window | `YYYY-MM-DD to YYYY-MM-DD` | n=`<sessions>` |
| **Total log return** | `+/- XX.X bps` | over OOS span |
| **Annualized return** | `+/- X.XX%` | × 252 sessions/yr |
| **Annualized vol** | `X.XX%` | × √252 |
| **Annualized Sharpe** | `+/- X.XX` (CI [`<lower>`, `<upper>`]) | Lo 2002 §III HAC + Opdyke 2007 / LW2008 bootstrap, B=2000 |
| **Sortino (annualized)** | `+/- X.XX` | downside-only vol |
| **Calmar (annualized return / max DD)** | `+/- X.XX` | |
| **Max drawdown** | `-X.X bps (-X.X%)` | peak `<date>` → trough `<date>` → recover `<date or NOT_RECOVERED>` |
| **DD duration** | `<N sessions>` | + `<M total underwater>` |
| **Win rate** | `XX.X%` (`<n_wins>`/`<n_sessions>`) | |
| **Avg win / avg loss** | `+XX.X / -XX.X bps` | |
| **Profit factor** | `X.XX` | abs(sum(wins) / sum(losses)) |
| **Max consecutive wins / losses** | `<W>` / `<L>` | |
| **Hansen SPA p-value** (multiple-testing-corrected) | `0.XXXX` (`spa-passes` / `spa-rejects`) | omega-corrected per ADR-0008 |
| **LW2008 ΔSharpe vs passive** | `+/- X.XXXX` (CI [`<lower>`, `<upper>`]; excludes_zero=`<bool>`) | studentized circular-block bootstrap |
| **Cost-c (1-tick)** | `X.XXXX bps/RT` | from instruments.yaml + nt8_es_nq_rth_v1 |
| **Net mean per session (1-tick)** | `+/- X.XX bps` | gross - cost |
| **Net annualized return (1-tick)** | `+/- X.XX%` | |
| **Net annualized Sharpe (1-tick)** | `+/- X.XX` | |
| **2-tick sensitivity Sharpe** | `+/- X.XX` | for cost-floor robustness check |

### Per-year breakdown (REQUIRED if test span > 1 year)

| Year | n_sessions | Win rate | Annualized return | Mean (bps) | Std (bps) | Annualized Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| `YYYY` | | | | | | |

### Per-month breakdown (OPTIONAL but RECOMMENDED for drawdown investigation)

Truncate or expand as needed; include any month with notable performance shifts (drawdowns > 100 bps; win rate < 40%; consecutive-loss streaks ≥ 4).

## Class A binding-gate verdicts (per ADR-0012)

| Symbol | Arm | PIT canary | Repro log | BSS lower CI | Reliability slope CI covers 1.0 | DSR (when applicable) |
|---|---|---|---|---:|---|---|
| `<sym>` | `<arm>` | PASS/FAIL (n_tests=`<n>`) | PASS/FAIL | `<value>` (PASS/FAIL) | `[<lower>, <upper>]` (PASS/FAIL) | `<value>` |

## Class B KPI report card (per ADR-0012)

(KPIs that are non-binding but inform operator decision; sub-set of the strategy-performance metrics above plus any hypothesis-specific KPIs.)

## Operator decision matrix (per ADR-0014)

Given the lifecycle_state above:

- **If lifecycle_state = paper-trade-eligible**: auto-promotion criteria met; recommend operator promote to paper-trade per ADR-0011 governance.
- **If lifecycle_state = active-investigation AND strategy is profitable per ADR-0014 §2**: recommend operator promote to paper-trade with WRITTEN GATE-BYPASS JUSTIFICATION noting the failed Class A gate(s) and the operational interpretation. Do NOT archive.
- **If lifecycle_state = active-investigation AND strategy is NOT profitable**: recommend operator review the remediation paths and decide whether to (a) re-run with amended methodology, (b) launch a successor hypothesis with §1-§7 estimator change, (c) promote anyway with extra paper-trade scrutiny, OR (d) explicitly archive (operator only; pass `explicit_archive=True`).
- **If lifecycle_state = archived**: operator has explicitly closed the hypothesis; record the date + reason in CLAUDE.md.

> **Per ADR-0014 §8 NEVER ARCHIVE AUTONOMOUSLY**: Claude SHALL NOT recommend archive; surface the question to the operator with full evidence and let the operator decide.

## Follow-ups registered

| Tag | Severity | Description |
|---|---|---|
| `P1-...` | (blocking / non-blocking) | (one-line description) |

## Provenance

- **Sidecar JSON**: `<runs/h0XX/.../sidecar.json>`
- **Performance dashboard JSON**: `<runs/h0XX/diagnostics/<phase>_performance.json>` (output of `scripts/analyze_h053_v3_arm2_performance.py`-equivalent for this hypothesis)
- **Audit trail**: `<docs/audits/audit_trail_YYYY-MM-DD_h0XX-<phase>.md>`
- **Disposition memo**: `<reports/h0XX/<phase>_disposition.md>`
