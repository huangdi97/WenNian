"""Tests for UI app launch (smoke test)."""

import pytest


class TestUIApp:
    def test_interface_creation(self):
        """Verify the Gradio interface can be created without errors."""
        from src.ui.app import create_interface
        demo = create_interface()
        assert demo is not None

    def test_full_spectrum_normal(self):
        """Test the full spectrum assessment function with normal values."""
        from src.ui.app import tab_full_spectrum
        report = tab_full_spectrum(
            age=40.0, albumin=43.0, creatinine=75.0, glucose=5.1,
            lymphocyte=33.0, mcv=90.0, rdw=13.0,
            alp=70.0, wbc=6.5, crp=1.0, sbp=120.0, dbp=80.0,
        )
        assert isinstance(report, str)
        assert len(report) > 100

    def test_full_spectrum_invalid(self):
        """Test assessment with invalid inputs."""
        from src.ui.app import tab_full_spectrum
        report = tab_full_spectrum(
            age=200.0, albumin=5.0, creatinine=75.0, glucose=5.1,
            lymphocyte=33.0, mcv=90.0, rdw=13.0,
            alp=70.0, wbc=6.5, crp=None, sbp=None, dbp=None,
        )
        assert "校验失败" in report or "错误" in report

    def test_product_validation(self):
        """Test product validation tab."""
        from src.ui.app import tab_product_validation
        report = tab_product_validation("TestCorp", "TestProduct", 10)
        assert isinstance(report, str)
        assert "p值" in report or "Cohen" in report

    def test_target_prioritize(self):
        """Test target prioritization tab."""
        from src.ui.app import tab_target_prioritize
        report = tab_target_prioritize("整体")
        assert "靶点排序" in report

    def test_intervention_sim(self):
        """Test intervention simulation tab."""
        from src.ui.app import tab_intervention_sim
        report = tab_intervention_sim(["有氧运动", "NMN"], 0.5, 40, 42)
        assert "干预模拟" in report
