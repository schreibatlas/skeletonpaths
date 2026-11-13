from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

import numpy as np

Point = tuple[float, float]
Pixel = tuple[int, int]

DEFAULT_MAX_PATHS = 10_000


@dataclass(frozen=True)
class SkeletonNode:
    id: int
    xy: Point
    degree: int
    radius_px: float
    confidence: float

    def __post_init__(self) -> None:
        if isinstance(self.id, bool) or not isinstance(self.id, (int, np.integer)) or self.id < 0:
            raise ValueError("node id must be a nonnegative integer")
        if (
            isinstance(self.degree, bool)
            or not isinstance(self.degree, (int, np.integer))
            or self.degree < 0
        ):
            raise ValueError("node degree must be a nonnegative integer")
        if len(self.xy) != 2 or not np.isfinite(self.xy).all():
            raise ValueError("node coordinates must be a finite xy pair")
        if not np.isfinite(self.radius_px) or self.radius_px < 0.0:
            raise ValueError("node radius must be finite and nonnegative")
        if not np.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("node confidence must be between zero and one")
        object.__setattr__(self, "id", int(self.id))
        object.__setattr__(self, "degree", int(self.degree))
        object.__setattr__(self, "xy", (float(self.xy[0]), float(self.xy[1])))
        object.__setattr__(self, "radius_px", float(self.radius_px))
        object.__setattr__(self, "confidence", float(self.confidence))


@dataclass(frozen=True)
class SkeletonEdge:
    a: int
    b: int
    xy: np.ndarray
    length_px: float
    mean_radius_px: float
    confidence: float

    def __post_init__(self) -> None:
        if any(
            isinstance(node, bool) or not isinstance(node, (int, np.integer)) or node < 0
            for node in (self.a, self.b)
        ):
            raise ValueError("edge endpoints must be nonnegative integer node ids")
        xy = np.array(self.xy, dtype=np.float64, copy=True)
        if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or not np.isfinite(xy).all():
            raise ValueError("edge xy must contain at least two finite xy points")
        geometry_length = float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())
        if (
            not np.isfinite(self.length_px)
            or self.length_px < 0.0
            or not np.isclose(self.length_px, geometry_length, rtol=1e-6, atol=1e-9)
        ):
            raise ValueError("edge length must match its finite xy geometry")
        if not np.isfinite(self.mean_radius_px) or self.mean_radius_px < 0.0:
            raise ValueError("edge mean radius must be finite and nonnegative")
        if not np.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("edge confidence must be between zero and one")
        xy.setflags(write=False)
        object.__setattr__(self, "a", int(self.a))
        object.__setattr__(self, "b", int(self.b))
        object.__setattr__(self, "xy", xy)
        object.__setattr__(self, "length_px", float(self.length_px))
        object.__setattr__(self, "mean_radius_px", float(self.mean_radius_px))
        object.__setattr__(self, "confidence", float(self.confidence))


@dataclass(frozen=True)
class SkeletonGraph:
    nodes: tuple[SkeletonNode, ...]
    edges: tuple[SkeletonEdge, ...]

    def __post_init__(self) -> None:
        nodes = tuple(self.nodes)
        edges = tuple(self.edges)
        node_by_id = {node.id: node for node in nodes}
        if len(node_by_id) != len(nodes):
            raise ValueError("graph node ids must be unique")
        for edge in edges:
            if edge.a not in node_by_id or edge.b not in node_by_id:
                raise ValueError("edge endpoint references an unknown node")
            if not np.allclose(edge.xy[0], node_by_id[edge.a].xy) or not np.allclose(
                edge.xy[-1], node_by_id[edge.b].xy
            ):
                raise ValueError("edge xy endpoints must match its graph nodes")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)

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
    endpoint_order_error_px: float | None
    measured_confidence: float
    length_error_px: float | None
    turning_cost: float | None

    def __post_init__(self) -> None:
        for name in (
            "guide_distance_px",
            "endpoint_order_error_px",
            "length_error_px",
            "turning_cost",
        ):
            value = getattr(self, name)
            if value is not None and (not np.isfinite(value) or value < 0.0):
                raise ValueError(f"{name} must be finite and nonnegative")
        if not np.isfinite(self.measured_confidence) or not 0.0 <= self.measured_confidence <= 1.0:
            raise ValueError("measured confidence must be between zero and one")


