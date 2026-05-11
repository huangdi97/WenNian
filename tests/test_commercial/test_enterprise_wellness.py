"""Tests for enterprise wellness module."""

import pytest
from src.commercial.enterprise_wellness import (
    aggregate_employee_aging, build_enterprise_dashboard,
    K_ANONYMITY_THRESHOLD,
)


class TestEnterpriseWellness:
    @pytest.fixture
    def large_dataset(self):
        employees = []
        for i in range(50):
            dept = "Engineering" if i < 30 else "Marketing"
            employees.append({
                "id": f"E{i:04d}",
                "biological_age": 40.0 + i * 0.2,
                "chronological_age": 38.0 + i * 0.2,
                "department": dept,
            })
        return employees

    @pytest.fixture
    def small_dataset(self):
        return [
            {"biological_age": 42.0, "chronological_age": 40.0, "department": "Eng"},
            {"biological_age": 41.0, "chronological_age": 39.0, "department": "Mkt"},
        ]

    def test_aggregate_large(self, large_dataset):
        result = aggregate_employee_aging(large_dataset)
        assert result["total_employees"] == 50
        assert "overall" in result
        assert result["overall"]["mean_chronological_age"] > 0
        assert "departments" in result

    def test_k_anonymity_small(self, small_dataset):
        result = aggregate_employee_aging(small_dataset)
        assert "error" in result
        assert result["current_count"] < K_ANONYMITY_THRESHOLD

    def test_department_suppression(self, large_dataset):
        # Add a small department
        for i in range(10):
            large_dataset.append({
                "id": f"EXTRA-{i}",
                "biological_age": 40.0,
                "chronological_age": 38.0,
                "department": "TinyDept",
            })
        result = aggregate_employee_aging(large_dataset)
        depts = result.get("departments", {})
        tiny = depts.get("TinyDept", {})
        assert tiny.get("suppressed") is True

    def test_build_dashboard(self, large_dataset):
        aggregated = aggregate_employee_aging(large_dataset)
        dashboard = build_enterprise_dashboard(aggregated, "TestCorp")
        assert "TestCorp" in dashboard
        assert "健康资本指数" in dashboard or "health" in dashboard.lower()

    def test_build_dashboard_small(self, small_dataset):
        aggregated = aggregate_employee_aging(small_dataset)
        dashboard = build_enterprise_dashboard(aggregated)
        assert "数据不足" in dashboard

    def test_age_groups(self, large_dataset):
        result = aggregate_employee_aging(large_dataset)
        assert "age_groups" in result
        assert any(group in result["age_groups"] for group in ["30-39", "40-49"])

    def test_health_capital_index(self, large_dataset):
        result = aggregate_employee_aging(large_dataset)
        hci = result["overall"]["health_capital_index"]
        assert 0.0 <= hci <= 1.0
