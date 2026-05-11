"""Tests for AgingIntegrator."""

import pytest
from src.integrator import AgingIntegrator, IntegratedReport
from src.clocks import ClockRegistry
from src.core.exceptions import ComputationError


class TestAgingIntegrator:
    def test_assess_normal(self, integrator, sample_biomarkers):
        result = integrator.assess(sample_biomarkers)
        assert isinstance(result, IntegratedReport)
        assert result.biological_age > 0
        assert result.chronological_age == 40.0
        assert len(result.clock_results) == 4
        assert result.confidence > 0

    def test_assess_incomplete(self, integrator, incomplete_biomarkers):
        with pytest.raises(ComputationError):
            integrator.assess(incomplete_biomarkers)

    def test_assess_extreme(self, integrator, extreme_biomarkers):
        result = integrator.assess(extreme_biomarkers)
        assert isinstance(result, IntegratedReport)
        # Should still produce output even with extreme values
        assert result.biological_age > 0

    def test_empty_registry(self):
        registry = ClockRegistry()
        registry.clear()
        integrator = AgingIntegrator(registry=registry)
        with pytest.raises(ComputationError):
            integrator.assess({"age": 40})

    def test_clock_results_have_status(self, integrator, sample_biomarkers):
        result = integrator.assess(sample_biomarkers)
        for cr in result.clock_results:
            assert cr.clock_name
            assert cr.status in ("ok",) or "error" in cr.status

    def test_weighted_fusion(self, sample_biomarkers, populated_registry):
        weights = {"phenoage": 2.0, "kdm": 0.5, "dnn": 0.5, "lifeclock": 1.0}
        integrator = AgingIntegrator(registry=populated_registry, weights=weights)
        result = integrator.assess(sample_biomarkers)
        assert result.biological_age > 0
