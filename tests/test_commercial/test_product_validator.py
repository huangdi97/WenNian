"""Tests for product validator module."""

import pytest
from src.commercial.product_validator import (
    run_product_validation, build_poc_report, POCResult
)


class TestProductValidator:
    def test_run_validation_significant(self):
        before = [42.0, 43.0, 44.0, 41.0, 45.0, 40.0, 43.5, 42.5, 44.5, 41.5]
        after  = [40.5, 41.0, 42.5, 39.5, 43.0, 39.0, 42.0, 41.0, 43.0, 40.0]
        result = run_product_validation("TestProduct", before, after)
        assert isinstance(result, POCResult)
        assert result.sample_size == 10
        assert result.mean_difference < 0  # Should show reduction

    def test_run_validation_no_effect(self):
        before = [40.0, 41.0, 42.0, 43.0, 44.0]
        after  = [40.1, 41.0, 42.0, 42.9, 44.0]
        result = run_product_validation("Placebo", before, after)
        assert result.sample_size == 5
        # Cohen's d should be very small
        assert abs(result.cohens_d) < 0.5

    def test_run_validation_mismatched_lengths(self):
        with pytest.raises(ValueError):
            run_product_validation("Bad", [1.0, 2.0], [1.0])

    def test_run_validation_too_small(self):
        with pytest.raises(ValueError):
            run_product_validation("Small", [1.0, 2.0], [1.5, 2.5])

    def test_build_poc_report(self):
        before = [42.0, 43.0, 44.0, 41.0, 45.0]
        after  = [40.5, 41.5, 42.5, 39.5, 43.5]
        result = run_product_validation("TestProduct", before, after)
        report = build_poc_report(result)
        assert "TestProduct" in report
        assert "p值" in report
        assert "Cohen" in report
        assert "免责声明" in report

    def test_confidence_intervals(self):
        before = [40.0, 42.0, 41.0, 43.0, 44.0, 39.0, 41.5, 42.5, 40.5, 43.5]
        after  = [38.5, 40.5, 39.5, 41.5, 42.5, 38.0, 40.0, 41.0, 39.0, 42.0]
        result = run_product_validation("Prod", before, after)
        assert result.ci_95[0] < result.ci_95[1]

    def test_subject_ids(self):
        before = [40.0, 41.0, 42.0, 43.0, 44.0]
        after  = [39.0, 40.0, 41.0, 42.0, 43.0]
        result = run_product_validation("Prod", before, after, subject_ids=["A", "B", "C", "D", "E"])
        assert result.individual_results[0]["subject_id"] == "A"
        assert len(result.individual_results) == 5
