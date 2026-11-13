# Examples

These scripts demonstrate the public SkeletonPaths API. Each example runs only when executed as a script, so importing it does not print output or create files.

Run from the repository root:

```bash
python examples/01_basic_straight.py
python examples/02_spur_pruning.py
python examples/03_guided_branch_selection.py
python examples/04_loop_detection.py
python examples/05_mask_radius_confidence.py
python examples/06_inventory_reranking.py
python examples/07_planarcurve_interop.py
python examples/08_route_ambiguity.py
```

Examples 04 and 05 use image-processing dependencies. Install them with:

```bash
python -m pip install "skeletonpaths[image]"
```

PlanarCurve is already a SkeletonPaths runtime dependency and needs no separate installation.

| Script | Demonstrates | Expected invariant |
| --- | --- | --- |
| `01_basic_straight.py` | A straight pre-thinned skeleton and endpoint-constrained selection | Two endpoints and a six-pixel route |
| `02_spur_pruning.py` | Explicit spur removal | The short branch is removed only because a positive threshold is supplied |
| `03_guided_branch_selection.py` | Hard endpoint constraints with a misleading guide | The vertical endpoint-constrained route wins over the guide's branch preference |
| `04_loop_detection.py` | Closed-loop routing | The selected route has one cycle and matching start/end coordinates |
| `05_mask_radius_confidence.py` | Mask input, automatic radius derivation, and confidence propagation | Radius is derived without a supplied map and edge confidence reflects the input map |
| `06_inventory_reranking.py` | A selective open-route inventory reused with different endpoint constraints | One inventory supports multiple selections without enumerating other route kinds |
| `07_planarcurve_interop.py` | A bent raster route passed to PlanarCurve | Resampling preserves the route as ordinary polyline geometry with a measurable turn cost |
| `08_route_ambiguity.py` | Two equal routes and guide-based disambiguation | The unguided selection is ambiguous; the upper-route guide resolves it |

The scripts are executable examples, not a promise that a selected route represents physical drawing direction. See the main README for topology, ranking, ambiguity, and search-limit contracts.
