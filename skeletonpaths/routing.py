from typing import Literal

import numpy as np

from .model import (
    DEFAULT_SEARCH_LIMITS,
    PathSearchLimitError,
    PathSearchLimits,
    SkeletonEdge,
    SkeletonGraph,
    TopologyPathInventory,
    TopologyRoute,
    _resolve_search_limits,
)


def _other_node(edge: SkeletonEdge, node_id: int) -> int:
    return edge.b if edge.a == node_id else edge.a


def _edge_route(
    graph: SkeletonGraph, edge_ids: tuple[int, ...], start: int
) -> tuple[np.ndarray, int]:
    current = start
    points: list[np.ndarray] = []
    for edge_id in edge_ids:
        edge = graph.edges[edge_id]
        if edge.a == current:
            edge_points = edge.xy
        elif edge.b == current:
            edge_points = edge.xy[::-1]
        else:
            raise ValueError("edge sequence is not connected")
        points.extend(edge_points if not points else edge_points[1:])
        current = _other_node(edge, current)
    return np.asarray(points, dtype=float), current


def _next_expansion_count(
    path_kind: str,
    limits: PathSearchLimits,
    states_expanded: int,
) -> int:
    if states_expanded >= limits.max_states:
        raise PathSearchLimitError(
            path_kind,
            "max_states",
            limits.max_states,
            states_expanded + 1,
        )
    return states_expanded + 1


def _open_paths(
    graph: SkeletonGraph,
    path_kind: Literal["open", "open-with-loop"],
    *,
    limits: PathSearchLimits = DEFAULT_SEARCH_LIMITS,
) -> list[TopologyRoute]:
    incident: dict[int, list[int]] = {node.id: [] for node in graph.nodes}
    for edge_id, edge in enumerate(graph.edges):
        incident[edge.a].append(edge_id)
        if edge.b != edge.a:
            incident[edge.b].append(edge_id)
    endpoints = sorted(node.id for node in graph.nodes if node.degree == 1)
    paths: dict[tuple[tuple[int, ...], int], TopologyRoute] = {}
    allow_one_cycle = path_kind == "open-with-loop"
    states_expanded = 0

    for start in endpoints:
        stack = [(start, start, (), {start: 1}, 0)]
        while stack:
            current_start, current, used_edges, visits, cycle_count = stack.pop()
            states_expanded = _next_expansion_count(path_kind, limits, states_expanded)
            if current != current_start and current in endpoints:
                if (path_kind == "open" and cycle_count == 0) or (
                    allow_one_cycle and cycle_count == 1
                ):
                    key = (tuple(sorted(used_edges)), current_start)
                    if key not in paths:
                        if len(paths) >= limits.max_paths:
                            raise PathSearchLimitError(
                                path_kind,
                                "max_paths",
                                limits.max_paths,
                                len(paths) + 1,
                            )
                        paths[key] = TopologyRoute(used_edges, current_start, current, cycle_count)
                continue

            used = set(used_edges)
            for edge_id in sorted(incident[current], reverse=True):
                if edge_id in used:
                    continue
                next_node = _other_node(graph.edges[edge_id], current)
                next_visits = visits.get(next_node, 0)
                if next_visits >= 2:
                    continue
                added_cycle = int(next_visits > 0)
                if cycle_count + added_cycle > 1:
                    continue
                stack.append(
                    (
                        current_start,
                        next_node,
                        (*used_edges, edge_id),
                        visits | {next_node: next_visits + 1},
                        cycle_count + added_cycle,
                    )
                )
    return list(paths.values())


def _loop_paths(
    graph: SkeletonGraph,
    *,
    limits: PathSearchLimits = DEFAULT_SEARCH_LIMITS,
) -> list[TopologyRoute]:
    incident: dict[int, list[int]] = {node.id: [] for node in graph.nodes}
    for edge_id, edge in enumerate(graph.edges):
        incident[edge.a].append(edge_id)
        if edge.b != edge.a:
            incident[edge.b].append(edge_id)
    paths: dict[tuple[int, ...], TopologyRoute] = {}
    states_expanded = 0

    for node in graph.nodes:
        start = node.id
        stack = [(start, start, (), frozenset({start}))]
        while stack:
            current_start, current, used_edges, visited_nodes = stack.pop()
            states_expanded = _next_expansion_count("loop", limits, states_expanded)
            for edge_id in sorted(incident[current], reverse=True):
                if edge_id in used_edges:
                    continue
                next_node = _other_node(graph.edges[edge_id], current)
                if next_node == current_start:
                    sequence = (*used_edges, edge_id)
                    key = tuple(sorted(sequence))
                    if key not in paths:
                        if len(paths) >= limits.max_paths:
                            raise PathSearchLimitError(
                                "loop",
                                "max_paths",
                                limits.max_paths,
                                len(paths) + 1,
                            )
                        paths[key] = TopologyRoute(sequence, current_start, current_start, 1)
                elif next_node not in visited_nodes:
                    stack.append(
                        (
                            current_start,
                            next_node,
                            (*used_edges, edge_id),
                            visited_nodes | {next_node},
                        )
                    )
    return list(paths.values())


def prepare_topology_paths(
    graph: SkeletonGraph,
    *,
    path_kinds: tuple[Literal["open", "loop", "open-with-loop"], ...] = (
        "open",
        "loop",
        "open-with-loop",
    ),
    limits: PathSearchLimits | None = None,
    max_paths: int | None = None,
) -> TopologyPathInventory:
    """Enumerate selected route kinds once for reuse during ranking.

    Parameters
    ----------
    graph : SkeletonGraph
        Graph whose routes are enumerated. The returned inventory belongs to
        this exact graph object.
    path_kinds : tuple of str
        Supported entries are ``"open"``, ``"loop"``, and ``"open-with-loop"``.
        The default prepares all three kinds.
        Duplicates and unsupported kinds are invalid; an empty tuple prepares no
        routes.
    limits : PathSearchLimits or None
        Per-route-kind bounds for completed routes and expanded search states.
    max_paths : int or None
        Legacy maximum completed routes per route kind. Mutually exclusive with
        ``limits``.

    Returns
    -------
    TopologyPathInventory
        Inventory containing immutable route tuples keyed by the requested kinds.

    Raises
    ------
    TypeError
        If ``limits`` is not a ``PathSearchLimits`` instance.
    ValueError
        If route kinds are unsupported or duplicated, or both ``limits`` and
        ``max_paths`` are supplied.
    PathSearchLimitError
        If enumeration exceeds a configured path or state limit. No partial
        inventory is returned.

    Notes
    -----
    Search limits apply independently to each requested route kind. Selective
    inventories avoid enumerating kinds that will not be ranked. Stored edge
    sequences trade memory and initial enumeration cost for reuse across
    repeated ranking or selection calls.
    """
    limits = _resolve_search_limits(limits, max_paths)
    kinds = tuple(path_kinds)
    supported = {"open", "loop", "open-with-loop"}
    if any(not isinstance(kind, str) or kind not in supported for kind in kinds):
        raise ValueError("path_kinds contains an unsupported route kind")
    if len(set(kinds)) != len(kinds):
        raise ValueError("path_kinds must not contain duplicates")

    paths_by_kind: dict[str, tuple[TopologyRoute, ...]] = {}
    for kind in kinds:
        if kind == "loop":
            routes = _loop_paths(graph, limits=limits)
        else:
            routes = _open_paths(graph, kind, limits=limits)
        paths_by_kind[kind] = tuple(routes)
    return TopologyPathInventory(graph=graph, paths_by_kind=paths_by_kind)
