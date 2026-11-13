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

## Coordinate contract

Input arrays use image indexing `[row, column]`. Public geometry uses `(x=column, y=row)`.

## MVP API

- `graph_from_mask(...)`
- `graph_from_skeleton(...)`
- `prune_spurs(...)`
- `prepare_topology_paths(...)`
- `rank_paths(...)`
- `select_path(...)`
- `SkeletonNode`, `SkeletonEdge`, `SkeletonGraph`, `SkeletonPath`

Compatibility names from the extracted InkGrammar implementation are also exported: `build_skeleton_graph`, `rank_topology_paths`, and `select_topology_path`.

The initial path kinds are `"open"`, `"loop"`, and `"open-with-loop"`.

## Ambiguity

Skeleton topology is undirected. Candidate geometry and endpoint constraints can induce an orientation, but that orientation should not be interpreted automatically as physical drawing direction. `SkeletonPath.ambiguous` reports close competing selections.

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
