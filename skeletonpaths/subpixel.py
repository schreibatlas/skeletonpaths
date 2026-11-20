"""Topology-preserving reconstruction of continuous subpixel centerlines."""

from __future__ import annotations

from dataclasses import replace
from math import ceil, floor
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

from .model import (
    RefinedEdgeDiagnostics,
    RefinedEdgeGeometry,
    RefinedSkeletonGeometry,
    RefinedWalkGeometry,
    SkeletonAnalysis,
    SkeletonEdge,
    SkeletonWalk,
    SubpixelCenterlineOptions,
)


class SubpixelReconstructionError(RuntimeError):
    """Raised when continuous geometry cannot be reconstructed reliably."""


class SubpixelReconstructionLimitError(RuntimeError):
    """Raised when a configured refinement work bound would be exceeded."""

    def __init__(self, limit_name: str, configured: int, observed: int) -> None:
        self.limit_name = limit_name
        self.configured = configured
        self.observed = observed
        super().__init__(
            f"subpixel refinement exceeded {limit_name}={configured} (observed {observed})"
        )


class _WorkBudget:
    def __init__(self, options: SubpixelCenterlineOptions) -> None:
        self.options = options
        self.samples = 0
        self.probes = 0

    def add_samples(self, count: int) -> None:
        observed = self.samples + count
        if observed > self.options.max_refinement_samples:
            raise SubpixelReconstructionLimitError(
                "max_refinement_samples", self.options.max_refinement_samples, observed
            )
        self.samples = observed

    def add_probes(self, count: int) -> None:
        observed = self.probes + count
        if observed > self.options.max_normal_probes:
            raise SubpixelReconstructionLimitError(
                "max_normal_probes", self.options.max_normal_probes, observed
            )
        self.probes = observed


class _Observations:
    def __init__(self, points: np.ndarray) -> None:
        self.raw_points = np.array(points, dtype=float, copy=True)
        self.centers = self.raw_points.copy()
        self.radii = np.zeros(len(points), dtype=float)
        self.confidence = np.zeros(len(points), dtype=float)
        self.valid = np.zeros(len(points), dtype=bool)
        self.reasons: dict[str, int] = {}
        self.probes = 0
        self.junction_guard_count = 0

    def reject(self, index: int, reason: str) -> None:
        self.reasons[reason] = self.reasons.get(reason, 0) + 1
        if reason == "junction_guard":
            self.junction_guard_count += 1
        self.valid[index] = False
        self.confidence[index] = 0.0
        self.centers[index] = self.raw_points[index]


def _binary_signed_distance(mask: np.ndarray) -> np.ndarray:
    try:
        from scipy.ndimage import distance_transform_edt
    except ImportError as error:  # pragma: no cover - depends on optional installation
        raise ImportError(
            "binary-distance subpixel fallback requires SciPy; install skeletonpaths[image]"
        ) from error
    return distance_transform_edt(mask) - distance_transform_edt(~mask)


