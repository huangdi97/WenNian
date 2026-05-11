"""Tests for actuarial pricing module."""

import pytest
from src.commercial.actuarial_pricing import (
    compute_risk_score, generate_actuarial_report, batch_risk_portfolio,
    LongevityRiskScore,
)


class TestActuarialPricing:
    def test_compute_normal_risk(self):
        score = compute_risk_score(40.0, 40.5)
        assert isinstance(score, LongevityRiskScore)
        assert abs(score.risk_multiple - 1.0) < 0.1
        assert score.risk_category == "平均风险"

    def test_compute_high_risk(self):
        score = compute_risk_score(40.0, 50.0)
        assert score.risk_multiple > 1.0
        assert "高" in score.risk_category

    def test_compute_low_risk(self):
        score = compute_risk_score(40.0, 30.0)
        assert score.risk_multiple < 1.0
        assert "低" in score.risk_category

    def test_premium_discount_for_low_risk(self):
        score = compute_risk_score(40.0, 32.0)
        assert score.recommended_premium_adjustment < 0  # Discount

    def test_generate_actuarial_report(self):
        score = compute_risk_score(40.0, 45.0, confidence=0.8)
        report = generate_actuarial_report(score)
        assert "风险概况" in report
        assert "风险倍数" in report
        assert "免责声明" in report

    def test_batch_risk_portfolio(self):
        assessments = [
            {"chronological_age": 40, "biological_age": 32},  # Low risk (-8)
            {"chronological_age": 40, "biological_age": 48},  # High risk (+8)
            {"chronological_age": 40, "biological_age": 42},  # Average (+2)
        ]
        portfolio = batch_risk_portfolio(assessments)
        assert portfolio["count"] == 3
        assert "mean_risk_multiple" in portfolio
        assert portfolio["high_risk_count"] >= 1
        assert portfolio["low_risk_count"] >= 1

    def test_empty_portfolio(self):
        result = batch_risk_portfolio([])
        assert result["count"] == 0

    def test_biomarker_factors(self):
        score = compute_risk_score(40.0, 45.0, biomarkers={
            "glucose": 7.0, "c_reactive_protein": 5.0, "albumin": 30.0,
        })
        assert len(score.factors) >= 2
