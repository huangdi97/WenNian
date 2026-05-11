"""Additional comprehensive tests for commercial, inputs, and knowledge modules."""

import pytest
from src.commercial import generate_batch_reports, create_zip_package, apply_brand_template
from src.commercial.product_validator import run_product_validation, POCResult
from src.commercial.actuarial_pricing import batch_risk_portfolio
from src.commercial.cro_terminal import export_sdtm_dm, export_adam_adsl, monitor_data_quality
from src.commercial.enterprise_wellness import build_enterprise_dashboard, aggregate_employee_aging
from src.inputs import parse_csv_report, generate_parsing_summary
from src.outputs.instant_feedback import generate_daily_card, generate_trend_card, generate_intervention_reminder
from src.outputs.report_builder import build_debate_section
from src.knowledge.symptom_map import map_symptoms_to_dimensions, get_top_dimensions
from src.validation.benchmark_validator import run_benchmark, BASELINE_REFERENCES
from src.agents.health_interviewer import HealthInterviewer
from src.agents.explorer import Explorer
from src.engines import ProdromalDetector
from src.lab.opentrons_driver import OT2Simulator, run_senescence_assay_simulation
from src.lab.lims import LIMS
from src.lab.drywet_loop import DryWetLoop


class TestBatchAdditional:
    def test_white_label_medical_template(self):
        config = apply_brand_template({"name": "Test"}, "medical")
        assert "disclaimer" in config

    def test_white_label_corporate(self):
        config = apply_brand_template({"name": "Test"}, "corporate")
        assert config["theme_color"] == "#003366"

    def test_product_validator_effect_size(self):
        import random
        random.seed(1)
        before = [42 + random.gauss(0, 1) for _ in range(15)]
        after = [b - 2 + random.gauss(0, 1) for b in before]
        result = run_product_validation("Test", before, after)
        assert result.cohens_d > 0.5

    def test_actuarial_batch_single(self):
        result = batch_risk_portfolio([{"chronological_age": 40, "biological_age": 42}])
        assert result["count"] == 1

    def test_cro_export_empty(self):
        csv = export_sdtm_dm([])
        assert "STUDYID" in csv

    def test_cro_quality_all_missing(self):
        subjects = [{"biomarkers": {}} for _ in range(3)]
        result = monitor_data_quality(subjects)
        assert result["overall_quality_score"] < 0.2

    def test_enterprise_mixed_departments(self):
        emps = [{"biological_age": 40 + i*0.1, "chronological_age": 38 + i*0.1, "department": "D1" if i < 25 else "D2"} for i in range(50)]
        result = aggregate_employee_aging(emps)
        depts = result.get("departments", {})
        assert not depts.get("D1", {}).get("suppressed", True)

    def test_ehr_long_format_aliases(self):
        import tempfile, os
        content = "biomarker,value\nALB,43\nGLU,5.1\n"
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        tmp.write(content); tmp.close()
        result = parse_csv_report(tmp.name)
        assert result["biomarkers"].get("albumin") == 43 or result["biomarkers"].get("glucose") == 5.1
        os.unlink(tmp.name)

    def test_feedback_reminder_high_adherence(self):
        card = generate_intervention_reminder("Program", 3.0, adherence_pct=95)
        assert "优秀" in card

    def test_debate_section_builder(self):
        debate = {
            "proposition": "Test",
            "rounds": [{
                "round_number": 1, "judge_score": 7.0,
                "judge_rationale": "Good",
                "pro_arguments": [{"claim": "C1", "references": ["R1"]}],
                "con_arguments": [{"claim": "C2", "references": []}],
            }],
            "winner": "pro", "final_score": 7.5,
            "consensus_notes": "Consensus text",
        }
        section = build_debate_section(debate)
        assert "辩论日志" in section
        assert "C1" in section

    def test_benchmark_all_references(self):
        result = run_benchmark()
        for ref_name in BASELINE_REFERENCES:
            assert ref_name in result["results"]

    def test_health_interviewer_dimensions(self):
        hi = HealthInterviewer(max_rounds=3)
        output = hi.execute({"initial_complaint": "失眠焦虑压力大"})
        dims = output.data.get("identified_dimensions", [])
        assert len(dims) >= 1

    def test_explorer_velocity(self):
        exp = Explorer()
        data = [
            {"biological_age": 40, "chronological_age": 40, "albumin": 43, "glucose": 5.1},
            {"biological_age": 42, "chronological_age": 41, "albumin": 43, "glucose": 5.1},
        ]
        output = exp.execute({"data": data})
        assert "records_analyzed" in output.data

    def test_prodromal_trend(self):
        pd = ProdromalDetector()
        pd.set_baseline({"hr": (70, 5)})
        for _ in range(5):
            pd.detect({"hr": 72})
        trend = pd.get_recent_trend("hr", days=3)
        assert len(trend) >= 1

    def test_ot2_pipette_validation(self):
        sim = OT2Simulator()
        sim.load_labware("plate", "1")
        sim.load_pipette("p300_single", "right")
        result = sim.transfer(400, "A1", "B1")
        assert "error" in result

    def test_lims_invalid_assay(self):
        lims = LIMS()
        result = lims.submit_results("nonexistent", {})
        assert "error" in result

    def test_drywet_unknown_prediction(self):
        loop = DryWetLoop()
        result = loop.record_validation("nonexistent", 1.0)
        assert "error" in result

    def test_symptom_map_empty(self):
        result = map_symptoms_to_dimensions([])
        assert result == {}

    def test_symptom_top_dimensions_empty(self):
        result = get_top_dimensions([])
        assert result == []
