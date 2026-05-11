"""Tests for InputValidator."""

import pytest
from src.validation.input_validator import InputValidator, ValidationResult


class TestInputValidator:
    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_valid_input(self, validator, sample_biomarkers):
        result = validator.validate(sample_biomarkers)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_hard_limit_rejection(self, validator):
        result = validator.validate({
            "age": 200.0,
            "albumin": 43.0,
        })
        assert not result.is_valid
        assert any("age" in e for e in result.errors)

    def test_glucose_extreme(self, validator):
        result = validator.validate({
            "age": 40,
            "glucose": 100.0,  # > 50 mmol/L hard limit
        })
        assert not result.is_valid

    def test_soft_warning(self, validator):
        result = validator.validate({
            "age": 40,
            "albumin": 15.0,  # Below soft threshold of 30
        })
        assert result.is_valid  # Still valid
        assert len(result.warnings) > 0
        assert any("albumin" in w for w in result.warnings)

    def test_soft_warning_high(self, validator):
        result = validator.validate({
            "age": 40,
            "glucose": 9.0,  # Above soft threshold of 8.0
        })
        assert any("glucose" in w for w in result.warnings)

    def test_alt_bilirubin_contradiction(self, validator):
        result = validator.validate({
            "age": 40,
            "alt": 250.0,
            "bilirubin": 10.0,
        })
        assert any("ALT" in c for c in result.contradictions)

    def test_bp_inversion_contradiction(self, validator):
        result = validator.validate({
            "age": 40,
            "systolic_bp": 80.0,
            "diastolic_bp": 120.0,
        })
        assert any("systolic" in c.lower() for c in result.contradictions)

    def test_ldl_greater_than_total(self, validator):
        result = validator.validate({
            "age": 40,
            "cholesterol_total": 4.0,
            "ldl": 5.0,
        })
        assert any("LDL" in c for c in result.contradictions)

    def test_non_numeric_value(self, validator):
        result = validator.validate({
            "age": "forty",
        })
        assert not result.is_valid
        assert any("age" in e for e in result.errors)
