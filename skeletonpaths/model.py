from __future__ import annotations

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
    """Frozen node in a raster-derived topology graph.

    Attributes
    ----------
    id : int
        Nonnegative graph-local node identifier.
    xy : tuple of float
        Pixel coordinate as ``(x, y) = (column, row)``.
    degree : int
        Number of incident raster-topology neighbors at the node pixel.
    radius_px : float
        Radius at the node pixel, in pixels.
    confidence : float
        Node confidence in the inclusive range ``[0, 1]``.

    The model is immutable.
    """

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
    """Frozen graph edge with ordered pixel geometry.

    Attributes
    ----------
    a, b : int
        Graph-local IDs of the edge's endpoint nodes.
    xy : numpy.ndarray
        Read-only ``(N, 2)`` geometry in ``(x, y)`` pixel coordinates, ordered
        from node ``a`` to node ``b``.
    length_px : float
        Polyline length in pixels, consistent with ``xy``.
    mean_radius_px : float
        Mean radius sampled along the edge chain, in pixels.
    confidence : float
        Mean confidence sampled along the edge chain, in ``[0, 1]``.

    Edge ordering supports geometry assembly and ranking. It does not imply
    physical drawing direction. The model is immutable.
    """

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
    """Frozen undirected topology graph.

    Attributes
    ----------
    nodes : tuple of SkeletonNode
        Graph nodes in deterministic order.
    edges : tuple of SkeletonEdge
        Graph edges in deterministic order.

    Construction validates unique node IDs, known edge endpoints, and agreement
    between edge geometry endpoints and their referenced nodes. Public geometry
    uses ``(x, y) = (column, row)`` pixel coordinates. Graph collections are
    tuples and the model is immutable.
    """

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
        """Number of connected components in the graph, or zero for an empty graph."""
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
        """Graph-level cyclomatic diagnostic, ``max(0, |E| - |V| + components)``.

        This counts cycles in the whole graph. It is distinct from a route's
        ``cycle_count`` and does not directly constrain route selection.
        """
        return max(0, len(self.edges) - len(self.nodes) + self.component_count)

    @property
    def endpoint_count(self) -> int:
        """Number of graph nodes whose raster-topology degree is one."""
        return sum(node.degree == 1 for node in self.nodes)

    @property
    def junction_count(self) -> int:
        """Number of graph nodes whose raster-topology degree exceeds two."""
        return sum(node.degree > 2 for node in self.nodes)


@dataclass(frozen=True)
class SkeletonImage:
    """Compatibility base model for skeleton, radius, and topology results.

    :class:`SkeletonAnalysis` extends this model with the analyzed mask and
    confidence arrays and is returned by :func:`analyze_mask`.
    """

    skeleton: np.ndarray
    radius: np.ndarray
    graph: SkeletonGraph

    def __post_init__(self) -> None:
        skeleton = np.asarray(self.skeleton)
        if skeleton.ndim != 2:
            raise ValueError("skeleton must be a two-dimensional binary image")
        if not np.issubdtype(skeleton.dtype, np.bool_) and (
            not np.issubdtype(skeleton.dtype, np.number)
            or not np.isfinite(skeleton).all()
            or np.any((skeleton != 0) & (skeleton != 1))
        ):
            raise ValueError("skeleton must be a two-dimensional binary image")
        skeleton = np.array(skeleton, dtype=bool, copy=True)
        radius = np.asarray(self.radius, dtype=float)
        if radius.shape != skeleton.shape or not np.isfinite(radius).all() or np.any(radius < 0.0):
            raise ValueError("radius must be finite, nonnegative, and match the skeleton")
        if not isinstance(self.graph, SkeletonGraph):
            raise TypeError("graph must be a SkeletonGraph")
        radius = np.array(radius, copy=True)
        skeleton.setflags(write=False)
        radius.setflags(write=False)
        object.__setattr__(self, "skeleton", skeleton)
        object.__setattr__(self, "radius", radius)


@dataclass(frozen=True, init=False)
class SkeletonAnalysis(SkeletonImage):
    """Immutable result of analyzing a binary mask.

    ``mask``, ``skeleton``, ``radius``, and ``confidence`` are owned read-only
    arrays. ``component_labels`` is read-only when present. Confidence is generic
    foreground evidence, not a probability that any route or traversal is correct.
    """

    mask: np.ndarray
    confidence: np.ndarray
    component_labels: np.ndarray | None

    def __init__(
        self,
        mask: np.ndarray,
        skeleton: np.ndarray,
        radius: np.ndarray,
        confidence: np.ndarray,
        graph: SkeletonGraph,
        component_labels: np.ndarray | None = None,
    ) -> None:
        object.__setattr__(self, "mask", mask)
        object.__setattr__(self, "skeleton", skeleton)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "graph", graph)
        object.__setattr__(self, "component_labels", component_labels)
        self.__post_init__()

    def __post_init__(self) -> None:
        SkeletonImage.__post_init__(self)
        mask = np.asarray(self.mask)
        if mask.ndim != 2 or mask.shape != self.skeleton.shape:
            raise ValueError("mask must be two-dimensional and match the skeleton")

        if not np.issubdtype(mask.dtype, np.bool_) and (
            not np.issubdtype(mask.dtype, np.number)
            or not np.isfinite(mask).all()
            or np.any((mask != 0) & (mask != 1))
        ):
            raise ValueError("mask must be a two-dimensional binary image")
        confidence = np.asarray(self.confidence, dtype=float)
        if (
            confidence.shape != mask.shape
            or not np.isfinite(confidence).all()
            or np.any((confidence < 0.0) | (confidence > 1.0))
        ):
            raise ValueError("confidence must be finite, between zero and one, and match the mask")
        component_labels = self.component_labels
        if component_labels is not None:
            labels = np.asarray(component_labels)
            if (
                labels.shape != mask.shape
                or not np.issubdtype(labels.dtype, np.integer)
                or np.any(labels < 0)
                or np.any(labels[~mask] != 0)
            ):
                raise ValueError("component labels must be nonnegative integers matching the mask")
            component_labels = np.array(labels, copy=True)
            component_labels.setflags(write=False)
        mask = np.array(mask, dtype=bool, copy=True)
        confidence = np.array(confidence, dtype=float, copy=True)
        mask.setflags(write=False)
        confidence.setflags(write=False)
        object.__setattr__(self, "mask", mask)
        object.__setattr__(self, "confidence", confidence)
        if component_labels is not None:
            object.__setattr__(self, "component_labels", component_labels)

    @property
    def component_count(self) -> int:
        return self.graph.component_count

    @property
    def endpoint_count(self) -> int:
        return self.graph.endpoint_count

    @property
    def junction_count(self) -> int:
        return self.graph.junction_count

    @property
    def cycle_count(self) -> int:
        return self.graph.cycle_count


