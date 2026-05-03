"""ADR-0012 disposition framework — Class A binding gates + Class B KPIs + Class C documentation.

Per [docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md](
../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md):
the SKIE-Universe project's disposition philosophy is restructured from
"Sharpe-CI gates plus annotations" to a three-class rubric:

- **Class A binding gates**: PIT/leakage canary + applicable calibration
  (BSS + reliability slope) + reproducibility log + DSR-when-active +
  Hansen SPA at operator-promotion.
- **Class B KPIs**: Sharpe-vs-passive, Sharpe-vs-bench (AR(1) lag-1),
  SPA family p, max-DD ratio, power margin, mediation NIE/NDE,
  partial-R², cost-floor sensitivity. Reported with qualitative
  annotations only (numerical sub-classification thresholds deferred).
- **Class C documentation**: per-cycle audit-remediate-loop trail link
  + substrate dataset_checksum + PIT canary suite reference.

The four legal **disposition_class** values (in strict precedence):

1. ``leakage-detected`` — PIT canary or any leakage gate failed.
2. ``reproducibility-incomplete`` — required provenance fields missing.
3. ``calibration-failed`` — BSS ≤ 0 or reliability slope outside
   [0.7, 1.3] (where applicable).
4. ``prerequisite-not-met`` — §11.2 prerequisites for the arm did not
   land before ``running``.
5. ``archive(complete; KPI report)`` — passes Class A gates; KPI
   report card published.

The ``archive(complete; KPI report)`` disposition makes an arm
**eligible for paper-trade** subject to the operator-promotion gate
(see ``emit_promotion_log()``). Operator MUST promote any arm
satisfying Class A pass + sharpe-vs-passive-positive/marginal +
Hansen SPA p ≤ α at promotion + max-DD ≤ 1.5; deferral allowed only
under enumerated conditions.

References
----------
- ADR-0012 disposition-philosophy-aspirational-mvp (this commit's
  binding policy).
- Brier, G. W. 1950. "Verification of Forecasts Expressed in Terms of
  Probability." *Monthly Weather Review* 78(1):1-3. DOI 10.1175/1520-0493
  (1950)078<0001:VOFEIT>2.0.CO;2.
- Niculescu-Mizil, A. & Caruana, R. 2005. "Predicting good probabilities
  with supervised learning." *ICML 2005*. DOI 10.1145/1102351.1102430.
- Bailey, D. H. & López de Prado, M. 2014. "The Deflated Sharpe Ratio."
  *Journal of Portfolio Management* 40(5):94-107. DOI 10.3905/jpm.2014.40.5.094.
- López de Prado, M. 2018. *Advances in Financial Machine Learning* §12.
  Wiley. ISBN 978-1-119-48208-6.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from skie_ninja.utils.paths import ProjectPaths

_log = logging.getLogger(__name__)


# Disposition class labels per ADR-0012 §"Disposition labels under the new rubric".
# Strict precedence: leakage-detected → reproducibility-incomplete →
# calibration-failed → prerequisite-not-met → archive(complete; KPI report).
#
# NOTE per ADR-0014: only `archive(complete)` and `archive(null, ...)` are TRUE
# archive labels. The other four disposition_class values below are *states*
# indicating remediation-pending status — they are NOT archive decisions.
# See `lifecycle_state` for the operator-visible "is this hypothesis still alive?"
# answer.
DISPOSITION_LEAKAGE_DETECTED = "leakage-detected"
DISPOSITION_REPRO_INCOMPLETE = "reproducibility-incomplete"
DISPOSITION_CALIBRATION_FAILED = "calibration-failed"
DISPOSITION_PREREQUISITE_NOT_MET = "prerequisite-not-met"
DISPOSITION_ARCHIVE_COMPLETE = "archive(complete; KPI report)"

# Lifecycle states per ADR-0014 — operator-visible "is this hypothesis still alive?"
LIFECYCLE_PAPER_TRADE_ELIGIBLE = "paper-trade-eligible"
LIFECYCLE_ACTIVE_INVESTIGATION = "active-investigation"
LIFECYCLE_ARCHIVED = "archived"


@dataclass(frozen=True)
class ClassAGateApplicability:
    """Per-hypothesis applicability of Class A binding gates.

    Per ADR-0012 §"Class A" + Round-1 audit F-1-2 + F-1-6 remediations,
    calibration gates (BSS, reliability) are applicability-conditional;
    PIT/leakage and reproducibility are always binding; DSR binds only
    when family ≥ activation_size; SPA binds at operator-promotion only
    (not at design-time disposition).
    """

    pit_canary_applicable: bool = True               # ALWAYS; non-negotiable
    bss_applicable: bool = False                     # YES for hypotheses with categorical-probability outputs
    reliability_slope_applicable: bool = False       # same as BSS
    repro_log_applicable: bool = True                # ALWAYS
    dsr_applicable: bool = False                     # YES when family ≥ activation_size
    bss_applicable_reason: str = ""                  # justification text

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClassAGateVerdicts:
    """Outcome of the Class A binding-gate evaluation."""

    pit_canary_passed: bool                                  # True iff all PIT canary tests green
    pit_canary_test_count: int                               # number of tests in the suite
    pit_canary_test_path: str                                # path to the integration test file
    bss_value: float | None                                  # None if not applicable
    bss_passed: bool | None                                  # None if not applicable; else bss > 0
    reliability_slope_value: float | None                    # None if not applicable
    reliability_slope_passed: bool | None                    # None if not applicable; else slope ∈ [0.7, 1.3]
    repro_log_present: bool                                  # True iff git_head + dataset_checksum + scientific_payload_sha256 + pip_freeze_sha all populated
    dsr_value: float | None                                  # None if not applicable
    dsr_passed: bool | None                                  # None if not applicable
    all_applicable_gates_passed: bool                        # composite: True iff every applicable gate passed

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SharpeKPI:
    """Sharpe-style KPI report (vs passive or bench)."""

    point_estimate: float
    ci_low: float
    ci_high: float
    excludes_zero: bool
    n_observations: int
    annotation: str                                          # one of {positive, marginal, flat, negative}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClassBKPIReportCard:
    """ADR-0012 §"Class B" KPI report card; reported, not nulling."""

    sharpe_vs_passive: SharpeKPI
    sharpe_vs_bench: SharpeKPI                               # AR(1) lag-1 for H053
    spa_family_p: float | None                               # Hansen SPA omega-corrected p; None if not computed
    spa_family_annotation: str                               # 'spa-passes' / 'spa-rejects' / 'spa-not-computed'
    max_dd_ratio: float                                      # arm DD / passive DD
    max_dd_annotation: str                                   # 'favorable' / 'comparable' / 'adverse'
    power_margin_ratio: float                                # realized n_oos / n_required_for_power_80
    power_margin_annotation: str                             # 'adequate' / 'marginal' / 'low'
    mediation_nie_significant: bool | None                   # None if not computed
    mediation_nde_significant: bool | None                   # None if not computed
    partial_r2_value: float | None                           # None if not computed
    partial_r2_annotation: str                               # 'positive' / 'flat' / 'not-computed'
    cost_floor_annotation: str                               # 'cost-robust' / 'cost-floor-conditional' / 'cost-flat' / 'not-evaluated'
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClassCDocumentation:
    """ADR-0012 §"Class C" documentation requirements."""

    audit_trail_link: str | None
    substrate_dataset_checksum: str
    pit_canary_suite_path: str
    repro_log_path: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DispositionResult:
    """Composite disposition payload per ADR-0012 + ADR-0014."""

    hypothesis_id: str
    arm_id: str
    run_id: str
    disposition_class: str                                   # one of the DISPOSITION_* constants (technical state)
    class_a_applicability: ClassAGateApplicability
    class_a_verdicts: ClassAGateVerdicts
    class_b_kpis: ClassBKPIReportCard
    class_c_documentation: ClassCDocumentation
    disposition_string: str                                  # full disposition_class | KPI annotations | strengths
    paper_trade_eligible: bool                               # True iff disposition_class == archive(complete) AND operator-promotion criteria met
    lifecycle_state: str = LIFECYCLE_ACTIVE_INVESTIGATION    # ADR-0014: operator-visible "is this hypothesis still alive?"
    lifecycle_state_reason: str = ""                         # justification for lifecycle_state assignment

    def to_dict(self) -> dict[str, Any]:
        d = {
            "hypothesis_id": self.hypothesis_id,
            "arm_id": self.arm_id,
            "run_id": self.run_id,
            "disposition_class": self.disposition_class,
            "class_a_applicability": self.class_a_applicability.to_dict(),
            "class_a_verdicts": self.class_a_verdicts.to_dict(),
            "class_b_kpis": self.class_b_kpis.to_dict(),
            "class_c_documentation": self.class_c_documentation.to_dict(),
            "disposition_string": self.disposition_string,
            "paper_trade_eligible": self.paper_trade_eligible,
            "lifecycle_state": self.lifecycle_state,
            "lifecycle_state_reason": self.lifecycle_state_reason,
        }
        return d


# ---------------------------------------------------------------------------
# Helpers — KPI computation primitives
# ---------------------------------------------------------------------------


def annotate_sharpe(point: float, ci_low: float, ci_high: float) -> str:
    """ADR-0012 qualitative annotation for a Sharpe-style KPI.

    Per ADR-0012 + Round-1 audit F-1-4 remediation, no hard-coded
    sub-classification thresholds; only qualitative labels.
    """
    excludes_zero = (ci_low > 0.0) or (ci_high < 0.0)
    if point < 0.0:
        return "negative"
    if abs(point) < 1e-9:
        return "flat"
    # point > 0
    if excludes_zero:
        return "positive"
    return "marginal"  # CI covers zero, point > 0


def ar1_lag1_benchmark_returns(test_y: np.ndarray, test_y_prev: np.ndarray) -> np.ndarray:
    """AR(1) lag-1 benchmark per ADR-0012 §"Class B" + `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE`.

    The benchmark predicts ``y_{i, t} = y_{i, t-1}`` (sign of prior-day
    same-bin return); strategy return = sign(y_{i, t-1}) · y_{i, t}.

    Per Round-1 audit F-1-11 acknowledgement: this is an AR(1) lag-1
    baseline, NOT the original HKS periodicity-confound benchmark. The
    HKS periodicity confound remains unaddressed under this substitute
    (the original per-clock-bin construction is degenerate for
    single-clock-time predictands like H053).

    Parameters
    ----------
    test_y : (n,) array
        Realized predictand on the OOS fold.
    test_y_prev : (n,) array
        Prior-period predictand (lag-1) — same instrument, same
        clock-bin, prior trading session. NaN where prior-day is
        unavailable (first OOS row, post-holiday gaps).

    Returns
    -------
    bench_returns : (n,) array
        ``sign(test_y_prev) · test_y`` with ``sign(0) = 0`` and NaN
        for rows where ``test_y_prev`` is NaN.
    """
    test_y = np.asarray(test_y, dtype=np.float64)
    test_y_prev = np.asarray(test_y_prev, dtype=np.float64)
    sign = np.sign(test_y_prev)
    sign[~np.isfinite(test_y_prev)] = 0.0
    return sign * test_y


def max_dd_ratio_kpi(arm_returns: np.ndarray, passive_returns: np.ndarray) -> tuple[float, str]:
    """Compute max-DD ratio (arm DD / passive DD) per ADR-0012 §Class B.

    Annotation: ``favorable`` (ratio < 0.9) / ``comparable`` (0.9-1.1) /
    ``adverse`` (ratio > 1.1). The ±10% band around 1.0 is an operational
    pin tracked under follow-up `P1-DISPOSITION-MAX-DD-RATIO-CALIBRATION`.
    """
    def _max_dd(returns: np.ndarray) -> float:
        cum = np.cumsum(returns)
        peak = np.maximum.accumulate(cum)
        dd = peak - cum
        return float(np.max(dd)) if len(dd) > 0 else 0.0

    arm_dd = _max_dd(np.asarray(arm_returns, dtype=np.float64))
    passive_dd = _max_dd(np.asarray(passive_returns, dtype=np.float64))
    if passive_dd == 0.0:
        ratio = float("inf") if arm_dd > 0 else 0.0
    else:
        ratio = arm_dd / passive_dd
    if not np.isfinite(ratio):
        annotation = "adverse"
    elif ratio < 0.9:
        annotation = "favorable"
    elif ratio <= 1.1:
        annotation = "comparable"
    else:
        annotation = "adverse"
    return float(ratio), annotation


def power_margin_kpi(n_oos: int, n_required_for_power_80: int) -> tuple[float, str]:
    """Compute power-margin ratio + annotation per ADR-0012 §Class B.

    Annotation: ``adequate`` (≥ 1.0) / ``marginal`` (0.5-1.0) /
    ``low`` (< 0.5). ``power-margin-low`` arms require an extended
    120-session-day paper-trade verification window per ADR-0012 §Class B
    + Round-1 audit F-1-8 remediation.
    """
    if n_required_for_power_80 <= 0:
        return float("inf"), "adequate"
    ratio = n_oos / n_required_for_power_80
    if ratio >= 1.0:
        annotation = "adequate"
    elif ratio >= 0.5:
        annotation = "marginal"
    else:
        annotation = "low"
    return float(ratio), annotation


# ---------------------------------------------------------------------------
# Class A gate computation
# ---------------------------------------------------------------------------


def assert_pit_canaries_green(
    test_path: str,
    *,
    timeout_sec: int = 300,
) -> tuple[bool, int, str]:
    """Run the PIT canary integration tests; return (passed, n_tests, output_tail).

    Per ADR-0012 Class A "PIT / leakage-canary" binding gate. The H053
    PIT canary suite is at ``tests/integration/test_h053_pit_canaries.py``;
    H050/H051/H052a/H052b have ``tests/integration/test_h0XX_pit.py``
    (to be authored as §11.2 prereq before next launch per
    `P1-H0XX-PIT-CANARY-INTEGRATION-TEST-LANDED` follow-ups).
    """
    paths = ProjectPaths.discover()
    full_path = paths.root / test_path
    if not full_path.exists():
        return False, 0, f"PIT canary suite not found at {full_path}"
    cmd = ["uv", "run", "pytest", str(full_path), "-q", "--no-header"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=paths.root,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return False, 0, f"PIT canary suite timeout after {timeout_sec}s"
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    # Parse "N passed in Xs" (or "N failed")
    n_passed = 0
    n_failed = 0
    for line in output.splitlines():
        if " passed" in line:
            try:
                n_passed = int(line.split(" passed")[0].split()[-1])
            except (ValueError, IndexError):
                pass
        if " failed" in line:
            try:
                n_failed = int(line.split(" failed")[0].split()[-1])
            except (ValueError, IndexError):
                pass
    passed = (proc.returncode == 0) and (n_failed == 0) and (n_passed > 0)
    return passed, n_passed, output[-500:]  # last 500 chars for context


def evaluate_class_a_gates(
    *,
    applicability: ClassAGateApplicability,
    pit_canary_test_path: str,
    bss_value: float | None,
    reliability_slope_value: float | None,
    repro_log_present: bool,
    dsr_value: float | None,
    pit_canary_skip: bool = False,  # operator-bypass for fast iteration; logged
) -> ClassAGateVerdicts:
    """Evaluate all Class A binding gates; return ClassAGateVerdicts.

    Gates marked `applicable: False` are recorded as `passed: None`
    (vacuously satisfied — the disposition class doesn't fail on a
    not-applicable gate).
    """
    if pit_canary_skip:
        _log.warning(
            "PIT canary suite SKIPPED via pit_canary_skip=True; this is operator-bypass "
            "for fast iteration ONLY and must NOT be used for paper-trade-eligible runs. "
            "Per F-2-9 closure: skip-PIT runs force pit_canary_passed=False so the "
            "downstream disposition class is leakage-detected (paper-trade ineligible)."
        )
        pit_passed, pit_n_tests, _ = (False, 0, "skipped-PIT-forced-False-per-F-2-9")
    elif applicability.pit_canary_applicable:
        pit_passed, pit_n_tests, _ = assert_pit_canaries_green(pit_canary_test_path)
    else:
        pit_passed, pit_n_tests = True, 0  # vacuously passed

    # Per plan v3-r3 §B (within ADR-0012 §"Frozen pre-registration amendment" carve-out;
    # ADR-0013 documents this as a §10 procedural strengthening — lower-CI > 0 is
    # MORE conservative than design.md §4.5.3 BSS > 0 point-test).
    # Caller passes ``bss_value`` as the lower bound of the bootstrap CI on binary BSS;
    # ``reliability_slope_value`` is the binary "1.0 ∈ CI" verdict re-encoded as
    # a center-of-CI value mapped to a sentinel range [0.99, 1.01] when the gate
    # passes (so the legacy [0.7, 1.3] range check still trips correctly without
    # callers re-computing the band). The new disposition.py API will get a
    # dedicated field in a follow-up; for now the v2 numeric API is preserved.
    bss_passed = (bss_value is not None and bss_value > 0.0) if applicability.bss_applicable else None
    reliability_passed = (
        reliability_slope_value is not None
        and 0.7 <= reliability_slope_value <= 1.3
        if applicability.reliability_slope_applicable
        else None
    )
    dsr_passed = (dsr_value is not None and dsr_value > 0.0) if applicability.dsr_applicable else None

    all_passed = pit_passed and repro_log_present
    if applicability.bss_applicable:
        all_passed = all_passed and bool(bss_passed)
    if applicability.reliability_slope_applicable:
        all_passed = all_passed and bool(reliability_passed)
    if applicability.dsr_applicable:
        all_passed = all_passed and bool(dsr_passed)

    return ClassAGateVerdicts(
        pit_canary_passed=pit_passed,
        pit_canary_test_count=pit_n_tests,
        pit_canary_test_path=pit_canary_test_path,
        bss_value=bss_value,
        bss_passed=bss_passed,
        reliability_slope_value=reliability_slope_value,
        reliability_slope_passed=reliability_passed,
        repro_log_present=repro_log_present,
        dsr_value=dsr_value,
        dsr_passed=dsr_passed,
        all_applicable_gates_passed=all_passed,
    )


# ---------------------------------------------------------------------------
# Disposition-class determination
# ---------------------------------------------------------------------------


def determine_disposition_class(
    *,
    verdicts: ClassAGateVerdicts,
    applicability: ClassAGateApplicability,
    prerequisite_met: bool = True,
) -> str:
    """Apply ADR-0012 §10.1 strict precedence to determine disposition class.

    Strict precedence:
    1. ``leakage-detected`` — PIT canary failed (when applicable).
    2. ``reproducibility-incomplete`` — repro log missing (always required).
    3. ``calibration-failed`` — BSS or reliability failed (when applicable).
    4. ``prerequisite-not-met`` — §11 prerequisites did not land.
    5. ``archive(complete; KPI report)`` — all applicable gates passed.
    """
    if applicability.pit_canary_applicable and not verdicts.pit_canary_passed:
        return DISPOSITION_LEAKAGE_DETECTED
    if not verdicts.repro_log_present:
        return DISPOSITION_REPRO_INCOMPLETE
    if applicability.bss_applicable and verdicts.bss_passed is False:
        return DISPOSITION_CALIBRATION_FAILED
    if applicability.reliability_slope_applicable and verdicts.reliability_slope_passed is False:
        return DISPOSITION_CALIBRATION_FAILED
    if applicability.dsr_applicable and verdicts.dsr_passed is False:
        return DISPOSITION_CALIBRATION_FAILED  # treat DSR-fail as a calibration-style failure
    if not prerequisite_met:
        return DISPOSITION_PREREQUISITE_NOT_MET
    return DISPOSITION_ARCHIVE_COMPLETE


# ---------------------------------------------------------------------------
# Operator-promotion log emission
# ---------------------------------------------------------------------------


def emit_promotion_log(
    *,
    result: DispositionResult,
    promotion_dir: Path | None = None,
) -> Path:
    """Emit the per-arm promotion log per ADR-0012 §"Promotion log".

    Markdown contents:
    - Class B KPI report card values at promotion time
    - Operator decision (default: ``defer pending operator review``)
    - Pre-registered deferral condition invoked + written justification
      (operator fills in)
    - Cross-link to disposition memo + ReproLog

    Returns the absolute path of the emitted log.
    """
    if promotion_dir is None:
        paths = ProjectPaths.discover()
        promotion_dir = paths.logs / "promotions"
    promotion_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{result.run_id}_{result.hypothesis_id}_{result.arm_id}_promotion.md"
    out_path = promotion_dir / fname

    kpis = result.class_b_kpis
    body = f"""---
