# Search limits and route inventories

Route enumeration can grow exponentially on branched or cyclic graphs. Limits bound route enumeration, and exceeding a limit raises {class}`skeletonpaths.PathSearchLimitError` instead of returning partial results.

## Default bounds

```python
DEFAULT_SEARCH_LIMITS.max_paths  # 10_000
DEFAULT_SEARCH_LIMITS.max_states  # 100_000
```

{class}`skeletonpaths.PathSearchLimits` `max_paths` bounds completed routes. `max_states` bounds expanded search states. Limits apply independently to each requested route kind. The exception reports `path_kind`, `limit_name`, `limit_value`, and `observed`.

The older `max_paths` keyword remains available for compatibility. `limits` and `max_paths` are mutually exclusive.

## Prepared inventories

{func}`skeletonpaths.prepare_topology_paths` enumerates selected route kinds once and returns a {class}`skeletonpaths.TopologyPathInventory`:

```python
inventory = prepare_topology_paths(
    graph,
    path_kinds=("open",),
)
```

An inventory belongs to the exact graph object used to create it. A later request for a route kind absent from the inventory raises `ValueError`. Selective inventories avoid enumerating unneeded kinds; the default prepares `"open"`, `"loop"`, and `"open-with-loop"`. Its mapping and route collections are immutable, while retaining the enumerated edge sequences in memory. This trades memory and initial enumeration cost for reuse during repeated ranking or selection.

The reusable inventory example is maintained as executable source in `examples/`:

```{literalinclude} ../../examples/06_inventory_reranking.py
:language: python
```

## Do not confuse the two `limit` controls

:::{admonition} Route enumeration versus returned objects
:class: important

- `PathSearchLimits.max_paths` bounds route enumeration for each requested route kind.
- {func}`skeletonpaths.rank_paths` bounds the number of final `SkeletonPath` objects returned.

The result `limit` does not prevent route enumeration. {func}`skeletonpaths.rank_paths` still scores all feasible candidates to preserve exact ordering, then materializes only the requested number of path objects.
:::

{func}`skeletonpaths.select_path` likewise considers feasible alternatives for ambiguity while materializing only the selected `SkeletonPath`. Search limits bound the enumeration stage, not every later geometry-scoring operation.
