from collections import deque
from heapq import heappop, heappush
from math import hypot

import numpy as np
from numpy.typing import ArrayLike

from .model import (
    JunctionRegion,
    JunctionRegionOptions,
    Pixel,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonNode,
)


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


def _binary_image(values: ArrayLike, *, name: str) -> np.ndarray:
    image = np.asarray(values)
    if image.ndim != 2:
        raise ValueError(f"{name} must be a two-dimensional image")
    if image.dtype == np.bool_:
        return image.copy()
    if (
        not np.issubdtype(image.dtype, np.number)
        or not np.isfinite(image).all()
        or np.any((image != 0) & (image != 1))
    ):
        raise ValueError(f"{name} must contain only finite zero and one values")
    return image.astype(bool, copy=True)


def prune_spurs(skeleton: ArrayLike, min_length_px: float) -> np.ndarray:
    """Remove short endpoint-to-junction branches from a binary skeleton.

    Parameters
    ----------
    skeleton : numpy.typing.ArrayLike
        Two-dimensional boolean image or finite numeric image containing only
        zero and one values.
    min_length_px : float
        Finite, nonnegative branch-length threshold in pixels. A branch is
        removed only when its length is strictly less than this value.

    Returns
    -------
    numpy.ndarray
        Boolean copy of the skeleton after pruning. A zero threshold returns an
        equivalent copy without pruning; the input dtype is not preserved.

    Raises
    ------
    ValueError
        If the image is not two-dimensional binary data or the threshold is
        negative or non-finite.

    Notes
    -----
    Only endpoint-to-junction branches are candidates. Pruning repeats until no
    qualifying branch remains. Arbitrary short edges are not removed.

    See Also
    --------
    graph_from_skeleton : Build a graph from an already-thinned skeleton.
    graph_from_mask : Skeletonize a binary mask and build its graph.
    """
    source = _binary_image(skeleton, name="skeleton")
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


