# SkeletonPaths

SkeletonPaths converts binary masks and precomputed skeletons into topology graphs, routes, and bounded ranked stroke/traversal hypotheses. It reports ambiguity and evidence without claiming to recover true historical pen order or physical direction.

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


Use `analyze_mask(mask)` to return immutable mask, skeleton, radius, confidence, optional component labels, and graph evidence in a `SkeletonAnalysis`. The default radius is derived from the foreground; default confidence is all-ones evidence, not a probability. `covering_walk()` returns one deterministic traversal for a connected graph, while `rank_covering_walks()` returns bounded ranked multi-walk hypotheses. Neither API claims physical pen order.


For spur filtering, `analyze_mask()` and `graph_from_mask()` accept the legacy `min_spur_length` name and the preferred `min_spur_length_px` alias; do not supply both with non-default values.

## Documentation

The Sphinx guides and API reference explain graph construction, route selection, multi-stroke hypotheses, ranking and ambiguity, search limits, and the supported API.

## Processing pipeline

1. Supply a two-dimensional binary mask or already-thinned skeleton. Boolean arrays and finite numeric arrays containing only `0` and `1` are accepted. NaN, infinity, and other numeric values are rejected.
2. `graph_from_mask()` optionally removes small components, derives radius values from the source mask with a Euclidean distance transform when no radius map is supplied, and skeletonizes the remaining mask. `graph_from_skeleton()` skips skeletonization and defaults radius values to zero when no radius map is supplied.
3. Bridge-aware pixel adjacency is compressed into provisional junction regions and graph edges. A semantic cleanup stage considers short graph corridors, normalized local radius, port tangents, confidence, and crossing/endpoint protection instead of globally increasing the merge radius. The graph exposes raw, provisional, and semantic junction counts. A degree-two-only component receives a deterministic cycle anchor; endpoints remain distinct and self-edges count two ports.
4. Use `rank_paths()` and `select_path()` for simple route selection. Use `rank_covering_walks()` for bounded multi-walk hypotheses, including explicit repeats, junction pairing alternatives, and ambiguity evidence.
5. Pass candidate `xy` geometry and optional guide paths to PlanarCurve-backed scoring. Geometry and orientation help rank hypotheses but do not establish historical pen behavior.

## Coordinates and raster topology

Input arrays use image indexing `[row, column]`. Public coordinates use `(x=column, y=row)`, in pixel units.

Pixel adjacency uses orthogonal neighbors and permits a diagonal neighbor only when neither orthogonal bridge pixel is foreground. Raw junction seeds are skeleton pixels with degree greater than two. Nearby seeds are contracted into bounded semantic regions using geodesic neighborhoods scaled by the local ink radius; without a radius map, pre-thinned input contracts only directly or near-adjacent seeds conservatively. Endpoints are never absorbed. A region's representative node degree is the count of its boundary ports, with a self-edge contributing two ports. A single physical junction may be encountered multiple times in a traversal without becoming multiple graph nodes.


A second semantic cleanup stage can consolidate provisional regions connected by a short, tangent-continuous graph corridor with local radius and confidence support. It does not merge clearly independent crossings, and endpoints remain protected. `raw_junction_seed_count`, `provisional_junction_count`, and `semantic_junction_count` distinguish the three topology stages; `junction_count` remains the semantic count.


Graph edges represent undirected raster evidence. Their stored endpoint and edge order is deterministic for geometry assembly, not physical drawing order. `SkeletonPath` is a non-repeating route through part of a graph; `SkeletonWalk` is an ordered traversal that may repeat edges to cover a connected graph.

`graph_from_mask()` uses eight-neighbor connected-component labeling when `min_component_area` is greater than zero. Components smaller than the requested area are removed before skeletonization. A supplied `radius` map must match the image shape and contain finite nonnegative values. A supplied `confidence` map must match the image shape and contain values between zero and one.

## Data model

The public models are frozen. Graph and path collections are tuples, graph and path coordinate arrays are read-only, and inventory mappings are immutable.

