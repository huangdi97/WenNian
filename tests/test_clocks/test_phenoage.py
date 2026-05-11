"""Tests for the PhenoAge clock."""

import pytest
from src.clocks.phenoage import PhenoAgeClock, PHENOAGE_COEFFICIENTS
from src.clocks import ClockResult
from src.core.exceptions import ComputationError


class TestPhenoAgeClock:
    """Tests for PhenoAgeClock."""

    @pytest.fixture
    def clock(self):
        return PhenoAgeClock()

    @pytest.fixture
    def valid_biomarkers(self):
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

    def test_name_and_version(self, clock):
        assert clock.name == "phenoage"
        assert clock.version == "1.0.0"

    def test_required_biomarkers(self, clock):
        assert "albumin" in clock.required_biomarkers
        assert "age" in clock.required_biomarkers
        assert len(clock.required_biomarkers) == 10

    def test_predict_valid(self, clock, valid_biomarkers):
        result = clock.predict(valid_biomarkers)
        assert isinstance(result, ClockResult)
        assert result.predicted_age > 0
        assert result.confidence > 0
        assert result.lower_bound is not None
        assert result.upper_bound is not None
        assert result.lower_bound < result.predicted_age < result.upper_bound

    def test_predict_missing_biomarkers(self, clock):
        with pytest.raises(ComputationError):
            clock.predict({"age": 40})

    def test_predict_elderly_shows_higher_age(self, clock):
        young = clock.predict({
            "age": 25.0, "albumin": 46.0, "creatinine": 65.0,
            "glucose": 4.8, "c_reactive_protein": 0.5,
            "lymphocyte_percent": 38.0, "mcv": 88.0, "rdw": 12.0,
            "alkaline_phosphatase": 55.0, "white_blood_cell_count": 5.8,
        })
        old = clock.predict({
            "age": 65.0, "albumin": 38.0, "creatinine": 90.0,
            "glucose": 5.8, "c_reactive_protein": 3.0,
            "lymphocyte_percent": 25.0, "mcv": 94.0, "rdw": 14.5,
            "alkaline_phosphatase": 85.0, "white_blood_cell_count": 7.2,
        })
        assert old.predicted_age > young.predicted_age

    def test_get_metadata(self, clock):
        meta = clock.get_metadata()
        assert meta["name"] == "phenoage"
        assert meta["version"] == "1.0.0"
        assert "required_biomarkers" in meta
