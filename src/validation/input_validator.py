"""Input validation for biomarker data with hard bounds, soft warnings, and contradiction detection.

Implements three levels of validation:
1. Hard limits — physically/biologically impossible values → reject
2. Soft thresholds — extreme but possible values → warn
3. Contradiction detection — mutually inconsistent values → flag
"""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from src.core.exceptions import ValidationError

# Hard physiological limits (value outside = rejected)
HARD_LIMITS: Dict[str, Tuple[float, float]] = {
    "age": (0, 130),
    "albumin": (10, 80),               # g/L
    "creatinine": (10, 2000),           # umol/L
    "glucose": (1, 50),                 # mmol/L
    "c_reactive_protein": (0, 500),     # mg/L
    "lymphocyte_percent": (0, 100),     # %
    "mcv": (50, 150),                   # fL
    "rdw": (8, 35),                     # %
    "alkaline_phosphatase": (5, 2000),  # U/L
    "white_blood_cell_count": (0.1, 100),  # 10^9/L
    "cholesterol_total": (1, 20),       # mmol/L
    "hdl": (0.1, 5),                    # mmol/L
    "ldl": (0.1, 15),                   # mmol/L
    "triglycerides": (0.1, 50),         # mmol/L
    "systolic_bp": (50, 300),           # mmHg
    "diastolic_bp": (20, 200),          # mmHg
    "bmi": (10, 70),                    # kg/m²
    "hemoglobin": (20, 250),            # g/L
    "platelets": (10, 2000),            # 10^9/L
    "alt": (1, 5000),                   # U/L
    "ast": (1, 5000),                   # U/L
    "bilirubin": (1, 500),              # umol/L
    "egfr": (1, 200),                   # mL/min/1.73m²
}

# Soft thresholds (outside = warning, but not rejected)
SOFT_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "age": (18, 100),
    "albumin": (30, 55),
    "creatinine": (30, 150),
    "glucose": (3.5, 8.0),
    "c_reactive_protein": (0, 10),
    "lymphocyte_percent": (15, 50),
    "mcv": (75, 105),
    "rdw": (11, 16),
    "alkaline_phosphatase": (30, 150),
    "white_blood_cell_count": (3.5, 12.0),
    "cholesterol_total": (3.0, 7.0),
    "hdl": (0.8, 2.5),
    "ldl": (1.0, 5.0),
    "systolic_bp": (90, 160),
    "diastolic_bp": (60, 100),
    "bmi": (16, 40),
}

# Contradiction rules: (marker1, marker2, condition_fn_name, description)
# Each rule is a tuple: (marker_a, marker_b, predicate, message)
CONTRADICTIONS: List[Dict[str, Any]] = [
    {
        "markers": ["alt", "bilirubin"],
        "predicate": "alt_high_bilirubin_normal",
        "description": "ALT > 200 U/L with normal bilirubin is unusual; suggests lab error or specific pathology",
    },
    {
        "markers": ["systolic_bp", "diastolic_bp"],
        "predicate": "bp_inversion",
        "description": "Diastolic BP should be less than systolic BP",
    },
    {
        "markers": ["ldl", "cholesterol_total"],
        "predicate": "ldl_greater_than_total",
        "description": "LDL cholesterol should not exceed total cholesterol",
    },
    {
        "markers": ["hdl", "ldl"],
        "predicate": "hdl_ldl_exceed_total",
        "description": "HDL + LDL should not exceed total cholesterol by more than 10%",
    },
    {
        "markers": ["egfr", "creatinine"],
        "predicate": "egfr_creatinine_mismatch",
        "description": "eGFR should be inversely related to creatinine",
    },
]


class ValidationResult(BaseModel):
    """Output of the input validation process.

    Attributes:
        is_valid: True if no hard limit violations.
        warnings: List of soft threshold warning messages.
        errors: List of hard limit violation messages.
        contradictions: List of detected contradictory values.
    """

    is_valid: bool = True
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)


