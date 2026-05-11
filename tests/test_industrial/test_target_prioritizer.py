"""Tests for target prioritizer."""

import pytest
from src.industrial import TargetPrioritizer, TargetScore


class TestTargetPrioritizer:
    @pytest.fixture
    def prioritizer(self):
        return TargetPrioritizer()

    def test_prioritize_inflammation(self, prioritizer):
        results = prioritizer.prioritize(outcome="inflammation", top_k=5)
        assert len(results) > 0
        assert len(results) <= 5
        assert isinstance(results[0], TargetScore)
        assert results[0].priority_score > 0

    def test_prioritize_organ(self, prioritizer):
        results = prioritizer.prioritize(outcome="organ", top_k=3)
        assert len(results) > 0

    def test_results_sorted(self, prioritizer):
        results = prioritizer.prioritize(outcome="inflammation")
        for i in range(len(results) - 1):
            assert results[i].priority_score >= results[i + 1].priority_score

    def test_compare_targets(self, prioritizer):
        comparison = prioritizer.compare_targets(
            ["immune", "senescence", "metabolic"]
        )
        assert "immune" in comparison
        assert "senescence" in comparison
        assert comparison["immune"]["total_effect"] >= 0

    def test_target_properties(self, prioritizer):
        results = prioritizer.prioritize(outcome="inflammation")
        for r in results:
            assert r.target_name
            assert 0 <= r.off_target_risk <= 1
            assert 0 <= r.druggability <= 1

    def test_prioritize_without_safety(self, prioritizer):
        results_safe = prioritizer.prioritize(outcome="inflammation", include_safety=True)
        results_nosafe = prioritizer.prioritize(outcome="inflammation", include_safety=False)
        assert len(results_safe) == len(results_nosafe)
