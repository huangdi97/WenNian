"""Additional integration and cross-module tests."""

import pytest
from src.agents.director import run_debate_pipeline
from src.agents.executor import Executor
from src.agents.protocols import InterventionScenario
from src.causality import CausalGraph, InterventionSimulator
from src.knowledge import LiteratureRetriever
from src.knowledge.coagulation_pathway import get_coagulation_pathway, estimate_coagulation_burden
from src.validation.stability_guard import StabilityGuard
from src.validation.output_consistency import OutputConsistency
from src.validation.benchmark_validator import run_benchmark


class TestIntegration:
    def test_debate_with_interpreter(self, sample_biomarkers):
        from src.agents.interpreter import Interpreter
        debate = run_debate_pipeline(
            biomarkers=sample_biomarkers,
            assessment={"biological_age": 42.0, "chronological_age": 40.0},
            max_rounds=2,
        )
        interpreter = Interpreter()
        output = interpreter.execute({
            "biomarkers": sample_biomarkers,
            "assessment": {"biological_age": 42.0},
        })
        assert debate["winner"] in ("pro", "con", "tie", None)
        assert output.success

    def test_executor_with_causal_graph(self):
        graph = CausalGraph()
        sim = InterventionSimulator(graph)
        result = sim.simulate("immune", intensity=0.5)
        assert result["direct_effect"] > 0

        executor = Executor()
        scenario = InterventionScenario(
            target_dimension="immune", intervention_type="test", intensity=0.5
        )
        pred = executor.simulate(scenario)
        assert pred.predicted_age_reduction > 0

    def test_rag_with_coagulation(self):
        retriever = LiteratureRetriever()
        results = retriever.retrieve("凝血因子 GAS6", top_k=3)
        assert len(results) > 0

        pathway = get_coagulation_pathway()
        assert len(pathway["factors"]) >= 3

    def test_stability_guard_integration(self):
        guard = StabilityGuard()
        data = {"x": float("nan"), "y": 1.0, "z": float("inf")}
        cleaned = guard.guard_dict(data)
        assert cleaned["x"] == 0.0
        assert cleaned["y"] == 1.0
        assert cleaned["z"] == 0.0

    def test_output_consistency_sequence(self):
        oc = OutputConsistency()
        for age in range(38, 45):
            oc.add_record({"biological_age": float(age) + 1.0, "chronological_age": float(age)})
        result = oc.check({"biological_age": 46.0, "chronological_age": 45.0})
        assert result["is_consistent"]

    def test_benchmark_with_custom_clocks(self):
        from src.clocks.phenoage import PhenoAgeClock
        from src.clocks.kdm import KDMClock
        clocks = [("phenoage", PhenoAgeClock()), ("kdm", KDMClock())]
        result = run_benchmark(clocks=clocks)
        assert result["clocks_tested"] == 2
        assert "results" in result
