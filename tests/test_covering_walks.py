import numpy as np

from skeletonpaths import SkeletonEdge, SkeletonGraph, SkeletonNode, rank_covering_walks


def _graph(points, edges):
    degrees = {node_id: 0 for node_id in points}
    for first, second in edges:
        degrees[first] += 1
        degrees[second] += 1
    nodes = tuple(
        SkeletonNode(node_id, point, degrees[node_id], 1.0, 1.0)
        for node_id, point in points.items()
    )
    graph_edges = []
    for first, second in edges:
        xy = np.asarray((points[first], points[second]), dtype=float)
        length = float(np.linalg.norm(xy[1] - xy[0]))
        graph_edges.append(SkeletonEdge(first, second, xy, length, 1.0, 1.0))
    return SkeletonGraph(nodes, tuple(graph_edges))


def test_rank_covering_walks_reports_complete_walk_and_separate_scores():
    graph = _graph({0: (0.0, 0.0), 1: (2.0, 0.0), 2: (4.0, 0.0)}, ((0, 1), (1, 2)))

    hypotheses = rank_covering_walks(graph)
    hypothesis = hypotheses[0]

    assert hypothesis.covered_edge_ids == frozenset({0, 1})
    assert hypothesis.uncovered_edge_ids == frozenset()
    assert hypothesis.repeated_edge_ids == ()
    assert hypothesis.pen_lift_count == 0
    assert hypothesis.score.coverage_error == 0.0
    assert hypothesis.score.uncovered_length_px == 0.0
    assert hypothesis.score.repeat_length_px == 0.0
    assert hypothesis.orientation_ambiguous
    assert hypothesis.orientation_ambiguous_strokes == (True,)
    assert not hypothesis.truncated


def test_rank_covering_walks_orders_alternatives_deterministically_and_marks_limit():
    graph = _graph(
        {
            0: (0.0, 0.0),
            1: (-1.0, 0.0),
            2: (1.0, 0.0),
            3: (0.0, 1.0),
        },
        ((0, 1), (0, 2), (0, 3)),
    )

    first = rank_covering_walks(graph, limit=2)
    second = rank_covering_walks(graph, limit=2)

    assert len(first) == 2
    assert all(item.truncated for item in first)
    assert [
        (item.score, item.junction_pairings, tuple(walk.edge_ids for walk in item.walks))
        for item in first
    ] == [
        (item.score, item.junction_pairings, tuple(walk.edge_ids for walk in item.walks))
        for item in second
    ]
    assert all(item.covered_edge_ids == frozenset({0, 1, 2}) for item in first)


def test_rank_covering_walks_handles_loop_and_open_route_with_a_loop():
    loop = _graph(
        {0: (0.0, 0.0), 1: (2.0, 0.0), 2: (2.0, 2.0), 3: (0.0, 2.0)},
        ((0, 1), (1, 2), (2, 3), (3, 0)),
    )
    open_with_loop = _graph(
        {
            0: (0.0, 0.0),
            1: (2.0, 0.0),
            2: (2.0, 2.0),
            3: (0.0, 2.0),
            4: (-2.0, 0.0),
        },
        ((0, 1), (1, 2), (2, 3), (3, 0), (0, 4)),
    )

    loop_hypothesis = rank_covering_walks(loop)[0]
    open_hypothesis = rank_covering_walks(open_with_loop)[0]

    assert loop_hypothesis.covered_edge_ids == frozenset(range(4))
    assert loop_hypothesis.walks[0].start_node == loop_hypothesis.walks[0].end_node
    assert open_hypothesis.covered_edge_ids == frozenset(range(5))
    assert not open_hypothesis.uncovered_edge_ids


def test_planarcurve_guide_geometry_orients_a_walk_and_reports_distance():
    graph = _graph({0: (0.0, 0.0), 1: (3.0, 0.0)}, ((0, 1),))
    guide = np.asarray(((3.0, 0.0), (0.0, 0.0)))

    hypothesis = rank_covering_walks(graph, guide_paths=(guide,))[0]

    assert hypothesis.walks[0].start_node == 1
    assert hypothesis.walks[0].steps[0].direction == "b-to-a"
    assert hypothesis.score.guide_distance_px == 0.0
    assert not hypothesis.orientation_ambiguous
