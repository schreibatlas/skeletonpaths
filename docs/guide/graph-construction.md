# Graph construction

SkeletonPaths turns a binary raster into an undirected topology graph. Graph edges are evidence of raster connectivity, not directed strokes; their deterministic storage order is for geometry assembly and is not physical drawing order. Raster arrays use `[row, column]`, while {class}`skeletonpaths.SkeletonNode` and {class}`skeletonpaths.SkeletonEdge` geometry and later route coordinates use `(x, y) = (column, row)` in pixel units.

## Accepted binary images

Both graph entry points accept a two-dimensional boolean image or a finite numeric image containing only `0` and `1`.

| Input | Accepted? |
| --- | --- |
| Boolean values | Yes |
| Finite numeric zero and one | Yes |
| NaN or infinity | No |
| A numeric value such as `2` | No |

Values are not interpreted as foreground merely because they are nonzero.

## Mask versus pre-thinned skeleton

| Behavior | {func}`skeletonpaths.graph_from_skeleton` | {func}`skeletonpaths.graph_from_mask` / {func}`skeletonpaths.analyze_mask` |
| --- | --- | --- |
| Input already thinned | Yes | No |
| Skeletonization | No | Yes |
| Automatic radius | No. Radius is zero if absent. | Yes. Uses a Euclidean distance transform if absent. |
| Component filtering | No | Optional `min_component_area`, before skeletonization |
| Image extra | Not required | Required for mask processing |
For {func}`skeletonpaths.graph_from_mask`, component filtering labels 8-neighbor mask components and removes components smaller than the requested area. The default `min_component_area=0` keeps every component. SciPy is needed to derive radius for a nonempty mask or when filtering is enabled. scikit-image is needed to skeletonize. Imports are lazy. Supplying a radius map avoids automatic radius derivation, but does not remove the skeletonization dependency.



`analyze_mask()` applies the same processing and returns a frozen `SkeletonAnalysis` containing owned read-only copies of the normalized mask, skeleton, radius, and confidence arrays, together with the graph. `graph_from_mask()` is the graph-only shortcut. Empty masks produce an empty graph and skeleton with a zero radius map.
{func}`skeletonpaths.graph_from_skeleton` assumes the input is already thinned. It does not infer radius from surrounding ink and can run without SciPy or scikit-image. {func}`skeletonpaths.build_skeleton_graph` is the lower-level constructor. With `already_skeleton=False` it skeletonizes and lazily imports scikit-image; with `already_skeleton=True` it uses the pixels directly. It does not derive a distance-transform radius.

## Pixel adjacency

Orthogonal foreground neighbors connect. A diagonal pair connects only when neither of the two orthogonal bridge pixels is foreground. This bridge-aware diagonal rule is neither plain four-connectivity nor naïve eight-connectivity. An orthogonal bridge suppresses the diagonal edge.

## Graph compression

- Every foreground pixel whose raster-topology degree is not two becomes a node.
- Degree-two pixel chains collapse into graph edges.
- An all-degree-two connected component receives a deterministic representative node.
- Adjacent junction pixels remain separate nodes.
- Edge length is the assembled polyline length in pixels.

Edge geometry is stored from endpoint node `a` to node `b`. This deterministic storage orientation supports geometry assembly and ranking; it does not imply physical drawing direction or traversal order.


`SkeletonPath` represents a connected candidate route with unique edge IDs. `SkeletonWalk` is separate and may repeat edge IDs in its ordered traversal. `covering_walk()` provides a deterministic connected traversal hypothesis and raises `DisconnectedGraphError` for disconnected graphs.

## Spur pruning

Topology is preserved by default. The minimum spur threshold defaults to zero, which is a no-op that returns an equivalent boolean copy. With a positive threshold, only endpoint-to-junction branches are candidates. A branch is pruned only when its length is **strictly less than** the threshold. Pruning repeats until stable. This does not delete arbitrary short graph edges.

See the canonical executable example:

```{literalinclude} ../../examples/02_spur_pruning.py
:language: python
```

## Radius and confidence maps

A supplied `radius` map must match the image shape, contain finite values, and be nonnegative. A supplied `confidence` map must match the shape, contain finite values, and lie in `[0, 1]`.

- A node's radius and confidence come from its pixel.
- An edge's mean radius and confidence are means over its edge-chain pixels.
- A path's measured confidence is the edge-length-weighted mean of its edge confidences.

When no confidence map is supplied, analysis returns an all-ones confidence map as generic foreground evidence, not a probability of route correctness. Graph nodes and edges therefore receive confidence one by default. When no radius map is supplied to the pre-thinned entry point, radius defaults to zero. Mask input derives radius automatically unless a radius map is provided.

The mask and confidence example is maintained in `examples/` and included here without copying its source:

```{literalinclude} ../../examples/05_mask_radius_confidence.py
:language: python
```


```{literalinclude} ../../examples/09_analyze_mask.py
:language: python
```

## Graph diagnostics

{class}`skeletonpaths.SkeletonGraph` exposes graph-level `component_count`, `cycle_count`, `endpoint_count`, and `junction_count`. The graph cycle diagnostic is the cyclomatic count `max(0, |E| - |V| + component_count)`. It describes the whole graph, not a route. See {doc}`path-selection` for route-level cycle constraints.

An empty skeleton is valid input and produces an empty graph.