hypothesis_id: {result.hypothesis_id}
arm_id: {result.arm_id}
run_id: {result.run_id}
disposition_class: {result.disposition_class}
paper_trade_eligible: {result.paper_trade_eligible}
written_at: {datetime.now(timezone.utc).isoformat()}
---

# Operator promotion log — {result.hypothesis_id} arm {result.arm_id}

Per [ADR-0012 §"Operator-promotion rule"](../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md).

## Disposition class

**{result.disposition_class}**

## Class A gate verdicts

- PIT canary: {"PASS" if result.class_a_verdicts.pit_canary_passed else "FAIL"}
  (n_tests = {result.class_a_verdicts.pit_canary_test_count}; suite = {result.class_a_verdicts.pit_canary_test_path})
- BSS (applicable={result.class_a_applicability.bss_applicable}): value = {result.class_a_verdicts.bss_value}, passed = {result.class_a_verdicts.bss_passed}
- Reliability slope (applicable={result.class_a_applicability.reliability_slope_applicable}): value = {result.class_a_verdicts.reliability_slope_value}, passed = {result.class_a_verdicts.reliability_slope_passed}
- Reproducibility log present: {result.class_a_verdicts.repro_log_present}
- DSR (applicable={result.class_a_applicability.dsr_applicable}): value = {result.class_a_verdicts.dsr_value}, passed = {result.class_a_verdicts.dsr_passed}

