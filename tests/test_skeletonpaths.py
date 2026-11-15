import numpy as np
import pytest
from skimage.draw import circle_perimeter

from skeletonpaths import (
    DEFAULT_MAX_PATHS,
    DEFAULT_RANKING_POLICY,
    DEFAULT_SEARCH_LIMITS,
    NoFeasiblePathError,
    PathRankingPolicy,
    PathScore,
    PathSearchLimitError,
    PathSearchLimits,
    PathSelection,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonImage,
    SkeletonNode,
    SkeletonWalk,
    TopologyPathInventory,
    TopologyRoute,
    analyze_mask,
    build_skeleton_graph,
    covering_walk,
    graph_from_mask,
    graph_from_skeleton,
    prepare_topology_paths,
    prune_spurs,
    rank_paths,
    rank_topology_paths,
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

    selection = select_path(
        graph,
        path_kind="open",
        expected_cycles=0,
        expected_endpoints=((15.0, 3.0), (15.0, 27.0)),
        endpoint_tolerance_px=1.0,
        candidate_xy=bad_candidate,
    )

    np.testing.assert_array_equal(selection.path.xy[0], [15.0, 3.0])
    np.testing.assert_array_equal(selection.path.xy[-1], [15.0, 27.0])
    assert np.all(selection.path.xy[:, 0] == 15.0)
    assert selection.path.cycle_count == 0
    assert selection.path.confidence == 1.0


def test_candidate_orientation_breaks_reversed_path_ties_without_hard_endpoints():
    skeleton = np.zeros((9, 9), dtype=bool)
    skeleton[4, 1:8] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
    candidate = np.column_stack((np.arange(1.0, 8.0), np.full(7, 4.0)))

    selection = select_path(
        graph,
        path_kind="open",
        expected_cycles=0,
        candidate_xy=candidate,
    )

    np.testing.assert_array_equal(selection.path.xy[0], candidate[0])
    np.testing.assert_array_equal(selection.path.xy[-1], candidate[-1])
    assert selection.ambiguous is False
    assert selection.orientation_ambiguous is False


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
    assert ranked[0].score.endpoint_order_error_px == 0.0


def test_closed_skeleton_cycle_is_reported_and_selected_as_a_loop():
    skeleton = np.zeros((31, 31), dtype=bool)
    rows, columns = circle_perimeter(15, 15, 8)
    skeleton[rows, columns] = True
    graph = graph_from_skeleton(skeleton, min_spur_length=0.0)

    assert graph.cycle_count == 1
    selection = select_path(graph, path_kind="loop", expected_cycles=1)

    assert selection.path.cycle_count == 1
    assert selection.path.start_node == selection.path.end_node
    np.testing.assert_array_equal(selection.path.xy[0], selection.path.xy[-1])
    assert selection.path.length_px > 0


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

    assert all(node.radius_px == 2.0 for node in graph.nodes)
    assert graph.edges[0].mean_radius_px == 2.0
    assert graph.edges[0].confidence < 1.0


def test_open_with_loop_path_preserves_a_cycle_and_its_continuation():
    graph = SkeletonGraph(
        nodes=(
            SkeletonNode(0, (0.0, 0.0), degree=1, radius_px=1.0, confidence=1.0),
            SkeletonNode(1, (1.0, 0.0), degree=3, radius_px=1.0, confidence=1.0),
            SkeletonNode(2, (2.0, 0.0), degree=1, radius_px=1.0, confidence=1.0),
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

    selection = select_path(
        graph,
        path_kind="open-with-loop",
        expected_cycles=1,
        expected_endpoints=((0.0, 0.0), (2.0, 0.0)),
        endpoint_tolerance_px=0.0,
    )
    path = selection.path

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

    prepared_selection = select_path(
        graph,
        expected_cycles=0,
        candidate_xy=candidate,
        path_inventory=inventory,
    )
    direct_selection = select_path(
        graph,
        expected_cycles=0,
        candidate_xy=candidate,
    )

    np.testing.assert_array_equal(prepared_selection.path.xy, direct_selection.path.xy)
    assert prepared_selection.path.edge_ids == direct_selection.path.edge_ids
    assert prepared_selection.ambiguous == direct_selection.ambiguous


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


def test_rank_paths_limit_and_select_path_materialize_only_needed_paths(monkeypatch):
    import skeletonpaths.ranking as ranking

    graph = _parallel_route_graph()
    candidate = np.array([[0.0, 0.0], [4.0, 0.0]])
    complete = rank_paths(graph, candidate_xy=candidate)
    original_path_type = ranking.SkeletonPath
    materialized = []

    def record_path(*args, **kwargs):
        path = original_path_type(*args, **kwargs)
        materialized.append(path)
        return path

    monkeypatch.setattr(ranking, "SkeletonPath", record_path)
    limited = rank_paths(graph, candidate_xy=candidate, limit=2)

    assert len(limited) == 2
    assert len(materialized) == 2
    for actual, expected in zip(limited, complete[:2], strict=True):
        assert actual.edge_ids == expected.edge_ids
        assert actual.start_node == expected.start_node
        assert actual.score == expected.score
        np.testing.assert_array_equal(actual.xy, expected.xy)

    materialized.clear()

    def unexpected_rank_paths(*args, **kwargs):
        pytest.fail("select_path must not call rank_paths")

    monkeypatch.setattr(ranking, "rank_paths", unexpected_rank_paths)
    selection = ranking.select_path(graph, candidate_xy=candidate)

    assert len(materialized) == 1
    assert selection.path.edge_ids == complete[0].edge_ids
    assert selection.feasible_path_count == len(complete)


def test_rank_paths_limit_must_be_a_positive_integer():
    graph = _parallel_route_graph()

    for limit in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="limit must be a positive integer"):
            rank_paths(graph, limit=limit)


def test_ambiguity_does_not_change_measured_confidence():
    selection = select_path(_parallel_route_graph())

    assert selection.ambiguous is True
    assert selection.orientation_ambiguous is True
    assert selection.feasible_path_count == 4
    assert selection.path.confidence == 1.0
    assert selection.path.score.measured_confidence == 1.0


def test_ranking_policy_configures_ambiguity_thresholds():
    graph = _parallel_route_graph()
    edges = list(graph.edges)
    edge = edges[1]
    edges[1] = SkeletonEdge(
        edge.a,
        edge.b,
        edge.xy,
        edge.length_px,
        edge.mean_radius_px,
        0.5,
    )
    graph = SkeletonGraph(graph.nodes, tuple(edges))

    assert select_path(graph).ambiguous is False
    assert DEFAULT_RANKING_POLICY.guide_samples == 64
    policy = PathRankingPolicy(ambiguity_confidence=0.4)
    assert select_path(graph, policy=policy).ambiguous is True


def test_ranking_policy_configures_samples_and_guide_tie_grouping(monkeypatch):
    import skeletonpaths.ranking as ranking

    skeleton = np.zeros((9, 9), dtype=bool)
    skeleton[4, 1:8] = True
    graph = graph_from_skeleton(skeleton)
    candidate = np.array([[1.0, 4.0], [7.0, 4.0]])
    guide_samples = []
    turning_samples = []

    def guide_distance(xy, target, *, samples):
        guide_samples.append(samples)
        return 0.0 if xy[0, 0] == 7.0 else 1e-8

    def turning_cost(xy, *, samples):
        turning_samples.append(samples)
        return 0.0

    monkeypatch.setattr(ranking, "symmetric_polyline_distance", guide_distance)
    monkeypatch.setattr(ranking, "mean_squared_turn_angle", turning_cost)
    policy = PathRankingPolicy(
        guide_samples=17,
        turning_samples=23,
        guide_tie_tolerance_px=2e-8,
    )

    ranked = rank_paths(graph, candidate_xy=candidate, policy=policy)
    assert ranked[0].start_node == 0
    assert set(guide_samples) == {17}
    assert set(turning_samples) == {23}

    untied = rank_paths(
        graph,
        candidate_xy=candidate,
        policy=PathRankingPolicy(guide_tie_tolerance_px=0.0),
    )
    assert untied[0].start_node == 1


def test_turning_cost_does_not_resolve_ambiguity_unless_policy_enables_it():
    def make_edge(a, b, xy):
        length = float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())
        return SkeletonEdge(a, b, xy, length, 0.0, 1.0)

    graph = SkeletonGraph(
        nodes=(
            SkeletonNode(0, (0.0, 0.0), 1, 0.0, 1.0),
            SkeletonNode(1, (1.0, 0.0), 3, 0.0, 1.0),
            SkeletonNode(2, (5.0, 0.0), 3, 0.0, 1.0),
            SkeletonNode(3, (6.0, 0.0), 1, 0.0, 1.0),
        ),
        edges=(
            make_edge(0, 1, np.array([[0.0, 0.0], [1.0, 0.0]])),
            make_edge(1, 2, np.array([[1.0, 0.0], [5.0, 0.0]])),
            make_edge(
                1,
                2,
                np.array([[1.0, 0.0], [2.0, 1.0], [3.0, 0.0], [4.0, 1.0], [5.0, 0.0]]),
            ),
            make_edge(2, 3, np.array([[5.0, 0.0], [6.0, 0.0]])),
        ),
    )

    assert select_path(graph).ambiguous is True
    policy = PathRankingPolicy(turning_cost_is_evidence=True, ambiguity_turning_cost=0.0)
    assert select_path(graph, policy=policy).ambiguous is False


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
            SkeletonEdge(
                2,
                3,
                np.array([[10.0, 0.0], [10.0, 1.0], [11.0, 0.0]]),
                1.0 + np.sqrt(2.0),
                0.0,
                1.0,
            ),
        ),
    )

    assert graph.cycle_count == 1
    assert rank_paths(graph, expected_cycles=0)
    assert select_path(graph, expected_cycles=0).path.cycle_count == 0
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
    assert any(node.radius_px > 0.0 for node in graph.nodes)
    assert all(node.radius_px == 0.0 for node in skeleton.nodes)
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
    with pytest.raises(PathSearchLimitError, match="max_paths=1") as error:
        prepare_topology_paths(graph, max_paths=1)
    assert error.value.path_kind == "open"
    assert error.value.limit_name == "max_paths"
    assert error.value.limit_value == 1
    assert error.value.observed == 2
    with pytest.raises(PathSearchLimitError, match="max_paths=1"):
        rank_paths(graph, max_paths=1)
    with pytest.raises(ValueError, match="positive integer"):
        prepare_topology_paths(graph, max_paths=0)
    with pytest.raises(ValueError, match="max_states must be a positive integer"):
        PathSearchLimits(max_states=0)


