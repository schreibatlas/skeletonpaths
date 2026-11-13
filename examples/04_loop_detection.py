import numpy as np
from skimage.draw import circle_perimeter

from skeletonpaths import graph_from_skeleton, select_path


def main():
    skeleton = np.zeros((31, 31), dtype=bool)
    rows, columns = circle_perimeter(15, 15, 8)
    skeleton[rows, columns] = True

    graph = graph_from_skeleton(skeleton)
    selection = select_path(graph, path_kind="loop", expected_cycles=1)

    print("graph cycles:", graph.cycle_count)
    print("path cycles:", selection.path.cycle_count)
    print("closed:", bool(np.array_equal(selection.path.xy[0], selection.path.xy[-1])))
    print("length_px:", round(selection.path.length_px, 3))


if __name__ == "__main__":
    main()
