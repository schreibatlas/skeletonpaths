# SkeletonPaths

SkeletonPaths converts binary masks and precomputed skeletons into compact topology graphs and candidate routes. It provides route ranking and selection without claiming that a selected route is the true drawing order or physical stroke direction.

Raster topology and route-selection policy belong to SkeletonPaths. Generic polyline geometry belongs to PlanarCurve. PlanarCurve is installed as a runtime dependency, so no separate install step is required.

## Install

Install the core package for pre-thinned skeletons:

```bash
python -m pip install skeletonpaths
```

Install the `image` extra to process masks, skeletonize ink, derive radius maps, or filter small mask components:

```bash
python -m pip install "skeletonpaths[image]"
```

The core dependencies are NumPy and PlanarCurve. SciPy and scikit-image are optional and imported only when image-processing operations need them. `graph_from_skeleton()` and package import work without the image extra.

For development and tests:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

```python
import numpy as np
from skeletonpaths import graph_from_skeleton, select_path

skeleton = np.zeros((9, 9), dtype=bool)
skeleton[4, 1:8] = True

graph = graph_from_skeleton(skeleton)
selection = select_path(graph, path_kind="open", expected_cycles=0)

print(graph.endpoint_count)  # 2
print(selection.path.xy)  # public coordinates are (x, y)
print(selection.ambiguous)
```

For a binary mask, use `graph_from_mask(mask)`. It skeletonizes the mask, derives a radius map from the source mask when one is not supplied, and retains all connected components by default.

## Processing pipeline

1. Supply a two-dimensional binary mask or already-thinned skeleton. Boolean arrays and finite numeric arrays containing only `0` and `1` are accepted. NaN, infinity, and other numeric values are rejected.
2. `graph_from_mask()` optionally removes small components, derives radius values from the source mask with a Euclidean distance transform when no radius map is supplied, and skeletonizes the remaining mask. `graph_from_skeleton()` skips skeletonization and defaults radius values to zero when no radius map is supplied.
3. Raster pixels are converted to an undirected topology graph. Pixels whose degree differs from two remain graph nodes. An all-degree-two component receives a deterministic representative node. Degree-two chains become graph edges. Short spurs are preserved unless `min_spur_length` is explicitly set above zero.
4. Route enumeration produces `TopologyRoute` records. `rank_paths()` scores feasible routes, and `select_path()` returns the selected route with selection-context ambiguity metadata.
5. The selected route's `xy` array can be passed to PlanarCurve for generic curve resampling or geometry operations.

## Coordinates and raster topology

Input arrays use image indexing `[row, column]`. Public coordinates use `(x=column, y=row)`, in pixel units.

Pixel adjacency uses orthogonal neighbors and permits a diagonal neighbor only when neither orthogonal bridge pixel is foreground. This bridge-aware rule is neither plain four-connectivity nor naïve eight-connectivity, and it determines graph topology. Adjacent junction pixels remain separate graph nodes. Graph construction preserves the input topology by default because spur pruning defaults to zero.

`graph_from_mask()` uses eight-neighbor connected-component labeling when `min_component_area` is greater than zero. Components smaller than the requested area are removed before skeletonization. A supplied `radius` map must match the image shape and contain finite nonnegative values. A supplied `confidence` map must match the image shape and contain values between zero and one.

## Data model

The public models are frozen. Graph and path collections are tuples, graph and path coordinate arrays are read-only, and inventory mappings are immutable.

- `SkeletonGraph` contains nodes and edges, with `component_count`, `cycle_count`, `endpoint_count`, and `junction_count` graph diagnostics.
- `SkeletonNode` records its integer ID, `(x, y)` coordinate, degree, radius in pixels, and confidence.
- `SkeletonEdge` records endpoint node IDs, ordered `(x, y)` geometry, length in pixels, mean radius, and confidence.
- `TopologyRoute` records an ordered edge sequence, start and end node IDs, and route-level cycle count. Routes are undirected graph traversals with an explicit orientation for geometry assembly.
- `SkeletonPath` contains assembled route geometry, edge IDs, oriented endpoint IDs, length, measured confidence, route cycle count, and `PathScore`. It does not contain selection ambiguity flags.
- `PathScore` reports guide distance in pixels, ordered-endpoint error in pixels, measured confidence, expected-length error in pixels, and sampled turning cost in squared radians. Measurements that do not apply are `None`.
- `PathSelection` contains the selected `path`, whether a competing route is ambiguous, whether the same route has an ambiguous orientation, and `feasible_path_count`.
- `TopologyPathInventory` stores enumerated routes by the requested path kinds for reuse during ranking.


`path_kind` selects the route topology:

- `"open"` selects endpoint-to-endpoint routes with no route-level cycle.
- `"loop"` selects closed cycles.
- `"open-with-loop"` selects endpoint-to-endpoint routes containing exactly one route-level cycle.

`expected_cycles` constrains each route. It does not compare a route with the graph's total cycle count. `SkeletonGraph.cycle_count` remains a graph-level diagnostic.

## Ranking policy and ambiguity

`rank_paths()` and `select_path()` accept a frozen `PathRankingPolicy`. The default is `DEFAULT_RANKING_POLICY`:

| Policy field | Default | Meaning |
| --- | ---: | --- |
| `guide_samples` | 64 | Samples used for symmetric guide distance |
| `turning_samples` | 64 | Samples used for turning cost |
| `guide_tie_tolerance_px` | 1e-9 | Guide-distance tolerance for endpoint-order tie-breaking |
| `ambiguity_guide_distance_px` | 0.5 | Maximum guide-distance difference treated as overlapping evidence |
| `ambiguity_endpoint_order_px` | 0.5 | Maximum ordered-endpoint difference treated as overlapping evidence |
| `ambiguity_confidence` | 0.05 | Maximum measured-confidence difference treated as overlapping evidence |
| `ambiguity_length_error_px` | 1.0 | Maximum expected-length-error difference treated as overlapping evidence |
| `ambiguity_turning_cost` | 0.1 | Turning-cost tolerance when turning is explicitly used as ambiguity evidence |
| `turning_cost_is_evidence` | `False` | Whether turning cost may reduce route ambiguity |

