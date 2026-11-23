import numpy as np
import pytest

from skeletonpaths import (
    JunctionPairingLimitError,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
    StrokeSearchLimitError,
    StrokeSearchLimits,
    rank_covering_walks,
)


def _star_graph():
    points = {0: (0.0, 0.0), 1: (-1.0, 0.0), 2: (1.0, 0.0), 3: (0.0, 1.0)}
    pairs = ((0, 1), (0, 2), (0, 3))
    degrees = {node_id: 0 for node_id in points}
    for first, second in pairs:
        degrees[first] += 1
        degrees[second] += 1
    nodes = tuple(
        SkeletonNode(node_id, point, degrees[node_id], 1.0, 1.0)
        for node_id, point in points.items()
    )
    edges = []
    for first, second in pairs:
        xy = np.asarray((points[first], points[second]), dtype=float)
        length = float(np.linalg.norm(xy[1] - xy[0]))
        edges.append(SkeletonEdge(first, second, xy, length, 1.0, 1.0))
    return SkeletonGraph(nodes, tuple(edges))


def _degree_nine_star():
    points = {0: (0.0, 0.0)}
    points.update({index: (float(index), float(index % 3)) for index in range(1, 10)})
    edges = []
    degrees = {node_id: 0 for node_id in points}
    for node_id in range(1, 10):
        degrees[0] += 1
        degrees[node_id] += 1
        xy = np.asarray((points[0], points[node_id]), dtype=float)
        length = float(np.linalg.norm(xy[1] - xy[0]))
        edges.append(SkeletonEdge(0, node_id, xy, length, 1.0, 1.0))
    nodes = tuple(
        SkeletonNode(node_id, point, degrees[node_id], 1.0, 1.0)
        for node_id, point in points.items()
    )
    return SkeletonGraph(nodes, tuple(edges))


def test_stroke_search_limit_reports_name_values_and_stage():
    with pytest.raises(StrokeSearchLimitError) as caught:
        rank_covering_walks(_star_graph(), limits=StrokeSearchLimits(max_states=1))

    assert caught.value.limit_name == "max_states"
    assert caught.value.configured_value == 1
    assert caught.value.observed_value == 2
    assert caught.value.search_stage == "junction-pairing-generation"


def test_junction_pairing_has_a_dedicated_bound():
    with pytest.raises(JunctionPairingLimitError) as caught:
        rank_covering_walks(_star_graph(), limits=StrokeSearchLimits(max_junction_pairings=1))

    assert caught.value.limit_name == "max_junction_pairings"
    assert caught.value.configured_value == 1
    assert caught.value.observed_value == 2
    assert caught.value.search_stage == "junction-pairing-generation"


def test_degree_nine_strict_search_preserves_pairing_limit_error():
    with pytest.raises(JunctionPairingLimitError) as caught:
        rank_covering_walks(
            _degree_nine_star(),
            limits=StrokeSearchLimits(max_junction_pairings=1000),
            on_limit="raise",
        )

    assert caught.value.limit_name == "max_junction_pairings"
    assert caught.value.observed_value == 1001


def test_hypothesis_budget_and_walk_step_limits_are_hard_bounds():
    with pytest.raises(StrokeSearchLimitError, match="max_hypotheses"):
        rank_covering_walks(_star_graph(), limits=StrokeSearchLimits(max_hypotheses=1))

    graph = SkeletonGraph(
        (
            SkeletonNode(0, (0.0, 0.0), 1, 1.0, 1.0),
            SkeletonNode(1, (1.0, 0.0), 2, 1.0, 1.0),
            SkeletonNode(2, (2.0, 0.0), 1, 1.0, 1.0),
        ),
        (
            SkeletonEdge(0, 1, np.asarray(((0.0, 0.0), (1.0, 0.0))), 1.0, 1.0, 1.0),
            SkeletonEdge(1, 2, np.asarray(((1.0, 0.0), (2.0, 0.0))), 1.0, 1.0, 1.0),
        ),
    )
    with pytest.raises(StrokeSearchLimitError, match="max_walk_steps"):
        rank_covering_walks(graph, limits=StrokeSearchLimits(max_walk_steps=1))


