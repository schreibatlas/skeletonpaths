import warnings
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike
from planarcurve.polyline import (
    mean_squared_turn_angle,
    polyline_length,
    symmetric_polyline_distance,
)

from .model import (
    DEFAULT_RANKING_POLICY,
    NoFeasiblePathError,
    PathRankingPolicy,
    PathScore,
    PathSearchLimitError,
    PathSearchLimits,
    PathSelection,
    Point,
    SkeletonGraph,
    SkeletonPath,
    TopologyPathInventory,
    TopologyRoute,
    _resolve_search_limits,
)
from .routing import _edge_route, _loop_paths, _open_paths


@dataclass(frozen=True)
class _ScoredRoute:
    route: TopologyRoute
    length_px: float
    score: PathScore


def _score_landscapes_overlap(
    first: PathScore, second: PathScore, policy: PathRankingPolicy
) -> bool:
    for first_value, second_value, tolerance in (
        (
            first.guide_distance_px,
            second.guide_distance_px,
            policy.ambiguity_guide_distance_px,
        ),
        (
            first.endpoint_order_error_px,
            second.endpoint_order_error_px,
            policy.ambiguity_endpoint_order_px,
        ),
        (first.length_error_px, second.length_error_px, policy.ambiguity_length_error_px),
    ):
        if (
            first_value is not None
            and second_value is not None
            and abs(first_value - second_value) > tolerance
        ):
            return False
    if abs(first.measured_confidence - second.measured_confidence) > policy.ambiguity_confidence:
        return False
    return not (
        policy.turning_cost_is_evidence
        and first.turning_cost is not None
        and second.turning_cost is not None
        and abs(first.turning_cost - second.turning_cost) > policy.ambiguity_turning_cost
    )


