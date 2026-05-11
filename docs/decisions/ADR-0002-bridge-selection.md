---
id: ADR-0002
title: Python↔NinjaTrader 8 execution bridge selection
status: proposed
date: 2026-04-15
decision-owner: Execution-research agent / Lead researcher
supersedes: none
related:
  - plan/buildouts/implementation-plan_2026-04-15.md §P0-10
  - plan/buildouts/implementation-plan_2026-04-15.md §7 Execution Adapter Interface
  - plan/buildouts/implementation-plan_2026-04-15.md §8 Kill-Switches
  - docs/methodology/arch_ninjatrader-automation-options_2026-04-15.md
  - research/03_audits/audit-round1-quant_2026-04-15.md #22
---

# ADR-0002 — Python↔NinjaTrader 8 execution bridge selection

> **Phase-0 gate status.** STATUS: proposed. This ADR BLOCKS Phase-0 gate G0 per [plan §P0-10](../../plan/buildouts/implementation-plan_2026-04-15.md) acceptance until the measurement protocol in §5 is executed by the user and status flipped to `accepted`. See §8 Acceptance Checklist and §9 Phase-0 follow-up.

## Status

Proposed. Acceptance is conditional on executing the measurement protocol in §5 against a live NinjaTrader 8 paper account. Status moves to `accepted` only when the checklist in §8 is green.

## 1. Context

[§7 of the implementation plan](../../plan/buildouts/implementation-plan_2026-04-15.md) defines `OrderRouter`, `NinjaTraderRouter`, and `MCPRouter`. The bridge chosen here instantiates `NinjaTraderRouter`. [§8](../../plan/buildouts/implementation-plan_2026-04-15.md) requires `LatencyAnomalySwitch` with baseline `submit→ack` p99; the baseline is a direct function of the bridge choice. The project constraint set requires bounded latency, deterministic behaviour, full observability, parity between research and live, and hard kill-switches (CLAUDE.md §Research philosophy, §Execution bar for live; [arch doc §1](../methodology/arch_ninjatrader-automation-options_2026-04-15.md)).

Candidate set (P0-10 scope):

