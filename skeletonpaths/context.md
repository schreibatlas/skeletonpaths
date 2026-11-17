# Codecrate Context Pack

Root: `.`

Format: `codecrate.v4`

Layout: `full`

## How to Use This Pack

This pack is a read-only repository snapshot for analysis and patch proposals.

**Quick workflow**
1. **Directory Tree** (L90-103)
2. **Repository Guide** (L22-25)
3. **Symbol Index** (L104-207)
4. **Files** (L208-2891)

**Proposing changes**
- Prefer minimal unified diffs (`--- a/...` / `+++ b/...`) with repo-relative paths.

## Repository Guide

- Central modules: `model.py`, `core.py`, `graph.py`, `ranking.py`, `routing.py`

## Machine Header

```codecrate-machine-header
{"format":"codecrate.v4","manifest_sha256":"fef7c6175ae61e5ce45fd835b973dfdf871ff98333c8e53c0db0a900d5d7811f","repo_label":".","repo_slug":"repo"}
```

## Manifest

```codecrate-manifest
{
  "format": "codecrate.v4",
  "id_format_version": "sha1-8-upper:v1",
  "marker_format_version": "v1",
  "root": ".",
  "files": [
    {
      "path": "__init__.py",
      "line_count": 78,
      "sha256_original": "399ec2051b8798ecc1706b88f746ca0d6c59c1f236250f98410573c35e0bf141"
    },
    {
      "path": "_version.py",
      "line_count": 25,
      "sha256_original": "1e17fbac58501af4658b54c617e64a43d5643a8673f1da912c5808d5eec54e0c"
    },
    {
      "path": "core.py",
      "line_count": 61,
      "sha256_original": "728da38dcd7d5dabf96214df22918011c7c72f96bc6c7dcc0dd6fe9ff1af9098"
    },
    {
      "path": "graph.py",
      "line_count": 335,
      "sha256_original": "b59edbb7b202521b65da6230002b32dc19610d7fa23d1213a23282095c39fc51"
    },
    {
      "path": "image.py",
      "line_count": 147,
      "sha256_original": "af28cabb941ed65d3c045341501b642291397e219cc2a890705a4c75af600e15"
    },
    {
      "path": "model.py",
      "line_count": 852,
      "sha256_original": "3861dec32ee35aedc541a2afcc6ac6fa2878a5841e8d42449d6032410d807a81"
    },
    {
      "path": "ranking.py",
      "line_count": 657,
      "sha256_original": "c094ce349739699296dd88925cda954ccdd6a2b9ee4ed12cd1399c9a52f57862"
    },
    {
      "path": "routing.py",
      "line_count": 229,
      "sha256_original": "a0fe3f4920dc1422ed1c8ca31c93aa3ee5fe20c9d6e9e23ef7ef2eee60148a80"
    },
    {
      "path": "walk.py",
      "line_count": 253,
      "sha256_original": "a9fc287b5b2b736219979efc42d69608b86b41453a3210ce94c45ed5b321fd45"
    }
  ]
}
```

## Directory Tree

```text
├─ __init__.py
├─ _version.py
├─ core.py
├─ graph.py
├─ image.py
├─ model.py
├─ ranking.py
├─ routing.py
└─ walk.py
```

## Symbol Index

### `__init__.py` (L214-290)
<a id="file-init-py"></a>

### `_version.py` (L297-320)
<a id="file-version-py"></a>

### `core.py` (L327-386)
<a id="file-core-py"></a>

### `graph.py` (L393-726)
<a id="file-graph-py"></a>
- `_pixel_adjacency` → (L402-418)
- `_components` → (L421-437)
- `_binary_image` → (L440-452)
- `prune_spurs` → (L455-517)
- `_radius_and_confidence` → (L520-527)
- `build_skeleton_graph` → (L530-671)
- `graph_from_skeleton` → (L674-726)

### `image.py` (L733-878)
<a id="file-image-py"></a>
- `analyze_mask` → (L742-857)
- `graph_from_mask` → (L860-878)

