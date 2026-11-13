# Examples

The scripts in `examples/` are the canonical executable examples. The guides include their source with Sphinx `literalinclude`, rather than maintaining copied code. Use this index to find the relevant script and explanation.

| Script | Topic | Guide |
| --- | --- | --- |
| `01_basic_straight.py` | Pre-thinned skeleton and first selection | {doc}`getting-started` |
| `02_spur_pruning.py` | Explicit opt-in spur pruning | {doc}`guide/graph-construction` |
| `03_guided_branch_selection.py` | Hard endpoints versus a misleading guide | {doc}`guide/path-selection` |
| `04_loop_detection.py` | Closed-loop route selection | {doc}`guide/path-selection` |
| `05_mask_radius_confidence.py` | Mask input, radius derivation, and confidence propagation | {doc}`guide/graph-construction` |
| `06_inventory_reranking.py` | Reuse of a selective route inventory | {doc}`guide/search-limits` |
| `07_planarcurve_interop.py` | PlanarCurve geometry interoperability | {doc}`guide/planarcurve` |
| `08_route_ambiguity.py` | Route ambiguity and guide-based disambiguation | {doc}`guide/ambiguity-and-ranking` |

Run examples from the repository root as documented in `examples/README.md`. Examples 04 and 05 use image-processing dependencies; install `skeletonpaths[image]` for those scripts. The scripts demonstrate topology and ranking behavior, not physical drawing order or pen direction.
