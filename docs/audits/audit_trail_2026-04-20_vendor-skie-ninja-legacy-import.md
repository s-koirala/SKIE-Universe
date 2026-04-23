# Audit trail — sibling-repo ES data import (2026-04-20)

## Context

Phase-1 data substrate tracking identified ES/NQ tick/bar as the outstanding dependency for H050–H052. A machine-local sweep discovered an already-processed ES 5-min features parquet in the sibling research repo at `C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\data\processed\es_5min_features_2020_2025.parquet`. A provenance-verification agent established the full chain: Databento GLBX.MDP3 ES 1-min → SKIE_Ninja `enhanced_feature_pipeline.py` → 5-min aggregated features parquet.

## Architectural decision

Three options were considered for wiring this data into SKIE-Universe:

- (a) Reroute analysis to external dir (point `SKIE_SHARED_DATA` or `ProjectPaths` at the sibling repo's `data/processed/`). **Rejected**: couples SKIE-Universe to another repo's internal filesystem layout, violating the shared-root convention in [config/shared_data.yaml](../../config/shared_data.yaml).
- (b) Extend the central shared-data root (`~/datasets/`) with a vendor-namespaced subdir and copy the parquet in. **Accepted**: matches the established pattern documented in [README.md](../../README.md) §Environment setup and the `ProjectPaths.shared_*` property family in [src/skie_ninja/utils/paths.py](../../src/skie_ninja/utils/paths.py). Decouples from sibling-repo existence.
- (c) Copy into in-repo `data/external/`. **Rejected**: already gitignored per [.gitignore](../../.gitignore) so no git-tracking gain, and violates the shared-root pattern (duplicates bytes per project).

## Changes shipped

| Surface | Change |
|---|---|
| [config/shared_data.yaml](../../config/shared_data.yaml) | Added `vendor_skie_ninja_legacy` subdir under shared root with a comment block explaining the vendor-namespacing policy |
| [src/skie_ninja/utils/paths.py](../../src/skie_ninja/utils/paths.py) | New `shared_vendor_skie_ninja_legacy` property on `ProjectPaths` |
| [tests/unit/test_paths.py](../../tests/unit/test_paths.py) | Extended coverage to assert the new property resolves under `shared_data` with the expected name |
| [config/data_sources.yaml](../../config/data_sources.yaml) | Databento `vetted: false` with note documenting the sibling-repo inheritance; new `vendor_skie_ninja_legacy` entry marked `vetted: true` with full transform + usability notes per evidence-bar policy |
| `~/datasets/vendor_skie_ninja_legacy/es_5min_features_2020_2025.parquet` (80,191,584 B ≈ 80.19 MB) | Copy of sibling parquet, SHA256-verified against source |
| `~/datasets/vendor_skie_ninja_legacy/es_5min_features_2020_2025.provenance.json` | Sidecar with source_path, source_sha256, timestamps, vendor-chain description, license note, and usability caveats |
| [README.md](../../README.md) | Phase-1 bullet updated to reflect the new ES data availability |
| [CLAUDE.md](../../CLAUDE.md) | "Implemented infrastructure" block extended |

## Import provenance

```json
{
  "dataset": "vendor_skie_ninja_legacy/es_5min_features_2020_2025",
  "source_path": "C:/Users/skoir/Documents/SKIE Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/data/processed/es_5min_features_2020_2025.parquet",
  "source_sha256": "b58ce8a5aec6a9fa34b79772010ea0d09d8fe615a72671502858acc218d1ba62",
  "source_size_bytes": 80191584,
  "rows": 269594,
  "columns": 48,
  "timestamp_range_utc": ["2020-01-01T23:00:00+00:00", "2025-12-03T23:55:00+00:00"],
  "vendor_chain": "Databento GLBX.MDP3 ES 1-min → SKIE_Ninja enhanced_feature_pipeline.py → 5-min aggregated parquet with 47 non-leaky technical features"
}
```

## Evidence-bar usability caveat

Per [CLAUDE.md](../../CLAUDE.md) §Evidence bar requirement and [rules/quant-project.md](~/.claude/rules/quant-project.md) §Reporting (data vendor + snapshot date must be declared), this parquet is classified **prototype-tier**:

- ✓ Acceptable for: H050/H051 HMM regime code plumbing, walk-forward CV harness dev, feature-engineering sanity checks, code-review of look-ahead-bias guards.
- ✗ Not acceptable for: final evidence-bar backtests feeding paper-trade decisions. CLAUDE.md §Verification requires "reproduce referenced methods; no paraphrasing without verification" — the 47 features here are the sibling repo's methodology, not SKIE-Universe's. Evidence-bar runs must re-derive features in-project from raw Databento 1-min, either via a SKIE-Universe Databento subscription or via import of the sibling's raw 1-min CSVs under a second `vendor_skie_ninja_legacy/raw/` namespace.

## Residual risk

- **NQ not covered.** This import is ES-only. NQ 5-min equivalent has not been located; the NT8 `db\minute\` tree contains ES contracts but not (apparently) NQ. H050/H051 pairs work on ES/NQ basis requires NQ data; currently blocked on either a separate Databento fetch or an NT8 minute-export via NinjaScript for NQ.
- **Static snapshot.** The parquet ends 2025-12-03. New bars require either a re-run in the sibling repo or a direct Databento fetch in SKIE-Universe.
- **Vendor-chain inheritance.** License validity transfers because both projects are under the same pseudonymous SKIE owner. A co-author or downstream redistribution would require a fresh Databento subscription check.

## Round 2 — audit-remediate response (2026-04-20)

Quant auditor returned `proceed-with-remediation` with 5 Major and 3 Minor findings, no Critical. Remediation applied in this commit:

| Finding | Severity | Disposition |
|---|---|---|
| F-1-1: prototype-tier flag not machine-checkable | Major | **Closed.** Added `tier: prototype` and `evidence_bar_eligible: false` to provenance sidecar + [config/data_sources.yaml](../../config/data_sources.yaml). [tests/integration/test_vendor_skie_ninja_legacy.py::test_tier_is_prototype_and_not_evidence_bar](../../tests/integration/test_vendor_skie_ninja_legacy.py) asserts the gate. |
| F-1-2: Databento license inheritance un-verified | Major | **Partially closed — user-action.** Sidecar now carries `license_status: pending-verification` and explicit `license_action_required` describing the ToS clause review the user must perform before evidence-bar advancement. |
| F-1-3: look-ahead QC taken on sibling's word | Major | **Partially closed.** Permutation-shift surrogate test added ([test_positive_lag_leakage_regression](../../tests/integration/test_vendor_skie_ninja_legacy.py)): shifts a candidate feature +1 bar and asserts leaky correlation > baseline by ≥0.01. Passes on imported data. Full bitwise re-derivation remains open follow-up #3. |
| F-1-4: test coverage limited to paths property | Major | **Closed.** 6-test integration suite added: row/column count, UTC tz-awareness, timestamp range, tier gate, source vs dest SHA256 equality, leakage surrogate. Machine-gated via skip-if-missing. |
| F-1-5: no ingest module | Major | **Deferred.** Tracked as follow-up #1 (unchanged). Justification: the one-shot Python copy is traceable via the provenance sidecar + this audit trail; scripting is a hygiene-not-correctness concern. Next ingest event (NQ, raw 1-min) will land via a proper `vendor_skie_ninja_legacy.py` ingest module. |
| F-1-6: size discrepancy + no dest SHA256 | Minor | **Closed.** Reconciled — audit trail size field was a typo (80215216 vs actual 80191584); corrected. `dest_sha256` + `dest_size_bytes` + `dest_verified_at_utc` added to sidecar. |
| F-1-7: NQ gap not propagated to H050/H051/H052 | Minor | **Closed.** Data-readiness block added to each of [H050](../../research/01_hypothesis_register/H050/README.md), [H051](../../research/01_hypothesis_register/H051/README.md), [H052](../../research/01_hypothesis_register/H052/README.md) linking back here. |
| F-1-8: mixed vetted states + conflated retrieval_date | Minor | **Closed.** Sidecar + data_sources.yaml split `upstream_retrieval_date` from `import_date`; upstream date marked `pending-documentation-from-sibling-repo`. |

Round 2 reached a defensible state within one remediation pass. Residual risk acknowledged: prototype-tier use in H050/H051 code development still carries the anchoring concern flagged by the auditor; evidence-bar re-derivation must run on independently-derived features.

## Follow-ups opened

1. Write `src/skie_ninja/data/ingest/vendor_skie_ninja_legacy.py` ingest module (CSV + SHA256 idempotency, two-phase commit) so future re-imports are scriptable rather than one-shot Python. Pattern: mirror [fomc_text.py](../../src/skie_ninja/data/ingest/fomc_text.py).
2. Locate or derive NQ 5-min equivalent. Options: (a) sibling-repo search for NQ features parquet, (b) NT8 minute-export NinjaScript for NQ contracts, (c) Databento NQ 1-min fetch from SKIE-Universe directly.
3. Import sibling-repo raw 1-min CSVs (`ES_1min_databento.csv` 2023–2024 in-sample + 2020/2021/2022/2025 out-of-sample) into `vendor_skie_ninja_legacy/raw/` namespace so evidence-bar feature re-derivation has canonical inputs. Blocks formal closure of F-1-3.
4. User-action: verify Databento license clause covering cross-project reuse of derivative datasets by a single subscriber; record subscriber ID + reviewed clause into provenance sidecar `license_status` field.
