# Path selection

Graph construction supplies an undirected topology. Route enumeration produces connected edge sequences, and ranking evaluates only routes that satisfy the requested feasibility constraints. Ordered path geometry is useful for measurement and ranking, but does not establish physical direction.

## Route kinds

- `"open"`: endpoint-to-endpoint route with zero route-level cycles.
- `"loop"`: closed cycle.
- `"open-with-loop"`: endpoint-to-endpoint route containing exactly one route-level cycle.

`"open-with-loop"` describes cycles on the selected route, not a route that merely lies in a graph containing a loop. {class}`skeletonpaths.SkeletonGraph` `cycle_count` is a whole-graph diagnostic. {class}`skeletonpaths.TopologyRoute` and {class}`skeletonpaths.SkeletonPath` `cycle_count` values describe the route. Therefore, a loop in another graph component does not prevent selecting an open route with zero route-level cycles.

## `rank_paths()` and `select_path()`

{func}`skeletonpaths.rank_paths` returns ranked {class}`skeletonpaths.SkeletonPath` objects. Where applicable, open routes can appear in both orientations. Its optional `limit` controls how many final path objects are returned, but feasible alternatives are still scored so ordering stays exact.

{func}`skeletonpaths.select_path` returns a {class}`skeletonpaths.PathSelection` containing the selected path, ambiguity flags, and `feasible_path_count`. It materializes only the selected {class}`skeletonpaths.SkeletonPath`, but evaluates feasible alternatives because they can affect ambiguity.

## Feasibility constraints

`path_kind`, `expected_cycles`, and `expected_endpoints` constrain which routes are feasible. `endpoint_tolerance_px` controls the maximum distance from each specified endpoint. For `expected_endpoints=(start, end)`, the order matters: the first point constrains the route start and the second constrains its end. Each endpoint can be `None` to leave that side unconstrained.

`expected_cycles` constrains the selected route's cycle count, not {class}`skeletonpaths.SkeletonGraph` `cycle_count`.

A `candidate_xy` guide affects ranking, not feasibility. It cannot rescue a route that fails a hard endpoint or topology constraint. Candidate and expected endpoint coordinates use `(x, y)` pixel units. A guide must be a finite `(N, 2)` array with at least two distinct points. Symmetric guide distance measures geometric alignment; endpoint-order error can help resolve orientation when guide geometry ties. Guide geometry is not evidence of physical direction.

The hard-endpoint versus misleading-guide behavior is demonstrated by the canonical example:

```{literalinclude} ../../examples/03_guided_branch_selection.py
:language: python
```

## Expected length

When supplied, `expected_length_px` is ranking evidence. It is not a hard feasibility limit. When omitted, shorter paths are not automatically preferred.

## No feasible route

{func}`skeletonpaths.rank_paths` returns an empty tuple when no route remains feasible. {func}`skeletonpaths.select_path` raises {class}`skeletonpaths.NoFeasiblePathError` for the same situation.

The loop-routing example is kept in `examples/`:

```{literalinclude} ../../examples/04_loop_detection.py
:language: python
```

See {doc}`ambiguity-and-ranking` for effective score ordering and the precise meanings of selection ambiguity.
