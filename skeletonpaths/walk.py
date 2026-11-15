from __future__ import annotations

import heapq
from math import inf

import numpy as np

from .model import SkeletonGraph, SkeletonWalk


class DisconnectedGraphError(ValueError):
    """Raised when a graph cannot be covered by one continuous walk."""


def _adjacency(graph: SkeletonGraph) -> tuple[dict[int, list[tuple[int, int]]], dict[int, int]]:
    adjacent = {node.id: [] for node in graph.nodes}
    degrees = {node.id: 0 for node in graph.nodes}
    for edge_id, edge in enumerate(graph.edges):
        adjacent[edge.a].append((edge.b, edge_id))
        if edge.b != edge.a:
            adjacent[edge.b].append((edge.a, edge_id))
        degrees[edge.a] += 1
        degrees[edge.b] += 1
    for neighbors in adjacent.values():
        neighbors.sort(key=lambda neighbor: (neighbor[1], neighbor[0]))
    return adjacent, degrees


def _shortest_paths(
    graph: SkeletonGraph,
    adjacent: dict[int, list[tuple[int, int]]],
    source: int,
) -> tuple[dict[int, float], dict[int, tuple[int, int]]]:
    distances = {source: 0.0}
    previous: dict[int, tuple[int, int]] = {}
    queue = [(0.0, source)]
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != distances[node]:
            continue
        for neighbor, edge_id in adjacent[node]:
            candidate = distance + graph.edges[edge_id].length_px
            if candidate < distances.get(neighbor, inf):
                distances[neighbor] = candidate
                previous[neighbor] = (node, edge_id)
                heapq.heappush(queue, (candidate, neighbor))
    return distances, previous


def _path_edges(
    source: int,
    target: int,
    previous: dict[int, tuple[int, int]],
) -> tuple[int, ...]:
    path = []
    current = target
    while current != source:
        current, edge_id = previous[current]
        path.append(edge_id)
    path.reverse()
    return tuple(path)


def _endpoints(
    odd_nodes: list[int],
    endpoint_nodes: list[int],
    node_ids: set[int],
    closed_start: int,
    start_node: int | None,
    end_node: int | None,
) -> tuple[int, int]:
    if start_node is None:
        if end_node is None:
            candidates = endpoint_nodes or odd_nodes
            start_node = candidates[0] if candidates else closed_start
        else:
            candidates = [node for node in endpoint_nodes if node != end_node]
            candidates = candidates or [node for node in odd_nodes if node != end_node]
            candidates = candidates or [node for node in sorted(node_ids) if node != end_node]
            start_node = candidates[0] if candidates else end_node
    if end_node is None:
        candidates = [node for node in endpoint_nodes if node != start_node]
        candidates = candidates or [node for node in odd_nodes if node != start_node]
        end_node = candidates[0] if candidates else start_node
    return start_node, end_node


def _validate_endpoint(node_id: int | None, node_ids: set[int], name: str) -> int | None:
    if node_id is None:
        return None
    if isinstance(node_id, bool) or not isinstance(node_id, (int, np.integer)):
        raise ValueError(f"{name} must be an integer node ID")
    node_id = int(node_id)
    if node_id not in node_ids:
        raise ValueError(f"{name} is not present in the graph")
    return node_id


