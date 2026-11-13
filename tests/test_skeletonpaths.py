import numpy as np
import pytest
from skimage.draw import circle_perimeter

from skeletonpaths import (
    DEFAULT_MAX_PATHS,
    NoFeasiblePathError,
    PathScore,
    PathSearchLimitError,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
    build_skeleton_graph,
    graph_from_mask,
    graph_from_skeleton,
    prepare_topology_paths,
    prune_spurs,
    rank_paths,
    select_path,
    select_topology_path,
)


def test_short_endpoint_spur_is_pruned_and_graph_chains_are_collapsed():
    skeleton = np.zeros((31, 31), dtype=bool)
    skeleton[4:27, 15] = True
    skeleton[15, 9:16] = True

    pruned = prune_spurs(skeleton, min_length_px=7.0)
    graph = build_skeleton_graph(
        skeleton,
        min_spur_length_px=7.0,
        already_skeleton=True,
    )

    assert not pruned[15, 9:15].any()
    assert graph.endpoint_count == 2
    assert graph.junction_count == 0
    assert len(graph.edges) == 1
    assert graph.edges[0].length_px == 22.0


def test_hard_endpoint_constraints_override_a_bad_candidate_path():
    skeleton = np.zeros((31, 31), dtype=bool)
    skeleton[3:28, 15] = True
    skeleton[15, 5:16] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
    bad_candidate = np.column_stack((np.arange(5, 16), np.full(11, 15)))

    path = select_path(
        graph,
        path_kind="open",
        expected_cycles=0,
        expected_endpoints=((15.0, 3.0), (15.0, 27.0)),
        endpoint_tolerance_px=1.0,
        candidate_xy=bad_candidate,
    )

    np.testing.assert_array_equal(path.xy[0], [15.0, 3.0])
    np.testing.assert_array_equal(path.xy[-1], [15.0, 27.0])
    assert np.all(path.xy[:, 0] == 15.0)
    assert path.cycle_count == 0
    assert path.confidence == 1.0


def test_candidate_orientation_breaks_reversed_path_ties_without_hard_endpoints():
    skeleton = np.zeros((9, 9), dtype=bool)
    skeleton[4, 1:8] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
    candidate = np.column_stack((np.arange(1.0, 8.0), np.full(7, 4.0)))

    path = select_path(
        graph,
        path_kind="open",
        expected_cycles=0,
        candidate_xy=candidate,
    )

    np.testing.assert_array_equal(path.xy[0], candidate[0])
    np.testing.assert_array_equal(path.xy[-1], candidate[-1])
    assert path.ambiguous is False
    assert path.orientation_ambiguous is False


def test_endpoint_orientation_breaks_subpixel_guide_distance_ties():
    edge_xy = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 1.0], [3.0, 2.0], [4.0, 2.0], [6.0, 3.0]])
    graph = SkeletonGraph(
        nodes=(
            SkeletonNode(0, (0.0, 0.0), 1, 0.0, 1.0),
            SkeletonNode(1, (6.0, 3.0), 1, 0.0, 1.0),
        ),
        edges=(
            SkeletonEdge(
                0,
                1,
                edge_xy,
                float(np.linalg.norm(np.diff(edge_xy, axis=0), axis=1).sum()),
                0.0,
                1.0,
            ),
        ),
    )
    candidate = np.array(
        [
            [0.0, 0.0],
            [1.6059721297588443, 0.3251191942180365],
            [2.9027296383923713, 1.7206560752229345],
            [4.540981680204202, 2.920835442908214],
            [6.0, 3.0],
        ]
    )

    ranked = rank_paths(graph, candidate_xy=candidate)
    forward = next(path for path in ranked if path.start_node == 0)
    reverse = next(path for path in ranked if path.start_node == 1)

    assert abs(forward.score.guide_distance_px - reverse.score.guide_distance_px) < 1e-9
    assert ranked[0].start_node == 0
    assert ranked[0].score.endpoint_orientation_error_px == 0.0


def test_closed_skeleton_cycle_is_reported_and_selected_as_a_loop():
    skeleton = np.zeros((31, 31), dtype=bool)
    rows, columns = circle_perimeter(15, 15, 8)
    skeleton[rows, columns] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)

    assert graph.cycle_count == 1
    path = select_path(graph, path_kind="loop", expected_cycles=1)

    assert path.cycle_count == 1
    assert path.start_node == path.end_node
    np.testing.assert_array_equal(path.xy[0], path.xy[-1])
    assert path.length_px > 0


def test_graph_propagates_radius_and_ink_confidence():
    skeleton = np.zeros((9, 9), dtype=bool)
    skeleton[2:7, 4] = True
    radius = np.full(skeleton.shape, 2.0)
    confidence = np.ones(skeleton.shape)
    confidence[4, 4] = 0.25
    graph = graph_from_skeleton(
        skeleton,
        radius=radius,
        confidence=confidence,
        min_spur_length=0.0,
    )

    assert all(node.radius == 2.0 for node in graph.nodes)
    assert graph.edges[0].mean_radius_px == 2.0
    assert graph.edges[0].confidence < 1.0


