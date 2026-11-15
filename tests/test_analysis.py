import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

from skeletonpaths import SkeletonAnalysis, SkeletonImage, analyze_mask, graph_from_mask


def _mask(kind: str) -> np.ndarray:
    mask = np.zeros((25, 27), dtype=bool)
    if kind == "line":
        mask[11:14, 3:24] = True
    elif kind == "curve":
        mask[3:22, 4:7] = True
        mask[19:22, 4:23] = True
    elif kind == "loop":
        mask[3:6, 4:23] = True
        mask[19:22, 4:23] = True
        mask[3:22, 4:7] = True
        mask[3:22, 20:23] = True
    elif kind == "branch":
        mask[3:14, 12:15] = True
        mask[11:14, 4:23] = True
    elif kind != "empty":
        raise ValueError(kind)
    return mask


def _assert_graphs_equal(first, second) -> None:
    assert first.nodes == second.nodes
    assert len(first.edges) == len(second.edges)
    for first_edge, second_edge in zip(first.edges, second.edges, strict=True):
        assert (first_edge.a, first_edge.b) == (second_edge.a, second_edge.b)
        np.testing.assert_array_equal(first_edge.xy, second_edge.xy)
        assert first_edge.length_px == second_edge.length_px
        assert first_edge.mean_radius_px == second_edge.mean_radius_px
        assert first_edge.confidence == second_edge.confidence


@pytest.mark.parametrize(
    ("kind", "endpoints", "junctions", "cycles"),
    [
        ("line", 2, 0, 0),
        ("curve", 2, 0, 0),
        ("loop", 0, 0, 1),
        ("branch", 3, 1, 0),
        ("empty", 0, 0, 0),
    ],
)
def test_analyze_mask_returns_complete_immutable_analysis(kind, endpoints, junctions, cycles):
    input_mask = _mask(kind)
    result = analyze_mask(input_mask)

    assert isinstance(result, SkeletonAnalysis)
    assert isinstance(result, SkeletonImage)
    assert result.mask.shape == input_mask.shape
    assert result.skeleton.shape == input_mask.shape
    assert result.radius.shape == input_mask.shape
    assert result.confidence.shape == input_mask.shape
    assert result.endpoint_count == endpoints
    assert result.junction_count == junctions
    assert result.cycle_count == cycles
    assert result.component_count == (0 if kind == "empty" else 1)
    assert np.isfinite(result.radius).all()
    assert np.all(result.radius >= 0.0)
    assert np.all(result.confidence == 1.0)
    assert not result.mask.flags.writeable
    assert not result.skeleton.flags.writeable
    assert not result.radius.flags.writeable
    assert not result.confidence.flags.writeable
    assert not np.shares_memory(result.mask, input_mask)
    assert not np.any(result.skeleton & ~result.mask)
    if kind == "empty":
        assert result.graph.nodes == ()
        assert result.graph.edges == ()
        assert not result.skeleton.any()
        assert not result.radius.any()
    else:
        assert result.skeleton.any()
        assert result.radius.max() > 0.0


def test_analyze_mask_radius_matches_mask_distance_transform_and_graph_samples():
    mask = _mask("line")
    result = analyze_mask(mask)

    np.testing.assert_array_equal(result.radius, distance_transform_edt(mask))
    for node in result.graph.nodes:
        x, y = map(int, node.xy)
        assert node.radius_px == result.radius[y, x]
    for edge in result.graph.edges:
        assert edge.mean_radius_px > 0.0


def test_analyze_mask_propagates_confidence_and_prunes_spurs():
    mask = np.zeros((31, 31), dtype=bool)
    mask[4:27, 15] = True
    mask[15, 9:16] = True
    confidence = np.full(mask.shape, 0.75)

    unpruned = analyze_mask(mask, confidence=confidence)
    pruned = analyze_mask(mask, min_spur_length=7.0, confidence=confidence)

    assert unpruned.endpoint_count == 3
    assert pruned.endpoint_count == 2
    assert all(node.confidence == 0.75 for node in pruned.graph.nodes)
    assert all(edge.confidence == 0.75 for edge in pruned.graph.edges)
    np.testing.assert_array_equal(pruned.confidence, confidence)
    assert not np.shares_memory(pruned.confidence, confidence)
    _assert_graphs_equal(
        pruned.graph,
        graph_from_mask(mask, min_spur_length=7.0, confidence=confidence),
    )


def test_analyze_mask_graph_order_is_deterministic():
    mask = _mask("branch")

    first = analyze_mask(mask)
    second = analyze_mask(mask.copy())

    _assert_graphs_equal(first.graph, second.graph)
    np.testing.assert_array_equal(first.skeleton, second.skeleton)


def test_analyze_mask_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="two-dimensional"):
        analyze_mask(np.zeros((3, 4, 1), dtype=bool))

    mask = _mask("line")
    with pytest.raises(ValueError, match="confidence"):
        analyze_mask(mask, confidence=np.ones((2, 2)))
    with pytest.raises(ValueError, match="confidence"):
        analyze_mask(mask, confidence=np.full(mask.shape, np.nan))
    with pytest.raises(ValueError, match="confidence"):
        analyze_mask(mask, confidence=np.full(mask.shape, -0.1))
    with pytest.raises(ValueError, match="confidence"):
        analyze_mask(mask, confidence=np.full(mask.shape, 1.1))
    with pytest.raises(ValueError, match="spur length"):
        analyze_mask(mask, min_spur_length=-1.0)


def test_analyze_mask_rejects_invalid_radius_and_exposes_graph_diagnostics():
    mask = _mask("line")
    with pytest.raises(ValueError, match="radius map"):
        analyze_mask(mask, radius=np.full(mask.shape, np.inf))

    result = analyze_mask(mask)
    assert result.component_count == result.graph.component_count
    assert result.endpoint_count == result.graph.endpoint_count
    assert result.junction_count == result.graph.junction_count
    assert result.cycle_count == result.graph.cycle_count
