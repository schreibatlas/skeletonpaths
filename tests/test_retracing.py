import numpy as np

from skeletonpaths import (
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
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


def test_repeated_edges_are_explicit_and_respect_the_repeat_budget():
    graph = _star_graph()

    hypotheses = rank_covering_walks(graph, limit=32)
    repeated = [item for item in hypotheses if item.repeated_edge_ids]
    no_repeats = rank_covering_walks(
        graph,
        limits=StrokeSearchLimits(max_repeated_edges=0),
        limit=32,
    )

    assert repeated
    assert all(item.repeat_required_by_hypothesis for item in repeated)
    assert all(sum(walk.repeated_edge_count for walk in item.walks) > 0 for item in repeated)
    assert all(not item.repeated_edge_ids for item in no_repeats)
