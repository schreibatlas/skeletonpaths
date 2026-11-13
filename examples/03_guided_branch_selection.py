import numpy as np

from skeletonpaths import graph_from_skeleton, rank_paths, select_path

skeleton = np.zeros((31, 31), dtype=bool)
skeleton[3:28, 15] = True
skeleton[15, 5:16] = True
graph = graph_from_skeleton(skeleton, min_spur_length=0.0)

# A guide that points at the short left branch.
misleading_guide = np.column_stack((np.arange(5.0, 16.0), np.full(11, 15.0)))

# Endpoint constraints are hard and therefore override the guide.
selected = select_path(
    graph,
    path_kind="open",
    expected_cycles=0,
    expected_endpoints=((15.0, 3.0), (15.0, 27.0)),
    endpoint_tolerance_px=1.0,
    candidate_xy=misleading_guide,
)

print("all feasible lengths:", [p.length_px for p in rank_paths(graph)])
print("selected length:", selected.length_px)
print("selected endpoints:", selected.xy[0].tolist(), selected.xy[-1].tolist())
