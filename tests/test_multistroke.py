import numpy as np

from skeletonpaths import (
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
    analyze_mask,
    rank_covering_walks,
    stroke_hypotheses_from_analysis,
)


def _disconnected_graph():
    points = {
        0: (0.0, 0.0),
        1: (2.0, 0.0),
        2: (5.0, 0.0),
        3: (7.0, 0.0),
        4: (10.0, 0.0),
    }
    pairs = ((0, 1), (2, 3))
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


def test_disconnected_graph_reports_walks_lifts_and_order_ambiguity():
    hypothesis = rank_covering_walks(_disconnected_graph())[0]

    assert hypothesis.stroke_count == 3
    assert hypothesis.pen_lift_count == 2
    assert hypothesis.component_order_ambiguous
    assert hypothesis.orientation_ambiguous_strokes == (True, True, True)
    assert hypothesis.covered_edge_ids == frozenset({0, 1})


def test_analysis_entry_point_orchestrates_component_hypotheses():
    mask = np.zeros((24, 40), dtype=bool)
    mask[4:7, 2:17] = True
    mask[15:18, 23:38] = True
    analysis = analyze_mask(mask)

    hypotheses = stroke_hypotheses_from_analysis(analysis)

    assert analysis.component_labels is not None
    assert analysis.graph.component_count == 2
    assert hypotheses[0].stroke_count == 2
    assert hypotheses[0].component_order_ambiguous
    assert hypotheses[0].covered_edge_ids == frozenset(range(len(analysis.graph.edges)))
