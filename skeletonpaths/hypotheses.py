from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import replace

import numpy as np
from numpy.typing import ArrayLike
from planarcurve.descriptors import descriptor_distance, reverse_descriptor, trajectory_descriptor
from planarcurve.polyline import (
    mean_squared_turn_angle,
    polyline_length,
    project_points_to_polyline,
    symmetric_polyline_distance,
    unit_tangents,
)

from .model import (
    JunctionPairing,
    JunctionPairingLimitError,
    SkeletonAnalysis,
    SkeletonGraph,
    SkeletonWalk,
    StrokeHypothesis,
    StrokeHypothesisScore,
    StrokeSearchLimitError,
    StrokeSearchLimits,
    StrokeSearchPolicy,
)
from .walk import covering_walk

DEFAULT_STROKE_SEARCH_LIMITS = StrokeSearchLimits()
DEFAULT_STROKE_SEARCH_POLICY = StrokeSearchPolicy()


def _count_state(states: list[int], limits: StrokeSearchLimits, stage: str) -> None:
    states[0] += 1
    if states[0] > limits.max_states:
        raise StrokeSearchLimitError("max_states", limits.max_states, states[0], stage)


def _components(graph: SkeletonGraph) -> tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]:
    adjacency = {node.id: set() for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.a].add(edge.b)
        adjacency[edge.b].add(edge.a)
    remaining = set(adjacency)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        nodes = {start}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in sorted(adjacency[node] & remaining):
                remaining.remove(neighbor)
                nodes.add(neighbor)
                queue.append(neighbor)
        edge_ids = tuple(
            edge_id
            for edge_id, edge in enumerate(graph.edges)
            if edge.a in nodes and edge.b in nodes
        )
        components.append((tuple(sorted(nodes)), edge_ids))
    return tuple(components)


def _incident_edges(graph: SkeletonGraph) -> dict[int, list[tuple[int, str]]]:
    incident = {node.id: [] for node in graph.nodes}
    for edge_id, edge in enumerate(graph.edges):
        incident[edge.a].append((edge_id, "a"))
        incident[edge.b].append((edge_id, "b"))
    for ports in incident.values():
        ports.sort()
    return incident



def _guide_arrays(guide_paths: Sequence[ArrayLike] | None) -> tuple[np.ndarray, ...]:
    if guide_paths is None:
        return ()
    if isinstance(guide_paths, np.ndarray) and guide_paths.ndim == 2:
        sources = (guide_paths,)
    else:
        sources = tuple(guide_paths)
    guides = []
    for guide in sources:
        points = np.asarray(guide, dtype=float)
        if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
            raise ValueError("each guide path must have shape (N, 2) with N >= 2")
        if not np.isfinite(points).all() or polyline_length(points) <= 1e-12:
            raise ValueError("guide paths must contain finite coordinates and positive length")
        guides.append(np.array(points, copy=True))
    return tuple(guides)


def _edge_outward_tangent(
    graph: SkeletonGraph, port: tuple[int, str], node_id: int
) -> np.ndarray:
    edge_id, side = port
    edge = graph.edges[edge_id]
    tangent = unit_tangents(edge.xy)
    if side == "a" and edge.a == node_id:
        return tangent[0]
    if side == "b" and edge.b == node_id:
        return -tangent[-1]
    raise ValueError("junction port does not touch its node")



def _guide_tangent_cost(
    graph: SkeletonGraph,
    node_id: int,
    continuation: np.ndarray,
    guides: tuple[np.ndarray, ...],
) -> float:
    if not guides:
        return 0.0
    node = np.asarray(next(node for node in graph.nodes if node.id == node_id).xy)
    costs = []
    for guide in guides:
        projection = project_points_to_polyline(node[None, :], guide)
        segment = int(projection.segment_index[0])
        tangent = unit_tangents(guide)[segment]
        costs.append(1.0 - abs(float(np.dot(continuation, tangent))))
    return min(costs)


