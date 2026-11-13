from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import hypot
from typing import Literal

import numpy as np
from planarcurve.polyline import (
    mean_squared_turn_angle,
    polyline_length,
    symmetric_polyline_distance,
)
from scipy.ndimage import distance_transform_edt
from scipy.ndimage import label as label_components
from skimage.morphology import skeletonize

Point = tuple[float, float]
Pixel = tuple[int, int]

DEFAULT_MAX_PATHS = 10_000


@dataclass(frozen=True)
class SkeletonNode:
    id: int
    xy: Point
    degree: int
    radius: float
    confidence: float


@dataclass(frozen=True)
class SkeletonEdge:
    a: int
    b: int
    pixels: np.ndarray
    length_px: float
    mean_radius_px: float
    confidence: float


@dataclass(frozen=True)
class SkeletonGraph:
    nodes: tuple[SkeletonNode, ...]
    edges: tuple[SkeletonEdge, ...]

    @property
    def component_count(self) -> int:
        if not self.nodes:
            return 0
        adjacency = {node.id: set() for node in self.nodes}
        for edge in self.edges:
            adjacency[edge.a].add(edge.b)
            adjacency[edge.b].add(edge.a)
        remaining = set(adjacency)
        count = 0
        while remaining:
            count += 1
            stack = [remaining.pop()]
            while stack:
                current = stack.pop()
                for neighbor in adjacency[current] & remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        return count

    @property
    def cycle_count(self) -> int:
        return max(0, len(self.edges) - len(self.nodes) + self.component_count)

    @property
    def endpoint_count(self) -> int:
        return sum(node.degree == 1 for node in self.nodes)

    @property
    def junction_count(self) -> int:
        return sum(node.degree > 2 for node in self.nodes)


@dataclass(frozen=True)
class PathScore:
    guide_distance_px: float | None
    endpoint_orientation_error_px: float | None
    measured_confidence: float
    length_error_px: float | None
    turning_cost: float | None


class NoFeasiblePathError(ValueError):
    """Raised when no route satisfies the requested topology and constraints."""


class PathSearchLimitError(RuntimeError):
    """Raised when topology route enumeration exceeds its candidate limit."""


def _validate_max_paths(max_paths: int) -> int:
    if isinstance(max_paths, bool) or not isinstance(max_paths, (int, np.integer)) or max_paths < 1:
        raise ValueError("max_paths must be a positive integer")
    return int(max_paths)


@dataclass(frozen=True)
class SkeletonPath:
    xy: np.ndarray
    edge_ids: tuple[int, ...]
    start_node: int
    end_node: int
    length_px: float
    confidence: float
    cycle_count: int
    ambiguous: bool
    orientation_ambiguous: bool
    alternatives: int
    score: PathScore


@dataclass(frozen=True)
class TopologyPathInventory:
    graph: SkeletonGraph
    paths_by_kind: dict[
        Literal["open", "loop", "open-with-loop"],
        tuple[tuple[tuple[int, ...], int, int, int], ...],
    ]


def _pixel_adjacency(skeleton: np.ndarray) -> dict[Pixel, tuple[Pixel, ...]]:
    """Use diagonal neighbors only when neither orthogonal bridge pixel exists."""
    pixels = {tuple(map(int, pixel)) for pixel in np.argwhere(skeleton)}
    adjacency: dict[Pixel, tuple[Pixel, ...]] = {}
    for row, column in sorted(pixels):
        neighbors = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                neighbor = (row + dy, column + dx)
                if dx and dy and ((row, column + dx) in pixels or (row + dy, column) in pixels):
                    continue
                if neighbor in pixels:
                    neighbors.append(neighbor)
        adjacency[(row, column)] = tuple(sorted(neighbors))
    return adjacency


