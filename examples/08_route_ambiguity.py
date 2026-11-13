import numpy as np

from skeletonpaths import graph_from_skeleton, rank_paths, select_path


def main():
    skeleton = np.zeros((21, 21), dtype=bool)
    skeleton[10, 2:7] = True
    skeleton[10, 14:19] = True
    skeleton[6:11, 6] = True
    skeleton[6, 6:15] = True
    skeleton[6:11, 14] = True
    skeleton[10:15, 6] = True
    skeleton[14, 6:15] = True
    skeleton[10:15, 14] = True
    graph = graph_from_skeleton(skeleton)

    un_guided = select_path(graph, path_kind="open")
    print("unguided route scores:")
    for path in rank_paths(graph, path_kind="open"):
        print("  edges:", path.edge_ids, "score:", path.score)
    print("unguided ambiguous:", un_guided.ambiguous)

    upper_guide = np.array(
        [[2.0, 10.0], [6.0, 10.0], [6.0, 6.0], [14.0, 6.0], [14.0, 10.0], [18.0, 10.0]]
    )
    guided = select_path(graph, path_kind="open", candidate_xy=upper_guide)
    print("guided ambiguous:", guided.ambiguous)
    print("guided route length_px:", guided.path.length_px)


if __name__ == "__main__":
    main()
