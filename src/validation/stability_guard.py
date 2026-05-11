"""Stability guard — unified NaN/Inf handling and conservative fallback.

Ensures all numerical computations produce finite, valid results.
When NaN or Inf is detected, the guard applies a configurable
conservative fallback strategy.
"""

import math
from typing import Any, Callable, Dict, List, Optional, Union


class StabilityGuard:
    """Guards against numerical instability in computations.

    Wraps functions and scalars to ensure NaN/Inf values are
    replaced with conservative defaults. Provides diagnostics
    for debugging computational issues.

    Attributes:
        default_value: Fallback value for NaN/Inf scalars.
        max_value: Upper bound for clamping.
        min_value: Lower bound for clamping.
        raise_on_nan: If True, raise ComputationError instead of using fallback.
        log_violations: If True, log when NaN/Inf is detected.
    """

    def __init__(
        self,
        default_value: float = 0.0,
        max_value: Optional[float] = 120.0,
        min_value: Optional[float] = 0.0,
        raise_on_nan: bool = False,
        log_violations: bool = True,
    ) -> None:
        self.default_value = default_value
        self.max_value = max_value
        self.min_value = min_value
        self.raise_on_nan = raise_on_nan
        self.log_violations = log_violations
        self._violations: List[Dict[str, Any]] = []

    def guard_scalar(
        self,
        value: Any,
        name: str = "unknown",
        max_value: Optional[float] = None,
        min_value: Optional[float] = None,
    ) -> float:
        """Guard a single scalar value.

        Args:
            value: Input value (can be float, int, str, or None).
            name: Identifier for logging purposes.
            max_value: Override instance max_value for this call.
            min_value: Override instance min_value for this call.

        Returns:
            A valid finite float.
        """
        _max = max_value if max_value is not None else self.max_value
        _min = min_value if min_value is not None else self.min_value

        try:
            result = float(value)
        except (TypeError, ValueError):
            self._record_violation(name, f"Non-numeric: {value}")
            return self.default_value

        if math.isnan(result):
            self._record_violation(name, "NaN detected")
            if self.raise_on_nan:
                from src.core.exceptions import ComputationError
                raise ComputationError(f"NaN detected in {name}")
            return self.default_value

        if math.isinf(result):
            self._record_violation(name, "Inf detected")
            if self.raise_on_nan:
                from src.core.exceptions import ComputationError
                raise ComputationError(f"Inf detected in {name}")
            return self.default_value

        if _min is not None and result < _min:
            result = _min
        if _max is not None and result > _max:
            result = _max

        return result

    def guard_dict(
        self, data: Dict[str, Any], prefix: str = ""
    ) -> Dict[str, float]:
        """Guard all numeric values in a dictionary.

        Args:
            data: Dictionary potentially containing numeric values.
            prefix: Prefix for naming tracked values.

        Returns:
            Dictionary with all values guarded.
        """
        result: Dict[str, float] = {}
        for key, value in data.items():
            name = f"{prefix}.{key}" if prefix else key
            result[key] = self.guard_scalar(value, name)
        return result

    def guard_division(
        self, numerator: float, denominator: float, name: str = "division"
    ) -> float:
        """Safely divide two numbers.

        Args:
            numerator: Dividend.
            denominator: Divisor.
            name: Identifier for logging.

        Returns:
            Quotient or default_value if division is unsafe.
        """
        num = self.guard_scalar(numerator, f"{name}.numerator")
        den = self.guard_scalar(denominator, f"{name}.denominator")
        if den == 0:
            self._record_violation(name, "Division by zero")
            return self.default_value
        result = num / den
        return self.guard_scalar(result, name)

    def _record_violation(self, name: str, reason: str) -> None:
        """Record a numerical violation for diagnostics.

        Args:
            name: Identifier of the value.
            reason: Description of the issue.
        """
        if self.log_violations:
            self._violations.append({"name": name, "reason": reason})

    def get_violations(self) -> List[Dict[str, Any]]:
        """Get all recorded numerical violations.

        Returns:
            List of violation records.
        """
        return list(self._violations)

    def clear_violations(self) -> None:
        """Clear the violation log."""
        self._violations.clear()
