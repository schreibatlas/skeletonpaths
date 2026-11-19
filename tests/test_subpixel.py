import numpy as np
import pytest

from skeletonpaths import (
    RefinedEdgeDiagnostics,
    RefinedEdgeGeometry,
    RefinedSkeletonGeometry,
    RefinedWalkGeometry,
    SubpixelCenterlineOptions,
    SubpixelReconstructionLimitError,
    analyze_mask,
    covering_walk,
    refine_graph_geometry,
    refined_walk,
)


def _line_analysis():
    mask = np.zeros((15, 20), dtype=bool)
    mask[6:9, 2:18] = True
    return analyze_mask(mask)


def test_subpixel_result_models_are_public_and_immutable():
    analysis = _line_analysis()
    edge = analysis.graph.edges[0]
    points = edge.xy.copy()
    tangent = np.tile((1.0, 0.0), (len(points), 1))
    diagnostics = RefinedEdgeDiagnostics(
        raw_point_count=len(points),
        valid_cross_section_count=len(points),
        invalid_reason_counts={},
        median_shift_px=0.0,
        p95_shift_px=0.0,
        median_spline_residual_px=0.0,
        p95_spline_residual_px=0.0,
        selected_control_count=4,
        first_pass_improvement_px=0.0,
        junction_guard_sample_count=0,
        max_abs_curvature_radius=0.0,
        normal_probe_count=0,
        spline_fit_count=1,
    )
    refined_edge = RefinedEdgeGeometry(
        edge_id=0,
        xy=points,
        tangent=tangent,
        curvature=np.zeros(len(points)),
        radius_px=np.ones(len(points)),
        confidence=np.ones(len(points)),
        length_px=edge.length_px,
        source="binary-distance-fallback",
        diagnostics=diagnostics,
    )
    node_xy = {node.id: node.xy for node in analysis.graph.nodes}
    node_confidence = {node.id: node.confidence for node in analysis.graph.nodes}
    node_radius = {node.id: node.radius_px for node in analysis.graph.nodes}
    refined_graph = RefinedSkeletonGeometry(
        analysis=analysis,
        edges=(refined_edge,),
        node_xy=node_xy,
        node_confidence=node_confidence,
        node_radius_px=node_radius,
        diagnostics={"edge_count": 1},
    )
    walk_geometry = RefinedWalkGeometry(
        xy=points,
        tangent=tangent,
        curvature=np.zeros(len(points)),
        radius_px=np.ones(len(points)),
        confidence=np.ones(len(points)),
        length_px=edge.length_px,
        edge_ids=(0,),
        edge_directions=("forward",),
    )

    assert refined_graph.graph is analysis.graph
    assert refined_graph.edge_by_id[0] is refined_edge
    assert walk_geometry.edge_ids == (0,)
    assert not refined_edge.xy.flags.writeable
    assert not walk_geometry.tangent.flags.writeable
    with pytest.raises(TypeError):
        refined_graph.node_xy[0] = (0.0, 0.0)


def test_subpixel_options_validate_bounded_parameters():
    options = SubpixelCenterlineOptions()
    assert options.refinement_passes == 2
    assert options.normal_sample_step_px == 0.125
    with pytest.raises(ValueError, match="refinement_passes"):
        SubpixelCenterlineOptions(refinement_passes=4)
    with pytest.raises(ValueError, match="min_sample_confidence"):
        SubpixelCenterlineOptions(min_sample_confidence=1.1)


def _offset_rectangle():
    analysis = _line_analysis()
    y, x = np.mgrid[: analysis.mask.shape[0], : analysis.mask.shape[1]]
    field = np.minimum.reduce((y - 5.8, 8.4 - y, x - 1.5, 17.5 - x))
    return analysis, field


