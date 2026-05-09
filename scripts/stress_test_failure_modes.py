"""Synthetic-failure-mode stress test harness per ADR-0017 §6.

Five synthetic failure modes evaluated against the §5 K-1..K-8 hard kill-switch
constraints:

- FM-1 — Death by thousand cuts: replace per-trade losses with -0.25R losses
  in larger quantity; preserves total $-loss but spreads across more entries.
  Pass criterion: K-6 daily circuit breaker fires before week-end.
- FM-2 — Gap-overnight: inject overnight gap = -3 ATR on a held position
  from one session to the next. Pass criterion: K-1 per-trade $-stop fires
  at session open; realized loss bounded at 1R + slippage.
- FM-3 — News-spike: inject 5σ adverse return in a 1-min bar during an
  active position. Pass criterion: either K-1 fires (bounded loss) or the
  news-calendar §4 eligible-bar filter prevents entry in the news window.
- FM-4 — Latency-induced bad fill: inject 2-tick adverse slippage on every
  entry and exit. Pass criterion: cost-floor sensitivity exhibit per
  design.md §14 (cost_mult = 2.0) demonstrates strategy survives elevated
  cost regime.
- FM-5 — Regime change mid-trade: inject structural break in per-session
  return distribution at OOS-window midpoint. Pass criterion: either the
  strategy's regime-conditioning catches the break OR K-7 weekly circuit
  breaker fires before cumulative damage exceeds 5% of equity.

The stress test is implemented per `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §6).

Pass criteria are NOT binding gates per ADR-0013 §1+§2 no-gates philosophy.
A strategy failing one or more stress tests records a methodological-correctness
annotation `stress-test-FM-N-fail` with the offending behavior enumerated in
the failure_log.md per ADR-0013 §4.2. Operator-discretionary review at
promotion time decides remediation timing.

Usage:
    python scripts/stress_test_failure_modes.py \\
        --hypothesis H055 \\
        --config config/hypotheses/H055.yaml \\
        --out artifacts/stress_test/H055_stress_test.json

Pending implementation per `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    """Stress-test entrypoint stub.

    Pending implementation per `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`.
    Returns nonzero exit code; CLI surface defined here to lock the
    interface contract before BLOCKING-before-launch implementation.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hypothesis", required=True, help="Hypothesis ID (e.g., H055)")
    parser.add_argument("--config", required=True, help="Path to hypothesis config YAML")
    parser.add_argument("--out", required=True, help="Output JSON path for stress-test results")
    args = parser.parse_args()  # noqa: F841 — interface lock

    raise NotImplementedError(
        "P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE pending; "
        "5 synthetic failure modes (FM-1..FM-5) per ADR-0017 §6"
    )


if __name__ == "__main__":
    sys.exit(main())