def _components(adjacency: dict[Pixel, tuple[Pixel, ...]]) -> list[set[Pixel]]:
    remaining = set(adjacency)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def prune_spurs(skeleton: np.ndarray, min_length_px: float) -> np.ndarray:
    """Remove endpoint-to-junction branches shorter than the configured length."""
    source = np.asarray(skeleton, dtype=bool)
    if source.ndim != 2:
        raise ValueError("skeleton must be a two-dimensional mask")
    if not np.isfinite(min_length_px) or min_length_px < 0.0:
        raise ValueError("minimum spur length must be finite and nonnegative")
    result = source.copy()
    if min_length_px == 0.0:
        return result
    while True:
        adjacency = _pixel_adjacency(result)
        degrees = {pixel: len(neighbors) for pixel, neighbors in adjacency.items()}
        remove: set[Pixel] = set()
        for endpoint in sorted(pixel for pixel, degree in degrees.items() if degree == 1):
            path = [endpoint]
            previous = None
            current = endpoint
            length = 0.0
            while True:
                next_pixels = [pixel for pixel in adjacency[current] if pixel != previous]
                if len(next_pixels) != 1:
                    break
                following = next_pixels[0]
                length += hypot(following[0] - current[0], following[1] - current[1])
                path.append(following)
                previous, current = current, following
            if degrees.get(current, 0) > 2 and length < min_length_px:
                remove.update(path[:-1])
        if not remove:
            return result
        for row, column in remove:
            result[row, column] = False


def _radius_and_confidence(
    point: Pixel,
    radius_map: np.ndarray | None,
    confidence_map: np.ndarray,
) -> tuple[float, float]:
    row, column = point
    radius = float(radius_map[row, column]) if radius_map is not None else 0.0
    return radius, float(confidence_map[row, column])


def build_skeleton_graph(
    observed_ink: np.ndarray,
    *,
    min_spur_length_px: float = 3.0,
    radius: np.ndarray | None = None,
    confidence: np.ndarray | None = None,
    already_skeleton: bool = False,
) -> SkeletonGraph:
    """Skeletonize observed ink and collapse degree-two pixel chains into graph edges."""
    ink = np.asarray(observed_ink, dtype=bool)
    if ink.ndim != 2:
        raise ValueError("observed ink must be a two-dimensional mask")
    if radius is not None:
        radius = np.asarray(radius, dtype=float)
        if radius.shape != ink.shape or not np.isfinite(radius).all() or np.any(radius < 0.0):
            raise ValueError("radius map must be finite, nonnegative, and match observed ink")
    if confidence is None:
        confidence_map = np.ones(ink.shape, dtype=float)
    else:
        confidence_map = np.asarray(confidence, dtype=float)
        if (
            confidence_map.shape != ink.shape
            or not np.isfinite(confidence_map).all()
            or np.any((confidence_map < 0.0) | (confidence_map > 1.0))
        ):
            raise ValueError("confidence map must be between zero and one and match observed ink")

    thin = ink.copy() if already_skeleton else skeletonize(ink)
    thin = prune_spurs(thin, min_spur_length_px)
    adjacency = _pixel_adjacency(thin)
    degrees = {pixel: len(neighbors) for pixel, neighbors in adjacency.items()}
    components = _components(adjacency)
    node_pixels = {pixel for pixel, degree in degrees.items() if degree != 2}
    for component in components:
        if component and all(degrees[pixel] == 2 for pixel in component):
            node_pixels.add(min(component))

    ordered_nodes = sorted(node_pixels)
    node_ids = {pixel: index for index, pixel in enumerate(ordered_nodes)}
    nodes = []
    for pixel in ordered_nodes:
        radius_value, confidence_value = _radius_and_confidence(pixel, radius, confidence_map)
        nodes.append(
            SkeletonNode(
                id=node_ids[pixel],
                xy=(float(pixel[1]), float(pixel[0])),
                degree=degrees[pixel],
                radius=radius_value,
                confidence=confidence_value,
            )
        )

    visited: set[frozenset[Pixel]] = set()
    edges = []
    for start in ordered_nodes:
        for neighbor in adjacency[start]:
            first_key = frozenset((start, neighbor))
            if first_key in visited:
                continue
            chain = [start, neighbor]
            visited.add(first_key)
            previous, current = start, neighbor
            while current not in node_pixels:
                following_pixels = [pixel for pixel in adjacency[current] if pixel != previous]
                if len(following_pixels) != 1:
                    break
                following = following_pixels[0]
                key = frozenset((current, following))
                if key in visited:
                    break
                visited.add(key)
                chain.append(following)
                previous, current = current, following
            if current not in node_ids:
                continue
            xy = np.asarray([(column, row) for row, column in chain], dtype=float)
            length = float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())
            radius_values = [
                _radius_and_confidence(pixel, radius, confidence_map)[0] for pixel in chain
            ]
            confidence_values = [
                _radius_and_confidence(pixel, radius, confidence_map)[1] for pixel in chain
            ]
            edges.append(
                SkeletonEdge(
                    a=node_ids[start],
                    b=node_ids[current],
                    pixels=xy,
                    length_px=length,
                    mean_radius_px=float(np.mean(radius_values)),
                    confidence=float(np.mean(confidence_values)),
                )
            )

    return SkeletonGraph(tuple(nodes), tuple(edges))


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
            edge_points = edge.pixels
        elif edge.b == current:
            edge_points = edge.pixels[::-1]
        else:
            raise ValueError("edge sequence is not connected")
        points.extend(edge_points if not points else edge_points[1:])
        current = _other_node(edge, current)
    return np.asarray(points, dtype=float), current


