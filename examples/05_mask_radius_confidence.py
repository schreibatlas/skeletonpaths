import numpy as np

from skeletonpaths import graph_from_mask


def main():
    mask = np.zeros((25, 35), dtype=bool)
    mask[10:15, 4:31] = True
    confidence = np.ones(mask.shape, dtype=float)
    confidence[:, 17:] = 0.6

    graph = graph_from_mask(mask, confidence=confidence)

    edge = graph.edges[0]
    print("nodes/edges:", len(graph.nodes), len(graph.edges))
    print("mean radius px:", round(edge.mean_radius_px, 3))
    print("edge confidence:", round(edge.confidence, 3))


if __name__ == "__main__":
    main()