### `model.py` (L885-1735)
<a id="file-model-py"></a>
- `class SkeletonNode` (L899-943)
- `class SkeletonEdge` (L947-1001)
- `class SkeletonGraph` (L1005-1078)
- `class SkeletonImage` (L1082-1113)
- `class SkeletonAnalysis` (L1117-1182)
- `class SkeletonWalk` (L1186-1316)
- `class PathScore` (L1320-1362)
- `class PathRankingPolicy` (L1366-1439)
- `class PathSearchLimits` (L1446-1468)
- `class NoFeasiblePathError` (L1474-1479)
- `class PathSearchLimitError` (L1482-1511)
- `class SkeletonPath` (L1530-1600)
- `class PathSelection` (L1604-1640)
- `class TopologyRoute` (L1644-1690)
- `class TopologyPathInventory` (L1694-1735)
- `SkeletonNode.__post_init__` → (L924-943)
- `SkeletonEdge.__post_init__` → (L975-1001)
- `SkeletonGraph.__post_init__` → (L1024-1038)
- `SkeletonGraph.component_count` → (L1041-1059)
- `SkeletonGraph.cycle_count` → (L1062-1068)
- `SkeletonGraph.endpoint_count` → (L1071-1073)
- `SkeletonGraph.junction_count` → (L1076-1078)
- `SkeletonImage.__post_init__` → (L1093-1113)
- `SkeletonAnalysis.__init__` → (L1128-1141)
- `SkeletonAnalysis.__post_init__` → (L1143-1166)
- `SkeletonAnalysis.component_count` → (L1169-1170)
- `SkeletonAnalysis.endpoint_count` → (L1173-1174)
- `SkeletonAnalysis.junction_count` → (L1177-1178)
- `SkeletonAnalysis.cycle_count` → (L1181-1182)
- `SkeletonWalk.__post_init__` → (L1205-1277)
- `SkeletonWalk._validate_graph` → (L1279-1316)
- `PathScore.__post_init__` → (L1350-1362)
- `PathRankingPolicy.__post_init__` → (L1415-1439)
- `PathSearchLimits.__post_init__` → (L1463-1468)
- `PathSearchLimitError.__init__` → (L1497-1511)
- `_resolve_search_limits` → (L1514-1526)
- `SkeletonPath.__post_init__` → (L1565-1600)
- `PathSelection.__post_init__` → (L1629-1640)
- `TopologyRoute.__post_init__` → (L1667-1690)
- `TopologyPathInventory.__post_init__` → (L1713-1735)

### `ranking.py` (L1742-2397)
<a id="file-ranking-py"></a>
- `class _ScoredRoute` (L1773-1776)
- `_normalized_tangents` → (L1779-1798)
- `_first_tangent` → (L1801-1813)
- `_endpoint_tangent_errors` → (L1816-1832)
- `_mean_tangent_error` → (L1835-1837)
- `_score_landscapes_overlap` → (L1840-1877)
- `_rank_candidates` → (L1880-2078)
- `_rank_candidates.tie_break_key` → (L2023-2041)
- `_materialize_path` → (L2081-2095)
- `rank_paths` → (L2098-2216)
- `select_topology_path` → (L2219-2230)
- `select_path` → (L2233-2384)
- `rank_topology_paths` → (L2387-2397)

### `routing.py` (L2404-2631)
<a id="file-routing-py"></a>
- `_other_node` → (L2420-2421)
- `_edge_route` → (L2424-2439)
- `_next_expansion_count` → (L2442-2454)
- `_open_paths` → (L2457-2514)
- `_loop_paths` → (L2517-2561)
- `prepare_topology_paths` → (L2564-2631)

### `walk.py` (L2638-2889)
<a id="file-walk-py"></a>
- `class DisconnectedGraphError` (L2648-2649)
- `_adjacency` → (L2652-2663)
- `_shortest_paths` → (L2666-2684)
- `_path_edges` → (L2687-2698)
- `_endpoints` → (L2701-2722)
- `_validate_endpoint` → (L2725-2733)
- `covering_walk` → (L2736-2889)

## Files

### `__init__.py` (L214-290)
<a id="src-init-py"></a>

