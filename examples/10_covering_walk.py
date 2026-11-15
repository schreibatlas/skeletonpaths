"""Build a deterministic graph-covering traversal from an analyzed mask."""

import numpy as np

from skeletonpaths import analyze_mask, covering_walk


def main() -> None:
    mask = np.zeros((18, 24), dtype=bool)
    mask[2:10, 10:13] = True
    mask[7:10, 3:21] = True
    analysis = analyze_mask(mask)

    endpoints = sorted(
        (node for node in analysis.graph.nodes if node.degree == 1),
        key=lambda node: (node.xy[0], node.xy[1], node.id),
    )
    walk = covering_walk(
        analysis.graph,
        start_node=endpoints[0].id,
        end_node=endpoints[-1].id,
    )

    assert walk.covered_edge_count == len(analysis.graph.edges)
    assert set(walk.covered_edge_ids) == set(range(len(analysis.graph.edges)))
    assert walk.length_px >= sum(
        analysis.graph.edges[edge_id].length_px for edge_id in walk.covered_edge_ids
    )

    print(f"traversed edges: {walk.edge_ids}")
    print(f"edge directions: {walk.edge_directions}")
    print(f"repeated traversals: {walk.repeated_edge_count}")


if __name__ == "__main__":
    main()