def _validate_decision_field(field: ArrayLike, mask: np.ndarray) -> np.ndarray:
    try:
        values = np.asarray(field, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("decision_field must be a finite numeric array") from error
    if values.shape != mask.shape or values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("decision_field must be finite and match the mask shape")
    if np.any(values[mask] < 0.0) or np.any(values[~mask] > 0.0):
        raise ValueError(
            "decision_field must be nonnegative inside and nonpositive outside the mask"
        )
    return np.array(values, dtype=float, copy=True)


def _bilinear(values: np.ndarray, xy: np.ndarray) -> float | None:
    x, y = map(float, xy)
    height, width = values.shape
    if x < 0.0 or y < 0.0 or x > width - 1 or y > height - 1:
        return None
    x0, y0 = floor(x), floor(y)
    x1, y1 = min(x0 + 1, width - 1), min(y0 + 1, height - 1)
    tx, ty = x - x0, y - y0
    top = values[y0, x0] * (1.0 - tx) + values[y0, x1] * tx
    bottom = values[y1, x0] * (1.0 - tx) + values[y1, x1] * tx
    return float(top * (1.0 - ty) + bottom * ty)


def _cumulative_length(points: np.ndarray) -> np.ndarray:
    if len(points) < 2:
        return np.zeros(len(points), dtype=float)
    return np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-12:
        return np.array((1.0, 0.0))
    return vector / norm


def _local_tangents(points: np.ndarray, window_px: float) -> np.ndarray:
    distances = _cumulative_length(points)
    tangents = np.empty_like(points, dtype=float)
    total_length = distances[-1]
    for index in range(len(points)):
        start_distance = max(0.0, distances[index] - window_px / 2.0)
        end_distance = min(total_length, distances[index] + window_px / 2.0)
        if distances[index] < window_px / 2.0:
            end_distance = min(total_length, window_px)
        elif total_length - distances[index] < window_px / 2.0:
            start_distance = max(0.0, total_length - window_px)
        low = int(np.searchsorted(distances, start_distance, side="left"))
        high = int(np.searchsorted(distances, end_distance, side="right"))
        if high - low < 2:
            low = max(0, min(index - 1, len(points) - 2))
            high = min(len(points), low + 2)
        local = points[low:high]
        centered = local - local.mean(axis=0)
        covariance = centered.T @ centered
        _, vectors = np.linalg.eigh(covariance)
        tangent = _unit(vectors[:, -1])
        if float(np.dot(tangent, points[high - 1] - points[low])) < 0.0:
            tangent = -tangent
        tangents[index] = tangent
    return tangents


def _locate_boundary(
    field: np.ndarray,
    center: np.ndarray,
    normal: np.ndarray,
    direction: float,
    center_value: float,
    max_search: float,
    options: SubpixelCenterlineOptions,
    budget: _WorkBudget,
) -> tuple[float | None, float, int, int]:
    step = options.normal_sample_step_px
    steps = max(1, ceil(max_search / step))
    if steps > options.max_normal_probes - budget.probes:
        raise SubpixelReconstructionLimitError(
            "max_normal_probes", options.max_normal_probes, budget.probes + steps
        )
    previous_value = center_value
    previous_distance = 0.0
    crossing: float | None = None
    gradient = 0.0
    crossing_count = 0
    probes = 0
    for step_index in range(1, steps + 1):
        distance = min(step_index * step, max_search)
        value = _bilinear(field, center + direction * distance * normal)
        probes += 1
        if value is None:
            break
        if previous_value > 0.0 and value <= 0.0:
            crossing_count += 1
            if crossing is None:
                fraction = previous_value / (previous_value - value)
                crossing = previous_distance + fraction * (distance - previous_distance)
                gradient = abs(value - previous_value) / (distance - previous_distance)
        elif previous_value <= 0.0 and value > 0.0:
            crossing_count += 1
        previous_value = value
        previous_distance = distance
        if distance >= max_search:
            break
    budget.add_probes(probes)
    return crossing, gradient, crossing_count, probes


def _cross_section(
    point: np.ndarray,
    tangent: np.ndarray,
    field: np.ndarray,
    radius_map: np.ndarray,
    options: SubpixelCenterlineOptions,
    budget: _WorkBudget,
) -> tuple[np.ndarray | None, float, float, str | None, int]:
    center_value = _bilinear(field, point)
    if center_value is None or center_value <= 0.0:
        return None, 0.0, 0.0, "center_not_inside", 0
    expected_radius = _bilinear(radius_map, point)
    expected_radius = max(0.5, expected_radius or 0.0)
    max_search = options.max_normal_search_px
    if max_search is None:
        max_search = min(32.0, max(2.0, 3.0 * expected_radius + 1.0))
    normal = np.array((-tangent[1], tangent[0]))
    plus, plus_gradient, plus_count, plus_probes = _locate_boundary(
        field, point, normal, 1.0, center_value, max_search, options, budget
    )
    minus, minus_gradient, minus_count, minus_probes = _locate_boundary(
        field, point, normal, -1.0, center_value, max_search, options, budget
    )
    probes = plus_probes + minus_probes
    if plus_count > 1 or minus_count > 1:
        return None, expected_radius, 0.0, "multiple_crossings", probes
    if plus is None or minus is None:
        reason = "missing_positive_crossing" if plus is None else "missing_negative_crossing"
        return None, expected_radius, 0.0, reason, probes
    if min(plus_gradient, minus_gradient) < options.min_boundary_gradient:
        return None, expected_radius, 0.0, "weak_boundary_gradient", probes
    radius = 0.5 * (plus + minus)
    ratio = radius / expected_radius
    if ratio < 0.2 or ratio > 3.5:
        return None, expected_radius, 0.0, "radius_disagreement", probes
    gradient_score = min(
        1.0,
        min(plus_gradient, minus_gradient) / max(0.25, 4.0 * options.min_boundary_gradient),
    )
    radius_score = float(np.exp(-abs(np.log(max(ratio, 1e-12)))))
    confidence = gradient_score * radius_score
    candidate = point + 0.5 * (plus - minus) * normal
    if confidence < options.min_sample_confidence:
        return None, expected_radius, confidence, "low_sample_confidence", probes
    return candidate, radius, confidence, None, probes


def _observe_edge(
    points: np.ndarray,
    tangents: np.ndarray,
    edge: SkeletonEdge,
    analysis: SkeletonAnalysis,
    field: np.ndarray,
    options: SubpixelCenterlineOptions,
    budget: _WorkBudget,
) -> _Observations:
    observations = _Observations(points)
    distances = _cumulative_length(points)
    edge_length = float(distances[-1]) if len(distances) else 0.0
    node_by_id = {node.id: node for node in analysis.graph.nodes}
    region_by_node = {region.node_id: region for region in analysis.junction_regions}
    start_region = region_by_node.get(edge.a)
    end_region = region_by_node.get(edge.b)
    start_support = set(start_region.support_pixels) if start_region is not None else set()
    end_support = set(end_region.support_pixels) if end_region is not None else set()
    start_junction = start_region is not None or node_by_id[edge.a].degree > 2
    end_junction = end_region is not None or node_by_id[edge.b].degree > 2

    def guard_for(region) -> float:
        if region is None:
            radius_guard = 0.0
        else:
            radius_guard = options.junction_guard_radius_factor * region.radius_px
        requested = max(options.junction_guard_px, radius_guard)
        return min(requested, options.junction_guard_max_edge_fraction * edge_length)

    start_guard = guard_for(start_region) if start_junction else 0.0
    end_guard = guard_for(end_region) if end_junction else 0.0
    for index, point in enumerate(points):
        pixel = (int(np.rint(point[1])), int(np.rint(point[0])))
        if pixel in start_support or pixel in end_support:
            observations.reject(index, "junction_guard")
            continue
        if start_junction and distances[index] < start_guard:
            observations.reject(index, "junction_guard")
            continue
        if end_junction and edge_length - distances[index] < end_guard:
            observations.reject(index, "junction_guard")
            continue
        candidate, radius, confidence, reason, probes = _cross_section(
            point, tangents[index], field, analysis.radius, options, budget
        )
        observations.probes += probes
        if reason is not None:
            observations.reject(index, reason)
            continue
        assert candidate is not None
        observations.centers[index] = candidate
        observations.radii[index] = radius
        observations.confidence[index] = confidence
        observations.valid[index] = True
    valid_indices = np.flatnonzero(observations.valid)
    for index in valid_indices:
        neighbors = valid_indices[np.abs(valid_indices - index) <= 2]
        if len(neighbors) > 1:
            local = observations.radii[neighbors]
            ratio = float(np.max(local) / max(np.min(local), 1e-6))
            if ratio > 2.5:
                observations.confidence[index] *= 0.35
                if observations.confidence[index] < options.min_sample_confidence:
                    observations.reject(index, "radius_discontinuity")
    return observations



def _nearest_valid(observations: _Observations, from_start: bool) -> int | None:
    indices = np.flatnonzero(observations.valid)
    if not len(indices):
        return None
    return int(indices[0] if from_start else indices[-1])


def _reject_high_curvature(
    observations: _Observations,
    curvature: np.ndarray,
    max_curvature_radius: float,
) -> None:
    for index in np.flatnonzero(observations.valid):
        if abs(curvature[index]) * observations.radii[index] > max_curvature_radius:
            observations.reject(int(index), "high_curvature_radius")


def _refined_nodes(
    analysis: SkeletonAnalysis,
    observations_by_edge: dict[int, _Observations],
    tangents_by_edge: dict[int, np.ndarray],
    endpoint_guard_px: float,
) -> tuple[dict[int, tuple[float, float]], dict[int, float], dict[int, float]]:
    graph = analysis.graph
    node_xy: dict[int, tuple[float, float]] = {}
    node_confidence: dict[int, float] = {}
    node_radius: dict[int, float] = {}
    for node in graph.nodes:
        raw = np.asarray(node.xy, dtype=float)
        candidates: list[tuple[np.ndarray, float, float, float]] = []
        for edge_id, edge in enumerate(graph.edges):
            if edge.a == node.id and edge.b == node.id:
                continue
            if edge.a != node.id and edge.b != node.id:
                continue
            from_start = edge.a == node.id
            observations = observations_by_edge[edge_id]
            distances = _cumulative_length(edge.xy)
            index = _nearest_valid(observations, from_start)
            if index is None:
                continue
            if node.degree == 1:
                valid_indices = np.flatnonzero(observations.valid)
                endpoint_distances = (
                    distances[valid_indices]
                    if from_start
                    else distances[-1] - distances[valid_indices]
                )
                away_from_cap = valid_indices[endpoint_distances >= endpoint_guard_px]
                if len(away_from_cap):
                    index = int(away_from_cap[0] if from_start else away_from_cap[-1])
            candidate = observations.centers[index]
            confidence = float(observations.confidence[index])
            radius = float(observations.radii[index])
            if node.degree == 1:
                edge_tangent = tangents_by_edge[edge_id][index]
                normal = np.array((-edge_tangent[1], edge_tangent[0]))
                signed_distance = (
                    -distances[index] if from_start else distances[-1] - distances[index]
                )
                predicted_node = candidate + signed_distance * edge_tangent
                shift = predicted_node - raw
                prediction = raw + float(np.dot(shift, normal)) * normal
                distance = abs(float(signed_distance))
            elif node.degree > 2:
                tangent = tangents_by_edge[edge_id][index]
                signed_distance = (
                    -distances[index] if from_start else distances[-1] - distances[index]
                )
                prediction = candidate + signed_distance * tangent
                distance = abs(float(signed_distance))
            else:
                continue
            candidates.append((prediction, confidence / (1.0 + distance), confidence, radius))
        if candidates:
            weights = np.asarray([candidate[1] for candidate in candidates], dtype=float)
            predicted = np.asarray([candidate[0] for candidate in candidates], dtype=float)
            position = np.average(predicted, axis=0, weights=weights)
            max_shift = max(0.75, min(3.0, max(node.radius_px, 0.75)))
            delta = position - raw
            norm = float(np.linalg.norm(delta))
            if norm > max_shift:
                position = raw + delta * (max_shift / norm)
            confidence = float(
                np.average([candidate[2] for candidate in candidates], weights=weights)
            )
            radii = [candidate[3] for candidate in candidates if candidate[3] > 0.0]
            radius = float(np.average(radii)) if radii else node.radius_px
        else:
            position = raw
            confidence = 0.0 if node.degree == 0 else 0.25
            radius = node.radius_px
        node_xy[node.id] = (float(position[0]), float(position[1]))
        node_confidence[node.id] = confidence
        node_radius[node.id] = radius
    return node_xy, node_confidence, node_radius


def _default_spline_options():
    try:
        from planarcurve.fitting import PolylineSplineFitOptions
    except ImportError as error:  # pragma: no cover - depends on optional installation
        raise ImportError(
            "subpixel spline fitting requires PlanarCurve's fitting extra and SciPy"
        ) from error
    return PolylineSplineFitOptions(
        min_control_points=4,
        max_control_points=12,
        candidate_control_counts=(4, 6, 8, 10, 12),
        target_rms_error_fraction=0.004,
        target_p95_error_fraction=0.008,
    )


def _locked_spline_options(options: SubpixelCenterlineOptions):
    try:
        from planarcurve.fitting import PolylineSplineFitOptions, SplineEndpointPolicy
    except ImportError as error:  # pragma: no cover - depends on optional installation
        raise ImportError(
            "subpixel spline fitting requires PlanarCurve's fitting extra and SciPy"
        ) from error
    spline_options = options.spline_options or _default_spline_options()
    if not isinstance(spline_options, PolylineSplineFitOptions):
        raise TypeError("spline_options must be a PolylineSplineFitOptions value")
    if spline_options.max_control_points > 16:
        raise ValueError("spline_options.max_control_points must not exceed 16")
    if (
        spline_options.candidate_control_counts is not None
        and len(spline_options.candidate_control_counts) > 9
    ):
        raise ValueError("spline_options may test at most nine control counts")
    return replace(
        spline_options,
        endpoint_policy=SplineEndpointPolicy(start="locked", end="locked"),
    )


def _fit_one(
    points: np.ndarray,
    confidence: np.ndarray,
    start: tuple[float, float],
    end: tuple[float, float],
    spline_options,
):
    from planarcurve.fitting import fit_polyline_spline

    fit_points = np.array(points, dtype=float, copy=True)
    fit_points[0] = start
    fit_points[-1] = end
    weights = np.maximum(np.asarray(confidence, dtype=float), 0.01)
    try:
        return fit_polyline_spline(fit_points, weights=weights, options=spline_options)
    except (ValueError, np.linalg.LinAlgError) as error:
        raise SubpixelReconstructionError(
            f"PlanarCurve could not fit an edge segment: {error}"
        ) from error


def _fit_and_sample_segment(
    points: np.ndarray,
    radii: np.ndarray,
    confidence: np.ndarray,
    start: tuple[float, float],
    end: tuple[float, float],
    spline_options,
    options: SubpixelCenterlineOptions,
    budget: _WorkBudget,
):
    from planarcurve.polyline import normalized_arclength

    fit_points = np.array(points, dtype=float, copy=True)
    fit_points[0], fit_points[-1] = start, end
    fit = _fit_one(fit_points, confidence, start, end, spline_options)
    curve = fit.curve
    dense_count = max(64, min(2048, len(curve.control_points) * 32))
    dense = curve.sample_by_arclength(dense_count)
    length = float(np.linalg.norm(np.diff(dense.xy, axis=0), axis=1).sum())
    count = max(2, ceil(length / options.output_spacing_px) + 1)
    budget.add_samples(count)
    sampled = curve.sample_by_arclength(count)
    observation_parameters = normalized_arclength(fit_points)
    sample_radii = np.interp(sampled.u, observation_parameters, radii)
    sample_confidence = np.interp(sampled.u, observation_parameters, confidence)
    residual_scale = fit.diagnostics.normalized_scale
    residual_median = fit.diagnostics.residual_median * residual_scale
    residual_p95 = fit.diagnostics.residual_p95 * residual_scale
    return (
        curve,
        sampled.xy,
        sampled.tangent,
        sampled.curvature,
        sample_radii,
        sample_confidence,
        length,
        residual_median,
        residual_p95,
        fit.diagnostics.control_count,
    )


def _fit_edge(
    edge: SkeletonEdge,
    points: np.ndarray,
    observations: _Observations,
    node_xy: dict[int, tuple[float, float]],
    spline_options,
    options: SubpixelCenterlineOptions,
    budget: _WorkBudget,
):
    if edge.a != edge.b:
        result = _fit_and_sample_segment(
            points,
            observations.radii,
            observations.confidence,
            node_xy[edge.a],
            node_xy[edge.b],
            spline_options,
            options,
            budget,
        )
        curve, xy, tangent, curvature, radius, confidence, length, median, p95, controls = result
        return (curve,), xy, tangent, curvature, radius, confidence, length, median, p95, controls

    distances = _cumulative_length(points)
    if len(points) < 3 or distances[-1] <= 0.0:
        raise SubpixelReconstructionError(
            "a closed graph edge needs at least three distinct samples"
        )
    split_index = int(np.argmin(np.abs(distances - 0.5 * distances[-1])))
    split_index = min(max(split_index, 1), len(points) - 2)
    split = tuple(map(float, points[split_index]))
    first = _fit_and_sample_segment(
        points[: split_index + 1],
        observations.radii[: split_index + 1],
        observations.confidence[: split_index + 1],
        node_xy[edge.a],
        split,
        spline_options,
        options,
        budget,
    )
    second = _fit_and_sample_segment(
        points[split_index:],
        observations.radii[split_index:],
        observations.confidence[split_index:],
        split,
        node_xy[edge.a],
        spline_options,
        options,
        budget,
    )
    curves = (first[0], second[0])
    arrays = [np.concatenate((first[index], second[index][1:]), axis=0) for index in range(1, 6)]
    length = first[6] + second[6]
    median = float(np.average((first[7], second[7]), weights=(first[6], second[6])))
    p95 = max(first[8], second[8])
    controls = first[9] + second[9]
    return curves, *arrays, length, median, p95, controls


def _merge_reasons(target: dict[str, int], source: dict[str, int]) -> None:
    for reason, count in source.items():
        target[reason] = target.get(reason, 0) + count


def refine_graph_geometry(
    analysis: SkeletonAnalysis,
    *,
    decision_field: ArrayLike | None = None,
    options: SubpixelCenterlineOptions | None = None,
) -> RefinedSkeletonGeometry:
    """Refine graph edges to subpixel geometry without modifying discrete topology.

    ``decision_field`` is a finite signed field sampled at pixel centers, with
    nonnegative values inside the mask and nonpositive values outside. When it is
    omitted, a signed Euclidean distance transform is constructed from the mask.
    """
    if not isinstance(analysis, SkeletonAnalysis):
        raise TypeError("analysis must be a SkeletonAnalysis")
    if options is None:
        options = SubpixelCenterlineOptions()
    if not isinstance(options, SubpixelCenterlineOptions):
        raise TypeError("options must be SubpixelCenterlineOptions")
    source: Literal["decision-field", "binary-distance-fallback"]
    if decision_field is None:
        field = _binary_signed_distance(analysis.mask)
        source = "binary-distance-fallback"
    else:
        field = _validate_decision_field(decision_field, analysis.mask)
        source = "decision-field"

    graph = analysis.graph
    budget = _WorkBudget(options)
    budget.add_samples(sum(len(edge.xy) for edge in graph.edges))
    raw_observations: dict[int, _Observations] = {}
    raw_tangents: dict[int, np.ndarray] = {}
    all_reasons: dict[int, dict[str, int]] = {}
    probe_counts = {edge_id: 0 for edge_id in range(len(graph.edges))}
    for edge_id, edge in enumerate(graph.edges):
        tangents = _local_tangents(edge.xy, options.tangent_window_px)
        observations = _observe_edge(edge.xy, tangents, edge, analysis, field, options, budget)
        raw_observations[edge_id] = observations
        raw_tangents[edge_id] = tangents
        all_reasons[edge_id] = dict(observations.reasons)
        probe_counts[edge_id] += observations.probes

    node_xy, node_confidence, node_radius = _refined_nodes(
        analysis,
        raw_observations,
        raw_tangents,
        options.tangent_window_px / 2.0,
    )
    spline_options = _locked_spline_options(options) if graph.edges else None
    current_points = {edge_id: edge.xy for edge_id, edge in enumerate(graph.edges)}
    current_tangents = raw_tangents
    current_curvatures: dict[int, np.ndarray] = {}
    final_data = {}
    initial_residuals: dict[int, float] = {}
    for pass_index in range(options.refinement_passes):
        next_points: dict[int, np.ndarray] = {}
        next_curvatures: dict[int, np.ndarray] = {}
        next_tangents: dict[int, np.ndarray] = {}
        for edge_id, edge in enumerate(graph.edges):
            if pass_index == 0:
                observations = raw_observations[edge_id]
            else:
                observations = _observe_edge(
                    current_points[edge_id],
                    current_tangents[edge_id],
                    edge,
                    analysis,
                    field,
                    options,
                    budget,
                )
                _reject_high_curvature(
                    observations,
                    current_curvatures[edge_id],
                    options.max_curvature_radius,
                )
                _merge_reasons(all_reasons[edge_id], observations.reasons)
                probe_counts[edge_id] += observations.probes
            (
                curves,
                xy,
                tangent,
                curvature,
                radius,
                confidence,
                length,
                median,
                p95,
                controls,
            ) = _fit_edge(
                edge,
                observations.centers,
                observations,
                node_xy,
                spline_options,
                options,
                budget,
            )
            if pass_index == 0:
                initial_residuals[edge_id] = p95
            next_points[edge_id] = xy
            next_tangents[edge_id] = tangent
            next_curvatures[edge_id] = curvature
            final_data[edge_id] = (
                curves,
                xy,
                tangent,
                curvature,
                radius,
                confidence,
                length,
                median,
                p95,
                controls,
                observations,
            )
        current_points = next_points
        current_tangents = next_tangents
        current_curvatures = next_curvatures

    refined_edges = []
    for edge_id, edge in enumerate(graph.edges):
        (
            curves,
            xy,
            tangent,
            curvature,
            radius,
            confidence,
            length,
            median_residual,
            p95_residual,
            controls,
            final_observations,
        ) = final_data[edge_id]
        xy = np.array(xy, dtype=float, copy=True)
        xy[0] = node_xy[edge.a]
        xy[-1] = node_xy[edge.b]
        confidence = np.array(confidence, dtype=float, copy=True)
        radius = np.array(radius, dtype=float, copy=True)
        confidence[0] = node_confidence[edge.a]
        confidence[-1] = node_confidence[edge.b]
        radius[0] = node_radius[edge.a]
        radius[-1] = node_radius[edge.b]
        if edge.a == edge.b and len(confidence) > 2:
            raw_distances = _cumulative_length(edge.xy)
            raw_split = int(np.argmin(np.abs(raw_distances - 0.5 * edge.length_px)))
            split_point = edge.xy[raw_split]
            split_index = int(np.argmin(np.linalg.norm(xy - split_point, axis=1)))
            split_index = min(max(split_index, 1), len(confidence) - 2)
            if float(np.dot(tangent[split_index - 1], tangent[split_index + 1])) < 0.85:
                confidence[split_index] *= 0.25
                all_reasons[edge_id]["loop_split_tangent_discontinuity"] = 1
        curvature_radius = np.abs(curvature) * radius
        initial_count = int(raw_observations[edge_id].valid.sum())
        diagnostics = RefinedEdgeDiagnostics(
            raw_point_count=len(edge.xy),
            valid_cross_section_count=initial_count,
            invalid_reason_counts=all_reasons[edge_id],
            median_shift_px=float(
                np.median(np.linalg.norm(raw_observations[edge_id].centers - edge.xy, axis=1))
            ),
            p95_shift_px=float(
                np.percentile(
                    np.linalg.norm(raw_observations[edge_id].centers - edge.xy, axis=1),
                    95,
                )
            ),
            median_spline_residual_px=median_residual,
            p95_spline_residual_px=p95_residual,
            selected_control_count=controls,
            first_pass_improvement_px=initial_residuals[edge_id] - p95_residual,
            junction_guard_sample_count=sum(
                count
                for reason, count in all_reasons[edge_id].items()
                if reason == "junction_guard"
            ),
            max_abs_curvature_radius=float(np.max(curvature_radius, initial=0.0)),
            normal_probe_count=probe_counts[edge_id],
            spline_fit_count=len(curves) * options.refinement_passes,
        )
        refined_edges.append(
            RefinedEdgeGeometry(
                edge_id=edge_id,
                xy=xy,
                tangent=tangent,
                curvature=curvature,
                radius_px=radius,
                confidence=confidence,
                length_px=length,
                source=source,
                diagnostics=diagnostics,
                curve_segments=curves,
            )
        )

    return RefinedSkeletonGeometry(
        analysis=analysis,
        edges=tuple(refined_edges),
        node_xy=node_xy,
        node_confidence=node_confidence,
        node_radius_px=node_radius,
        diagnostics={
            "source": source,
            "normal_probe_count": budget.probes,
            "refinement_sample_count": budget.samples,
            "spline_fit_count": sum(edge.diagnostics.spline_fit_count for edge in refined_edges),
        },
    )


_MAX_WALK_SAMPLES = 1_000_000


def _resample_edge(
    edge: RefinedEdgeGeometry, sample_count: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    distances = _cumulative_length(edge.xy)
    if distances[-1] <= 0.0:
        raise SubpixelReconstructionError("a refined edge must have positive sampled length")
    target = np.linspace(0.0, distances[-1], sample_count)
    xy = np.column_stack([np.interp(target, distances, edge.xy[:, axis]) for axis in range(2)])
    tangent = np.column_stack(
        [np.interp(target, distances, edge.tangent[:, axis]) for axis in range(2)]
    )
    tangent_norm = np.linalg.norm(tangent, axis=1)
    valid = tangent_norm > 1e-12
    tangent[valid] /= tangent_norm[valid, None]
    tangent[~valid] = (1.0, 0.0)
    curvature = np.interp(target, distances, edge.curvature)
    radius = np.interp(target, distances, edge.radius_px)
    confidence = np.interp(target, distances, edge.confidence)
    return xy, tangent, curvature, radius, confidence


def refined_walk(
    graph_geometry: RefinedSkeletonGeometry,
    walk: SkeletonWalk,
    *,
    sample_count: int | None = None,
) -> RefinedWalkGeometry:
    """Assemble continuous geometry from the exact edge sequence of ``walk``.

    Each edge is reused from ``graph_geometry``. Reverse traversals reverse the
    samples, negate tangent and signed curvature, and repeated traversals never
    trigger another fit. When ``sample_count`` is supplied, each edge traversal
    is independently resampled to that many points before shared nodes are joined.
    """
    if not isinstance(graph_geometry, RefinedSkeletonGeometry):
        raise TypeError("graph_geometry must be a RefinedSkeletonGeometry")
    if not isinstance(walk, SkeletonWalk):
        raise TypeError("walk must be a SkeletonWalk")
    walk._validate_graph(graph_geometry.graph)

    if sample_count is not None:
        if (
            isinstance(sample_count, bool)
            or not isinstance(sample_count, (int, np.integer))
            or sample_count < 2
        ):
            raise ValueError("sample_count must be an integer of at least two")
        if (
            any(
                graph_geometry.graph.edges[edge_id].a == graph_geometry.graph.edges[edge_id].b
                for edge_id in walk.edge_ids
            )
            and sample_count < 3
        ):
            raise ValueError("closed-edge traversals require sample_count of at least three")
        sample_count = int(sample_count)
        requested = sample_count * len(walk.edge_ids)
        if requested > _MAX_WALK_SAMPLES:
            raise SubpixelReconstructionLimitError("max_walk_samples", _MAX_WALK_SAMPLES, requested)

    if not walk.edge_ids:
        if walk.start_node is None:
            empty_xy = np.empty((0, 2), dtype=float)
            return RefinedWalkGeometry(
                xy=empty_xy,
                tangent=empty_xy,
                curvature=np.empty(0),
                radius_px=np.empty(0),
                confidence=np.empty(0),
                length_px=0.0,
                edge_ids=(),
                edge_directions=(),
            )
        point = np.asarray([graph_geometry.node_xy[walk.start_node]], dtype=float)
        return RefinedWalkGeometry(
            xy=point,
            tangent=np.zeros((1, 2), dtype=float),
            curvature=np.zeros(1),
            radius_px=np.asarray([graph_geometry.node_radius_px[walk.start_node]]),
            confidence=np.asarray([graph_geometry.node_confidence[walk.start_node]]),
            length_px=0.0,
            edge_ids=(),
            edge_directions=(),
        )

    graph = graph_geometry.graph
    edge_lookup = graph_geometry.edge_by_id
    pieces: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
    current_node = walk.start_node
    total_length = 0.0
    total_samples = 0
    for edge_id, direction in zip(walk.edge_ids, walk.edge_directions, strict=True):
        edge = graph.edges[edge_id]
        refined = edge_lookup[edge_id]
        if direction == "forward":
            entry, exit_node = edge.a, edge.b
            arrays = (
                refined.xy,
                refined.tangent,
                refined.curvature,
                refined.radius_px,
                refined.confidence,
            )
        else:
            entry, exit_node = edge.b, edge.a
            arrays = (
                refined.xy[::-1],
                -refined.tangent[::-1],
                -refined.curvature[::-1],
                refined.radius_px[::-1],
                refined.confidence[::-1],
            )
        if entry != current_node:
            raise ValueError("walk edge direction does not continue from the current node")
        if sample_count is not None:
            arrays = _resample_edge(refined, sample_count)
            if direction == "reverse":
                arrays = (
                    arrays[0][::-1],
                    -arrays[1][::-1],
                    -arrays[2][::-1],
                    arrays[3][::-1],
                    arrays[4][::-1],
                )
        arrays = tuple(np.array(values, dtype=float, copy=True) for values in arrays)
        arrays[0][0] = graph_geometry.node_xy[entry]
        arrays[0][-1] = graph_geometry.node_xy[exit_node]
        if pieces:
            previous_end = pieces[-1][0][-1]
            if not np.allclose(previous_end, arrays[0][0], rtol=0.0, atol=1e-8):
                raise SubpixelReconstructionError(
                    f"refined edges do not meet at graph node {entry}"
                )
        total_samples += len(arrays[0])
        if total_samples > _MAX_WALK_SAMPLES:
            raise SubpixelReconstructionLimitError(
                "max_walk_samples", _MAX_WALK_SAMPLES, total_samples
            )
        pieces.append(arrays)
        total_length += refined.length_px
        current_node = exit_node

    joined = tuple(np.concatenate([piece[axis] for piece in pieces], axis=0) for axis in range(5))
    return RefinedWalkGeometry(
        xy=joined[0],
        tangent=joined[1],
        curvature=joined[2],
        radius_px=joined[3],
        confidence=joined[4],
        length_px=total_length,
        edge_ids=walk.edge_ids,
        edge_directions=walk.edge_directions,
    )
