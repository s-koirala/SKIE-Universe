---
type: memo
scope: project-wide
date: 2026-05-18
purpose: enumerate every substrate SHA in active use across SKIE-Universe KPI emissions; map each output_frame_sha256 → provenance JSON → consuming KPI report cards
closes: P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE (Phase O.1 follow-on follow-up)
audit_trail: docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md (Round 1 reproducibility-verifier finding R-3 — 4 distinct substrate SHAs in active use without reconciliation)
---

# Substrate-vintage inventory and KPI report card mapping

## Context

The 2026-05-18 post-merge audit-remediate-loop Round 1 reproducibility-verifier surfaced **4 distinct substrate SHAs** in active use across SKIE-Universe artifacts, with no project-level reconciliation. This memo enumerates each, maps it to its provenance JSON, lists consuming KPI report cards, and documents the canonical going-forward SHA.

## Inventory

| SHA (first 8 chars) | Full output_frame_sha256 | Provenance JSON | Ingest date | Consuming KPI cards |
|---|---|---|---|---|
| `1247dc7e` | `1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959` | [`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json`](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json), [`...20260515.json`](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260515.json) | 2026-05-12 / 2026-05-15 | H062 v1 (run_id `16cb68d997c148a2834aad21b73bfdb6`); H062 design.md §16 substrate binding |
| `b93e5448` | `b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce` | sibling worktree `.claude/worktrees/nervous-greider-90c8f0/data/processed/_provenance/...` (not committed to main checkout); referenced via embedded sidecar substrate root path | 2026-05-16 (post-Phase O.3 2026-H1 backfill) | H055 v1 (run_id `v2_sweep_20260516T025924Z`); H065 v1 (run_id `tp_overlay_sweep_20260516T030515Z`) |
| `317429e4` | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` | [`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260516.json`](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260516.json); **canonical re-ingest 2026-05-18 reproduced at** [`...20260518.json`](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`) | 2026-05-16 (post-Phase O.8 ES+NQ pre-2020 + NQ 2025 backfill) / 2026-05-18 (re-derived deterministically on main HEAD `a5766fd`) | H062 Phase O.9 sub-window simulators; **canonical substrate going forward on main HEAD** |
| `242aaa28` | `242aaa280b216f45edc3b9d9de9630f52f71206eea7832c1cb0470296190f46f` | **NO PROVENANCE JSON matches this SHA.** Referenced only in CLAUDE.md Phase O.0 ledger entries as a claim. No on-disk substrate matches this hash on main HEAD. | (claim only; not reproducible) | (no KPI cards bind to this SHA; ledger-only) |

## Canonical going-forward SHA

