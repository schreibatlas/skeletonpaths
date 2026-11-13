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
    """Build a graph from a binary mask, deriving raster radius when omitted.

    Components smaller than ``min_component_area`` pixels are removed. The
    default of zero keeps all components. Public coordinates are always
    ``(x=column, y=row)``.
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
