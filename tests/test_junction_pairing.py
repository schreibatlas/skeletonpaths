import numpy as np

from skeletonpaths import SkeletonEdge, SkeletonGraph, SkeletonNode, rank_covering_walks


def _crossing_graph():
    points = {
        0: (0.0, 0.0),
        1: (2.0, 0.0),
        2: (0.0, 2.0),
        3: (-2.0, 0.0),
        4: (0.0, -2.0),
    }
    pairs = ((0, 1), (0, 2), (0, 3), (0, 4))
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


def test_junction_pairing_keeps_generic_alternatives_and_ranks_tangents():
    hypotheses = rank_covering_walks(_crossing_graph(), limit=32)

    pairings = [
        hypothesis.junction_pairings[0] for hypothesis in hypotheses if hypothesis.junction_pairings
    ]
    complete = [pairing for pairing in pairings if len(pairing.pairs) == 2]

    assert len(complete) == 3
    assert complete[0].pairs == ((0, 2), (1, 3))
    assert complete[0].tangent_cost < complete[1].tangent_cost
    assert all(pairing.node_id == 0 for pairing in pairings)
    assert all("physically" not in repr(pairing).lower() for pairing in pairings)


def test_figure_eight_crossing_generates_pairing_candidates():
    points = {
        0: (0.0, 0.0),
        1: (1.0, 0.0),
        2: (1.0, 1.0),
        3: (0.0, 1.0),
        4: (-1.0, 0.0),
        5: (-1.0, -1.0),
        6: (0.0, -1.0),
    }
    pairs = ((0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (4, 5), (5, 6), (6, 0))
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
    graph = SkeletonGraph(nodes, tuple(edges))

    hypotheses = rank_covering_walks(graph, limit=32)

    assert any(
        hypothesis.junction_pairings and len(hypothesis.junction_pairings[0].pairs) == 2
        for hypothesis in hypotheses
    )
    assert all(hypothesis.covered_edge_ids == frozenset(range(8)) for hypothesis in hypotheses)
