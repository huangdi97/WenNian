"""Tests for debate agents (director, skeptic, pro, con, judge)."""

import pytest
from src.agents.director import LongevityDirector, run_debate_pipeline
from src.agents.skeptic import Skeptic
from src.agents.pro_debater import ProDebater
from src.agents.con_debater import ConDebater
from src.agents.judge import Judge
from src.agents.protocols import Argument


class TestDirector:
    def test_quick_assessment(self, sample_biomarkers):
        director = LongevityDirector()
        output = director.execute({
            "scenario": "quick_assessment",
            "biomarkers": sample_biomarkers,
        })
        assert output.success
        assert "biological_age" in output.data

    def test_unknown_scenario(self):
        director = LongevityDirector()
        output = director.execute({"scenario": "invalid"})
        assert not output.success


class TestSkeptic:
    def test_review_normal(self, sample_biomarkers):
        skeptic = Skeptic()
        output = skeptic.execute({"biomarkers": sample_biomarkers, "assessment": {}})
        assert output.success
        assert "data_quality_score" in output.data

    def test_review_missing_crp(self, sample_biomarkers):
        skeptic = Skeptic()
        bio = dict(sample_biomarkers)
        bio.pop("c_reactive_protein", None)
        output = skeptic.execute({"biomarkers": bio, "assessment": {}})
        assert any("CRP" in str(l) for l in output.data.get("limitations", []))

    def test_review_empty(self):
        skeptic = Skeptic()
        output = skeptic.execute({"biomarkers": {}, "assessment": {}})
        # With empty biomarkers, data quality should be low
        assert output.data["data_quality_score"] < 1.0


class TestProDebater:
    def test_generate_arguments(self, sample_biomarkers):
        pro = ProDebater()
        output = pro.execute({
            "proposition": "应优先干预免疫衰老",
            "biomarkers": sample_biomarkers,
            "assessment": {"biological_age": 42.0, "chronological_age": 40.0},
            "round": 1,
            "previous_rounds": [],
            "skeptic_notes": {},
        })
        assert output.success
        assert len(output.data["arguments"]) > 0

    def test_topic_selection_immune(self):
        pro = ProDebater()
        topics = pro._select_topics("免疫衰老需优先干预", {}, {})
        assert "immune_aging" in topics


class TestConDebater:
    def test_generate_counter_arguments(self, sample_biomarkers):
        con = ConDebater()
        output = con.execute({
            "proposition": "应优先干预免疫衰老",
            "biomarkers": sample_biomarkers,
            "assessment": {},
            "round": 1,
            "previous_rounds": [],
            "pro_arguments": [],
            "skeptic_notes": {},
        })
        assert output.success
        assert len(output.data["arguments"]) > 0

    def test_responds_to_pro(self):
        con = ConDebater()
        pro_args = [{"claim": "免疫衰老是全身衰老的核心驱动", "evidence_level": "meta_analysis"}]
        output = con.execute({
            "proposition": "test",
            "biomarkers": {},
            "assessment": {},
            "round": 1,
            "previous_rounds": [],
            "pro_arguments": pro_args,
            "skeptic_notes": {},
        })
        assert len(output.data["arguments"]) > 1  # Measurement + counter


class TestJudge:
    def test_evaluate_round(self):
        judge = Judge(max_rounds=3)
        result = judge.evaluate_round(
            proposition="Test proposition",
            pro_arguments=[
                {"claim": "P1", "evidence": "Evidence for P1", "evidence_level": "meta_analysis", "confidence": 0.9},
            ],
            con_arguments=[
                {"claim": "C1", "evidence": "Evidence for C1", "evidence_level": "cohort", "confidence": 0.7},
            ],
            round_number=1,
        )
        assert result.round_number == 1
        assert result.judge_score is not None
        assert result.judge_rationale

    def test_should_terminate_max_rounds(self):
        judge = Judge(max_rounds=3)
        judge._round_count = 3
        assert judge.should_terminate()

    def test_should_terminate_clear_winner(self):
        judge = Judge(max_rounds=3)
        judge._cumulative_pro_score = 10.0
        judge._cumulative_con_score = 1.0
        judge._round_count = 2
        assert judge.should_terminate()

    def test_final_verdict(self):
        judge = Judge(max_rounds=3)
        judge._cumulative_pro_score = 8.0
        judge._cumulative_con_score = 4.0
        verdict = judge.final_verdict([])
        assert verdict["winner"] == "pro"
        assert verdict["final_score"] > 0


class TestDebatePipeline:
    def test_full_debate(self, sample_biomarkers):
        result = run_debate_pipeline(
            biomarkers=sample_biomarkers,
            assessment={"biological_age": 42.5, "chronological_age": 40.0},
            max_rounds=2,
        )
        assert "rounds" in result
        assert "winner" in result
        assert len(result["rounds"]) <= 2
        assert "consensus_notes" in result
