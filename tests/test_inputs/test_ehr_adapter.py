"""Tests for EHR adapter module."""

import csv
import os
import tempfile

import pytest
from src.inputs import parse_csv_report, generate_parsing_summary


class TestEHRAdapter:
    @pytest.fixture
    def sample_csv(self):
        content = (
            "age,albumin,creatinine,glucose,c_reactive_protein,"
            "lymphocyte_percent,mcv,rdw,alkaline_phosphatase,white_blood_cell_count\n"
            "40,43,75,5.1,1.0,33,90,13,70,6.5\n"
        )
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
        )
        tmp.write(content)
        tmp.close()
        yield tmp.name
        os.unlink(tmp.name)

    @pytest.fixture
    def long_format_csv(self):
        content = (
            "biomarker,value\n"
            "age,40\n"
            "albumin,43\n"
            "creatinine,75\n"
            "glucose,5.1\n"
        )
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
        )
        tmp.write(content)
        tmp.close()
        yield tmp.name
        os.unlink(tmp.name)

    @pytest.fixture
    def chinese_csv(self):
        content = (
            "年龄,白蛋白,肌酐,空腹血糖\n"
            "40,43,75,5.1\n"
        )
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
        )
        tmp.write(content)
        tmp.close()
        yield tmp.name
        os.unlink(tmp.name)

    def test_parse_wide_format(self, sample_csv):
        result = parse_csv_report(sample_csv)
        assert "biomarkers" in result
        assert result["biomarkers"]["age"] == 40.0
        assert result["biomarkers"]["albumin"] == 43.0

    def test_parse_long_format(self, long_format_csv):
        result = parse_csv_report(long_format_csv)
        assert result["biomarkers"]["age"] == 40.0
        assert result["biomarkers"]["albumin"] == 43.0

    def test_parse_chinese_headers(self, chinese_csv):
        result = parse_csv_report(chinese_csv)
        assert result["biomarkers"]["age"] == 40.0
        assert result["biomarkers"]["albumin"] == 43.0
        assert result["biomarkers"]["glucose"] == 5.1

    def test_generate_summary(self, sample_csv):
        result = parse_csv_report(sample_csv)
        summary = generate_parsing_summary(result)
        assert "数据源" in summary
        assert "成功解析" in summary

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_csv_report("nonexistent.csv")

    def test_empty_csv(self):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        )
        tmp.write("")
        tmp.close()
        with pytest.raises(ValueError):
            parse_csv_report(tmp.name)
        os.unlink(tmp.name)
