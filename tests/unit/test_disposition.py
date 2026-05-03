"""ADR-0012 disposition framework unit tests.

Verifies the three-class rubric primitives:
- annotate_sharpe (qualitative annotation function)
- ar1_lag1_benchmark_returns (AR(1) bench per `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE`)
- max_dd_ratio_kpi (max-DD ratio + annotation)
- power_margin_kpi (power-margin ratio + annotation)
- evaluate_class_a_gates (Class A gate evaluation with applicability)
- determine_disposition_class (strict-precedence flow)
- compose_disposition (full DispositionResult builder)
- emit_promotion_log (promotion log artifact)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from skie_ninja.inference.disposition import (
    DISPOSITION_ARCHIVE_COMPLETE,
    DISPOSITION_CALIBRATION_FAILED,
    DISPOSITION_LEAKAGE_DETECTED,
    DISPOSITION_PREREQUISITE_NOT_MET,
    DISPOSITION_REPRO_INCOMPLETE,
    ClassAGateApplicability,
    ClassAGateVerdicts,
    ClassBKPIReportCard,
    ClassCDocumentation,
    SharpeKPI,
    annotate_sharpe,
    ar1_lag1_benchmark_returns,
    compose_disposition,
    determine_disposition_class,
    emit_promotion_log,
    max_dd_ratio_kpi,
    power_margin_kpi,
)


# ---------------------------------------------------------------------------
# annotate_sharpe — qualitative-only per ADR-0012 + Round-1 audit F-1-4
# ---------------------------------------------------------------------------


class TestAnnotateSharpe:
    def test_positive_when_ci_excludes_zero_above(self):
        assert annotate_sharpe(0.10, 0.05, 0.15) == "positive"

    def test_marginal_when_ci_covers_zero_point_above(self):
        assert annotate_sharpe(0.05, -0.05, 0.15) == "marginal"

    def test_flat_when_point_near_zero(self):
        assert annotate_sharpe(0.0, -0.10, 0.10) == "flat"
        assert annotate_sharpe(1e-12, -0.10, 0.10) == "flat"

    def test_negative_when_point_below_zero(self):
        assert annotate_sharpe(-0.10, -0.20, 0.0) == "negative"
        assert annotate_sharpe(-0.10, -0.20, 0.05) == "negative"


# ---------------------------------------------------------------------------
# ar1_lag1_benchmark_returns — AR(1) lag-1 bench per ADR-0012 Class B
# ---------------------------------------------------------------------------


class TestAR1Lag1Benchmark:
    def test_positive_prev_returns_test_y(self):
        test_y = np.array([0.01, -0.02])
        test_y_prev = np.array([0.005, 0.01])
        out = ar1_lag1_benchmark_returns(test_y, test_y_prev)
        np.testing.assert_array_equal(out, np.array([0.01, -0.02]))

    def test_negative_prev_flips_sign(self):
        test_y = np.array([0.01, -0.02])
        test_y_prev = np.array([-0.005, -0.01])
        out = ar1_lag1_benchmark_returns(test_y, test_y_prev)
        np.testing.assert_array_equal(out, np.array([-0.01, 0.02]))

    def test_zero_prev_yields_zero(self):
        out = ar1_lag1_benchmark_returns(np.array([0.05]), np.array([0.0]))
        np.testing.assert_array_equal(out, np.array([0.0]))

    def test_nan_prev_yields_zero(self):
        out = ar1_lag1_benchmark_returns(np.array([0.05]), np.array([np.nan]))
        np.testing.assert_array_equal(out, np.array([0.0]))


# ---------------------------------------------------------------------------
# max_dd_ratio_kpi
# ---------------------------------------------------------------------------


class TestMaxDDRatio:
    def test_favorable_when_arm_dd_smaller(self):
        arm = np.array([0.01, -0.02, 0.005])
        passive = np.array([0.02, -0.10, 0.03])
        ratio, ann = max_dd_ratio_kpi(arm, passive)
        assert ann == "favorable"
        assert 0 < ratio < 0.9

    def test_comparable_when_arm_dd_close_to_passive(self):
        arm = np.array([0.01, -0.05, 0.02])
        passive = np.array([0.01, -0.05, 0.02])
        ratio, ann = max_dd_ratio_kpi(arm, passive)
        assert ann == "comparable"
        assert abs(ratio - 1.0) < 1e-9

    def test_adverse_when_arm_dd_larger(self):
        arm = np.array([0.01, -0.20, 0.02])
        passive = np.array([0.01, -0.05, 0.02])
        ratio, ann = max_dd_ratio_kpi(arm, passive)
        assert ann == "adverse"
        assert ratio > 1.1


# ---------------------------------------------------------------------------
# power_margin_kpi
# ---------------------------------------------------------------------------


class TestPowerMargin:
    def test_adequate_when_oos_meets_required(self):
        ratio, ann = power_margin_kpi(620, 620)
        assert ann == "adequate"
        assert ratio == 1.0

    def test_marginal_when_half_to_full_required(self):
        ratio, ann = power_margin_kpi(310, 620)  # 0.5
        assert ann == "marginal"

    def test_low_when_below_half_required(self):
        ratio, ann = power_margin_kpi(100, 620)
        assert ann == "low"


# ---------------------------------------------------------------------------
# determine_disposition_class — strict precedence per ADR-0012 §10.1
# ---------------------------------------------------------------------------


def _make_verdicts(
    *,
    pit_passed=True,
    bss_value=0.05,
    bss_passed=True,
    reliability_value=1.0,
    reliability_passed=True,
    repro_present=True,
    dsr_value=None,
    dsr_passed=None,
):
    return ClassAGateVerdicts(
        pit_canary_passed=pit_passed,
        pit_canary_test_count=14,
        pit_canary_test_path="tests/integration/test_h053_pit_canaries.py",
        bss_value=bss_value,
        bss_passed=bss_passed,
        reliability_slope_value=reliability_value,
        reliability_slope_passed=reliability_passed,
        repro_log_present=repro_present,
        dsr_value=dsr_value,
        dsr_passed=dsr_passed,
        all_applicable_gates_passed=(pit_passed and repro_present and (bss_passed is not False) and (reliability_passed is not False)),
    )


class TestDetermineDispositionClass:
    def test_archive_complete_when_all_pass(self):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts()
        assert determine_disposition_class(verdicts=v, applicability=appl) == DISPOSITION_ARCHIVE_COMPLETE

    def test_leakage_detected_when_pit_fails(self):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts(pit_passed=False)
        assert determine_disposition_class(verdicts=v, applicability=appl) == DISPOSITION_LEAKAGE_DETECTED

    def test_repro_incomplete_when_log_missing(self):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts(repro_present=False)
        assert determine_disposition_class(verdicts=v, applicability=appl) == DISPOSITION_REPRO_INCOMPLETE

    def test_calibration_failed_when_bss_negative(self):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts(bss_value=-0.5, bss_passed=False)
        assert determine_disposition_class(verdicts=v, applicability=appl) == DISPOSITION_CALIBRATION_FAILED

    def test_calibration_not_failed_when_bss_negative_but_not_applicable(self):
        # H050/H051/H052a/H052b case: BSS not applicable for continuous-output hypotheses
        appl = ClassAGateApplicability(bss_applicable=False, reliability_slope_applicable=False)
        v = _make_verdicts(bss_value=-0.5, bss_passed=None)  # None when not applicable
        assert determine_disposition_class(verdicts=v, applicability=appl) == DISPOSITION_ARCHIVE_COMPLETE

    def test_prerequisite_not_met_blocks_archive(self):
        appl = ClassAGateApplicability(bss_applicable=False, reliability_slope_applicable=False)
        v = _make_verdicts()
        assert (
            determine_disposition_class(
                verdicts=v, applicability=appl, prerequisite_met=False
            )
            == DISPOSITION_PREREQUISITE_NOT_MET
        )

    def test_pit_failure_takes_precedence_over_calibration(self):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts(pit_passed=False, bss_passed=False)
        # PIT failure beats calibration failure in strict precedence
        assert determine_disposition_class(verdicts=v, applicability=appl) == DISPOSITION_LEAKAGE_DETECTED


# ---------------------------------------------------------------------------
# compose_disposition + paper_trade_eligibility
# ---------------------------------------------------------------------------


def _make_kpis(
    *,
    sharpe_passive_ann="positive",
    sharpe_bench_ann="positive",
    spa_ann="spa-passes",
    max_dd_ann="favorable",
):
    sharpe_passive = SharpeKPI(0.20, 0.05, 0.35, True, 489, sharpe_passive_ann)
    sharpe_bench = SharpeKPI(0.10, 0.0, 0.20, True, 489, sharpe_bench_ann)
    return ClassBKPIReportCard(
        sharpe_vs_passive=sharpe_passive,
        sharpe_vs_bench=sharpe_bench,
        spa_family_p=0.02,
        spa_family_annotation=spa_ann,
        max_dd_ratio=0.7,
        max_dd_annotation=max_dd_ann,
        power_margin_ratio=1.0,
        power_margin_annotation="adequate",
        mediation_nie_significant=None,
        mediation_nde_significant=None,
        partial_r2_value=None,
        partial_r2_annotation="not-computed",
        cost_floor_annotation="not-evaluated",
    )


def _make_doc(tmp_path: Path):
    return ClassCDocumentation(
        audit_trail_link="docs/audits/audit_trail_2026-05-01_disposition-philosophy-shift.md",
        substrate_dataset_checksum="bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665",
        pit_canary_suite_path="tests/integration/test_h053_pit_canaries.py",
        repro_log_path=str(tmp_path / "fake_repro.json"),
    )


class TestComposeDisposition:
    def test_paper_trade_eligible_when_all_promotion_criteria_met(self, tmp_path: Path):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts()
        kpis = _make_kpis()
        doc = _make_doc(tmp_path)
        result = compose_disposition(
            hypothesis_id="H053", arm_id="arm1_elasticnet", run_id="testrun001",
            applicability=appl, verdicts=v, kpis=kpis, documentation=doc,
        )
        assert result.disposition_class == DISPOSITION_ARCHIVE_COMPLETE
        assert result.paper_trade_eligible is True

    def test_not_paper_trade_eligible_when_sharpe_negative(self, tmp_path: Path):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts()
        kpis = _make_kpis(sharpe_passive_ann="negative")
        doc = _make_doc(tmp_path)
        result = compose_disposition(
            hypothesis_id="H053", arm_id="arm1_elasticnet", run_id="testrun002",
            applicability=appl, verdicts=v, kpis=kpis, documentation=doc,
        )
        assert result.disposition_class == DISPOSITION_ARCHIVE_COMPLETE
        # Disposition is archive(complete) but auto-promotion is NOT eligible
        assert result.paper_trade_eligible is False

    def test_not_paper_trade_eligible_when_spa_rejects(self, tmp_path: Path):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts()
        kpis = _make_kpis(spa_ann="spa-rejects")
        doc = _make_doc(tmp_path)
        result = compose_disposition(
            hypothesis_id="H053", arm_id="arm1_elasticnet", run_id="testrun003",
            applicability=appl, verdicts=v, kpis=kpis, documentation=doc,
        )
        assert result.paper_trade_eligible is False

    def test_not_paper_trade_eligible_when_max_dd_adverse(self, tmp_path: Path):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts()
        kpis = _make_kpis(max_dd_ann="adverse")
        doc = _make_doc(tmp_path)
        result = compose_disposition(
            hypothesis_id="H053", arm_id="arm1_elasticnet", run_id="testrun004",
            applicability=appl, verdicts=v, kpis=kpis, documentation=doc,
        )
        assert result.paper_trade_eligible is False


# ---------------------------------------------------------------------------
# emit_promotion_log
# ---------------------------------------------------------------------------


class TestEmitPromotionLog:
    def test_promotion_log_emitted_with_all_fields(self, tmp_path: Path):
        appl = ClassAGateApplicability(bss_applicable=True, reliability_slope_applicable=True)
        v = _make_verdicts()
        kpis = _make_kpis()
        doc = _make_doc(tmp_path)
        result = compose_disposition(
            hypothesis_id="H053", arm_id="arm1_elasticnet", run_id="testrun010",
            applicability=appl, verdicts=v, kpis=kpis, documentation=doc,
        )
        out_path = emit_promotion_log(result=result, promotion_dir=tmp_path / "promotions")
        assert out_path.exists()
        assert out_path.name == "testrun010_H053_arm1_elasticnet_promotion.md"
        content = out_path.read_text(encoding="utf-8")
        # Sanity check for key fields
        assert "disposition_class:" in content
        assert "Class A gate verdicts" in content
        assert "Class B KPI report card" in content
        assert "Operator decision" in content
        assert "spa-passes" in content
        assert "PROMOTE" in content
        assert "DEFER" in content
