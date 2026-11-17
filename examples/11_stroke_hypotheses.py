"""Rank generic stroke-set hypotheses without inferring physical pen history."""

import numpy as np

from skeletonpaths import analyze_mask, stroke_hypotheses_from_analysis


def main() -> None:
    mask = np.zeros((24, 34), dtype=bool)
    mask[3:20, 8:11] = True
    mask[9:12, 3:20] = True
    mask[4:7, 27:30] = True
    analysis = analyze_mask(mask)
    hypotheses = stroke_hypotheses_from_analysis(analysis, limit=3)

    assert hypotheses
    assert all(
        item.covered_edge_ids | item.uncovered_edge_ids == set(range(len(analysis.graph.edges)))
        for item in hypotheses
    )
    print(f"components: {analysis.graph.component_count}")
    for index, hypothesis in enumerate(hypotheses, start=1):
        print(
            f"hypothesis {index}: walks={hypothesis.stroke_count}, "
            f"lifts={hypothesis.pen_lift_count}, repeated={hypothesis.repeated_edge_ids}, "
            f"route_ambiguous={hypothesis.route_ambiguous}, "
            f"orientation_ambiguous={hypothesis.orientation_ambiguous}, "
            f"component_order_ambiguous={hypothesis.component_order_ambiguous}, "
            f"truncated={hypothesis.truncated}"
        )
        print(f"  score: {hypothesis.score}")
        print(f"  junction pairings: {hypothesis.junction_pairings}")


if __name__ == "__main__":
    main()
