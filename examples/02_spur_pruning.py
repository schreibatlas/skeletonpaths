import numpy as np

from skeletonpaths import graph_from_skeleton, prune_spurs


def main():
    skeleton = np.zeros((31, 31), dtype=bool)
    skeleton[4:27, 15] = True
    skeleton[15, 9:16] = True

    pruned = prune_spurs(skeleton, min_length_px=7.0)
    graph = graph_from_skeleton(skeleton, min_spur_length=7.0)

    print("foreground before/after:", int(skeleton.sum()), int(pruned.sum()))
    print("endpoints:", graph.endpoint_count)
    print("junctions:", graph.junction_count)
    print("edges:", len(graph.edges))
    print("remaining edge length:", graph.edges[0].length_px)


if __name__ == "__main__":
    main()