def test_topology_search_state_limit_reports_structured_details():
    graph = _parallel_route_graph()
    limits = PathSearchLimits(max_paths=100, max_states=1)

    with pytest.raises(PathSearchLimitError, match="max_states=1") as error:
        rank_paths(graph, limits=limits)

    assert error.value.path_kind == "open"
    assert error.value.limit_name == "max_states"
    assert error.value.limit_value == 1
    assert error.value.observed == 2
    assert DEFAULT_SEARCH_LIMITS.max_paths == DEFAULT_MAX_PATHS
    assert DEFAULT_SEARCH_LIMITS.max_states == 100_000


def test_iterative_route_search_handles_graphs_deeper_than_recursion_limit():
    node_count = 1_201
    nodes = tuple(
        SkeletonNode(
            node_id,
            (float(node_id), 0.0),
            1 if node_id in {0, node_count - 1} else 2,
            0.0,
            1.0,
        )
        for node_id in range(node_count)
    )
    edges = tuple(
        SkeletonEdge(
            node_id,
            node_id + 1,
            np.array([[float(node_id), 0.0], [float(node_id + 1), 0.0]]),
            1.0,
            0.0,
            1.0,
        )
        for node_id in range(node_count - 1)
    )
    graph = SkeletonGraph(nodes, edges)

    paths = rank_paths(
        graph,
        limits=PathSearchLimits(max_paths=2, max_states=3_000),
    )

    assert len(paths) == 2
    assert all(path.length_px == node_count - 1 for path in paths)
    assert all(len(path.xy) == node_count for path in paths)


