# API reference

The package root, `skeletonpaths`, is the supported import surface. The explicit directives below document the public exports. Function signatures and object definitions are generated from Python objects, not maintained in prose.

## Graph construction

```{eval-rst}
.. autofunction:: skeletonpaths.graph_from_skeleton
```

```{eval-rst}
.. autofunction:: skeletonpaths.graph_from_mask
```

```{eval-rst}
.. autofunction:: skeletonpaths.build_skeleton_graph
```

```{eval-rst}
.. autofunction:: skeletonpaths.prune_spurs
```

## Mask analysis and edge covering

```{eval-rst}
.. autofunction:: skeletonpaths.analyze_mask
```

```{eval-rst}
.. autofunction:: skeletonpaths.covering_walk
```

## Route enumeration, ranking, and selection

```{eval-rst}
.. autofunction:: skeletonpaths.prepare_topology_paths
```

```{eval-rst}
.. autofunction:: skeletonpaths.rank_paths
```

```{eval-rst}
.. autofunction:: skeletonpaths.select_path
```

## Data models

```{eval-rst}
.. autoclass:: skeletonpaths.SkeletonNode
```

```{eval-rst}
.. autoclass:: skeletonpaths.SkeletonEdge
```

```{eval-rst}
.. autoclass:: skeletonpaths.SkeletonGraph
```


```{eval-rst}
.. autoclass:: skeletonpaths.SkeletonAnalysis
```

```{eval-rst}
.. autoclass:: skeletonpaths.SkeletonImage
```

```{eval-rst}
.. autoclass:: skeletonpaths.SkeletonWalk
```

```{eval-rst}
.. autoclass:: skeletonpaths.TopologyRoute
```

```{eval-rst}
.. autoclass:: skeletonpaths.SkeletonPath
```

```{eval-rst}
.. autoclass:: skeletonpaths.PathScore
```

```{eval-rst}
.. autoclass:: skeletonpaths.PathSelection
```

```{eval-rst}
.. autoclass:: skeletonpaths.TopologyPathInventory
```

```{eval-rst}
.. autoclass:: skeletonpaths.PathRankingPolicy
```

```{eval-rst}
.. autoclass:: skeletonpaths.PathSearchLimits
```

## Constants

`DEFAULT_MAX_PATHS` is the legacy default completed-route bound per route kind. The default search object also sets the independent expanded-state bound.

```{eval-rst}
.. autodata:: skeletonpaths.DEFAULT_MAX_PATHS
```

```{eval-rst}
.. autodata:: skeletonpaths.DEFAULT_RANKING_POLICY
```

```{eval-rst}
.. autodata:: skeletonpaths.DEFAULT_SEARCH_LIMITS
```

## Errors

```{eval-rst}
.. autoclass:: skeletonpaths.DisconnectedGraphError
```

```{eval-rst}
.. autoclass:: skeletonpaths.NoFeasiblePathError
```

```{eval-rst}
.. autoclass:: skeletonpaths.PathSearchLimitError
```

## Deprecated compatibility wrappers

These names remain available for compatibility and emit `DeprecationWarning`. Prefer `rank_paths()` and `select_path()`.

```{eval-rst}
.. autofunction:: skeletonpaths.rank_topology_paths
```

```{eval-rst}
.. autofunction:: skeletonpaths.select_topology_path
```
