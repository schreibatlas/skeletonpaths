import subprocess
import sys
from pathlib import Path

import numpy as np

import skeletonpaths


def test_core_api_imports_without_image_dependencies():
    script = """
import builtins

original_import = builtins.__import__
def without_image_dependencies(name, *args, **kwargs):
    if name.split(".", 1)[0] in {"scipy", "skimage"}:
        raise ModuleNotFoundError(f"No module named {name!r}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = without_image_dependencies
import numpy as np
import skeletonpaths

skeleton = np.zeros((5, 7), dtype=bool)
skeleton[2, 1:6] = True
graph = skeletonpaths.graph_from_skeleton(skeleton)
assert graph.endpoint_count == 2
try:
    skeletonpaths.graph_from_mask(skeleton)
except ImportError as error:
    assert "skeletonpaths[image]" in str(error)
else:
    raise AssertionError("graph_from_mask unexpectedly worked without image dependencies")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_image_extra_graph_from_mask_smoke():
    mask = np.zeros((15, 20), dtype=bool)
    mask[6:9, 3:17] = True

    graph = skeletonpaths.graph_from_mask(mask)

    assert graph.endpoint_count == 2
    assert graph.edges
    assert max(node.radius_px for node in graph.nodes) > 0.0
