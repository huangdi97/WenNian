"""LifeClock — simplified biological age clock based on clinical ranges.

Uses z-score deviations from clinical reference ranges to estimate
biological age acceleration. Provides a lightweight alternative when
more sophisticated clocks cannot be fully computed.

Reference:
    Adapted from clinical reference range methodology.
    Belsky DW et al. eLife. 2022;11:e73420.
"""

from typing import Any, ClassVar, Dict, List

from . import BaseClock, ClockResult
from src.core.exceptions import ComputationError

# Clinical reference ranges (lower, upper) for healthy adults 30-50
REFERENCE_RANGES: Dict[str, tuple] = {
    "albumin": (35, 50),          # g/L
    "creatinine": (50, 110),      # umol/L
    "glucose": (3.9, 6.1),        # mmol/L (fasting)
    "lymphocyte_percent": (20, 40),  # %
    "mcv": (80, 100),             # fL
    "rdw": (11.5, 14.5),          # %
    "alkaline_phosphatase": (40, 130),  # U/L
    "white_blood_cell_count": (4.0, 10.0),  # 10^9/L
}

# Age-related drift per decade per biomarker (approximate)
AGE_DRIFT: Dict[str, float] = {
    "albumin": -0.5,
    "creatinine": 3.0,
    "glucose": 0.15,
    "lymphocyte_percent": -0.5,
    "mcv": 1.0,
    "rdw": 0.3,
    "alkaline_phosphatase": 5.0,
    "white_blood_cell_count": 0.1,
}


class LifeClock(BaseClock):
    """Simplified biological age clock using clinical reference ranges.

    Computes a z-score-based aging acceleration by comparing biomarker
    values against established clinical reference ranges and known
    age-related drift patterns.
    """

    name: ClassVar[str] = "lifeclock"
    version: ClassVar[str] = "1.0.0"
    required_biomarkers: ClassVar[List[str]] = [
        "albumin",
        "creatinine",
        "glucose",
        "lymphocyte_percent",
        "mcv",
        "rdw",
        "alkaline_phosphatase",
        "white_blood_cell_count",
        "age",
    ]

    def predict(self, biomarkers: Dict[str, Any]) -> ClockResult:
        """Compute biological age via clinical reference deviation.

        Args:
            biomarkers: Dictionary with biomarker values and age.

        Returns:
            ClockResult with predicted biological age.

        Raises:
            ComputationError: If required biomarkers are missing.
        """
        missing = self._check_required(biomarkers)
        if missing:
            raise ComputationError(
                f"LifeClock missing biomarkers: {missing}",
                details={"missing": missing},
            )

        try:
            chron_age = float(biomarkers["age"])
            z_scores = []
            weights = []

            for marker in self.required_biomarkers:
                if marker == "age":
                    continue
                if marker not in REFERENCE_RANGES:
                    continue
                value = float(biomarkers[marker])
                low, high = REFERENCE_RANGES[marker]
                mid = (low + high) / 2.0
                ref_range = (high - low) / 2.0
                if ref_range == 0:
                    continue
                # Expected value for the person's age (relative to age 40 baseline)
                decades_from_40 = (chron_age - 40.0) / 10.0
                expected = mid + AGE_DRIFT.get(marker, 0.0) * decades_from_40
                z = (value - expected) / ref_range
                z_scores.append(z)
                weights.append(1.0)

            if not z_scores:
                raise ComputationError("LifeClock: no valid biomarkers for computation")

            avg_z = sum(z * w for z, w in zip(z_scores, weights)) / sum(weights)

            # Each z-score unit corresponds to ~8 years of age acceleration
            age_acceleration = avg_z * 8.0
            predicted = chron_age + age_acceleration
            predicted = max(18.0, min(120.0, predicted))

            se = 8.0 / (len(z_scores) ** 0.5)
            lower = max(18.0, predicted - 1.96 * se)
            upper = min(120.0, predicted + 1.96 * se)
            confidence = min(0.91, max(0.4, 1.0 - se / 25.0))

            return ClockResult(
                predicted_age=predicted,
                lower_bound=lower,
                upper_bound=upper,
                confidence=confidence,
                metadata={
                    "model": "LifeClock_v1",
                    "method": "clinical_reference",
                    "age_acceleration": age_acceleration,
                },
            )
        except (ValueError, TypeError) as e:
            raise ComputationError(
                f"LifeClock computation failed: {e}",
                details={"error": str(e)},
            ) from e