def test_refine_graph_geometry_uses_signed_field_and_preserves_graph():
    analysis, field = _offset_rectangle()
    original_edge_xy = tuple(edge.xy.copy() for edge in analysis.graph.edges)
    geometry = refine_graph_geometry(analysis, decision_field=field)

    assert geometry.graph is analysis.graph
    assert len(geometry.edges) == len(analysis.graph.edges)
    assert geometry.diagnostics["source"] == "decision-field"
    assert geometry.edges[0].source == "decision-field"
    assert geometry.edges[0].diagnostics.valid_cross_section_count > 0
    assert abs(float(np.median(geometry.edges[0].xy[:, 1])) - 7.1) <= 0.12
    for edge, refined in zip(analysis.graph.edges, geometry.edges, strict=True):
        np.testing.assert_array_equal(edge.xy, original_edge_xy[refined.edge_id])
        np.testing.assert_allclose(refined.xy[0], geometry.node_xy[edge.a])
        np.testing.assert_allclose(refined.xy[-1], geometry.node_xy[edge.b])
        assert np.all(np.isfinite(refined.tangent))
        assert np.all(np.isfinite(refined.curvature))


def test_refine_graph_geometry_fallback_and_input_validation():
    analysis = _line_analysis()
    fallback = refine_graph_geometry(analysis)
    assert fallback.diagnostics["source"] == "binary-distance-fallback"
    assert fallback.edges[0].source == "binary-distance-fallback"
    assert np.any(np.abs(fallback.edges[0].xy - np.rint(fallback.edges[0].xy)) > 1e-8)

    with pytest.raises(ValueError, match="decision_field"):
        refine_graph_geometry(analysis, decision_field=np.ones((2, 2)))
    wrong_sign = np.ones(analysis.mask.shape)
    with pytest.raises(ValueError, match="nonnegative inside"):
        refine_graph_geometry(analysis, decision_field=wrong_sign)
    with pytest.raises(ValueError, match="finite and match"):
        refine_graph_geometry(analysis, decision_field=np.full(analysis.mask.shape, np.nan))


def test_refine_graph_geometry_handles_empty_and_low_gradient_inputs():
    empty = analyze_mask(np.zeros((8, 9), dtype=bool))
    result = refine_graph_geometry(empty)
    assert result.edges == ()
    assert result.node_xy == {}

    analysis = _line_analysis()
    low_gradient = refine_graph_geometry(analysis, decision_field=np.zeros(analysis.mask.shape))
    assert low_gradient.edges[0].diagnostics.valid_cross_section_count == 0
    assert low_gradient.edges[0].diagnostics.invalid_reason_counts["center_not_inside"] > 0


@pytest.mark.parametrize("thickness", [1, 2])
def test_one_and_two_pixel_strokes_refine_without_topology_changes(thickness):
    mask = np.zeros((15, 24), dtype=bool)
    mask[7 : 7 + thickness, 2:22] = True
    analysis = analyze_mask(mask)
    geometry = refine_graph_geometry(analysis)

    assert geometry.graph is analysis.graph
    assert len(geometry.edges) == 1
    expected_y = 7.0 + (thickness - 1) / 2.0
    assert abs(float(np.median(geometry.edges[0].xy[:, 1])) - expected_y) <= 0.2
    assert geometry.edges[0].diagnostics.valid_cross_section_count > 0


def test_touching_parallel_strokes_keep_the_analyzed_topology():
    mask = np.zeros((32, 24), dtype=bool)
    mask[4:28, 5:8] = True
    mask[4:28, 8:11] = True
    analysis = analyze_mask(mask)
    geometry = refine_graph_geometry(analysis)

    assert geometry.graph is analysis.graph
    assert geometry.graph.component_count == analysis.graph.component_count == 1
    assert tuple(edge.edge_id for edge in geometry.edges) == tuple(range(len(analysis.graph.edges)))
    assert all(np.isfinite(edge.xy).all() for edge in geometry.edges)