@pytest.mark.parametrize("diversity", ("none", "stroke-count"))
def test_diversity_does_not_bypass_hypothesis_or_walk_step_limits(diversity):
    with pytest.raises(StrokeSearchLimitError, match="max_hypotheses"):
        rank_covering_walks(
            _star_graph(), limits=StrokeSearchLimits(max_hypotheses=1), diversity=diversity
        )

    with pytest.raises(StrokeSearchLimitError, match="max_walk_steps"):
        rank_covering_walks(
            _star_graph(), limits=StrokeSearchLimits(max_walk_steps=1), diversity=diversity
        )


def test_bounded_degree_nine_search_is_deterministic_and_reports_truncation():
    graph = _degree_nine_star()
    limits = StrokeSearchLimits(max_pairings_per_junction=24, max_junction_combinations=64)
    first = rank_covering_walks(graph, limit=8, limits=limits, on_limit="truncate")
    second = rank_covering_walks(graph, limit=8, limits=limits, on_limit="truncate")

    def stable_key(hypothesis):
        return (
            tuple(walk.edge_ids for walk in hypothesis.walks),
            tuple((item.port_pairs, item.unpaired_ports) for item in hypothesis.junction_pairings),
            hypothesis.covered_edge_ids,
            hypothesis.repeated_edge_ids,
        )

    assert first
    assert [stable_key(item) for item in first] == [stable_key(item) for item in second]
    assert all(item.truncated for item in first)
    assert first[0].search_diagnostics.truncated
    assert "local-junction-search" in first[0].search_diagnostics.truncation_reasons
    assert first[0].search_diagnostics.maximum_junction_degree == 9
    assert all(
        item.covered_edge_ids | item.uncovered_edge_ids == frozenset(range(9)) for item in first
    )
    pair_counts = {
        len(pairing.port_pairs) for hypothesis in first for pairing in hypothesis.junction_pairings
    }
    assert len(pair_counts) > 1


def test_bounded_combination_budget_is_reported():
    base = _degree_nine_star()
    nodes = []
    edges = []
    for offset, shift in ((0, 0.0), (10, 20.0)):
        for node in base.nodes:
            nodes.append(
                SkeletonNode(
                    node.id + offset, (node.xy[0] + shift, node.xy[1]), node.degree, 1.0, 1.0
                )
            )
        for edge in base.edges:
            xy = edge.xy + np.asarray((shift, 0.0))
            edges.append(
                SkeletonEdge(edge.a + offset, edge.b + offset, xy, edge.length_px, 1.0, 1.0)
            )
    graph = SkeletonGraph(tuple(nodes), tuple(edges))
    result = rank_covering_walks(
        graph,
        limit=4,
        limits=StrokeSearchLimits(
            max_pairings_per_junction=16,
            max_junction_combinations=5,
        ),
        on_limit="truncate",
    )

    assert result
    diagnostic = result[0].search_diagnostics
    assert diagnostic.generated_combinations == 5
    assert "junction-combination-search" in diagnostic.truncation_reasons
    assert diagnostic.junction_port_counts == (9, 9)


def test_truncated_state_budget_still_returns_baseline():
    result = rank_covering_walks(
        _star_graph(),
        limits=StrokeSearchLimits(max_states=1),
        on_limit="truncate",
    )

    assert result
    assert result[0].covered_edge_ids == frozenset(range(3))
    assert "state-budget" in result[0].search_diagnostics.truncation_reasons


def test_hypothesis_budget_truncates_when_requested():
    result = rank_covering_walks(
        _star_graph(),
        limits=StrokeSearchLimits(max_hypotheses=1),
        on_limit="truncate",
    )

    assert len(result) == 1
    assert "hypothesis-budget" in result[0].search_diagnostics.truncation_reasons
