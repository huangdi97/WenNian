"""Auditor agent — independent audit of assessment outputs.

Performs red-line scanning, numerical consistency checks, and
disclaimer verification on the final output before delivery.
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from . import BaseAgent, AgentOutput, CapabilityToken

DEFAULT_AGENT_ID = "auditor.v1"

# Default red-line patterns — configurable via configuration
DEFAULT_REDLINE_PATTERNS: List[str] = [
    r"(?i)(建议服用|推荐用药|处方|开具|配药|治疗建议|诊断结果|确诊)",
    r"(?i)(guarantee.*cure|cure.*guarantee|治愈|根治|包治)",
    r"(?i)(一定有效|100%有效|百分百有效|绝对有效)",
    r"(?i)(无需医生|不需要医生|替代医生|取代诊断)",
]


class AuditResult(BaseModel):
    """Result of the auditor's review.

    Attributes:
        passed: True if no violations found.
        violations: List of violation descriptions.
        recommendations: Suggested improvements.
    """

    passed: bool = True
    violations: List[str] = []
    recommendations: List[str] = []


class Auditor(BaseAgent):
    """Independent audit agent for compliance and quality assurance.

    Scans output content for prohibited patterns, verifies numerical
    consistency of reported ages, and ensures mandatory disclaimers
    are present.

    Args:
        redline_patterns: List of regex patterns that trigger violations.
        agent_id: Unique identifier for this agent instance.
        capability: Capability token for access control.
    """

    def __init__(
        self,
        redline_patterns: Optional[List[str]] = None,
        agent_id: str = DEFAULT_AGENT_ID,
        capability: CapabilityToken = None,
    ) -> None:
        super().__init__(agent_id=agent_id, capability=capability)
        self._redline_patterns = redline_patterns or DEFAULT_REDLINE_PATTERNS
        self._compiled = [re.compile(p) for p in self._redline_patterns]

    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        """Execute the full audit on the provided output context.

        Args:
            context: Should contain:
                - ``report_text``: The full markdown report text.
                - ``biological_age``: The fused biological age value.
                - ``chronological_age``: The chronological age value.

        Returns:
            AgentOutput with audit results.
        """
        audit = AuditResult()

        report_text = context.get("report_text", "")
        bio_age = context.get("biological_age", 0)
        chron_age = context.get("chronological_age", 0)

        # Red-line scan
        self._scan_redlines(report_text, audit)

        # Numerical consistency
        self._check_consistency(bio_age, chron_age, audit)

        # Disclaimer check
        self._check_disclaimer(report_text, audit)

        return AgentOutput(
            success=audit.passed,
            data={
                "passed": audit.passed,
                "violations": audit.violations,
                "recommendations": audit.recommendations,
            },
        )

    def _scan_redlines(self, text: str, audit: AuditResult) -> None:
        """Scan text for prohibited patterns.

        Args:
            text: The content to scan.
            audit: AuditResult to populate with violations.
        """
        for i, pattern in enumerate(self._compiled):
            matches = pattern.findall(text)
            for match in matches:
                match_str = match if isinstance(match, str) else match[0]
                audit.violations.append(
                    f"Red-line violation (pattern {i}): '{match_str}'"
                )
                audit.passed = False

    @staticmethod
    def _check_consistency(bio_age: float, chron_age: float, audit: AuditResult) -> None:
        """Verify numerical consistency between biological and chronological age.

        Args:
            bio_age: Reported biological age.
            chron_age: Reported chronological age.
            audit: AuditResult to populate.
        """
        try:
            bio = float(bio_age)
            chron = float(chron_age)
            if bio < 0 or bio > 150:
                audit.violations.append(f"Biological age {bio} is outside plausible range [0, 150]")
                audit.passed = False
            if abs(bio - chron) > 60:
                audit.violations.append(
                    f"Biological age ({bio}) differs from chronological age ({chron}) by > 60 years; verify"
                )
                audit.passed = False
        except (ValueError, TypeError):
            audit.violations.append("Age values are not valid numbers")
            audit.passed = False

    @staticmethod
    def _check_disclaimer(text: str, audit: AuditResult) -> None:
        """Check that the mandatory disclaimer is present.

        Args:
            text: The content to scan.
            audit: AuditResult to populate.
        """
        required_phrases = ["不构成医疗诊断", "disclaimer", "免责"]
        found = any(phrase.lower() in text.lower() for phrase in required_phrases)
        if not found:
            audit.violations.append("Missing mandatory medical disclaimer")
            audit.passed = False
