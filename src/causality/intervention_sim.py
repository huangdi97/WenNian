"""Intervention simulation using causal graph do-calculus."""

from typing import Any, Dict, List, Optional, Tuple

from .causal_graph import CausalGraph, CausalEdge


class InterventionSimulator:
    """Simulates interventions on the aging causal graph."""

    def __init__(self, graph: Optional[CausalGraph] = None) -> None:
        self._graph = graph or CausalGraph()

    def simulate(
        self, target_node: str, intensity: float = 0.5, max_depth: int = 3
    ) -> Dict[str, Any]:
        if target_node not in self._graph.nodes:
            return {
                "target": target_node, "intensity": intensity,
                "direct_effect": 0.0, "downstream_effects": {},
                "error": f"Unknown node: {target_node}",
            }
        direct_effect = intensity * 0.8
        downstream: Dict[str, float] = {}
        self._propagate(target_node, intensity, max_depth, downstream, visited=set())
        n_downstream = max(1, len(downstream))
        se = 0.15 * intensity / (n_downstream ** 0.5)
        ci_lower_80 = direct_effect - 1.28 * se
        ci_upper_80 = direct_effect + 1.28 * se
        ci_lower_95 = direct_effect - 1.96 * se
        ci_upper_95 = direct_effect + 1.96 * se
        return {
            "target": target_node, "intensity": intensity,
            "direct_effect": round(direct_effect, 3),
            "ci_80": [max(0, round(ci_lower_80, 3)), round(ci_upper_80, 3)],
            "ci_95": [max(0, round(ci_lower_95, 3)), round(ci_upper_95, 3)],
            "downstream_effects": {k: round(v, 3) for k, v in sorted(
                downstream.items(), key=lambda x: x[1], reverse=True
            )},
            "assumptions": [
                "基于因果图的路径乘积估计效应传播",
                "假设效应沿边线性传播，无饱和效应",
            ],
        }

    def _propagate(self, node: str, intensity: float, depth: int,
                   downstream: Dict[str, float], visited: set) -> None:
        if depth <= 0 or node in visited:
            return
        visited.add(node)
        for neighbor in self._graph.adjacency.get(node, []):
            if neighbor in visited:
                continue
            edge = self._graph._find_edge(node, neighbor)
            if edge:
                propagated = intensity * edge.effect_size * edge.confidence
                downstream[neighbor] = downstream.get(neighbor, 0.0) + propagated
                self._propagate(neighbor, propagated * 0.6, depth - 1, downstream, visited)

    def rank_targets(self, outcome_node: str,
                     candidate_nodes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if candidate_nodes is None:
            aging_dims = [
                "immune", "organ", "epigenetic", "metabolic", "senescence",
                "microbiome", "neural", "musculoskeletal", "skin",
                "sensory", "reproductive", "social",
            ]
            candidate_nodes = [n for n in aging_dims if n in self._graph.nodes]
        rankings = []
        for node in candidate_nodes:
            effect = self._graph.estimate_intervention_effect(node, outcome_node)
            rankings.append({
                "target": node,
                "total_effect": round(effect, 4),
                "target_name": self._graph.nodes[node].name if node in self._graph.nodes else node,
            })
        rankings.sort(key=lambda x: x["total_effect"], reverse=True)
        return rankings

    def simulate_combination(self, interventions: List[Tuple[str, float]]) -> Dict[str, Any]:
        all_downstream: Dict[str, float] = {}
        total_direct = 0.0
        for target, intensity in interventions:
            result = self.simulate(target, intensity)
            total_direct += result["direct_effect"]
            for k, v in result.get("downstream_effects", {}).items():
                all_downstream[k] = all_downstream.get(k, 0.0) + v
        dim_factor = 1.0 / (1.0 + 0.2 * (len(interventions) - 1))
        total_direct *= dim_factor
        return {
            "interventions": interventions,
            "combined_direct_effect": round(total_direct, 3),
            "combined_downstream": {k: round(v * dim_factor, 3) for k, v in
                                     sorted(all_downstream.items(), key=lambda x: x[1], reverse=True)},
            "diminishing_factor": round(dim_factor, 3),
        }
