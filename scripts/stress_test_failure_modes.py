"""Synthetic-failure-mode stress test harness — CLI entrypoint per ADR-0017 §6.

Loads a per-trade R-multiple sequence (from a walk-forward run output, or a
synthetic baseline for sanity-checking) plus the kill-switch parameters from
the hypothesis design.md §11.1, runs the 5 FM-1..FM-5 stress tests, and writes
a deterministic JSON results file.

Usage (synthetic-baseline mode; for sanity-checking the simulator):
    python scripts/stress_test_failure_modes.py \\
        --hypothesis H055 \\
        --config config/hypotheses/H055.yaml \\
        --out artifacts/stress_test/H055_stress_test.json \\
        --synthetic

Usage (empirical mode; ingests post-walk-forward IS-fold output):
    python scripts/stress_test_failure_modes.py \\
        --hypothesis H055 \\
        --config config/hypotheses/H055.yaml \\
        --walk-forward-output runs/H055/<run_id>/ \\
        --out artifacts/stress_test/H055_stress_test.json

Per ADR-0017 §6, pass criteria are NOT binding gates per ADR-0013 §1+§2 no-gates
philosophy. Failures emit `stress-test-FM-N-fail` annotations to be recorded in
the per-hypothesis failure_log.md per ADR-0013 §4.2.

Implementation per `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`
(BLOCKING-BEFORE-LAUNCH per ADR-0017 §6).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from skie_ninja.backtest.stress_test import (
    KillSwitchParams,
    StressTestResult,
    TradeEvent,
    run_all_failure_mode_stress_tests,
)


def _load_kill_switch_params(config_path: Path) -> KillSwitchParams:
    """Load K-1+K-6+K-7 from hypothesis YAML config.

    Reads ``kill_switch:`` block (optional). Falls back to project-canonical
    defaults per ADR-0017 §5 if any field is absent.
    """
    if not config_path.exists():
        return KillSwitchParams()
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    kill_switch_cfg = cfg.get("kill_switch", {}) or {}
    return KillSwitchParams(
        per_trade_stop_r=float(kill_switch_cfg.get("per_trade_stop_r", 1.0)),
        daily_circuit_breaker_fraction=float(
            kill_switch_cfg.get("daily_circuit_breaker_fraction", -0.02)
        ),
        weekly_circuit_breaker_fraction=float(
            kill_switch_cfg.get("weekly_circuit_breaker_fraction", -0.05)
        ),
    )


def _generate_synthetic_trades(
    n_trades: int = 200,
    *,
    rng_seed: int = 20260508,
    mean_r: float = 0.1,
    sd_r: float = 1.0,
    win_prob: float = 0.55,
) -> list[TradeEvent]:
    """Generate a synthetic per-trade sequence for sanity-checking the simulator.

    Trades are spread across consecutive sessions (1 trade per session,
    5 sessions per week). The default distribution is a +0.1R-mean Gaussian
    mixture of winners and losers with 55% win rate.
    """
    rng = np.random.default_rng(rng_seed)
    trades: list[TradeEvent] = []
    for i in range(n_trades):
        is_winner = rng.random() < win_prob
        r = float(rng.normal(mean_r if is_winner else -mean_r, sd_r))
        trades.append(TradeEvent(r_value=r, session_id=i, week_id=i // 5))
    return trades


def _load_empirical_trades(walk_forward_output_dir: Path) -> list[TradeEvent]:
    """Load empirical per-trade R-multiples from a walk-forward run output.

    Reads ``trades.parquet`` (or ``trades.csv`` fallback) under the run
    directory. Required columns: ``r_value``, ``session_id``, ``week_id``.

    Pending standardisation under `P1-WALK-FORWARD-PER-TRADE-LEDGER-SCHEMA`
    (BLOCKING-BEFORE-EMPIRICAL-MODE-FIRST-USE). At this primitive's land time,
    the H055 walk-forward orchestrator does not yet emit a per-trade ledger;
    empirical mode requires the ledger to be wired (cross-link to A2
    `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`).
    """
    raise NotImplementedError(
        "Empirical mode requires the walk-forward per-trade-ledger schema to "
        "be wired (`P1-WALK-FORWARD-PER-TRADE-LEDGER-SCHEMA`); pending under "
        "the A2 `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` follow-up. Use "
        "--synthetic in the meantime for simulator sanity-checking."
    )


def _result_to_jsonable(result: StressTestResult) -> dict[str, Any]:
    """Convert a StressTestResult to a JSON-serialisable dict."""
    d = dataclasses.asdict(result)
    d["triggered_kill_switches"] = list(result.triggered_kill_switches)
    return d


def _payload_sha256(payload: dict[str, Any]) -> str:
    """SHA256 over the canonical-JSON-encoded payload (sort_keys=True)."""
    serialised = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialised).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hypothesis", required=True, help="Hypothesis ID (e.g., H055)")
    parser.add_argument("--config", required=True, help="Path to hypothesis config YAML")
    parser.add_argument("--out", required=True, help="Output JSON path for results")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Use synthetic baseline (sanity-check mode); cannot be combined with "
        "--walk-forward-output",
    )
    parser.add_argument(
        "--walk-forward-output",
        type=str,
        default=None,
        help="Path to walk-forward run output dir (empirical mode)",
    )
    parser.add_argument(
        "--starting-equity",
        type=float,
        default=10_000.0,
        help="Starting equity (default $10,000 per ADR-0013 §3.1)",
    )
    parser.add_argument(
        "--risk-budget-pct",
        type=float,
        default=0.01,
        help=(
            "Per-trade dollars-at-risk fraction of equity (default 0.01 = "
            "Turtle 1%% per Faith 2007 *practitioner*, ISBN 978-0071486644)"
        ),
    )
    parser.add_argument(
        "--rng-seed",
        type=int,
        default=20260508,
        help="Deterministic RNG seed (default ADR-0017 design date)",
    )
    parser.add_argument(
        "--n-synthetic-trades",
        type=int,
        default=200,
        help="Number of synthetic trades when --synthetic is set",
    )
    args = parser.parse_args()

    if args.synthetic and args.walk_forward_output:
        print(
            "error: --synthetic and --walk-forward-output are mutually exclusive",
            file=sys.stderr,
        )
        return 2
    if not args.synthetic and not args.walk_forward_output:
        print(
            "error: one of --synthetic or --walk-forward-output is required",
            file=sys.stderr,
        )
        return 2

    config_path = Path(args.config)
    if not config_path.exists():
        # R-4 fix: fail loud on missing config — silent fallback to in-code
        # defaults undermines the audit-trail discipline of CLAUDE.md
        # §"Reproducibility (hook-enforced)".
        print(
            f"error: config file not found at {config_path.as_posix()}; "
            "no silent fallback to defaults — supply a valid hypothesis YAML "
            "(per ADR-0017 §5 + H055 §11.1).",
            file=sys.stderr,
        )
        return 2
    kill_switch_params = _load_kill_switch_params(config_path)

    if args.synthetic:
        trades = _generate_synthetic_trades(
            n_trades=args.n_synthetic_trades, rng_seed=args.rng_seed
        )
        input_mode = "synthetic"
    else:
        trades = _load_empirical_trades(Path(args.walk_forward_output))
        input_mode = "empirical"

    results = run_all_failure_mode_stress_tests(
        trades,
        starting_equity=args.starting_equity,
        risk_budget_pct=args.risk_budget_pct,
        kill_switch_params=kill_switch_params,
        rng_seed=args.rng_seed,
    )

    payload: dict[str, Any] = {
        "hypothesis_id": args.hypothesis,
        # R-1 fix: as_posix() for cross-platform-stable canonical-JSON SHA.
        "config_path": config_path.as_posix(),
        "input_mode": input_mode,
        "starting_equity": args.starting_equity,
        "risk_budget_pct": args.risk_budget_pct,
        "rng_seed": args.rng_seed,
        "n_trades": len(trades),
        "kill_switch_params": dataclasses.asdict(kill_switch_params),
        "results": {
            fm_id: _result_to_jsonable(result) for fm_id, result in results.items()
        },
        "summary": {
            "all_passed": all(r.passed for r in results.values()),
            "n_passed": sum(1 for r in results.values() if r.passed),
            "n_failed": sum(1 for r in results.values() if not r.passed),
            "failed_ids": [fm_id for fm_id, r in results.items() if not r.passed],
        },
    }
    payload["payload_sha256"] = _payload_sha256(
        {k: v for k, v in payload.items() if k != "payload_sha256"}
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=2)

    print(
        f"FM stress test ({input_mode}): "
        f"{payload['summary']['n_passed']}/5 passed; "
        f"failed={payload['summary']['failed_ids']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