@dataclass(frozen=True)
class RouteStep:
    """One explicitly oriented graph-edge traversal."""

    edge_id: int
    direction: Literal["a-to-b", "b-to-a"]

    def __post_init__(self) -> None:
        if (
            isinstance(self.edge_id, bool)
            or not isinstance(self.edge_id, (int, np.integer))
            or self.edge_id < 0
        ):
            raise ValueError("route step edge ID must be a nonnegative integer")
        if self.direction not in {"a-to-b", "b-to-a"}:
            raise ValueError("route step direction must be 'a-to-b' or 'b-to-a'")
        object.__setattr__(self, "edge_id", int(self.edge_id))

    def reversed(self) -> RouteStep:
        """Return this edge step in the opposite graph direction."""
        direction = "b-to-a" if self.direction == "a-to-b" else "a-to-b"
        return RouteStep(self.edge_id, direction)


@dataclass(frozen=True)
class SkeletonWalk:
    """Immutable ordered traversal that may repeat graph edges.

    Coordinates, edge IDs, and directions describe a traversal hypothesis, not
    physical drawing direction. Graph-dependent invariants are checked against
    the source graph by :func:`covering_walk`.
    """

    xy: np.ndarray
    edge_ids: tuple[int, ...]
    edge_directions: tuple[Literal["forward", "reverse"], ...]
    start_node: int | None
    end_node: int | None
    covered_edge_ids: tuple[int, ...]
    covered_edge_count: int
    total_edge_count: int
    repeated_edge_count: int
    length_px: float

    def __post_init__(self) -> None:
        points = np.asarray(self.xy, dtype=float)
        if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
            raise ValueError("walk coordinates must have shape (N, 2) and be finite")
        edge_ids = tuple(self.edge_ids)
        if any(
            isinstance(edge_id, bool) or not isinstance(edge_id, (int, np.integer)) or edge_id < 0
            for edge_id in edge_ids
        ):
            raise ValueError("walk edge IDs must be nonnegative integers")
        edge_ids = tuple(int(edge_id) for edge_id in edge_ids)
        directions = tuple(self.edge_directions)
        if len(directions) != len(edge_ids) or any(
            direction not in {"forward", "reverse"} for direction in directions
        ):
            raise ValueError("walk directions must match the edge traversal sequence")
        covered_edge_ids = tuple(self.covered_edge_ids)
        expected_covered = tuple(sorted(set(edge_ids)))
        if covered_edge_ids != expected_covered:
            raise ValueError("covered edge IDs must be the sorted unique traversed edge IDs")
        if any(
            isinstance(edge_id, bool) or not isinstance(edge_id, (int, np.integer)) or edge_id < 0
            for edge_id in covered_edge_ids
        ):
            raise ValueError("covered edge IDs must be nonnegative integers")
        counts = (self.covered_edge_count, self.total_edge_count, self.repeated_edge_count)
        if any(
            isinstance(count, bool) or not isinstance(count, (int, np.integer)) or count < 0
            for count in counts
        ):
            raise ValueError("walk edge counts must be nonnegative integers")
        covered_count, total_count, repeated_count = (int(count) for count in counts)
        if (
            covered_count != len(covered_edge_ids)
            or any(edge_id >= total_count for edge_id in covered_edge_ids)
            or repeated_count != len(edge_ids) - covered_count
        ):
            raise ValueError("walk edge coverage counts are inconsistent")
        if (self.start_node is None) != (self.end_node is None):
            raise ValueError("walk start and end nodes must both be set or both be None")
        if self.start_node is not None and any(
            isinstance(node, bool) or not isinstance(node, (int, np.integer)) or node < 0
            for node in (self.start_node, self.end_node)
        ):
            raise ValueError("walk endpoints must be nonnegative integer node IDs")
        if not np.isfinite(self.length_px) or self.length_px < 0.0:
            raise ValueError("walk length must be finite and nonnegative")
        geometry_length = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
        if not np.isclose(self.length_px, geometry_length, rtol=1e-6, atol=1e-9):
            raise ValueError("walk length must match its traversal geometry")
        if edge_ids:
            if self.start_node is None or len(points) < 2:
                raise ValueError("an edge-covering walk must include endpoints and geometry")
        elif self.start_node is None:
            if len(points) != 0 or total_count != 0:
                raise ValueError("an empty graph walk must have no coordinates or edges")
        elif len(points) != 1 or self.start_node != self.end_node:
            raise ValueError("a walk without edges must represent one isolated node")
        points = np.array(points, copy=True)
        points.setflags(write=False)
        object.__setattr__(self, "xy", points)
        object.__setattr__(self, "edge_ids", edge_ids)
        object.__setattr__(self, "edge_directions", directions)
        object.__setattr__(self, "covered_edge_ids", expected_covered)
        object.__setattr__(self, "covered_edge_count", covered_count)
        object.__setattr__(self, "total_edge_count", total_count)
        object.__setattr__(self, "repeated_edge_count", repeated_count)
        object.__setattr__(self, "length_px", float(self.length_px))
        if self.start_node is not None:
            object.__setattr__(self, "start_node", int(self.start_node))
            assert self.end_node is not None
            object.__setattr__(self, "end_node", int(self.end_node))

    @property
    def steps(self) -> tuple[RouteStep, ...]:
        """Traversal steps using directions relative to each graph edge."""
        return tuple(
            RouteStep(edge_id, "a-to-b" if direction == "forward" else "b-to-a")
            for edge_id, direction in zip(self.edge_ids, self.edge_directions, strict=True)
        )

    def reversed(self) -> SkeletonWalk:
        """Return the same traversal with order and direction reversed."""
        return SkeletonWalk(
            xy=self.xy[::-1],
            edge_ids=self.edge_ids[::-1],
            edge_directions=tuple(
                "reverse" if direction == "forward" else "forward"
                for direction in reversed(self.edge_directions)
            ),
            start_node=self.end_node,
            end_node=self.start_node,
            covered_edge_ids=self.covered_edge_ids,
            covered_edge_count=self.covered_edge_count,
            total_edge_count=self.total_edge_count,
            repeated_edge_count=self.repeated_edge_count,
            length_px=self.length_px,
        )

    def _validate_graph(self, graph: SkeletonGraph) -> None:
        if self.total_edge_count != len(graph.edges):
            raise ValueError("walk total edge count does not match its graph")
        node_by_id = {node.id: node for node in graph.nodes}
        if self.start_node is None:
            if graph.nodes or graph.edges:
                raise ValueError("empty walk does not match a nonempty graph")
            return
        if self.start_node not in node_by_id or self.end_node not in node_by_id:
            raise ValueError("walk endpoint references an unknown graph node")
        if not self.edge_ids:
            if self.start_node != self.end_node or not np.allclose(
                self.xy[0], node_by_id[self.start_node].xy
            ):
                raise ValueError("walk without edges must match its isolated graph node")
            return
        current = self.start_node
        expected_points = [np.asarray(node_by_id[current].xy, dtype=float)]
        for edge_id, direction in zip(self.edge_ids, self.edge_directions, strict=True):
            if edge_id >= len(graph.edges):
                raise ValueError("walk references an unknown graph edge")
            edge = graph.edges[edge_id]
            if direction == "forward" and edge.a == current:
                current = edge.b
                edge_points = edge.xy
            elif direction == "reverse" and edge.b == current:
                current = edge.a
                edge_points = edge.xy[::-1]
            else:
                raise ValueError("walk edge directions are not connected in sequence")
            expected_points.extend(edge_points[1:])
        if current != self.end_node:
            raise ValueError("walk end node does not match its traversal")
        if not np.allclose(self.xy, np.asarray(expected_points), rtol=1e-7, atol=1e-9):
            raise ValueError("walk coordinates do not match oriented edge geometry")
        expected_length = float(sum(graph.edges[edge_id].length_px for edge_id in self.edge_ids))
        if not np.isclose(self.length_px, expected_length, rtol=1e-6, atol=1e-9):
            raise ValueError("walk length does not match its traversed graph edges")