def _junction_options(
    graph: SkeletonGraph,
    guides: tuple[np.ndarray, ...],
    limits: StrokeSearchLimits,
    states: list[int],
) -> tuple[tuple[JunctionPairing, ...], ...]:
    incident = _incident_edges(graph)
    junctions = [
        (node_id, ports) for node_id, ports in sorted(incident.items()) if len(ports) > 2
    ]
    if not junctions:
        return ((),)

    pairing_count = [0]
    options_by_node = []
    for node_id, ports in junctions:
        tangent_by_port = {
            port: _edge_outward_tangent(graph, port, node_id) for port in ports
        }
        candidates = []

        def enumerate_matchings(
            remaining: tuple[tuple[int, str], ...],
            pairs: tuple[tuple[tuple[int, str], tuple[int, str]], ...],
            *,
            node_id: int = node_id,
            ports: list[tuple[int, str]] = ports,
            tangent_by_port: dict[tuple[int, str], np.ndarray] = tangent_by_port,
            candidates: list[JunctionPairing] = candidates,
        ) -> None:
            _count_state(states, limits, "junction-pairing-generation")
            if not remaining:
                paired = {port for pair in pairs for port in pair}
                unpaired_ports = tuple(port for port in ports if port not in paired)
                edge_pairs = tuple((first[0], second[0]) for first, second in pairs)
                unpaired_edges = tuple(sorted({port[0] for port in unpaired_ports}))
                cost = 0.0
                for first, second in pairs:
                    first_tangent = tangent_by_port[first]
                    second_tangent = tangent_by_port[second]
                    continuation = second_tangent - first_tangent
                    magnitude = float(np.linalg.norm(continuation))
                    continuation = continuation / magnitude if magnitude > 1e-12 else np.zeros(2)
                    cost += 1.0 + float(np.dot(first_tangent, second_tangent))
                    cost += _guide_tangent_cost(graph, node_id, continuation, guides)
                candidate = JunctionPairing(
                    node_id=node_id,
                    pairs=edge_pairs,
                    unpaired_edges=unpaired_edges,
                    tangent_cost=max(0.0, cost),
                    port_pairs=pairs,
                    unpaired_ports=unpaired_ports,
                )
                candidates.append(candidate)
                pairing_count[0] += 1
                if pairing_count[0] > limits.max_junction_pairings:
                    raise JunctionPairingLimitError(
                        "max_junction_pairings",
                        limits.max_junction_pairings,
                        pairing_count[0],
                        "junction-pairing-generation",
                    )
                return

            first = remaining[0]
            enumerate_matchings(remaining[1:], pairs)
            for index in range(1, len(remaining)):
                second = remaining[index]
                next_remaining = remaining[1:index] + remaining[index + 1 :]
                enumerate_matchings(next_remaining, pairs + ((first, second),))

        enumerate_matchings(tuple(ports), ())
        candidates.sort(
            key=lambda item: (item.tangent_cost, item.pairs, item.port_pairs, item.unpaired_ports)
        )
        options_by_node.append(tuple(candidates))

    combinations = []
    combination_count = [0]

    def combine(index: int, selected: tuple[JunctionPairing, ...]) -> None:
        _count_state(states, limits, "junction-pairing-combination")
        if index == len(options_by_node):
            combination_count[0] += 1
            if combination_count[0] > limits.max_junction_pairings:
                raise JunctionPairingLimitError(
                    "max_junction_pairings",
                    limits.max_junction_pairings,
                    combination_count[0],
                    "junction-pairing-combination",
                )
            combinations.append(selected)
            return
        for option in options_by_node[index]:
            combine(index + 1, selected + (option,))

    combine(0, ())
    return tuple(combinations)



def _transitions(
    graph: SkeletonGraph, pairings: tuple[JunctionPairing, ...]
) -> dict[tuple[int, tuple[int, str]], tuple[int, str]]:
    transitions = {}
    for node_id, ports in _incident_edges(graph).items():
        if len(ports) == 2:
            first, second = ports
            transitions[node_id, first] = second
            transitions[node_id, second] = first
    for pairing in pairings:
        if pairing.port_pairs:
            port_pairs = pairing.port_pairs
        else:
            ports = _incident_edges(graph)[pairing.node_id]
            port_by_edge = {port[0]: port for port in ports}
            port_pairs = tuple(
                (port_by_edge[first], port_by_edge[second])
                for first, second in pairing.pairs
            )
        for first, second in port_pairs:
            transitions[pairing.node_id, first] = second
            transitions[pairing.node_id, second] = first
    return transitions



