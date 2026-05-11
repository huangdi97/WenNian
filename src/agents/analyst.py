"""Analyst agent — runs aging assessment and produces structured results.

The Analyst is the primary assessment agent: it receives user biomarker
input, runs the AgingIntegrator, collects per-clock results, and returns
a structured evaluation.
"""

from typing import Any, Dict

from . import BaseAgent, AgentOutput, CapabilityToken
from src.integrator import AgingIntegrator, IntegratedReport

DEFAULT_AGENT_ID = "analyst.v1"


class Analyst(BaseAgent):
    """Primary aging assessment agent.

    Orchestrates biomarker assessment by invoking the AgingIntegrator
    and packaging results into a standardized output.

    Args:
        integrator: The AgingIntegrator to use for assessments.
        agent_id: Unique identifier for this agent instance.
        capability: Capability token for access control.
    """

    def __init__(
        self,
        integrator: AgingIntegrator,
        agent_id: str = DEFAULT_AGENT_ID,
        capability: CapabilityToken = None,
    ) -> None:
        super().__init__(agent_id=agent_id, capability=capability)
        self._integrator = integrator

    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        """Run the full aging assessment.

        Expects ``context["biomarkers"]`` to contain the input data.

        Args:
            context: Must include a 'biomarkers' key.

        Returns:
            AgentOutput with the integrated report and per-clock details.
        """
        biomarkers = context.get("biomarkers", {})
        if not biomarkers:
            return AgentOutput(
                success=False,
                errors=["No biomarkers provided"],
                data={},
            )

        try:
            report: IntegratedReport = self._integrator.assess(biomarkers)
            return AgentOutput(
                success=True,
                data={
                    "chronological_age": report.chronological_age,
                    "biological_age": report.biological_age,
                    "age_acceleration": report.age_acceleration,
                    "confidence": report.confidence,
                    "lower_bound": report.lower_bound,
                    "upper_bound": report.upper_bound,
                    "clock_results": [
                        {
                            "name": cr.clock_name,
                            "predicted_age": cr.predicted_age,
                            "confidence": cr.confidence,
                            "status": cr.status,
                        }
                        for cr in report.clock_results
                    ],
                    "warnings": report.warnings,
                },
                metadata={"integrator_version": "2.0"},
            )
        except Exception as e:
            self.log(f"Assessment failed: {e}", "ERROR")
            return AgentOutput(
                success=False,
                errors=[str(e)],
                data={},
            )
