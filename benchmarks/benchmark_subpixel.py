"""Measure bounded subpixel reconstruction work on a deterministic synthetic glyph."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from typing import Any

import numpy as np

from skeletonpaths import SubpixelCenterlineOptions, analyze_mask, refine_graph_geometry


def _capsule_field(
    shape: tuple[int, int], start: tuple[float, float], end: tuple[float, float], radius: float
) -> np.ndarray:
    y, x = np.mgrid[: shape[0], : shape[1]]
    points = np.stack((x, y), axis=-1)
    first = np.asarray(start, dtype=float)
    vector = np.asarray(end, dtype=float) - first
    parameter = np.clip(
        np.sum((points - first) * vector, axis=-1) / np.dot(vector, vector),
        0.0,
        1.0,
    )
    nearest = first + parameter[..., None] * vector
    return radius - np.linalg.norm(points - nearest, axis=-1)


def _glyph_field(side: int) -> np.ndarray:
    """Build a signed-field A-shaped glyph inside a square crop."""
    top = (0.5 * side, 0.12 * side)
    left_foot = (0.18 * side, 0.84 * side)
    right_foot = (0.82 * side, 0.84 * side)
    crossbar_start = (0.36 * side, 0.60 * side)
    crossbar_end = (0.64 * side, 0.60 * side)
    radius = max(2.0, 0.035 * side)
    strokes = (
        _capsule_field((side, side), top, left_foot, radius),
        _capsule_field((side, side), top, right_foot, radius),
        _capsule_field((side, side), crossbar_start, crossbar_end, radius),
    )
    return np.maximum.reduce(strokes)


def _retained_edge_array_bytes(geometry: Any) -> int:
    return sum(
        array.nbytes
        for edge in geometry.edges
        for array in (edge.xy, edge.tangent, edge.curvature, edge.radius_px, edge.confidence)
    )


def _analysis_array_bytes(analysis: Any, decision_field: np.ndarray) -> int:
    arrays = [
        analysis.mask,
        analysis.skeleton,
        analysis.radius,
        analysis.confidence,
        decision_field,
    ]
    if analysis.component_labels is not None:
        arrays.append(analysis.component_labels)
    return sum(array.nbytes for array in arrays)


def _timed_run(field: np.ndarray, options: SubpixelCenterlineOptions) -> tuple[float, Any, int]:
    started = time.perf_counter()
    analysis = analyze_mask(field > 0.0)
    geometry = refine_graph_geometry(analysis, decision_field=field, options=options)
    elapsed = time.perf_counter() - started
    return elapsed, geometry, _analysis_array_bytes(analysis, field)


def _peak_traced_bytes(field: np.ndarray, options: SubpixelCenterlineOptions) -> int:
    tracemalloc.start()
    try:
        analysis = analyze_mask(field > 0.0)
        refine_graph_geometry(analysis, decision_field=field, options=options)
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak_bytes


def run_benchmark(side: int, repeats: int) -> dict[str, Any]:
    field = _glyph_field(side)
    options = SubpixelCenterlineOptions(
        max_refinement_samples=100_000,
        max_normal_probes=1_000_000,
    )

    # Warm up lazy spline imports and native-library initialization before timing.
    analysis = analyze_mask(field > 0.0)
    refine_graph_geometry(analysis, decision_field=field, options=options)

    runtimes: list[float] = []
    sample_counts: list[int] = []
    probe_counts: list[int] = []
    probes_per_point: list[float] = []
    fits_per_edge: list[int] = []
    last_geometry = None
    analysis_bytes = 0
    for _ in range(repeats):
        elapsed, geometry, analysis_bytes = _timed_run(field, options)
        runtimes.append(elapsed)
        sample_counts.append(int(geometry.diagnostics["refinement_sample_count"]))
        probe_counts.append(int(geometry.diagnostics["normal_probe_count"]))
        probes_per_point.extend(
            edge.diagnostics.normal_probe_count / max(1, edge.diagnostics.raw_point_count)
            for edge in geometry.edges
        )
        fits_per_edge.extend(edge.diagnostics.spline_fit_count for edge in geometry.edges)
        last_geometry = geometry
    peak_traced_bytes = _peak_traced_bytes(field, options)
    assert last_geometry is not None
    retained_geometry_bytes = _retained_edge_array_bytes(last_geometry)
    return {
        "configuration": {
            "side_px": side,
            "repeats": repeats,
            "warmup_runs": 1,
            "memory_measurement_runs": 1,
        },
        "runtime_seconds_per_glyph_crop": {
            "median": statistics.median(runtimes),
            "minimum": min(runtimes),
            "maximum": max(runtimes),
        },
        "work": {
            "edge_count": len(last_geometry.edges),
            "peak_refinement_sample_count": max(sample_counts),
            "peak_normal_probe_count": max(probe_counts),
            "median_cross_section_probes_per_edge_point": statistics.median(probes_per_point),
            "median_spline_fits_per_edge": statistics.median(fits_per_edge),
        },
        "memory": {
            "analysis_and_field_array_bytes": analysis_bytes,
            "retained_refined_geometry_array_bytes": retained_geometry_bytes,
            "refined_to_analysis_array_ratio": retained_geometry_bytes / max(1, analysis_bytes),
            "peak_traced_bytes": peak_traced_bytes,
            "measurement_note": (
                "peak_traced_bytes uses a separate run so tracing does not affect runtime; "
                "array byte totals exclude Python and PlanarCurve object overhead."
            ),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--side", type=int, default=128, help="square crop side in pixels (64..512)"
    )
    parser.add_argument("--repeats", type=int, default=3, help="measured runs (1..20)")
    parser.add_argument("--json", action="store_true", help="emit the full machine-readable report")
    args = parser.parse_args()
    if not 64 <= args.side <= 512:
        parser.error("--side must be between 64 and 512")
    if not 1 <= args.repeats <= 20:
        parser.error("--repeats must be between 1 and 20")
    return args


def main() -> int:
    args = _parse_args()
    report = run_benchmark(args.side, args.repeats)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        runtime = report["runtime_seconds_per_glyph_crop"]["median"]
        work = report["work"]
        memory = report["memory"]
        print(f"Median runtime per glyph crop: {runtime:.6f} s")
        print(f"Peak refinement samples: {work['peak_refinement_sample_count']}")
        print(
            "Median cross-section probes per edge point: "
            f"{work['median_cross_section_probes_per_edge_point']:.2f}"
        )
        print(f"Median spline fits per edge: {work['median_spline_fits_per_edge']:.1f}")
        print(
            "Retained refined geometry array bytes: "
            f"{memory['retained_refined_geometry_array_bytes']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
