"""Inter-agent communication protocols using Pydantic models.

Defines the structured message types exchanged between agents
during the debate, assessment, and intervention workflows.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentMessageType(str, Enum):
    """Types of messages exchanged between agents."""
    ASSESSMENT_REQUEST = "assessment_request"
    ASSESSMENT_RESULT = "assessment_result"
    SKEPTIC_REVIEW = "skeptic_review"
    PRO_ARGUMENT = "pro_argument"
    CON_ARGUMENT = "con_argument"
    JUDGE_VERDICT = "judge_verdict"
    INTERVENTION_REQUEST = "intervention_request"
    INTERVENTION_RESULT = "intervention_result"
    EXPLANATION_REQUEST = "explanation_request"
    EXPLANATION_RESULT = "explanation_result"
    AUDIT_REQUEST = "audit_request"
    AUDIT_RESULT = "audit_result"
    ORCHESTRATOR_COMMAND = "orchestrator_command"


class EvidenceLevel(str, Enum):
    """Evidence quality levels for arguments."""
    META_ANALYSIS = "meta_analysis"
    RCT = "rct"
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    EXPERT_OPINION = "expert_opinion"
    IN_SILICO = "in_silico"


class Argument(BaseModel):
    """A single argument in the debate with evidence support.

    Attributes:
        claim: The central claim being made.
        evidence: Supporting evidence text.
        references: Literature references (DOI, PMID, or citation).
        evidence_level: Quality tier of the supporting evidence.
        confidence: Confidence score 0-1.
    """
    claim: str
    evidence: str
    references: List[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel = EvidenceLevel.EXPERT_OPINION
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class DebateRound(BaseModel):
    """A single round in the debate process.

    Attributes:
        round_number: 1-indexed round number.
        pro_arguments: Arguments supporting the proposition.
        con_arguments: Arguments opposing the proposition.
        judge_score: Score assigned by the judge (0-10).
        judge_rationale: Explanation of the judge's score.
    """
    round_number: int
    proposition: str = ""
    pro_arguments: List[Argument] = Field(default_factory=list)
    con_arguments: List[Argument] = Field(default_factory=list)
    judge_score: Optional[float] = None
    judge_rationale: Optional[str] = None


class DebateResult(BaseModel):
    """Complete debate outcome after all rounds.

    Attributes:
        proposition: The debated proposition.
        rounds: All debate rounds.
        winner: "pro" or "con".
        final_score: Final judge score.
        consensus_notes: Summary of the consensus reached.
    """
    proposition: str
    rounds: List[DebateRound] = Field(default_factory=list)
    winner: Optional[str] = None
    final_score: Optional[float] = None
    consensus_notes: str = ""


class InterventionScenario(BaseModel):
    """An intervention scenario to simulate.

    Attributes:
        target_dimension: Which aging dimension to intervene on.
        intervention_type: Type of intervention (e.g., 'senolytic', 'lifestyle').
        intensity: Intervention intensity level (0.0-1.0).
        duration_months: Simulated duration in months.
    """
    target_dimension: str
    intervention_type: str
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    duration_months: float = 12.0


class InterventionPrediction(BaseModel):
    """Predicted outcome of an intervention simulation.

    Attributes:
        scenario: The intervention scenario that was simulated.
        predicted_age_reduction: Expected reduction in biological age (years).
        lower_80ci: Lower bound of 80% confidence interval.
        upper_80ci: Upper bound of 80% confidence interval.
        lower_95ci: Lower bound of 95% confidence interval.
        upper_95ci: Upper bound of 95% confidence interval.
        downstream_effects: Effects on other dimensions.
        assumptions: Key assumptions underlying the prediction.
        confidence: Overall confidence 0-1.
    """
    scenario: InterventionScenario
    predicted_age_reduction: float
    lower_80ci: float
    upper_80ci: float
    lower_95ci: float
    upper_95ci: float
    downstream_effects: Dict[str, float] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AgentTask(BaseModel):
    """A task dispatched by the orchestrator to an agent.

    Attributes:
        task_id: Unique task identifier.
        agent_id: Target agent identifier.
        message_type: Type of message this task represents.
        payload: Task-specific data.
        timeout_seconds: Maximum execution time.
        priority: Task priority (lower = higher).
    """
    task_id: str
    agent_id: str
    message_type: AgentMessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 30.0
    priority: int = 5


class AgentMessage(BaseModel):
    """Envelope for inter-agent messages.

    Attributes:
        message_id: Unique message identifier.
        sender: Sending agent ID.
        receiver: Receiving agent ID.
        message_type: Type classification.
        payload: Message content.
        timestamp: When the message was sent.
    """
    message_id: str
    sender: str
    receiver: str
    message_type: AgentMessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
