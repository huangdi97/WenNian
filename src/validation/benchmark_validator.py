"""Benchmark validator — compares internal clocks against external benchmarks.

Supports comparison with pyaging library outputs or built-in baseline
reference values to validate clock accuracy.
"""

from typing import Any, Dict, List, Optional


# Built-in baseline reference values for benchmark comparison
BASELINE_REFERENCES: Dict[str, Dict[str, float]] = {
    "healthy_40yo": {
        "age": 40.0, "albumin": 43.0, "creatinine": 75.0, "glucose": 5.1,
        "c_reactive_protein": 1.0, "lymphocyte_percent": 33.0, "mcv": 90.0,
        "rdw": 13.0, "alkaline_phosphatase": 70.0, "white_blood_cell_count": 6.5,
        "expected_phenoage": 43.0,
    },
    "healthy_30yo": {
        "age": 30.0, "albumin": 45.0, "creatinine": 68.0, "glucose": 4.9,
        "c_reactive_protein": 0.5, "lymphocyte_percent": 36.0, "mcv": 88.0,
        "rdw": 12.5, "alkaline_phosphatase": 58.0, "white_blood_cell_count": 5.8,
        "expected_phenoage": 32.0,
    },
    "healthy_60yo": {
        "age": 60.0, "albumin": 40.0, "creatinine": 85.0, "glucose": 5.5,
        "c_reactive_protein": 2.0, "lymphocyte_percent": 28.0, "mcv": 93.0,
        "rdw": 14.0, "alkaline_phosphatase": 80.0, "white_blood_cell_count": 7.0,
        "expected_phenoage": 55.0,
    },
}


def run_benchmark(
    clocks: Optional[List[Any]] = None,
    references: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """Run benchmark validation of internal clocks against reference data.

    Args:
        clocks: List of (clock_name, clock_instance) pairs. Uses built-in if None.
        references: Reference data. Uses BASELINE_REFERENCES if None.

    Returns:
        Benchmark report dict.
    """
    refs = references or BASELINE_REFERENCES

    if clocks is None:
        from src.clocks.phenoage import PhenoAgeClock
        from src.clocks.kdm import KDMClock
        clocks = [
            ("phenoage", PhenoAgeClock()),
            ("kdm", KDMClock()),
        ]

    results = {}
    for ref_name, ref_data in refs.items():
        biomarkers = {k: v for k, v in ref_data.items()
                      if not k.startswith("expected_")}
        results[ref_name] = {"biomarkers": biomarkers, "predictions": {}}
        for clock_name, clock in clocks:
            try:
                pred = clock.predict(biomarkers)
                results[ref_name]["predictions"][clock_name] = {
                    "predicted_age": pred.predicted_age,
                    "confidence": pred.confidence,
                }
            except Exception as e:
                results[ref_name]["predictions"][clock_name] = {
                    "error": str(e),
                }

    return {
        "benchmark_type": "internal_reference",
        "reference_sets": len(refs),
        "clocks_tested": len(clocks),
        "results": results,
        "summary": _build_benchmark_summary(results, refs),
    }


def _build_benchmark_summary(
    results: Dict[str, Any],
    refs: Dict[str, Dict[str, float]],
) -> str:
    """Build a benchmark summary string."""
    lines = ["# 时钟基准测试报告", ""]
    for ref_name, ref_data in refs.items():
        chron_age = ref_data.get("age", 0)
        lines.append(f"## {ref_name} (日历年龄: {chron_age:.0f}岁)")
        predictions = results.get(ref_name, {}).get("predictions", {})
        for clock_name, pred in predictions.items():
            if "error" in pred:
                lines.append(f"- {clock_name}: ❌ {pred['error']}")
            else:
                expected_key = f"expected_{clock_name}"
                expected = ref_data.get(expected_key)
                if expected is not None:
                    diff = pred["predicted_age"] - expected
                    lines.append(
                        f"- {clock_name}: 预测{pred['predicted_age']:.1f}岁 "
                        f"(预期{expected:.1f}岁, 偏差{diff:+.1f}岁)"
                    )
                else:
                    lines.append(f"- {clock_name}: 预测{pred['predicted_age']:.1f}岁")
        lines.append("")
    return "\n".join(lines)
