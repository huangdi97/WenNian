"""Aging integrator — orchestrates all registered clocks and produces fused assessments.

Coordinates the execution of all registered aging clocks, computes a
weighted fusion of their predictions, and produces a unified report
with per-clock details and confidence metrics.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import math

from pydantic import BaseModel

from src.clocks import ClockRegistry, ClockResult, BaseClock
from src.core.exceptions import ComputationError


class ClockOutput(BaseModel):
    """Individual clock prediction output within the integrated report.

    Attributes:
        clock_name: Identifier of the clock.
        predicted_age: Biological age prediction.
        lower_bound: Lower confidence bound.
        upper_bound: Upper confidence bound.
        confidence: Clock-level confidence.
        status: 'ok' if successful, otherwise error description.
        metadata: Additional clock metadata.
    """

    clock_name: str
    predicted_age: float = 0.0
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: float = 0.0
    status: str = "ok"
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntegratedReport(BaseModel):
    """Complete integrated aging assessment.

    Attributes:
        chronological_age: The subject's chronological age.
        biological_age: Weighted fusion of all clock predictions.
        lower_bound: Lower confidence bound of the fused estimate.
        upper_bound: Upper confidence bound of the fused estimate.
        confidence: Overall confidence in the fused estimate.
        age_acceleration: Difference between biological and chronological age.
        clock_results: Per-clock prediction details.
        warnings: Aggregated warnings from the integration process.
        organ_ages: Optional organ-specific aging assessments (Stage 2).
        top_drivers: Optional top aging driver dimensions (Stage 2).
    """

    chronological_age: float = 0.0
    biological_age: float = 0.0
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: float = 0.0
    age_acceleration: float = 0.0
    ensemble_std: float = 0.0
    clock_results: List[ClockOutput] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    organ_ages: Optional[List[Any]] = None
    top_drivers: Optional[List[Dict[str, Any]]] = None


class AgingIntegrator:
    """Orchestrates aging clocks and produces fused biological age estimates.

    Schedules all registered clocks, collects their predictions, and
    computes a weighted average based on per-clock confidence and
    configured weights.

    Args:
        registry: The ClockRegistry to source clocks from.
        weights: Optional dictionary mapping clock_id → weight.
                 Defaults to equal weighting.
    """

    def __init__(
        self,
        registry: Optional[ClockRegistry] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self._registry = registry or ClockRegistry()
        self._weights = weights or {}

    def assess(self, biomarkers: Dict[str, Any]) -> IntegratedReport:
        """Run all registered clocks and produce a fused assessment.

        Args:
            biomarkers: Dictionary of biomarker name → value.

        Returns:
            IntegratedReport with fused biological age and per-clock details.

        Raises:
            ComputationError: If no clocks are registered or all fail.
        """
        clock_ids = self._registry.list_all()
        if not clock_ids:
            raise ComputationError("No clocks registered in the registry")

        chron_age = float(biomarkers.get("age", 0))
        report = IntegratedReport(chronological_age=chron_age)
        predictions: List[tuple] = []  # (predicted_age, weight, confidence)

        for cid in clock_ids:
            clock = self._registry.get(cid)
            if clock is None:
                continue
            clock_out = self._run_clock(clock, cid, biomarkers)
            report.clock_results.append(clock_out)
            if clock_out.status == "ok":
                weight = self._weights.get(cid, 1.0)
                predictions.append((clock_out.predicted_age, weight, clock_out.confidence))

        if not predictions:
            raise ComputationError("All clocks failed to produce valid predictions")

        total_weight = sum(p[1] for p in predictions)
        if total_weight == 0:
            report.biological_age = chron_age
            report.confidence = 0.1
            return report

        # Weighted fusion
        fused = sum(p[0] * p[1] for p in predictions) / total_weight
        fused_confidence = sum(p[2] * p[1] for p in predictions) / total_weight

        # Compute ensemble-based confidence interval
        n_clocks = len(predictions)
        ages = [p[0] for p in predictions]
        if n_clocks > 1:
            ensemble_std = math.sqrt(sum((a - fused) ** 2 for a in ages) / (n_clocks - 1))
        else:
            ensemble_std = 5.0

        se = ensemble_std / math.sqrt(max(n_clocks, 1))
        fused_lower = max(20.0, fused - 1.96 * se)
        fused_upper = min(100.0, fused + 1.96 * se)

        # If clock predictions are highly inconsistent, widen interval and warn
        ci_width = fused_upper - fused_lower
        if ci_width > 20:
            report.warnings.append(
                f"时钟间一致性偏低(集成标准差={ensemble_std:.1f}岁, CI宽度={ci_width:.1f}岁)，建议关注各时钟独立结果"
            )
            # Widen to min/max of individual bounds as fallback
            bounds = [(c.lower_bound, c.upper_bound) for c in report.clock_results
                       if c.status == "ok" and c.lower_bound is not None and c.upper_bound is not None]
            if bounds:
                fused_lower = min(fused_lower, min(b[0] for b in bounds))
                fused_upper = max(fused_upper, max(b[1] for b in bounds))

        report.biological_age = fused
        report.lower_bound = fused_lower
        report.upper_bound = fused_upper
        report.confidence = fused_confidence
        report.age_acceleration = fused - chron_age
        report.ensemble_std = round(ensemble_std, 2)

        # Stage 2: Organ-level aging and main driver identification
        try:
            from src.dimensions import assess_organ_ages, identify_top_drivers
            organ_ages = assess_organ_ages(biomarkers, chron_age)
            if organ_ages:
                report.organ_ages = [
                    {
                        "organ": oa.organ,
                        "estimated_age": oa.estimated_age,
                        "asynchrony_score": oa.asynchrony_score,
                        "inflection_age": oa.inflection_age,
                    }
                    for oa in organ_ages
                ]
                report.top_drivers = identify_top_drivers(organ_ages, top_n=3)
        except Exception:
            pass

        return report

    def _run_clock(
        self, clock: BaseClock, clock_id: str, biomarkers: Dict[str, Any]
    ) -> ClockOutput:
        """Execute a single clock and wrap its result.

        Args:
            clock: The clock instance.
            clock_id: Registry identifier for the clock.
            biomarkers: Input biomarker data.

        Returns:
            ClockOutput with prediction result or error status.
        """
        try:
            result = clock.predict(biomarkers)
            return ClockOutput(
                clock_name=clock_id,
                predicted_age=result.predicted_age,
                lower_bound=result.lower_bound,
                upper_bound=result.upper_bound,
                confidence=result.confidence,
                status="ok",
                metadata=result.metadata,
            )
        except Exception as e:
            return ClockOutput(
                clock_name=clock_id,
                predicted_age=0.0,
                confidence=0.0,
                status=f"error: {e}",
            )
