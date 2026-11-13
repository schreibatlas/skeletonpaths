import numpy as np
from scipy.ndimage import distance_transform_edt

from skeletonpaths import graph_from_mask

mask = np.zeros((25, 35), dtype=bool)
mask[10:15, 4:31] = True
radius = distance_transform_edt(mask)
confidence = np.ones(mask.shape, dtype=float)
confidence[:, 17:] = 0.6

graph = graph_from_mask(
    mask,
    min_spur_length=0.0,
    radius=radius,
    confidence=confidence,
)

edge = graph.edges[0]
print("nodes/edges:", len(graph.nodes), len(graph.edges))
print("mean radius px:", round(edge.mean_radius_px, 3))
print("edge confidence:", round(edge.confidence, 3))