def test_isolated_pixel_and_disconnected_masks_keep_component_semantics():
    isolated = np.zeros((9, 12), dtype=bool)
    isolated[4, 6] = True
    isolated_analysis = analyze_mask(isolated)
    isolated_geometry = refine_graph_geometry(isolated_analysis)
    assert isolated_geometry.graph is isolated_analysis.graph
    assert isolated_geometry.graph.component_count == 1
    assert isolated_geometry.edges == ()

    disconnected = np.zeros((28, 48), dtype=bool)
    disconnected[4:7, 3:20] = True
    disconnected[18:21, 28:45] = True
    analysis = analyze_mask(disconnected)
    geometry = refine_graph_geometry(analysis)
    assert geometry.graph is analysis.graph
    assert geometry.graph.component_count == analysis.graph.component_count == 2
    assert len(geometry.edges) == len(analysis.graph.edges)


def test_refine_graph_geometry_obeys_probe_budget():
    analysis, field = _offset_rectangle()
    options = SubpixelCenterlineOptions(max_normal_probes=1)
    with pytest.raises(SubpixelReconstructionLimitError, match="max_normal_probes"):
        refine_graph_geometry(analysis, decision_field=field, options=options)

    sample_options = SubpixelCenterlineOptions(max_refinement_samples=1)
    with pytest.raises(SubpixelReconstructionLimitError, match="max_refinement_samples"):
        refine_graph_geometry(analysis, decision_field=field, options=sample_options)


def test_refine_graph_geometry_shares_junction_positions():
    mask = np.zeros((31, 31), dtype=bool)
    mask[3:16, 14:17] = True
    mask[14:17, 4:27] = True
    analysis = analyze_mask(mask)
    assert analysis.graph.junction_count >= 1
    geometry = refine_graph_geometry(analysis)

    assert geometry.graph is analysis.graph
    assert geometry.graph.cycle_count == analysis.graph.cycle_count
    junction_nodes = {node.id for node in analysis.graph.nodes if node.degree > 2}
    for edge in geometry.edges:
        original = analysis.graph.edges[edge.edge_id]
        if original.a in junction_nodes:
            np.testing.assert_allclose(edge.xy[0], geometry.node_xy[original.a])
            assert edge.diagnostics.junction_guard_sample_count > 0
        if original.b in junction_nodes:
            np.testing.assert_allclose(edge.xy[-1], geometry.node_xy[original.b])
            assert edge.diagnostics.junction_guard_sample_count > 0


def test_refine_graph_geometry_closes_pure_loop_without_new_topology():
    mask = np.zeros((25, 27), dtype=bool)
    mask[3:6, 4:23] = True
    mask[19:22, 4:23] = True
    mask[3:22, 4:7] = True
    mask[3:22, 20:23] = True
    analysis = analyze_mask(mask)
    assert analysis.graph.cycle_count == 1
    assert len(analysis.graph.edges) == 1
    assert analysis.graph.edges[0].a == analysis.graph.edges[0].b
    geometry = refine_graph_geometry(analysis)

    assert len(geometry.edges) == 1
    assert geometry.graph.cycle_count == 1
    assert geometry.edges[0].edge_id == 0
    np.testing.assert_allclose(geometry.edges[0].xy[0], geometry.edges[0].xy[-1])
    assert len(geometry.edges[0].curve_segments) == 2


def test_refined_walk_reverses_edge_geometry_and_resamples_per_edge():
    analysis, field = _offset_rectangle()
    geometry = refine_graph_geometry(analysis, decision_field=field)
    walk = covering_walk(analysis.graph)
    assert len(walk.edge_ids) == 1

    forward = refined_walk(geometry, walk)
    reverse = refined_walk(geometry, walk.reversed())
    assert forward.edge_ids == walk.edge_ids
    assert forward.edge_directions == walk.edge_directions
    np.testing.assert_array_equal(reverse.xy, forward.xy[::-1])
    np.testing.assert_array_equal(reverse.tangent, -forward.tangent[::-1])
    np.testing.assert_array_equal(reverse.curvature, -forward.curvature[::-1])

    sampled = refined_walk(geometry, walk, sample_count=17)
    assert len(sampled.xy) == 17
    np.testing.assert_allclose(sampled.xy[0], geometry.node_xy[walk.start_node])
    np.testing.assert_allclose(sampled.xy[-1], geometry.node_xy[walk.end_node])
    with pytest.raises(ValueError, match="sample_count"):
        refined_walk(geometry, walk, sample_count=1)