@dataclass(frozen=True)
class StrokeSearchLimits:
    """Hard bounds for states, candidate hypotheses, traversal work, repeats,
    walks, and junction pairings."""

    max_states: int = 100_000
    max_hypotheses: int = 1_000
    max_walk_steps: int = 10_000
    max_repeated_edges: int = 8
    max_strokes: int = 64
    max_junction_pairings: int = 1_000

    def __post_init__(self) -> None:
        for name in (
            "max_states",
            "max_hypotheses",
            "max_walk_steps",
            "max_strokes",
            "max_junction_pairings",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
            object.__setattr__(self, name, int(value))
        value = self.max_repeated_edges
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
            raise ValueError("max_repeated_edges must be a nonnegative integer")
        object.__setattr__(self, "max_repeated_edges", int(value))


@dataclass(frozen=True)
class StrokeSearchPolicy:
    """Configure independent ranking penalties and ambiguity tolerances.

    Coverage, uncovered length, repeat length, lift count, cycle error, turning
    cost, junction pairing cost, and guide distance each have a weight. The two
    ambiguity tolerances control score overlap and endpoint-order overlap.
    """

    coverage_error_weight: float = 1_000_000.0
    uncovered_length_weight: float = 1_000.0
    repeat_length_weight: float = 100.0
    lift_cost_weight: float = 10.0
    cycle_error_weight: float = 25.0
    turning_cost_weight: float = 1.0
    junction_pairing_cost_weight: float = 1.0
    guide_distance_weight: float = 1.0
    ambiguity_score_tolerance: float = 0.05
    orientation_ambiguity_tolerance_px: float = 0.5
    junction_pairing_tie_tolerance: float = 0.05

    def __post_init__(self) -> None:
        for name in (
            "coverage_error_weight",
            "uncovered_length_weight",
            "repeat_length_weight",
            "lift_cost_weight",
            "cycle_error_weight",
            "turning_cost_weight",
            "junction_pairing_cost_weight",
            "guide_distance_weight",
            "ambiguity_score_tolerance",
            "orientation_ambiguity_tolerance_px",
            "junction_pairing_tie_tolerance",
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, float(value))


@dataclass(frozen=True)
class JunctionPairing:
    """One generic candidate pairing of branches at a graph junction.

    ``pairs`` contains edge-ID pairs; ``unpaired_edges`` retains branches not
    paired by this candidate. ``tangent_cost`` is generic geometry evidence, not
    a claim about the physically correct stroke continuation.
    """

    node_id: int
    pairs: tuple[tuple[int, int], ...]
    unpaired_edges: tuple[int, ...]
    tangent_cost: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.node_id, bool)
            or not isinstance(self.node_id, (int, np.integer))
            or self.node_id < 0
        ):
            raise ValueError("junction node ID must be a nonnegative integer")
        pairs = tuple(tuple(pair) for pair in self.pairs)
        if any(len(pair) != 2 for pair in pairs):
            raise ValueError("junction pairs must contain two edge IDs")
        normalized_pairs = tuple(tuple(sorted(pair)) for pair in pairs)
        unpaired = tuple(self.unpaired_edges)
        edge_ids = [edge_id for pair in normalized_pairs for edge_id in pair] + list(unpaired)
        if any(
            isinstance(edge_id, bool) or not isinstance(edge_id, (int, np.integer)) or edge_id < 0
            for edge_id in edge_ids
        ):
            raise ValueError("junction edge IDs must be nonnegative integers")
        if len(set(edge_ids)) != len(edge_ids):
            raise ValueError("junction pairing edge IDs must be unique")
        if not np.isfinite(self.tangent_cost) or self.tangent_cost < 0.0:
            raise ValueError("junction tangent cost must be finite and nonnegative")
        object.__setattr__(self, "node_id", int(self.node_id))
        object.__setattr__(self, "pairs", tuple(sorted(normalized_pairs)))
        object.__setattr__(self, "unpaired_edges", tuple(sorted(int(edge) for edge in unpaired)))
        object.__setattr__(self, "tangent_cost", float(self.tangent_cost))