def _junction_region_supports(
    seeds: list[Pixel],
    adjacency: dict[Pixel, tuple[Pixel, ...]],
    degrees: dict[Pixel, int],
    radius_map: np.ndarray | None,
    options: JunctionRegionOptions,
) -> list[set[Pixel]]:
    if not options.enabled or not seeds:
        return []

    seed_indices = {seed: index for index, seed in enumerate(seeds)}
    parent = list(range(len(seeds)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parent[max(first_root, second_root)] = min(first_root, second_root)

    endpoints = {pixel for pixel, degree in degrees.items() if degree == 1}
    if radius_map is None:
        connecting_paths = []
        for seed_index, seed in enumerate(seeds):
            frontier = [(seed, (seed,))]
            for _ in range(2):
                following = []
                for pixel, path in frontier:
                    for neighbor in adjacency[pixel]:
                        if neighbor in endpoints or neighbor in path:
                            continue
                        next_path = (*path, neighbor)
                        neighbor_index = seed_indices.get(neighbor)
                        if neighbor_index is not None and neighbor_index > seed_index:
                            union(seed_index, neighbor_index)
                            connecting_paths.append(next_path)
                        following.append((neighbor, next_path))
                frontier = following
        groups: dict[int, set[Pixel]] = {}
        for index, seed in enumerate(seeds):
            groups.setdefault(find(index), set()).add(seed)
        for path in connecting_paths:
            groups[find(seed_indices[path[0]])].update(path)
        return [groups[root] for root in sorted(groups)]

    neighborhoods: list[set[Pixel]] = []
    for seed in seeds:
        row, column = seed
        merge_radius = max(
            options.minimum_merge_radius_px,
            options.merge_radius_factor * float(radius_map[row, column]),
        )
        if options.maximum_merge_radius_px is not None:
            merge_radius = min(merge_radius, options.maximum_merge_radius_px)
        distances = {seed: 0.0}
        frontier = [(0.0, seed)]
        while frontier:
            distance, pixel = heappop(frontier)
            if distance > distances[pixel]:
                continue
            for neighbor in adjacency[pixel]:
                if neighbor in endpoints:
                    continue
                step = hypot(neighbor[0] - pixel[0], neighbor[1] - pixel[1])
                next_distance = distance + step
                if next_distance > merge_radius or next_distance >= distances.get(
                    neighbor, float("inf")
                ):
                    continue
                distances[neighbor] = next_distance
                heappush(frontier, (next_distance, neighbor))
        neighborhoods.append(set(distances))

    owners: dict[Pixel, list[int]] = {}
    for index, neighborhood in enumerate(neighborhoods):
        for pixel in sorted(neighborhood):
            for other in owners.get(pixel, ()):
                union(index, other)
            owners.setdefault(pixel, []).append(index)

    groups: dict[int, set[Pixel]] = {}
    for index, neighborhood in enumerate(neighborhoods):
        groups.setdefault(find(index), set()).update(neighborhood)
    return [groups[root] for root in sorted(groups)]


def _region_representative(
    support: set[Pixel], radius_map: np.ndarray | None, method: str
) -> tuple[Pixel, float]:
    pixels = sorted(support)
    points = np.asarray(pixels, dtype=float)
    if radius_map is None:
        radii = np.zeros(len(pixels), dtype=float)
    else:
        radii = np.asarray([radius_map[row, column] for row, column in pixels], dtype=float)
    weights = radii if float(radii.sum()) > 0.0 else np.ones(len(pixels), dtype=float)
    if method == "radius-weighted-centroid":
        center = np.average(points, axis=0, weights=weights)
        distances = np.sum((points - center) ** 2, axis=1)
    else:
        distances = np.asarray(
            [np.sum(np.linalg.norm(points - point, axis=1) * weights) for point in points]
        )
    representative = pixels[int(np.argmin(distances))]
    local_radius = float(np.average(radii, weights=weights)) if len(radii) else 0.0
    return representative, local_radius


def _trace_graph_edges(
    node_supports: list[set[Pixel]],
    node_pixels: list[Pixel],
    adjacency: dict[Pixel, tuple[Pixel, ...]],
    radius_map: np.ndarray | None,
    confidence_map: np.ndarray,
) -> tuple[list[SkeletonEdge], list[set[tuple[Pixel, Pixel]]]]:
    support_owner = {
        pixel: node_id for node_id, support in enumerate(node_supports) for pixel in support
    }
    ports: list[set[tuple[Pixel, Pixel]]] = [set() for _ in node_supports]
    for node_id, support in enumerate(node_supports):
        for pixel in sorted(support):
            for neighbor in adjacency[pixel]:
                if support_owner.get(neighbor) != node_id:
                    ports[node_id].add((pixel, neighbor))

    visited: set[frozenset[Pixel]] = set()
    edges = []
    for start_node, node_ports in enumerate(ports):
        for inside, outside in sorted(node_ports):
            first_key = frozenset((inside, outside))
            if first_key in visited:
                continue
            chain = [inside, outside]
            visited.add(first_key)
            previous, current = inside, outside
            while current not in support_owner:
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
            end_node = support_owner.get(current)
            if end_node is None:
                continue
            xy = np.asarray(
                [
                    (float(node_pixels[start_node][1]), float(node_pixels[start_node][0])),
                    *[(float(column), float(row)) for row, column in chain[1:-1]],
                    (float(node_pixels[end_node][1]), float(node_pixels[end_node][0])),
                ],
                dtype=float,
            )
            length = float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())
            radius_values = [
                _radius_and_confidence(pixel, radius_map, confidence_map)[0] for pixel in chain
            ]
            confidence_values = [
                _radius_and_confidence(pixel, radius_map, confidence_map)[1] for pixel in chain
            ]
            edges.append(
                SkeletonEdge(
                    a=start_node,
                    b=end_node,
                    xy=xy,
                    length_px=length,
                    mean_radius_px=float(np.mean(radius_values)),
                    confidence=float(np.mean(confidence_values)),
                )
            )
    return edges, ports


def build_skeleton_graph(
    observed_ink: ArrayLike,
    *,
    min_spur_length_px: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    junction_options: JunctionRegionOptions | None = None,
    already_skeleton: bool = False,
) -> SkeletonGraph:
    """Build a graph from observed ink or an already-thinned skeleton.

    Parameters
    ----------
    observed_ink : numpy.typing.ArrayLike
        Two-dimensional boolean image or finite numeric image containing only
        zero and one values.
    min_spur_length_px : float
        Remove endpoint-to-junction branches strictly shorter than this
        threshold, in pixels. Zero preserves all spurs.
    radius : numpy.typing.ArrayLike or None
        Optional finite, nonnegative radius map with the same shape as the image.
        If omitted, graph node and edge radius values are zero.
    confidence : numpy.typing.ArrayLike or None
        Optional finite confidence map with the same shape and values in
        ``[0, 1]``. If omitted, confidence values are one.
    already_skeleton : bool
        If false, skeletonize the observed ink. If true, use the supplied pixels
        directly as an already-thinned skeleton.

    Returns
    -------
    SkeletonGraph
        Immutable topology graph whose public coordinates are ``(x, y) =
        (column, row)`` in pixel units.

    Raises
    ------
    ValueError
        If the image, radius map, confidence map, or spur threshold is invalid.
    ImportError
        If skeletonization is requested but scikit-image is unavailable.

    Notes
    -----
    This lower-level constructor does not derive radius from surrounding ink.
    Radius derivation for masks is provided by ``graph_from_mask()``. SciPy and
    scikit-image are imported lazily only by operations that need them. Raster
    diagonal adjacency uses the bridge-aware rule: a diagonal connects only
    when neither orthogonal bridge pixel is foreground.
    """
    ink = _binary_image(observed_ink, name="observed ink")
    if junction_options is not None and not isinstance(junction_options, JunctionRegionOptions):
        raise TypeError("junction_options must be JunctionRegionOptions")
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

    if already_skeleton:
        thin = ink.copy()
    else:
        try:
            from skimage.morphology import skeletonize
        except ImportError as error:
            raise ImportError(
                "skeletonizing observed ink requires scikit-image; install skeletonpaths[image]"
            ) from error
        thin = skeletonize(ink)
    thin = prune_spurs(thin, min_spur_length_px)
    adjacency = _pixel_adjacency(thin)
    degrees = {pixel: len(neighbors) for pixel, neighbors in adjacency.items()}
    components = _components(adjacency)
    junction_options = junction_options or JunctionRegionOptions()
    raw_seeds = sorted(pixel for pixel, degree in degrees.items() if degree > 2)
    region_supports = _junction_region_supports(
        raw_seeds, adjacency, degrees, radius, junction_options
    )
    region_specs = []
    for support in region_supports:
        representative, region_radius = _region_representative(
            support, radius, junction_options.representative
        )
        region_confidence = float(
            np.mean([confidence_map[row, column] for row, column in sorted(support)])
        )
        region_specs.append((representative, support, True, region_radius, region_confidence))

    absorbed = set().union(*(support for support in region_supports)) if region_supports else set()
    node_specs = list(region_specs)
    for pixel, degree in sorted(degrees.items()):
        if degree != 2 and pixel not in absorbed:
            node_specs.append((pixel, {pixel}, False, 0.0, 0.0))

    for component in components:
        if not any(pixel in absorbed or degrees[pixel] != 2 for pixel in component):
            anchor = min(component)
            node_specs.append((anchor, {anchor}, False, 0.0, 0.0))

    node_specs.sort(key=lambda item: (item[0], not item[2]))
    node_pixels = [spec[0] for spec in node_specs]
    node_supports = [spec[1] for spec in node_specs]
    edges, ports = _trace_graph_edges(node_supports, node_pixels, adjacency, radius, confidence_map)
    nodes = []
    junction_regions = []
    for node_id, (pixel, support, is_region, region_radius, region_confidence) in enumerate(
        node_specs
    ):
        if is_region:
            radius_value = region_radius
            confidence_value = region_confidence
            port_count = len(ports[node_id])
            junction_regions.append(
                JunctionRegion(
                    node_id=node_id,
                    xy=(float(pixel[1]), float(pixel[0])),
                    radius_px=radius_value,
                    support_pixels=tuple(sorted(support)),
                    port_count=port_count,
                    confidence=confidence_value,
                )
            )
        else:
            radius_value, confidence_value = _radius_and_confidence(pixel, radius, confidence_map)
            port_count = len(ports[node_id])
        nodes.append(
            SkeletonNode(
                id=node_id,
                xy=(float(pixel[1]), float(pixel[0])),
                degree=port_count,
                radius_px=radius_value,
                confidence=confidence_value,
            )
        )

    return SkeletonGraph(
        tuple(nodes), tuple(edges), tuple(junction_regions), raw_junction_seed_count=len(raw_seeds)
    )


def graph_from_skeleton(
    skeleton: ArrayLike,
    *,
    min_spur_length: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    junction_options: JunctionRegionOptions | None = None,
) -> SkeletonGraph:
    """Build a graph from an already-thinned binary skeleton.

    Parameters
    ----------
    skeleton : numpy.typing.ArrayLike
        Two-dimensional boolean image or finite numeric image containing only
        zero and one values. It is used directly and is not skeletonized.
    min_spur_length : float
        Remove endpoint-to-junction branches strictly shorter than this
        threshold, in pixels. Zero preserves all spurs.
    radius : numpy.typing.ArrayLike or None
        Optional finite, nonnegative radius map matching ``skeleton``. If
        omitted, graph radius values are zero.
    confidence : numpy.typing.ArrayLike or None
        Optional finite map matching ``skeleton`` with values in ``[0, 1]``. If
        omitted, confidence values are one.

    Returns
    -------
    SkeletonGraph
        Immutable topology graph with public coordinates in ``(x, y) =
        (column, row)`` pixel units.

    Raises
    ------
    ValueError
        If the skeleton or supplied maps are invalid.

    Notes
    -----
    This is the preferred lightweight entry point for pre-thinned data. It does
    not require SciPy or scikit-image, does not skeletonize, and does not derive
    radius from surrounding ink.

    See Also
    --------
    graph_from_mask : Build a graph from a binary mask with optional image processing.
    build_skeleton_graph : Lower-level graph constructor.
    """
    return build_skeleton_graph(
        skeleton,
        min_spur_length_px=min_spur_length,
        radius=radius,
        confidence=confidence,
        junction_options=junction_options,
        already_skeleton=True,
    )