```python
"""Skeleton graphs and candidate path extraction from binary masks."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .core import (
    DEFAULT_MAX_PATHS,
    DEFAULT_RANKING_POLICY,
    DEFAULT_SEARCH_LIMITS,
    DisconnectedGraphError,
    NoFeasiblePathError,
    PathRankingPolicy,
    PathScore,
    PathSearchLimitError,
    PathSearchLimits,
    PathSelection,
    SkeletonAnalysis,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonImage,
    SkeletonNode,
    SkeletonPath,
    SkeletonWalk,
    TopologyPathInventory,
    TopologyRoute,
    analyze_mask,
    build_skeleton_graph,
    covering_walk,
    graph_from_mask,
    graph_from_skeleton,
    prepare_topology_paths,
    prune_spurs,
    rank_paths,
    rank_topology_paths,
    select_path,
    select_topology_path,
)

try:
    __version__ = version("skeletonpaths")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "DEFAULT_MAX_PATHS",
    "DEFAULT_RANKING_POLICY",
    "DEFAULT_SEARCH_LIMITS",
    "DisconnectedGraphError",
    "NoFeasiblePathError",
    "PathRankingPolicy",
    "PathScore",
    "PathSearchLimitError",
    "PathSearchLimits",
    "PathSelection",
    "SkeletonAnalysis",
    "SkeletonEdge",
    "SkeletonGraph",
    "SkeletonImage",
    "SkeletonNode",
    "SkeletonPath",
    "SkeletonWalk",
    "TopologyPathInventory",
    "TopologyRoute",
    "__version__",
    "analyze_mask",
    "build_skeleton_graph",
    "covering_walk",
    "graph_from_mask",
    "graph_from_skeleton",
    "prepare_topology_paths",
    "prune_spurs",
    "rank_paths",
    "rank_topology_paths",
    "select_path",
    "select_topology_path",
]
```

### `_version.py` (L297-320)
<a id="src-version-py"></a>

```python
# file generated by vcs-versioning
# don't change, don't track in version control
from __future__ import annotations

__all__ = [
    "__version__",
    "__version_tuple__",
    "version",
    "version_tuple",
    "__commit_id__",
    "commit_id",
]

version: str
__version__: str
__version_tuple__: tuple[int | str, ...]
version_tuple: tuple[int | str, ...]
commit_id: str | None
__commit_id__: str | None

__version__ = version = '0.1.2'
__version_tuple__ = version_tuple = (0, 1, 2)

__commit_id__ = commit_id = 'gc977e6b1c'
```

### `core.py` (L327-386)
<a id="src-core-py"></a>

```python
"""Compatibility re-exports for the internal SkeletonPaths modules."""

from .graph import build_skeleton_graph, graph_from_skeleton, prune_spurs
from .image import analyze_mask, graph_from_mask
from .model import (
    DEFAULT_MAX_PATHS,
    DEFAULT_RANKING_POLICY,
    DEFAULT_SEARCH_LIMITS,
    NoFeasiblePathError,
    PathRankingPolicy,
    PathScore,
    PathSearchLimitError,
    PathSearchLimits,
    PathSelection,
    SkeletonAnalysis,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonImage,
    SkeletonNode,
    SkeletonPath,
    SkeletonWalk,
    TopologyPathInventory,
    TopologyRoute,
)
from .ranking import rank_paths, rank_topology_paths, select_path, select_topology_path
from .routing import prepare_topology_paths
from .walk import DisconnectedGraphError, covering_walk

__all__ = [
    "DEFAULT_MAX_PATHS",
    "DEFAULT_RANKING_POLICY",
    "DEFAULT_SEARCH_LIMITS",
    "DisconnectedGraphError",
    "NoFeasiblePathError",
    "PathRankingPolicy",
    "PathScore",
    "PathSearchLimitError",
    "PathSearchLimits",
    "PathSelection",
    "SkeletonAnalysis",
    "SkeletonEdge",
    "SkeletonGraph",
    "SkeletonImage",
    "SkeletonNode",
    "SkeletonPath",
    "SkeletonWalk",
    "TopologyPathInventory",
    "TopologyRoute",
    "analyze_mask",
    "build_skeleton_graph",
    "covering_walk",
    "graph_from_mask",
    "graph_from_skeleton",
    "prepare_topology_paths",
    "prune_spurs",
    "rank_paths",
    "rank_topology_paths",
    "select_path",
    "select_topology_path",
]
```

### `graph.py` (L393-726)
<a id="src-graph-py"></a>

```python
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


def build_skeleton_graph(
    observed_ink: ArrayLike,
    *,
    min_spur_length_px: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
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
        already_skeleton=True,
    )
```

### `image.py` (L733-878)
<a id="src-image-py"></a>

