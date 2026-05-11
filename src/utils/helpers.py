"""General-purpose utility functions for safe computation and formatting."""

import hashlib
import json
from typing import Any, Dict, Optional


def safe_float(
    value: Any,
    default: float = 0.0,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> float:
    """Safely convert a value to float with bounds clamping.

    Args:
        value: Input value to convert.
        default: Fallback value if conversion fails or yields NaN/Inf.
        min_val: Optional lower bound; values below are clamped.
        max_val: Optional upper bound; values above are clamped.

    Returns:
        A valid finite float within the specified bounds.
    """
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    import math
    if math.isnan(result) or math.isinf(result):
        return default
    if min_val is not None and result < min_val:
        return min_val
    if max_val is not None and result > max_val:
        return max_val
    return result


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default on division-by-zero or invalid operands.

    Args:
        a: Numerator.
        b: Denominator.
        default: Value returned when division is unsafe.

    Returns:
        a / b if safe, otherwise default.
    """
    try:
        if b == 0:
            return default
        result = a / b
        import math
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def truncate_string(s: str, max_len: int = 100) -> str:
    """Truncate a string to max_len characters, appending '...' if shortened.

    Args:
        s: Input string.
        max_len: Maximum allowed length.

    Returns:
        Truncated string with ellipsis if needed.
    """
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def hash_dict(d: Dict[str, Any]) -> str:
    """Create a deterministic SHA-256 hash for a dictionary.

    Useful for cache keys. Keys are sorted before serialization
    to ensure deterministic output.

    Args:
        d: Dictionary to hash.

    Returns:
        Hexadecimal SHA-256 digest string.
    """
    canonical = json.dumps(d, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
