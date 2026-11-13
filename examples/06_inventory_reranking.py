import numpy as np

from skeletonpaths import graph_from_skeleton, prepare_topology_paths, select_path


def main():
    skeleton = np.zeros((31, 31), dtype=bool)
    skeleton[3:28, 15] = True
    skeleton[15, 5:16] = True
    graph = graph_from_skeleton(skeleton)
    inventory = prepare_topology_paths(graph, path_kinds=("open",))

    for end in ((15.0, 27.0), (5.0, 15.0)):
        selection = select_path(
            graph,
            expected_cycles=0,
            expected_endpoints=((15.0, 3.0), end),
            endpoint_tolerance_px=0.0,
            path_inventory=inventory,
        )
        print(
            "target end:",
            end,
            "length:",
            selection.path.length_px,
            "edge ids:",
            selection.path.edge_ids,
        )


if __name__ == "__main__":
    main()
