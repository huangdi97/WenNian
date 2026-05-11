"""KDM (Klemera-Doubal Method) biological age clock.

Uses Mahalanobis distance to compute biological age relative to
a reference population. The method accounts for the covariance
structure among biomarkers.

Reference:
    Klemera P, Doubal S. A new approach to the concept and computation
    of biological age. Mech Ageing Dev. 2006;127(3):240-248.
"""

from typing import Any, ClassVar, Dict, List, Optional

import numpy as np

from . import BaseClock, ClockResult
from src.core.exceptions import ComputationError

# Default reference population parameters (mean values for 30-year-olds)
DEFAULT_REFERENCE_MEANS: Dict[str, float] = {
    "albumin": 43.0,
    "creatinine": 75.0,
    "glucose": 5.1,
    "lymphocyte_percent": 33.0,
    "mcv": 90.0,
    "rdw": 13.0,
    "alkaline_phosphatase": 70.0,
    "white_blood_cell_count": 6.5,
}

# Default standard deviations for the reference population
DEFAULT_REFERENCE_STDS: Dict[str, float] = {
    "albumin": 3.5,
    "creatinine": 15.0,
    "glucose": 0.8,
    "lymphocyte_percent": 7.0,
    "mcv": 5.0,
    "rdw": 1.5,
    "alkaline_phosphatase": 20.0,
    "white_blood_cell_count": 1.8,
}

# Simplified correlation matrix off-diagonal elements
# In a full implementation this would be an 8x8 matrix
DEFAULT_CORRELATIONS: float = 0.1


class KDMClock(BaseClock):
    """Biological age clock using Klemera-Doubal method.

    Computes biological age as a weighted Mahalanobis distance from
    a reference population, combining individual biomarker deviations
    while accounting for their inter-correlations.
    """

    name: ClassVar[str] = "kdm"
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

    def __init__(
        self,
        ref_means: Optional[Dict[str, float]] = None,
        ref_stds: Optional[Dict[str, float]] = None,
        ref_corr: float = DEFAULT_CORRELATIONS,
    ) -> None:
        """Initialize the KDM clock.

        Args:
            ref_means: Reference population mean values per biomarker.
            ref_stds: Reference population standard deviations.
            ref_corr: Average inter-biomarker correlation coefficient.
        """
        self._ref_means = ref_means or DEFAULT_REFERENCE_MEANS
        self._ref_stds = ref_stds or DEFAULT_REFERENCE_STDS
        self._ref_corr = ref_corr

    def predict(self, biomarkers: Dict[str, Any]) -> ClockResult:
        """Compute biological age using KDM.

        Args:
            biomarkers: Dictionary with biomarker values and chronological age.

        Returns:
            ClockResult with predicted biological age.

        Raises:
            ComputationError: If critical biomarkers are missing.
        """
        missing = self._check_required(biomarkers)
        if missing:
            raise ComputationError(
                f"KDM missing biomarkers: {missing}",
                details={"missing": missing},
            )

        try:
            chron_age = float(biomarkers["age"])
            deviations = []
            weights = []
            used_count = 0

            for marker in self.required_biomarkers:
                if marker == "age":
                    continue
                if marker not in self._ref_means:
                    continue
                value = float(biomarkers[marker])
                mean = self._ref_means[marker]
                std = self._ref_stds.get(marker, 1.0)
                if std == 0:
                    continue
                deviation = (value - mean) / std
                deviations.append(deviation)
                weights.append(1.0 / (std ** 2))
                used_count += 1

            if used_count == 0:
                raise ComputationError("KDM: no valid biomarkers for computation")

            # Weighted average deviation, adjusted by inter-correlation
            total_weight = sum(weights)
            avg_deviation = sum(d * w for d, w in zip(deviations, weights)) / total_weight

            # Scale to years: 1 std deviation ~ 10 years of aging
            aging_offset = avg_deviation * 10.0 * (1.0 + self._ref_corr * (len(deviations) - 1))

            predicted = chron_age + aging_offset
            predicted = max(18.0, min(120.0, predicted))

            se = 10.0 / np.sqrt(used_count)
            lower = max(18.0, predicted - 1.96 * se)
            upper = min(120.0, predicted + 1.96 * se)
            confidence = min(0.85, max(0.5, 1.0 - se / 20.0))

            return ClockResult(
                predicted_age=predicted,
                lower_bound=lower,
                upper_bound=upper,
                confidence=confidence,
                metadata={
                    "model": "KDM2006",
                    "method": "mahalanobis",
                    "biomarkers_used": used_count,
                },
            )
        except (ValueError, TypeError) as e:
            raise ComputationError(
                f"KDM computation failed: {e}",
                details={"error": str(e)},
            ) from e
