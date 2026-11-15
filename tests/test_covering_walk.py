import numpy as np
import pytest

from skeletonpaths import (
    DisconnectedGraphError,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
    SkeletonWalk,
    covering_walk,
)


def _graph(
    points: dict[int, tuple[float, float]], pairs: tuple[tuple[int, int], ...]
) -> SkeletonGraph:
    degrees = {node_id: 0 for node_id in points}
    for first, second in pairs:
        degrees[first] += 1
        degrees[second] += 1
    nodes = tuple(
        SkeletonNode(node_id, point, degrees[node_id], radius_px=1.0, confidence=1.0)
        for node_id, point in points.items()
    )
    edges = []
    for first, second in pairs:
        xy = np.asarray((points[first], points[second]), dtype=float)
        length = float(np.linalg.norm(xy[1] - xy[0]))
        edges.append(SkeletonEdge(first, second, xy, length, 1.0, 1.0))
    return SkeletonGraph(nodes, tuple(edges))


def _line_graph() -> SkeletonGraph:
    return _graph({0: (0.0, 0.0), 1: (1.0, 0.0), 2: (2.0, 0.0)}, ((0, 1), (1, 2)))


def _star_graph() -> SkeletonGraph:
    return _graph(
        {0: (1.0, 1.0), 1: (0.0, 1.0), 2: (2.0, 1.0), 3: (1.0, 0.0)},
        ((0, 1), (0, 2), (0, 3)),
    )


def _loop_graph() -> SkeletonGraph:
    return _graph(
        {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (1.0, 1.0), 3: (0.0, 1.0)},
        ((0, 1), (1, 2), (2, 3), (3, 0)),
    )


def _assert_coverage(graph: SkeletonGraph, walk: SkeletonWalk) -> None:
    node_by_id = {node.id: node for node in graph.nodes}
    assert walk.covered_edge_ids == tuple(range(len(graph.edges)))
    assert walk.covered_edge_count == len(graph.edges)
    assert walk.total_edge_count == len(graph.edges)
    assert walk.repeated_edge_count == len(walk.edge_ids) - len(set(walk.edge_ids))
    assert len(walk.edge_directions) == len(walk.edge_ids)
    assert not walk.xy.flags.writeable
    if walk.start_node is None:
        assert graph.nodes == ()
        assert walk.xy.shape == (0, 2)
        return

    current = walk.start_node
    expected_xy = [np.asarray(node_by_id[current].xy)]
    expected_length = 0.0
    for edge_id, direction in zip(walk.edge_ids, walk.edge_directions, strict=True):
        edge = graph.edges[edge_id]
        if direction == "forward":
            assert edge.a == current
            points = edge.xy
            current = edge.b
        else:
            assert edge.b == current
            points = edge.xy[::-1]
            current = edge.a
        expected_xy.extend(points[1:])
        expected_length += edge.length_px
    assert current == walk.end_node
    np.testing.assert_allclose(walk.xy, expected_xy)
    assert walk.length_px == pytest.approx(expected_length)


def test_covering_walk_covers_line_and_honors_reversed_endpoints():
    graph = _line_graph()

    walk = covering_walk(graph, start_node=2, end_node=0)

    _assert_coverage(graph, walk)
    assert walk.start_node == 2
    assert walk.end_node == 0
    np.testing.assert_array_equal(walk.xy[0], graph.nodes[2].xy)
    np.testing.assert_array_equal(walk.xy[-1], graph.nodes[0].xy)
    assert walk.edge_ids == (1, 0)


def test_covering_walk_deterministically_covers_branched_and_odd_degree_graphs():
    graph = _star_graph()

    first = covering_walk(graph, start_node=1, end_node=2)
    second = covering_walk(graph, start_node=1, end_node=2)

    _assert_coverage(graph, first)
    assert first.edge_ids == second.edge_ids
    np.testing.assert_array_equal(first.xy, second.xy)
    assert len(first.edge_ids) > len(graph.edges)
    assert first.start_node == 1
    assert first.end_node == 2
    np.testing.assert_array_equal(first.xy[0], graph.nodes[1].xy)
    np.testing.assert_array_equal(first.xy[-1], graph.nodes[2].xy)


