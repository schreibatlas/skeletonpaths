import numpy as np
import pytest

from skeletonpaths import (
    PathRankingPolicy,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
    rank_paths,
    select_path,
)


def _line_graph() -> SkeletonGraph:
    xy = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
    nodes = (
        SkeletonNode(0, (0.0, 0.0), 1, 0.0, 1.0),
        SkeletonNode(1, (3.0, 0.0), 1, 0.0, 1.0),
    )
    edge = SkeletonEdge(0, 1, xy, 3.0, 0.0, 1.0)
    return SkeletonGraph(nodes, (edge,))


def test_endpoint_tangents_rank_the_matching_route_orientation_first():
    graph = _line_graph()

    ranked = rank_paths(graph, expected_endpoint_tangents=((1.0, 0.0), (1.0, 0.0)))

    assert ranked[0].start_node == 0
    assert ranked[0].score.endpoint_tangent_error_deg == pytest.approx(0.0)
    assert ranked[1].score.endpoint_tangent_error_deg == pytest.approx(180.0)
    assert (
        select_path(
            graph,
            expected_endpoint_tangents=((1.0, 0.0), (1.0, 0.0)),
        ).orientation_ambiguous
        is False
    )


def test_symmetric_tangent_evidence_preserves_orientation_ambiguity():
    graph = _line_graph()

    selection = select_path(
        graph,
        expected_endpoint_tangents=((0.0, 1.0), (0.0, 1.0)),
    )

    assert selection.orientation_ambiguous is True
    assert selection.path.score.endpoint_tangent_error_deg == pytest.approx(90.0)


def test_tangent_noise_within_hard_tolerance_keeps_route_and_does_not_mutate_graph():
    graph = _line_graph()
    edge_xy_before = graph.edges[0].xy.copy()
    noisy_tangent = (np.cos(np.deg2rad(20.0)), np.sin(np.deg2rad(20.0)))
    policy = PathRankingPolicy(endpoint_tangents_are_hard=True)

    selection = select_path(
        graph,
        expected_endpoint_tangents=(noisy_tangent, noisy_tangent),
        tangent_tolerance_deg=35.0,
        policy=policy,
    )

    assert selection.path.start_node == 0
    assert selection.path.score.endpoint_tangent_error_deg == pytest.approx(20.0)
    assert selection.feasible_path_count == 1
    np.testing.assert_array_equal(graph.edges[0].xy, edge_xy_before)


def test_tangent_constraints_validate_vectors_and_tolerance():
    graph = _line_graph()

    with pytest.raises(ValueError, match="nonzero"):
        rank_paths(graph, expected_endpoint_tangents=((0.0, 0.0), None))
    with pytest.raises(ValueError, match="finite"):
        rank_paths(graph, expected_endpoint_tangents=((np.nan, 0.0), None))
    with pytest.raises(ValueError, match="between zero and 180"):
        rank_paths(graph, expected_endpoint_tangents=(None, None), tangent_tolerance_deg=181.0)
