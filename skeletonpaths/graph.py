from collections import deque
from math import hypot

import numpy as np
from numpy.typing import ArrayLike

from .model import Pixel, SkeletonEdge, SkeletonGraph, SkeletonNode


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
    """Remove endpoint-to-junction branches shorter than the configured length."""
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


def build_skeleton_graph(
    observed_ink: ArrayLike,
    *,
    min_spur_length_px: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    already_skeleton: bool = False,
) -> SkeletonGraph:
    """Skeletonize observed ink and collapse degree-two pixel chains into graph edges."""
    ink = _binary_image(observed_ink, name="observed ink")
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
                radius_px=radius_value,
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
                    xy=xy,
                    length_px=length,
                    mean_radius_px=float(np.mean(radius_values)),
                    confidence=float(np.mean(confidence_values)),
                )
            )

    return SkeletonGraph(tuple(nodes), tuple(edges))


def graph_from_skeleton(
    skeleton: ArrayLike,
    *,
    min_spur_length: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
) -> SkeletonGraph:
    """Build a compact graph from an already-thinned 2-D skeleton."""
    return build_skeleton_graph(
        skeleton,
        min_spur_length_px=min_spur_length,
        radius=radius,
        confidence=confidence,
        already_skeleton=True,
    )