def test_refined_walk_reuses_retraced_edges_and_handles_empty_walks():
    mask = np.zeros((31, 31), dtype=bool)
    mask[3:16, 14:17] = True
    mask[14:17, 4:27] = True
    analysis = analyze_mask(mask)
    geometry = refine_graph_geometry(analysis)
    walk = covering_walk(analysis.graph)
    assert walk.repeated_edge_count > 0
    refined = refined_walk(geometry, walk)
    assert refined.edge_ids == walk.edge_ids
    assert refined.edge_directions == walk.edge_directions

    chunks = {}
    cursor = 0
    for edge_id, direction in zip(walk.edge_ids, walk.edge_directions, strict=True):
        edge = geometry.edges[edge_id]
        count = len(edge.xy)
        start = cursor
        stop = start + count
        points = refined.xy[start:stop]
        tangents = refined.tangent[start:stop]
        curvature = refined.curvature[start:stop]
        expected_xy = edge.xy if direction == "forward" else edge.xy[::-1]
        expected_tangent = edge.tangent if direction == "forward" else -edge.tangent[::-1]
        expected_curvature = edge.curvature if direction == "forward" else -edge.curvature[::-1]
        np.testing.assert_array_equal(points, expected_xy)
        np.testing.assert_array_equal(tangents, expected_tangent)
        np.testing.assert_array_equal(curvature, expected_curvature)
        chunks.setdefault(edge_id, []).append((direction, points, tangents, curvature))
        cursor = stop
    for occurrences in chunks.values():
        if len(occurrences) < 2:
            continue
        first, second = occurrences[:2]
        if first[0] != second[0]:
            np.testing.assert_array_equal(second[1], first[1][::-1])
            np.testing.assert_array_equal(second[2], -first[2][::-1])
            np.testing.assert_array_equal(second[3], -first[3][::-1])
        else:
            np.testing.assert_array_equal(second[1], first[1])

    empty = analyze_mask(np.zeros((8, 9), dtype=bool))
    empty_geometry = refine_graph_geometry(empty)
    empty_walk = refined_walk(empty_geometry, covering_walk(empty.graph))
    assert empty_walk.xy.shape == (0, 2)

    isolated_mask = np.zeros((8, 9), dtype=bool)
    isolated_mask[4, 5] = True
    isolated = analyze_mask(isolated_mask)
    isolated_geometry = refine_graph_geometry(isolated)
    isolated_walk = refined_walk(isolated_geometry, covering_walk(isolated.graph))
    assert isolated_walk.xy.shape == (1, 2)


def _capsule_field(shape, start, end, radius):
    y, x = np.mgrid[: shape[0], : shape[1]]
    points = np.stack((x, y), axis=-1)
    start = np.asarray(start, dtype=float)
    vector = np.asarray(end, dtype=float) - start
    parameter = np.clip(
        np.sum((points - start) * vector, axis=-1) / np.dot(vector, vector),
        0.0,
        1.0,
    )
    nearest = start + parameter[..., None] * vector
    return radius - np.linalg.norm(points - nearest, axis=-1)


def _polyline_field(shape, points, radius):
    y, x = np.mgrid[: shape[0], : shape[1]]
    grid = np.stack((x.ravel(), y.ravel()), axis=-1)
    distance = np.full(len(grid), np.inf)
    for start, end in zip(points[:-1], points[1:], strict=True):
        vector = end - start
        parameter = np.clip(
            np.sum((grid - start) * vector, axis=1) / np.dot(vector, vector),
            0.0,
            1.0,
        )
        nearest = start + parameter[:, None] * vector
        distance = np.minimum(distance, np.linalg.norm(grid - nearest, axis=1))
    return radius - distance.reshape(shape)


