# H055 KPI Report Card v1 (run_id `prod_ES`)

Survival-constrained inferential framework per [ADR-0017 §1](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md). Sharpe-family metrics archived per project directive (2026-05-09 operator instruction).


## §1 Realized OOS ($10,000 starting capital)

| Symbol | n_bars | n_setups | n_post_gate | n_trades_filled | Realized end | % change | Max-DD | Ann. return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES | 1,500 | 172 | 2 | 0 | $10,000.00 | +0.00% | 0.00% | 0.00% |


## §2 ADR-0017 §1 Primary Inference (with stationary-bootstrap CI)

| Symbol | Calmar | Profit-factor | R-mult mean | R-mult 95% CI | Excludes 0 | Underpowered |
|---|---:|---:|---:|:--:|:--:|:--:|
| ES | +0.000 | n/a | +0.0000 | n/a (n_trades < 4) | n/a | n/a |


## §3 Forward 1-year projection (252-session bootstrap; 5,000 paths)

| Symbol | Median | q01 | q05 | q95 | q99 | P(loss) | P(<50% bankroll) | Risk-of-ruin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |


## §4 ADR-0017 §1 Verdict per Symbol

- **ES**: Calmar = +0.000 (marginal)


> **Production-mode result**: real substrate. Operator review per the user's 2026-05-04 standing decline-ninjascript directive + ADR-0013 §5.3 operator-discretionary clause.
