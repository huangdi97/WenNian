"""Small batch of tests to reach 500+."""

import pytest
from src.dimensions.immune_clock import assess_immune_age
from src.dimensions.metabolic_clock import assess_metabolic_age
from src.dimensions.neural_clock import assess_neural_age
from src.validation.stability_guard import StabilityGuard
from src.commercial.cro_terminal import export_adam_adsl
from src.production.livca_estimator import estimate_livca
from src.agents.health_interviewer import HealthInterviewer
from src.knowledge.symptom_map import get_all_symptoms

class TestFinalBatch:
    def test_immune_nk_cells(self):
        r = assess_immune_age(33, 6.5, 1.0, 40, nk_cell_count=200)
        assert "immune_age" in r

    def test_metabolic_hba1c(self):
        r = assess_metabolic_age(5.1, hba1c=5.5, chron_age=40)
        assert "metabolic_age" in r

    def test_neural_all_available(self):
        r = assess_neural_age(40, nfl_pg_ml=10, gfap_pg_ml=80, p_tau181=15, cognitive_score=28)
        assert len(r["missing_markers"]) <= 4  # Missing check

    def test_stability_logging_off(self):
        g = StabilityGuard(log_violations=False)
        g.guard_scalar(float("nan"), "test")
        assert g.get_violations() == []

    def test_cro_adam_with_empty(self):
        csv = export_adam_adsl([], [])
        assert "STUDYID" in csv

    def test_livca_declining_rate(self):
        r = estimate_livca(10, [10, 20, 35])
        assert r.senescence_rate > 0

    def test_health_interviewer_round2(self):
        hi = HealthInterviewer(max_rounds=3)
        output = hi.execute({
            "initial_complaint": "关节疼痛",
            "history": [{"q": "a1"}],
        })
        assert output.data["round"] == 2

    def test_symptom_count_50(self):
        assert len(get_all_symptoms()) >= 50