- `SkeletonGraph` contains nodes, edges, and semantic `junction_regions`, with `component_count`, `cycle_count`, `endpoint_count`, `junction_count`, `raw_junction_seed_count`, `provisional_junction_count`, and `semantic_junction_count` diagnostics.
- `SkeletonAnalysis` contains owned read-only mask, skeleton, radius, and confidence arrays, optional component labels, graph, semantic junction regions, and raw, provisional, and semantic junction counts.
- `JunctionRegion` reports one representative node, center, local radius, absorbed support pixels, boundary-port count, and aggregate confidence. `JunctionRegionOptions` controls bounded region contraction.
- `SkeletonNode.degree` is semantic port degree for junctions. Self-edges count twice, once for each port.
- `SkeletonNode` records its integer ID, `(x, y)` coordinate, degree, radius in pixels, and confidence.
- `SkeletonEdge` records endpoint node IDs, ordered `(x, y)` geometry, length in pixels, mean radius, and confidence. Edge IDs assigned during enumeration are graph-local implementation identifiers, not stable across topology-model upgrades.
- `TopologyRoute` records an ordered edge sequence, start and end node IDs, and route-level cycle count. Routes are undirected graph traversals with an explicit orientation for geometry assembly.
- `SkeletonPath` contains assembled route geometry, edge IDs, oriented endpoint IDs, length, measured confidence, route cycle count, and `PathScore`. It does not contain selection ambiguity flags.
- `SkeletonWalk` records ordered `RouteStep` values, endpoints, geometry, covered edges, and repeats. Its `reversed()` operation explicitly reverses both traversal order and direction; partial walks support multi-stroke hypotheses.
- `PathScore` reports guide distance, ordered-endpoint error, endpoint-tangent error in degrees, measured confidence, expected-length error, and sampled turning cost in squared radians. Measurements that do not apply are `None`.
- `PathSelection` contains the selected `path`, whether a competing route is ambiguous, whether the same route has an ambiguous orientation, and `feasible_path_count`.
- `TopologyPathInventory` stores enumerated routes by the requested path kinds for reuse during ranking.
- `RouteStep` identifies one edge and its explicit `a-to-b` or `b-to-a` traversal direction.
- `JunctionPairing` records generic tangent-ranked branch pairs and unpaired edges, not physical truth.
- `StrokeHypothesis` contains topology traversal candidates, covered and uncovered edges, repeated-edge evidence, lift count, separate score dimensions, pairing candidates, route/orientation/component-order ambiguity, and an `orientation_relation` label.
- `StrokeSearchLimits` and `StrokeSearchPolicy` configure hard bounds and separate ranking penalties.


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
| `ambiguity_endpoint_tangent_deg` | 15.0 | Maximum tangent-error difference treated as overlapping evidence |
| `tangent_error_is_evidence` | `True` | Whether tangent error guides ranking and ambiguity |
| `endpoint_tangents_are_hard` | `False` | Whether tangent errors outside the supplied tolerance exclude routes |

With `candidate_xy`, ranking compares symmetric guide distance first. Endpoint order breaks guide ties within `guide_tie_tolerance_px`, followed by tangent error when enabled, measured confidence, expected-length error, turning cost, and edge IDs. Without a guide, enabled tangent error is considered before measured confidence. Endpoint tangent constraints are ranking evidence by default; `endpoint_tangents_are_hard=True` makes them feasibility constraints using `tangent_tolerance_deg`. Route confidence is the length-weighted mean of edge confidences.

Ambiguity compares score evidence using the configured tolerances, including tangent error when enabled. Turning cost is a deterministic ranking tie-breaker, but by default it does not make the selection appear more certain. `ambiguous` concerns competing edge routes; `orientation_ambiguous` concerns reversed orientations of the selected route. Tangent or endpoint evidence can resolve orientation ambiguity, but neither the route nor its orientation establishes physical drawing direction.

Candidate geometry, `expected_endpoints`, and `expected_endpoint_tangents` use `(x, y)` coordinates or vectors. Endpoint feasibility uses `endpoint_tolerance_px`; tangent scoring uses `tangent_tolerance_deg` only when the ranking policy enables hard tangent constraints. Alignment and ordered orientation remain route evidence, not physical drawing direction.

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

## Multi-stroke hypotheses

`rank_covering_walks(graph, ...)` returns a deterministic ranked tuple of stroke-set hypotheses. `stroke_hypotheses_from_analysis(analysis, ...)` uses the graph from a mask analysis. The existing singular `covering_walk()` remains available for clients that need one connected graph-covering traversal.

Each `StrokeHypothesisScore` preserves coverage error, uncovered length, repeat length, turning cost, junction pairing cost, lift cost, guide distance, and cycle error separately. `StrokeSearchPolicy` configures their ranking penalties. `JunctionPairing` candidates use local tangents and optional guides to rank alternatives without asserting which pairing is physically true. Disconnected components produce separate walks and set `component_order_ambiguous` because their temporal ordering is unavailable from the raster.

A repeat is evidence about a hypothesis only. `repeat_required_by_hypothesis` never means that the source was observed to be retraced. Orientation flags and component ordering likewise describe ambiguity in candidate explanations, not recovered history. If the requested result `limit` omits lower-ranked candidates, each returned hypothesis sets `truncated=True`.


