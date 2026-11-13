import numpy as np
from planarcurve.polyline import resample_polyline_by_arclength

from skeletonpaths import graph_from_skeleton, select_path

skeleton = np.zeros((64, 64), dtype=bool)
skeleton[32, 8:56] = True

graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
path = select_path(graph)
curve = resample_polyline_by_arclength(path.xy, 32)

print(path.length_px)
print(curve.shape)