@dataclass(frozen=True)
class PathRankingPolicy:
    """Configure ranking resolution, tie handling, and ambiguity evidence.

    Turning cost remains a deterministic tie-breaker, but does not resolve
    ambiguity unless ``turning_cost_is_evidence`` is enabled.
    """

    guide_samples: int = 64
    turning_samples: int = 64
    guide_tie_tolerance_px: float = 1e-9
    ambiguity_guide_distance_px: float = 0.5
    ambiguity_endpoint_order_px: float = 0.5
    ambiguity_confidence: float = 0.05
    ambiguity_length_error_px: float = 1.0
    ambiguity_turning_cost: float = 0.1
    turning_cost_is_evidence: bool = False

    def __post_init__(self) -> None:
        for name in ("guide_samples", "turning_samples"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
            object.__setattr__(self, name, int(value))
        for name in (
            "guide_tie_tolerance_px",
            "ambiguity_guide_distance_px",
            "ambiguity_endpoint_order_px",
            "ambiguity_confidence",
            "ambiguity_length_error_px",
            "ambiguity_turning_cost",
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, float(value))
        if not isinstance(self.turning_cost_is_evidence, bool):
            raise TypeError("turning_cost_is_evidence must be bool")


DEFAULT_RANKING_POLICY = PathRankingPolicy()


@dataclass(frozen=True)
class PathSearchLimits:
    max_paths: int = DEFAULT_MAX_PATHS
    max_states: int = 100_000

    def __post_init__(self) -> None:
        for name in ("max_paths", "max_states"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
            object.__setattr__(self, name, int(value))


DEFAULT_SEARCH_LIMITS = PathSearchLimits()


class NoFeasiblePathError(ValueError):
    """Raised when no route satisfies the requested topology and constraints."""


class PathSearchLimitError(RuntimeError):
    """Raised when path or state search limits stop route enumeration."""

    def __init__(
        self,
        path_kind: str,
        limit_name: Literal["max_paths", "max_states"],
        limit_value: int,
        observed: int,
    ) -> None:
        self.path_kind = path_kind
        self.limit_name = limit_name
        self.limit_value = limit_value
        self.observed = observed
        super().__init__(
            f"{path_kind} route enumeration exceeded {limit_name}={limit_value} "
            f"(observed {observed})"
        )


def _resolve_search_limits(
    limits: PathSearchLimits | None,
    max_paths: int | None,
) -> PathSearchLimits:
    if limits is not None and not isinstance(limits, PathSearchLimits):
        raise TypeError("limits must be a PathSearchLimits")
    if limits is not None and max_paths is not None:
        raise ValueError("pass either limits or max_paths, not both")
    if limits is not None:
        return limits
    if max_paths is not None:
        return PathSearchLimits(max_paths=max_paths)
    return DEFAULT_SEARCH_LIMITS


@dataclass(frozen=True)
class SkeletonPath:
    xy: np.ndarray
    edge_ids: tuple[int, ...]
    start_node: int
    end_node: int
    length_px: float
    confidence: float
    cycle_count: int
    score: PathScore

    def __post_init__(self) -> None:
        xy = np.array(self.xy, dtype=np.float64, copy=True)
        if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or not np.isfinite(xy).all():
            raise ValueError("path xy must contain at least two finite xy points")
        if not np.isfinite(self.length_px) or self.length_px < 0.0:
            raise ValueError("path length must be finite and nonnegative")
        if not np.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("path confidence must be between zero and one")
        if (
            isinstance(self.cycle_count, bool)
            or not isinstance(self.cycle_count, (int, np.integer))
            or self.cycle_count < 0
        ):
            raise ValueError("path cycle count must be a nonnegative integer")
        if any(
            isinstance(node, bool) or not isinstance(node, (int, np.integer)) or node < 0
            for node in (self.start_node, self.end_node)
        ):
            raise ValueError("path endpoints must be nonnegative integer node ids")
        edge_ids = tuple(self.edge_ids)
        if any(
            isinstance(edge_id, bool) or not isinstance(edge_id, (int, np.integer)) or edge_id < 0
            for edge_id in edge_ids
        ):
            raise ValueError("path edge ids must be nonnegative integers")
        xy_length = float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())
        if not np.isclose(self.length_px, xy_length, rtol=1e-6, atol=1e-9):
            raise ValueError("path length must match its xy geometry")
        xy.setflags(write=False)
        object.__setattr__(self, "xy", xy)
        object.__setattr__(self, "edge_ids", tuple(int(edge_id) for edge_id in edge_ids))
        object.__setattr__(self, "start_node", int(self.start_node))
        object.__setattr__(self, "end_node", int(self.end_node))
        object.__setattr__(self, "length_px", float(self.length_px))
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "cycle_count", int(self.cycle_count))


