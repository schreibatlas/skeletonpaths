# SkeletonPaths review examples

These scripts use only the current public `skeletonpaths` API plus its declared runtime dependencies.
Run them from an environment where `skeletonpaths` is installed:

```bash
python 01_basic_straight.py
python 02_spur_pruning.py
python 03_guided_branch_selection.py
python 04_loop_detection.py
python 05_mask_radius_confidence.py
python 06_inventory_reranking.py
python 07_planarcurve_interop.py
```

`07_planarcurve_interop.py` uses SkeletonPaths for raster topology and PlanarCurve for neutral polyline resampling. Install both packages before running it.
They are intended as seeds for a future `examples/` directory in the package repository.
