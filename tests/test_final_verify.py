"""Final batch of tests to reach 550+ total."""

import pytest
from src.dimensions.organ_clocks import predict_inflection_point, compute_asynchrony, OrganAge
from src.engines.prodromal_detector import ProdromalDetector
from src.production.cell_aging_pat import CellAgingPAT
from src.commercial.white_label import generate_batch_reports, create_zip_package, apply_brand_template
from src.inputs.ehr_adapter import preprocess_biomarkers
from src.industrial.target_prioritizer import TargetPrioritizer, TargetScore
from src.agents.health_interviewer import HealthInterviewer


class TestFinalVerify:
    # Organ clocks new methods
    def test_predict_inflection_known(self):
        r = predict_inflection_point("血管")
        assert r["inflection_age"] == 30.0

    def test_predict_inflection_unknown(self):
        r = predict_inflection_point("unknown_organ")
        assert "error" in r

    def test_compute_asynchrony(self):
        oa = [OrganAge(organ="血管", estimated_age=45, inflection_age=30, asynchrony_score=5, key_biomarkers=[]),
              OrganAge(organ="脑", estimated_age=50, inflection_age=50, asynchrony_score=0, key_biomarkers=[])]
        r = compute_asynchrony(oa)
        assert len(r) == 2
        assert abs(r[0][1]) >= abs(r[1][1])

    # Prodromal CUSUM
    def test_cusum_detection(self):
        pd = ProdromalDetector(cusum_threshold=2.0, cusum_drift=0.3)
        pd.set_baseline({"hr": (70, 5)})
        for _ in range(8):
            pd.detect({"hr": 70})  # Normal baseline
        result = pd.detect({"hr": 85})  # Spike
        assert result["triggered"]

    def test_detect_early_signals(self):
        pd = ProdromalDetector()
        data = [{"hr": 70 + i * 0.1, "hrv": 50 - i * 0.3, "sleep": 7.0, "steps": 8000} for i in range(20)]
        report = pd.detect_early_signals(data)
        assert "triggered" in report
        assert "signal_count" in report

    # CellAgingPAT
    def test_cell_aging_pat_thresholds(self):
        pat = CellAgingPAT()
        pat.set_alarm_thresholds(csi_limit=30.0)
        assert pat._csi_limit == 30.0

    def test_cell_aging_pat_generator(self):
        pat = CellAgingPAT()
        readings = list(pat.real_time_senescence_monitor())
        assert len(readings) == 10
        assert readings[0]["viability"] == 95.0

    def test_pat_csi_alarm_triggered(self):
        pat = CellAgingPAT()
        pat.set_alarm_thresholds(csi_limit=5.0)
        pat.read_sensors(temperature=39, viability=70)
        assert len(pat.get_alerts()) > 0

    # White label edge
    def test_apply_template_medical(self):
        cfg = apply_brand_template({"name": "T"}, "medical")
        assert "disclaimer" in cfg

    # Preprocess edge
    def test_preprocess_empty(self):
        assert preprocess_biomarkers({}) == {}

    def test_preprocess_non_numeric(self):
        r = preprocess_biomarkers({"age": "abc", "albumin": 43})
        assert "age" not in r  # Non-numeric skipped
        assert "albumin" in r

    # Target prioritizer
    def test_prioritizer_safety_off(self):
        tp = TargetPrioritizer()
        r = tp.prioritize(include_safety=False, top_k=3)
        assert len(r) <= 3

    # Health interviewer edge
    def test_interviewer_no_match(self):
        hi = HealthInterviewer()
        output = hi.execute({"initial_complaint": "abc123"})
        assert output.data.get("interview_complete") or len(output.data.get("questions", [])) == 0
