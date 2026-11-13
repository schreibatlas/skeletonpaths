# Behavior contracts

This page collects concise integration guarantees. See the {doc}`../guide/graph-construction`, {doc}`../guide/path-selection`, and {doc}`../guide/ambiguity-and-ranking` guides for explanations.

## Coordinates and topology

Raster arrays use `[row, column]` indexing. Public geometry uses `(x, y) = (column, row)` in pixel units. Graph topology is undirected. Route start/end order exists for geometry assembly and ranking, not as evidence of physical drawing direction.

{class}`skeletonpaths.SkeletonGraph` `cycle_count` is graph-level. {class}`skeletonpaths.TopologyRoute` and {class}`skeletonpaths.SkeletonPath` `cycle_count` values are route-level. `expected_cycles` constrains the route being considered, not every component of the graph.

## Immutability

Public models are frozen. Graph node and edge collections are tuples. {class}`skeletonpaths.SkeletonEdge` `xy` and {class}`skeletonpaths.SkeletonPath` `xy` arrays are read-only. A {class}`skeletonpaths.TopologyPathInventory` exposes an immutable mapping whose route collections are tuples.

## Empty input

An empty skeleton is valid and produces an empty {class}`skeletonpaths.SkeletonGraph`.

## Validation

- Binary images are two-dimensional booleans or finite numeric arrays containing only zero and one.
- Radius maps match the image shape and contain finite, nonnegative values.
- Confidence maps match the image shape and contain finite values in `[0, 1]`.
- Candidate geometry is finite `(N, 2)` data with at least two distinct `(x, y)` points.
- Ranking policies and search limits validate their sample counts, tolerances, and bounds.
- Invalid inputs raise `ValueError` or `TypeError` as appropriate. Image-only dependency failures are raised lazily by the operations that need those dependencies.

## Determinism and stability

Traversal and tie-breakers are deterministic for a fixed package version, input, and policy. The pre-1.0 project does not promise identical ordering across versions. Public APIs may change in minor releases before 1.0.

## Deprecated names

{func}`skeletonpaths.rank_topology_paths` is deprecated in favor of {func}`skeletonpaths.rank_paths`. {func}`skeletonpaths.select_topology_path` is deprecated in favor of {func}`skeletonpaths.select_path`. Both compatibility wrappers emit `DeprecationWarning` and forward to the supported functions.

See the {doc}`api` for the package-root imports and full object documentation.
