import numpy as np
import pytest
from scipy.ndimage import binary_dilation
from skimage.draw import disk as draw_disk
from skimage.draw import line
from skimage.morphology import disk

from skeletonpaths import (
    JunctionRegionOptions,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
    SubpixelCenterlineOptions,
    analyze_mask,
    graph_from_skeleton,
    rank_covering_walks,
)
from skeletonpaths.hypotheses import _incident_edges
from skeletonpaths.subpixel import _local_tangents, _observe_edge, _WorkBudget


def _draw_segments(segments, shape=(15, 19)):
    skeleton = np.zeros(shape, dtype=bool)
    for (row, column), (end_row, end_column) in segments:
        steps = max(abs(end_row - row), abs(end_column - column))
        for step in range(steps + 1):
            y = round(row + (end_row - row) * step / max(steps, 1))
            x = round(column + (end_column - column) * step / max(steps, 1))
            skeleton[y, x] = True
    return skeleton


def _e_like_mask(scale, stroke_width, contact_gap, rotation=0):
    mask = np.zeros((75 * scale, 75 * scale), dtype=bool)
    baseline = 38 * scale
    left_contact = 32 * scale
    right_contact = left_contact + contact_gap * scale
    loop_top = 21 * scale

    for start, end in (
        ((baseline, 4 * scale), (baseline, 70 * scale)),
        ((baseline, left_contact), (loop_top, left_contact)),
        ((loop_top, left_contact), (loop_top, right_contact)),
        ((loop_top, right_contact), (baseline, right_contact)),
    ):
        rows, columns = line(*start, *end)
        mask[rows, columns] = True
    mask = binary_dilation(mask, structure=disk(stroke_width // 2))
    return np.rot90(mask, rotation)


def _realistic_e_contact_mask(scale=1, rotation=0):
    mask = np.zeros((120 * scale, 130 * scale), dtype=bool)
    baseline = 76 * scale

    def draw_variable_stroke(points, radii):
        for (x, y), radius in zip(points, radii, strict=True):
            rows, columns = draw_disk((y, x), radius, shape=mask.shape)
            mask[rows, columns] = True

    baseline_x = np.arange(8 * scale, 111 * scale)
    draw_variable_stroke(
        np.column_stack((baseline_x, np.full_like(baseline_x, baseline))),
        np.linspace(3 * scale, 4 * scale, len(baseline_x)),
    )

    gap = 16 * scale
    start = np.asarray((40 * scale, baseline), dtype=float)
    control_one = np.asarray((40 * scale + 0.28 * gap, baseline))
    control_two = np.asarray((40 * scale + 0.72 * gap, baseline - 42 * scale))
    end = np.asarray((40 * scale + gap, baseline), dtype=float)
    parameter = np.linspace(0.0, 1.0, 200 * scale)
    points = (
        ((1.0 - parameter) ** 3)[:, None] * start
        + (3.0 * (1.0 - parameter) ** 2 * parameter)[:, None] * control_one
        + (3.0 * (1.0 - parameter) * parameter**2)[:, None] * control_two
        + (parameter**3)[:, None] * end
    )
    draw_variable_stroke(points, np.linspace(4 * scale, 2.25 * scale, len(points)))
    return np.rot90(mask, rotation)


@pytest.mark.parametrize(
    ("scale", "stroke_width", "contact_gap", "rotation"),
    (
        (1, 3, 4, 0),
        (1, 5, 6, 0),
        (2, 6, 4, 0),
        (2, 6, 4, 1),
        (2, 10, 6, 0),
    ),
    ids=("thin", "medium", "scaled", "rotated", "thick-scaled"),
)
def test_e_like_loop_contracts_to_one_junction_and_remains_coverable(
    scale, stroke_width, contact_gap, rotation
):
    analysis = analyze_mask(_e_like_mask(scale, stroke_width, contact_gap, rotation))
    graph = analysis.graph

    assert graph.endpoint_count == 2
    assert graph.junction_count == 1
    assert graph.cycle_count == 1
    assert graph.raw_junction_seed_count >= 2
    region = analysis.junction_regions[0]
    assert region.port_count == 4
    assert region.radius_px > 0.0
    assert region.support_pixels
    assert region.node_id in {node.id for node in graph.nodes}
    assert [edge for edge in graph.edges if edge.a == edge.b == region.node_id]

    all_edges = frozenset(range(len(graph.edges)))
    hypotheses = rank_covering_walks(graph, limit=64)
    assert len(hypotheses) <= 64
    assert any(
        len(hypothesis.walks) == 1 and hypothesis.covered_edge_ids == all_edges
        for hypothesis in hypotheses
    )


@pytest.mark.parametrize(("scale", "rotation"), ((1, 0), (2, 0), (1, 1), (1, 2), (1, 3)))
def test_realistic_e_contact_does_not_create_spurious_second_semantic_junction(scale, rotation):
    analysis = analyze_mask(_realistic_e_contact_mask(scale, rotation))
    graph = analysis.graph

    assert graph.endpoint_count == 2
    assert graph.junction_count == 1
    assert graph.semantic_junction_count == 1
    assert graph.cycle_count == 1
    assert graph.raw_junction_seed_count >= 2
    assert graph.provisional_junction_count >= 2
    assert analysis.provisional_junction_count == graph.provisional_junction_count
    assert analysis.semantic_junction_count == graph.semantic_junction_count


def test_semantic_cleanup_is_scale_stable():
    graphs = [analyze_mask(_realistic_e_contact_mask(scale=scale)).graph for scale in (1, 2)]

    assert [
        (graph.endpoint_count, graph.junction_count, graph.cycle_count) for graph in graphs
    ] == [
        (2, 1, 1),
        (2, 1, 1),
    ]


def test_semantic_cleanup_is_rotation_stable():
    graphs = [
        analyze_mask(_realistic_e_contact_mask(rotation=rotation)).graph for rotation in range(4)
    ]

    assert [
        (graph.endpoint_count, graph.junction_count, graph.cycle_count) for graph in graphs
    ] == [
        (2, 1, 1),
    ] * 4


def test_semantic_cleanup_diagnostics_are_deterministic():
    mask = _realistic_e_contact_mask()
    first = analyze_mask(mask).graph
    second = analyze_mask(mask).graph

    assert (
        first.raw_junction_seed_count,
        first.provisional_junction_count,
        first.semantic_junction_count,
    ) == (
        second.raw_junction_seed_count,
        second.provisional_junction_count,
        second.semantic_junction_count,
    )
    assert [(node.xy, node.degree) for node in first.nodes] == [
        (node.xy, node.degree) for node in second.nodes
    ]
    assert [(edge.a, edge.b, edge.xy.tolist()) for edge in first.edges] == [
        (edge.a, edge.b, edge.xy.tolist()) for edge in second.edges
    ]


def test_junction_region_radius_tracks_stroke_width_and_scale():
    thin = analyze_mask(_e_like_mask(1, 3, 4)).junction_regions[0].radius_px
    wider = analyze_mask(_e_like_mask(1, 5, 6)).junction_regions[0].radius_px
    scaled = analyze_mask(_e_like_mask(2, 6, 4)).junction_regions[0].radius_px

    assert wider > thin
    assert scaled == pytest.approx(2.0 * thin, rel=0.08)


def test_adjacent_raw_junction_seeds_contract_to_one_region():
    skeleton = _draw_segments([((4, 1), (4, 8)), ((1, 4), (4, 4)), ((4, 5), (7, 5))], shape=(9, 10))

    graph = graph_from_skeleton(skeleton)

    assert graph.raw_junction_seed_count == 2
    assert graph.junction_count == 1
    assert graph.endpoint_count == 4
    region = graph.junction_regions[0]
    assert region.port_count == 4
    assert graph.nodes[region.node_id].degree == 4


def test_diagonal_x_crossing_has_one_semantic_junction():
    skeleton = _draw_segments(
        [((1, 2), (7, 8)), ((1, 3), (7, 9)), ((1, 8), (7, 2)), ((1, 9), (7, 3))],
        shape=(11, 12),
    )

    graph = graph_from_skeleton(skeleton)

    assert graph.raw_junction_seed_count > 1
    assert graph.junction_count == 1
    assert graph.junction_regions[0].port_count == 4


def test_semantic_cleanup_preserves_two_distinct_nearby_crossings():
    skeleton = np.zeros((15, 19), dtype=bool)
    skeleton[7, 1:18] = True
    skeleton[2:13, 5] = True
    skeleton[2:13, 13] = True
    radius = np.zeros(skeleton.shape, dtype=float)
    radius[skeleton] = 1.0

    graph = graph_from_skeleton(skeleton, radius=radius)

    assert graph.raw_junction_seed_count == 2
    assert graph.junction_count == 2
    assert [region.port_count for region in graph.junction_regions] == [4, 4]


def test_semantic_cleanup_never_absorbs_endpoint():
    skeleton = np.zeros((12, 15), dtype=bool)
    skeleton[7, 2:13] = True
    skeleton[3:8, 7] = True
    radius = np.zeros(skeleton.shape, dtype=float)
    radius[skeleton] = 5.0

    graph = graph_from_skeleton(skeleton, radius=radius)

    assert graph.endpoint_count == 3
    region = graph.junction_regions[0]
    assert (3, 7) not in region.support_pixels
    assert region.port_count == 3


def test_pure_loop_keeps_one_cycle_anchor_without_a_junction_region():
    skeleton = np.zeros((12, 12), dtype=bool)
    skeleton[3, 3:9] = True
    skeleton[8, 3:9] = True
    skeleton[3:9, 3] = True
    skeleton[3:9, 8] = True

    graph = graph_from_skeleton(skeleton)

    assert graph.raw_junction_seed_count == 0
    assert graph.junction_regions == ()
    assert graph.junction_count == 0
    assert graph.cycle_count == 1
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 1
    assert graph.edges[0].a == graph.edges[0].b


def test_junction_options_validate_and_can_disable_contraction():
    options = JunctionRegionOptions(enabled=False)
    skeleton = _draw_segments([((4, 1), (4, 8)), ((1, 4), (4, 4)), ((4, 5), (7, 5))], shape=(9, 10))

    graph = graph_from_skeleton(skeleton, junction_options=options)

    assert graph.junction_regions == ()
    assert graph.junction_count == graph.raw_junction_seed_count
    with pytest.raises(ValueError, match="maximum merge radius"):
        JunctionRegionOptions(minimum_merge_radius_px=2.0, maximum_merge_radius_px=1.0)
    with pytest.raises(ValueError, match="representative"):
        JunctionRegionOptions(representative="unsupported")


def _self_loop_junction_graph():
    points = {0: (0.0, 0.0), 1: (-2.0, 0.0), 2: (2.0, 0.0)}
    nodes = (
        SkeletonNode(0, points[0], 4, 1.0, 1.0),
        SkeletonNode(1, points[1], 1, 1.0, 1.0),
        SkeletonNode(2, points[2], 1, 1.0, 1.0),
    )
    geometries = (
        np.asarray((points[0], points[1])),
        np.asarray((points[0], points[2])),
        np.asarray(((0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0), (0.0, 0.0))),
    )
    edges = tuple(
        SkeletonEdge(
            a=0,
            b=1 if edge_id == 0 else 2 if edge_id == 1 else 0,
            xy=xy,
            length_px=float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum()),
            mean_radius_px=1.0,
            confidence=1.0,
        )
        for edge_id, xy in enumerate(geometries)
    )
    return SkeletonGraph(nodes, edges)


def test_self_loop_has_two_junction_ports_and_a_complete_one_walk_hypothesis():
    graph = _self_loop_junction_graph()
    incident = _incident_edges(graph)[0]

    assert graph.junction_count == 1
    assert graph.cycle_count == 1
    assert graph.nodes[0].degree == len(incident) == 4
    assert (2, "a") in incident
    assert (2, "b") in incident
    assert any(
        pairing.pairs == ((0, 2), (1, 2))
        and {(edge_id, side) for pair in pairing.port_pairs for edge_id, side in pair}
        == {(0, "a"), (1, "a"), (2, "a"), (2, "b")}
        for hypothesis in rank_covering_walks(graph, limit=32)
        for pairing in hypothesis.junction_pairings
    )

    first = rank_covering_walks(graph, limit=32)
    second = rank_covering_walks(graph, limit=32)
    one_walks = [
        hypothesis
        for hypothesis in first
        if len(hypothesis.walks) == 1 and hypothesis.covered_edge_ids == frozenset(range(3))
    ]
    assert one_walks
    assert len(first) <= 32
    assert [
        (hypothesis.walks[0].edge_ids, hypothesis.walks[0].edge_directions) for hypothesis in first
    ] == [
        (hypothesis.walks[0].edge_ids, hypothesis.walks[0].edge_directions) for hypothesis in second
    ]


def test_subpixel_junction_guard_is_adaptive_and_edge_length_capped():
    mask = np.zeros((43, 43), dtype=bool)
    mask[19:24, 3:40] = True
    mask[3:40, 19:24] = True
    analysis = analyze_mask(mask)
    region = analysis.junction_regions[0]
    edge = next(edge for edge in analysis.graph.edges if region.node_id in (edge.a, edge.b))
    field = np.where(analysis.mask, 1.0, -1.0)

    def observe(options):
        tangents = _local_tangents(edge.xy, options.tangent_window_px)
        return _observe_edge(
            edge.xy, tangents, edge, analysis, field, options, _WorkBudget(options)
        )

    baseline = observe(
        SubpixelCenterlineOptions(junction_guard_px=0.0, junction_guard_radius_factor=0.0)
    )
    adaptive = observe(
        SubpixelCenterlineOptions(
            junction_guard_px=0.0,
            junction_guard_radius_factor=2.0,
            junction_guard_max_edge_fraction=0.4,
        )
    )
    capped = observe(
        SubpixelCenterlineOptions(
            junction_guard_px=100.0,
            junction_guard_radius_factor=100.0,
            junction_guard_max_edge_fraction=0.25,
        )
    )

    assert adaptive.junction_guard_count > baseline.junction_guard_count
    assert capped.junction_guard_count < len(edge.xy)
    support = set(region.support_pixels)
    for index, point in enumerate(edge.xy):
        pixel = (int(np.rint(point[1])), int(np.rint(point[0])))
        if pixel in support:
            assert not adaptive.valid[index]
