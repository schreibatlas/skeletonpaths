# Ambiguity and ranking

Ranking orders feasible routes. Ambiguity describes whether the available score evidence distinguishes alternatives in a particular selection. It is not confidence, and it is not a probability of correctness.

## Ranking with a guide

When `candidate_xy` is supplied, the effective ranking order is:

1. Symmetric guide distance.
2. For guide distances within `guide_tie_tolerance_px`, endpoint-order error.
3. Measured confidence.
4. Expected-length error, when `expected_length_px` is supplied.
5. Turning cost.
6. Deterministic route identity tie-breakers.

Guide distances are grouped by direct numeric tolerance. They are not decimal-rounded.

## Ranking without a guide

Without `candidate_xy`, ranking considers:

1. Measured confidence.
2. Expected-length error, when `expected_length_px` is supplied.
3. Turning cost.
4. Deterministic route identity tie-breakers.

An absent expected length does not make shorter routes preferable. Turning cost normally helps deterministic ranking only. It reduces ambiguity only when {class}`skeletonpaths.PathRankingPolicy` `turning_cost_is_evidence=True`.

## Scores and policy

{class}`skeletonpaths.PathScore` contains `guide_distance_px`, `endpoint_order_error_px`, `measured_confidence`, `length_error_px`, and `turning_cost`. Distance and length values are in pixels. Turning cost is sampled mean squared turn angle in squared radians. `None` means a score dimension was not applicable or requested, not zero.

The default {class}`skeletonpaths.PathRankingPolicy` is:

| Field | Default |
| --- | ---: |
| `guide_samples` | 64 |
| `turning_samples` | 64 |
| `guide_tie_tolerance_px` | `1e-9` |
| `ambiguity_guide_distance_px` | 0.5 |
| `ambiguity_endpoint_order_px` | 0.5 |
| `ambiguity_confidence` | 0.05 |
| `ambiguity_length_error_px` | 1.0 |
| `ambiguity_turning_cost` | 0.1 |
| `turning_cost_is_evidence` | `False` |

Guide tie tolerance controls ranking grouping. The ambiguity tolerances control overlap of score evidence. They are separate policy concepts.

:::{warning}
{class}`skeletonpaths.SkeletonPath` `confidence` is a measurement propagated from the supplied confidence map, or from default confidence values. It is not the probability that the selected route is correct.
:::

## Route and orientation ambiguity

{class}`skeletonpaths.PathSelection` `ambiguous` is true when a different edge route has overlapping score evidence within the configured ambiguity tolerances. `orientation_ambiguous` is true when the reversed orientation of the same edge route remains indistinguishable within endpoint-order evidence. Both flags can be true at once.

For example, suppose an upper and lower branch form distinct but equally scored edge routes. The selected edge route also has no ordered endpoint evidence to distinguish its forward and reversed geometry. The selection can then report both a competing-route ambiguity and an orientation ambiguity. Neither flag modifies {class}`skeletonpaths.SkeletonPath` `confidence`.

A candidate guide can help distinguish route geometry or route orientation. It remains ranking guidance, not a hard constraint or a statement of physical drawing direction.

The equal-route and guide-disambiguation example is the canonical executable source:

```{literalinclude} ../../examples/08_route_ambiguity.py
:language: python
```