def _rank_candidates(
    graph: SkeletonGraph,
    *,
    path_kind: Literal["open", "loop", "open-with-loop"] = "open",
    expected_cycles: int | None = None,
    expected_endpoints: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    expected_length_px: float | None = None,
    candidate_xy: ArrayLike | None = None,
    path_inventory: TopologyPathInventory | None = None,
    policy: PathRankingPolicy = DEFAULT_RANKING_POLICY,
    limits: PathSearchLimits | None = None,
    max_paths: int | None = None,
) -> tuple[_ScoredRoute, ...]:
    """Rank feasible routes by candidate geometry, confidence, and later tie-breakers.

    Feasibility constraints are applied before scoring. With a candidate curve,
    symmetric guide distance is primary, endpoint orientation breaks geometric
    ties, and measured confidence is secondary. Expected length, sampled turning
    cost, and edge IDs provide deterministic later tie-breakers.
    """
    if path_kind not in {"open", "loop", "open-with-loop"}:
        raise ValueError(f"unsupported path kind: {path_kind}")
    if not isinstance(policy, PathRankingPolicy):
        raise TypeError("policy must be a PathRankingPolicy")
    if path_inventory is not None and path_inventory.graph is not graph:
        raise ValueError("topology path inventory belongs to a different skeleton graph")
    if expected_cycles is not None and (
        isinstance(expected_cycles, bool)
        or not isinstance(expected_cycles, (int, np.integer))
        or expected_cycles < 0
    ):
        raise ValueError("expected cycle count must be a nonnegative integer")
    if not np.isfinite(endpoint_tolerance_px) or endpoint_tolerance_px < 0.0:
        raise ValueError("endpoint tolerance must be finite and nonnegative")
    if expected_length_px is not None and (
        not np.isfinite(expected_length_px) or expected_length_px <= 0.0
    ):
        raise ValueError("expected path length must be positive and finite")
    candidate = None if candidate_xy is None else np.asarray(candidate_xy, dtype=float)
    if candidate is not None:
        if candidate.ndim != 2 or candidate.shape[1] != 2 or len(candidate) < 2:
            raise ValueError("candidate curve must contain at least two finite xy points")
        if not np.isfinite(candidate).all() or polyline_length(candidate) <= 1e-12:
            raise ValueError("candidate curve must contain at least two distinct finite xy points")

    limits = _resolve_search_limits(limits, max_paths)
    if path_inventory is not None:
        if path_kind not in path_inventory.paths_by_kind:
            raise ValueError(f"path inventory does not include {path_kind!r} routes")
        candidates = path_inventory.paths_by_kind[path_kind]
        if len(candidates) > limits.max_paths:
            raise PathSearchLimitError(
                path_kind,
                "max_paths",
                limits.max_paths,
                len(candidates),
            )
    elif path_kind == "loop":
        candidates = _loop_paths(graph, limits=limits)
    else:
        candidates = _open_paths(graph, path_kind, limits=limits)
    if expected_endpoints is None:
        start_expected, end_expected = None, None
    else:
        if len(expected_endpoints) != 2:
            raise ValueError("expected endpoints must contain two xy pairs or None")
        start_expected, end_expected = expected_endpoints
    expected_points: list[np.ndarray | None] = []
    for point in (start_expected, end_expected):
        if point is None:
            expected_points.append(None)
            continue
        value = np.asarray(point, dtype=float)
        if value.shape != (2,) or not np.isfinite(value).all():
            raise ValueError("expected endpoint coordinates must be finite xy pairs")
        expected_points.append(value)
    start_expected_xy, end_expected_xy = expected_points
    start_nodes = {node.id: np.asarray(node.xy) for node in graph.nodes}
    scored: list[_ScoredRoute] = []
    for route in candidates:
        edge_ids = route.edge_ids
        start = route.start_node
        end = route.end_node
        cycles = route.cycle_count
        if expected_cycles is not None and cycles != expected_cycles:
            continue
        if (
            start_expected_xy is not None
            and np.linalg.norm(start_nodes[start] - start_expected_xy) > endpoint_tolerance_px
        ):
            continue
        if (
            end_expected_xy is not None
            and np.linalg.norm(start_nodes[end] - end_expected_xy) > endpoint_tolerance_px
        ):
            continue
        xy, routed_end = _edge_route(graph, edge_ids, start)
        if routed_end != end:
            continue
        length = float(sum(graph.edges[edge_id].length_px for edge_id in edge_ids))
        confidence = float(
            np.average(
                [graph.edges[edge_id].confidence for edge_id in edge_ids],
                weights=[max(graph.edges[edge_id].length_px, 1e-12) for edge_id in edge_ids],
            )
        )
        guide_distance = (
            symmetric_polyline_distance(xy, candidate, samples=policy.guide_samples)
            if candidate is not None
            else None
        )
        orientation_error = (
            float(np.linalg.norm(xy[0] - candidate[0]) + np.linalg.norm(xy[-1] - candidate[-1]))
            if candidate is not None
            else None
        )
        score = PathScore(
            guide_distance_px=guide_distance,
            endpoint_order_error_px=orientation_error,
            measured_confidence=confidence,
            length_error_px=(
                abs(length - expected_length_px) if expected_length_px is not None else None
            ),
            turning_cost=mean_squared_turn_angle(xy, samples=policy.turning_samples),
        )
        scored.append(_ScoredRoute(route, length, score))

    def tie_break_key(
        item: _ScoredRoute,
    ) -> tuple[float, float, float, float, tuple[int, ...], int, int]:
        route = item.route
        score = item.score
        return (
            score.endpoint_order_error_px if score.endpoint_order_error_px is not None else 0.0,
            -score.measured_confidence,
            score.length_error_px if score.length_error_px is not None else 0.0,
            score.turning_cost if score.turning_cost is not None else 0.0,
            route.edge_ids,
            route.start_node,
            route.end_node,
        )

    if candidate is None:
        scored.sort(
            key=lambda item: (
                -item.score.measured_confidence,
                item.score.length_error_px if item.score.length_error_px is not None else 0.0,
                item.score.turning_cost if item.score.turning_cost is not None else 0.0,
                item.route.edge_ids,
                item.route.start_node,
                item.route.end_node,
            )
        )
    else:
        scored.sort(key=lambda item: item.score.guide_distance_px)
        ordered = []
        start_index = 0
        while start_index < len(scored):
            guide_distance = scored[start_index].score.guide_distance_px
            stop_index = start_index + 1
            while (
                stop_index < len(scored)
                and scored[stop_index].score.guide_distance_px - guide_distance
                <= policy.guide_tie_tolerance_px
            ):
                stop_index += 1
            group = scored[start_index:stop_index]
            group.sort(key=tie_break_key)
            ordered.extend(group)
            start_index = stop_index
        scored = ordered
    return tuple(scored)