def test_covering_walk_closes_even_degree_loops():
    graph = _loop_graph()

    walk = covering_walk(graph)

    _assert_coverage(graph, walk)
    assert walk.start_node == walk.end_node == 0
    assert len(walk.edge_ids) == len(graph.edges)
    np.testing.assert_array_equal(walk.xy[0], walk.xy[-1])


def test_covering_walk_handles_empty_and_isolated_graphs():
    empty = covering_walk(SkeletonGraph((), ()))
    isolated_graph = _graph({4: (2.0, 3.0)}, ())
    isolated = covering_walk(isolated_graph)

    assert empty.xy.shape == (0, 2)
    assert empty.start_node is None and empty.end_node is None
    assert isolated.xy.shape == (1, 2)
    assert isolated.start_node == isolated.end_node == 4


def test_covering_walk_rejects_disconnected_graphs_and_unknown_endpoints():
    graph = _graph(
        {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (4.0, 0.0), 3: (5.0, 0.0)},
        ((0, 1), (2, 3)),
    )

    with pytest.raises(DisconnectedGraphError, match="connected graph"):
        covering_walk(graph)
    with pytest.raises(ValueError, match="not present"):
        covering_walk(_line_graph(), start_node=7)


def test_covering_walk_single_edge_records_forward_and_reverse_direction():
    graph = _graph({0: (0.0, 0.0), 1: (2.0, 0.0)}, ((0, 1),))

    forward = covering_walk(graph, start_node=0, end_node=1)
    reverse = covering_walk(graph, start_node=1, end_node=0)

    _assert_coverage(graph, forward)
    _assert_coverage(graph, reverse)
    assert forward.edge_directions == ("forward",)
    assert reverse.edge_directions == ("reverse",)


def test_covering_walk_uses_graph_endpoints_and_covers_y_branch():
    graph = _graph(
        {0: (0.0, 0.0), 1: (-1.0, 1.0), 2: (1.0, 1.0), 3: (0.0, -1.0)},
        ((0, 1), (0, 2), (0, 3)),
    )

    walk = covering_walk(graph)

    _assert_coverage(graph, walk)
    assert walk.start_node in {1, 2, 3}
    assert walk.end_node in {1, 2, 3}
    assert walk.repeated_edge_count > 0


def test_covering_walk_loop_with_tail_and_same_start_end():
    graph = _graph(
        {
            0: (0.0, 0.0),
            1: (1.0, 0.0),
            2: (1.0, 1.0),
            3: (0.0, 1.0),
            4: (-1.0, 0.0),
        },
        ((0, 1), (1, 2), (2, 3), (3, 0), (0, 4)),
    )

    open_walk = covering_walk(graph)
    closed_walk = covering_walk(graph, start_node=4, end_node=4)

    _assert_coverage(graph, open_walk)
    _assert_coverage(graph, closed_walk)
    assert open_walk.start_node == 4
    assert open_walk.end_node == 0
    assert closed_walk.start_node == closed_walk.end_node == 4
    assert closed_walk.repeated_edge_count > 0


def test_covering_walk_closed_graph_defaults_to_lexicographic_xy_node():
    graph = _graph(
        {0: (10.0, 0.0), 1: (0.0, 5.0), 2: (0.0, -2.0), 3: (3.0, 0.0)},
        ((0, 1), (1, 2), (2, 3), (3, 0)),
    )

    walk = covering_walk(graph)

    _assert_coverage(graph, walk)
    assert walk.start_node == walk.end_node == 2


def test_skeleton_walk_rejects_inconsistent_local_invariants():
    from dataclasses import replace

    walk = covering_walk(_line_graph())
    with pytest.raises(ValueError, match="directions"):
        replace(walk, edge_directions=("sideways", *walk.edge_directions[1:]))
    with pytest.raises(ValueError, match="counts"):
        replace(walk, repeated_edge_count=walk.repeated_edge_count + 1)
    with pytest.raises(ValueError, match="length"):
        replace(walk, length_px=walk.length_px + 1.0)
