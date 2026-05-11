"""Custom exception hierarchy for the WenNian system.

All exceptions inherit from WenNianError and carry a message plus
optional details dictionary for structured error propagation.
"""

from typing import Any, Dict, Optional


class WenNianError(Exception):
    """Base exception for all WenNian errors.

    Args:
        message: Human-readable error description.
        details: Optional dictionary with structured error context.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(WenNianError):
    """Raised when configuration loading or parsing fails."""


class ValidationError(WenNianError):
    """Raised when input data fails validation checks."""


class PermissionDenied(WenNianError):
    """Raised when a capability token check fails."""


class ModelNotFound(WenNianError):
    """Raised when a required model file (e.g., .pt weights) is missing."""


class ComputationError(WenNianError):
    """Raised when a computation produces NaN, Inf, or otherwise invalid results."""


class RedLineViolation(WenNianError):
    """Raised when red-line content (prohibited patterns) is detected."""