def test_open_with_loop_path_preserves_a_cycle_and_its_continuation():
    graph = SkeletonGraph(
        nodes=(
            SkeletonNode(0, (0.0, 0.0), degree=1, radius=1.0, confidence=1.0),
            SkeletonNode(1, (1.0, 0.0), degree=3, radius=1.0, confidence=1.0),
            SkeletonNode(2, (2.0, 0.0), degree=1, radius=1.0, confidence=1.0),
        ),
        edges=(
            SkeletonEdge(0, 1, np.array([[0.0, 0.0], [1.0, 0.0]]), 1.0, 1.0, 1.0),
            SkeletonEdge(
                1,
                1,
                np.array([[1.0, 0.0], [1.0, 1.0], [2.0, 1.0], [2.0, 0.0], [1.0, 0.0]]),
                4.0,
                1.0,
                1.0,
            ),
            SkeletonEdge(1, 2, np.array([[1.0, 0.0], [2.0, 0.0]]), 1.0, 1.0, 1.0),
        ),
    )

    path = select_topology_path(
        graph,
        path_kind="open-with-loop",
        expected_cycles=1,
        expected_endpoints=((0.0, 0.0), (2.0, 0.0)),
        endpoint_tolerance_px=0.0,
    )

    assert path.cycle_count == 1
    assert path.edge_ids == (0, 1, 2)
    np.testing.assert_array_equal(path.xy[0], [0.0, 0.0])
    np.testing.assert_array_equal(path.xy[-1], [2.0, 0.0])


def test_prepared_topology_path_inventory_matches_dynamic_selection():
    skeleton = np.zeros((9, 9), dtype=bool)
    skeleton[4, 1:8] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
    candidate = np.column_stack((np.arange(1.0, 8.0), np.full(7, 4.0)))
    inventory = prepare_topology_paths(graph)

    prepared_path = select_topology_path(
        graph,
        expected_cycles=0,
        candidate_xy=candidate,
        path_inventory=inventory,
    )
    direct_path = select_topology_path(
        graph,
        expected_cycles=0,
        candidate_xy=candidate,
    )

    np.testing.assert_array_equal(prepared_path.xy, direct_path.xy)
    assert prepared_path.edge_ids == direct_path.edge_ids
    assert prepared_path.ambiguous == direct_path.ambiguous


def test_public_coordinates_are_xy_not_row_column():
    skeleton = np.zeros((8, 10), dtype=bool)
    skeleton[3, 2:7] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)

    assert {node.xy for node in graph.nodes} == {(2.0, 3.0), (6.0, 3.0)}


def test_empty_skeleton_is_valid_empty_graph():
    graph = graph_from_skeleton(np.zeros((5, 5), dtype=bool), min_spur_length=0.0)
    assert graph.nodes == ()
    assert graph.edges == ()
    assert graph.component_count == 0
    assert graph.cycle_count == 0


def test_candidate_geometry_ranks_a_less_confident_route_first():
    skeleton = np.zeros((15, 15), dtype=bool)
    skeleton[7, 2:13] = True
    skeleton[2:13, 7] = True
    confidence = np.ones(skeleton.shape)
    confidence[7, :] = 0.1
    graph = graph_from_skeleton(
        skeleton,
        confidence=confidence,
        min_spur_length=0.0,
    )
    candidate = np.column_stack((np.arange(2.0, 13.0), np.full(11, 7.0)))

    ranked = rank_paths(graph, candidate_xy=candidate)

    assert np.all(ranked[0].xy[:, 1] == 7.0)
    assert ranked[0].score.guide_distance_px == pytest.approx(0.0)
    assert ranked[0].confidence < max(path.confidence for path in ranked)
    assert isinstance(ranked[0].score, PathScore)
    assert ranked[0].score.measured_confidence == ranked[0].confidence


def _parallel_route_graph():
    return SkeletonGraph(
        nodes=(
            SkeletonNode(0, (0.0, 0.0), 1, 1.0, 1.0),
            SkeletonNode(1, (1.0, 0.0), 3, 1.0, 1.0),
            SkeletonNode(2, (3.0, 0.0), 3, 1.0, 1.0),
            SkeletonNode(3, (4.0, 0.0), 1, 1.0, 1.0),
        ),
        edges=(
            SkeletonEdge(0, 1, np.array([[0.0, 0.0], [1.0, 0.0]]), 1.0, 1.0, 1.0),
            SkeletonEdge(
                1,
                2,
                np.array([[1.0, 0.0], [2.0, 1.0], [3.0, 0.0]]),
                2.0 * np.sqrt(2.0),
                1.0,
                1.0,
            ),
            SkeletonEdge(
                1,
                2,
                np.array([[1.0, 0.0], [2.0, -1.0], [3.0, 0.0]]),
                2.0 * np.sqrt(2.0),
                1.0,
                1.0,
            ),
            SkeletonEdge(2, 3, np.array([[3.0, 0.0], [4.0, 0.0]]), 1.0, 1.0, 1.0),
        ),
    )


def test_ambiguity_does_not_change_measured_confidence():
    path = select_path(_parallel_route_graph())

    assert path.ambiguous is True
    assert path.orientation_ambiguous is True
    assert path.confidence == 1.0
    assert path.score.measured_confidence == 1.0


