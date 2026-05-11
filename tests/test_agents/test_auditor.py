"""Tests for Auditor agent."""

import pytest
from src.agents.auditor import Auditor, AuditResult
from src.agents import AgentOutput


class TestAuditor:
    @pytest.fixture
    def auditor(self):
        return Auditor()

    def test_clean_report_passes(self, auditor):
        report = """# 衰老评估报告
        生物年龄: 42.0
        免责声明：不构成医疗诊断
        """
        output = auditor.execute({
            "report_text": report,
            "biological_age": 42.0,
            "chronological_age": 40.0,
        })
        assert isinstance(output, AgentOutput)
        assert output.data["passed"]

    def test_redline_triggered(self, auditor):
        report = """# 评估
        建议服用人参提取物
        免责声明：不构成医疗诊断
        """
        output = auditor.execute({
            "report_text": report,
            "biological_age": 42.0,
            "chronological_age": 40.0,
        })
        assert not output.data["passed"]
        assert len(output.data["violations"]) > 0

    def test_redline_diagnosis(self, auditor):
        report = """# 报告
        确诊为衰老加速
        免责声明：不构成医疗诊断
        """
        output = auditor.execute({"report_text": report,
            "biological_age": 45.0, "chronological_age": 40.0})
        assert not output.data["passed"]

    def test_missing_disclaimer(self, auditor):
        output = auditor.execute({
            "report_text": "# Just a report",
            "biological_age": 42.0,
            "chronological_age": 40.0,
        })
        assert not output.data["passed"]

    def test_numerical_consistency_extreme(self, auditor):
        report = "# Report\n免责声明：不构成医疗诊断"
        output = auditor.execute({
            "report_text": report,
            "biological_age": 150.0,
            "chronological_age": 40.0,
        })
        assert not output.data["passed"]

    def test_recommend_prescription(self, auditor):
        report = """# 报告
        推荐用药：二甲双胍
        免责声明：不构成医疗诊断
        """
        output = auditor.execute({"report_text": report,
            "biological_age": 42.0, "chronological_age": 40.0})
        assert not output.data["passed"]
