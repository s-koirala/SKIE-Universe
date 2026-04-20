---
name: ADR-0001 — Project scope and boundary
description: Fixes what this project is and is not
type: project
status: accepted
date: 2026-04-15
---

# ADR-0001 — Project scope and boundary

## Context
SKIE Ninja prior work established predictability of volatility, breakout, and movement size on crypto/event-contract substrates, but direction remains 50% AUC via technicals. The user wants an ES/NQ intraday program executed on NinjaTrader Desktop, attacking the directional wall exhaustively and longitudinally.

## Decision
- **In scope**: ES, NQ, MES, MNQ front-month futures; RTH + ETH sessions; any signal family (microstructure, flow, macro surprise, text/LLM, alt-data, cross-asset); execution via NinjaTrader 8 Desktop (paper → live).
- **Out of scope**: portfolio construction across non-index futures; options market-making; anything that doesn't ultimately produce an ES/NQ directional or sizing decision intraday.
- **Philosophy**: longitudinal — every signal in the backlog gets a pre-registered design doc. Null results are kept. No "one-strategy" framing.
- **Exhaustiveness principle**: we evaluate *everything* in the hypothesis backlog whose expected-information / cost ratio beats the current bar, refreshed quarterly.

## Consequences
- Folder structure accommodates unbounded growth in signals and models ([../../research/01_hypothesis_register/](../../research/01_hypothesis_register/), [../../src/skie_ninja/features/](../../src/skie_ninja/features/)).
- Multiple-testing correction is not an afterthought — Hansen SPA is a first-class gate.
- Execution adapter is pluggable because the Python↔NinjaTrader approach may be revised after empirical latency testing.

## Alternatives considered
- Single-strategy CTA build: rejected; does not match user's stated exhaustive/longitudinal intent.
- Broker-agnostic execution layer: rejected for now; NinjaTrader Desktop is the user-specified endpoint. Abstraction can be added later if a second venue emerges.
