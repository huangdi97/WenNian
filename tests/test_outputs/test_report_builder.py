"""Tests for report_builder."""

import pytest
from src.outputs.report_builder import build_markdown_report, build_compact_report
from src.integrator import IntegratedReport, ClockOutput


@pytest.fixture
def sample_report():
    """Build a sample IntegratedReport for testing."""
    return IntegratedReport(
        chronological_age=40.0,
        biological_age=42.5,
        age_acceleration=2.5,
        confidence=0.82,
        lower_bound=38.0,
        upper_bound=47.0,
        clock_results=[
            ClockOutput(clock_name="phenoage", predicted_age=42.0, confidence=0.80, status="ok"),
            ClockOutput(clock_name="kdm", predicted_age=43.0, confidence=0.75, status="ok"),
            ClockOutput(clock_name="dnn", predicted_age=41.5, confidence=0.70, status="ok"),
            ClockOutput(clock_name="lifeclock", predicted_age=43.5, confidence=0.85, status="ok"),
        ],
        warnings=["Slight elevation in glucose"],
    )


class TestBuildMarkdownReport:
    def test_full_report(self, sample_report):
        md = build_markdown_report(sample_report)
        assert "衰老评估报告" in md
        assert "42.5" in md
        assert "40.0" in md
        assert "免责声明" in md

    def test_report_sections(self, sample_report):
        md = build_markdown_report(sample_report)
        assert "生物年龄总结" in md
        assert "时钟详细结果" in md
        assert "方法学透明" in md

    def test_disclaimer_present(self, sample_report):
        md = build_markdown_report(sample_report)
        assert "不构成医疗诊断" in md

    def test_brand_customization(self, sample_report):
        brand = {"name": "TestBrand", "theme_color": "#FF0000"}
        md = build_markdown_report(sample_report, brand_config=brand)
        assert "TestBrand" in md

    def test_acceleration_positive(self, sample_report):
        md = build_markdown_report(sample_report)
        assert "加速衰老" in md.lower() or "大于" in md

    def test_compact_report(self):
        data = {
            "biological_age": 42.5,
            "chronological_age": 40.0,
            "age_acceleration": 2.5,
            "confidence": 0.82,
        }
        report = build_compact_report(data)
        assert "42.5" in report
        assert "40.0" in report
        assert "不构成医疗诊断" in report
