import numpy as np
from numpy.typing import ArrayLike

from .graph import _binary_image, build_skeleton_graph
from .model import SkeletonGraph


def graph_from_mask(
    mask: ArrayLike,
    *,
    min_spur_length: float = 0.0,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    min_component_area: int = 0,
) -> SkeletonGraph:
    """Skeletonize a binary mask and build its topology graph.

    Parameters
    ----------
    mask : numpy.typing.ArrayLike
        Two-dimensional boolean image or finite numeric image containing only
        zero and one values.
    min_spur_length : float
        Remove endpoint-to-junction branches strictly shorter than this
        threshold, in pixels. Zero preserves all spurs.
    radius : numpy.typing.ArrayLike or None
        Optional finite, nonnegative radius map matching ``mask``. If omitted,
        derive radius from the mask with a Euclidean distance transform.
    confidence : numpy.typing.ArrayLike or None
        Optional finite confidence map matching ``mask`` with values in
        ``[0, 1]``. If omitted, confidence values are one.
    min_component_area : int
        Remove 8-neighbor mask components smaller than this pixel area before
        skeletonization. Zero keeps every component.

    Returns
    -------
    SkeletonGraph
        Immutable topology graph with public coordinates in ``(x, y) =
        (column, row)`` pixel units.

    Raises
    ------
    ValueError
        If the mask, component area, or supplied maps are invalid.
    ImportError
        If SciPy is unavailable for automatic radius derivation or requested
        component filtering, or scikit-image is unavailable for skeletonization.

    Notes
    -----
    Component filtering occurs before skeletonization and uses 8-neighbor
    component labeling. SciPy is required when ``radius`` is omitted and when
    ``min_component_area`` is positive. Skeletonization requires scikit-image.
    These dependencies are imported lazily. Use ``graph_from_skeleton()`` for
    pre-thinned input without image-processing dependencies.

    See Also
    --------
    graph_from_skeleton : Build a graph from an already-thinned skeleton.
    build_skeleton_graph : Lower-level graph constructor.
    """

    source = _binary_image(mask, name="mask")
    if (
        isinstance(min_component_area, bool)
        or not isinstance(min_component_area, (int, np.integer))
        or min_component_area < 0
    ):
        raise ValueError("minimum component area must be a nonnegative integer")
    if min_component_area > 0:
        try:
            from scipy.ndimage import label as label_components
        except ImportError as error:
            raise ImportError(
                "component filtering requires SciPy; install skeletonpaths[image]"
            ) from error
        labels, _ = label_components(source, structure=np.ones((3, 3), dtype=np.uint8))
        areas = np.bincount(labels.ravel())
        keep = areas >= min_component_area
        keep[0] = False
        source = keep[labels]
    if radius is None:
        try:
            from scipy.ndimage import distance_transform_edt
        except ImportError as error:
            raise ImportError(
                "automatic mask radius requires SciPy; install skeletonpaths[image]"
            ) from error
        radius = distance_transform_edt(source)
    return build_skeleton_graph(
        source,
        min_spur_length_px=min_spur_length,
        radius=radius,
        confidence=confidence,
        already_skeleton=False,
    )