@dataclass(frozen=True)
class StrokeHypothesisScore:
    """Independent measurements used to rank one stroke-set explanation.

    Lengths and guide distance are in pixels. ``turning_cost`` is measured in
    squared radians; lift and cycle costs are counts/errors. ``coverage_error``
    is a normalized uncovered-length measure. These dimensions stay separate.
    """

    coverage_error: float
    uncovered_length_px: float
    repeat_length_px: float
    turning_cost: float
    junction_pairing_cost: float
    lift_cost: float
    guide_distance_px: float | None
    cycle_error: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "coverage_error",
            "uncovered_length_px",
            "repeat_length_px",
            "turning_cost",
            "junction_pairing_cost",
            "lift_cost",
            "cycle_error",
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, float(value))
        if self.guide_distance_px is not None:
            if not np.isfinite(self.guide_distance_px) or self.guide_distance_px < 0.0:
                raise ValueError("guide distance must be finite and nonnegative")
            object.__setattr__(self, "guide_distance_px", float(self.guide_distance_px))


@dataclass(frozen=True)
class StrokeHypothesis:
    """A scored explanation of graph edges as one or more traversal walks.

    ``walks`` are topology alternatives, not observed physical strokes. The
    coverage and repeat fields summarize their edge evidence. Ambiguity flags
    describe competing routes, orientations, and component orders; ``truncated``
    means lower-ranked candidates were omitted by the requested result limit.
    """

    walks: tuple[SkeletonWalk, ...]
    covered_edge_ids: frozenset[int]
    uncovered_edge_ids: frozenset[int]
    repeated_edge_ids: tuple[int, ...]
    pen_lift_count: int
    score: StrokeHypothesisScore
    route_ambiguous: bool
    orientation_ambiguous: bool
    junction_pairings: tuple[JunctionPairing, ...] = ()
    component_order_ambiguous: bool = False
    orientation_ambiguous_strokes: tuple[bool, ...] = ()
    repeat_required_by_hypothesis: bool = False
    truncated: bool = False

    def __post_init__(self) -> None:
        walks = tuple(self.walks)
        if any(not isinstance(walk, SkeletonWalk) for walk in walks):
            raise TypeError("hypothesis walks must be SkeletonWalk values")
        covered = frozenset(self.covered_edge_ids)
        uncovered = frozenset(self.uncovered_edge_ids)
        repeated = tuple(sorted(set(self.repeated_edge_ids)))
        edge_ids = covered | uncovered | set(repeated)
        if any(
            isinstance(edge_id, bool) or not isinstance(edge_id, (int, np.integer)) or edge_id < 0
            for edge_id in edge_ids
        ):
            raise ValueError("hypothesis edge IDs must be nonnegative integers")
        if covered & uncovered or not set(repeated) <= covered:
            raise ValueError("hypothesis edge coverage and repetition sets are inconsistent")
        if (
            isinstance(self.pen_lift_count, bool)
            or not isinstance(self.pen_lift_count, (int, np.integer))
            or self.pen_lift_count != max(0, len(walks) - 1)
        ):
            raise ValueError("pen-lift count must equal the number of transitions between walks")
        if not isinstance(self.score, StrokeHypothesisScore):
            raise TypeError("hypothesis score must be a StrokeHypothesisScore")
        for name in ("route_ambiguous", "orientation_ambiguous", "component_order_ambiguous"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.repeat_required_by_hypothesis, bool):
            raise TypeError("repeat_required_by_hypothesis must be bool")
        if not isinstance(self.truncated, bool):
            raise TypeError("truncated must be bool")
        if self.repeat_required_by_hypothesis != bool(repeated):
            raise ValueError("repeat flag must match repeated edge evidence")
        pairings = tuple(self.junction_pairings)
        if any(not isinstance(pairing, JunctionPairing) for pairing in pairings):
            raise TypeError("junction pairings must be JunctionPairing values")
        orientation = tuple(self.orientation_ambiguous_strokes)
        if orientation and (
            len(orientation) != len(walks)
            or any(not isinstance(value, bool) for value in orientation)
        ):
            raise ValueError("per-stroke orientation ambiguity must match the walks")
        object.__setattr__(self, "walks", walks)
        object.__setattr__(self, "covered_edge_ids", frozenset(int(edge) for edge in covered))
        object.__setattr__(self, "uncovered_edge_ids", frozenset(int(edge) for edge in uncovered))
        object.__setattr__(self, "repeated_edge_ids", repeated)
        object.__setattr__(self, "pen_lift_count", int(self.pen_lift_count))
        object.__setattr__(self, "junction_pairings", pairings)
        object.__setattr__(self, "orientation_ambiguous_strokes", orientation)

    @property
    def stroke_count(self) -> int:
        """Number of graph walks in this explanation, not a claim of pen strokes."""
        return len(self.walks)


