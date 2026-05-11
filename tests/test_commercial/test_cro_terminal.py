"""Tests for CRO terminal module."""

import pytest
from src.commercial.cro_terminal import (
    export_sdtm_dm, export_adam_adsl, monitor_data_quality,
)


class TestCROTerminal:
    @pytest.fixture
    def sample_subjects(self):
        return [
            {"usubjid": f"SUB-{i:03d}", "age": 40 + i * 5, "sex": "M", "arm": "TREATMENT"}
            for i in range(5)
        ]

    @pytest.fixture
    def sample_biomarkers(self):
        return [
            {"biomarkers": {"age": 40, "albumin": 43, "creatinine": 75, "glucose": 5.1}}
            for _ in range(5)
        ]

    def test_export_sdtm_dm(self, sample_subjects):
        csv_content = export_sdtm_dm(sample_subjects)
        assert "STUDYID" in csv_content
        assert "USUBJID" in csv_content
        assert "SUB-001" in csv_content

    def test_export_adam_adsl(self, sample_subjects):
        assessments = [
            {"biological_age": 42.0, "age_acceleration": 2.0, "status": "success"}
            for _ in range(5)
        ]
        csv_content = export_adam_adsl(sample_subjects, assessments)
        assert "BIOLOGICAL_AGE" in csv_content
        assert "AGE_ACCELERATION" in csv_content

    def test_export_adam_missing_assessments(self, sample_subjects):
        csv_content = export_adam_adsl(sample_subjects)
        assert "BIOLOGICAL_AGE" in csv_content  # Should still produce output

    def test_monitor_data_quality(self, sample_biomarkers):
        result = monitor_data_quality(sample_biomarkers)
        assert result["total_subjects"] == 5
        assert result["overall_quality_score"] > 0.9

    def test_monitor_data_quality_missing(self):
        subjects = [
            {"biomarkers": {"age": 40}},
            {"biomarkers": {"age": 41, "albumin": 43}},
        ]
        result = monitor_data_quality(subjects)
        assert result["missing_values"]["glucose"] >= 1

    def test_monitor_empty(self):
        result = monitor_data_quality([])
        assert result["total_subjects"] == 0

    def test_export_sdtm_custom_study(self, sample_subjects):
        csv_content = export_sdtm_dm(sample_subjects, study_id="CUSTOM-001")
        assert "CUSTOM-001" in csv_content
