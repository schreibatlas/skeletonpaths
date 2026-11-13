import numpy as np

from skeletonpaths import graph_from_skeleton, select_path

skeleton = np.zeros((9, 9), dtype=bool)
skeleton[4, 1:8] = True

graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
path = select_path(
    graph,
    path_kind="open",
    expected_cycles=0,
    expected_endpoints=((1.0, 4.0), (7.0, 4.0)),
    endpoint_tolerance_px=0.0,
)

print("nodes:", len(graph.nodes))
print("edges:", len(graph.edges))
print("endpoints:", graph.endpoint_count)
print("length_px:", path.length_px)
print("start/end:", path.xy[0].tolist(), path.xy[-1].tolist())