With `candidate_xy`, ranking compares symmetric guide distance first. Endpoint order breaks guide ties within `guide_tie_tolerance_px`, followed by measured confidence, expected-length error, turning cost, and edge IDs. The tie tolerance is applied directly. Guide distances are not rounded to decimal places. Without a guide, measured confidence is the primary score. Route confidence is the length-weighted mean of its edge confidences.

Ambiguity compares score evidence using the configured tolerances. Turning cost is a deterministic ranking tie-breaker, but by default it does not make the selection appear more certain. Set `turning_cost_is_evidence=True` only when that interpretation is appropriate for the application. `ambiguous` concerns competing edge routes; `orientation_ambiguous` concerns reversed orientations of the selected route. Neither flag changes measured confidence.

Candidate geometry and `expected_endpoints` use `(x, y)` coordinates. Endpoint feasibility uses `endpoint_tolerance_px`, which defaults to three pixels. Candidate alignment or endpoint order does not establish physical drawing direction.

## Search limits and route inventories

Exhaustive route enumeration can grow exponentially on branched or cyclic graphs. `DEFAULT_SEARCH_LIMITS` is a frozen `PathSearchLimits` with `max_paths=10_000` and `max_states=100_000`. `max_paths` limits completed routes per route kind. `max_states` limits expanded DFS states. The limits apply independently to each requested route kind.


`rank_paths()` returns all feasible ranked routes by default, including both orientations of open routes. Pass a positive `limit` to return only the leading paths; every candidate is still scored to preserve exact ordering, but only the requested `SkeletonPath` objects are created. `select_path()` evaluates feasible alternatives for ambiguity while creating only the selected `SkeletonPath`. Search limits bound route enumeration, not the cost of downstream geometry scoring. Prepared inventories retain enumerated edge sequences in memory.

```python
from skeletonpaths import PathSearchLimits, prepare_topology_paths, select_path

limits = PathSearchLimits(max_paths=2_000, max_states=50_000)
inventory = prepare_topology_paths(
    graph,
    path_kinds=("open",),
    limits=limits,
)
selection = select_path(graph, path_inventory=inventory, limits=limits)
```

By default, `prepare_topology_paths()` prepares `"open"`, `"loop"`, and `"open-with-loop"`. Pass `path_kinds` to prepare only the kinds you need. A later ranking request must use a kind present in the inventory. Prepared inventories trade memory and initial enumeration time for reuse across repeated rankings.

When either search limit is exceeded, `PathSearchLimitError` is raised rather than returning a partial result. The exception exposes `path_kind`, `limit_name`, `limit_value`, and `observed`. The older `max_paths` keyword remains available on route preparation, ranking, and selection; do not pass it together with `limits`.

## Core API

The supported package-root exports are:

- Constants: `DEFAULT_MAX_PATHS`, `DEFAULT_RANKING_POLICY`, `DEFAULT_SEARCH_LIMITS`, `__version__`.
- Models and errors: `NoFeasiblePathError`, `PathRankingPolicy`, `PathScore`, `PathSearchLimitError`, `PathSearchLimits`, `PathSelection`, `SkeletonEdge`, `SkeletonGraph`, `SkeletonNode`, `SkeletonPath`, `TopologyPathInventory`, and `TopologyRoute`.
- Graph and image functions: `build_skeleton_graph`, `graph_from_mask`, `graph_from_skeleton`, and `prune_spurs`.
- Routing and ranking functions: `prepare_topology_paths`, `rank_paths`, and `select_path`.

`graph_from_skeleton()` is the lightweight entry point for pre-thinned images. `graph_from_mask()` uses the optional image dependencies. `build_skeleton_graph()` is the lower-level graph constructor and skeletonizes by default unless `already_skeleton=True`.

`rank_topology_paths()` and `select_topology_path()` are deprecated compatibility wrappers. Use `rank_paths()` and `select_path()` instead. The wrappers emit `DeprecationWarning`.

## PlanarCurve interoperability

SkeletonPaths owns raster connectivity, graph construction, route enumeration, and route-selection policy. PlanarCurve owns neutral polyline mathematics. Pass `selection.path.xy` to PlanarCurve when the selected raster route needs continuous-curve resampling or measurement. SkeletonPaths does not fit splines or Bezier curves and does not infer handwriting or pen semantics.

## What this package does not infer

- Graph topology and routes are undirected. An oriented route is an ordering for geometry, not evidence of physical direction.
- A selected route is not guaranteed to be the intended route. Inspect `PathSelection` ambiguity and the scores when alternatives matter.
- Measured confidence is propagated from input values. It is not a probability that a route is correct.
- SkeletonPaths does not infer pen lifts, stroke order, crossings, or application-specific meanings from raster topology.

## Provenance and stability

SkeletonPaths was extracted and adapted from InkGrammar. It has no InkGrammar runtime dependency and is intended for general raster-skeleton topology, not handwriting-specific behavior.

The package is pre-1.0. Public API changes may occur in minor releases while these contracts mature. Versions are derived from Git tags with `setuptools-scm`; tag releases with names such as `v0.1.0`. Source builds outside a Git checkout use the configured development fallback version.

## Development checks

```bash
pytest
ruff check .
ruff format --check .
python -m build
python -m twine check dist/*
```

## License

Apache-2.0.
