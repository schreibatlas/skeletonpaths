# Subpixel centerline reconstruction

SkeletonPaths keeps raster topology and continuous geometry separate. The default graph, paths, and walks remain pixel-based. Call `refine_graph_geometry()` only when downstream work needs a continuous estimate of the medial centerline.

## Pipeline

```text
binary mask
-> raster skeleton
-> topology graph
-> discrete route
-> subpixel edge observations
-> regularized continuous edge geometry
-> refined route/walk geometry
```

The continuous layer is additive. It does not change `SkeletonNode.xy`, `SkeletonEdge.xy`, `SkeletonPath.xy`, or `SkeletonWalk.xy`, nor does it alter graph connectivity, edge IDs, route ordering, or ambiguity metadata.

All coordinates are `(x, y) = (column, row)` in pixel units. Array samples are treated as values at pixel centers.

## Basic use

Pass a `SkeletonAnalysis` and, when available, a signed decision field from the segmentation stage:

```python
from skeletonpaths import analyze_mask, covering_walk, refine_graph_geometry, refined_walk

analysis = analyze_mask(mask)
geometry = refine_graph_geometry(analysis, decision_field=signed_field)
walk = covering_walk(analysis.graph)
walk_geometry = refined_walk(geometry, walk)
```
```

The decision field must be a finite 2D numeric array with the same shape as the mask. Positive values mean inside the stroke, negative values mean outside, and zero is the boundary. The field is sampled bilinearly along bounded edge-normal probes. It may be a signed distance field or another smooth, signed segmentation field. It should describe the same foreground used to produce `analysis`.

Without `decision_field`, SkeletonPaths derives a signed-distance field from the mask. This deterministic fallback uses SciPy and is reported as `binary-distance-fallback` in edge results. Install the image extra for the fallback and image analysis dependencies. PlanarCurve's SciPy-dependent spline fitting is loaded lazily when refinement is requested.

## Geometry and diagnostics

`RefinedSkeletonGeometry.edges` is in original graph edge order. Each `RefinedEdgeGeometry` retains its graph `edge_id` and contains:

- `xy`: subpixel samples of the fitted centerline;
- `tangent`: unit tangent vectors from the fitted curve's first derivative;
- `curvature`: signed curvature from the fitted curve's derivatives, in inverse pixel units;
- `radius_px`: estimated local stroke half-width;
- `confidence`: bounded evidence scores in `[0, 1]`;
- `source` and `diagnostics`: field provenance, rejected-observation reasons, shifts, residuals, fit counts, and bounded probe counts.

Confidence combines a boundary-gradient score and agreement between the observed half-width and the raster distance-transform radius. It is an evidence score, not a probability that a route or interpretation is correct. Weak gradients, competing crossings, radius disagreement, junction guards, and curvature-radius checks are reported as invalid reasons rather than silently treated as precise observations.

Shared topology nodes have one refined coordinate in `geometry.node_xy`, reused by all incident refined edges. Junction neighborhoods are guarded against ambiguous cross-sections. A pure loop may be fit as two open spline segments around a deterministic internal split; that split is not exposed as a graph node and does not change cycle or edge identity.

PlanarCurve's public `fit_polyline_spline()` API selects a bounded number of controls and provides the analytic differential geometry. `SubpixelCenterlineOptions` controls probe spacing and range, tangent window, fixed and radius-adaptive junction guards, the maximum guarded fraction from each edge end, confidence thresholds, fit passes, output spacing, curvature-radius rejection, and work budgets. Samples on junction-region support are always excluded. `max_refinement_samples` and `max_normal_probes` bound work; exceeding either raises `SubpixelReconstructionLimitError`.

## Refined walks

`refined_walk(geometry, walk)` follows the exact edge IDs and directions in the existing discrete walk. It does not fit a new spline through the whole route. Reverse traversal reverses the cached samples, negates tangent and signed curvature, and retains radius and confidence. Repeated traversals reuse the same edge geometry. The returned `RefinedWalkGeometry` keeps `edge_ids` and `edge_directions` for traceability. An optional `sample_count` resamples each edge traversal before shared endpoints are joined.

A refined route is still a geometric representation, not evidence of a writer's pen direction, stroke chronology, or intended route. Existing route ambiguity remains visible and unchanged.

## Limitations and InkGrammar handoff

This process estimates the medial geometry supported by the observed raster stroke. It cannot recover unavailable temporal information, prove historical pen direction, infer where a pen lifted, or resolve an ambiguous route. Smooth fitting never unions or splits topology. Junctions, touching strokes, loops, weak boundaries, and narrow features can have lower confidence or rejected observations. Inspect diagnostics when geometry quality matters.

Applications may pass refined geometry to InkGrammar as geometric evidence. That handoff does not make the geometry a historical trajectory or establish stroke order. SkeletonPaths has no InkGrammar runtime dependency and does not infer letter identity, handwriting scores, or stroke outlines.

## Bounded benchmark

Run the deterministic A-shaped crop benchmark from the repository root:

```console
python benchmarks/benchmark_subpixel.py --side 128 --repeats 3 --json
```

`--side` is bounded to 64..512 pixels and `--repeats` to 1..20. The report includes median runtime per crop, peak refinement samples and normal probes, median cross-section probes per edge point, median spline fits per edge, retained refined-geometry array bytes, analysis-array bytes, and peak Python allocator tracing. Array byte totals exclude Python and PlanarCurve object overhead. The benchmark uses a warm-up run before timing, a separate traced memory pass, and fixed refinement work limits; its timings are comparative measurements, not performance guarantees.