class InputValidator:
    """Validator for biomarker input data.

    Applies hard limits, soft thresholds, and contradiction checks
    in sequence. Hard limit failures invalidate the input; soft threshold
    and contradiction failures produce warnings.
    """

    def __init__(
        self,
        hard_limits: Optional[Dict[str, Tuple[float, float]]] = None,
        soft_thresholds: Optional[Dict[str, Tuple[float, float]]] = None,
        contradictions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._hard_limits = hard_limits or HARD_LIMITS
        self._soft_thresholds = soft_thresholds or SOFT_THRESHOLDS
        self._contradictions = contradictions or CONTRADICTIONS

    def validate(self, biomarkers: Dict[str, Any]) -> ValidationResult:
        """Run all validation checks on biomarker data.

        Args:
            biomarkers: Dictionary of biomarker name → value.

        Returns:
            ValidationResult with errors, warnings, and contradictions.
        """
        result = ValidationResult()

        self._check_hard_limits(biomarkers, result)
        self._check_soft_thresholds(biomarkers, result)
        self._check_contradictions(biomarkers, result)

        return result

    def _check_hard_limits(
        self, biomarkers: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate values against hard physiological limits.

        Args:
            biomarkers: Input biomarker dictionary.
            result: ValidationResult to mutate.
        """
        for key, (low, high) in self._hard_limits.items():
            if key not in biomarkers:
                continue
            try:
                value = float(biomarkers[key])
            except (TypeError, ValueError):
                result.errors.append(f"{key}: cannot convert '{biomarkers[key]}' to number")
                result.is_valid = False
                continue
            if value < low or value > high:
                msg = f"{key}: {value} outside hard limits [{low}, {high}]"
                result.errors.append(msg)
                result.is_valid = False

    def _check_soft_thresholds(
        self, biomarkers: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check values against soft (warning) thresholds.

        Args:
            biomarkers: Input biomarker dictionary.
            result: ValidationResult to mutate.
        """
        for key, (low, high) in self._soft_thresholds.items():
            if key not in biomarkers:
                continue
            try:
                value = float(biomarkers[key])
            except (TypeError, ValueError):
                continue
            if value < low:
                result.warnings.append(
                    f"{key}: {value} is below typical range [{low}, {high}]; consider verifying"
                )
            elif value > high:
                result.warnings.append(
                    f"{key}: {value} is above typical range [{low}, {high}]; consider verifying"
                )

    def _check_contradictions(
        self, biomarkers: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Detect logically contradictory biomarker values.

        Args:
            biomarkers: Input biomarker dictionary.
            result: ValidationResult to mutate.
        """
        for rule in self._contradictions:
            markers = rule["markers"]
            if not all(m in biomarkers for m in markers):
                continue
            predicate_name = rule["predicate"]
            checker = getattr(self, f"_check_{predicate_name}", None)
            if checker is None:
                continue
            if checker(biomarkers):
                result.contradictions.append(rule["description"])

    @staticmethod
    def _check_alt_high_bilirubin_normal(bio: Dict[str, Any]) -> bool:
        """ALT > 200 but bilirubin < 20 is contradictory."""
        try:
            alt = float(bio["alt"])
            bil = float(bio["bilirubin"])
            return alt > 200 and bil < 20
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _check_bp_inversion(bio: Dict[str, Any]) -> bool:
        """Diastolic > systolic is contradictory."""
        try:
            return float(bio["diastolic_bp"]) > float(bio["systolic_bp"])
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _check_ldl_greater_than_total(bio: Dict[str, Any]) -> bool:
        """LDL > total cholesterol is contradictory."""
        try:
            return float(bio["ldl"]) > float(bio["cholesterol_total"])
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _check_hdl_ldl_exceed_total(bio: Dict[str, Any]) -> bool:
        """HDL + LDL > total * 1.1 is contradictory."""
        try:
            total = float(bio["cholesterol_total"])
            return float(bio["hdl"]) + float(bio["ldl"]) > total * 1.1
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _check_egfr_creatinine_mismatch(bio: Dict[str, Any]) -> bool:
        """eGFR very low but creatinine low is contradictory."""
        try:
            return float(bio["egfr"]) < 15 and float(bio["creatinine"]) < 80
        except (ValueError, TypeError):
            return False
