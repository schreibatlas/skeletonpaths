"""Inspect skeleton, radius, confidence, and graph results from a binary mask."""

import numpy as np

from skeletonpaths import SkeletonAnalysis, analyze_mask


def main() -> None:
    mask = np.zeros((24, 28), dtype=bool)
    mask[10:14, 3:25] = True

    analysis = analyze_mask(mask)
    assert isinstance(analysis, SkeletonAnalysis)
    assert not analysis.mask.flags.writeable
    assert not analysis.skeleton.flags.writeable
    assert not analysis.radius.flags.writeable
    assert not analysis.confidence.flags.writeable

    print(f"components: {analysis.component_count}")
    print(f"endpoints: {analysis.endpoint_count}")
    print(f"maximum radius: {analysis.radius.max():.1f}px")


if __name__ == "__main__":
    main()