def _materialize_path(graph: SkeletonGraph, scored: _ScoredRoute) -> SkeletonPath:
    route = scored.route
    xy, routed_end = _edge_route(graph, route.edge_ids, route.start_node)
    if routed_end != route.end_node:
        raise ValueError("route endpoints do not match its edge sequence")
    return SkeletonPath(
        xy=xy,
        edge_ids=route.edge_ids,
        start_node=route.start_node,
        end_node=route.end_node,
        length_px=scored.length_px,
        confidence=scored.score.measured_confidence,
        cycle_count=route.cycle_count,
        score=scored.score,
    )


def rank_paths(
    graph: SkeletonGraph,
    *,
    path_kind: Literal["open", "loop", "open-with-loop"] = "open",
    expected_cycles: int | None = None,
    expected_endpoints: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    expected_length_px: float | None = None,
    candidate_xy: ArrayLike | None = None,
    path_inventory: TopologyPathInventory | None = None,
    policy: PathRankingPolicy = DEFAULT_RANKING_POLICY,
    limits: PathSearchLimits | None = None,
    max_paths: int | None = None,
    limit: int | None = None,
) -> tuple[SkeletonPath, ...]:
    """Rank feasible topology routes and materialize ordered path geometries.

    Parameters
    ----------
    graph : SkeletonGraph
        Graph whose routes are searched or whose prepared inventory is ranked.
    path_kind : str
        Route kind to consider. ``"open"`` is endpoint-to-endpoint with zero
        route-level cycles; ``"loop"`` is a closed cycle; ``"open-with-loop"``
        is endpoint-to-endpoint with exactly one route-level cycle.
    expected_cycles : int or None
        Required cycle count of each route. This constrains routes, not the whole
        graph.
    expected_endpoints : tuple or None
        Ordered ``(start, end)`` coordinate expectations in ``(x, y)`` pixel
        units. Either endpoint may be ``None`` to leave it unconstrained.
    endpoint_tolerance_px : float
        Maximum distance in pixels from each specified expected endpoint. Must be
        finite and nonnegative.
    expected_length_px : float or None
        Positive finite expected route length in pixels. When provided, length
        error is ranking evidence; when omitted, shorter routes are not preferred.
    candidate_xy : numpy.typing.ArrayLike or None
        Optional guide polyline with shape ``(N, 2)``, at least two finite,
        distinct ``(x, y)`` points. It guides ranking but is not a feasibility
        constraint and does not imply physical direction.
    path_inventory : TopologyPathInventory or None
        Optional prepared routes. The inventory must belong to this exact graph
        object and include ``path_kind``.
    policy : PathRankingPolicy
        Sampling, tie, and ambiguity-evidence policy.
    limits : PathSearchLimits or None
        Route enumeration bounds. Limits apply independently to each route kind.
    max_paths : int or None
        Legacy maximum routes per kind. Mutually exclusive with ``limits``.
    limit : int or None
        Positive maximum number of returned ``SkeletonPath`` objects. All
        feasible candidates are still scored so ordering remains exact.

    Returns
    -------
    tuple of SkeletonPath
        Feasible routes in ranking order. Open routes may appear in both
        orientations. Returns an empty tuple when no route remains feasible.

    Raises
    ------
    ValueError
        If a route kind, constraint, guide, inventory, or result limit is invalid.
    TypeError
        If ``policy`` or ``limits`` has an invalid type.
    PathSearchLimitError
        If route enumeration exceeds a configured bound. No partial result is
        returned.

    Notes
    -----
    Feasibility filtering precedes ranking. With ``candidate_xy``, symmetric
    guide distance is primary; distances within ``guide_tie_tolerance_px`` are
    grouped by direct numeric tolerance, then endpoint-order error, measured
    confidence, expected-length error when present, turning cost, and deterministic
    route identity break ties. Without a guide, measured confidence is primary,
    followed by expected-length error when present, turning cost, and route
    identity. Turning cost is normally only a tie-breaker. ``limit`` controls
    materialized results, not route enumeration or scoring.

    See Also
    --------
    select_path : Select the leading route with ambiguity metadata.
    prepare_topology_paths : Prepare reusable route inventories.
    """
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, (int, np.integer)) or limit < 1:
            raise ValueError("limit must be a positive integer")
        limit = int(limit)

    scored = _rank_candidates(
        graph,
        path_kind=path_kind,
        expected_cycles=expected_cycles,
        expected_endpoints=expected_endpoints,
        endpoint_tolerance_px=endpoint_tolerance_px,
        expected_length_px=expected_length_px,
        candidate_xy=candidate_xy,
        path_inventory=path_inventory,
        policy=policy,
        limits=limits,
        max_paths=max_paths,
    )
    if limit is not None:
        scored = scored[:limit]
    return tuple(_materialize_path(graph, route) for route in scored)


