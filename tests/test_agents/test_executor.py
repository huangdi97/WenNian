"""Tests for Executor agent."""

import pytest
from src.agents.executor import Executor
from src.agents.protocols import InterventionScenario, InterventionPrediction


class TestExecutor:
    @pytest.fixture
    def executor(self):
        return Executor()

    def test_simulate_metabolic(self, executor):
        scenario = InterventionScenario(
            target_dimension="metabolic",
            intervention_type="lifestyle",
            intensity=0.5,
            duration_months=12.0,
        )
        pred = executor.simulate(scenario)
        assert isinstance(pred, InterventionPrediction)
        assert pred.predicted_age_reduction > 0
        assert pred.lower_80ci >= 0
        assert pred.lower_95ci >= 0

    def test_simulate_immune(self, executor):
        scenario = InterventionScenario(
            target_dimension="immune", intervention_type="test", intensity=0.3
        )
        pred = executor.simulate(scenario)
        assert pred.confidence > 0.5

    def test_execute_with_scenarios(self, executor):
        output = executor.execute({
            "scenarios": [
                {"target_dimension": "metabolic", "intervention_type": "lifestyle", "intensity": 0.5},
                {"target_dimension": "immune", "intervention_type": "test", "intensity": 0.3},
            ],
        })
        assert output.success
        assert len(output.data["predictions"]) == 2

    def test_execute_default(self, executor):
        output = executor.execute({})
        assert output.success
        assert len(output.data["predictions"]) == 1

    def test_confidence_intervals(self, executor):
        scenario = InterventionScenario(
            target_dimension="cellular_senescence",
            intervention_type="senolytic",
            intensity=0.8,
        )
        pred = executor.simulate(scenario)
        assert pred.lower_80ci <= pred.upper_80ci
        assert pred.lower_95ci <= pred.upper_95ci
        assert pred.lower_95ci <= pred.lower_80ci  # 95% CI is wider

    def test_downstream_effects(self, executor):
        scenario = InterventionScenario(
            target_dimension="immune", intervention_type="test", intensity=1.0
        )
        pred = executor.simulate(scenario)
        assert len(pred.downstream_effects) > 0