class StrokeSearchLimitError(RuntimeError):
    """Raised when bounded search exceeds a configured limit.

    The exception exposes ``limit_name``, ``configured_value``,
    ``observed_value``, and ``search_stage``. Legacy aliases ``limit_value``,
    ``observed``, and ``stage`` are also available.
    """

    def __init__(
        self,
        limit_name: str,
        configured_value: int,
        observed_value: int,
        search_stage: str,
    ) -> None:
        self.limit_name = limit_name
        self.configured_value = configured_value
        self.observed_value = observed_value
        self.search_stage = search_stage
        self.limit_value = configured_value
        self.observed = observed_value
        self.stage = search_stage
        super().__init__(
            f"{search_stage} exceeded {limit_name}={configured_value} (observed {observed_value})"
        )


class JunctionPairingLimitError(StrokeSearchLimitError):
    """Raised when junction-pairing enumeration exceeds its dedicated bound."""


@dataclass(frozen=True)
class PathScore:
    """Measured ranking values for one feasible route.

    Attributes
    ----------
    guide_distance_px : float or None
        Symmetric geometric distance to ``candidate_xy``, in pixels.
    endpoint_order_error_px : float or None
        Sum of ordered start/end guide endpoint distances, in pixels.
    measured_confidence : float
        Length-weighted route confidence in ``[0, 1]``. This is not a
        probability that the route is correct.
    length_error_px : float or None
        Absolute error from ``expected_length_px``, in pixels.
    turning_cost : float or None
        Sampled mean squared turn angle, in squared radians.
    endpoint_tangent_error_deg : float or None
        Mean angular error for supplied endpoint tangent evidence, in degrees.

    A ``None`` score dimension was not applicable or requested; it does not
    represent zero. The model is immutable.
    """

    guide_distance_px: float | None
    endpoint_order_error_px: float | None
    measured_confidence: float
    length_error_px: float | None
    turning_cost: float | None
    endpoint_tangent_error_deg: float | None = None

    def __post_init__(self) -> None:
        for name in (
            "guide_distance_px",
            "endpoint_order_error_px",
            "length_error_px",
            "turning_cost",
            "endpoint_tangent_error_deg",
        ):
            value = getattr(self, name)
            if value is not None and (not np.isfinite(value) or value < 0.0):
                raise ValueError(f"{name} must be finite and nonnegative")
        if not np.isfinite(self.measured_confidence) or not 0.0 <= self.measured_confidence <= 1.0:
            raise ValueError("measured confidence must be between zero and one")


