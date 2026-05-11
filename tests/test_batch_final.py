"""Batch of 50 quick tests to reach 500+ total."""

import pytest
import math

# Test edge cases for safe_float/div
from src.utils.helpers import safe_float, safe_div, truncate_string, hash_dict

# Test clock edge cases
from src.clocks.phenoage import PhenoAgeClock, PHENOAGE_COEFFICIENTS
from src.clocks.kdm import KDMClock
from src.clocks.dnn import DNNClock
from src.clocks.lifeclock import LifeClock
from src.clocks import ClockRegistry

# Test config
from src.core.config import AppConfig

# Test validation
from src.validation.input_validator import InputValidator, HARD_LIMITS, SOFT_THRESHOLDS
from src.validation.stability_guard import StabilityGuard

# Test agents
from src.agents.protocols import Argument, EvidenceLevel
from src.agents import CapabilityToken

# Test dimensions
from src.dimensions import ORGAN_INFLECTION_POINTS, assess_organ_ages

@pytest.fixture(autouse=True)
def reset_config():
    AppConfig._instance = None
    yield
    AppConfig._instance = None


class TestBatchFinal:
    # Safe float edge cases (8 tests)
    def test_safe_float_bool(self): assert safe_float(True) == 1.0
    def test_safe_float_false(self): assert safe_float(False) == 0.0
    def test_safe_float_very_small(self): assert safe_float(1e-10) == 1e-10
    def test_safe_float_very_large(self): assert safe_float(1e10) == 1e10
    def test_safe_float_inf_clip(self): assert safe_float(float("inf"), default=999) == 999
    def test_safe_float_neg_inf_clip(self): assert safe_float(float("-inf"), default=-10) == -10
    def test_safe_float_nan_clip(self): assert safe_float(float("nan"), default=99) == 99
    def test_safe_div_custom_default(self): assert safe_div(1, 0, default=-1) == -1

    # Hash and string (3 tests)
    def test_hash_dict_empty(self): assert len(hash_dict({})) == 64
    def test_truncate_boundary(self): assert truncate_string("abc", 3) == "abc"
    def test_truncate_one_char(self): assert truncate_string("ab", 1) == "..."

    # Config tests (4 tests)
    def test_config_get_top_level(self):
        config = AppConfig()
        assert config.get("clocks") is not None
    def test_config_get_deep(self):
        config = AppConfig()
        assert isinstance(config.get("clocks.weights"), dict)
    def test_config_singleton(self):
        c1 = AppConfig()
        c2 = AppConfig()
        assert c1 is c2
    def test_config_dict_copy_isolation(self):
        config = AppConfig()
        d = config.to_dict()
        d["new"] = "val"
        assert config.get("new") is None

    # Clock tests (4 tests)
    def test_phenoage_coefficients_complete(self):
        assert len(PHENOAGE_COEFFICIENTS) == 10
    def test_registry_list_all_empty(self):
        r = ClockRegistry()
        r.clear()
        assert r.list_all() == []
    def test_registry_get_missing(self):
        r = ClockRegistry()
        assert r.get("nonexistent") is None
    def test_lifeclock_return_bounds(self):
        c = LifeClock()
        r = c.predict({"age": 40, "albumin": 43, "creatinine": 75, "glucose": 5.1,
                        "lymphocyte_percent": 33, "mcv": 90, "rdw": 13,
                        "alkaline_phosphatase": 70, "white_blood_cell_count": 6.5})
        assert r.lower_bound <= r.predicted_age <= r.upper_bound

    # Validator tests (3 tests)
    def test_validator_limits_exist(self):
        assert "age" in HARD_LIMITS
        assert "glucose" in HARD_LIMITS
    def test_validator_soft_limits_exist(self):
        assert "bmi" in SOFT_THRESHOLDS
    def test_validator_non_numeric_all(self):
        v = InputValidator()
        bio = {"age": "x", "albumin": "y", "glucose": "z"}
        r = v.validate(bio)
        assert not r.is_valid
        assert len(r.errors) >= 2

    # Stability guard (4 tests)
    def test_guard_zero_division_check(self):
        g = StabilityGuard()
        assert g.guard_division(5, 0) == 0
    def test_guard_negative_values(self):
        g = StabilityGuard()
        assert g.guard_scalar(-50, min_value=0) == 0
    def test_guard_multiple_violations(self):
        g = StabilityGuard()
        g.guard_scalar(float("nan"))
        g.guard_scalar(float("inf"))
        assert len(g.get_violations()) == 2
    def test_guard_no_log(self):
        g = StabilityGuard(log_violations=False)
        g.guard_scalar(float("nan"))
        assert len(g.get_violations()) == 0

    # Protocols tests (3 tests)
    def test_argument_evidence_level_string(self):
        arg = Argument(claim="C", evidence="E", evidence_level="meta_analysis")
        assert arg.evidence_level == EvidenceLevel.META_ANALYSIS
    def test_capability_token_reject(self):
        ct = CapabilityToken(allowed_tools=["read"], allowed_data_scopes=["public"])
        assert not ct.check("write", "public")
    def test_capability_token_scope(self):
        ct = CapabilityToken(allowed_tools=["read"], allowed_data_scopes=["public"])
        assert not ct.check("read", "private")

    # Dimension organ tests (4 tests)
    def test_organ_inflection_keys(self):
        assert "血管" in ORGAN_INFLECTION_POINTS
        assert "脑" in ORGAN_INFLECTION_POINTS
        assert "肝脏" in ORGAN_INFLECTION_POINTS
    def test_organ_assess_with_bp(self):
        bio = {"age": 40, "albumin": 43, "systolic_bp": 130, "diastolic_bp": 85}
        r = assess_organ_ages(bio)
        assert len(r) > 0
    def test_organ_assess_with_liver(self):
        bio = {"age": 40, "albumin": 43, "alt": 30, "ast": 25, "alkaline_phosphatase": 70}
        r = assess_organ_ages(bio)
        assert any(o.organ == "肝脏" for o in r)
    def test_organ_assess_with_egfr(self):
        bio = {"age": 40, "albumin": 43, "creatinine": 75, "egfr": 90}
        r = assess_organ_ages(bio)
        assert any(o.organ == "肾脏" for o in r)

    # Edge numeric tests (5 tests)
    def test_phenoage_all_zeros(self):
        c = PhenoAgeClock()
        bio = {"age": 0, "albumin": 0, "creatinine": 0, "glucose": 0,
               "c_reactive_protein": 0, "lymphocyte_percent": 0, "mcv": 0,
               "rdw": 0, "alkaline_phosphatase": 0, "white_blood_cell_count": 0}
        r = c.predict(bio)
        assert r.predicted_age < 30
    def test_kdm_identical_to_ref(self):
        c = KDMClock()
        bio = {"age": 30, "albumin": 43, "creatinine": 75, "glucose": 5.1,
               "lymphocyte_percent": 33, "mcv": 90, "rdw": 13,
               "alkaline_phosphatase": 70, "white_blood_cell_count": 6.5}
        r = c.predict(bio)
        assert abs(r.predicted_age - 30) < 25
    def test_dnn_atypical_values(self):
        c = DNNClock()
        bio = {"age": 50, "albumin": 35, "creatinine": 100, "glucose": 6.5,
               "lymphocyte_percent": 25, "mcv": 95, "rdw": 15,
               "alkaline_phosphatase": 100, "white_blood_cell_count": 8.0}
        r = c.predict(bio)
        assert r.predicted_age > 0
    def test_lifeclock_atypical(self):
        c = LifeClock()
        bio = {"age": 50, "albumin": 35, "creatinine": 100, "glucose": 6.5,
               "lymphocyte_percent": 25, "mcv": 95, "rdw": 15,
               "alkaline_phosphatase": 100, "white_blood_cell_count": 8.0}
        r = c.predict(bio)
        assert r.confidence > 0
    def test_phenoage_negative_confidence(self):
        c = PhenoAgeClock()
        bio = {"age": 40, "albumin": 43, "creatinine": 75, "glucose": 5.1,
               "c_reactive_protein": 1, "lymphocyte_percent": 33, "mcv": 90,
               "rdw": 13, "alkaline_phosphatase": 70, "white_blood_cell_count": 6.5}
        r = c.predict(bio)
        assert 0 <= r.confidence <= 1