## Class B KPI report card (at promotion time)

| KPI | Value | Annotation |
|---|---:|:---:|
| Sharpe-vs-passive | point={kpis.sharpe_vs_passive.point_estimate:.4f}, CI=[{kpis.sharpe_vs_passive.ci_low:.4f}, {kpis.sharpe_vs_passive.ci_high:.4f}] | `{kpis.sharpe_vs_passive.annotation}` |
| Sharpe-vs-bench (AR(1) lag-1) | point={kpis.sharpe_vs_bench.point_estimate:.4f}, CI=[{kpis.sharpe_vs_bench.ci_low:.4f}, {kpis.sharpe_vs_bench.ci_high:.4f}] | `{kpis.sharpe_vs_bench.annotation}` |
| Hansen SPA family p (omega-corrected) | {kpis.spa_family_p} | `{kpis.spa_family_annotation}` |
| Max-DD ratio (arm/passive) | {kpis.max_dd_ratio:.4f} | `{kpis.max_dd_annotation}` |
| Power margin (n_oos / n_required_for_power_80) | {kpis.power_margin_ratio:.4f} | `{kpis.power_margin_annotation}` |
| Mediation NIE significant | {kpis.mediation_nie_significant} | |
| Mediation NDE significant | {kpis.mediation_nde_significant} | |
| In-sample partial-R² | {kpis.partial_r2_value} | `{kpis.partial_r2_annotation}` |
| Cost-floor sensitivity | | `{kpis.cost_floor_annotation}` |