def covering_walk(
    graph: SkeletonGraph,
    *,
    start_node: int | None = None,
    end_node: int | None = None,
) -> SkeletonWalk:
    """Return a deterministic connected traversal covering every graph edge.

    Repeated shortest paths correct vertex parity before a deterministic Euler
    traversal. This bounded polynomial strategy is not necessarily globally
    minimal and does not infer physical drawing direction.
    """
    if not isinstance(graph, SkeletonGraph):
        raise TypeError("graph must be a SkeletonGraph")
    node_ids = {node.id for node in graph.nodes}
    start_node = _validate_endpoint(start_node, node_ids, "start_node")
    end_node = _validate_endpoint(end_node, node_ids, "end_node")
    if not graph.nodes:
        if start_node is not None or end_node is not None:
            raise ValueError("empty graph has no walk endpoints")
        walk = SkeletonWalk(
            xy=np.empty((0, 2)),
            edge_ids=(),
            edge_directions=(),
            start_node=None,
            end_node=None,
            covered_edge_ids=(),
            covered_edge_count=0,
            total_edge_count=0,
            repeated_edge_count=0,
            length_px=0.0,
        )
        walk._validate_graph(graph)
        return walk
    if graph.component_count != 1:
        raise DisconnectedGraphError("covering walk requires a connected graph")

    adjacent, degrees = _adjacency(graph)
    odd_nodes = sorted(node_id for node_id, degree in degrees.items() if degree % 2)
    endpoint_nodes = sorted(node.id for node in graph.nodes if node.degree == 1)
    closed_start = min(
        graph.nodes,
        key=lambda node: (node.xy[0], node.xy[1], node.id),
    ).id
    start_node, end_node = _endpoints(
        odd_nodes,
        endpoint_nodes,
        node_ids,
        closed_start,
        start_node,
        end_node,
    )
    target_odd_nodes = {start_node, end_node} if start_node != end_node else set()
    to_pair = sorted(set(odd_nodes) ^ target_odd_nodes)

    shortest_trees = {node: _shortest_paths(graph, adjacent, node) for node in to_pair}
    duplicate_edge_ids = []
    remaining = set(to_pair)
    while remaining:
        best = None
        ordered = sorted(remaining)
        for first_index, first in enumerate(ordered):
            distances, _ = shortest_trees[first]
            for second in ordered[first_index + 1 :]:
                candidate = (distances.get(second, inf), first, second)
                if best is None or candidate < best:
                    best = candidate
        if best is None or best[0] == inf:
            raise RuntimeError("Euler parity correction could not pair the graph nodes")
        _, first, second = best
        _, previous = shortest_trees[first]
        duplicate_edge_ids.extend(_path_edges(first, second, previous))
        remaining.remove(first)
        remaining.remove(second)

    instance_edge_ids = list(range(len(graph.edges)))
    instance_edge_ids.extend(duplicate_edge_ids)
    walk_adjacency = {node_id: [] for node_id in node_ids}
    for instance_id, edge_id in enumerate(instance_edge_ids):
        edge = graph.edges[edge_id]
        walk_adjacency[edge.a].append((instance_id, edge.b))
        if edge.b != edge.a:
            walk_adjacency[edge.b].append((instance_id, edge.a))
    for neighbors in walk_adjacency.values():
        neighbors.sort()

    cursors = {node_id: 0 for node_id in node_ids}
    used_instances = set()
    stack = [(start_node, None)]
    reverse_nodes = []
    reverse_instances = []
    while stack:
        current = stack[-1][0]
        neighbors = walk_adjacency[current]
        cursor = cursors[current]
        while cursor < len(neighbors) and neighbors[cursor][0] in used_instances:
            cursor += 1
        cursors[current] = cursor
        if cursor == len(neighbors):
            node, incoming_instance = stack.pop()
            reverse_nodes.append(node)
            if incoming_instance is not None:
                reverse_instances.append(incoming_instance)
            continue
        instance_id, neighbor = neighbors[cursor]
        cursors[current] += 1
        if instance_id in used_instances:
            continue
        used_instances.add(instance_id)
        stack.append((neighbor, instance_id))

    if len(used_instances) != len(instance_edge_ids):
        raise RuntimeError("covering walk did not traverse every augmented graph edge")
    walk_nodes = list(reversed(reverse_nodes))
    walk_instances = list(reversed(reverse_instances))
    if walk_nodes[0] != start_node or walk_nodes[-1] != end_node:
        raise RuntimeError("covering walk endpoints do not match the requested nodes")

    node_by_id = {node.id: node for node in graph.nodes}
    coordinates = [np.asarray(node_by_id[start_node].xy, dtype=float)]
    traversed_edge_ids = []
    edge_directions = []
    for instance_id, source, target in zip(
        walk_instances, walk_nodes[:-1], walk_nodes[1:], strict=True
    ):
        edge_id = instance_edge_ids[instance_id]
        edge = graph.edges[edge_id]
        if edge.a == source and edge.b == target:
            points = edge.xy
            direction = "forward"
        elif edge.b == source and edge.a == target:
            points = edge.xy[::-1]
            direction = "reverse"
        else:
            raise RuntimeError("covering walk contains a nonincident graph edge")
        coordinates.extend(points[1:])
        traversed_edge_ids.append(edge_id)
        edge_directions.append(direction)

    covered_edge_ids = tuple(sorted(set(traversed_edge_ids)))
    walk = SkeletonWalk(
        xy=np.asarray(coordinates, dtype=float),
        edge_ids=tuple(traversed_edge_ids),
        edge_directions=tuple(edge_directions),
        start_node=start_node,
        end_node=end_node,
        covered_edge_ids=covered_edge_ids,
        covered_edge_count=len(covered_edge_ids),
        total_edge_count=len(graph.edges),
        repeated_edge_count=len(traversed_edge_ids) - len(covered_edge_ids),
        length_px=float(sum(graph.edges[edge_id].length_px for edge_id in traversed_edge_ids)),
    )
    walk._validate_graph(graph)
    return walk