def _walk_from_steps(
    graph: SkeletonGraph,
    steps: tuple[tuple[int, str], ...],
    *,
    isolated_node: int | None = None,
) -> SkeletonWalk:
    if not steps:
        if isolated_node is None:
            raise ValueError("an empty traversal needs an isolated node")
        point = next(node.xy for node in graph.nodes if node.id == isolated_node)
        return SkeletonWalk(
            xy=np.asarray([point], dtype=float),
            edge_ids=(),
            edge_directions=(),
            start_node=isolated_node,
            end_node=isolated_node,
            covered_edge_ids=(),
            covered_edge_count=0,
            total_edge_count=len(graph.edges),
            repeated_edge_count=0,
            length_px=0.0,
        )

    first_edge_id, first_side = steps[0]
    first_edge = graph.edges[first_edge_id]
    start_node = first_edge.a if first_side == "a" else first_edge.b
    current = start_node
    coordinates = [np.asarray(next(node.xy for node in graph.nodes if node.id == current))]
    edge_ids = []
    directions = []
    for edge_id, source_side in steps:
        edge = graph.edges[edge_id]
        if source_side == "a" and edge.a == current:
            direction = "forward"
            current = edge.b
            points = edge.xy
        elif source_side == "b" and edge.b == current:
            direction = "reverse"
            current = edge.a
            points = edge.xy[::-1]
        else:
            raise ValueError("walk step port does not match the current graph node")
        coordinates.extend(points[1:])
        edge_ids.append(edge_id)
        directions.append(direction)
    covered = tuple(sorted(set(edge_ids)))
    return SkeletonWalk(
        xy=np.asarray(coordinates),
        edge_ids=tuple(edge_ids),
        edge_directions=tuple(directions),
        start_node=start_node,
        end_node=current,
        covered_edge_ids=covered,
        covered_edge_count=len(covered),
        total_edge_count=len(graph.edges),
        repeated_edge_count=len(edge_ids) - len(covered),
        length_px=float(sum(graph.edges[edge_id].length_px for edge_id in edge_ids)),
    )



def _decompose(
    graph: SkeletonGraph,
    pairings: tuple[JunctionPairing, ...],
    limits: StrokeSearchLimits,
    states: list[int],
) -> tuple[SkeletonWalk, ...]:
    transitions = _transitions(graph, pairings)
    incident = _incident_edges(graph)
    used: set[int] = set()
    walks = []

    def trace(edge_id: int, source_side: str) -> SkeletonWalk:
        steps = []
        current_edge = edge_id
        current_side = source_side
        while current_edge not in used:
            _count_state(states, limits, "walk-decomposition")
            steps.append((current_edge, current_side))
            used.add(current_edge)
            edge = graph.edges[current_edge]
            if current_side == "a":
                next_node, arrival_port = edge.b, (current_edge, "b")
            else:
                next_node, arrival_port = edge.a, (current_edge, "a")
            following = transitions.get((next_node, arrival_port))
            if following is None or following[0] in used:
                break
            current_edge, current_side = following
        return _walk_from_steps(graph, tuple(steps))

    start_sides = [
        (node_id, edge_id, side)
        for node_id, ports in incident.items()
        for edge_id, side in ports
        if (node_id, (edge_id, side)) not in transitions
    ]
    for _, edge_id, side in sorted(start_sides):
        if edge_id not in used:
            walks.append(trace(edge_id, side))
    for edge_id in range(len(graph.edges)):
        if edge_id not in used:
            walks.append(trace(edge_id, "a"))
    for node_id in sorted(incident):
        if not incident[node_id]:
            walks.append(_walk_from_steps(graph, (), isolated_node=node_id))
    return tuple(walks)