def test_expected_cycles_constrains_a_route_not_an_unrelated_component():
    graph = SkeletonGraph(
        nodes=(
            SkeletonNode(0, (0.0, 0.0), 1, 0.0, 1.0),
            SkeletonNode(1, (2.0, 0.0), 1, 0.0, 1.0),
            SkeletonNode(2, (10.0, 0.0), 2, 0.0, 1.0),
            SkeletonNode(3, (11.0, 0.0), 2, 0.0, 1.0),
        ),
        edges=(
            SkeletonEdge(0, 1, np.array([[0.0, 0.0], [2.0, 0.0]]), 2.0, 0.0, 1.0),
            SkeletonEdge(2, 3, np.array([[10.0, 0.0], [11.0, 0.0]]), 1.0, 0.0, 1.0),
            SkeletonEdge(2, 3, np.array([[10.0, 0.0], [10.0, 1.0], [11.0, 0.0]]), 2.0, 0.0, 1.0),
        ),
    )

    assert graph.cycle_count == 1
    assert rank_paths(graph, expected_cycles=0)
    assert select_path(graph, expected_cycles=0).cycle_count == 0
    assert rank_paths(graph, expected_cycles=1) == ()
    with pytest.raises(NoFeasiblePathError):
        select_path(graph, expected_cycles=1)


def test_absent_expected_length_does_not_prefer_a_shorter_route():
    graph = SkeletonGraph(
        nodes=(
            SkeletonNode(0, (0.0, 0.0), 1, 0.0, 1.0),
            SkeletonNode(1, (20.0, 0.0), 1, 0.0, 1.0),
            SkeletonNode(2, (30.0, 0.0), 1, 0.0, 1.0),
            SkeletonNode(3, (33.0, 0.0), 1, 0.0, 1.0),
        ),
        edges=(
            SkeletonEdge(0, 1, np.array([[0.0, 0.0], [20.0, 0.0]]), 20.0, 0.0, 1.0),
            SkeletonEdge(2, 3, np.array([[30.0, 0.0], [33.0, 0.0]]), 3.0, 0.0, 1.0),
        ),
    )

    ranked = rank_paths(graph)

    assert ranked[0].edge_ids == (0,)
    assert ranked[0].length_px == 20.0
    assert ranked[0].score.length_error_px is None


def test_candidate_guide_requires_two_distinct_finite_points():
    skeleton = np.zeros((5, 8), dtype=bool)
    skeleton[2, 1:7] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)

    for candidate in (
        np.array([[1.0, 2.0]]),
        np.array([[1.0, 2.0], [1.0, 2.0]]),
        np.array([[1.0, 2.0], [np.nan, 2.0]]),
    ):
        with pytest.raises(ValueError, match="candidate curve"):
            rank_paths(graph, candidate_xy=candidate)


def test_graph_from_mask_derives_radius_and_filters_components_only_when_requested():
    mask = np.zeros((15, 16), dtype=bool)
    mask[4:7, 2:13] = True
    mask[11, 13] = True

    graph = graph_from_mask(mask, min_spur_length=0.0)
    filtered = graph_from_mask(mask, min_spur_length=0.0, min_component_area=2)
    skeleton = graph_from_skeleton(mask, min_spur_length=0.0)

    assert graph.component_count == 2
    assert filtered.component_count == 1
    assert any(node.radius > 0.0 for node in graph.nodes)
    assert all(node.radius == 0.0 for node in skeleton.nodes)
    assert all(edge.mean_radius_px > 0.0 for edge in graph.edges)


def test_pixel_adjacency_suppresses_diagonals_with_orthogonal_bridges():
    bridged = np.zeros((5, 5), dtype=bool)
    bridged[1, 1] = True
    bridged[1, 2] = True
    bridged[2, 1] = True
    bridged_graph = graph_from_skeleton(bridged, min_spur_length=0.0)

    diagonal = np.zeros((5, 5), dtype=bool)
    diagonal[1, 1] = True
    diagonal[2, 2] = True
    diagonal_graph = graph_from_skeleton(diagonal, min_spur_length=0.0)

    assert bridged_graph.cycle_count == 0
    assert bridged_graph.endpoint_count == 2
    assert len(bridged_graph.edges) == 1
    assert bridged_graph.edges[0].length_px == 2.0
    assert diagonal_graph.endpoint_count == 2
    assert len(diagonal_graph.edges) == 1
    assert diagonal_graph.edges[0].length_px == pytest.approx(np.sqrt(2.0))


def test_topology_route_enumeration_raises_at_candidate_limit():
    graph = _parallel_route_graph()

    assert DEFAULT_MAX_PATHS > 1
    with pytest.raises(PathSearchLimitError, match="max_paths=1"):
        prepare_topology_paths(graph, max_paths=1)
    with pytest.raises(PathSearchLimitError, match="max_paths=1"):
        rank_paths(graph, max_paths=1)
    with pytest.raises(ValueError, match="positive integer"):
        prepare_topology_paths(graph, max_paths=0)
