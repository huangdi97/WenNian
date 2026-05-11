"""Tests for coagulation pathway module."""

from src.knowledge.coagulation_pathway import (
    get_coagulation_pathway, estimate_coagulation_burden, COAGULATION_FACTORS,
)


class TestCoagulationPathway:
    def test_get_pathway(self):
        pathway = get_coagulation_pathway()
        assert "factors" in pathway
        assert "organs_affected" in pathway
        assert len(pathway["factors"]) >= 3

    def test_factors_have_metadata(self):
        for factor, info in COAGULATION_FACTORS.items():
            assert "source_organ" in info
            assert "target_organs" in info
            assert "mechanism" in info

    def test_liver_is_primary_source(self):
        pathway = get_coagulation_pathway()
        assert pathway["primary_source"] == "肝脏"

    def test_estimate_burden_with_crp(self):
        result = estimate_coagulation_burden(
            {"c_reactive_protein": 5.0, "albumin": 40.0}, age=50
        )
        assert "total_coagulation_burden" in result
        assert "risk_level" in result
        assert result["risk_level"] in ("高", "中", "低")

    def test_estimate_burden_low_albumin(self):
        result = estimate_coagulation_burden(
            {"albumin": 30.0}, age=60
        )
        total = result["total_coagulation_burden"]
        assert total >= 0

    def test_estimate_burden_empty(self):
        result = estimate_coagulation_burden({}, age=40)
        assert result["total_coagulation_burden"] == 0.0
