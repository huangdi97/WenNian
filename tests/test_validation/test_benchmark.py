"""Tests for benchmark validator and deployment checks."""

import pytest
from src.validation.benchmark_validator import run_benchmark, BASELINE_REFERENCES


class TestBenchmarkValidator:
    def test_run_benchmark(self):
        result = run_benchmark()
        assert "benchmark_type" in result
        assert result["reference_sets"] >= 2
        assert result["clocks_tested"] >= 1
        assert "results" in result

    def test_summary_generated(self):
        result = run_benchmark()
        assert "summary" in result
        assert "基准测试报告" in result["summary"]

    def test_baseline_references_loaded(self):
        assert "healthy_40yo" in BASELINE_REFERENCES
        assert "expected_phenoage" in BASELINE_REFERENCES["healthy_40yo"]

    def test_benchmark_handles_missing_clock(self):
        from src.clocks.phenoage import PhenoAgeClock
        clocks = [("phenoage", PhenoAgeClock())]
        result = run_benchmark(clocks=clocks)
        assert result["clocks_tested"] == 1
