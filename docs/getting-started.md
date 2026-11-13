# Getting started

## Install

The base package supports pre-thinned skeleton input and does not require SciPy or scikit-image:

```bash
python -m pip install skeletonpaths
```

Install the optional image extra for mask skeletonization, automatic mask-radius derivation, or component filtering:

```bash
python -m pip install "skeletonpaths[image]"
```

## Build a graph from a skeleton

A skeleton is a two-dimensional binary image. Arrays use `[row, column]` indexing; public geometry uses `(x, y) = (column, row)` in pixel units.

```python
import numpy as np
from skeletonpaths import graph_from_skeleton, select_path

skeleton = np.zeros((9, 9), dtype=bool)
skeleton[4, 1:8] = True

graph = graph_from_skeleton(skeleton)
selection = select_path(graph, path_kind="open", expected_cycles=0)

print(graph.endpoint_count)  # 2
print(selection.path.xy)  # public coordinates are (x, y)
```

Raster pixels with degree other than two become graph nodes. Degree-two chains are compressed into edges. The graph is undirected, so a path's start and end order is for geometry assembly and ranking, not a physical traversal direction. Short spurs are preserved unless a positive pruning threshold is supplied.

The full executable source from `examples/01_basic_straight.py` is included below:

```{literalinclude} ../examples/01_basic_straight.py
:language: python
```

## Build a graph from a mask

Use `graph_from_mask()` for binary ink that has not yet been skeletonized:

```python
from skeletonpaths import graph_from_mask

graph = graph_from_mask(mask)
```

This workflow requires the `image` extra. It skeletonizes the mask and, when `radius` is omitted, derives a Euclidean distance-transform radius from the mask. Component filtering is opt-in. In contrast, `graph_from_skeleton()` uses pre-thinned pixels directly, does not derive radius, and assigns zero radius values when no radius map is supplied.

See {doc}`guide/graph-construction` for validation, dependency, and propagation details.

## Inspect a selection

{func}`skeletonpaths.select_path` returns a {class}`skeletonpaths.PathSelection`, not a {class}`skeletonpaths.SkeletonPath` directly:

```python
selection.path.xy
selection.path.length_px
selection.path.confidence
selection.ambiguous
selection.orientation_ambiguous
selection.feasible_path_count
```

`ambiguous` describes competing edge routes in this selection context. `orientation_ambiguous` describes whether the reverse orientation of the selected route remains indistinguishable. Both flags belong to {class}`skeletonpaths.PathSelection`, not {class}`skeletonpaths.SkeletonPath`; neither changes measured confidence, which is not a probability of correctness.

Continue with {doc}`guide/path-selection`, {doc}`guide/ambiguity-and-ranking`, or the {doc}`reference/api`.