def test_selective_path_inventory_matches_dynamic_selection():
    graph = _parallel_route_graph()
    inventory = prepare_topology_paths(graph, path_kinds=("open",))
    prepared = select_path(graph, path_inventory=inventory)
    direct = select_path(graph)

    assert set(inventory.paths_by_kind) == {"open"}
    assert prepared.path.edge_ids == direct.path.edge_ids
    assert prepared.ambiguous == direct.ambiguous
    with pytest.raises(ValueError, match="does not include 'loop'"):
        select_path(graph, path_kind="loop", path_inventory=inventory)


def test_public_arrays_and_inventory_are_immutable():
    graph = graph_from_skeleton(np.pad(np.ones((1, 5), dtype=bool), ((2, 2), (1, 1))))
    selection = select_path(graph)
    inventory = prepare_topology_paths(graph)

    assert isinstance(selection, PathSelection)
    with pytest.raises(ValueError):
        graph.edges[0].xy[0, 0] = -1.0
    with pytest.raises(ValueError):
        selection.path.xy[0, 0] = -1.0
    with pytest.raises(TypeError):
        inventory.paths_by_kind["open"] = ()


def test_public_models_reject_inconsistent_geometry_and_route_ids():
    node = SkeletonNode(0, (0.0, 0.0), 1, 0.0, 1.0)
    edge = SkeletonEdge(0, 1, np.array([[0.0, 0.0], [1.0, 0.0]]), 1.0, 0.0, 1.0)

    with pytest.raises(ValueError, match="unknown node"):
        SkeletonGraph((node,), (edge,))
    with pytest.raises(ValueError, match="finite xy"):
        SkeletonEdge(0, 1, np.array([[0.0, 0.0], [np.nan, 0.0]]), 1.0, 0.0, 1.0)
    with pytest.raises(ValueError, match="radius"):
        SkeletonNode(0, (0.0, 0.0), 1, -1.0, 1.0)

    graph = graph_from_skeleton(np.pad(np.ones((1, 5), dtype=bool), ((2, 2), (1, 1))))
    invalid_route = TopologyRoute((len(graph.edges),), 0, 1, 0)
    with pytest.raises(ValueError, match="unknown edge"):
        TopologyPathInventory(graph, {"open": (invalid_route,)})


