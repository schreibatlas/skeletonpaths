import numpy as np
from planarcurve.polyline import mean_squared_turn_angle, resample_polyline_by_arclength

from skeletonpaths import graph_from_skeleton, select_path


def main():
    skeleton = np.zeros((48, 48), dtype=bool)
    skeleton[38, 4:17] = True
    for offset in range(1, 11):
        skeleton[38 - offset, 16 + offset] = True
    skeleton[28, 27:44] = True

    graph = graph_from_skeleton(skeleton)
    selection = select_path(graph)
    route_xy = selection.path.xy
    curve_xy = resample_polyline_by_arclength(route_xy, 48)

    print("route length_px:", round(selection.path.length_px, 3))
    print("resampled points:", len(curve_xy))
    print("mean squared turn angle:", round(mean_squared_turn_angle(curve_xy), 6))


if __name__ == "__main__":
    main()
