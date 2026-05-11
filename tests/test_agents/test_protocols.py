"""Tests for agent protocols."""

from src.agents.protocols import (
    Argument, DebateRound, DebateResult, InterventionScenario,
    InterventionPrediction, AgentTask, AgentMessage, AgentMessageType,
    EvidenceLevel,
)


class TestProtocols:
    def test_argument_creation(self):
        arg = Argument(claim="Test", evidence="Evidence", references=["ref1"])
        assert arg.claim == "Test"
        assert arg.evidence_level == EvidenceLevel.EXPERT_OPINION

    def test_debate_round_creation(self):
        pro_arg = Argument(claim="Pro", evidence="E1")
        con_arg = Argument(claim="Con", evidence="E2")
        dr = DebateRound(
            round_number=1, proposition="Test",
            pro_arguments=[pro_arg], con_arguments=[con_arg],
            judge_score=7.5, judge_rationale="Good"
        )
        assert dr.round_number == 1
        assert len(dr.pro_arguments) == 1
        assert dr.judge_score == 7.5

    def test_debate_result(self):
        result = DebateResult(proposition="P", winner="pro", final_score=8.0)
        assert result.winner == "pro"
        assert result.final_score == 8.0

    def test_intervention_scenario(self):
        sc = InterventionScenario(
            target_dimension="metabolic",
            intervention_type="lifestyle",
            intensity=0.5, duration_months=12
        )
        assert sc.target_dimension == "metabolic"
        assert 0 <= sc.intensity <= 1

    def test_intervention_prediction(self):
        sc = InterventionScenario(target_dimension="immune", intervention_type="test", intensity=0.5)
        pred = InterventionPrediction(
            scenario=sc, predicted_age_reduction=2.5,
            lower_80ci=1.0, upper_80ci=4.0,
            lower_95ci=0.5, upper_95ci=4.5,
        )
        assert pred.predicted_age_reduction == 2.5

    def test_agent_task(self):
        task = AgentTask(
            task_id="t1", agent_id="a1",
            message_type=AgentMessageType.ASSESSMENT_REQUEST,
            payload={"key": "val"}
        )
        assert task.agent_id == "a1"
        assert task.message_type == AgentMessageType.ASSESSMENT_REQUEST

    def test_agent_message(self):
        msg = AgentMessage(
            message_id="m1", sender="s", receiver="r",
            message_type=AgentMessageType.ASSESSMENT_RESULT,
        )
        assert msg.sender == "s"
        assert msg.receiver == "r"
