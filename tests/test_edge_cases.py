"""Additional edge case and boundary tests for Stage 1-4 modules."""

import pytest
import math
from src.clocks import ClockRegistry, ClockResult
from src.clocks.phenoage import PhenoAgeClock
from src.clocks.kdm import KDMClock
from src.clocks.dnn import DNNClock
from src.clocks.lifeclock import LifeClock
from src.core.exceptions import ComputationError, ValidationError
from src.validation.input_validator import InputValidator
from src.agents.auditor import Auditor
from src.integrator import AgingIntegrator


class TestClockEdgeCases:
    def test_phenoage_boundary_age(self):
        clock = PhenoAgeClock()
        bio = {"age": 0, "albumin": 35, "creatinine": 50, "glucose": 3.9,
               "c_reactive_protein": 0, "lymphocyte_percent": 20, "mcv": 80,
               "rdw": 11.5, "alkaline_phosphatase": 40, "white_blood_cell_count": 4.0}
        result = clock.predict(bio)
        assert result.predicted_age > 0

    def test_phenoage_elderly(self):
        clock = PhenoAgeClock()
        bio = {"age": 100, "albumin": 30, "creatinine": 120, "glucose": 7.0,
               "c_reactive_protein": 5, "lymphocyte_percent": 15, "mcv": 100,
               "rdw": 16, "alkaline_phosphatase": 150, "white_blood_cell_count": 10.0}
        result = clock.predict(bio)
        # Elderly with poor markers should show elevated biological age
        assert result.predicted_age > 30

    def test_kdm_with_custom_reference(self):
        clock = KDMClock(ref_means={"albumin": 40}, ref_stds={"albumin": 5})
        bio = {"age": 40, "albumin": 35, "creatinine": 75, "glucose": 5.1,
               "lymphocyte_percent": 33, "mcv": 90, "rdw": 13,
               "alkaline_phosphatase": 70, "white_blood_cell_count": 6.5}
        result = clock.predict(bio)
        assert result.predicted_age > 0

    def test_lifeclock_very_young(self):
        clock = LifeClock()
        bio = {"age": 18, "albumin": 46, "creatinine": 55, "glucose": 4.5,
               "lymphocyte_percent": 38, "mcv": 86, "rdw": 12,
               "alkaline_phosphatase": 50, "white_blood_cell_count": 5.5}
        result = clock.predict(bio)
        assert result.predicted_age >= 18

    def test_dnn_fallback_with_path(self):
        clock = DNNClock(model_path="nonexistent.pt")
        assert clock._using_fallback
        bio = {"age": 40, "albumin": 43, "creatinine": 75, "glucose": 5.1,
               "lymphocyte_percent": 33, "mcv": 90, "rdw": 13,
               "alkaline_phosphatase": 70, "white_blood_cell_count": 6.5}
        result = clock.predict(bio)
        assert result.confidence > 0

    def test_registry_clear_and_register(self):
        registry = ClockRegistry()
        registry.clear()
        registry.register(phenoage=PhenoAgeClock())
        assert "phenoage" in registry.list_all()
        registry.unregister("phenoage")
        assert "phenoage" not in registry.list_all()


class TestValidatorEdgeCases:
    def test_extreme_albumin_hard_limit(self):
        v = InputValidator()
        result = v.validate({"age": 40, "albumin": 0})
        assert not result.is_valid

    def test_contradiction_hdl_ldl_total(self):
        v = InputValidator()
        result = v.validate({"age": 40, "cholesterol_total": 4.0, "hdl": 3.0, "ldl": 3.0})
        assert any("HDL" in c or "LDL" in c for c in result.contradictions)

    def test_contradiction_egfr_creatinine(self):
        v = InputValidator()
        result = v.validate({"age": 40, "egfr": 5, "creatinine": 60})
        assert len(result.contradictions) > 0

    def test_valid_with_all_optional(self):
        v = InputValidator()
        bio = {"age": 40, "albumin": 43, "systolic_bp": 120, "diastolic_bp": 80,
               "cholesterol_total": 4.5, "hdl": 1.3, "ldl": 2.5}
        result = v.validate(bio)
        assert result.is_valid


class TestAuditorEdgeCases:
    def test_multiple_violations(self):
        auditor = Auditor()
        output = auditor.execute({
            "report_text": "建议服用XX，推荐用药YY，无需医生",
            "biological_age": 42, "chronological_age": 40,
        })
        assert not output.data["passed"]
        assert len(output.data["violations"]) >= 2

    def test_clean_report_with_disclaimer(self):
        auditor = Auditor()
        output = auditor.execute({
            "report_text": "评估结果: 生物年龄42岁。免责声明: 不构成医疗诊断。",
            "biological_age": 42, "chronological_age": 40,
        })
        assert output.data["passed"]


class TestIntegratorEdgeCases:
    def test_empty_registry_assess(self):
        registry = ClockRegistry()
        registry.clear()
        integrator = AgingIntegrator(registry=registry)
        with pytest.raises(ComputationError):
            integrator.assess({"age": 40})

    def test_custom_weights_apply(self, sample_biomarkers, populated_registry):
        integrator = AgingIntegrator(registry=populated_registry, weights={"phenoage": 5.0})
        result = integrator.assess(sample_biomarkers)
        assert result.biological_age > 0