def _cubic_bezier(control, parameter):
    t = parameter[:, None]
    one_minus = 1.0 - t
    p0, p1, p2, p3 = control
    xy = one_minus**3 * p0 + 3 * one_minus**2 * t * p1 + 3 * one_minus * t**2 * p2 + t**3 * p3
    first = 3 * one_minus**2 * (p1 - p0) + 6 * one_minus * t * (p2 - p1) + 3 * t**2 * (p3 - p2)
    second = 6 * one_minus * (p2 - 2 * p1 + p0) + 6 * t * (p3 - 2 * p2 + p1)
    cross = first[:, 0] * second[:, 1] - first[:, 1] * second[:, 0]
    curvature = cross / np.linalg.norm(first, axis=1) ** 3
    return xy, first, curvature


@pytest.mark.parametrize("center_y", [10.1, 10.25, 10.5, 10.75, 10.9])
def test_fractional_offset_straight_strokes_are_subpixel(center_y):
    shape = (32, 70)
    field = _capsule_field(shape, (7.0, center_y), (62.0, center_y), 2.5)
    analysis = analyze_mask(field > 0.0)
    geometry = refine_graph_geometry(analysis, decision_field=field)
    assert len(geometry.edges) == 1

    edge = geometry.edges[0]
    assert abs(float(np.median(edge.xy[:, 1])) - center_y) <= 0.12
    interior = (edge.xy[:, 0] > 15.0) & (edge.xy[:, 0] < 54.0)
    heading_error = np.degrees(np.arccos(np.clip(np.abs(edge.tangent[interior, 0]), 0.0, 1.0)))
    assert float(np.sqrt(np.mean(heading_error**2))) <= 0.5


@pytest.mark.parametrize("angle_degrees", [7.0, 23.0, 41.0, 68.0, 83.0])
def test_rotated_straight_strokes_remove_pixel_staircase(angle_degrees):
    angle = np.radians(angle_degrees)
    tangent = np.asarray((np.cos(angle), np.sin(angle)))
    center = np.asarray((40.0, 40.0))
    start, end = center - 24.0 * tangent, center + 24.0 * tangent
    field = _capsule_field((82, 82), start, end, 2.8)
    analysis = analyze_mask(field > 0.0)
    geometry = refine_graph_geometry(analysis, decision_field=field)
    assert len(geometry.edges) == 1

    edge = geometry.edges[0]
    progress = (edge.xy - start) @ tangent
    interior = (progress > 7.0) & (progress < 41.0)
    alignment = np.clip(np.abs(edge.tangent[interior] @ tangent), 0.0, 1.0)
    heading_error = np.degrees(np.arccos(alignment))
    assert float(np.sqrt(np.mean(heading_error**2))) <= 1.5


@pytest.mark.parametrize("rotation_degrees", [0.0, 45.0, 90.0])
def test_circular_arc_geometry_tracks_position_and_signed_curvature(rotation_degrees):
    center = np.asarray((36.0, 36.0))
    radius = 17.0
    rotation = np.radians(rotation_degrees)
    start_angle, end_angle = -1.1 + rotation, 1.1 + rotation
    y, x = np.mgrid[:72, :72]
    points = np.stack((x, y), axis=-1)
    angle = np.arctan2(points[..., 1] - center[1], points[..., 0] - center[0])
    clipped = np.clip(angle, start_angle, end_angle)
    nearest = center + radius * np.stack((np.cos(clipped), np.sin(clipped)), axis=-1)
    field = 2.6 - np.linalg.norm(points - nearest, axis=-1)
    analysis = analyze_mask(field > 0.0)
    geometry = refine_graph_geometry(analysis, decision_field=field)
    assert len(geometry.edges) == 1

    edge = geometry.edges[0]
    recovered_radius = np.linalg.norm(edge.xy - center, axis=1)
    theta = np.arctan2(edge.xy[:, 1] - center[1], edge.xy[:, 0] - center[0])
    interior = (theta > start_angle + 0.2) & (theta < end_angle - 0.2)
    errors = np.abs(recovered_radius[interior] - radius)
    assert float(np.median(errors)) <= 0.20
    analytic_tangent = np.column_stack((-np.sin(theta[interior]), np.cos(theta[interior])))
    direction = np.sign(np.sum(edge.tangent[interior] * analytic_tangent, axis=1))
    assert np.all(edge.curvature[interior] * direction > 0.0)
    curvature_error = np.abs(edge.curvature[interior] * radius - direction)
    assert float(np.median(curvature_error)) <= 0.1


