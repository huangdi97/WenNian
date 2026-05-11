"""Tests for the LifeClock."""

import pytest
from src.clocks.lifeclock import LifeClock
from src.clocks import ClockResult
from src.core.exceptions import ComputationError


class TestLifeClock:
    @pytest.fixture
    def clock(self):
        return LifeClock()

    @pytest.fixture
    def valid_biomarkers(self):
        return {
            "age": 40.0,
            "albumin": 43.0,
            "creatinine": 75.0,
            "glucose": 5.1,
            "lymphocyte_percent": 33.0,
            "mcv": 90.0,
            "rdw": 13.0,
            "alkaline_phosphatase": 70.0,
            "white_blood_cell_count": 6.5,
        }

    def test_predict_valid(self, clock, valid_biomarkers):
        result = clock.predict(valid_biomarkers)
        assert isinstance(result, ClockResult)
        assert result.predicted_age > 0
        assert result.confidence > 0

    def test_predict_missing(self, clock):
        with pytest.raises(ComputationError):
            clock.predict({"age": 40})

    def test_metadata(self, clock):
        meta = clock.get_metadata()
        assert meta["name"] == "lifeclock"

    def test_healthy_equals_chron(self, clock):
        """For reference-range-perfect values, predicted should be close to chronological."""
        result = clock.predict({
            "age": 35.0, "albumin": 42.0, "creatinine": 80.0,
            "glucose": 5.0, "lymphocyte_percent": 30.0,
            "mcv": 90.0, "rdw": 13.0, "alkaline_phosphatase": 85.0,
            "white_blood_cell_count": 7.0,
        })
        assert abs(result.predicted_age - 35.0) < 30

    def test_age_acceleration_metadata(self, clock, valid_biomarkers):
        result = clock.predict(valid_biomarkers)
        assert "age_acceleration" in result.metadata
