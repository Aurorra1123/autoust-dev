---
name: paper-search
description: Compatibility alias for literature-search. Do not use as a standalone active pipeline tool.
---

# paper-search

This file is a compatibility alias for older workbenches and historical
pipeline designs. It is not a standalone active pipeline tool.

For all new literature work, load and follow
[`literature-search.md`](./literature-search.md).

Historical behavior was arXiv-only metadata search that wrote root-level
`references.bib` and `references.json`. That is no longer the active contract.
arXiv remains available inside `literature-search.md` as one provider among
several, with automatic fallback, access-depth reporting, and manual-download
blocker reporting.

If a legacy `pipeline_design.md` names `paper-search.md`, normalize it to
`literature-search.md` before executing the stage. Keep root-level
`references.bib` only as a compatibility copy of `literature/references.bib`.