def _open_paths(
    graph: SkeletonGraph,
    path_kind: Literal["open", "open-with-loop"],
    *,
    max_paths: int = DEFAULT_MAX_PATHS,
) -> list[tuple[tuple[int, ...], int, int, int]]:
    max_paths = _validate_max_paths(max_paths)
    incident: dict[int, list[int]] = {node.id: [] for node in graph.nodes}
    for edge_id, edge in enumerate(graph.edges):
        incident[edge.a].append(edge_id)
        if edge.b != edge.a:
            incident[edge.b].append(edge_id)
    endpoints = sorted(node.id for node in graph.nodes if node.degree == 1)
    paths: dict[tuple[tuple[int, ...], int], tuple[tuple[int, ...], int, int, int]] = {}
    allow_one_cycle = path_kind == "open-with-loop"

    def walk(
        start: int,
        current: int,
        used_edges: tuple[int, ...],
        visits: dict[int, int],
        cycle_count: int,
    ) -> None:
        if current != start and current in endpoints:
            if (path_kind == "open" and cycle_count == 0) or (allow_one_cycle and cycle_count == 1):
                key = (tuple(sorted(used_edges)), start)
                if key not in paths:
                    if len(paths) >= max_paths:
                        raise PathSearchLimitError(
                            f"{path_kind} route enumeration exceeded max_paths={max_paths}"
                        )
                    paths[key] = (used_edges, start, current, cycle_count)
            return
        used = set(used_edges)
        for edge_id in sorted(incident[current]):
            if edge_id in used:
                continue
            next_node = _other_node(graph.edges[edge_id], current)
            next_visits = visits.get(next_node, 0)
            if next_visits >= 2:
                continue
            added_cycle = int(next_visits > 0)
            if cycle_count + added_cycle > 1:
                continue
            walk(
                start,
                next_node,
                (*used_edges, edge_id),
                visits | {next_node: next_visits + 1},
                cycle_count + added_cycle,
            )

    for start in endpoints:
        walk(start, start, (), {start: 1}, 0)
    return list(paths.values())


