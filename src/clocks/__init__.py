"""Base clock abstraction and registry for the aging clock system.

All aging clocks inherit from BaseClock and are registered in the
singleton ClockRegistry for auto-discovery and unified invocation.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, Field


class ClockResult(BaseModel):
    """Standardized output for any aging clock prediction.

    Attributes:
        predicted_age: The predicted biological age in years.
        lower_bound: Lower bound of the confidence interval.
        upper_bound: Upper bound of the confidence interval.
        confidence: Confidence score between 0.0 and 1.0.
        metadata: Arbitrary additional information from the clock.
    """

    predicted_age: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseClock(ABC):
    """Abstract base class for all aging clocks.

    Subclasses must define name, version, required_biomarkers (class vars)
    and implement predict().

    Attributes:
        name: Unique human-readable clock identifier.
        version: Semantic version string.
        required_biomarkers: Biomarker keys this clock needs.
    """

    name: ClassVar[str]
    version: ClassVar[str]
    required_biomarkers: ClassVar[List[str]]

    @abstractmethod
    def predict(self, biomarkers: Dict[str, Any]) -> ClockResult:
        """Compute biological age from biomarker values.

        Args:
            biomarkers: Dictionary mapping biomarker names to numeric values.

        Returns:
            A ClockResult with predicted age and metadata.

        Raises:
            ComputationError: If prediction fails due to invalid data.
        """

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about this clock.

        Returns:
            Dictionary with name, version, and required biomarkers.
        """
        return {
            "name": self.name,
            "version": self.version,
            "required_biomarkers": self.required_biomarkers,
        }

    def _check_required(self, biomarkers: Dict[str, Any]) -> List[str]:
        """Return list of missing required biomarkers.

        Args:
            biomarkers: Available biomarker dictionary.

        Returns:
            List of biomarker keys that are missing.
        """
        return [k for k in self.required_biomarkers if k not in biomarkers]


class ClockRegistry:
    """Singleton registry for all aging clocks.

    Clocks are registered by their name attribute and can be
    retrieved individually or listed.
    """

    _instance: Optional["ClockRegistry"] = None
    _clocks: Dict[str, BaseClock]

    def __new__(cls) -> "ClockRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._clocks = {}
        return cls._instance

    def register(self, clock_id: Optional[str] = None, clock: Optional["BaseClock"] = None, **kwargs: Any) -> None:
        """Register a clock instance.

        Supports both positional and keyword-style registration:
        - registry.register("myclock", MyClock())
        - registry.register(myclock=MyClock())

        Args:
            clock_id: Unique identifier for the clock (defaults to clock.name).
            clock: The clock instance to register.
            **kwargs: Keyword-style clock_id=clock_instance pairs.
        """
        if clock is not None:
            cid = clock_id or clock.name
            self._clocks[cid] = clock
        for key, value in kwargs.items():
            if isinstance(value, BaseClock):
                self._clocks[key] = value

    def get(self, clock_id: str) -> Optional[BaseClock]:
        """Retrieve a clock by its identifier.

        Args:
            clock_id: The clock's registered identifier.

        Returns:
            The clock instance or None if not found.
        """
        return self._clocks.get(clock_id)

    def list_all(self) -> List[str]:
        """List all registered clock identifiers.

        Returns:
            Sorted list of clock IDs.
        """
        return sorted(self._clocks.keys())

    def unregister(self, clock_id: str) -> None:
        """Remove a clock from the registry.

        Args:
            clock_id: Identifier of the clock to remove.
        """
        self._clocks.pop(clock_id, None)

    def clear(self) -> None:
        """Remove all registered clocks."""
        self._clocks.clear()
