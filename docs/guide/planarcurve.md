# PlanarCurve interoperability

SkeletonPaths and PlanarCurve have separate responsibilities.

SkeletonPaths owns:

- raster validation and mask/skeleton entry points,
- raster connectivity and graph construction,
- route enumeration and feasibility constraints,
- ranking policy and ambiguity metadata.

PlanarCurve owns neutral polyline geometry, including arclength resampling, polyline length, curve-to-curve distance, and turning geometry. A selected route's `selection.path.xy` can be passed to PlanarCurve when generic curve operations are needed.

An ordered route geometry is a representation for geometry assembly and ranking. It does not establish pen direction, drawing order, or stroke chronology.

SkeletonPaths does not perform spline or Bezier fitting, infer pen lifts or crossings, attach handwriting semantics, infer true stroke order, or infer physical direction. InkGrammar is provenance context only, not a runtime or conceptual dependency of the public API.

The executable interoperability example is the source of truth for the handoff:

```{literalinclude} ../../examples/07_planarcurve_interop.py
:language: python
```