@dataclass(frozen=True)
class PathRankingPolicy:
    """Configure route ranking, guide ties, and ambiguity evidence.

    Attributes
    ----------
    guide_samples : int
        Number of samples used for symmetric candidate-guide distance.
    turning_samples : int
        Number of samples used for mean squared turning cost.
    guide_tie_tolerance_px : float
        Direct numeric tolerance for grouping guide distances before endpoint
        order and later ranking dimensions break ties. Distances are not rounded.
    ambiguity_guide_distance_px : float
        Maximum guide-distance difference considered overlapping evidence.
    ambiguity_endpoint_order_px : float
        Maximum endpoint-order error difference considered overlapping evidence.
    ambiguity_confidence : float
        Maximum measured-confidence difference considered overlapping evidence.
    ambiguity_length_error_px : float
        Maximum expected-length error difference considered overlapping evidence.
    ambiguity_turning_cost : float
        Maximum turning-cost difference considered overlapping when enabled.
    turning_cost_is_evidence : bool
        Whether turning-cost separation may reduce ambiguity. Turning cost is
        otherwise a deterministic ranking tie-breaker only.
    ambiguity_endpoint_tangent_deg : float
        Maximum tangent-error difference considered overlapping when enabled.
    tangent_error_is_evidence : bool
        Whether endpoint tangent error guides ranking and ambiguity decisions.
    endpoint_tangents_are_hard : bool
        Whether routes outside the supplied tangent tolerance are infeasible.

    Guide tie tolerance controls ranking order and is separate from the
    ambiguity tolerances. The model is immutable.
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
    ambiguity_endpoint_tangent_deg: float = 15.0
    tangent_error_is_evidence: bool = True
    endpoint_tangents_are_hard: bool = False

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
            "ambiguity_endpoint_tangent_deg",
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, float(value))
        if not isinstance(self.turning_cost_is_evidence, bool):
            raise TypeError("turning_cost_is_evidence must be bool")
        if not isinstance(self.tangent_error_is_evidence, bool):
            raise TypeError("tangent_error_is_evidence must be bool")
        if not isinstance(self.endpoint_tangents_are_hard, bool):
            raise TypeError("endpoint_tangents_are_hard must be bool")


DEFAULT_RANKING_POLICY = PathRankingPolicy()


@dataclass(frozen=True)
class PathSearchLimits:
    """Bounds for enumerating topology routes.

    Attributes
    ----------
    max_paths : int
        Maximum completed routes enumerated for each requested route kind.
    max_states : int
        Maximum search states expanded for each requested route kind.

    Exceeding either limit raises ``PathSearchLimitError`` rather than returning
    a partial result. The model is immutable.
    """

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
    """Raised when no route satisfies the requested kind and constraints.

    ``select_path()`` raises this exception when no feasible route remains.
    ``rank_paths()`` returns an empty tuple for the same absence of candidates.
    """


class PathSearchLimitError(RuntimeError):
    """Raised when route enumeration exceeds a configured search bound.

    Attributes
    ----------
    path_kind : str
        Route kind whose enumeration exceeded a limit.
    limit_name : str
        Search bound that was exceeded.
    limit_value : int
        Configured value of the exceeded bound.
    observed : int
        Number of paths or states observed at the point the limit was exceeded.
    """

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
    """Frozen, ranked route geometry assembled from a topology route.

    Attributes
    ----------
    xy : numpy.ndarray
        Read-only polyline coordinates with shape ``(N, 2)`` in ``(x, y)``
        pixel units.
    edge_ids : tuple of int
        Ordered graph edge IDs forming the route.
    start_node, end_node : int
        Node IDs defining this geometry's orientation for assembly and ranking.
    length_px : float
        Polyline length in pixels, consistent with ``xy``.
    confidence : float
        Length-weighted measured confidence in ``[0, 1]``, not a probability
        that the route is correct.
    cycle_count : int
        Number of cycles in this route, not the whole graph.
    score : PathScore
        Measured ranking dimensions for this route.

    Ambiguity belongs to ``PathSelection`` and is intentionally not stored on a
    ``SkeletonPath``. The model is immutable.
    """

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
    """Selected path and selection-context ambiguity metadata.

    Attributes
    ----------
    path : SkeletonPath
        Highest-ranked feasible route materialized by the selection.
    ambiguous : bool
        Whether another different edge route has overlapping score evidence
        under the configured ambiguity tolerances.
    orientation_ambiguous : bool
        Whether the reversed orientation of this same edge route remains
        indistinguishable within endpoint-order evidence.
    feasible_path_count : int
        Number of scored alternatives satisfying the requested constraints.

    Ambiguity flags describe this selection context and do not change the path's
    measured confidence. The model is immutable.
    """

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
    """Topology-level route represented by a connected edge sequence.

    Attributes
    ----------
    edge_ids : tuple of int
        Unique graph edge IDs in traversal order.
    start_node, end_node : int
        Endpoint node IDs defining the sequence orientation. A loop has the same
        start and end node.
    cycle_count : int
        Number of cycles in this route, independent of graph-level cycles.

    The edge sequence is connected and has no repeated edge. Its orientation is
    for topology traversal and geometry assembly, not physical drawing
    direction. The model is immutable.
    """

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
    """Reusable route enumeration tied to one exact ``SkeletonGraph`` object.

    Attributes
    ----------
    graph : SkeletonGraph
        The graph instance used to prepare the inventory. Ranking requires that
        same object.
    paths_by_kind : collections.abc.Mapping
        Immutable mapping from selectively prepared route kinds to tuples of
        ``TopologyRoute`` objects.

    Preparing only needed kinds avoids unnecessary enumeration. Stored route
    edge sequences consume memory in exchange for reuse. The model is immutable.
    """

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


@dataclass(frozen=True)
class SubpixelCenterlineOptions:
    """Bounded controls for reconstructing continuous centerline geometry."""

    normal_sample_step_px: float = 0.125
    max_normal_search_px: float | None = None
    tangent_window_px: float = 4.0
    junction_guard_px: float = 2.0
    min_boundary_gradient: float = 0.02
    min_sample_confidence: float = 0.05
    refinement_passes: int = 2
    spline_options: object | None = None
    output_spacing_px: float = 0.25
    max_curvature_radius: float = 0.8
    max_refinement_samples: int = 100_000
    max_normal_probes: int = 2_000_000

    def __post_init__(self) -> None:
        for name in (
            "normal_sample_step_px",
            "tangent_window_px",
            "output_spacing_px",
            "max_curvature_radius",
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
            object.__setattr__(self, name, float(value))
        for name in ("junction_guard_px", "min_boundary_gradient"):
            value = getattr(self, name)
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, float(value))
        if self.max_normal_search_px is not None:
            if (
                not np.isfinite(self.max_normal_search_px)
                or self.max_normal_search_px <= 0.0
                or self.max_normal_search_px > 64.0
            ):
                raise ValueError("max_normal_search_px must be positive and no greater than 64")
            object.__setattr__(self, "max_normal_search_px", float(self.max_normal_search_px))
        if (
            not np.isfinite(self.min_sample_confidence)
            or not 0.0 <= self.min_sample_confidence <= 1.0
        ):
            raise ValueError("min_sample_confidence must be between zero and one")
        if (
            isinstance(self.refinement_passes, bool)
            or not isinstance(self.refinement_passes, (int, np.integer))
            or not 1 <= self.refinement_passes <= 3
        ):
            raise ValueError("refinement_passes must be an integer between one and three")
        if (
            isinstance(self.max_refinement_samples, bool)
            or not isinstance(self.max_refinement_samples, (int, np.integer))
            or self.max_refinement_samples < 1
        ):
            raise ValueError("max_refinement_samples must be a positive integer")
        object.__setattr__(self, "refinement_passes", int(self.refinement_passes))
        object.__setattr__(self, "max_refinement_samples", int(self.max_refinement_samples))
        if (
            isinstance(self.max_normal_probes, bool)
            or not isinstance(self.max_normal_probes, (int, np.integer))
            or self.max_normal_probes < 1
        ):
            raise ValueError("max_normal_probes must be a positive integer")
        object.__setattr__(self, "max_normal_probes", int(self.max_normal_probes))


def _subpixel_array(values: object, *, name: str, columns: int | None = None) -> np.ndarray:
    array = np.array(values, dtype=float, copy=True)
    if array.ndim != (2 if columns is not None else 1):
        raise ValueError(f"{name} must have {2 if columns is not None else 1} dimensions")
    if columns is not None and array.shape[1] != columns:
        raise ValueError(f"{name} must have shape (N, {columns})")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class RefinedEdgeDiagnostics:
    """Bounded evidence and fitting diagnostics for one refined edge."""

    raw_point_count: int
    valid_cross_section_count: int
    invalid_reason_counts: Mapping[str, int]
    median_shift_px: float
    p95_shift_px: float
    median_spline_residual_px: float
    p95_spline_residual_px: float
    selected_control_count: int
    first_pass_improvement_px: float
    junction_guard_sample_count: int
    max_abs_curvature_radius: float
    normal_probe_count: int
    spline_fit_count: int

    def __post_init__(self) -> None:
        for name in (
            "raw_point_count",
            "valid_cross_section_count",
            "selected_control_count",
            "junction_guard_sample_count",
            "normal_probe_count",
            "spline_fit_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
            object.__setattr__(self, name, int(value))
        if self.valid_cross_section_count > self.raw_point_count:
            raise ValueError("valid cross-section count cannot exceed the raw point count")
        for name in (
            "median_shift_px",
            "p95_shift_px",
            "median_spline_residual_px",
            "p95_spline_residual_px",
            "max_abs_curvature_radius",
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, float(value))
        if not np.isfinite(self.first_pass_improvement_px):
            raise ValueError("first_pass_improvement_px must be finite")
        object.__setattr__(self, "first_pass_improvement_px", float(self.first_pass_improvement_px))
        reasons = dict(self.invalid_reason_counts)
        if any(not isinstance(key, str) or not key for key in reasons):
            raise ValueError("invalid reason names must be nonempty strings")
        if any(
            isinstance(count, bool) or not isinstance(count, (int, np.integer)) or count < 0
            for count in reasons.values()
        ):
            raise ValueError("invalid reason counts must be nonnegative integers")
        object.__setattr__(
            self,
            "invalid_reason_counts",
            MappingProxyType({key: int(value) for key, value in reasons.items()}),
        )


@dataclass(frozen=True)
class RefinedEdgeGeometry:
    """Continuous geometry for one graph edge in ``(column, row)`` coordinates."""

    edge_id: int
    xy: np.ndarray
    tangent: np.ndarray
    curvature: np.ndarray
    radius_px: np.ndarray
    confidence: np.ndarray
    length_px: float
    source: Literal["decision-field", "binary-distance-fallback"]
    diagnostics: RefinedEdgeDiagnostics
    curve_segments: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        if (
            isinstance(self.edge_id, bool)
            or not isinstance(self.edge_id, (int, np.integer))
            or self.edge_id < 0
        ):
            raise ValueError("edge_id must be a nonnegative integer")
        xy = _subpixel_array(self.xy, name="xy", columns=2)
        tangent = _subpixel_array(self.tangent, name="tangent", columns=2)
        curvature = _subpixel_array(self.curvature, name="curvature")
        radius = _subpixel_array(self.radius_px, name="radius_px")
        confidence = _subpixel_array(self.confidence, name="confidence")
        if len(xy) < 2:
            raise ValueError("refined edge geometry must contain at least two points")
        if any(len(values) != len(xy) for values in (tangent, curvature, radius, confidence)):
            raise ValueError("refined edge geometry arrays must have matching lengths")
        if np.any(radius < 0.0):
            raise ValueError("radius_px must be nonnegative")
        if np.any((confidence < 0.0) | (confidence > 1.0)):
            raise ValueError("confidence must be between zero and one")
        if not np.isfinite(self.length_px) or self.length_px <= 0.0:
            raise ValueError("length_px must be finite and positive")
        if self.source not in {"decision-field", "binary-distance-fallback"}:
            raise ValueError("unsupported refined edge source")
        if not isinstance(self.diagnostics, RefinedEdgeDiagnostics):
            raise TypeError("diagnostics must be RefinedEdgeDiagnostics")
        curves = tuple(self.curve_segments)
        object.__setattr__(self, "edge_id", int(self.edge_id))
        object.__setattr__(self, "xy", xy)
        object.__setattr__(self, "tangent", tangent)
        object.__setattr__(self, "curvature", curvature)
        object.__setattr__(self, "radius_px", radius)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "length_px", float(self.length_px))
        object.__setattr__(self, "curve_segments", curves)


@dataclass(frozen=True)
class RefinedSkeletonGeometry:
    """Refined edge geometries tied to their unchanged discrete skeleton graph."""

    analysis: SkeletonAnalysis
    edges: tuple[RefinedEdgeGeometry, ...]
    node_xy: Mapping[int, Point]
    node_confidence: Mapping[int, float]
    node_radius_px: Mapping[int, float]
    diagnostics: Mapping[str, int | float | str]

    def __post_init__(self) -> None:
        if not isinstance(self.analysis, SkeletonAnalysis):
            raise TypeError("analysis must be a SkeletonAnalysis")
        edges = tuple(self.edges)
        if any(not isinstance(edge, RefinedEdgeGeometry) for edge in edges):
            raise TypeError("edges must contain RefinedEdgeGeometry values")
        edge_ids = tuple(edge.edge_id for edge in edges)
        if len(edges) != len(self.analysis.graph.edges) or edge_ids != tuple(range(len(edges))):
            raise ValueError("refined edges must preserve every graph edge ID in order")
        node_ids = {node.id for node in self.analysis.graph.nodes}
        node_xy = {
            int(key): (float(value[0]), float(value[1])) for key, value in self.node_xy.items()
        }
        node_confidence = {int(key): float(value) for key, value in self.node_confidence.items()}
        node_radius = {int(key): float(value) for key, value in self.node_radius_px.items()}
        if any(set(values) != node_ids for values in (node_xy, node_confidence, node_radius)):
            raise ValueError("refined node maps must contain exactly the graph node IDs")
        if any(not np.isfinite(point).all() for point in node_xy.values()):
            raise ValueError("refined node coordinates must be finite")
        if any(
            not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in node_confidence.values()
        ):
            raise ValueError("node confidence must be between zero and one")
        if any(not np.isfinite(value) or value < 0.0 for value in node_radius.values()):
            raise ValueError("node radius must be finite and nonnegative")
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "node_xy", MappingProxyType(node_xy))
        object.__setattr__(self, "node_confidence", MappingProxyType(node_confidence))
        object.__setattr__(self, "node_radius_px", MappingProxyType(node_radius))
        object.__setattr__(self, "diagnostics", MappingProxyType(dict(self.diagnostics)))

    @property
    def graph(self) -> SkeletonGraph:
        """The unchanged discrete graph from the source analysis."""
        return self.analysis.graph

    @property
    def edge_by_id(self) -> Mapping[int, RefinedEdgeGeometry]:
        """Immutable edge lookup keyed by the original graph edge ID."""
        return MappingProxyType({edge.edge_id: edge for edge in self.edges})


@dataclass(frozen=True)
class RefinedWalkGeometry:
    """Continuous samples assembled from a discrete walk without changing its events."""

    xy: np.ndarray
    tangent: np.ndarray
    curvature: np.ndarray
    radius_px: np.ndarray
    confidence: np.ndarray
    length_px: float
    edge_ids: tuple[int, ...]
    edge_directions: tuple[Literal["forward", "reverse"], ...]

    def __post_init__(self) -> None:
        xy = _subpixel_array(self.xy, name="xy", columns=2)
        tangent = _subpixel_array(self.tangent, name="tangent", columns=2)
        curvature = _subpixel_array(self.curvature, name="curvature")
        radius = _subpixel_array(self.radius_px, name="radius_px")
        confidence = _subpixel_array(self.confidence, name="confidence")
        if any(len(values) != len(xy) for values in (tangent, curvature, radius, confidence)):
            raise ValueError("refined walk geometry arrays must have matching lengths")
        if np.any(radius < 0.0) or np.any((confidence < 0.0) | (confidence > 1.0)):
            raise ValueError("walk radius and confidence values are out of range")
        if not np.isfinite(self.length_px) or self.length_px < 0.0:
            raise ValueError("length_px must be finite and nonnegative")
        edge_ids = tuple(int(value) for value in self.edge_ids)
        directions = tuple(self.edge_directions)
        if any(value < 0 for value in edge_ids):
            raise ValueError("walk edge IDs must be nonnegative")
        if len(edge_ids) != len(directions) or any(
            direction not in {"forward", "reverse"} for direction in directions
        ):
            raise ValueError("walk directions must match its edge sequence")
        object.__setattr__(self, "xy", xy)
        object.__setattr__(self, "tangent", tangent)
        object.__setattr__(self, "curvature", curvature)
        object.__setattr__(self, "radius_px", radius)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "length_px", float(self.length_px))
        object.__setattr__(self, "edge_ids", edge_ids)
        object.__setattr__(self, "edge_directions", directions)
