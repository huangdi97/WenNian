"""Tests for compound screener."""

import pytest
from src.industrial.compound_screener import CompoundScreener, CompoundScore


class TestCompoundScreener:
    @pytest.fixture
    def screener(self):
        return CompoundScreener()

    def test_score_all(self, screener):
        results = screener.score_all()
        assert len(results) >= 5
        assert isinstance(results[0], CompoundScore)

    def test_sorted_by_sas(self, screener):
        results = screener.score_all()
        for i in range(len(results) - 1):
            assert results[i].sas_score >= results[i + 1].sas_score

    def test_known_senolytics_higher(self, screener):
        comparison = screener.compare_senolytics_vs_others()
        assert comparison["senolytics"]["mean_sas"] > comparison["others"]["mean_sas"]
        assert comparison["senolytic_advantage"] > 1.0

    def test_get_known_senolytics(self, screener):
        senolytics = screener.get_known_senolytics()
        assert len(senolytics) > 0
        for s in senolytics:
            assert s.known_senolytic

    def test_rank_by_safety(self, screener):
        results = screener.rank_by_safety()
        assert len(results) > 0
        # Safety-adjusted score should be ≤ raw SAS score
        for r in results:
            safety_score = r.sas_score * (1.0 - r.toxicity_risk)
            assert safety_score <= r.sas_score

    def test_screen_custom_compound(self, screener):
        result = screener.screen_custom_compound(
            "Novel-Senolytic", sas_score=0.7, toxicity=0.3, selectivity=0.6
        )
        assert result.compound_name == "Novel-Senolytic"
        assert result.sas_score == 0.7

    def test_dq_top_score(self, screener):
        results = screener.score_all()
        if any("Dasatinib+Quercetin" == r.compound_name for r in results):
            dq = next(r for r in results if r.compound_name == "Dasatinib+Quercetin")
            assert dq.sas_score >= 0.9