```python
from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .graph import _binary_image, graph_from_skeleton, prune_spurs
from .model import SkeletonAnalysis, SkeletonGraph


def analyze_mask(
    mask: ArrayLike,
    *,
    min_spur_length: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    min_component_area: int = 0,
) -> SkeletonAnalysis:
    """Skeletonize a binary mask and return its raster data and topology.

    Parameters
    ----------
    mask : numpy.typing.ArrayLike
        Two-dimensional boolean image or finite numeric image containing only
        zero and one values.
    min_spur_length : float
        Remove endpoint-to-junction branches strictly shorter than this
        threshold, in pixels. Zero preserves all spurs.
    radius : numpy.typing.ArrayLike or None
        Optional finite, nonnegative radius map matching ``mask``. If omitted,
        derive radius from the foreground with a Euclidean distance transform.
    confidence : numpy.typing.ArrayLike or None
        Optional finite confidence map matching ``mask`` with values in
        ``[0, 1]``. If omitted, the analysis confidence map is all ones.
        These values are generic evidence, not a probability.
    min_component_area : int
        Remove 8-neighbor mask components smaller than this pixel area before
        skeletonization. Zero keeps every component.

    Returns
    -------
    SkeletonAnalysis
        Owned read-only mask, skeleton, radius, and confidence arrays alongside the topology graph.

    Raises
    ------
    ValueError
        If the mask, component area, or supplied maps are invalid.
    ImportError
        If SciPy is unavailable for automatic radius derivation or requested
        component filtering, or scikit-image is unavailable for skeletonization.

    Notes
    -----
    Component filtering occurs before skeletonization and uses 8-neighbor
    component labeling. SciPy is required when radius is omitted for nonempty
    masks and when ``min_component_area`` is positive. Skeletonization requires
    scikit-image. These dependencies are imported lazily.
    """
    source = _binary_image(mask, name="mask")
    if (
        isinstance(min_component_area, bool)
        or not isinstance(min_component_area, (int, np.integer))
        or min_component_area < 0
    ):
        raise ValueError("minimum component area must be a nonnegative integer")
    if min_component_area > 0:
        try:
            from scipy.ndimage import label as label_components
        except ImportError as error:
            raise ImportError(
                "component filtering requires SciPy; install skeletonpaths[image]"
            ) from error
        labels, _ = label_components(source, structure=np.ones((3, 3), dtype=np.uint8))
        areas = np.bincount(labels.ravel())
        keep = areas >= min_component_area
        keep[0] = False
        source = keep[labels]

    radius_map: np.ndarray
    if radius is None:
        if source.any():
            try:
                from scipy.ndimage import distance_transform_edt
            except ImportError as error:
                raise ImportError(
                    "automatic mask radius requires SciPy; install skeletonpaths[image]"
                ) from error
            radius_map = distance_transform_edt(source)
        else:
            radius_map = np.zeros(source.shape, dtype=float)
    else:
        radius_map = np.asarray(radius, dtype=float)
        if (
            radius_map.shape != source.shape
            or not np.isfinite(radius_map).all()
            or np.any(radius_map < 0.0)
        ):
            raise ValueError("radius map must be finite, nonnegative, and match observed ink")

    if confidence is None:
        confidence_map = np.ones(source.shape, dtype=float)
    else:
        confidence_map = np.asarray(confidence, dtype=float)
        if (
            confidence_map.shape != source.shape
            or not np.isfinite(confidence_map).all()
            or np.any((confidence_map < 0.0) | (confidence_map > 1.0))
        ):
            raise ValueError("confidence map must be between zero and one and match observed ink")

    try:
        from skimage.morphology import skeletonize
    except ImportError as error:
        raise ImportError(
            "skeletonizing observed ink requires scikit-image; install skeletonpaths[image]"
        ) from error
    skeleton = prune_spurs(skeletonize(source), min_spur_length)
    graph = graph_from_skeleton(skeleton, radius=radius_map, confidence=confidence_map)
    return SkeletonAnalysis(
        mask=source,
        skeleton=skeleton,
        radius=radius_map,
        confidence=confidence_map,
        graph=graph,
    )


def graph_from_mask(
    mask: ArrayLike,
    *,
    min_spur_length: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    min_component_area: int = 0,
) -> SkeletonGraph:
    """Skeletonize a binary mask and build its topology graph.

    Use :func:`analyze_mask` when the skeleton and radius arrays are also needed.
    """
    return analyze_mask(
        mask,
        min_spur_length=min_spur_length,
        radius=radius,
        confidence=confidence,
        min_component_area=min_component_area,
    ).graph
```

