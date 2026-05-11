"""Tests for the DNN clock."""

import pytest
from src.clocks.dnn import DNNClock
from src.clocks import ClockResult
from src.core.exceptions import ComputationError


class TestDNNClock:
    @pytest.fixture
    def clock(self):
        return DNNClock()  # No model path → uses fallback

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

    def test_predict_fallback(self, clock, valid_biomarkers):
        result = clock.predict(valid_biomarkers)
        assert isinstance(result, ClockResult)
        assert result.predicted_age > 0
        assert result.confidence > 0
        assert "fallback" in result.metadata.get("model", "").lower()

    def test_predict_missing(self, clock):
        with pytest.raises(ComputationError):
            clock.predict({"age": 40})

    def test_metadata(self, clock):
        meta = clock.get_metadata()
        assert meta["name"] == "dnn"

    def test_age_range(self, clock, valid_biomarkers):
        result = clock.predict(valid_biomarkers)
        assert 18.0 <= result.predicted_age <= 120.0

    def test_varied_inputs(self, clock):
        result = clock.predict({
            "age": 50.0, "albumin": 40.0, "creatinine": 80.0,
            "glucose": 5.5, "lymphocyte_percent": 30.0,
            "mcv": 92.0, "rdw": 13.5, "alkaline_phosphatase": 75.0,
            "white_blood_cell_count": 7.0,
        })
        assert isinstance(result, ClockResult)
