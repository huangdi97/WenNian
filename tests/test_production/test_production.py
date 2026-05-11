"""Tests for production modules — verify hard switch, safe fallback, GMP."""

import pytest
from src.production import PATMonitor
from src.production.bioreactor_controller import BioreactorController
from src.production.livca_estimator import estimate_livca, build_mcb_wcb_timeline
from src.production.process_trajectory import (
    predict_quality_trajectory, evaluate_process_capability,
)


class TestPATMonitor:
    def test_read_sensors_normal(self):
        pat = PATMonitor(enable_write=False)
        reading = pat.read_sensors()
        assert reading["status"] == "normal"
        assert reading["senescence_proxy"] >= 0

    def test_read_sensors_abnormal(self):
        pat = PATMonitor(enable_write=False)
        reading = pat.read_sensors(temperature=39.0, viability=80)
        assert reading["status"] == "warning"
        assert len(reading["flags"]) > 0

    def test_write_rejected_by_default(self):
        pat = PATMonitor(enable_write=False)
        result = pat.adjust_parameters(temperature=38.0)
        assert result["status"] == "rejected"
        assert "硬开关" in result["reason"]

    def test_write_allowed_when_enabled(self):
        pat = PATMonitor(enable_write=True)
        result = pat.adjust_parameters(temperature=38.0)
        assert result["status"] == "applied"

    def test_hard_switch_cannot_be_bypassed(self):
        pat = PATMonitor(enable_write=False)
        # Direct attribute access
        assert pat._enable_write == False
        # The property reflects the actual state
        assert pat.write_enabled == False
        # Write should be rejected regardless
        result = pat.adjust_parameters(temperature=38.0)
        assert result["status"] == "rejected"

    def test_generate_pat_report(self):
        pat = PATMonitor(enable_write=False)
        pat.read_sensors()
        report = pat.generate_pat_report()
        assert "PAT" in report
        assert "读写开关" in report
        assert "🔒" in report or "已锁定" in report

    def test_alerts_accumulated(self):
        pat = PATMonitor(enable_write=False)
        pat.read_sensors(temperature=39.0, viability=70)
        pat.read_sensors(ph=7.8)
        assert len(pat.get_alerts()) == 2


class TestBioreactorController:
    def test_write_protected(self):
        bc = BioreactorController(enable_write=False)
        result = bc.set_parameters({"temperature": 38.0}, operator_id="op1")
        assert result["status"] == "rejected"

    def test_write_enabled(self):
        bc = BioreactorController(enable_write=True)
        result = bc.set_parameters({"temperature": 38.0}, operator_id="op1", reason="test")
        assert result["status"] == "applied"

    def test_advisories(self):
        bc = BioreactorController(enable_write=False)
        result = bc.update_sensors({"temperature": 35.0, "ph": 6.5, "dissolved_oxygen": 20})
        assert len(result["advisories"]) > 0

    def test_emergency_shutdown(self):
        bc = BioreactorController(enable_write=False)
        result = bc.emergency_shutdown("op1")
        assert result["status"] == "shutdown"
        assert bc.get_state()["temperature"] == 20.0

    def test_gmp_compliance(self):
        bc = BioreactorController(enable_write=False)
        compliance = bc.validate_gmp_compliance()
        assert compliance["gmp_compliant"]

    def test_audit_log(self):
        bc = BioreactorController(enable_write=True)
        bc.set_parameters({"temperature": 38.0}, operator_id="op1", reason="test")
        log = bc.get_audit_log()
        assert len(log) > 0
        assert "op1" in str(log)

    def test_write_false_is_safe(self):
        bc = BioreactorController(enable_write=False)
        assert bc.write_enabled == False
        result = bc.set_parameters({"temperature": 99.0})
        assert result["status"] == "rejected"
        assert bc.get_state()["temperature"] == 37.0  # Unchanged


class TestLIVCA:
    def test_estimate_early(self):
        result = estimate_livca(10, [10.0, 12.0, 15.0])
        assert result.remaining_passages > 0
        assert result.livca_score < 100

    def test_estimate_late(self):
        result = estimate_livca(40, [50.0, 53.0, 57.0])
        assert result.remaining_passages < 20
        assert "寿命" in result.recommendation or "生产" in result.recommendation

    def test_single_passage(self):
        result = estimate_livca(10, [20.0])
        assert "需要至少2个" in result.recommendation

    def test_build_timeline(self):
        timeline = build_mcb_wcb_timeline()
        assert timeline["mcb"]["passage"] == 5
        assert timeline["wcb"]["passage"] == 15
        assert timeline["safety_margin"] >= 0


class TestProcessTrajectory:
    def test_predict_trajectory(self):
        result = predict_quality_trajectory(
            current_passage=10,
            csi_values=[10.0, 15.0, 20.0],
            quality_attributes=[{"titer": 1.0, "purity": 0.95}],
        )
        assert "predictions" in result
        assert len(result["predictions"]) > 0
        assert "recommendation" in result

    def test_evaluate_capability_excellent(self):
        quality_data = [{"purity": 0.96}, {"purity": 0.97}, {"purity": 0.96}, {"purity": 0.97}, {"purity": 0.96}]
        specs = {"purity": (0.90, 1.00)}
        result = evaluate_process_capability(quality_data, specs)
        assert result["overall_cpk"] > 1.0
        assert result["overall_capability"] in ("优秀", "可接受")

    def test_evaluate_capability_empty(self):
        result = evaluate_process_capability([], {"purity": (0.9, 1.0)})
        assert "error" in result
