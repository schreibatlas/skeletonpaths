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