def _single_walk_per_component(graph: SkeletonGraph) -> tuple[SkeletonWalk, ...]:
    walks = []
    for node_ids, edge_ids in _components(graph):
        if not edge_ids:
            walks.append(_walk_from_steps(graph, (), isolated_node=node_ids[0]))
            continue
        local_edges = tuple(graph.edges[edge_id] for edge_id in edge_ids)
        local_nodes = tuple(node for node in graph.nodes if node.id in node_ids)
        local_graph = SkeletonGraph(local_nodes, local_edges)
        local_walk = covering_walk(local_graph)
        steps = []
        for local_edge_id, direction in zip(
            local_walk.edge_ids, local_walk.edge_directions, strict=True
        ):
            edge_id = edge_ids[local_edge_id]
            source_side = "a" if direction == "forward" else "b"
            steps.append((edge_id, source_side))
        walks.append(_walk_from_steps(graph, tuple(steps)))
    return tuple(walks)




def _orient_walk(
    walk: SkeletonWalk,
    guides: tuple[np.ndarray, ...],
    guide_descriptors: tuple[object, ...],
    policy: StrokeSearchPolicy,
) -> tuple[SkeletonWalk, bool, float | None]:
    if not guides or len(walk.xy) < 2 or polyline_length(walk.xy) <= 1e-12:
        return walk, True, None
    descriptor = trajectory_descriptor(walk.xy, samples=32)
    reverse = reverse_descriptor(descriptor)
    forward_scores = [descriptor_distance(descriptor, guide) for guide in guide_descriptors]
    reverse_scores = [descriptor_distance(reverse, guide) for guide in guide_descriptors]
    forward_best = min(forward_scores)
    reverse_best = min(reverse_scores)
    forward_endpoint_error = min(
        np.linalg.norm(walk.xy[0] - guide[0]) + np.linalg.norm(walk.xy[-1] - guide[-1])
        for guide in guides
    )
    reverse_endpoint_error = min(
        np.linalg.norm(walk.xy[-1] - guide[0]) + np.linalg.norm(walk.xy[0] - guide[-1])
        for guide in guides
    )
    orientation_scores_overlap = (
        abs(forward_best - reverse_best) <= policy.ambiguity_score_tolerance
    )
    chosen = (
        walk.reversed()
        if (
            (orientation_scores_overlap and reverse_endpoint_error < forward_endpoint_error)
            or (not orientation_scores_overlap and reverse_best < forward_best)
        )
        else walk
    )
    orientation_ambiguous = bool(
        orientation_scores_overlap
        and abs(forward_endpoint_error - reverse_endpoint_error)
        <= policy.orientation_ambiguity_tolerance_px
    )
    guide_distance = min(symmetric_polyline_distance(walk.xy, guide) for guide in guides)
    return chosen, orientation_ambiguous, guide_distance