def select_topology_path(*args, **kwargs) -> SkeletonPath:
    """Deprecated wrapper for :func:`select_path`, returning its ``SkeletonPath``.

    Emits ``DeprecationWarning``. Use ``select_path()`` to obtain the selected
    path together with ambiguity metadata.
    """
    warnings.warn(
        "select_topology_path is deprecated; use select_path instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return select_path(*args, **kwargs).path


def select_path(
    graph: SkeletonGraph,
    *,
    path_kind: Literal["open", "loop", "open-with-loop"] = "open",
    expected_cycles: int | None = None,
    expected_endpoints: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    expected_length_px: float | None = None,
    candidate_xy: ArrayLike | None = None,
    path_inventory: TopologyPathInventory | None = None,
    policy: PathRankingPolicy = DEFAULT_RANKING_POLICY,
    limits: PathSearchLimits | None = None,
    max_paths: int | None = None,
) -> PathSelection:
    """Select the highest-ranked feasible route and report selection ambiguity.

    Parameters
    ----------
    graph : SkeletonGraph
        Graph whose routes are searched or whose prepared inventory is selected.
    path_kind : str
        Route kind to consider. ``"open"`` is endpoint-to-endpoint with zero
        route-level cycles; ``"loop"`` is a closed cycle; ``"open-with-loop"``
        is endpoint-to-endpoint with exactly one route-level cycle.
    expected_cycles : int or None
        Required cycle count of each route. This constrains routes, not the whole
        graph.
    expected_endpoints : tuple or None
        Ordered ``(start, end)`` coordinate expectations in ``(x, y)`` pixel
        units. Either endpoint may be ``None`` to leave it unconstrained.
    endpoint_tolerance_px : float
        Maximum distance in pixels from each specified expected endpoint. Must be
        finite and nonnegative.
    expected_length_px : float or None
        Positive finite expected route length in pixels. When provided, length
        error is ranking evidence; when omitted, shorter routes are not preferred.
    candidate_xy : numpy.typing.ArrayLike or None
        Optional guide polyline with shape ``(N, 2)``, at least two finite,
        distinct ``(x, y)`` points. It guides ranking but is not a feasibility
        constraint and does not imply physical direction.
    path_inventory : TopologyPathInventory or None
        Optional prepared routes. The inventory must belong to this exact graph
        object and include ``path_kind``.
    policy : PathRankingPolicy
        Sampling, tie, and ambiguity-evidence policy.
    limits : PathSearchLimits or None
        Route enumeration bounds. Limits apply independently to each route kind.
    max_paths : int or None
        Legacy maximum routes per kind. Mutually exclusive with ``limits``.

    Returns
    -------
    PathSelection
        Selected ``path``, route and orientation ambiguity flags, and the count of
        feasible scored routes. Only the selected ``SkeletonPath`` is materialized.

    Raises
    ------
    NoFeasiblePathError
        If no route satisfies the requested kind and hard feasibility constraints.
    ValueError
        If a route kind, constraint, guide, or inventory is invalid.
    TypeError
        If ``policy`` or ``limits`` has an invalid type.
    PathSearchLimitError
        If route enumeration exceeds a configured bound. No partial result is
        returned.

    Notes
    -----
    Feasibility filtering precedes ranking, and all feasible alternatives are
    scored because they may affect ambiguity. ``ambiguous`` means another
    different edge route has overlapping score evidence. ``orientation_ambiguous``
    means the reversed orientation of the selected edge route remains
    indistinguishable within endpoint-order evidence. Neither flag changes
    measured confidence. Candidate geometry guides ranking and orientation; it
    does not establish physical direction. See ``rank_paths()`` for ranking order
    and parameter semantics.

    See Also
    --------
    rank_paths : Return ranked path objects instead of one selection.
    prepare_topology_paths : Prepare reusable route inventories.
    """
    scored = _rank_candidates(
        graph,
        path_kind=path_kind,
        expected_cycles=expected_cycles,
        expected_endpoints=expected_endpoints,
        endpoint_tolerance_px=endpoint_tolerance_px,
        expected_length_px=expected_length_px,
        candidate_xy=candidate_xy,
        path_inventory=path_inventory,
        policy=policy,
        limits=limits,
        max_paths=max_paths,
    )
    if not scored:
        raise NoFeasiblePathError(
            f"no path satisfies topology kind {path_kind!r}, expected cycle count "
            f"{expected_cycles!r}, and endpoint constraints"
        )

    selected_record = scored[0]
    selected = _materialize_path(graph, selected_record)
    selected_route = tuple(sorted(selected.edge_ids))
    ambiguous = any(
        tuple(sorted(record.route.edge_ids)) != selected_route
        and _score_landscapes_overlap(selected_record.score, record.score, policy)
        for record in scored[1:]
    )

    orientation_ambiguous = False
    for record in scored[1:]:
        route = record.route
        if tuple(sorted(route.edge_ids)) != selected_route:
            continue
        xy, routed_end = _edge_route(graph, route.edge_ids, route.start_node)
        if routed_end != selected.start_node or not np.allclose(xy, selected.xy[::-1]):
            continue
        if (
            selected_record.score.endpoint_order_error_px is None
            or record.score.endpoint_order_error_px is None
            or abs(
                selected_record.score.endpoint_order_error_px - record.score.endpoint_order_error_px
            )
            <= policy.ambiguity_endpoint_order_px
        ):
            orientation_ambiguous = True
            break

    return PathSelection(selected, ambiguous, orientation_ambiguous, len(scored))


def rank_topology_paths(*args, **kwargs) -> tuple[SkeletonPath, ...]:
    """Deprecated wrapper for :func:`rank_paths`, returning ranked path objects.

    Emits ``DeprecationWarning``. Use ``rank_paths()`` instead.
    """
    warnings.warn(
        "rank_topology_paths is deprecated; use rank_paths instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return rank_paths(*args, **kwargs)