### `model.py` (L885-1735)
<a id="src-model-py"></a>

```python
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
    arrays. Confidence is generic foreground evidence, not a probability that
    any graph route or traversal is correct.
    """

    mask: np.ndarray
    confidence: np.ndarray

    def __init__(
        self,
        mask: np.ndarray,
        skeleton: np.ndarray,
        radius: np.ndarray,
        confidence: np.ndarray,
        graph: SkeletonGraph,
    ) -> None:
        object.__setattr__(self, "mask", mask)
        object.__setattr__(self, "skeleton", skeleton)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "graph", graph)
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
        mask = np.array(mask, dtype=bool, copy=True)
        confidence = np.array(confidence, dtype=float, copy=True)
        mask.setflags(write=False)
        confidence.setflags(write=False)
        object.__setattr__(self, "mask", mask)
        object.__setattr__(self, "confidence", confidence)

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
            or covered_count != total_count
            or covered_edge_ids != tuple(range(total_count))
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
        elif len(points) != 1 or self.start_node != self.end_node or total_count != 0:
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
```

### `ranking.py` (L1742-2397)
<a id="src-ranking-py"></a>

```python
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


def _normalized_tangents(
    tangents: tuple[Point | None, Point | None] | None,
) -> tuple[np.ndarray | None, np.ndarray | None] | None:
    if tangents is None:
        return None
    if len(tangents) != 2:
        raise ValueError("expected endpoint tangents must contain two xy vectors or None")
    normalized = []
    for tangent in tangents:
        if tangent is None:
            normalized.append(None)
            continue
        vector = np.asarray(tangent, dtype=float)
        if vector.shape != (2,) or not np.isfinite(vector).all():
            raise ValueError("expected endpoint tangents must be finite xy vectors")
        magnitude = float(np.linalg.norm(vector))
        if magnitude <= 1e-12:
            raise ValueError("expected endpoint tangents must be nonzero vectors")
        normalized.append(vector / magnitude)
    return normalized[0], normalized[1]


def _first_tangent(xy: np.ndarray) -> np.ndarray | None:
    if len(xy) < 2:
        return None
    distances = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    total_length = float(distances.sum())
    if total_length <= 1e-12:
        return None
    target_distance = min(2.0, total_length / 2.0)
    sample_distances = np.concatenate(([0.0], np.cumsum(distances)))
    sample_index = min(int(np.searchsorted(sample_distances, target_distance)), len(xy) - 1)
    vector = xy[sample_index] - xy[0]
    magnitude = float(np.linalg.norm(vector))
    return vector / magnitude if magnitude > 1e-12 else None


def _endpoint_tangent_errors(
    xy: np.ndarray,
    expected: tuple[np.ndarray | None, np.ndarray | None] | None,
) -> tuple[float | None, float | None]:
    if expected is None:
        return None, None
    actual = (_first_tangent(xy), None)
    end_reverse_tangent = _first_tangent(xy[::-1])
    actual = (actual[0], -end_reverse_tangent if end_reverse_tangent is not None else None)
    errors = []
    for expected_tangent, actual_tangent in zip(expected, actual, strict=True):
        if expected_tangent is None or actual_tangent is None:
            errors.append(None)
            continue
        cosine = float(np.clip(np.dot(expected_tangent, actual_tangent), -1.0, 1.0))
        errors.append(float(np.degrees(np.arccos(cosine))))
    return errors[0], errors[1]


def _mean_tangent_error(errors: tuple[float | None, float | None]) -> float | None:
    measured = [error for error in errors if error is not None]
    return float(np.mean(measured)) if measured else None


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
    if (
        policy.tangent_error_is_evidence
        and first.endpoint_tangent_error_deg is not None
        and second.endpoint_tangent_error_deg is not None
        and abs(first.endpoint_tangent_error_deg - second.endpoint_tangent_error_deg)
        > policy.ambiguity_endpoint_tangent_deg
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
    expected_endpoint_tangents: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    tangent_tolerance_deg: float = 35.0,
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
    if not np.isfinite(tangent_tolerance_deg) or not 0.0 <= tangent_tolerance_deg <= 180.0:
        raise ValueError("tangent tolerance must be finite and between zero and 180 degrees")
    expected_tangents = _normalized_tangents(expected_endpoint_tangents)
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
        tangent_errors = _endpoint_tangent_errors(xy, expected_tangents)
        tangent_error = _mean_tangent_error(tangent_errors)
        if policy.endpoint_tangents_are_hard and any(
            expected is not None and (error is None or error > tangent_tolerance_deg)
            for expected, error in zip(
                expected_tangents or (None, None), tangent_errors, strict=True
            )
        ):
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
            endpoint_tangent_error_deg=tangent_error,
        )
        scored.append(_ScoredRoute(route, length, score))

    def tie_break_key(
        item: _ScoredRoute,
    ) -> tuple[float, float, float, float, float, tuple[int, ...], int, int]:
        route = item.route
        score = item.score
        return (
            score.endpoint_order_error_px if score.endpoint_order_error_px is not None else 0.0,
            (
                score.endpoint_tangent_error_deg
                if policy.tangent_error_is_evidence and score.endpoint_tangent_error_deg is not None
                else 0.0
            ),
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
                (
                    item.score.endpoint_tangent_error_deg
                    if policy.tangent_error_is_evidence
                    and item.score.endpoint_tangent_error_deg is not None
                    else 0.0
                ),
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
    expected_endpoint_tangents: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    tangent_tolerance_deg: float = 35.0,
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
    expected_endpoint_tangents : tuple or None
        Ordered start and end tangent vectors in xy coordinates. Either may be None.
    tangent_tolerance_deg : float
        Maximum angular error for hard tangent constraints, in degrees. It must be
        between zero and 180 degrees and is used only when the policy enables hard constraints.
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
    grouped by direct numeric tolerance, then endpoint-order error, tangent error
    when enabled by policy, measured confidence, expected-length error when present,
    turning cost, and deterministic route identity break ties. Without a guide,
    tangent error is considered before measured confidence when enabled, followed
    by expected-length error, turning cost, and route identity. Tangent evidence is
    ranking evidence by default; ``endpoint_tangents_are_hard`` opts into filtering
    routes outside ``tangent_tolerance_deg``. Tangents use samples separated by up
    to two pixels. Turning cost is normally only a tie-breaker. ``limit`` controls
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
        expected_endpoint_tangents=expected_endpoint_tangents,
        endpoint_tolerance_px=endpoint_tolerance_px,
        tangent_tolerance_deg=tangent_tolerance_deg,
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
    expected_endpoint_tangents: tuple[Point | None, Point | None] | None = None,
    endpoint_tolerance_px: float = 3.0,
    tangent_tolerance_deg: float = 35.0,
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
    expected_endpoint_tangents : tuple or None
        Ordered start and end tangent vectors in xy coordinates. Either may be None.
    tangent_tolerance_deg : float
        Maximum angular error for hard tangent constraints, in degrees, between zero
        and 180 degrees.
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
    indistinguishable within endpoint-order and enabled tangent evidence. Neither
    flag changes measured confidence. Candidate geometry and tangent constraints
    guide ranking and orientation but do not establish physical direction. See
    ``rank_paths()`` for ranking order and parameter semantics.

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
        expected_endpoint_tangents=expected_endpoint_tangents,
        endpoint_tolerance_px=endpoint_tolerance_px,
        tangent_tolerance_deg=tangent_tolerance_deg,
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
        endpoint_order_overlap = (
            selected_record.score.endpoint_order_error_px is None
            or record.score.endpoint_order_error_px is None
            or abs(
                selected_record.score.endpoint_order_error_px - record.score.endpoint_order_error_px
            )
            <= policy.ambiguity_endpoint_order_px
        )
        tangent_overlap = (
            not policy.tangent_error_is_evidence
            or selected_record.score.endpoint_tangent_error_deg is None
            or record.score.endpoint_tangent_error_deg is None
            or abs(
                selected_record.score.endpoint_tangent_error_deg
                - record.score.endpoint_tangent_error_deg
            )
            <= policy.ambiguity_endpoint_tangent_deg
        )
        if endpoint_order_overlap and tangent_overlap:
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
```

### `routing.py` (L2404-2631)
<a id="src-routing-py"></a>

```python
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
```

### `walk.py` (L2638-2889)
<a id="src-walk-py"></a>

```python
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
```