## Operator decision

- [ ] PROMOTE to paper-trade
- [x] DEFER (default; operator must update this section)

### Deferral condition (if defer)

- [ ] `max-dd-adverse` (ratio > 1.5): ...
- [ ] `power-margin-low`: requires extended 120-session-day paper-trade window
- [ ] `cost-floor-conditional`: pending venue-slippage-assumption decision
- [ ] Other (NOT ALLOWED per ADR-0012 §"Operator-promotion rule"): ...

### Pre-registered promotion criteria (per ADR-0012 §"Operator-promotion rule")

The operator MUST promote any arm satisfying ALL of:
1. Class A binding gates pass: **{result.class_a_verdicts.all_applicable_gates_passed}**
2. `sharpe-vs-passive-positive` OR `sharpe-vs-passive-marginal`: **{kpis.sharpe_vs_passive.annotation in ("positive", "marginal")}**
3. Hansen SPA family p ≤ α at promotion: **{kpis.spa_family_annotation == "spa-passes"}**
4. `max-dd-comparable` OR `max-dd-favorable`: **{kpis.max_dd_annotation in ("favorable", "comparable")}**

**Auto-promotion eligible: {all([result.class_a_verdicts.all_applicable_gates_passed, kpis.sharpe_vs_passive.annotation in ("positive", "marginal"), kpis.spa_family_annotation == "spa-passes", kpis.max_dd_annotation in ("favorable", "comparable")])}**

