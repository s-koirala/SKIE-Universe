---
name: H059 data requirements
description: Pre-registration dataset checksums and coverage bounds for H059
type: project
hypothesis_id: H059
status: designed
created: 2026-04-27
---

# H059 — Data Requirements

Pre-registration companion to [design.md](design.md) §12. Frozen at the time the hypothesis moves to `status=running`. Any subsequent dataset update requires a successor hypothesis ID.

H059 introduces **no new substrate ingest**. The hypothesis reads the H050 roll-adjusted ES + NQ 1-minute parquet substrate; the rendered-chart inputs are computed at decision time from the substrate by [src/skie_ninja/models/vlm/render.py](../../../src/skie_ninja/models/vlm/render.py) (scaffold to be added at `status=running` transition). The Qwen2.5-VL-3B backbone weights and tokenizer are downloaded once from Hugging Face at `status=running` transition and pinned by SHA256 in the H059 sidecar per [design.md §12.1](design.md).

## Source dataset (inherited from H050)

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23; no redistribution; internal research use only. |
| Symbols | ES.FUT, NQ.FUT (front-month; Databento continuous series) |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment ([Lopez de Prado 2018](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086)) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` v0.3.0 (commit `329fd1b` decade-wraparound disambiguation) |

## Coverage (inherited from H050)

| Field | Value |
|---|---|
| ES date range | 2015-01-01 → 2025-12-03 UTC (last bar `ts_event`) |
| NQ date range | 2015-01-01 → 2025-12-19 UTC (last bar `ts_event`) |
| Total rows (combined, roll-adjusted) | 7,354,066 |
| ES rows (sum of partitions, roll-adjusted) | 3,694,534 |
| NQ rows (sum of partitions, roll-adjusted) | 3,659,532 |

H059 train/val/test windows match H050 exactly:
- train: 2015-01-01–2022-12-31
- val: 2023-01-01–2023-12-31
- test: 2024-01-01–2025-12-31

Right-edge truncation (28 days short for ES, 12 days short for NQ at 2025-12-31) applies symmetrically to all cohort arms and is tracked under follow-up `P1-DATABENTO-RIGHT-EDGE-EXTENSION`. If H059's eventual disposition (per [design.md §11](design.md)) materially depends on the last 12-28 days of 2025, the disposition entry receives a `test-window-truncated` annotation and references this section.

## Binding substrate checksum (inherited from H050)

| Field | Value |
|---|---|
| Combined SHA256 | `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` |
| Rows | 7,354,066 |
| Computed | 2026-04-26 |
| Provenance | [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json) |

Per-partition SHAs are listed verbatim at [H050/data_requirements.md §Per-partition](../H050/data_requirements.md). H059 reads the same partitions; recomputing the per-partition SHAs here would duplicate the canonical list and risk drift. The orchestrator at run time verifies each partition SHA against the provenance JSON before any decision is computed.

## Source CSV checksums (raw tier; inherited from H050)

Per [H050/data_requirements.md §Checksums — source CSV (raw tier)](../H050/data_requirements.md). Read from [data/processed/_provenance/vendor_legacy_1min_20260426.json](../../../data/processed/_provenance/vendor_legacy_1min_20260426.json) `dataset_checksums`. H059 inherits the full table by reference; the orchestrator verifies the raw-tier provenance before any roll-adjusted partition is loaded.

## H059-specific dependencies (new)

These are not data-substrate items but are pre-registration commitments whose checksums enter the H059 `model_hash` per [design.md §12.1](design.md).

### Qwen2.5-VL-3B backbone weights

| Field | Value |
|---|---|
| Source | Hugging Face `Qwen/Qwen2.5-VL-3B-Instruct` |
| Revision | TBD at `status=running` (pinned to a specific commit SHA on the HF model repo) |
| License | Apache-2.0 (verified via [QwenLM/Qwen2.5-VL repo](https://github.com/QwenLM/Qwen2.5-VL) LICENSE) |
| weights_sha256 | TBD at `status=running` (computed via `torch.save` deterministic mode on the loaded `state_dict`) |
| param_count | ~3 × 10⁹ |
| Storage path | `~/datasets/qwen25_vl_3b_instruct/<hf_revision>/` |

The backbone weights are downloaded once at `status=running` transition and pinned. Re-running with a different HF revision constitutes a new hypothesis ID per the project's pre-registration discipline.

### LoRA adapter

The LoRA adapter is **not** a pre-existing artefact; it is fit per fold during the production walk-forward run. Per-fold `adapter_weights_sha256` values populate the H059 sidecar at run time. The adapter configuration (`r=16`, `α=32`, target modules, learning rate, epochs) is fully specified at [design.md §5.2](design.md) and is the binding pre-registration commitment.

### Render configuration

| Field | Value |
|---|---|
| Path | `logs/reproducibility/{run_id}_h055_render_config.json` |
| Schema version | `h055_render_v1` |
| Content | Per [design.md §3.1](design.md) (lookback bars, aspect ratio, image resolution, bar style, indicators, axis scale, axis range source, header, background, gridlines, anti-aliasing, renderer, matplotlib version) |
| config_json_sha256 | TBD at `status=running` (canonical-JSON serialization of the entire render_config block) |

### Tokenizer

| Field | Value |
|---|---|
| Source | Qwen2.5-VL-3B-Instruct tokenizer at the same HF revision as the backbone weights |
| vocab_sha256 | TBD at `status=running` |
| tokenizer_json_sha256 | TBD at `status=running` |

### Prompt templates

| Template | Path | sha256 |
|---|---|---|
| `P_zs` (zero-shot, fold-0 smoke-test only) | `logs/reproducibility/{run_id}_h055_prompts.json` `.p_zs_template_text` | TBD at `status=running` (sha256 of UTF-8 bytes of the verbatim template at [design.md §3.4](design.md)) |
| `P_ft` (fine-tune-target, production) | same JSON file `.p_ft_template_text` | TBD at `status=running` |

The two templates are pre-registered verbatim at [design.md §3.4](design.md). Either template changing requires a successor hypothesis ID. The `{symbol}` substitution in `P_ft` is the only prompt-time variable.

## H059 sidecar

| Field | Value |
|---|---|
| Path | `logs/reproducibility/{run_id}_h055_qwenvl.json` |
| Schema version | `h055_qwenvl_v1` |
| Schema definition | [design.md §12.1](design.md) (full JSON schema field-listed) |
| Hash integration | `sha256(file_sha256(sidecar_path) || ledger_rollup_sha256 || hmm_sidecar_sha256 || warm_cold_sidecar_sha256 || h055_render_config_json_sha256 || h055_prompts_json_sha256)` → `ReproLog.model_hash` via `with_model_hash` |

## OFI / order-book dependencies

H059 does not consume the `ofi_tickrule@1.0` feature directly; the rendered chart contains only OHLC information from the substrate. The HMM gate inherits H050's feature set and therefore inherits the OFI dependency note at [H050/data_requirements.md §OFI dependency note](../H050/data_requirements.md). MBP-10 upgrade path applies symmetrically to H050 and H059 once available.

## Provenance file

Machine-readable provenance records (inherited from H050):
- `data/processed/_provenance/vendor_legacy_1min_20260426.json` (raw tier)
- `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json` (roll-adjusted tier)

H059-specific provenance records will be written at `status=running`:
- `logs/reproducibility/{run_id}_h055_qwenvl.json` (sidecar; schema `h055_qwenvl_v1`)
- `logs/reproducibility/{run_id}_h055_render_config.json` (render config snapshot)
- `logs/reproducibility/{run_id}_h055_prompts.json` (prompt templates verbatim)

## Open follow-ups blocking `status=running`

1. **`P1-MODEL-HASH-MULTI-SIDECAR-HELPER`** — open from the ADR-0005 warm-cold-diagnostic closure. H059 is the third hypothesis to require multi-sidecar concatenation into `model_hash` (alongside H050 + warm-cold). The helper scaffold must land before H059 enters production, otherwise the `model_hash` integration in [design.md §12.1](design.md) is hand-rolled per-run.
2. **`P1-H059-RENDER-PIT-CANARY-IMPL`** — implement the three PIT canaries at [tests/unit/test_h055_render_pit.py](../../../tests/unit/test_h055_render_pit.py) per [design.md §3.6](design.md). Pixel-identity, axis-range provenance, future-bar invariance. Evidence-bar gate; orchestrator refuses to enter walk-forward unless all three pass.
3. **`P1-H059-WALL-CLOCK-PILOT-MEASUREMENT`** — measure empirical per-fold wall-clock on production GPU at fold 0 with the binding hyperparameters at the per-bar inference cadence (Q-R1-2 binding per [design.md §3.3](design.md)). If projected to > 7 days/fold across the full walk-forward, escalation path triggers per [design.md §10/§11](design.md) with successor `H059b` registration. Canonical follow-up name per synthesis memo §5 (was `P1-H059-WALL-CLOCK-PILOT` in pre-Round-1 naming).
4. **`P1-H059-RENDERER-DETERMINISM-VERIFY`** — verify `matplotlib + Agg backend + anti_aliasing=False` produces byte-identical PNG bytes across consecutive runs on the production environment. Regression test at [tests/unit/test_h055_renderer_determinism.py](../../../tests/unit/test_h055_renderer_determinism.py).
5. **`P1-H059-CONSTRAINED-DECODING-PARSE-FAILURE-ASSERT`** — assert at scaffold time that the constrained-decoding `LogitsProcessor` cannot emit a non-`A`/`B`/`C` token; the parse-failure → vertical default branch in [design.md §3.5](design.md) is defense-in-depth and expected to be unreachable.
