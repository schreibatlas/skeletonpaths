import numpy as np
import pytest

from skeletonpaths import SkeletonImage, analyze_mask, graph_from_mask


def _mask(kind: str) -> np.ndarray:
    mask = np.zeros((17, 19), dtype=bool)
    if kind == "line":
        mask[7:10, 2:17] = True
    elif kind == "branch":
        mask[2:15, 8:11] = True
        mask[7:10, 2:17] = True
    elif kind == "loop":
        mask[3:6, 3:16] = True
        mask[11:14, 3:16] = True
        mask[3:14, 3:6] = True
        mask[3:14, 13:16] = True
    elif kind != "empty":
        raise ValueError(kind)
    return mask


def _assert_graph_equal(first, second) -> None:
    assert first.nodes == second.nodes
    assert len(first.edges) == len(second.edges)
    for first_edge, second_edge in zip(first.edges, second.edges, strict=True):
        assert first_edge.a == second_edge.a
        assert first_edge.b == second_edge.b
        np.testing.assert_array_equal(first_edge.xy, second_edge.xy)
        assert first_edge.length_px == second_edge.length_px
        assert first_edge.mean_radius_px == second_edge.mean_radius_px
        assert first_edge.confidence == second_edge.confidence


@pytest.mark.parametrize(
    ("kind", "cycle_count"),
    [("empty", 0), ("line", 0), ("branch", 0), ("loop", 1)],
)
def test_analyze_mask_returns_skeleton_radius_and_matching_graph(kind, cycle_count):
    mask = _mask(kind)

    result = analyze_mask(mask)

    assert isinstance(result, SkeletonImage)
    assert result.skeleton.shape == mask.shape
    assert result.radius.shape == mask.shape
    assert np.isfinite(result.radius).all()
    assert np.all(result.radius >= 0.0)
    assert not result.skeleton.flags.writeable
    assert not result.radius.flags.writeable
    assert result.graph.cycle_count == cycle_count
    assert not np.any(result.skeleton & ~mask)
    assert np.all(result.radius[~mask] == 0.0)
    if mask.any():
        assert result.skeleton.any()
        assert result.radius.max() > 0.0
    _assert_graph_equal(result.graph, graph_from_mask(mask))


def test_analyze_mask_preserves_supplied_radius_confidence_and_filtering():
    mask = _mask("line")
    mask[0, 0] = True
    radius = np.full(mask.shape, 2.5)
    confidence = np.full(mask.shape, 0.75)

    result = analyze_mask(
        mask,
        radius=radius,
        confidence=confidence,
        min_component_area=2,
    )

    assert not result.skeleton[0, 0]
    np.testing.assert_array_equal(result.radius, radius)
    assert all(node.confidence == 0.75 for node in result.graph.nodes)
    _assert_graph_equal(
        result.graph,
        graph_from_mask(
            mask,
            radius=radius,
            confidence=confidence,
            min_component_area=2,
        ),
    )


def test_skeleton_image_rejects_inconsistent_arrays():
    from skeletonpaths import SkeletonGraph

    with pytest.raises(ValueError, match="match the skeleton"):
        SkeletonImage(np.zeros((3, 4), dtype=bool), np.zeros((4, 3)), SkeletonGraph((), ()))
