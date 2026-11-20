import numpy as np

from skeletonpaths import (
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
    analyze_mask,
    orientation_variants,
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


def _five_arm_graph():
    endpoint_points = ((10.0, 0.0), (3.0, 9.0), (-8.0, 6.0), (-8.0, -6.0), (3.0, -9.0))
    points = {0: (0.0, 0.0), **{index + 1: point for index, point in enumerate(endpoint_points)}}
    nodes = (SkeletonNode(0, points[0], 5, 1.0, 1.0),) + tuple(
        SkeletonNode(index + 1, point, 1, 1.0, 1.0) for index, point in enumerate(endpoint_points)
    )
    edges = []
    for node_id in range(1, 6):
        xy = np.asarray((points[0], points[node_id]))
        length = float(np.linalg.norm(xy[1] - xy[0]))
        edges.append(SkeletonEdge(0, node_id, xy, length, 1.0, 1.0))
    return SkeletonGraph(nodes, tuple(edges))


def _hypothesis_identity(hypothesis):
    walks = tuple(
        (walk.edge_ids, walk.edge_directions, walk.start_node, walk.end_node)
        for walk in hypothesis.walks
    )
    pairings = tuple(
        (pairing.node_id, pairing.port_pairs, pairing.unpaired_ports)
        for pairing in hypothesis.junction_pairings
    )
    return walks, pairings


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


def test_stroke_count_diversity_preserves_one_walk_candidate_under_small_limit():
    graph = _five_arm_graph()
    legacy = rank_covering_walks(graph, limit=5, diversity="none")
    diverse = rank_covering_walks(graph, limit=5, diversity="stroke-count")

    all_edges = frozenset(range(len(graph.edges)))
    all_candidates = rank_covering_walks(graph, limit=100, diversity="none")
    best_by_stroke_count = {}
    for hypothesis in all_candidates:
        if not hypothesis.uncovered_edge_ids:
            best_by_stroke_count.setdefault(
                hypothesis.stroke_count, _hypothesis_identity(hypothesis)
            )
    diverse_identities = {_hypothesis_identity(item) for item in diverse}
    assert set(best_by_stroke_count.values()) <= diverse_identities
    assert len(diverse) == 5
    assert any(
        len(hypothesis.walks) == 1
        and not hypothesis.uncovered_edge_ids
        and hypothesis.covered_edge_ids == all_edges
        for hypothesis in diverse
    )
    assert not any(len(hypothesis.walks) == 1 for hypothesis in legacy)


def test_diversity_does_not_change_candidate_scores():
    graph = _five_arm_graph()
    all_candidates = rank_covering_walks(graph, limit=100, diversity="none")
    diverse = rank_covering_walks(graph, limit=5, diversity="stroke-count")
    scores = {_hypothesis_identity(item): item.score for item in all_candidates}

    assert all(item.score == scores[_hypothesis_identity(item)] for item in diverse)


def test_diversity_is_deterministic():
    graph = _five_arm_graph()
    first = rank_covering_walks(graph, limit=5, diversity="stroke-count")
    second = rank_covering_walks(graph, limit=5, diversity="stroke-count")

    assert [(_hypothesis_identity(item), item.score) for item in first] == [
        (_hypothesis_identity(item), item.score) for item in second
    ]


def test_diversity_none_preserves_legacy_global_ranking():
    graph = _five_arm_graph()
    default = rank_covering_walks(graph, limit=5)
    explicit_none = rank_covering_walks(graph, limit=5, diversity="none")

    assert [_hypothesis_identity(item) for item in explicit_none] == [
        _hypothesis_identity(item) for item in default
    ]


def test_analysis_entry_point_forwards_stroke_count_diversity():
    mask = np.zeros((24, 40), dtype=bool)
    mask[4:7, 2:17] = True
    mask[15:18, 23:38] = True
    analysis = analyze_mask(mask)

    direct = rank_covering_walks(analysis.graph, limit=5, diversity="stroke-count")
    through_analysis = stroke_hypotheses_from_analysis(analysis, limit=5, diversity="stroke-count")

    assert [_hypothesis_identity(item) for item in through_analysis] == [
        _hypothesis_identity(item) for item in direct
    ]


def test_global_reverse_preserves_covered_edges_and_length():
    graph = _five_arm_graph()
    all_edges = frozenset(range(len(graph.edges)))
    hypothesis = next(
        item
        for item in rank_covering_walks(graph, limit=100)
        if len(item.walks) == 1 and item.covered_edge_ids == all_edges
    )

    supplied, reverse = orientation_variants(hypothesis)

    assert supplied.orientation_relation == "as-supplied"
    assert reverse.orientation_relation == "global-reversal"
    assert reverse.covered_edge_ids == hypothesis.covered_edge_ids
    assert reverse.uncovered_edge_ids == hypothesis.uncovered_edge_ids
    assert reverse.repeated_edge_ids == hypothesis.repeated_edge_ids
    assert reverse.pen_lift_count == hypothesis.pen_lift_count
    assert reverse.score == hypothesis.score
    assert reverse.junction_pairings == hypothesis.junction_pairings
    assert reverse.route_ambiguous == hypothesis.route_ambiguous
    assert reverse.orientation_ambiguous == hypothesis.orientation_ambiguous
    assert reverse.component_order_ambiguous == hypothesis.component_order_ambiguous
    assert reverse.orientation_ambiguous_strokes == hypothesis.orientation_ambiguous_strokes
    assert reverse.repeat_required_by_hypothesis == hypothesis.repeat_required_by_hypothesis
    assert reverse.truncated == hypothesis.truncated
    np.testing.assert_array_equal(reverse.walks[0].xy, hypothesis.walks[0].xy[::-1])
    assert reverse.walks[0].covered_edge_ids == hypothesis.walks[0].covered_edge_ids
    assert reverse.walks[0].length_px == hypothesis.walks[0].length_px


def test_global_reverse_swaps_open_endpoints():
    graph = _five_arm_graph()
    all_edges = frozenset(range(len(graph.edges)))
    hypothesis = next(
        item
        for item in rank_covering_walks(graph, limit=100)
        if len(item.walks) == 1 and item.covered_edge_ids == all_edges
    )
    supplied, reverse = orientation_variants(hypothesis)
    forward_walk = supplied.walks[0]
    reversed_walk = reverse.walks[0]

    assert graph.nodes[forward_walk.start_node].degree == 1
    assert graph.nodes[forward_walk.end_node].degree == 1
    assert reversed_walk.start_node == forward_walk.end_node
    assert reversed_walk.end_node == forward_walk.start_node
    assert reversed_walk.edge_ids == tuple(reversed(forward_walk.edge_ids))
    assert reversed_walk.edge_directions == tuple(
        "reverse" if direction == "forward" else "forward"
        for direction in reversed(forward_walk.edge_directions)
    )


def test_global_reverse_reverses_multiwalk_order_and_each_walk():
    hypothesis = rank_covering_walks(_disconnected_graph())[0]
    supplied, reverse = orientation_variants(hypothesis)

    assert len(reverse.walks) == len(supplied.walks)
    assert reverse.orientation_ambiguous_strokes == tuple(
        reversed(supplied.orientation_ambiguous_strokes)
    )
    for actual, original in zip(reverse.walks, reversed(supplied.walks), strict=True):
        np.testing.assert_array_equal(actual.xy, original.xy[::-1])
        assert actual.edge_ids == tuple(reversed(original.edge_ids))
        assert actual.start_node == original.end_node
        assert actual.end_node == original.start_node


def test_unresolved_orientation_remains_ambiguous_in_both_variants():
    graph = _five_arm_graph()
    all_edges = frozenset(range(len(graph.edges)))
    hypothesis = next(
        item
        for item in rank_covering_walks(graph, limit=100)
        if len(item.walks) == 1 and item.covered_edge_ids == all_edges
    )
    supplied, reverse = orientation_variants(hypothesis)

    assert supplied.orientation_ambiguous
    assert reverse.orientation_ambiguous
