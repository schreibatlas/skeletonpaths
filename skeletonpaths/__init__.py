"""Skeleton graphs and candidate path extraction from binary masks."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .core import (
    DEFAULT_MAX_PATHS,
    DEFAULT_RANKING_POLICY,
    DEFAULT_SEARCH_LIMITS,
    DisconnectedGraphError,
    NoFeasiblePathError,
    PathRankingPolicy,
    PathScore,
    PathSearchLimitError,
    PathSearchLimits,
    PathSelection,
    SkeletonAnalysis,
    SkeletonEdge,
    SkeletonGraph,
    SkeletonImage,
    SkeletonNode,
    SkeletonPath,
    SkeletonWalk,
    TopologyPathInventory,
    TopologyRoute,
    analyze_mask,
    build_skeleton_graph,
    covering_walk,
    graph_from_mask,
    graph_from_skeleton,
    prepare_topology_paths,
    prune_spurs,
    rank_paths,
    rank_topology_paths,
    select_path,
    select_topology_path,
)

try:
    __version__ = version("skeletonpaths")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "DEFAULT_MAX_PATHS",
    "DEFAULT_RANKING_POLICY",
    "DEFAULT_SEARCH_LIMITS",
    "DisconnectedGraphError",
    "NoFeasiblePathError",
    "PathRankingPolicy",
    "PathScore",
    "PathSearchLimitError",
    "PathSearchLimits",
    "PathSelection",
    "SkeletonAnalysis",
    "SkeletonEdge",
    "SkeletonGraph",
    "SkeletonImage",
    "SkeletonNode",
    "SkeletonPath",
    "SkeletonWalk",
    "TopologyPathInventory",
    "TopologyRoute",
    "__version__",
    "analyze_mask",
    "build_skeleton_graph",
    "covering_walk",
    "graph_from_mask",
    "graph_from_skeleton",
    "prepare_topology_paths",
    "prune_spurs",
    "rank_paths",
    "rank_topology_paths",
    "select_path",
    "select_topology_path",
]
