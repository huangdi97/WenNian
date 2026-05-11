"""Additional comprehensive tests for Stage 5 modules."""

import pytest
from src.agents.protocols import (
    Argument, DebateRound, EvidenceLevel, InterventionScenario,
    InterventionPrediction, AgentTask, AgentMessageType,
)
from src.agents.task_orchestrator import TaskOrchestrator, CircuitBreaker
from src.knowledge.symptom_map import (
    map_symptoms_to_dimensions, get_top_dimensions, get_all_symptoms, SYMPTOM_MAP,
)
from src.commercial.actuarial_pricing import compute_risk_score, LongevityRiskScore
from src.commercial.enterprise_wellness import aggregate_employee_aging, K_ANONYMITY_THRESHOLD
from src.outputs.instant_feedback import generate_daily_card, generate_trend_card
from src.commercial.product_validator import run_product_validation, build_poc_report


class TestAdditional:
    def test_argument_all_levels(self):
        for level in EvidenceLevel:
            arg = Argument(claim="Test", evidence="E", evidence_level=level)
            assert arg.evidence_level == level

    def test_debate_round_full(self):
        args = [Argument(claim="C1", evidence="E1")]
        dr = DebateRound(
            round_number=2, proposition="P",
            pro_arguments=args, con_arguments=args,
            judge_score=6.0, judge_rationale="R"
        )
        assert dr.round_number == 2
        assert isinstance(dr.pro_arguments[0], Argument)

    def test_circuit_breaker_half_open(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=-1, half_open_limit=1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        assert cb.allow_request()  # transitions to half_open
        assert cb.state == "half_open"
        assert cb.allow_request()  # still allowed (1 attempt)
        assert not cb.allow_request()  # limit exceeded

    def test_orchestrator_multiple_agents(self):
        orch = TaskOrchestrator()
        orch.register_agent("a1", lambda p: {"r": 1})
        orch.register_agent("a2", lambda p: {"r": 2}, fallback_id="a1")
        task = AgentTask(task_id="t1", agent_id="a1", message_type=AgentMessageType.ASSESSMENT_REQUEST)
        result = orch.dispatch(task)
        assert result["r"] == 1

    def test_symptom_map_50_plus(self):
        symptoms = get_all_symptoms()
        assert len(symptoms) >= 50

    def test_symptom_fuzzy_match(self):
        result = map_symptoms_to_dimensions(["严重疲劳感"])
        assert len(result) > 0

    def test_risk_score_very_young(self):
        score = compute_risk_score(40, 30)
        assert score.recommended_premium_adjustment < 0

    def test_k_anonymity_exact_threshold(self):
        employees = [
            {"biological_age": 40 + i * 0.1, "chronological_age": 38 + i * 0.1, "department": "Eng"}
            for i in range(K_ANONYMITY_THRESHOLD)
        ]
        result = aggregate_employee_aging(employees)
        assert "error" not in result

    def test_daily_card_all_variants(self):
        for accel, _ in [(-4, "年轻"), (0, "正常"), (3, "加速"), (6, "偏快")]:
            card = generate_daily_card(40 + accel, 40)
            assert "免责声明" in card

    def test_trend_card_with_history(self):
        history = [("2026-05-01", 42.0), ("2026-05-02", 41.8),
                    ("2026-05-03", 42.2), ("2026-05-04", 42.0),
                    ("2026-05-05", 41.9), ("2026-05-06", 42.1),
                    ("2026-05-07", 42.3)]
        card = generate_trend_card(history)
        assert "趋势" in card

    def test_product_validation_large_sample(self):
        import random
        random.seed(42)
        before = [42 + random.gauss(0, 2) for _ in range(30)]
        after = [b - 1.5 + random.gauss(0, 1.5) for b in before]
        result = run_product_validation("Test", before, after)
        assert result.sample_size == 30
        assert result.mean_difference < 0

    def test_poc_report_contains_ci(self):
        before = [42, 43, 44, 41, 45, 40, 43, 42, 44, 41]
        after = [40.5, 41.5, 42.5, 39.5, 43.5, 38.5, 41.5, 40.5, 42.5, 39.5]
        result = run_product_validation("P", before, after)
        report = build_poc_report(result)
        assert "95% CI" in report or "CI" in report