def _make_hypothesis(
    graph: SkeletonGraph,
    walks: tuple[SkeletonWalk, ...],
    pairings: tuple[JunctionPairing, ...],
    guides: tuple[np.ndarray, ...],
    guide_descriptors: tuple[object, ...],
    expected_strokes: int | None,
    expected_cycles: int | None,
    policy: StrokeSearchPolicy,
) -> StrokeHypothesis:
    oriented = [_orient_walk(walk, guides, guide_descriptors, policy) for walk in walks]
    walks = tuple(result[0] for result in oriented)
    orientation = tuple(result[1] for result in oriented)
    guide_distances = [result[2] for result in oriented if result[2] is not None]
    edge_counts: dict[int, int] = {}
    for walk in walks:
        for edge_id in walk.edge_ids:
            edge_counts[edge_id] = edge_counts.get(edge_id, 0) + 1
    repeated = tuple(sorted(edge_id for edge_id, count in edge_counts.items() if count > 1))
    covered = frozenset(edge_counts)
    uncovered = frozenset(set(range(len(graph.edges))) - set(covered))
    total_length = sum(edge.length_px for edge in graph.edges)
    uncovered_length = sum(graph.edges[edge_id].length_px for edge_id in uncovered)
    repeat_length = sum(
        (edge_counts[edge_id] - 1) * graph.edges[edge_id].length_px
        for edge_id in edge_counts
        if edge_counts[edge_id] > 1
    )
    turning = sum(
        mean_squared_turn_angle(walk.xy)
        for walk in walks
        if len(walk.xy) >= 3 and polyline_length(walk.xy) > 1e-12
    )
    lifts = max(0, len(walks) - 1)
    lift_cost = float(lifts)
    if expected_strokes is not None:
        lift_cost += abs(len(walks) - expected_strokes)
    cycle_error = (
        float(abs(graph.cycle_count - expected_cycles)) if expected_cycles is not None else 0.0
    )
    score = StrokeHypothesisScore(
        coverage_error=(
            uncovered_length / total_length if total_length > 0.0 else float(bool(uncovered))
        ),
        uncovered_length_px=uncovered_length,
        repeat_length_px=repeat_length,
        turning_cost=turning,
        junction_pairing_cost=sum(pairing.tangent_cost for pairing in pairings),
        lift_cost=lift_cost,
        guide_distance_px=float(sum(guide_distances)) if guide_distances else None,
        cycle_error=cycle_error,
    )
    return StrokeHypothesis(
        walks=walks,
        covered_edge_ids=covered,
        uncovered_edge_ids=uncovered,
        repeated_edge_ids=repeated,
        pen_lift_count=lifts,
        score=score,
        route_ambiguous=False,
        orientation_ambiguous=any(orientation),
        junction_pairings=pairings,
        component_order_ambiguous=len(_components(graph)) > 1,
        orientation_ambiguous_strokes=orientation,
        repeat_required_by_hypothesis=bool(repeated),
    )


def _rank_value(hypothesis: StrokeHypothesis, policy: StrokeSearchPolicy) -> float:
    score = hypothesis.score
    return (
        score.coverage_error * policy.coverage_error_weight
        + score.uncovered_length_px * policy.uncovered_length_weight
        + score.repeat_length_px * policy.repeat_length_weight
        + score.lift_cost * policy.lift_cost_weight
        + score.cycle_error * policy.cycle_error_weight
        + score.turning_cost * policy.turning_cost_weight
        + score.junction_pairing_cost * policy.junction_pairing_cost_weight
        + (score.guide_distance_px or 0.0) * policy.guide_distance_weight
    )


def _signature(hypothesis: StrokeHypothesis) -> tuple[object, ...]:
    routes = tuple(sorted(tuple(sorted(walk.edge_ids)) for walk in hypothesis.walks))
    pairings = tuple(
        (pairing.node_id, pairing.pairs, pairing.port_pairs, pairing.unpaired_ports)
        for pairing in hypothesis.junction_pairings
    )
    return routes, pairings


