# SkeletonPaths

`SkeletonPaths` converts binary image masks or precomputed skeletons into compact topology graphs and ranked candidate paths.

It is deliberately domain-neutral: it exposes geometry, topology, candidate routes, ranking, and ambiguity without claiming that a selected path is the true drawing or pen direction.

## Install

```bash
pip install skeletonpaths
```

For development:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

```python
import numpy as np
from skeletonpaths import graph_from_skeleton, select_path

skeleton = np.zeros((9, 9), dtype=bool)
skeleton[4, 1:8] = True

graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
path = select_path(graph, path_kind="open", expected_cycles=0)

print(graph.endpoint_count)  # 2
print(path.xy)
```

From a binary mask, use `graph_from_mask(mask)`; scikit-image performs the skeletonization step.

`graph_from_mask` derives radius from the binary mask with a distance transform unless a radius map is supplied. Its `min_component_area` option filters small connected components and defaults to `0`, which keeps every component. `graph_from_skeleton` expects an already-thinned image and does not derive radius automatically.

## Coordinate contract

Input arrays use image indexing `[row, column]`. Public geometry uses `(x=column, y=row)`.

## MVP API

- `graph_from_mask(...)`
- `graph_from_skeleton(...)`
- `prune_spurs(...)`
- `prepare_topology_paths(...)`
- `rank_paths(...)`
- `select_path(...)`
- `PathScore`, `PathSearchLimitError`, `SkeletonNode`, `SkeletonEdge`, `SkeletonGraph`, `SkeletonPath`

Compatibility names from the extracted InkGrammar implementation are also exported: `build_skeleton_graph`, `rank_topology_paths`, and `select_topology_path`.

The initial path kinds are `"open"`, `"loop"`, and `"open-with-loop"`.

## Path ranking and ambiguity

With `candidate_xy`, route ranking uses symmetric guide distance first, endpoint orientation to break geometric ties, measured confidence next, then expected-length error, sampled turning cost, and edge IDs for deterministic tie-breaking. Without a guide, measured confidence leads. `PathScore` reports these measurements in pixel units, confidence, and squared radians for turning cost.

`expected_cycles` constrains each candidate route, not the whole graph's cycle count. `SkeletonGraph.cycle_count` remains a graph-level diagnostic. Topology enumeration is bounded by `max_paths` (default `10_000`); exceeding the limit raises `PathSearchLimitError`.

Skeleton topology is undirected. A selected orientation follows candidate geometry and endpoint constraints, but does not establish physical drawing direction. `SkeletonPath.ambiguous` reports competing routes, while `orientation_ambiguous` reports uncertainty between orientations of the same route. Neither flag changes measured confidence.

## Versioning

The package version is derived from Git tags with `setuptools-scm`; there is no hard-coded package version. Tag releases as, for example, `v0.1.0`.

Outside a Git checkout, source builds use the configured development fallback version.

## Development

```bash
pytest
python -m build
python -m twine check dist/*
```

## License

Apache-2.0.