**`317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`** is the canonical substrate on main HEAD `a5766fd` as of 2026-05-18. It was re-derived by running `scripts/ingest.py --dataset vendor_legacy_1min` (run_id `8819c5dd44c34f4da41b9a24d992b9f4`) + `scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted` (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`) on 2026-05-18 from the raw 1-min Databento CSVs at `~/datasets/vendor_skie_ninja_legacy/raw_1min/`. The derivation matches the post-Phase-O.8 substrate (Phase O.8 commit `f62cec1` "ES+NQ pre-2020 + NQ 2025 backfill") deterministically, confirming the roll-adjusted module's reproducibility.

**Substrate symbols**: ES, NQ, MGC, SIL (full periods 2015-2026), MCL (2021-07-12 inception per the Phase O.0 amendment).

## Reproducibility-binding semantics per emitted KPI card

| Hypothesis / version | Bound substrate SHA | Reproducibility status |
|---|---|---|
| H062 v1 (run_id `16cb68d9...`) | `1247dc7e...` | **Reproducible** from a checkout pinned to git_head `463378b` (Phase O.2 batch-3) + a substrate pinned to the pre-Phase-O.3-backfill vintage. The main-HEAD substrate `317429e4...` differs from `1247dc7e...` because of the 2026-H1 + pre-2020 backfills. Re-running H062 v1 on the current main HEAD produces DIFFERENT numerics. Per pre-reg freeze discipline this is correct behavior; the v1 result-of-record is the originally-emitted figures. |
| H055 v1 (run_id `v2_sweep_2026...`) | `b93e544...` | **Sibling-worktree-only reproducible.** The substrate at SHA `b93e544...` exists only in `.claude/worktrees/nervous-greider-90c8f0/...`. To reproduce H055 v1 on main HEAD, the operator must either (a) check out the `nervous-greider-90c8f0` worktree's substrate snapshot, or (b) re-run the H055 v2 sweep on the canonical `317429e4...` substrate which will produce a v2-distinct ReproLog. Per ADR-0013 §3 reproducibility contract this is a substrate-locality drift; the v1 emission is preserved verbatim per ADR-0013 §4.1 non-loss. |
| H065 v1 (run_id `tp_overlay_sweep_2026...`) | `b93e544...` | Same disposition as H055 v1. |
| H062 Phase O.9 sub-window | `317429e4...` | **Reproducible on main HEAD.** No drift. |
| MPV1 v1 descriptive exhibit (run_id `v1_2026...`) | inherits from H060 ReproLog (substrate via H060 arm) | **Non-reproducible**: H060 ReproLog `git_head=75f869e` is NOT reachable from main HEAD `a5766fd`. The H060 arm substrate provenance is broken at the reachable-commit layer; tracked under `P1-H060-REPROLOG-GIT-HEAD-UNREACHABLE`. |

## Ledger-claim correction for CLAUDE.md Phase O.0

CLAUDE.md Phase O.0 ledger entries claim **combined substrate SHA `242aaa280b216f45...`**. No provenance JSON on disk produces this SHA. The actual post-Phase-O.0-Stage-B substrate produces `1247dc7e...` (per [`vendor_legacy_1min_roll_adjusted_20260512.json`](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json)) on the 2026-05-12 vintage. The `242aaa28...` claim is a Phase O.0 ledger-error; preserved verbatim per the append-only-ledger discipline; this memo supplies the canonical correction.

Phase O.0 follow-on entry verified this same drift and registered `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE`. **This memo closes that follow-up.**

## Per-symbol coverage summary on the canonical `317429e4...` substrate

Per [`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json`](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json):

| Symbol | Coverage start | Coverage end | Notes |
|---|---|---|---|
| ES | 2015-01-01 | 2026-06-30 | full pre-COVID + post-Phase-O.8 backfill |
| NQ | 2015-01-01 | 2026-06-30 | full pre-COVID + post-Phase-O.8 NQ 2025 backfill |
| MCL | 2021-07-12 | 2026-06-30 | post-CME-Micro-Crude inception 2021-07-12; excluded from H060 v1 + H062 v1 per the Phase O.0 amendment |
| MGC | 2015-01-01 | 2026-06-30 | full coverage |
| SIL | 2015-01-01 | 2026-06-30 | full coverage |

## Action items

1. **Closes** `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE` (open from Phase O.1 follow-on).
2. **Promotes** `P1-H055-V2-RERUN-ON-CANONICAL-SUBSTRATE` from non-blocking to BLOCKING-BEFORE-NEXT-H055-PROMOTION (re-run the H055 v2 sweep on `317429e4...` for canonical-substrate reproducibility per ADR-0013 §3).
3. **Promotes** `P1-H065-V2-RERUN-ON-CANONICAL-SUBSTRATE` to BLOCKING with same rationale.
4. **Tracks** `P1-H060-REPROLOG-GIT-HEAD-UNREACHABLE` as BLOCKING-BEFORE-NEXT-MPV1-CASCADE.
5. **Tracks** `P1-SIDECAR-ROOT-PATH-PROJECT-RELATIVE` as non-blocking defensive hardening (strip absolute-path roots from sidecars at write time; closes the identity-hygiene OS-username leak across 5+ committed sidecars).

## Reproducibility contract going forward

Every new KPI emission MUST bind to the canonical substrate SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (or its deterministic successor on the next ingest run) UNLESS the design.md §16 explicitly pre-registers a different vintage. The reconciliation table above is the project-canonical mapping; future audits should re-verify against this table.
