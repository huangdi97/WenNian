"""Tests for intervention simulator."""

import pytest
from src.causality import CausalGraph
from src.causality.intervention_sim import InterventionSimulator


class TestInterventionSimulator:
    @pytest.fixture
    def simulator(self):
        return InterventionSimulator()

    def test_simulate_known_target(self, simulator):
        result = simulator.simulate("immune", intensity=0.5)
        assert result["target"] == "immune"
        assert result["direct_effect"] > 0
        assert "ci_80" in result
        assert "downstream_effects" in result

    def test_simulate_unknown_target(self, simulator):
        result = simulator.simulate("nonexistent", intensity=0.5)
        assert "error" in result

    def test_rank_targets(self, simulator):
        rankings = simulator.rank_targets("inflammation")
        assert len(rankings) > 0
        assert rankings[0]["total_effect"] >= rankings[-1]["total_effect"]

    def test_simulate_combination(self, simulator):
        result = simulator.simulate_combination([
            ("immune", 0.5),
            ("metabolic", 0.3),
        ])
        assert result["combined_direct_effect"] > 0
        assert result["diminishing_factor"] < 1.0

    def test_ci_consistency(self, simulator):
        result = simulator.simulate("immune", intensity=0.5)
        assert result["ci_80"][0] <= result["ci_80"][1]
        assert result["ci_95"][0] <= result["ci_95"][1]
        # 95% CI should be wider
        span_80 = result["ci_80"][1] - result["ci_80"][0]
        span_95 = result["ci_95"][1] - result["ci_95"][0]
        assert span_95 >= span_80
