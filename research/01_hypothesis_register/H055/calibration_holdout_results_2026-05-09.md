# H055 Calibration Holdout Results (2026-05-09)

Per-class trend-identifier Brier-score competition (§5.1) + ρ* quantile calibration (§5.2) per design.md §5.


> **Smoke-mode result**: synthetic 1-min bars; no statistical interpretation. Validates harness mechanics only.


## §5.1 Trend-identifier ID_1*_c (per instrument-class)

| Instrument class | Candidate ID_1 | n_eligible_bars | Brier score | Predicted (long/short/zero) |
|---|---|---:|---:|---:|
| ES_class | a | 995 | 1.3317 | 373 / 45 / 582 |
| ES_class | b | 995 | 1.6101 | 492 / 165 / 343 |
| ES_class | c | 995 | 1.5095 | 661 / 112 / 227 |
| ES_class | d **(SELECTED)** | 995 | 0.9980 | 2 / 0 / 998 |
| NQ_class | a | 995 | 1.2915 | 438 / 0 / 562 |
| NQ_class | b | 995 | 1.4704 | 531 / 110 / 359 |
| NQ_class | c | 995 | 1.4905 | 712 / 89 / 199 |
| NQ_class | d **(SELECTED)** | 995 | 1.0000 | 0 / 0 / 1000 |


### Selected ID_1*_c per instrument-class

- ES_class: ID_1*_c = `d`
- NQ_class: ID_1*_c = `d`


## §5.2 ρ* quantile selection (project-wide)

| Quantile q | ρ*_q | n_conditional_bars | Conditional Brier |
|---:|---:|---:|---:|
| 0.50 | 0.1007 | 2496 | 0.0489 |
| 0.60 | 0.1161 | 1997 | 0.0481 |
| 0.70 | 0.1345 | 1498 | 0.0481 |
| 0.80 | 0.1542 | 999 | 0.0420 |
| 0.90 **(SELECTED)** | 0.1858 | 500 | 0.0360 |


### Selected ρ* = 0.1858 (quantile q = 0.9)

Update `config/hypotheses/H055.yaml` `gates.rho_star` to this value via a separate audit-remediated commit per `P1-H055-CALIBRATION-HOLDOUT-RUN` closure.
