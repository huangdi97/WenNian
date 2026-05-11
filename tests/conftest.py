"""Shared pytest fixtures for the WenNian test suite."""

import os

import pytest

# Disable Gradio telemetry to avoid network I/O and log noise during tests
os.environ["GRADIO_ANALYTICS_ENABLED"] = "false"

from src.clocks import ClockRegistry
from src.clocks.phenoage import PhenoAgeClock
from src.clocks.kdm import KDMClock
from src.clocks.dnn import DNNClock
from src.clocks.lifeclock import LifeClock
from src.integrator import AgingIntegrator
from src.validation.input_validator import InputValidator
from src.core.config import AppConfig


@pytest.fixture
def sample_biomarkers() -> dict:
    """Return a set of typical biomarker values for a healthy 40-year-old."""
    return {
        "age": 40.0,
        "albumin": 43.0,
        "creatinine": 75.0,
        "glucose": 5.1,
        "c_reactive_protein": 1.0,
        "lymphocyte_percent": 33.0,
        "mcv": 90.0,
        "rdw": 13.0,
        "alkaline_phosphatase": 70.0,
        "white_blood_cell_count": 6.5,
    }


@pytest.fixture
def extreme_biomarkers() -> dict:
    """Return biologically impossible biomarker values for validation testing."""
    return {
        "age": 150.0,
        "albumin": 5.0,
        "creatinine": 0.0,
        "glucose": 100.0,
        "lymphocyte_percent": 150.0,
        "mcv": 200.0,
        "rdw": 50.0,
        "alkaline_phosphatase": 5000.0,
        "white_blood_cell_count": 200.0,
    }


@pytest.fixture
def incomplete_biomarkers() -> dict:
    """Return a partial biomarker set missing several required values."""
    return {
        "age": 40.0,
        "albumin": 43.0,
        "glucose": 5.1,
    }


@pytest.fixture
def populated_registry() -> ClockRegistry:
    """Return a ClockRegistry pre-populated with all four clock types."""
    registry = ClockRegistry()
    registry.clear()
    registry.register(phenoage=PhenoAgeClock())
    registry.register(kdm=KDMClock())
    registry.register(dnn=DNNClock())
    registry.register(lifeclock=LifeClock())
    return registry


@pytest.fixture
def integrator(populated_registry: ClockRegistry) -> AgingIntegrator:
    """Return an AgingIntegrator backed by the populated registry."""
    return AgingIntegrator(registry=populated_registry)


@pytest.fixture
def validator() -> InputValidator:
    """Return a default InputValidator."""
    return InputValidator()


@pytest.fixture
def mock_config() -> AppConfig:
    """Return the AppConfig singleton."""
    return AppConfig()
