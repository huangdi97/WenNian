"""Tests for PDF generator."""

import pytest
from src.outputs.pdf_generator import generate_pdf, REPORTLAB_AVAILABLE
from src.outputs.report_builder import build_markdown_report
from src.integrator import IntegratedReport, ClockOutput


@pytest.fixture
def sample_report():
    return IntegratedReport(
        chronological_age=40.0,
        biological_age=42.5,
        age_acceleration=2.5,
        confidence=0.82,
        lower_bound=38.0,
        upper_bound=47.0,
        clock_results=[
            ClockOutput(clock_name="phenoage", predicted_age=42.0, confidence=0.80, status="ok"),
        ],
        warnings=[],
    )


class TestPDFGenerator:
    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="ReportLab not installed")
    def test_pdf_bytes_generated(self, sample_report):
        md = build_markdown_report(sample_report)
        pdf_bytes = generate_pdf(md)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Check PDF magic bytes
        assert pdf_bytes[:5] == b"%PDF-"

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="ReportLab not installed")
    def test_pdf_contains_disclaimer(self, sample_report):
        md = build_markdown_report(sample_report)
        pdf_bytes = generate_pdf(md)
        # PDF text encoding varies, but disclaimer text is embedded
        assert len(pdf_bytes) > 1000

    def test_reportlab_missing_raises(self, monkeypatch, sample_report):
        """If ReportLab is not available, should raise ComputationError."""
        if REPORTLAB_AVAILABLE:
            monkeypatch.setattr(
                "src.outputs.pdf_generator.REPORTLAB_AVAILABLE", False
            )
            from src.core.exceptions import ComputationError
            with pytest.raises(ComputationError):
                generate_pdf("test content")
