"""Tests for the KDM clock."""

import pytest
from src.clocks.kdm import KDMClock
from src.clocks import ClockResult
from src.core.exceptions import ComputationError


class TestKDMClock:
    @pytest.fixture
    def clock(self):
        return KDMClock()

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

    def test_predict_missing_biomarkers(self, clock):
        with pytest.raises(ComputationError):
            clock.predict({"age": 40})

    def test_metadata(self, clock):
        meta = clock.get_metadata()
        assert meta["name"] == "kdm"

    def test_healthy_middle_age(self, clock):
        result = clock.predict({
            "age": 35.0, "albumin": 45.0, "creatinine": 70.0,
            "glucose": 4.9, "lymphocyte_percent": 35.0,
            "mcv": 89.0, "rdw": 12.5, "alkaline_phosphatase": 60.0,
            "white_blood_cell_count": 6.0,
        })
        assert 18.0 <= result.predicted_age <= 120.0

    def test_biomarkers_used_tracking(self, clock, valid_biomarkers):
        result = clock.predict(valid_biomarkers)
        assert "biomarkers_used" in result.metadata
        assert result.metadata["biomarkers_used"] > 0