@dataclass(frozen=True)
class PathSelection:
    path: SkeletonPath
    ambiguous: bool
    orientation_ambiguous: bool
    feasible_path_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.path, SkeletonPath):
            raise TypeError("selected path must be a SkeletonPath")
        if not isinstance(self.ambiguous, bool) or not isinstance(self.orientation_ambiguous, bool):
            raise TypeError("selection ambiguity flags must be bool")
        if (
            isinstance(self.feasible_path_count, bool)
            or not isinstance(self.feasible_path_count, (int, np.integer))
            or self.feasible_path_count < 1
        ):
            raise ValueError("feasible path count must be a positive integer")
        object.__setattr__(self, "feasible_path_count", int(self.feasible_path_count))


@dataclass(frozen=True)
class TopologyRoute:
    edge_ids: tuple[int, ...]
    start_node: int
    end_node: int
    cycle_count: int

    def __post_init__(self) -> None:
        edge_ids = tuple(self.edge_ids)
        if not edge_ids or any(
            isinstance(edge_id, bool) or not isinstance(edge_id, (int, np.integer)) or edge_id < 0
            for edge_id in edge_ids
        ):
            raise ValueError("route edge ids must be nonempty nonnegative integers")
        if len(set(edge_ids)) != len(edge_ids):
            raise ValueError("route edge ids must be unique")
        if any(
            isinstance(node, bool) or not isinstance(node, (int, np.integer)) or node < 0
            for node in (self.start_node, self.end_node)
        ):
            raise ValueError("route endpoints must be nonnegative integer node ids")
        if (
            isinstance(self.cycle_count, bool)
            or not isinstance(self.cycle_count, (int, np.integer))
            or self.cycle_count < 0
        ):
            raise ValueError("route cycle count must be a nonnegative integer")
        object.__setattr__(self, "edge_ids", tuple(int(edge_id) for edge_id in edge_ids))
        object.__setattr__(self, "start_node", int(self.start_node))
        object.__setattr__(self, "end_node", int(self.end_node))
        object.__setattr__(self, "cycle_count", int(self.cycle_count))


@dataclass(frozen=True)
class TopologyPathInventory:
    graph: SkeletonGraph
    paths_by_kind: Mapping[Literal["open", "loop", "open-with-loop"], tuple[TopologyRoute, ...]]

    def __post_init__(self) -> None:
        paths_by_kind = {kind: tuple(routes) for kind, routes in self.paths_by_kind.items()}
        node_ids = {node.id for node in self.graph.nodes}
        for kind, routes in paths_by_kind.items():
            if kind not in {"open", "loop", "open-with-loop"}:
                raise ValueError(f"unsupported path kind: {kind}")
            for route in routes:
                if any(edge_id >= len(self.graph.edges) for edge_id in route.edge_ids):
                    raise ValueError("route references an unknown edge id")
                if route.start_node not in node_ids or route.end_node not in node_ids:
                    raise ValueError("route references an unknown endpoint node")
                current = route.start_node
                for edge_id in route.edge_ids:
                    edge = self.graph.edges[edge_id]
                    if current == edge.a:
                        current = edge.b
                    elif current == edge.b:
                        current = edge.a
                    else:
                        raise ValueError("route edge sequence is disconnected")
                if current != route.end_node:
                    raise ValueError("route endpoints do not match its edge sequence")
        object.__setattr__(self, "paths_by_kind", MappingProxyType(paths_by_kind))
