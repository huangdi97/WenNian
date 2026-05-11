"""Tests for health interviewer, explorer, prodromal detector, symptom map."""

import pytest
from src.agents.health_interviewer import HealthInterviewer
from src.agents.explorer import Explorer
from src.engines import ProdromalDetector
from src.knowledge.symptom_map import (
    map_symptoms_to_dimensions, get_top_dimensions, get_all_symptoms,
)


class TestHealthInterviewer:
    def test_first_round(self):
        hi = HealthInterviewer(max_rounds=3)
        output = hi.execute({"initial_complaint": "最近总是疲劳，没精神"})
        assert output.success
        assert len(output.data["questions"]) > 0
        assert output.data["interview_ongoing"]

    def test_max_rounds_stops(self):
        hi = HealthInterviewer(max_rounds=3)
        output = hi.execute({
            "initial_complaint": "疲劳",
            "history": [{"q": "q1"}, {"q": "q2"}, {"q": "q3"}],
        })
        assert output.data.get("interview_complete")
        assert "structured_summary" in output.data

    def test_no_match_returns_summary(self):
        hi = HealthInterviewer(max_rounds=3)
        output = hi.execute({"initial_complaint": "xyz"})
        assert output.data.get("interview_complete")

    def test_disclaimer_present(self):
        hi = HealthInterviewer(max_rounds=3)
        output = hi.execute({
            "initial_complaint": "疲劳",
            "history": [{"q": "q1"}, {"q": "q2"}, {"q": "q3"}],
        })
        assert "诊断" in output.data.get("disclaimer", "") or "disclaimer" in output.data


class TestExplorer:
    def test_analyze_normal(self):
        exp = Explorer()
        data = [
            {"biological_age": 42, "chronological_age": 40, "albumin": 43, "glucose": 5.1},
            {"biological_age": 41, "chronological_age": 39, "albumin": 44, "glucose": 5.0},
            {"biological_age": 43, "chronological_age": 41, "albumin": 42, "glucose": 5.3},
        ]
        output = exp.execute({"data": data})
        assert output.success
        assert "records_analyzed" in output.data

    def test_empty_data(self):
        exp = Explorer()
        output = exp.execute({"data": []})
        assert not output.success

    def test_discordant_detection(self):
        exp = Explorer()
        data = [
            {"biological_age": 42, "chronological_age": 40, "albumin": 43},
            {"biological_age": 80, "chronological_age": 40, "albumin": 38},
            {"biological_age": 41, "chronological_age": 39, "albumin": 44},
            {"biological_age": 43, "chronological_age": 41, "albumin": 42},
            {"biological_age": 42, "chronological_age": 40, "albumin": 43},
            {"biological_age": 41, "chronological_age": 39, "albumin": 44},
            {"biological_age": 43, "chronological_age": 41, "albumin": 42},
            {"biological_age": 42, "chronological_age": 40, "albumin": 43},
        ]
        output = exp.execute({"data": data})
        assert any(f["type"] == "age_discordance" for f in output.data.get("findings", []))


class TestProdromalDetector:
    def test_normal_reading_no_alert(self):
        pd = ProdromalDetector()
        pd.set_baseline({"hr": (70, 5), "hrv": (50, 10), "temp": (36.5, 0.3)})
        result = pd.detect({"hr": 72, "hrv": 48, "temp": 36.6})
        assert not result["triggered"]

    def test_abnormal_reading_alerts(self):
        pd = ProdromalDetector()
        pd.set_baseline({"hr": (70, 5), "hrv": (50, 10), "temp": (36.5, 0.3)})
        result = pd.detect({"hr": 85, "hrv": 20, "temp": 37.8})
        assert result["triggered"]
        assert len(result["alerts"]) > 0

    def test_compute_baseline(self):
        pd = ProdromalDetector()
        history = [
            {"hr": 70, "hrv": 50}, {"hr": 72, "hrv": 48},
            {"hr": 68, "hrv": 52}, {"hr": 71, "hrv": 49},
        ]
        baseline = pd.compute_baseline(history)
        assert "hr" in baseline
        assert abs(baseline["hr"][0] - 70.25) < 1

    def test_disclaimer_on_alert(self):
        pd = ProdromalDetector()
        pd.set_baseline({"hr": (70, 5)})
        result = pd.detect({"hr": 90})
        assert "disclaimer" in result


class TestSymptomMap:
    def test_map_known_symptom(self):
        result = map_symptoms_to_dimensions(["疲劳"])
        assert "metabolic" in result

    def test_top_dimensions(self):
        dims = get_top_dimensions(["关节疼痛", "肌肉无力", "步速变慢"], top_k=2)
        assert len(dims) <= 2
        assert dims[0]["dimension"] == "musculoskeletal"

    def test_get_all_symptoms(self):
        symptoms = get_all_symptoms()
        assert len(symptoms) > 30

    def test_multiple_symptoms(self):
        result = map_symptoms_to_dimensions(["疲劳", "关节疼痛", "记忆力减退"])
        assert len(result) >= 2
