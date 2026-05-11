"""Tests for cell assay module."""

import pytest
from src.industrial.cell_assay import (
    compute_senescence_score, compute_treatment_effect,
    validate_positive_control, CellSenescenceResult,
)


class TestCellAssay:
    def test_compute_young_cells(self):
        result = compute_senescence_score("sample1", p16=1.0, p21=1.0)
        assert isinstance(result, CellSenescenceResult)
        assert result.sbi_index >= 0
        assert result.classification == "低衰老负荷"

    def test_compute_senescent_cells(self):
        result = compute_senescence_score(
            "old_sample",
            p16=5.0, p21=4.0,
            sasp_il6=6.0, sasp_il8=5.0, sasp_mmp3=4.0,
            gamma_h2ax=3.0, sa_beta_gal=4.0,
        )
        assert result.sbi_index > 50

    def test_treatment_effect(self):
        untreated = compute_senescence_score("ctrl",
            p16=5.0, p21=4.0, sasp_il6=6.0, sasp_il8=5.0, sasp_mmp3=4.0)
        treated = compute_senescence_score("treated",
            p16=3.0, p21=2.5, sasp_il6=3.0, sasp_il8=2.5, sasp_mmp3=2.0)
        result = compute_treatment_effect(treated, untreated)
        assert result.treatment_effect is not None
        assert result.treatment_effect > 0  # Should show reduction

    def test_positive_control_validation_pass(self):
        treated = {
            "p16_expression": -0.28,
            "p21_expression": -0.22,
            "sasp_score": -0.38,
            "gamma_h2ax": -0.18,
            "sa_beta_gal": -0.33,
        }
        result = validate_positive_control(treated, tolerance=0.3)
        assert result["overall_pass"]

    def test_positive_control_validation_fail(self):
        treated = {
            "p16_expression": 0.1,  # Wrong direction
            "p21_expression": -0.22,
            "sasp_score": -0.38,
            "gamma_h2ax": -0.18,
            "sa_beta_gal": -0.33,
        }
        result = validate_positive_control(treated, tolerance=0.3)
        assert not result["overall_pass"]

    def test_rapamycin_effect_consistent(self):
        """Verify rapamycin produces expected senescence reduction."""
        treated_markers = {
            "p16_expression": -0.32,
            "p21_expression": -0.27,
            "sasp_score": -0.42,
            "gamma_h2ax": -0.22,
            "sa_beta_gal": -0.36,
        }
        result = validate_positive_control(treated_markers, tolerance=0.15)
        assert result["overall_pass"]
