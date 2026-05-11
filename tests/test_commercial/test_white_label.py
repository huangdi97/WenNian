"""Tests for white label module."""

import json
import pytest
import zipfile
import io
from src.commercial import (
    generate_batch_reports, create_zip_package, apply_brand_template
)


class TestWhiteLabel:
    @pytest.fixture
    def sample_subjects(self):
        return [
            {
                "subject_id": f"SUBJ-{i:04d}",
                "biomarkers": {
                    "age": 40.0 + i * 5,
                    "albumin": 43.0 - i * 0.5,
                    "creatinine": 75.0 + i * 2,
                    "glucose": 5.1 + i * 0.1,
                    "c_reactive_protein": 1.0 + i * 0.5,
                    "lymphocyte_percent": 33.0 - i,
                    "mcv": 90.0 + i * 0.5,
                    "rdw": 13.0 + i * 0.2,
                    "alkaline_phosphatase": 70.0 + i * 5,
                    "white_blood_cell_count": 6.5 + i * 0.3,
                },
            }
            for i in range(5)
        ]

    def test_generate_batch_reports(self, sample_subjects):
        results = generate_batch_reports(sample_subjects)
        assert len(results) == 5
        assert all(r["status"] == "success" for r in results)
        assert all(r["biological_age"] > 0 for r in results)

    def test_generate_batch_with_brand(self, sample_subjects):
        brand = {"name": "TestClinic", "theme_color": "#FF0000"}
        results = generate_batch_reports(sample_subjects, brand_config=brand)
        assert "TestClinic" in results[0]["report_md"]

    def test_create_zip_package(self, sample_subjects):
        results = generate_batch_reports(sample_subjects)
        zip_bytes = create_zip_package(results)
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0

        # Verify ZIP content
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        names = zf.namelist()
        assert "summary.csv" in names
        assert any("SUBJ-" in n for n in names)

    def test_batch_with_errors(self):
        subjects = [
            {"subject_id": "BAD-0001", "biomarkers": {"age": 40}},
        ]
        results = generate_batch_reports(subjects)
        assert results[0]["status"] != "success"

    def test_apply_brand_template_medical(self):
        base = {"name": "Test"}
        result = apply_brand_template(base, "medical")
        assert result["theme_color"] == "#1B6B4A"
        assert "disclaimer" in result

    def test_apply_brand_template_default(self):
        base = {"name": "Test"}
        result = apply_brand_template(base, "invalid_template")
        assert result["theme_color"] == "#2E86AB"  # Falls back to default

    def test_create_zip_has_readme(self, sample_subjects):
        results = generate_batch_reports(sample_subjects)
        zip_bytes = create_zip_package(results)
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        readme = zf.read("README.txt").decode("utf-8")
        assert "问年" in readme or "WenNian" in readme
