import numpy as np

from skeletonpaths import graph_from_skeleton, prepare_topology_paths, select_path

skeleton = np.zeros((31, 31), dtype=bool)
skeleton[3:28, 15] = True
skeleton[15, 5:16] = True
graph = graph_from_skeleton(skeleton, min_spur_length=0.0)
inventory = prepare_topology_paths(graph)

for end in ((15.0, 27.0), (5.0, 15.0)):
    selected = select_path(
        graph,
        expected_cycles=0,
        expected_endpoints=((15.0, 3.0), end),
        endpoint_tolerance_px=0.0,
        path_inventory=inventory,
    )
    print("target end:", end, "length:", selected.length_px, "edge ids:", selected.edge_ids)