`diversity="none"` preserves legacy global ranking. Opt into `diversity="stroke-count"` to retain the best full-coverage candidate for each stroke-count family, including the minimum-stroke candidate, before filling remaining slots by global rank. Scores and search limits are unchanged. This is candidate preservation, not a handwriting-semantic selection or a claim that any route is historically correct.

`orientation_variants(hypothesis)` returns the supplied traversal candidate and its global reversal. The reversal reverses both walk order and each walk, and its `orientation_relation` is labeled `"global-reversal"`. Unresolved orientation remains ambiguous; neither ordering is a recovered pen start or historical trace.

`StrokeSearchLimits` bounds each search stage. Defaults are:

| Limit | Default | Bound |
| --- | ---: | --- |
| `max_states` | 100,000 | Expanded pairing and scoring states |
| `max_hypotheses` | 1,000 | Completed hypotheses retained for ranking |
| `max_walk_steps` | 10,000 | Traversal steps scored in a hypothesis |
| `max_repeated_edges` | 8 | Repeated edge traversals in a hypothesis |
| `max_strokes` | 64 | Walks accepted in one hypothesis |
| `max_junction_pairings` | 1,000 | Pairing candidates and combinations |

`StrokeSearchLimitError` and `JunctionPairingLimitError` report the limit name, configured value, observed value, and search stage. PlanarCurve provides guide distance, arc-length, tangent, turn, and directed trajectory descriptor calculations.

Run the complete example with `python examples/11_stroke_hypotheses.py` after installing `skeletonpaths[image]`.

## Core API

The supported package-root exports are:

- Constants: `DEFAULT_MAX_PATHS`, `DEFAULT_RANKING_POLICY`, `DEFAULT_SEARCH_LIMITS`, `DEFAULT_STROKE_SEARCH_LIMITS`, `DEFAULT_STROKE_SEARCH_POLICY`, and `__version__`.
- Models and errors: `DisconnectedGraphError`, `JunctionPairing`, `JunctionPairingLimitError`, `JunctionRegion`, `JunctionRegionOptions`, `NoFeasiblePathError`, path scoring and limit types, `RouteStep`, `SkeletonAnalysis`, graph/image/path/walk models, `StrokeHypothesis`, `StrokeHypothesisScore`, `StrokeSearchLimitError`, `StrokeSearchLimits`, `StrokeSearchPolicy`, `TopologyPathInventory`, and `TopologyRoute`.
- Graph, image, and hypothesis functions: `analyze_mask`, `build_skeleton_graph`, `covering_walk`, `graph_from_mask`, `graph_from_skeleton`, `prune_spurs`, `orientation_variants`, `rank_covering_walks`, and `stroke_hypotheses_from_analysis`.
- Route functions: `prepare_topology_paths`, `rank_paths`, and `select_path`.

`graph_from_skeleton()` is the lightweight entry point for pre-thinned images. `graph_from_mask()` uses the optional image dependencies. `build_skeleton_graph()` is the lower-level graph constructor and skeletonizes by default unless `already_skeleton=True`.

`rank_topology_paths()` and `select_topology_path()` are deprecated compatibility wrappers. Use `rank_paths()` and `select_path()` instead. The wrappers emit `DeprecationWarning`.

## PlanarCurve interoperability

SkeletonPaths owns raster connectivity, graph construction, route enumeration, and route-selection policy. PlanarCurve owns neutral polyline mathematics. Pass `selection.path.xy` to PlanarCurve when the selected raster route needs continuous-curve resampling or measurement. SkeletonPaths does not fit splines or Bezier curves and does not infer handwriting or pen semantics.

## What this package does not infer

- Graph topology and routes are undirected. An oriented route is an ordering for geometry, not evidence of physical direction.
- A selected route is not guaranteed to be the intended route. Inspect `PathSelection` ambiguity and the scores when alternatives matter.
- Measured confidence is propagated from input values. It is not a probability that a route is correct.
- Static raster evidence cannot establish true pen lifts, historical stroke order, physical branch pairings, or drawing direction. The library returns generic alternatives and marks ambiguity instead.

## Provenance and stability

SkeletonPaths was extracted and adapted from InkGrammar. It has no InkGrammar runtime dependency and is intended for general raster-skeleton topology, not handwriting-specific behavior.

The package is pre-1.0, so behaviorally significant topology changes belong in a new minor release line, for example `0.2.x`. This upgrade contracts raw junction-pixel clusters into semantic regions and changes graph topology; graph-local edge IDs are implementation identifiers and are not stable across topology-model upgrades. Versions are derived from Git tags with `setuptools-scm`; tag releases with names such as `v0.1.0`. Source builds outside a Git checkout use the configured development fallback version.

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