def _loop_paths(
    graph: SkeletonGraph, *, max_paths: int = DEFAULT_MAX_PATHS
) -> list[tuple[tuple[int, ...], int, int, int]]:
    max_paths = _validate_max_paths(max_paths)
    incident: dict[int, list[int]] = {node.id: [] for node in graph.nodes}
    for edge_id, edge in enumerate(graph.edges):
        incident[edge.a].append(edge_id)
        if edge.b != edge.a:
            incident[edge.b].append(edge_id)
    paths: dict[tuple[int, ...], tuple[tuple[int, ...], int, int, int]] = {}

    def walk(
        start: int,
        current: int,
        used_edges: tuple[int, ...],
        visited_nodes: set[int],
    ) -> None:
        for edge_id in sorted(incident[current]):
            if edge_id in used_edges:
                continue
            next_node = _other_node(graph.edges[edge_id], current)
            if next_node == start:
                sequence = (*used_edges, edge_id)
                key = tuple(sorted(sequence))
                if key not in paths:
                    if len(paths) >= max_paths:
                        raise PathSearchLimitError(
                            f"loop route enumeration exceeded max_paths={max_paths}"
                        )
                    paths[key] = (sequence, start, start, 1)
            elif next_node not in visited_nodes:
                walk(start, next_node, (*used_edges, edge_id), visited_nodes | {next_node})

    for node in graph.nodes:
        walk(node.id, node.id, (), {node.id})
    return list(paths.values())


def prepare_topology_paths(
    graph: SkeletonGraph, *, max_paths: int = DEFAULT_MAX_PATHS
) -> TopologyPathInventory:
    """Enumerate routes once, capped at ``max_paths`` per route kind.

    Exhaustive route enumeration may grow exponentially on branched or cyclic
    graphs. The cap counts distinct routes, including both orientations for open
    paths, and raises :class:`PathSearchLimitError` instead of returning a partial
    inventory.
    """
    max_paths = _validate_max_paths(max_paths)
    return TopologyPathInventory(
        graph=graph,
        paths_by_kind={
            "open": tuple(_open_paths(graph, "open", max_paths=max_paths)),
            "loop": tuple(_loop_paths(graph, max_paths=max_paths)),
            "open-with-loop": tuple(_open_paths(graph, "open-with-loop", max_paths=max_paths)),
        },
    )


def _score_landscapes_overlap(first: PathScore, second: PathScore) -> bool:
    if (
        first.guide_distance_px is not None
        and second.guide_distance_px is not None
        and abs(first.guide_distance_px - second.guide_distance_px) >= 0.5
    ):
        return False
    if (
        first.endpoint_orientation_error_px is not None
        and second.endpoint_orientation_error_px is not None
        and abs(first.endpoint_orientation_error_px - second.endpoint_orientation_error_px) >= 0.5
    ):
        return False
    if abs(first.measured_confidence - second.measured_confidence) >= 0.05:
        return False
    if (
        first.length_error_px is not None
        and second.length_error_px is not None
        and abs(first.length_error_px - second.length_error_px) >= 1.0
    ):
        return False
    return (
        first.turning_cost is None
        or second.turning_cost is None
        or abs(first.turning_cost - second.turning_cost) < 0.1
    )


