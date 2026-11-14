---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: v0.1.1
kind: added
summary: Added skeleton-only graph construction, optional mask processing, and ranked
  route selections with ambiguity metadata
status: accepted
audience: null
scopes: []
source_refs:
- git:32cac5f2ec488c8d5099d7137910ad8c6a440667
paths:
- .codecrate.toml
- .github/workflows/ci.yml
- .github/workflows/publish.yml
- .pre-commit-config.yaml
- README.md
- examples/01_basic_straight.py
- examples/02_spur_pruning.py
- examples/03_guided_branch_selection.py
- examples/04_loop_detection.py
- examples/05_mask_radius_confidence.py
- examples/06_inventory_reranking.py
- examples/07_planarcurve_interop.py
- examples/08_route_ambiguity.py
- examples/README.md
- pyproject.toml
- skeletonpaths/__init__.py
- skeletonpaths/core.py
- skeletonpaths/graph.py
- skeletonpaths/image.py
- skeletonpaths/model.py
- skeletonpaths/py.typed
- skeletonpaths/ranking.py
- skeletonpaths/routing.py
- tests/test_dependency_modes.py
- tests/test_examples.py
- tests/test_skeletonpaths.py
issues: []
prs: []
sources:
- git:32cac5f2ec488c8d5099d7137910ad8c6a440667
contributors:
- '@holgern'
breaking: false
internal: false
order: 1
---
