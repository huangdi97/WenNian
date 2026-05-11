"""Tests for Analyst agent."""

import pytest
from src.agents.analyst import Analyst
from src.agents import AgentOutput
from src.integrator import AgingIntegrator


class TestAnalyst:
    @pytest.fixture
    def analyst(self, integrator):
        return Analyst(integrator=integrator)

    def test_execute_normal(self, analyst, sample_biomarkers):
        output = analyst.execute({"biomarkers": sample_biomarkers})
        assert isinstance(output, AgentOutput)
        assert output.success
        assert "biological_age" in output.data
        assert output.data["chronological_age"] == 40.0

    def test_execute_empty_biomarkers(self, analyst):
        output = analyst.execute({"biomarkers": {}})
        assert not output.success
        assert len(output.errors) > 0

    def test_execute_no_biomarkers_key(self, analyst):
        output = analyst.execute({})
        assert not output.success

    def test_output_contains_clock_results(self, analyst, sample_biomarkers):
        output = analyst.execute({"biomarkers": sample_biomarkers})
        assert "clock_results" in output.data
        assert len(output.data["clock_results"]) == 4
