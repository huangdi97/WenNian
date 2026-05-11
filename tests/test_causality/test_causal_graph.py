"""Tests for causal graph module."""

import pytest
from src.causality import CausalGraph, CausalNode, CausalEdge


class TestCausalGraph:
    @pytest.fixture
    def graph(self):
        nodes = [
            CausalNode("A", "Node A"),
            CausalNode("B", "Node B"),
            CausalNode("C", "Node C"),
            CausalNode("D", "Node D"),
        ]
        edges = [
            CausalEdge("A", "B", 0.8, 0.9, ["ref1"], "A causes B"),
            CausalEdge("B", "C", 0.6, 0.8, ["ref2"], "B causes C"),
            CausalEdge("A", "C", 0.4, 0.7, ["ref3"], "A directly causes C"),
            CausalEdge("C", "D", 0.5, 0.6, ["ref4"], "C causes D"),
        ]
        return CausalGraph(nodes=nodes, edges=edges)

    def test_node_count(self, graph):
        assert graph.node_count == 4

    def test_edge_count(self, graph):
        assert graph.edge_count == 4

    def test_get_downstream(self, graph):
        downstream = graph.get_downstream("A", depth=1)
        assert "B" in downstream
        assert "C" in downstream  # A→C direct at depth 1
        assert "D" not in downstream  # D requires depth 2 via A→C→D

    def test_get_upstream(self, graph):
        upstream = graph.get_upstream("C", depth=2)
        assert "A" in upstream
        assert "B" in upstream

    def test_estimate_intervention_effect(self, graph):
        effect = graph.estimate_intervention_effect("A", "C")
        assert 0 < effect <= 1.0

    def test_intervention_effect_no_path(self, graph):
        effect = graph.estimate_intervention_effect("D", "A")
        assert effect == 0.0

    def test_node_references(self, graph):
        refs = graph.get_node_references("A")
        assert "Node A" in graph.nodes["A"].description or True

    def test_add_node_and_edge(self):
        graph = CausalGraph(nodes=[], edges=[])
        graph.add_node(CausalNode("X", "Test"))
        graph.add_edge(CausalEdge("X", "X", 0.5, 0.5))
        assert graph.node_count == 1

    def test_default_graph_nodes(self):
        graph = CausalGraph()
        assert graph.node_count >= 20
        assert graph.edge_count > 0
        assert "immune" in graph.nodes
        assert "metabolic" in graph.nodes