def test_graph_construction_preserves_short_spurs_by_default():
    skeleton = np.zeros((31, 31), dtype=bool)
    skeleton[4:27, 15] = True
    skeleton[15, 9:16] = True

    for build_graph in (graph_from_skeleton, graph_from_mask):
        preserved = build_graph(skeleton)
        pruned = build_graph(skeleton, min_spur_length=7.0)
        assert preserved.endpoint_count == 3
        assert preserved.junction_count == 1
        assert pruned.endpoint_count == 2
        assert pruned.junction_count == 0


def test_binary_images_accept_boolean_and_zero_one_values_only():
    binary = np.zeros((5, 7), dtype=np.uint8)
    binary[2, 1:6] = 1
    assert graph_from_skeleton(binary).endpoint_count == 2

    for invalid in (binary.astype(float) * np.nan, binary * 2):
        with pytest.raises(ValueError, match="finite zero and one"):
            graph_from_skeleton(invalid)
        with pytest.raises(ValueError, match="finite zero and one"):
            graph_from_mask(invalid)


def _draw_segments(segments):
    mask = np.zeros((9, 9), dtype=bool)
    for (row, column), (end_row, end_column) in segments:
        steps = max(abs(end_row - row), abs(end_column - column))
        for step in range(steps + 1):
            y = round(row + (end_row - row) * step / steps)
            x = round(column + (end_column - column) * step / steps)
            mask[y, x] = True
    return mask


