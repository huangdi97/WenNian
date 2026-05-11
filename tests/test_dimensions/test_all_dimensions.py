"""Tests for all dimension clock modules."""

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


class TestImmuneClock:
    def test_normal(self):
        r = assess_immune_age(33, 6.5, 1.0, 40)
        assert "immune_age" in r
        assert abs(r["immune_age"] - 40) < 20

    def test_elevated_crp(self):
        r = assess_immune_age(33, 6.5, 5.0, 40)
        assert r["immune_acceleration"] > 0


class TestEpigeneticClock:
    def test_dnam_provided(self):
        r = assess_epigenetic_age(40, dna_methylation_age=45)
        assert r["epigenetic_age"] == 45

    def test_dunedin_pace(self):
        r = assess_epigenetic_age(40, dunedin_pace=1.2)
        assert r["epigenetic_age"] > 40

    def test_smoking_effect(self):
        r = assess_epigenetic_age(40, smoking_pack_years=20)
        assert r["epigenetic_acceleration"] > 0


class TestMetabolicClock:
    def test_normal(self):
        r = assess_metabolic_age(5.1, 1.4, 1.5, chron_age=40)
        assert "metabolic_age" in r

    def test_high_glucose(self):
        r = assess_metabolic_age(7.0, chron_age=40)
        assert r["metabolic_acceleration"] > 0


class TestSenescenceBurden:
    def test_normal(self):
        r = assess_senescence_burden(40)
        assert "senescence_burden" in r
        assert 0 <= r["senescence_burden"] <= 100

    def test_high_p16(self):
        r = assess_senescence_burden(60, p16_expression=5.0)
        assert r["senescence_burden"] > 30


class TestMicrobiomeClock:
    def test_normal(self):
        r = assess_microbiome_age(40, shannon_diversity=4.0)
        assert "microbiome_age" in r

    def test_low_diversity(self):
        r = assess_microbiome_age(40, shannon_diversity=2.0)
        assert r["microbiome_acceleration"] > 0


class TestNeuralClock:
    def test_normal(self):
        r = assess_neural_age(40, nfl_pg_ml=10, gfap_pg_ml=80)
        assert "neural_age" in r

    def test_elevated_nfl(self):
        r = assess_neural_age(40, nfl_pg_ml=50)
        assert r["neural_acceleration"] > 0


class TestMusculoskeletalClock:
    def test_normal(self):
        r = assess_musculoskeletal_age(40, grip_strength_kg=35, gait_speed_ms=1.1)
        assert "musculoskeletal_age" in r

    def test_weak_grip(self):
        r = assess_musculoskeletal_age(40, grip_strength_kg=20)
        assert r["musculoskeletal_acceleration"] > 0


class TestSkinClock:
    def test_normal(self):
        r = assess_skin_age(40, wrinkle_score=2, elasticity_score=8)
        assert "skin_age" in r

    def test_wrinkled(self):
        r = assess_skin_age(40, wrinkle_score=7, elasticity_score=4)
        assert r["skin_acceleration"] > 0


class TestReproductiveAging:
    def test_female_normal(self):
        r = assess_reproductive_age(35, amh_ng_ml=2.5, sex="female")
        assert "reproductive_age" in r

    def test_male_skips(self):
        r = assess_reproductive_age(40, sex="male")
        assert r["reproductive_age"] == 40


class TestSensoryClock:
    def test_normal(self):
        r = assess_sensory_age(40, hearing_threshold_db=15, olfactory_score=10)
        assert "sensory_age" in r

    def test_hearing_loss(self):
        r = assess_sensory_age(40, hearing_threshold_db=40)
        assert r["sensory_acceleration"] > 0


class TestSocietalClock:
    def test_normal(self):
        r = assess_societal_age(40, loneliness_score=35, perceived_stress=10)
        assert "social_age" in r

    def test_lonely(self):
        r = assess_societal_age(40, loneliness_score=65)
        assert r["social_acceleration"] > 0
