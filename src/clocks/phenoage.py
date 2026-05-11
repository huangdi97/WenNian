"""PhenoAge clock implementation based on Levine 2018.

Reference:
    Levine ME. An epigenetic biomarker of aging for lifespan and healthspan.
    Aging (Albany NY). 2018;10(4):573-591. PMID: 29676998

The PhenoAge clock uses 9 blood chemistry biomarkers plus chronological age
to predict biological age via a linear model.
"""

from typing import Any, ClassVar, Dict, List, Optional

import numpy as np

from . import BaseClock, ClockResult
from src.core.exceptions import ComputationError

# Levine 2018 10-parameter model coefficients
# Biomarkers: albumin, creatinine, glucose, c_reactive_protein,
#             lymphocyte_percent, mcv, rdw, alkaline_phosphatase,
#             white_blood_cell_count, chronological_age
PHENOAGE_COEFFICIENTS: Dict[str, float] = {
    "albumin": -0.0336,
    "creatinine": 0.0095,
    "glucose": 0.1953,
    "c_reactive_protein": 0.0954,
    "lymphocyte_percent": -0.0120,
    "mcv": 0.0268,
    "rdw": 0.3306,
    "alkaline_phosphatase": 0.00188,
    "white_blood_cell_count": 0.0554,
    "age": 0.0804,
}

# Intercept for the linear predictor
PHENOAGE_INTERCEPT = 19.9067

# Biomarker units and transformation notes:
# albumin: g/L (serum)
# creatinine: umol/L (serum)
# glucose: mmol/L (serum, fasting)
# c_reactive_protein: mg/L (log-transformed)
# lymphocyte_percent: % of WBC
# mcv: fL (mean corpuscular volume)
# rdw: % (red cell distribution width)
# alkaline_phosphatase: U/L
# white_blood_cell_count: 10^9/L


class PhenoAgeClock(BaseClock):
    """PhenoAge biological age clock (Levine 2018).

    Implements the 10-parameter linear model that predicts biological age
    from standard clinical blood chemistry markers plus chronological age.
    """

    name: ClassVar[str] = "phenoage"
    version: ClassVar[str] = "1.0.0"
    required_biomarkers: ClassVar[List[str]] = [
        "albumin",
        "creatinine",
        "glucose",
        "c_reactive_protein",
        "lymphocyte_percent",
        "mcv",
        "rdw",
        "alkaline_phosphatase",
        "white_blood_cell_count",
        "age",
    ]

    def __init__(self, coefficients: Optional[Dict[str, float]] = None) -> None:
        """Initialize the PhenoAge clock.

        Args:
            coefficients: Optional custom coefficient overrides.
                          Defaults to the Levine 2018 published values.
        """
        self._coeffs = coefficients or PHENOAGE_COEFFICIENTS

    def predict(self, biomarkers: Dict[str, Any]) -> ClockResult:
        """Compute PhenoAge from biomarker values.

        Args:
            biomarkers: Dictionary with keys matching required_biomarkers.

        Returns:
            ClockResult with predicted age and confidence.

        Raises:
            ComputationError: If required biomarkers are missing.
        """
        missing = self._check_required(biomarkers)
        if missing:
            raise ComputationError(
                f"PhenoAge missing biomarkers: {missing}",
                details={"missing": missing},
            )

        try:
            linear_predictor = self._intercept
            for marker, coeff in self._coeffs.items():
                value = float(biomarkers.get(marker, 0))
                linear_predictor += coeff * value

            predicted = linear_predictor
            lower = predicted - 5.0
            upper = predicted + 5.0
            confidence = min(0.9, max(0.5, 1.0 - abs(predicted - float(biomarkers["age"])) / 30.0))

            return ClockResult(
                predicted_age=predicted,
                lower_bound=lower,
                upper_bound=upper,
                confidence=confidence,
                metadata={"model": "Levine2018", "method": "linear"},
            )
        except (ValueError, TypeError) as e:
            raise ComputationError(
                f"PhenoAge computation failed: {e}",
                details={"error": str(e)},
            ) from e

    @property
    def _intercept(self) -> float:
        return PHENOAGE_INTERCEPT
