"""Additional dimension tests covering edge cases and graceful degradation."""

import pytest
from src.dimensions.immune_clock import assess_immune_age
from src.dimensions.epigenetic_clock import assess_epigenetic_age
from src.dimensions.metabolic_clock import assess_metabolic_age
from src.dimensions.senescence_burden import assess_senescence_burden
from src.dimensions.microbiome_clock import assess_microbiome_age
from src.dimensions.neural_clock import assess_neural_age
from src.dimensions.musculoskeletal_clock import assess_musculoskeletal_age
from src.dimensions.face_age import assess_skin_age
from src.dimensions.reproductive_aging import assess_reproductive_age
from src.dimensions.sensory_clock import assess_sensory_age
from src.dimensions.societal_clock import assess_societal_age
from src.dimensions import assess_organ_ages


class TestDimensionGracefulDegradation:
    """Verify all dimensions handle missing data gracefully."""

    def test_immune_all_missing(self):
        r = assess_immune_age(chron_age=40)
        assert "immune_age" in r

    def test_epigenetic_no_data(self):
        r = assess_epigenetic_age(40)
        assert r["epigenetic_age"] == 40
        assert r["confidence"] < 0.5

    def test_metabolic_all_missing(self):
        r = assess_metabolic_age(chron_age=40)
        assert "metabolic_age" in r

    def test_senescence_all_missing(self):
        r = assess_senescence_burden(40)
        assert 0 <= r["senescence_burden"] <= 100

    def test_microbiome_all_missing(self):
        r = assess_microbiome_age(40)
        assert "microbiome_age" in r

    def test_neural_all_missing(self):
        r = assess_neural_age(40)
        assert "neural_age" in r

    def test_musculoskeletal_all_missing(self):
        r = assess_musculoskeletal_age(40)
        assert "musculoskeletal_age" in r

    def test_skin_all_missing(self):
        r = assess_skin_age(40)
        assert "skin_age" in r

    def test_reproductive_male(self):
        r = assess_reproductive_age(40, sex="male")
        assert r["reproductive_age"] == 40

    def test_sensory_all_missing(self):
        r = assess_sensory_age(40)
        assert "sensory_age" in r

    def test_societal_all_missing(self):
        r = assess_societal_age(40)
        assert "social_age" in r

    def test_organ_empty(self):
        r = assess_organ_ages({})
        assert r == []


class TestDimensionRanges:
    def test_all_dimensions_within_range(self):
        """All dimension ages should be within 18-120."""
        dims = [
            ("immune_age", assess_immune_age(40)),
            ("epigenetic_age", assess_epigenetic_age(40)),
            ("metabolic_age", assess_metabolic_age(chron_age=40)),
            ("microbiome_age", assess_microbiome_age(40)),
            ("neural_age", assess_neural_age(40)),
            ("musculoskeletal_age", assess_musculoskeletal_age(40)),
            ("skin_age", assess_skin_age(40)),
            ("sensory_age", assess_sensory_age(40)),
            ("social_age", assess_societal_age(40)),
        ]
        for key, d in dims:
            assert 18 <= d[key] <= 120, f"{key} out of range: {d[key]}"

    def test_senescence_burden_in_range(self):
        r = assess_senescence_burden(40)
        assert 0 <= r["senescence_burden"] <= 100