def rank_topology_paths(
    graph: SkeletonGraph,
    *,
    path_kind: Literal["open", "loop", "open-with-loop"] = "open",
    expected_cycles: int | None = None,
    expected_endpoints: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    expected_length_px: float | None = None,
    candidate_xy: np.ndarray | None = None,
    path_inventory: TopologyPathInventory | None = None,
    max_paths: int = DEFAULT_MAX_PATHS,
) -> tuple[SkeletonPath, ...]:
    """Rank feasible routes by candidate geometry, confidence, and later tie-breakers.

    Feasibility constraints are applied before scoring. With a candidate curve,
    symmetric guide distance is primary, endpoint orientation breaks geometric
    ties, and measured confidence is secondary. Expected length, sampled turning
    cost, and edge IDs provide deterministic later tie-breakers.
    """
    if path_kind not in {"open", "loop", "open-with-loop"}:
        raise ValueError(f"unsupported path kind: {path_kind}")
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

    max_paths = _validate_max_paths(max_paths)
    if path_inventory is not None:
        candidates = path_inventory.paths_by_kind[path_kind]
        if len(candidates) > max_paths:
            raise PathSearchLimitError(f"{path_kind} route inventory exceeds max_paths={max_paths}")
    elif path_kind == "loop":
        candidates = _loop_paths(graph, max_paths=max_paths)
    else:
        candidates = _open_paths(graph, path_kind, max_paths=max_paths)
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
    scored: list[tuple[tuple[int, ...], int, int, int, np.ndarray, float, PathScore]] = []
    for edge_ids, start, end, cycles in candidates:
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
            symmetric_polyline_distance(xy, candidate) if candidate is not None else None
        )
        orientation_error = (
            float(np.linalg.norm(xy[0] - candidate[0]) + np.linalg.norm(xy[-1] - candidate[-1]))
            if candidate is not None
            else None
        )
        score = PathScore(
            guide_distance_px=guide_distance,
            endpoint_orientation_error_px=orientation_error,
            measured_confidence=confidence,
            length_error_px=(
                abs(length - expected_length_px) if expected_length_px is not None else None
            ),
            turning_cost=mean_squared_turn_angle(xy, samples=64),
        )
        scored.append((edge_ids, start, end, cycles, xy, length, score))

    def sort_key(
        item: tuple[tuple[int, ...], int, int, int, np.ndarray, float, PathScore],
    ) -> tuple[float, float, float, float, float, tuple[int, ...], int, int]:
        edge_ids, start, end, _, _, _, score = item
        return (
            round(score.guide_distance_px, 9) if score.guide_distance_px is not None else 0.0,
            score.endpoint_orientation_error_px
            if score.endpoint_orientation_error_px is not None
            else 0.0,
            -score.measured_confidence,
            score.length_error_px if score.length_error_px is not None else 0.0,
            score.turning_cost if score.turning_cost is not None else 0.0,
            edge_ids,
            start,
            end,
        )

    scored.sort(key=sort_key)
    if not scored:
        return ()

    selected = scored[0]
    selected_route = tuple(sorted(selected[0]))
    ambiguous = any(
        tuple(sorted(item[0])) != selected_route and _score_landscapes_overlap(selected[6], item[6])
        for item in scored[1:]
    )
    orientation_ambiguous = any(
        tuple(sorted(item[0])) == selected_route
        and np.allclose(item[4], selected[4][::-1])
        and (
            selected[6].endpoint_orientation_error_px is None
            or item[6].endpoint_orientation_error_px is None
            or abs(
                selected[6].endpoint_orientation_error_px - item[6].endpoint_orientation_error_px
            )
            < 0.5
        )
        for item in scored[1:]
    )
    paths = []
    for index, (edge_ids, start, end, cycles, xy, length, score) in enumerate(scored):
        paths.append(
            SkeletonPath(
                xy=xy,
                edge_ids=edge_ids,
                start_node=start,
                end_node=end,
                length_px=length,
                confidence=score.measured_confidence,
                cycle_count=cycles,
                ambiguous=index == 0 and ambiguous,
                orientation_ambiguous=index == 0 and orientation_ambiguous,
                alternatives=len(scored),
                score=score,
            )
        )
    return tuple(paths)


def select_topology_path(
    graph: SkeletonGraph,
    *,
    path_kind: Literal["open", "loop", "open-with-loop"] = "open",
    expected_cycles: int | None = None,
    expected_endpoints: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    expected_length_px: float | None = None,
    candidate_xy: np.ndarray | None = None,
    path_inventory: TopologyPathInventory | None = None,
    max_paths: int = DEFAULT_MAX_PATHS,
) -> SkeletonPath:
    """Choose the highest-ranked route satisfying route and endpoint constraints."""
    ranked = rank_topology_paths(
        graph,
        path_kind=path_kind,
        expected_cycles=expected_cycles,
        expected_endpoints=expected_endpoints,
        endpoint_tolerance_px=endpoint_tolerance_px,
        expected_length_px=expected_length_px,
        candidate_xy=candidate_xy,
        path_inventory=path_inventory,
        max_paths=max_paths,
    )
    if ranked:
        return ranked[0]
    raise NoFeasiblePathError(
        f"no path satisfies topology kind {path_kind!r}, expected cycle count "
        f"{expected_cycles!r}, and endpoint constraints"
    )


