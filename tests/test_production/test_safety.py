"""Additional production and safety tests."""

import pytest
from src.production import PATMonitor, ENABLE_WRITE
from src.production.bioreactor_controller import BioreactorController
from src.production.livca_estimator import estimate_livca, build_mcb_wcb_timeline
from src.production.process_trajectory import predict_quality_trajectory, evaluate_process_capability


class TestProductionSafety:
    def test_module_level_enable_write_false(self):
        assert ENABLE_WRITE == False

    def test_pat_cannot_bypass_via_constructor_default(self):
        pat = PATMonitor()  # default enable_write=False
        assert pat.write_enabled == False
        result = pat.adjust_parameters(temperature=38.0)
        assert result["status"] == "rejected"

    def test_bioreactor_cannot_bypass_default(self):
        bc = BioreactorController()  # default enable_write=False
        assert bc.write_enabled == False
        result = bc.set_parameters({"temperature": 38.0})
        assert result["status"] == "rejected"

    def test_emergency_shutdown_always_works(self):
        bc = BioreactorController(enable_write=False)
        result = bc.emergency_shutdown("op1")
        assert result["status"] == "shutdown"

    def test_audit_trail_integrity(self):
        bc = BioreactorController(enable_write=True)
        bc.set_parameters({"temperature": 37.5}, operator_id="op1", reason="adjust")
        bc.set_parameters({"ph": 7.1}, operator_id="op2", reason="correct")
        log = bc.get_audit_log()
        assert len(log) == 2
        assert log[0]["operator"] == "op1"

    def test_gmp_compliance_write_enabled_fails(self):
        bc = BioreactorController(enable_write=True)
        compliance = bc.validate_gmp_compliance()
        assert not compliance["gmp_compliant"]
        assert not compliance["checks"]["write_protection"]["passed"]

    def test_livca_zero_rate(self):
        result = estimate_livca(10, [10.0, 10.0, 10.0])
        assert result.remaining_passages > 0

    def test_process_trajectory_cpk_calculation(self):
        quality = [{"purity": 0.95}, {"purity": 0.96}, {"purity": 0.94},
                    {"purity": 0.97}, {"purity": 0.95}, {"purity": 0.96}]
        specs = {"purity": (0.90, 1.00)}
        result = evaluate_process_capability(quality, specs)
        assert result["overall_cpk"] > 1.0

    def test_mcb_wcb_safety_margin(self):
        timeline = build_mcb_wcb_timeline(
            mcb_passage=5, wcb_passage=15, production_window=20,
            estimated_total_lifespan=40
        )
        assert timeline["safety_margin"] >= 0
        assert timeline["end_of_life"]["passage"] >= timeline["mcb"]["passage"]