@pytest.mark.parametrize(
    ("segments", "expected"),
    [
        ([((1, 4), (4, 4)), ((4, 1), (4, 7))], (3, 1, 0)),
        ([((1, 1), (7, 7)), ((1, 7), (7, 1))], (4, 1, 0)),
        ([((1, 4), (4, 4)), ((4, 4), (7, 1)), ((4, 4), (7, 7))], (3, 1, 0)),
        ([((4, 1), (4, 8)), ((1, 4), (4, 4)), ((4, 5), (7, 5))], (4, 2, 0)),
        (
            [
                ((1, 3), (4, 3)),
                ((1, 4), (4, 4)),
                ((4, 3), (7, 3)),
                ((4, 4), (7, 4)),
                ((3, 1), (3, 4)),
                ((4, 1), (4, 4)),
                ((3, 4), (3, 7)),
                ((4, 4), (4, 7)),
            ],
            (0, 16, 11),
        ),
        ([((1, 1), (7, 7))], (2, 0, 0)),
        (
            [
                ((2, 2), (2, 6)),
                ((2, 6), (6, 6)),
                ((6, 6), (6, 2)),
                ((6, 2), (2, 2)),
                ((4, 2), (4, 0)),
            ],
            (1, 1, 1),
        ),
    ],
    ids=("T", "X", "Y", "adjacent-junctions", "2x2-junction", "diagonal", "loop-junction"),
)
def test_junction_motifs_retain_per_pixel_topology(segments, expected):
    graph = graph_from_skeleton(_draw_segments(segments))
    assert (graph.endpoint_count, graph.junction_count, graph.cycle_count) == expected


def test_internal_module_exports_and_deprecated_names():
    import skeletonpaths
    import skeletonpaths.core as compatibility

    graph = graph_from_skeleton(np.pad(np.ones((1, 5), dtype=bool), ((2, 2), (1, 1))))
    ranked = rank_paths(graph)

    assert graph_from_skeleton.__module__ == "skeletonpaths.graph"
    assert graph_from_mask.__module__ == "skeletonpaths.image"
    assert analyze_mask.__module__ == "skeletonpaths.image"
    assert covering_walk.__module__ == "skeletonpaths.walk"
    assert SkeletonImage.__module__ == "skeletonpaths.model"
    assert SkeletonWalk.__module__ == "skeletonpaths.model"
    assert prepare_topology_paths.__module__ == "skeletonpaths.routing"
    assert rank_paths.__module__ == "skeletonpaths.ranking"
    assert compatibility.rank_paths is rank_paths
    assert compatibility.analyze_mask is analyze_mask
    assert compatibility.covering_walk is covering_walk
    assert skeletonpaths.SkeletonAnalysis.__module__ == "skeletonpaths.model"
    assert compatibility.SkeletonAnalysis is skeletonpaths.SkeletonAnalysis
    assert compatibility.DisconnectedGraphError is skeletonpaths.DisconnectedGraphError
    with pytest.warns(DeprecationWarning, match="rank_topology_paths"):
        legacy_ranked = rank_topology_paths(graph)
    with pytest.warns(DeprecationWarning, match="select_topology_path"):
        legacy_selected = select_topology_path(graph)
    assert legacy_ranked[0].edge_ids == ranked[0].edge_ids
    assert legacy_selected.edge_ids == ranked[0].edge_ids