def graph_from_mask(
    mask: np.ndarray,
    *,
    min_spur_length: float = 3.0,
    radius: np.ndarray | None = None,
    confidence: np.ndarray | None = None,
    min_component_area: int = 0,
) -> SkeletonGraph:
    """Build a graph from a binary mask, deriving raster radius when omitted.

    Components smaller than ``min_component_area`` pixels are removed. The
    default of zero keeps all components. Public coordinates are always
    ``(x=column, y=row)``.
    """
    source = np.asarray(mask, dtype=bool)
    if source.ndim != 2:
        raise ValueError("mask must be a two-dimensional image")
    if (
        isinstance(min_component_area, bool)
        or not isinstance(min_component_area, (int, np.integer))
        or min_component_area < 0
    ):
        raise ValueError("minimum component area must be a nonnegative integer")
    if min_component_area > 0:
        labels, _ = label_components(source, structure=np.ones((3, 3), dtype=np.uint8))
        areas = np.bincount(labels.ravel())
        keep = areas >= min_component_area
        keep[0] = False
        source = keep[labels]
    if radius is None:
        radius = distance_transform_edt(source)
    return build_skeleton_graph(
        source,
        min_spur_length_px=min_spur_length,
        radius=radius,
        confidence=confidence,
        already_skeleton=False,
    )


def graph_from_skeleton(
    skeleton: np.ndarray,
    *,
    min_spur_length: float = 3.0,
    radius: np.ndarray | None = None,
    confidence: np.ndarray | None = None,
) -> SkeletonGraph:
    """Build a compact graph from an already-thinned 2-D skeleton."""
    return build_skeleton_graph(
        skeleton,
        min_spur_length_px=min_spur_length,
        radius=radius,
        confidence=confidence,
        already_skeleton=True,
    )


def rank_paths(
    graph: SkeletonGraph,
    *,
    path_kind: Literal["open", "loop", "open-with-loop"] = "open",
    expected_cycles: int | None = None,
    expected_endpoints: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    expected_length_px: float | None = None,
    candidate_xy: np.ndarray | None = None,
    path_inventory: TopologyPathInventory | None = None,
    max_paths: int = DEFAULT_MAX_PATHS,
) -> tuple[SkeletonPath, ...]:
    """Typed public alias for :func:`rank_topology_paths`."""
    return rank_topology_paths(
        graph,
        path_kind=path_kind,
        expected_cycles=expected_cycles,
        expected_endpoints=expected_endpoints,
        endpoint_tolerance_px=endpoint_tolerance_px,
        expected_length_px=expected_length_px,
        candidate_xy=candidate_xy,
        path_inventory=path_inventory,
        max_paths=max_paths,
    )


def select_path(
    graph: SkeletonGraph,
    *,
    path_kind: Literal["open", "loop", "open-with-loop"] = "open",
    expected_cycles: int | None = None,
    expected_endpoints: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    expected_length_px: float | None = None,
    candidate_xy: np.ndarray | None = None,
    path_inventory: TopologyPathInventory | None = None,
    max_paths: int = DEFAULT_MAX_PATHS,
) -> SkeletonPath:
    """Typed public alias for :func:`select_topology_path`."""
    return select_topology_path(
        graph,
        path_kind=path_kind,
        expected_cycles=expected_cycles,
        expected_endpoints=expected_endpoints,
        endpoint_tolerance_px=endpoint_tolerance_px,
        expected_length_px=expected_length_px,
        candidate_xy=candidate_xy,
        path_inventory=path_inventory,
        max_paths=max_paths,
    )
