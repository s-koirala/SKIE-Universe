---
name: HXXX — <short title>
description: One-line statement of what's being tested
type: project
hypothesis_id: HXXX
status: designed  # queued | designed | running | evaluated | archived(positive|null|negative)
owner: skoir
created: YYYY-MM-DD
---

# HXXX — <Title>

## Pre-registered hypothesis
Null: <H0 in precise form>.
Alt: <H1 in precise form>.

## Economic rationale
<Why should this work? Cite primary literature, not paraphrase.>

## Data
- Instrument(s):
- Frequency:
- Sample window (train / val / test, time-ordered):
- External joins:
- Provenance + checksum:

## Estimator
- Feature construction (include point-in-time proof):
- Model family + hyperparameter search protocol (no magic numbers):
- Cross-validation scheme (purged walk-forward / CPCV):
- Loss / metric:

## Inference
- Standard errors (NW-HAC bandwidth rule):
- Sharpe CI method:
- Multiple-testing correction (SPA family the result enters):

## Assumption checks
- Stationarity:
- Independence:
- Distribution:
- Look-ahead audit:

## Stopping rule
<Pre-specified criterion for declaring null / positive / negative. No p-hacking.>

## Results
<Filled in at `evaluated`. Include bootstrap CI, SPA-corrected p-value, diagnostics.>

## Decision
<Archive label + one-paragraph post-mortem.>

## Reproducibility
- git HEAD:
- `uv pip freeze` hash:
- dataset checksum:
- seed:
- runtime env:
