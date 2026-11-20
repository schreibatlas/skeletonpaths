from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .graph import _binary_image, graph_from_skeleton, prune_spurs
from .model import JunctionRegionOptions, SkeletonAnalysis, SkeletonGraph


def analyze_mask(
    mask: ArrayLike,
    *,
    min_spur_length: float = 0.0,
    min_spur_length_px: float | None = None,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    min_component_area: int = 0,
    junction_options: JunctionRegionOptions | None = None,
) -> SkeletonAnalysis:
    """Skeletonize a binary mask and return its raster data and topology.

    Parameters
    ----------
    mask : numpy.typing.ArrayLike
        Two-dimensional boolean image or finite numeric image containing only
        zero and one values.
    min_spur_length : float
        Remove endpoint-to-junction branches strictly shorter than this
        threshold, in pixels. Zero preserves all spurs.
    min_spur_length_px : float or None
        Preferred pixel-suffixed alias for ``min_spur_length``. Supplying both
        names with non-default values is invalid.
    radius : numpy.typing.ArrayLike or None
        Optional finite, nonnegative radius map matching ``mask``. If omitted,
        derive radius from the foreground with a Euclidean distance transform.
    confidence : numpy.typing.ArrayLike or None
        Optional finite confidence map matching ``mask`` with values in
        ``[0, 1]``. If omitted, the analysis confidence map is all ones.
        These values are generic evidence, not a probability.
    min_component_area : int
        Remove 8-neighbor mask components smaller than this pixel area before
        skeletonization. Zero keeps every component.

    Returns
    -------
    SkeletonAnalysis
        Owned read-only mask, skeleton, radius, and confidence arrays alongside the topology graph.
        Optional component labels are included when available. The arrays are owned and read-only.

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
    component labeling. SciPy is required when radius is omitted for nonempty
    masks and when ``min_component_area`` is positive. Skeletonization requires
    scikit-image. These dependencies are imported lazily.
    """
    source = _binary_image(mask, name="mask")
    if (
        isinstance(min_component_area, bool)
        or not isinstance(min_component_area, (int, np.integer))
        or min_component_area < 0
    ):
        raise ValueError("minimum component area must be a nonnegative integer")
    if min_spur_length_px is not None:
        if min_spur_length != 0.0:
            raise ValueError("pass either min_spur_length or min_spur_length_px, not both")
        min_spur_length = min_spur_length_px
    component_labels = None
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
        component_labels = np.where(source, labels, 0)
    else:
        try:
            from scipy.ndimage import label as label_components
        except ImportError:
            pass
        else:
            component_labels, _ = label_components(
                source, structure=np.ones((3, 3), dtype=np.uint8)
            )
    radius_map: np.ndarray
    if radius is None:
        if source.any():
            try:
                from scipy.ndimage import distance_transform_edt
            except ImportError as error:
                raise ImportError(
                    "automatic mask radius requires SciPy; install skeletonpaths[image]"
                ) from error
            radius_map = distance_transform_edt(source)
        else:
            radius_map = np.zeros(source.shape, dtype=float)
    else:
        radius_map = np.asarray(radius, dtype=float)
        if (
            radius_map.shape != source.shape
            or not np.isfinite(radius_map).all()
            or np.any(radius_map < 0.0)
        ):
            raise ValueError("radius map must be finite, nonnegative, and match observed ink")

    if confidence is None:
        confidence_map = np.ones(source.shape, dtype=float)
    else:
        confidence_map = np.asarray(confidence, dtype=float)
        if (
            confidence_map.shape != source.shape
            or not np.isfinite(confidence_map).all()
            or np.any((confidence_map < 0.0) | (confidence_map > 1.0))
        ):
            raise ValueError("confidence map must be between zero and one and match observed ink")

    try:
        from skimage.morphology import skeletonize
    except ImportError as error:
        raise ImportError(
            "skeletonizing observed ink requires scikit-image; install skeletonpaths[image]"
        ) from error
    skeleton = prune_spurs(skeletonize(source), min_spur_length)
    graph = graph_from_skeleton(
        skeleton, radius=radius_map, confidence=confidence_map, junction_options=junction_options
    )
    return SkeletonAnalysis(
        mask=source,
        skeleton=skeleton,
        radius=radius_map,
        confidence=confidence_map,
        graph=graph,
        component_labels=component_labels,
    )


def graph_from_mask(
    mask: ArrayLike,
    *,
    min_spur_length: float = 0.0,
    min_spur_length_px: float | None = None,
    radius: ArrayLike | None = None,
    confidence: ArrayLike | None = None,
    min_component_area: int = 0,
    junction_options: JunctionRegionOptions | None = None,
) -> SkeletonGraph:
    """Skeletonize a binary mask and build its topology graph.

    Use :func:`analyze_mask` when the skeleton and radius arrays are also needed.
    """
    return analyze_mask(
        mask,
        min_spur_length=min_spur_length,
        min_spur_length_px=min_spur_length_px,
        radius=radius,
        confidence=confidence,
        min_component_area=min_component_area,
        junction_options=junction_options,
    ).graph
