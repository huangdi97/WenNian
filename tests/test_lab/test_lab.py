"""Tests for lab modules."""

import pytest
from src.lab.experiment_designer import design_intervention_study, design_dose_response
from src.lab.opentrons_driver import OT2Simulator, run_senescence_assay_simulation
from src.lab.lims import LIMS
from src.lab.drywet_loop import DryWetLoop


class TestExperimentDesigner:
    def test_design_intervention(self):
        design = design_intervention_study("Test Study", n_subjects_per_group=10, n_groups=2)
        assert design["total_subjects"] == 20
        assert len(design["groups"]) == 2
        assert design["duration_weeks"] == 12

    def test_design_dose_response(self):
        design = design_dose_response("Rapamycin", [0.01, 0.1, 1.0, 10.0], n_per_dose=6)
        assert design["total_wells"] == 30  # 4 doses + 1 vehicle, 6 each
        assert len(design["conditions"]) == 5

    def test_design_custom_groups(self):
        design = design_intervention_study(
            "Test", n_subjects_per_group=5, n_groups=3,
            group_names=["Ctrl", "Low", "High"]
        )
        assert design["groups"][2]["name"] == "High"


class TestOT2Simulator:
    def test_simulation_valid(self):
        result = run_senescence_assay_simulation()
        assert result["simulation_valid"]
        assert result["operations_count"] > 0

    def test_protocol_script_generated(self):
        result = run_senescence_assay_simulation()
        script = result["protocol_script"]
        assert "from opentrons import protocol_api" in script
        assert "def run" in script

    def test_load_labware(self):
        sim = OT2Simulator()
        sim.load_labware("test_plate", "1")
        assert "1" in sim._deck

    def test_volume_validation(self):
        sim = OT2Simulator()
        sim.load_labware("plate", "1")
        sim.load_pipette("p20_single", "right")
        result = sim.transfer(100, "A1", "B1")  # 100 > 20
        assert "error" in result


class TestLIMS:
    def test_create_sample(self):
        lims = LIMS()
        sample = lims.create_sample("blood", source="patient_01")
        assert "sample_id" in sample
        assert sample["status"] == "received"

    def test_create_assay_and_submit_results(self):
        lims = LIMS()
        sample = lims.create_sample("blood")
        assay = lims.create_assay("sa_beta_gal", [sample["sample_id"]])
        result = lims.submit_results(assay["assay_id"], {"pct_positive": 15.0})
        assert result["status"] == "completed"

    def test_get_sample_results(self):
        lims = LIMS()
        s = lims.create_sample("blood")
        a = lims.create_assay("elisa", [s["sample_id"]])
        lims.submit_results(a["assay_id"], {"il6": 2.5})
        results = lims.get_sample_results(s["sample_id"])
        assert len(results) == 1

    def test_get_all(self):
        lims = LIMS()
        lims.create_sample("blood")
        lims.create_assay("test", ["x"])
        assert len(lims.get_all_samples()) == 1
        assert len(lims.get_all_assays()) == 1


class TestDryWetLoop:
    def test_full_cycle(self):
        loop = DryWetLoop()
        pred_id = loop.record_prediction("phenoage", 43.0, "biological_age")
        val = loop.record_validation(pred_id, 44.0, "EXP-001")
        assert val["absolute_error"] == 1.0

    def test_calibration(self):
        loop = DryWetLoop()
        p1 = loop.record_prediction("m1", 40.0, "age")
        p2 = loop.record_prediction("m1", 42.0, "age")
        loop.record_validation(p1, 41.0)
        loop.record_validation(p2, 43.0)
        cal = loop.compute_calibration()
        assert cal["mae"] >= 0

    def test_closing_gap(self):
        loop = DryWetLoop()
        p1 = loop.record_prediction("m1", 40.0, "age")
        p2 = loop.record_prediction("m1", 42.0, "age")
        loop.record_validation(p1, 45.0)  # Error 5
        loop.record_validation(p2, 42.5)  # Error 0.5
        gap = loop.get_closing_gap()
        assert gap["trend"] == "improving"