1. **ATI-socket** — NinjaScript AddOn TCP server consumed over localhost; orders expressed as native NinjaScript order calls inside NT. Equivalent to arch-doc Approaches 2 and 9 ([AddOn Development Overview](https://ninjatrader.com/support/helpguides/nt8/addon_development_overview.htm); [NT forum: socket calls from NinjaScript](https://forum.ninjatrader.com/forum/ninjatrader-8/strategy-development/1148878-how-can-i-make-socket-calls-from-within-ninjascript)).
2. **NTDirect-pythonnet** — `NTDirect.dll` / `NinjaTrader.Client.dll` loaded in-process from Python via pythonnet/ctypes. Arch-doc Approaches 3 and 5 ([DLL Interface](https://ninjatrader.com/support/helpguides/nt8/dll_interface.htm); [DLL functions](https://ninjatrader.com/support/helpguides/nt8/functions.htm); [ATI overview](https://ninjatrader.com/support/helpGuides/nt8/automated_trading_interface_at.htm)).
3. **File-bridge** — OIF files dropped into `My Documents\<NT>\incoming\`, polled by NT. Arch-doc Approach 4 ([Order Instruction Files](https://ninjatrader.com/support/helpGuides/nt8/order_instruction_files_oif.htm); [File Interface](https://ninjatrader.com/support/helpguides/nt8/file_interface.htm)).
4. **MCP-server** — Model Context Protocol server exposing NT tools to an LLM client ([MCP spec](https://modelcontextprotocol.io/); [Anthropic: code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)).

## 2. Decision drivers

- D1 **One-way p50/p99 latency** of `submit → NT-accepted` under sustained rate; budget 50–200 ms intraday bars, sub-10 ms if microstructure ([arch doc §1](../methodology/arch_ninjatrader-automation-options_2026-04-15.md)).
- D2 **Determinism** — identical input, identical order action (CLAUDE.md §Parameter & Prompt Selection).
- D3 **Observability** — every order correlates to a JSONL record with `git_head`, `pip_freeze`, `dataset_sha`, RNG seed, model hash (CLAUDE.md §Reproducibility).
- D4 **Stability under NT point releases** — the interface must not silently break on NT update.
- D5 **Coupling cost** — single source of truth; minimise translation layers between research Python and live execution (arch doc §1.5 parity).
- D6 **Safety surface** — compatible with [§8 kill-switches](../../plan/buildouts/implementation-plan_2026-04-15.md) and broker-side Trailing Max Drawdown ([NT: Trailing Max Drawdown](https://support.ninjatrader.com/s/article/How-Do-I-Set-a-Trailing-Max-Drawdown-on-My-Account?language=en_US)).

## 3. Considered options

### 3.1 ATI-socket (AddOn TCP + NinjaScript order execution)

- **Mechanism**: NS AddOn hosts a length-prefixed MessagePack TCP server on localhost; a paired NS Strategy consumes validated signal messages and submits via native order methods with ATM bracket attachments ([ATM Strategy Methods](https://ninjatrader.com/support/helpguides/nt8/atm_strategy_methods.htm)).
- **Latency**: localhost loopback TCP round-trips are typically well below 1 ms at the transport layer; serialisation (MessagePack ~10–30 μs, JSON ~100 μs) and NS `OnMarketData`/order-engine queueing dominate. Expected end-to-end `python submit → NS ack` in the 5–30 ms range (arch doc §3.2).
- **Determinism**: NS order methods are deterministic given state; socket message handling is FIFO with explicit backpressure. Correlation IDs round-trip.
- **Observability**: both sides logged with correlation ID; NS trace + Output window + Strategy log available natively.
- **Stability**: AddOn surface is stable across NT8 point releases because it uses the supported .NET BCL and documented NS lifecycle ([NinjaScript Lifecycle](https://ninjatrader.com/support/helpguides/nt8/understanding_the_lifecycle_of.htm); [OnStateChange](https://ninjatrader.com/support/helpguides/nt8/onstatechange.htm)).
- **Risks**: socket desync, unbounded queues (mitigate via bounded MPSC with explicit drop-oldest and a `BackpressureSwitch`); ATM attachment semantics must be unit-tested on paper.

### 3.2 NTDirect-pythonnet

- **Mechanism**: load `NTDirect.dll` (unmanaged) or `NinjaTrader.Client.dll` (managed) from Python; call `Command(...)`, `MarketData(...)`, `Connected(...)` etc.
- **Latency**: in-process call; expected sub-ms at the DLL boundary, excluding NT's internal order queue.
- **Stability — material problem**: NT classifies the DLL as an ATI dispatcher and states support is "very limited", with external code explicitly out of scope ([NT forum: Using NTDirect.dll with NT8](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1215836-using-ntdirect-dll-with-nt8); [ATI overview](https://ninjatrader.com/support/helpGuides/nt8/automated_trading_interface_at.htm)). Invalid arguments may fail silently or return `-1`. Python ctypes marshalling pitfalls documented ([NT forum: Error loading NtDirect.dll in Python](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1077052-error-loading-ntdirect-dll-in-python); [NT forum: Connecting to NT8 from python](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1050517-connecting-to-nt8-from-python)).
- **Operational**: ATI toggle must be enabled each session unless persisted; ATI supports only a subset of order types ([ATI settings](https://ninjatrader.com/support/helpguides/nt8/options_ati.htm)).
- **R2 lock-in risk** ([audit-round1-quant item #22 / §R2](../../research/03_audits/audit-round1-quant_2026-04-15.md)): tight coupling of live research to an unsupported DLL ABI raises the expected cost of an NT point-release regression.

### 3.3 File-bridge (OIF)

- **Mechanism**: Python writes semicolon-delimited `COMMAND;ACCOUNT;INSTRUMENT;...` files to `incoming\`; NT polls the directory. Files must be written in place with unique names ([Order Instruction Files](https://ninjatrader.com/support/helpGuides/nt8/order_instruction_files_oif.htm)).
- **Latency**: disk flush + poll interval; ReadDirectoryChangesW / FileSystemWatcher coalesces events under load and is not a hard-real-time primitive ([MSDN: ReadDirectoryChangesW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw); [MSDN: FileSystemWatcher](https://learn.microsoft.com/en-us/dotnet/api/system.io.filesystemwatcher)). Expect p50 in hundreds of ms; p99 degrades severely under OneDrive / AV / Windows Search on `My Documents` ([NT forum: ATI vs OIF](https://forum.ninjatrader.com/forum/ninjatrader-8/add-on-development/1239740-ati-vs-oif)).
- **Use**: cold-DR path only; low-frequency rebalance or manual flatten.

### 3.4 MCP-server

- **Mechanism**: MCP tools wrap order submission; client is an LLM.
- **Latency floor**: 1–5 s including model inference, two to three orders of magnitude above the intraday budget (arch doc §4; [Building an AI Trading Bot with MCP (Medium)](https://medium.com/@cognidownunder/building-an-ai-trading-bot-using-model-context-protocol-mcp-server-a-detailed-guide-17a75e468ea5)).
- **Determinism**: LLM sampling breaks reproducibility; prompt-injection surface when the model consumes headlines/chat.
- **Designation**: [§7](../../plan/buildouts/implementation-plan_2026-04-15.md) explicitly assigns `MCPRouter` read-only research. **Rejected for live order placement.**

## 4. Decision outcome (tentative, conditional on §5 measurements)

**Selected: `ATI-socket` (NS AddOn TCP + NinjaScript execution).**

Ranking:

1. **ATI-socket — primary.** In the [arch-doc §8 recommendation](../methodology/arch_ninjatrader-automation-options_2026-04-15.md) this is the Phase-0 hybrid pattern (Approaches 9 + 2). It keeps a single source of truth in Python for decisions while execution runs on the only NT-supported surface (AddOn + Strategy). Expected latency satisfies D1 for intraday bars; stability under NT point releases (D4) is the strongest of the four. Observability (D3) is natural because both sides speak an application protocol with correlation IDs.
2. **NTDirect-pythonnet — fallback.** Lower nominal latency but materially higher fragility. NT's own documentation marks the interface as unsupported for general use; the R2 audit finding flags this as lock-in risk. Reserve as fallback only if the ATI-socket measurement fails D1 by a margin that sub-ms DLL calls would close (unlikely on intraday budgets).
3. **File-bridge — cold-disaster-recovery only.** OS-dependent polling latency and `My Documents` collision footguns disqualify it from the hot path. Retain as an operator-triggered flatten / re-enter mechanism when the socket path is down and broker-side kill-switches are insufficient.
4. **MCP — rejected for order placement.** Per [§7](../../plan/buildouts/implementation-plan_2026-04-15.md), `MCPRouter` is read-only. Live orders via MCP violate D1, D2, and D6.

**Reconciliation with the prior architecture survey:** the user-provided tentative ranking suggested NTDirect-pythonnet as primary with ATI-socket as fallback. The architecture survey ([arch_ninjatrader-automation-options_2026-04-15.md §3.3, §8](../methodology/arch_ninjatrader-automation-options_2026-04-15.md)) classifies NTDirect-pythonnet as "Prototypes only" on stability grounds and recommends the hybrid AddOn-socket pattern as the Phase-0 default. Per project convention the prior survey's ranking governs; this ADR inverts the first two positions of the proposed ranking accordingly and documents the inversion here so that the measurement protocol can falsify the survey if latency data so indicates.

## 5. Measurement protocol (to be executed by user before acceptance)

Each option under test drives a NinjaTrader 8 paper account (Sim101) with the ATI toggle enabled where applicable.

### 5.1 Payload shape — order-submit message

Fixed-schema MessagePack object (length-prefixed frame when a socket is used):

```
OrderSubmit := {
    "msg_id": uuid4,                   # correlation ID
    "ts_py_submit_mono_ns": uint64,    # time.monotonic_ns() at send
    "ts_py_submit_wall_ns": uint64,    # time.time_ns() for skew reporting
    "symbol": "MES 06-26",
    "side": "Buy" | "Sell",
    "qty": 1,
    "order_type": "Market",
    "tif": "Day",
    "account": "Sim101",
    "tag": "adr2_bench"
}
```

Payload is identical across options to remove serialisation-size as a covariate. For OIF the same fields are serialised into the NT-required semicolon-delimited line ([OIF spec](https://ninjatrader.com/support/helpGuides/nt8/order_instruction_files_oif.htm)).

### 5.2 Timing methodology

- Python clock: `time.monotonic_ns()` on the submitter side.
- NS clock: `Stopwatch.GetTimestamp()` scaled to ns on the AddOn/Strategy side.
- Wall clocks synchronised via Windows NTP (`w32tm /stripchart`); record per-session skew.
- Per message record: `ts_py_submit_mono_ns` (Python send), `ts_nt_receive_ns` (NS entry), `ts_nt_accept_ns` (order state == `Accepted`), `ts_py_ack_mono_ns` (Python-side ack of `Accepted`).
- Round-trip: `RTT = ts_py_ack - ts_py_submit`. Server-side processing: `SVC = ts_nt_accept - ts_nt_receive`.
- Approximate one-way Python→NT: `OW_in = (RTT − SVC) / 2 + SVC_in`, with the symmetric-path assumption stated; report also raw `ts_nt_receive - ts_py_submit` after monotonic-to-monotonic alignment using the session NTP skew.
- Orders are rejected at NT by submitting with `qty=0` when testing a read-only variant, or submitted and immediately cancelled when a real accept is required. Rejection rate logged.

### 5.3 Sample size and warm-up

- Per option: **N = 10 000** accepted messages after a **warm-up of 500** discarded. Rationale for ≥10k: per audit item #22, SE on empirical p99 with n=1000 and heavy-tailed latency dominates the quantile; see also [Hyndman-Fan 1996](https://doi.org/10.2307/2684934) on quantile estimator choice.
- Inter-message interval: Poisson(λ=20 Hz) to approximate bursty intraday submission, capped at 1 in-flight. Logged `submit_rate_hz`.
- Three sessions (RTH open, mid-day, ETH) per option to capture regime variability.

### 5.4 Estimator and inference

- Quantile estimator: Type 7 per [Hyndman-Fan 1996, Am Stat 50:361](https://doi.org/10.2307/2684934); report p50, p90, p99, p99.9, max.
- 95% CI on p99: **stationary bootstrap** per [Politis-Romano 1994, Ann Stat 22:2031](https://doi.org/10.1214/aos/1176325770) to respect serial dependence from burst patterns, with optimal expected block length from [Politis-White 2004](https://doi.org/10.1081/ETC-120028836). 10 000 bootstrap resamples; report Monte-Carlo SE √(p(1−p)/B).
- Distributional report: ECDF, log-log tail (Hill plot) to detect power-law tails; Anderson-Darling against exponential as a tail sanity check.
- Acceptance threshold: p99(ATI-socket) ≤ 50 ms with 95% CI upper bound ≤ 100 ms, intraday-bar budget per arch doc §1.

  ```
  # justify: 50 ms p99 / 100 ms CI-upper latency budget
  # Intraday microstructure alpha half-life for ES order-flow imbalance is of
  # order the tick-arrival interval (~10-100 ms during RTH) per Bouchaud,
  # Farmer, Lillo, "Trades, Quotes and Prices" (Cambridge UP, 2018), ch. 10.
  # Peer-reviewed anchor on OFI as the relevant intraday microstructure
  # signal: Cont, Kukanov, Stoikov 2014, J. Fin. Econometrics 12(1):47-88
  # (https://doi.org/10.1093/jjfinec/nbt030). A 50 ms p99 submit->ack budget
  # keeps one-way execution delay inside one half-life of the shortest
  # microstructure signal we plan to trade (H010 deep-OFI); the 100 ms 95% CI
  # upper bound preserves that guarantee under sampling uncertainty on the
  # empirical p99. If the auditor's finding or prior arch-doc analysis
  # identifies a tighter anchor, retain 50 ms and update the evidence basis
  # here rather than the number.
  ```

### 5.5 Outputs

- `logs/reproducibility/adr2_bridge_bench_{option}_{YYYYMMDD}.json` — repro log (git HEAD, `uv pip freeze`, dataset checksum N/A, RNG seed, NT version, broker, session tag) per CLAUDE.md §Reproducibility.
- `docs/decisions/ADR-0002-bridge-selection.md` — this file, with the populated table below once measured.

```
| option              | N     | p50_ms | p99_ms | p99_CI95_ms      | reject_rate | notes |
|---------------------|-------|--------|--------|------------------|-------------|-------|
| ATI-socket          | TBD   | TBD    | TBD    | [TBD, TBD]       | TBD         |       |
| NTDirect-pythonnet  | TBD   | TBD    | TBD    | [TBD, TBD]       | TBD         |       |
| file-bridge         | TBD   | TBD    | TBD    | [TBD, TBD]       | TBD         |       |
| MCP-server          | n/a   | n/a    | n/a    | n/a              | n/a         | rejected per §7 |
```

## 6. Consequences

### Positive

- `NinjaTraderRouter` binds to the NT-supported AddOn surface; no dependency on unsupported DLL ABIs.
- Single source of truth for signals stays in Python; NS owns only validation, submission, and ATM bracket attachment — minimising research/live parity drift (arch doc §1.5).
- Protocol is amenable to `GuardedRouter` + `§8` kill-switches: `DataStalenessSwitch`, `LatencyAnomalySwitch`, and `ConnectionSwitch` all have natural observation points at the socket boundary.
- File-bridge retained as an out-of-band operator-triggered flatten path independent of the main socket, aligning with CLAUDE.md §Execution bar for live "kill-switch documented".

### Negative

- Two codebases (Python + C#) and one serialisation contract to version. Mitigation: `schemas/execution.msgpack.v1.yaml` versioned and enforced both sides; CI asserts round-trip parity.
- Socket backpressure / queue-length management is now part of the execution contract. Mitigation: bounded queue with drop-oldest for market-data, bounded queue with block-and-alert for orders.
- Measurement protocol must be re-executed on any NT8 point release (D4 under change). Mitigation: add to `ci/nt_upgrade_checklist.md` as a release-gate item.
- NTDirect-pythonnet fallback requires a separate adapter to stay warm; if never exercised, will bit-rot. Mitigation: quarterly smoke test against paper account, logged to reproducibility trail.

## 7. Compliance

- CLAUDE.md §Reproducibility: every bench run writes a repro log; see §5.5.
- CLAUDE.md §Parameter & Prompt Selection (no magic numbers): acceptance thresholds (50 ms p99, N=10k, warmup=500) justified in §5.3–5.4 with citations; 50 ms is derived from the intraday bar budget in arch doc §1 and can be tightened if a microstructure hypothesis is later admitted.
- quant-project.md §Time-series integrity: bench uses Poisson inter-arrival to reflect bursty submission; no look-ahead concern since this is an execution-layer benchmark.
- quant-project.md §Inference: stationary bootstrap selected over iid bootstrap to respect serial dependence ([Politis-Romano 1994](https://doi.org/10.1214/aos/1176325770)).
- publishing.md §Identity hygiene: benchmark logs contain no PHI, no broker account numbers beyond `Sim101`; git author verified per project convention.

## 8. Acceptance checklist (status → `accepted`)

- [ ] NT8 paper account (Sim101) configured with ATI toggle enabled and broker-side Trailing Max Drawdown active ([NT: Trailing Max Drawdown](https://support.ninjatrader.com/s/article/How-Do-I-Set-a-Trailing-Max-Drawdown-on-My-Account?language=en_US)).
- [ ] Harness `scripts/bench_bridge.py` implemented per §5.1–5.2; CI-run on a Windows self-hosted runner or user workstation.
- [ ] Three sessions (RTH open, mid-day, ETH) completed per option 1–3; N≥10 000 accepted per session after 500-message warm-up.
- [ ] Stationary-bootstrap p99 CI table populated in §5.5.
- [ ] ATI-socket p99 95% CI upper bound ≤ 100 ms; if not, escalate to NTDirect-pythonnet fallback or revise the intraday budget.
- [ ] Repro logs written to `logs/reproducibility/adr2_bridge_bench_*_YYYYMMDD.json`.
- [ ] This ADR's `status` field edited to `accepted` with the date of the final measurement session.
- [ ] [§8 `LatencyAnomalySwitch`](../../plan/buildouts/implementation-plan_2026-04-15.md) baseline (rolling-100 p99) seeded from the accepted ATI-socket distribution.

## 9. Phase-0 follow-up

This ADR remains in `proposed` state and is the remediation record for audit finding **F-2-14** ([audit-round1-quant_2026-04-15.md #22 / §R2](../../research/03_audits/audit-round1-quant_2026-04-15.md)), which flagged the combination of `status=proposed` and a TBD latency table in §5.5 as a Phase-0 gate G0 blocker.

Remediation obligation (user-owned; not executable by the agent):

1. Provision NT8 paper account (Sim101) per §8 checklist item 1.
2. Execute the §5 measurement protocol across options 1–3 with N ≥ 10 000 accepted messages per option per session, three sessions (RTH open, mid-day, ETH).
3. Populate the latency table in §5.5 with empirical p50, p99, stationary-bootstrap 95% CI, and reject rate.
4. Verify ATI-socket p99 95% CI upper bound ≤ 100 ms against the budget justified in §5.4; if violated, invoke the NTDirect-pythonnet fallback clause in §4 or revise the budget with a documented evidence update.
5. Write reproducibility logs to `logs/reproducibility/adr2_bridge_bench_{option}_{YYYYMMDD}.json`.
6. Flip the frontmatter `status` field from `proposed` to `accepted` with the final measurement-session date, remove the Phase-0 gate banner at the top of this ADR, tick the §8 checklist, and seed [§8 `LatencyAnomalySwitch`](../../plan/buildouts/implementation-plan_2026-04-15.md) baseline from the accepted ATI-socket distribution.

Until step 6 is complete, Phase-0 gate G0 remains blocked and no code binding to `NinjaTraderRouter` may pass the plan's P0-10 acceptance criteria. The agent cannot fabricate or proxy the §5 measurements; the latency table must be populated from a real paper-account run.

## 10. References

### Official NinjaTrader documentation

- [Automated Trading Interface overview](https://ninjatrader.com/support/helpGuides/nt8/automated_trading_interface_at.htm)
- [ATI settings](https://ninjatrader.com/support/helpguides/nt8/options_ati.htm)
- [DLL Interface](https://ninjatrader.com/support/helpguides/nt8/dll_interface.htm)
- [DLL Functions](https://ninjatrader.com/support/helpguides/nt8/functions.htm)
- [File Interface](https://ninjatrader.com/support/helpguides/nt8/file_interface.htm)
- [Order Instruction Files (OIF)](https://ninjatrader.com/support/helpGuides/nt8/order_instruction_files_oif.htm)
- [AddOn Development Overview](https://ninjatrader.com/support/helpguides/nt8/addon_development_overview.htm)
- [NinjaScript Lifecycle](https://ninjatrader.com/support/helpguides/nt8/understanding_the_lifecycle_of.htm)
- [OnStateChange](https://ninjatrader.com/support/helpguides/nt8/onstatechange.htm)
- [OnMarketData](https://ninjatrader.com/support/helpguides/nt8/onmarketdata.htm)
- [ATM Strategy Methods](https://ninjatrader.com/support/helpguides/nt8/atm_strategy_methods.htm)
- [Performance Tips](https://ninjatrader.com/support/helpguides/nt8/performance_tips2.htm)
- [Trailing Max Drawdown](https://support.ninjatrader.com/s/article/How-Do-I-Set-a-Trailing-Max-Drawdown-on-My-Account?language=en_US)

### NinjaTrader community threads (vetted)

- [Connecting to NT8 from Python](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1050517-connecting-to-nt8-from-python)
- [Error loading NtDirect.dll in Python](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1077052-error-loading-ntdirect-dll-in-python)
- [Using NTDirect.dll with NT8](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1215836-using-ntdirect-dll-with-nt8)
- [Socket calls from within NinjaScript](https://forum.ninjatrader.com/forum/ninjatrader-8/strategy-development/1148878-how-can-i-make-socket-calls-from-within-ninjascript)
- [ATI vs OIF](https://forum.ninjatrader.com/forum/ninjatrader-8/add-on-development/1239740-ati-vs-oif)

### Microsoft platform documentation

- [ReadDirectoryChangesW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw)
- [FileSystemWatcher](https://learn.microsoft.com/en-us/dotnet/api/system.io.filesystemwatcher)

### MCP / LLM tooling

- [Model Context Protocol specification](https://modelcontextprotocol.io/)
- [Anthropic — Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Model Context Protocol (Wikipedia)](https://en.wikipedia.org/wiki/Model_Context_Protocol)
- [Building an AI Trading Bot with MCP (Medium)](https://medium.com/@cognidownunder/building-an-ai-trading-bot-using-model-context-protocol-mcp-server-a-detailed-guide-17a75e468ea5)

### Statistical methodology

- [Hyndman & Fan 1996, Am Stat 50:361 — Sample quantiles in statistical packages](https://doi.org/10.2307/2684934)
- [Politis & Romano 1994, Ann Stat 22:2031 — The stationary bootstrap](https://doi.org/10.1214/aos/1176325770)
- [Politis & White 2004 — Automatic block-length selection](https://doi.org/10.1081/ETC-120028836)

### Internal

- [docs/methodology/arch_ninjatrader-automation-options_2026-04-15.md](../methodology/arch_ninjatrader-automation-options_2026-04-15.md)
- [plan/buildouts/implementation-plan_2026-04-15.md §P0-10, §7, §8](../../plan/buildouts/implementation-plan_2026-04-15.md)
- [research/03_audits/audit-round1-quant_2026-04-15.md](../../research/03_audits/audit-round1-quant_2026-04-15.md)

## 11. AI-assistance statement

Draft produced by the execution-research agent (Claude Opus 4.6, 1M context) under the `audit-remediate-loop` pattern (CLAUDE.md §Agentic Iteration). Role: synthesis of prior arch survey, decision drafting, citation retrieval. No measurements were executed by the agent; all latency values remain TBD pending the §5 protocol run by the user. Per ICMJE (Jan 2026), AI is not an author; this statement satisfies disclosure.
