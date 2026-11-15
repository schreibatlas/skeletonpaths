# SkeletonPaths

SkeletonPaths converts binary masks and precomputed skeletons into compact topology graphs and ranked candidate routes. It does **not** infer physical drawing order or pen direction.

SkeletonPaths accepts images indexed as `[row, column]`, but all public geometric coordinates are returned as `(x, y) = (column, row)` in pixel units.

## Choose an input

| Input | Entry point | Installation |
| --- | --- | --- |
| Already-thinned skeleton | {func}`skeletonpaths.graph_from_skeleton` | Base package |
| Binary ink mask | {func}`skeletonpaths.graph_from_mask` or {func}`skeletonpaths.analyze_mask` | `skeletonpaths[image]` |

```python
import numpy as np
from skeletonpaths import graph_from_skeleton, select_path

skeleton = np.zeros((9, 9), dtype=bool)
skeleton[4, 1:8] = True
graph = graph_from_skeleton(skeleton)
selection = select_path(graph, path_kind="open")
print(selection.path.xy)  # (x, y) pixel coordinates
```

The selected route is an oriented geometry assembled from an undirected topology. Its ordering is not evidence of a stroke's physical direction.

```{toctree}
:maxdepth: 2
:hidden:

getting-started
examples
changelog
guide/graph-construction
guide/path-selection
guide/ambiguity-and-ranking
guide/search-limits
guide/planarcurve
reference/behavior-contracts
reference/api
```

Start with the {doc}`getting-started` guide. The conceptual guides explain {doc}`guide/graph-construction`, {doc}`guide/path-selection`, {doc}`guide/ambiguity-and-ranking`, and {doc}`guide/search-limits`. See the {doc}`reference/behavior-contracts` and {doc}`reference/api` for exact guarantees and the supported package-root API. See the {doc}`changelog` for release history.