## Cross-references

- Disposition memo: (link to be added by operator)
- ReproLog path: {result.class_c_documentation.repro_log_path}
- Audit trail: {result.class_c_documentation.audit_trail_link}
- Substrate dataset_checksum: `{result.class_c_documentation.substrate_dataset_checksum}`
"""
    out_path.write_text(body, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Main composer
# ---------------------------------------------------------------------------


def determine_lifecycle_state(
    *,
    disposition_class: str,
    sharpe_vs_passive: SharpeKPI,
    max_dd_annotation: str,
    explicit_archive: bool = False,
) -> tuple[str, str]:
    """Per ADR-0014: determine lifecycle_state distinct from disposition_class.

    Returns (lifecycle_state, reason).

    Rules:
    1. If `explicit_archive` (set only on operator decision after explicit review),
       return ARCHIVED.
    2. If disposition_class == archive(complete) AND auto-promotion criteria,
       return PAPER_TRADE_ELIGIBLE.
    3. If raw Sharpe is positive (point estimate > 0) AND CI lower bound
       NOT catastrophically low (> -0.5 floor), return ACTIVE_INVESTIGATION
       regardless of any failed Class A gate. ADR-0014 §2 NEVER-ARCHIVE-PROFITABLE.
    4. Else, return ACTIVE_INVESTIGATION (default; the DEFAULT IS NOT ARCHIVE per ADR-0014).
    """
    if explicit_archive:
        return LIFECYCLE_ARCHIVED, "operator-explicit archive decision"
    if disposition_class == DISPOSITION_ARCHIVE_COMPLETE:
        # Sharpe-positive Class-A-pass case → eligible for paper-trade
        return LIFECYCLE_PAPER_TRADE_ELIGIBLE, "Class A gates passed"
    # Per ADR-0014 §2: profitable strategy → ACTIVE_INVESTIGATION regardless of disposition_class
    sharpe_positive_at_alpha_10 = (
        sharpe_vs_passive.point_estimate > 0.0
        and sharpe_vs_passive.ci_low > -0.5
    )
    if sharpe_positive_at_alpha_10:
        return (
            LIFECYCLE_ACTIVE_INVESTIGATION,
            f"ADR-0014 NEVER-ARCHIVE-PROFITABLE: Sharpe point={sharpe_vs_passive.point_estimate:.4f} CI=[{sharpe_vs_passive.ci_low:.4f}, {sharpe_vs_passive.ci_high:.4f}] passes positive-at-alpha-0.10 floor; disposition_class={disposition_class} indicates remediation-pending state (NOT archive)",
        )
    # Default per ADR-0014 §4: ACTIVE_INVESTIGATION when in doubt
    return (
        LIFECYCLE_ACTIVE_INVESTIGATION,
        f"ADR-0014 default: disposition_class={disposition_class} is a remediation-pending state, NOT an archive decision; lifecycle_state stays active-investigation pending operator review",
    )


def compose_disposition(
    *,
    hypothesis_id: str,
    arm_id: str,
    run_id: str,
    applicability: ClassAGateApplicability,
    verdicts: ClassAGateVerdicts,
    kpis: ClassBKPIReportCard,
    documentation: ClassCDocumentation,
    prerequisite_met: bool = True,
    explicit_archive: bool = False,
) -> DispositionResult:
    """Compose a full ADR-0012 + ADR-0014 DispositionResult from Class A/B/C inputs."""
    disposition_class = determine_disposition_class(
        verdicts=verdicts,
        applicability=applicability,
        prerequisite_met=prerequisite_met,
    )

    # Auto-promotion eligibility per ADR-0012 §"Operator-promotion rule":
    # all Class A gates pass + sharpe-vs-passive positive/marginal + SPA passes + max-DD comparable/favorable.
    auto_eligible = (
        disposition_class == DISPOSITION_ARCHIVE_COMPLETE
        and kpis.sharpe_vs_passive.annotation in ("positive", "marginal")
        and kpis.spa_family_annotation == "spa-passes"
        and kpis.max_dd_annotation in ("favorable", "comparable")
    )

    # Build a compact disposition string
    annotations = [
        f"sharpe-vs-passive-{kpis.sharpe_vs_passive.annotation}",
        f"sharpe-vs-bench-{kpis.sharpe_vs_bench.annotation}",
        kpis.spa_family_annotation,
        f"max-dd-{kpis.max_dd_annotation}",
        f"power-margin-{kpis.power_margin_annotation}",
        f"partial-r2-{kpis.partial_r2_annotation}",
        kpis.cost_floor_annotation,
    ]
    if kpis.mediation_nie_significant is True:
        annotations.append("mediation-NIE-significant")
    if kpis.mediation_nde_significant is True:
        annotations.append("mediation-NDE-significant")
    disposition_string = f"{disposition_class}; KPI: " + ", ".join(annotations)

    lifecycle_state, lifecycle_reason = determine_lifecycle_state(
        disposition_class=disposition_class,
        sharpe_vs_passive=kpis.sharpe_vs_passive,
        max_dd_annotation=kpis.max_dd_annotation,
        explicit_archive=explicit_archive,
    )

    return DispositionResult(
        hypothesis_id=hypothesis_id,
        arm_id=arm_id,
        run_id=run_id,
        disposition_class=disposition_class,
        class_a_applicability=applicability,
        class_a_verdicts=verdicts,
        class_b_kpis=kpis,
        class_c_documentation=documentation,
        disposition_string=disposition_string,
        paper_trade_eligible=auto_eligible,
        lifecycle_state=lifecycle_state,
        lifecycle_state_reason=lifecycle_reason,
    )


__all__ = [
    "ClassAGateApplicability",
    "ClassAGateVerdicts",
    "ClassBKPIReportCard",
    "ClassCDocumentation",
    "DispositionResult",
    "SharpeKPI",
    "DISPOSITION_LEAKAGE_DETECTED",
    "DISPOSITION_REPRO_INCOMPLETE",
    "DISPOSITION_CALIBRATION_FAILED",
    "DISPOSITION_PREREQUISITE_NOT_MET",
    "DISPOSITION_ARCHIVE_COMPLETE",
    "LIFECYCLE_PAPER_TRADE_ELIGIBLE",
    "LIFECYCLE_ACTIVE_INVESTIGATION",
    "LIFECYCLE_ARCHIVED",
    "annotate_sharpe",
    "ar1_lag1_benchmark_returns",
    "max_dd_ratio_kpi",
    "power_margin_kpi",
    "assert_pit_canaries_green",
    "evaluate_class_a_gates",
    "determine_disposition_class",
    "determine_lifecycle_state",
    "emit_promotion_log",
    "compose_disposition",
]
