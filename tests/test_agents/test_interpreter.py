"""Tests for Interpreter agent."""

import pytest
from src.agents.interpreter import Interpreter


class TestInterpreter:
    @pytest.fixture
    def interpreter(self):
        return Interpreter()

    def test_execute_normal(self, interpreter, sample_biomarkers):
        output = interpreter.execute({
            "biomarkers": sample_biomarkers,
            "assessment": {},
        })
        assert output.success
        assert "feature_importances" in output.data
        assert "top_driver" in output.data

    def test_summary_generated(self, interpreter, sample_biomarkers):
        output = interpreter.execute({
            "biomarkers": sample_biomarkers,
            "assessment": {},
        })
        assert "summary" in output.data
        assert len(output.data["summary"]) > 0

    def test_empty_biomarkers(self, interpreter):
        output = interpreter.execute({"biomarkers": {}, "assessment": {}})
        assert output.success
        assert output.data["summary"] == "无足够数据进行解释分析"
