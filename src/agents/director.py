"""LongevityDirector — scene router and task dispatcher.

Routes user requests to appropriate workflows:
- quick_assessment: fast biomarker-only evaluation
- full_debate: multi-agent debate with literature
- intervention_simulation: causal intervention modeling
"""

from typing import Any, Dict, List, Optional

from . import BaseAgent, AgentOutput, CapabilityToken
from .protocols import AgentTask, AgentMessageType, DebateResult

DEFAULT_AGENT_ID = "director.v2"


class LongevityDirector(BaseAgent):
    """Top-level orchestrating agent for the WenNian system.

    Routes user scenarios to appropriate workflows and coordinates
    multi-agent execution through the TaskOrchestrator.

    Args:
        orchestrator: TaskOrchestrator for agent dispatch.
        agent_id: Unique identifier.
        capability: Capability token.
    """

    def __init__(
        self,
        orchestrator: Any = None,
        agent_id: str = DEFAULT_AGENT_ID,
        capability: Optional[CapabilityToken] = None,
    ) -> None:
        super().__init__(agent_id=agent_id, capability=capability)
        self._orchestrator = orchestrator

    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        """Route and execute the appropriate workflow.

        Args:
            context: Must include 'scenario' key:
                - 'quick_assessment'
                - 'full_debate'
                - 'intervention_simulation'
                Plus relevant data for each scenario.

        Returns:
            AgentOutput with workflow results.
        """
        scenario = context.get("scenario", "quick_assessment")

        if scenario == "quick_assessment":
            return self._route_quick(context)
        elif scenario == "full_debate":
            return self._route_debate(context)
        elif scenario == "intervention_simulation":
            return self._route_intervention(context)
        else:
            return AgentOutput(
                success=False,
                errors=[f"Unknown scenario: {scenario}"],
            )

    def _route_quick(self, context: Dict[str, Any]) -> AgentOutput:
        """Route to quick assessment workflow.

        Args:
            context: Contains 'biomarkers' key.

        Returns:
            Assessment results.
        """
        from src.integrator import AgingIntegrator
        from src.clocks import ClockRegistry
        from src.clocks.phenoage import PhenoAgeClock
        from src.clocks.kdm import KDMClock
        from src.clocks.dnn import DNNClock
        from src.clocks.lifeclock import LifeClock

        biomarkers = context.get("biomarkers", {})
        registry = ClockRegistry()
        registry.clear()
        registry.register(phenoage=PhenoAgeClock())
        registry.register(kdm=KDMClock())
        registry.register(dnn=DNNClock())
        registry.register(lifeclock=LifeClock())

        integrator = AgingIntegrator(registry=registry)
        result = integrator.assess(biomarkers)

        return AgentOutput(
            success=True,
            data={
                "biological_age": result.biological_age,
                "chronological_age": result.chronological_age,
                "age_acceleration": result.age_acceleration,
                "clock_results": [
                    {"name": c.clock_name, "age": c.predicted_age, "status": c.status}
                    for c in result.clock_results
                ],
            },
        )

    def _route_debate(self, context: Dict[str, Any]) -> AgentOutput:
        """Route to full debate workflow (Stage 2 integration).

        Args:
            context: Contains 'biomarkers' and 'proposition'.

        Returns:
            Debate results with integrated assessment.
        """
        biomarkers = context.get("biomarkers", {})
        proposition = context.get("proposition", "")

        # Quick assessment first
        quick = self._route_quick(context)
        if not quick.success:
            return quick

        # Run debate
        debate_result = run_debate_pipeline(
            biomarkers=biomarkers,
            proposition=proposition,
            assessment=quick.data,
        )

        return AgentOutput(
            success=True,
            data={
                "assessment": quick.data,
                "debate": debate_result,
            },
        )

    def _route_intervention(self, context: Dict[str, Any]) -> AgentOutput:
        """Route to intervention simulation workflow.

        Args:
            context: Contains 'assessment' and 'scenarios'.

        Returns:
            Intervention predictions.
        """
        from .executor import Executor
        from .protocols import InterventionScenario

        assessment = context.get("assessment", {})
        raw_scenarios = context.get("scenarios", [])

        executor = Executor()
        predictions = []

        for sc in raw_scenarios:
            scenario = InterventionScenario(**sc) if isinstance(sc, dict) else sc
            pred = executor.simulate(scenario, assessment)
            predictions.append(pred.model_dump())

        return AgentOutput(
            success=True,
            data={
                "predictions": predictions,
            },
        )


def run_debate_pipeline(
    biomarkers: Dict[str, Any],
    proposition: str = "",
    assessment: Optional[Dict[str, Any]] = None,
    max_rounds: int = 3,
) -> Dict[str, Any]:
    """Execute the full debate pipeline: Assessment → Skeptic → Pro/Con → Judge.

    Args:
        biomarkers: Input biomarker data.
        proposition: The proposition to debate.
        assessment: Pre-computed assessment data.
        max_rounds: Maximum debate rounds.

    Returns:
        Debate results including rounds, winner, and consensus.
    """
    from .skeptic import Skeptic
    from .pro_debater import ProDebater
    from .con_debater import ConDebater
    from .judge import Judge

    if not proposition:
        bio_age = assessment.get("biological_age", 0) if assessment else 0
        chron_age = biomarkers.get("age", 0)
        if bio_age > chron_age + 2:
            proposition = f"该受试者存在加速衰老（生物年龄{bio_age:.1f}岁 vs 日历年龄{chron_age:.0f}岁），应优先进行免疫和代谢维度干预"
        elif bio_age < chron_age - 2:
            proposition = f"该受试者衰老速度较慢（生物年龄{bio_age:.1f}岁 vs 日历年龄{chron_age:.0f}岁），应维持当前生活方式"
        else:
            proposition = f"该受试者衰老速度正常（生物年龄{bio_age:.1f}岁 vs 日历年龄{chron_age:.0f}岁），建议持续监测"

    skeptic = Skeptic()
    pro = ProDebater()
    con = ConDebater()
    judge = Judge(max_rounds=max_rounds)

    # Skeptic review
    skeptic_output = skeptic.execute({
        "biomarkers": biomarkers,
        "assessment": assessment or {},
    })

    rounds = []
    current_proposition = proposition

    for r in range(1, max_rounds + 1):
        pro_output = pro.execute({
            "proposition": current_proposition,
            "biomarkers": biomarkers,
            "assessment": assessment or {},
            "round": r,
            "previous_rounds": rounds,
            "skeptic_notes": skeptic_output.data,
        })

        con_output = con.execute({
            "proposition": current_proposition,
            "biomarkers": biomarkers,
            "assessment": assessment or {},
            "round": r,
            "previous_rounds": rounds,
            "pro_arguments": pro_output.data.get("arguments", []),
            "skeptic_notes": skeptic_output.data,
        })

        judge_output = judge.evaluate_round(
            proposition=current_proposition,
            pro_arguments=pro_output.data.get("arguments", []),
            con_arguments=con_output.data.get("arguments", []),
            round_number=r,
            previous_rounds=rounds,
        )

        rounds.append(judge_output.model_dump())

        if judge.should_terminate():
            break

    final = judge.final_verdict(rounds)

    return {
        "proposition": proposition,
        "rounds": rounds,
        "winner": final.get("winner"),
        "final_score": final.get("final_score"),
        "consensus_notes": final.get("consensus_notes", ""),
        "skeptic_notes": skeptic_output.data,
    }
