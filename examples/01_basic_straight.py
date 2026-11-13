import numpy as np

from skeletonpaths import graph_from_skeleton, select_path


def main():
    skeleton = np.zeros((9, 9), dtype=bool)
    skeleton[4, 1:8] = True

    graph = graph_from_skeleton(skeleton)
    selection = select_path(
        graph,
        path_kind="open",
        expected_cycles=0,
        expected_endpoints=((1.0, 4.0), (7.0, 4.0)),
        endpoint_tolerance_px=0.0,
    )

    print("nodes:", len(graph.nodes))
    print("edges:", len(graph.edges))
    print("endpoints:", graph.endpoint_count)
    print("length_px:", selection.path.length_px)
    print("start/end:", selection.path.xy[0].tolist(), selection.path.xy[-1].tolist())


if __name__ == "__main__":
    main()