def rank_covering_walks(
    graph: SkeletonGraph,
    *,
    expected_strokes: int | None = None,
    expected_cycles: int | None = None,
    guide_paths: Sequence[ArrayLike] | None = None,
    limits: StrokeSearchLimits | None = None,
    limit: int = 5,
    policy: StrokeSearchPolicy = DEFAULT_STROKE_SEARCH_POLICY,
) -> tuple[StrokeHypothesis, ...]:
    """Rank bounded multi-walk explanations of every edge in a skeleton graph.

    ``covering_walk`` remains the compatible single-walk API. This plural API
    includes edge-disjoint junction pairings and a repeated-edge covering walk
    for each connected component. A returned walk is a topology traversal, not
    evidence of a physical pen stroke or historical direction.
    """
    if not isinstance(graph, SkeletonGraph):
        raise TypeError("graph must be a SkeletonGraph")
    if limits is None:
        limits = DEFAULT_STROKE_SEARCH_LIMITS
    if not isinstance(limits, StrokeSearchLimits):
        raise TypeError("limits must be a StrokeSearchLimits")
    if not isinstance(policy, StrokeSearchPolicy):
        raise TypeError("policy must be a StrokeSearchPolicy")
    if isinstance(limit, bool) or not isinstance(limit, (int, np.integer)) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if expected_strokes is not None and (
        isinstance(expected_strokes, bool)
        or not isinstance(expected_strokes, (int, np.integer))
        or expected_strokes < 1
    ):
        raise ValueError("expected_strokes must be a positive integer")
    if expected_cycles is not None and (
        isinstance(expected_cycles, bool)
        or not isinstance(expected_cycles, (int, np.integer))
        or expected_cycles < 0
    ):
        raise ValueError("expected_cycles must be a nonnegative integer")
    expected_strokes = int(expected_strokes) if expected_strokes is not None else None
    expected_cycles = int(expected_cycles) if expected_cycles is not None else None
    guides = _guide_arrays(guide_paths)
    guide_descriptors = tuple(trajectory_descriptor(guide, samples=32) for guide in guides)
    states = [0]
    junction_choices = _junction_options(graph, guides, limits, states)
    candidate_walks = [
        (pairings, _decompose(graph, pairings, limits, states)) for pairings in junction_choices
    ]
    candidate_walks.append(((), _single_walk_per_component(graph)))

    hypotheses = []
    signatures = set()
    for pairings, walks in candidate_walks:
        _count_state(states, limits, "hypothesis-scoring")
        if len(walks) > limits.max_strokes:
            continue
        step_count = sum(len(walk.edge_ids) for walk in walks)
        if step_count > limits.max_walk_steps:
            raise StrokeSearchLimitError(
                "max_walk_steps", limits.max_walk_steps, step_count, "hypothesis-scoring"
            )
        hypothesis = _make_hypothesis(
            graph,
            walks,
            pairings,
            guides,
            guide_descriptors,
            expected_strokes,
            expected_cycles,
            policy,
        )
        repeated_steps = sum(walk.repeated_edge_count for walk in hypothesis.walks)
        if repeated_steps > limits.max_repeated_edges:
            continue
        signature = _signature(hypothesis)
        if signature in signatures:
            continue
        signatures.add(signature)
        hypotheses.append(hypothesis)
        if len(hypotheses) > limits.max_hypotheses:
            raise StrokeSearchLimitError(
                "max_hypotheses",
                limits.max_hypotheses,
                len(hypotheses),
                "hypothesis-scoring",
            )

    hypotheses.sort(
        key=lambda item: (
            _rank_value(item, policy),
            item.score.coverage_error,
            item.score.uncovered_length_px,
            item.score.repeat_length_px,
            item.score.lift_cost,
            item.score.turning_cost,
            item.score.junction_pairing_cost,
            item.score.guide_distance_px if item.score.guide_distance_px is not None else 0.0,
            _signature(item),
            tuple((walk.start_node, walk.end_node, walk.edge_ids) for walk in item.walks),
        )
    )
    marked = []
    for hypothesis in hypotheses:
        value = _rank_value(hypothesis, policy)
        ambiguous = any(
            other is not hypothesis
            and _signature(other) != _signature(hypothesis)
            and abs(_rank_value(other, policy) - value) <= policy.ambiguity_score_tolerance
            for other in hypotheses
        )
        marked.append(replace(hypothesis, route_ambiguous=ambiguous))
    is_truncated = len(marked) > int(limit)
    return tuple(replace(item, truncated=is_truncated) for item in marked[: int(limit)])


def stroke_hypotheses_from_analysis(
    analysis: SkeletonAnalysis,
    *,
    expected_strokes: int | None = None,
    expected_cycles: int | None = None,
    guide_paths: Sequence[ArrayLike] | None = None,
    limits: StrokeSearchLimits | None = None,
    limit: int = 5,
    policy: StrokeSearchPolicy = DEFAULT_STROKE_SEARCH_POLICY,
) -> tuple[StrokeHypothesis, ...]:
    """Search the graph in a ``SkeletonAnalysis`` result."""
    if not isinstance(analysis, SkeletonAnalysis):
        raise TypeError("analysis must be a SkeletonAnalysis")
    return rank_covering_walks(
        analysis.graph,
        expected_strokes=expected_strokes,
        expected_cycles=expected_cycles,
        guide_paths=guide_paths,
        limits=limits,
        limit=limit,
        policy=policy,
    )
