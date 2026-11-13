import numpy as np
from skimage.draw import circle_perimeter

from skeletonpaths import graph_from_skeleton, select_path

skeleton = np.zeros((31, 31), dtype=bool)
rows, cols = circle_perimeter(15, 15, 8)
skeleton[rows, cols] = True

graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
path = select_path(graph, path_kind="loop", expected_cycles=1)

print("graph cycles:", graph.cycle_count)
print("path cycles:", path.cycle_count)
print("closed:", bool(np.array_equal(path.xy[0], path.xy[-1])))
print("length_px:", round(path.length_px, 3))
