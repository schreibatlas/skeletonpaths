import numpy as np
import pytest

from skeletonpaths import RouteStep, SkeletonEdge, SkeletonGraph, SkeletonNode, covering_walk


def _line_graph() -> SkeletonGraph:
    nodes = (
        SkeletonNode(0, (0.0, 0.0), 1, 0.0, 1.0),
        SkeletonNode(1, (3.0, 0.0), 1, 0.0, 1.0),
    )
    edge = SkeletonEdge(0, 1, np.asarray(((0.0, 0.0), (3.0, 0.0))), 3.0, 0.0, 1.0)
    return SkeletonGraph(nodes, (edge,))


def test_route_step_validates_and_reverses_direction():
    forward = RouteStep(4, "a-to-b")

    assert forward.reversed() == RouteStep(4, "b-to-a")
    with pytest.raises(ValueError, match="edge ID"):
        RouteStep(-1, "a-to-b")
    with pytest.raises(ValueError, match="direction"):
        RouteStep(0, "sideways")


def test_skeleton_walk_exposes_explicit_steps_and_reversal():
    graph = _line_graph()
    forward = covering_walk(graph, start_node=0, end_node=1)
    reverse = forward.reversed()

    assert forward.steps == (RouteStep(0, "a-to-b"),)
    assert reverse.steps == (RouteStep(0, "b-to-a"),)
    assert reverse.start_node == forward.end_node
    assert reverse.end_node == forward.start_node
    np.testing.assert_array_equal(reverse.xy, forward.xy[::-1])
    assert reverse.length_px == forward.length_px
    assert reverse.reversed().steps == forward.steps
