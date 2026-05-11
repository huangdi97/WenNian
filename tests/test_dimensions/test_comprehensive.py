"""Additional dimension-specific edge case tests."""

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


def _make_tests(cls, fn, normal_args, high_args):
    """Batch generate test methods."""
    def test_normal(self):
        r = fn(**normal_args)
        assert any("age" in k.lower() for k in r)
    def test_degraded(self):
        r = fn()
        assert any("age" in k.lower() for k in r)
    def test_high(self):
        r = fn(**high_args)
        if "senescence" in fn.__name__:
            assert r.get("senescence_burden", 0) >= 0
        else:
            acc_key = None
            for k in r:
                if "acceleration" in k:
                    acc_key = k
                    break
            if acc_key:
                assert r[acc_key] >= 0
    return test_normal, test_degraded, test_high


class TestDimensionComprehensive:
    def test_immune_young(self): r = assess_immune_age(33, 6.5, 1.0, 25); assert "immune_age" in r
    def test_immune_old(self): r = assess_immune_age(25, 8.0, 3.0, 65); assert "immune_age" in r
    def test_immune_cd4(self): r = assess_immune_age(33, 6.5, 1.0, 40, cd4_cd8_ratio=1.5); assert r["missing_markers"] == []
    def test_immune_no_cd4(self): r = assess_immune_age(33, 6.5, 1.0, 40); assert "cd4_cd8_ratio" in r["missing_markers"]

    def test_epi_dnam_young(self): r = assess_epigenetic_age(25, dna_methylation_age=24); assert r["epigenetic_age"] == 24
    def test_epi_pace_slow(self): r = assess_epigenetic_age(40, dunedin_pace=0.8); assert r["epigenetic_age"] < 40
    def test_epi_bmi_low(self): r = assess_epigenetic_age(40, bmi=17); assert r["epigenetic_acceleration"] >= 0

    def test_meta_hdl_low(self): r = assess_metabolic_age(5.1, hdl=0.8, chron_age=40); assert r["metabolic_acceleration"] > 0
    def test_meta_ir_high(self): r = assess_metabolic_age(5.1, homa_ir=4.0, chron_age=40); assert r["metabolic_acceleration"] > 0
    def test_meta_missing(self): r = assess_metabolic_age(chron_age=40); assert len(r["missing_markers"]) > 0

    def test_sen_telomere_short(self): r = assess_senescence_burden(40, telomere_length_kb=5); assert r["senescence_burden"] > 0
    def test_sen_high_il6(self): r = assess_senescence_burden(40, sasp_il6=10); assert r["senescence_burden"] > 10
    def test_sen_very_young(self): r = assess_senescence_burden(20); assert r["senescence_burden"] < 30

    def test_micro_akkermansia_low(self): r = assess_microbiome_age(40, akkermansia_abundance=0.001); assert "microbiome_age" in r
    def test_micro_fb_high(self): r = assess_microbiome_age(40, firmicutes_bacteroidetes_ratio=2.5); assert r["microbiome_acceleration"] > 0
    def test_micro_all_present(self): r = assess_microbiome_age(40, shannon_diversity=3.5, firmicutes_bacteroidetes_ratio=1.2, akkermansia_abundance=0.02); assert len(r["missing_markers"]) <= 1

    def test_neural_gfap_high(self): r = assess_neural_age(40, gfap_pg_ml=200); assert r["neural_acceleration"] > 0
    def test_neural_tau_high(self): r = assess_neural_age(40, p_tau181=50); assert r["neural_acceleration"] > 0
    def test_neural_cognitive_low(self): r = assess_neural_age(40, cognitive_score=18); assert r["neural_acceleration"] > 0

    def test_msk_gait_slow(self): r = assess_musculoskeletal_age(40, gait_speed_ms=0.5); assert r["musculoskeletal_acceleration"] > 0
    def test_msk_bone_low(self): r = assess_musculoskeletal_age(40, bone_density_t=-2.5); assert r["musculoskeletal_acceleration"] > 0
    def test_msk_young(self): r = assess_musculoskeletal_age(25, grip_strength_kg=45, gait_speed_ms=1.4); assert abs(r["musculoskeletal_acceleration"]) < 10

    def test_skin_pigment(self): r = assess_skin_age(40, pigmentation_score=8); assert r["skin_acceleration"] > 0
    def test_skin_elast_low(self): r = assess_skin_age(40, elasticity_score=2); assert r["skin_acceleration"] > 0
    def test_skin_hydration(self): r = assess_skin_age(40, hydration_transepidermal=20); assert r["skin_acceleration"] > 0

    def test_repro_amh_high(self): r = assess_reproductive_age(30, amh_ng_ml=4.0, sex="female"); assert r["reproductive_age"] < 40
    def test_repro_amh_low(self): r = assess_reproductive_age(40, amh_ng_ml=0.3, sex="female"); assert r["reproductive_acceleration"] > 0
    def test_repro_fsh_high(self): r = assess_reproductive_age(40, fsh_iu_l=20, sex="female"); assert r["reproductive_acceleration"] > 0

    def test_sensory_hearing_loss(self): r = assess_sensory_age(40, hearing_threshold_db=50); assert r["sensory_acceleration"] > 0
    def test_sensory_olfactory_loss(self): r = assess_sensory_age(40, olfactory_score=3); assert r["sensory_acceleration"] > 0
    def test_sensory_vision_loss(self): r = assess_sensory_age(40, visual_acuity_logmar=0.8); assert r["sensory_acceleration"] > 0

    def test_social_pm25(self): r = assess_societal_age(40, pm25_exposure=50); assert r["social_acceleration"] > 0
    def test_social_no_sleep(self): r = assess_societal_age(40, sleep_hours=4); assert r["social_acceleration"] > 0
    def test_social_few_connections(self): r = assess_societal_age(40, social_connections=1); assert r["social_acceleration"] > 0
    def test_social_many_connections(self): r = assess_societal_age(40, social_connections=10, loneliness_score=25, perceived_stress=5); assert abs(r["social_acceleration"]) < 10
    def test_social_factors_provided(self): r = assess_societal_age(40, loneliness_score=65, pm25_exposure=35); assert len(r["factors"]) >= 1
