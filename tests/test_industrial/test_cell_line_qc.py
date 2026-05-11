"""Tests for cell line QC module."""

import pytest
from src.industrial.cell_line_qc import compute_csi, monitor_csi_trend


class TestCellLineQC:
    def test_compute_csi_young(self):
        result = compute_csi(passage_number=5, doubling_time_hours=22, viability_pct=95,
                             sa_beta_gal_pct=5, population_doublings=10, morphology_score=0.95)
        assert result["csi"] < 30
        assert "年轻" in result["status"]

    def test_compute_csi_old(self):
        result = compute_csi(passage_number=35, doubling_time_hours=48, viability_pct=75,
                             sa_beta_gal_pct=45, population_doublings=60, morphology_score=0.5)
        assert result["csi"] > 50

    def test_compute_csi_contamination(self):
        result = compute_csi(passage_number=10, doubling_time_hours=25, viability_pct=90,
                             sa_beta_gal_pct=10, population_doublings=20,
                             morphology_score=0.8, contamination_flag=True)
        assert result["csi"] > 25  # Penalty added

    def test_monitor_trend(self):
        history = [
            {"passage_number": 5, "csi": 10.0},
            {"passage_number": 10, "csi": 20.0},
            {"passage_number": 15, "csi": 30.0},
        ]
        result = monitor_csi_trend(history)
        assert result["current_csi"] == 30.0
        assert result["csi_slope_per_passage"] == 2.0
        assert result["trend"] == "加速衰老"

    def test_monitor_trend_insufficient(self):
        result = monitor_csi_trend([{"passage_number": 5, "csi": 10.0}])
        assert "error" in result

    def test_recommendation_severe(self):
        result = compute_csi(passage_number=40, doubling_time_hours=72, viability_pct=50,
                             sa_beta_gal_pct=80, population_doublings=80)
        assert "严重" in result["status"] or "停用" in result["recommendation"]
