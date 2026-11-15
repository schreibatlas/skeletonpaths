# Behavior contracts

This page collects concise integration guarantees. See the {doc}`../guide/graph-construction`, {doc}`../guide/path-selection`, and {doc}`../guide/ambiguity-and-ranking` guides for explanations.

## Coordinates and topology

Raster arrays use `[row, column]` indexing. Public geometry uses `(x, y) = (column, row)` in pixel units. Graph topology and edges are undirected evidence; deterministic node, edge, and endpoint storage order supports geometry assembly, not physical drawing order. `SkeletonPath` is a connected candidate route without repeated edge IDs. `SkeletonWalk` is an ordered traversal that may repeat edges to cover a connected graph.

{class}`skeletonpaths.SkeletonGraph` `cycle_count` is graph-level. {class}`skeletonpaths.TopologyRoute` and {class}`skeletonpaths.SkeletonPath` `cycle_count` values are route-level. `expected_cycles` constrains the route being considered, not every component of the graph.

## Immutability

Public models are frozen. Graph node and edge collections are tuples. {class}`skeletonpaths.SkeletonEdge` and {class}`skeletonpaths.SkeletonPath` coordinate arrays are read-only. `SkeletonAnalysis` owns read-only mask, skeleton, radius, and confidence arrays. A {class}`skeletonpaths.TopologyPathInventory` exposes an immutable mapping whose route collections are tuples.


`SkeletonWalk.xy` is read-only. `edge_ids` and `edge_directions` record every traversal in order, including repeats; `covered_edge_ids` is the sorted unique edge set, `repeated_edge_count` counts traversals beyond first coverage, and `length_px` includes repeats. `covering_walk()` is a deterministic traversal hypothesis for one connected graph. It honors requested endpoints, selects omitted endpoints deterministically, and raises `DisconnectedGraphError` rather than silently joining components.

## Empty input

An empty skeleton is valid and produces an empty `SkeletonGraph`. `analyze_mask()` returns matching empty mask and skeleton arrays, a zero-radius map, all-ones confidence evidence, and that graph.

## Validation

- Binary images are two-dimensional booleans or finite numeric arrays containing only zero and one.
- Radius maps match the image shape and contain finite, nonnegative values.
- Confidence maps match the image shape and contain finite values in `[0, 1]`.
- Candidate geometry is finite `(N, 2)` data with at least two distinct `(x, y)` points.
- Endpoint tangent vectors are finite nonzero xy vectors. Tangent tolerance is between zero and 180 degrees; tangent constraints rank routes by default and become hard feasibility constraints only when the policy opts in.
- Ranking policies and search limits validate their sample counts, tolerances, and bounds.
- Invalid inputs raise `ValueError` or `TypeError` as appropriate. Image-only dependency failures are raised lazily by the operations that need those dependencies.

## Determinism and stability

Traversal and tie-breakers are deterministic for a fixed package version, input, and policy. The default closed-graph walk start is the lexicographically smallest `(x, y, id)` node. The pre-1.0 project does not promise identical ordering across versions. Public APIs may change in minor releases before 1.0.

## Deprecated names

{func}`skeletonpaths.rank_topology_paths` is deprecated in favor of {func}`skeletonpaths.rank_paths`. {func}`skeletonpaths.select_topology_path` is deprecated in favor of {func}`skeletonpaths.select_path`. Both compatibility wrappers emit `DeprecationWarning` and forward to the supported functions.

See the {doc}`api` for the package-root imports and full object documentation.
