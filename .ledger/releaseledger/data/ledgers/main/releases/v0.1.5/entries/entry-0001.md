---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: v0.1.5
kind: changed
summary: Changed graph construction to contract nearby pixels into radius-aware semantic
  junction regions
status: accepted
audience: null
scopes: []
source_refs:
- git:68e64dd7f63a4c67b70bd4f0d1b147fb72a016cc
paths:
- README.md
- docs/getting-started.md
- docs/guide/graph-construction.md
- docs/reference/api.md
- docs/reference/behavior-contracts.md
- docs/subpixel-centerlines.md
- skeletonpaths/__init__.py
- skeletonpaths/graph.py
- skeletonpaths/hypotheses.py
- skeletonpaths/image.py
- skeletonpaths/model.py
- skeletonpaths/subpixel.py
- tests/test_junction_regions.py
- tests/test_skeletonpaths.py
issues: []
prs: []
sources:
- git:68e64dd7f63a4c67b70bd4f0d1b147fb72a016cc
contributors:
- '@holgern'
breaking: true
internal: false
order: 1
---
