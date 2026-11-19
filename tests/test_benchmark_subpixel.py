import json
import subprocess
import sys
from pathlib import Path


def test_subpixel_benchmark_smoke_reports_bounded_metrics():
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "benchmarks" / "benchmark_subpixel.py"),
            "--side",
            "64",
            "--repeats",
            "1",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=root,
    )
    report = json.loads(completed.stdout)

    assert report["configuration"]["side_px"] == 64
    assert report["runtime_seconds_per_glyph_crop"]["median"] > 0.0
    assert report["work"]["edge_count"] > 0
    assert 0 < report["work"]["peak_refinement_sample_count"] <= 100_000
    assert 0 < report["work"]["peak_normal_probe_count"] <= 1_000_000
    assert report["memory"]["retained_refined_geometry_array_bytes"] > 0