def test_curvature_radius_guard_rejects_cross_sections():
    center = np.asarray((24.0, 24.0))
    radius = 7.0
    start_angle, end_angle = -1.0, 1.0
    y, x = np.mgrid[:48, :48]
    points = np.stack((x, y), axis=-1)
    angle = np.arctan2(points[..., 1] - center[1], points[..., 0] - center[0])
    clipped = np.clip(angle, start_angle, end_angle)
    nearest = center + radius * np.stack((np.cos(clipped), np.sin(clipped)), axis=-1)
    field = 2.4 - np.linalg.norm(points - nearest, axis=-1)
    analysis = analyze_mask(field > 0.0)
    options = SubpixelCenterlineOptions(max_curvature_radius=0.1)
    geometry = refine_graph_geometry(analysis, decision_field=field, options=options)

    assert geometry.edges[0].diagnostics.invalid_reason_counts["high_curvature_radius"] > 0


def test_cubic_s_curve_tangent_and_curvature_follow_ground_truth():
    control = np.asarray(((7.0, 42.0), (20.0, 5.0), (48.0, 66.0), (63.0, 24.0)))
    parameters = np.linspace(0.0, 1.0, 300)
    centerline, analytic_tangent, analytic_curvature = _cubic_bezier(control, parameters)
    field = _polyline_field((72, 72), centerline, 2.5)
    analysis = analyze_mask(field > 0.0)
    geometry = refine_graph_geometry(analysis, decision_field=field)
    assert len(geometry.edges) == 1

    edge = geometry.edges[0]
    distances = np.linalg.norm(edge.xy[:, None, :] - centerline[None, :, :], axis=2)
    nearest = np.argmin(distances, axis=1)
    interior = (nearest > 20) & (nearest < len(parameters) - 20)
    alignment = np.clip(
        np.abs(np.sum(edge.tangent[interior] * analytic_tangent[nearest[interior]], axis=1)),
        0.0,
        1.0,
    )
    heading_error = np.degrees(np.arccos(alignment))
    assert float(np.sqrt(np.mean(heading_error**2))) <= 5.0
    orientation = np.sign(
        np.sum(edge.tangent[interior] * analytic_tangent[nearest[interior]], axis=1)
    )
    expected_curvature = analytic_curvature[nearest[interior]] * orientation
    correlation = np.corrcoef(edge.curvature[interior], expected_curvature)[0, 1]
    assert correlation > 0.6


def test_straight_stroke_resolution_invariance_preserves_topology():
    base_center = (31.0, 14.25)
    topologies = []
    centers = []
    headings = []
    for scale in (1, 2, 4):
        shape = (40 * scale, 72 * scale)
        field = _capsule_field(
            shape,
            (7.0 * scale, base_center[1] * scale),
            (64.0 * scale, base_center[1] * scale),
            2.5 * scale,
        )
        analysis = analyze_mask(field > 0.0)
        geometry = refine_graph_geometry(analysis, decision_field=field)
        topologies.append(
            (
                analysis.graph.component_count,
                len(analysis.graph.edges),
                analysis.graph.cycle_count,
            )
        )
        edge = geometry.edges[0]
        centers.append(float(np.median(edge.xy[:, 1])) / scale)
        normalized_vertical = np.abs(
            edge.tangent[:, 1] / np.maximum(np.linalg.norm(edge.tangent, axis=1), 1e-12)
        )
        headings.append(float(np.median(normalized_vertical)))

    assert topologies[0] == topologies[1] == topologies[2]
    errors = np.abs(np.asarray(centers) - base_center[1])
    assert max(errors) <= 0.12
    assert max(headings) <= 0.02
