# Direct-Source Reference Collector Recon Design

> 2026-06-15 · Design update for simplifying `do-homework [A]`
> reconnaissance while preserving broad Canvas discovery, complete original
> source evidence, and Main Agent source judgment.

## Context

The previous source reconnaissance design split homework source discovery into
`metadata_scout`, `reading_plan.compact.json`, `content_scout`,
`source_findings.compact.md`, and appendix evidence files. Real proposal runs
showed that this made `investigation/` noisy and turned a bounded source search
into many intermediate JSON/Markdown artifacts. It also encouraged the Main
Agent to reason about scout summaries instead of reading complete original
sources.

The new design keeps `sub-skills/tools/assignment-recon.md` as the mandatory
Canvas reconnaissance workflow. The broad system scan remains necessary because
Canvas assignment shells are often incomplete and the real spec may live in a
module page, attached PDF, syllabus section, file metadata, or announcement.

The change removes the source-scout reading-plan pipeline and replaces it with
an always-on `reference_collector` child role. This child does not interpret the
assignment. It only filters, downloads, and preserves complete original source
materials under `references/` so the Main Agent can read a smaller but complete
source set.

## Goals

1. Keep broad Canvas raw snapshot collection in `assignment-recon`.
2. Add Canvas announcements to standard assignment reconnaissance.
3. Always run a narrow `reference_collector` for homework reconnaissance.
4. Preserve complete original source evidence in `references/`, including
   Canvas-native JSON blocks copied verbatim.
5. Keep the Main Agent as the only actor that interprets source meaning, writes
   terminal reconnaissance artifacts, and decides source sufficiency.
6. Remove normal generation of `reading_plan.compact.json`,
   `source_findings.compact.md`, source body fragments, source index appendix,
   and source scout receipts.
7. Preserve the existing three-layer reference companion pattern for files:
   original file, extracted text, and link annotation manifest when applicable.

## Non-Goals

- Do not remove `assignment-recon.md`.
- Do not remove system-level Canvas discovery of modules, module items, pages,
  file metadata, assignment files, rubric, syllabus, or front page.
- Do not let a child subagent write `spec.md`, `rubric.md`, `review_a.json`,
  `recon_summary.md`, `explore_context.md`, `pipeline_design.md`, or user
  alignment decisions.
- Do not create a summarized source-finding interface that replaces original
  source reading.
- Do not redesign `task-orchestrator.md` execution stages in this change.

## Architecture

The new source flow is:

```text
Main Agent
  -> assignment-recon Stage 1 raw Canvas snapshot
  -> reference_collector child filters and preserves references
  -> Main Agent reads references and terminal Canvas shells
  -> Main Agent writes spec/rubric/review/recon_summary/explore_context
```

The `reference_collector` is not a `metadata_scout`, `content_scout`, or
`source_spec` child. It is a source preservation worker. Its output is a
curated `references/` tree plus `references/REFERENCE_INDEX.md`, not compact
claims.

## Stage Flow

### Stage 1: Raw Canvas Snapshot

`assignment-recon` fetches raw JSON snapshots into `<work_dir>/canvas/`:

```text
canvas/assignment.json
canvas/rubric.json
canvas/front-page.json
canvas/syllabus.json
canvas/modules.json
canvas/module-items-<module_id>.json
canvas/assignment-files.json
canvas/announcements.json
canvas/page-<page_url>.json
canvas/file-<file_id>.json
```

Announcements become part of the standard raw snapshot. If Canvas returns no
announcements, that is a valid checked state.

Raw snapshot collection can be broad. Broad collection is not broad task
context. The next stage narrows what becomes a reference for Main Agent reading.

### Stage 2: Reference Candidate Discovery

`reference_collector` reads the raw Canvas snapshots and finds task-relevant
candidate sources. Candidate origins include:

- files attached to the assignment shell;
- files returned by `assignment-files`;
- file IDs or external URLs in assignment description, front page, syllabus,
  module pages, or relevant Canvas pages;
- Canvas rubric body and rubric criteria;
- syllabus sections related to the assignment family, grading, collaboration,
  AI/tool use, submission rules, late policy, or academic integrity;
- module items whose title, page URL, or file name strongly matches the current
  assignment;
- Canvas page bodies for pages whose title or module context strongly matches
  the current assignment;
- announcements whose course, title, body, dates, assignment names, or linked
  files match the current assignment;
- file metadata whose display name, folder path, content type, or updated time
  indicates assignment relevance.

The collector uses these classifications only for indexing:

```text
direct_spec
rubric_source
syllabus_constraint
required_input
announcement_update
supporting_only
irrelevant
forbidden_or_stale
blocked
```

A direct-spec strong match is a candidate that has assignment-relevant title or
origin and body-level confirmation. Body-level confirmation can be opening text,
first PDF pages, page body, announcement body, or rubric content naming the
deliverable, format, deadline, sections, submission method, grading rule, prompt,
or required input.

### Stage 3: Reference Preservation

The collector downloads or copies only task-relevant references. It must not
download every course file.

Download file references under source-adjacent directories:

```text
references/source_docs/<slug>/
  <slug>.pdf
  <slug>.pdf.txt
  <slug>.pdf.links.json

references/slides/<slug>/
  <slug>.pptx
  <slug>.pptx.txt

references/external/<slug>.txt
```

For every fetched PDF that may affect the assignment spec, rubric, inputs, or
blockers, the collector preserves three layers:

1. original PDF;
2. extracted visible text as `.pdf.txt`;
3. link annotations as `.pdf.links.json`.

If a PDF has no links, write an empty `[]` link manifest. If text or link
extraction fails, record the failure in `investigation/unreachable.txt` with the
source path and error.

### Stage 4: Canvas-Native Source Preservation

When task-relevant information lives directly in raw Canvas JSON rather than a
downloadable file, the collector copies the relevant JSON block verbatim into
`references/canvas_native/`.

Examples:

```text
references/canvas_native/syllabus-project-policy/
  source.json
  source.txt
  ORIGIN.md

references/canvas_native/announcement-proposal-deadline-update/
  source.json
  source.txt
  ORIGIN.md

references/canvas_native/page-project-proposal-guidelines/
  source.json
  source.txt
  ORIGIN.md
```

Integrity rules:

- `source.json` is copied from the raw Canvas snapshot without paraphrase.
- If the raw JSON has no structured section boundaries, copy the complete
  relevant object. For syllabus bodies that are not sectioned, copying the full
  `canvas/syllabus.json` object is acceptable.
- `source.txt` is an exact body-text export when `body_text` or equivalent text
  exists.
- `ORIGIN.md` records source path, copied object identifier, classification, and
  why the source was preserved. It must not summarize the source requirements.

This preserves completeness while avoiding Main Agent scans over unrelated
Canvas JSON.

### Stage 5: Reference Index

The collector writes `references/REFERENCE_INDEX.md`.

The index is a directory map, not a source summary. It may include:

```md
| Classification | Reference Path | Raw Origin | Reason Selected | Companions |
|---|---|---|---|---|
| direct_spec | references/source_docs/project-proposal-handout/project-proposal-handout.pdf | canvas/file-658071.json | title and assignment module match Project Proposal | pdf, txt, links |
| syllabus_constraint | references/canvas_native/syllabus-project-policy/source.json | canvas/syllabus.json | syllabus contains project policy, grading, or AI sections | json, txt |
| announcement_update | references/canvas_native/announcement-proposal-deadline/source.json | canvas/announcements.json#id=... | announcement title/body matches assignment name or due date | json, txt |
```

`Reason Selected` explains selection logic. It must not restate source
requirements or replace reading the referenced source.

### Stage 6: Main Agent Source Reading

After `reference_collector` finishes, the Main Agent reads:

```text
references/REFERENCE_INDEX.md
references/source_docs/**/*
references/slides/**/*
references/external/**/*
references/canvas_native/**/source.json
references/canvas_native/**/source.txt
canvas/assignment.json
canvas/rubric.json
```

The Main Agent may read `canvas/syllabus.json` directly only when the preserved
canvas-native syllabus reference is missing, incomplete, or flagged as blocked.
The normal path is to read the preserved complete source copy under
`references/canvas_native/`.

The Main Agent does not read unrelated module item JSON, broad course file
metadata, irrelevant pages, stale source-scout appendix files, or prior
submission artifacts.

### Stage 7: Terminal Reconnaissance Artifacts

The Main Agent writes:

```text
spec.md
problem.md
investigation/explore_manifest.json
investigation/explore_context.md
investigation/recon_summary.md
investigation/rubric.md
investigation/unreachable.txt
investigation/review_a.json
pipeline_design.md
```

Normal runs do not write:

```text
investigation/reading_plan.compact.json
investigation/reading_plan.compact.approved.json
investigation/source_findings.compact.md
investigation/_appendix/source_index.json
investigation/_appendix/body_evidence_fragments/
investigation/_appendix/scout_receipts/
```

If stale copies exist from older runs, ignore them for source context and prefer
cleaning the workbench before rerunning.

## Reference Collector Contract

The collector may:

- read raw Canvas snapshots;
- classify candidate sources for selection;
- download task-relevant files;
- extract PDF text and PDF link annotations;
- export PPTX or external text where available;
- copy Canvas-native JSON blocks verbatim;
- write `references/REFERENCE_INDEX.md`;
- append blocked resource lines to `investigation/unreachable.txt`.

The collector must not:

- write `spec.md`, `rubric.md`, `review_a.json`, `recon_summary.md`,
  `explore_context.md`, `pipeline_design.md`, or alignment artifacts;
- paraphrase Canvas-native source contents;
- summarize requirements as the only evidence path;
- create `reading_plan.compact.json`, `source_findings.compact.md`, source body
  fragments, source index appendix, or source scout receipts;
- decide final source sufficiency or user-facing interpretation;
- use prior submissions, stale pipelines, old reviews, transcripts, or previous
  draft outputs as task context unless the user explicitly allowlists them.

## Review JSON Shape

`investigation/review_a.json` records Main Agent self-checks instead of scout
evidence. The expected shape includes:

```json
{
  "assignment_shell_checked": true,
  "rubric_checked": true,
  "syllabus_checked": true,
  "announcements_checked": true,
  "reference_collector_used": true,
  "source_scout_pipeline_used": false,
  "reference_index_checked": true,
  "direct_spec_sources": [],
  "rubric_sources": [],
  "required_inputs": [],
  "canvas_native_sources": [],
  "relevant_announcements": [],
  "downloaded_references": [],
  "pdf_link_manifests_checked": true,
  "blocked_sources": [],
  "forbidden_or_stale_sources": [],
  "supporting_sources_skipped": [],
  "inputs_complete": true,
  "parent_self_check_complete": true,
  "verdict": "proceed"
}
```

Runs blocked by missing assignment shell, missing direct-spec source, failed
required download, or unreadable required source set `verdict` to `blocked` and
name the next recovery action.

## Directory Boundaries

`references/` is the source evidence interface for Main Agent reading.

`investigation/` contains terminal reconnaissance artifacts and run status. It
does not contain source scout working files in standard runs.

`canvas/` contains raw snapshots. It is still durable evidence, but the Main
Agent should normally read only assignment/rubric shells directly and use
`references/canvas_native/` for narrowed complete Canvas-native source copies.

## Error Handling

- No announcements returned: record checked with an empty relevant list.
- Announcement command unavailable or failed: record in `unreachable.txt` and
  `review_a.json`; do not block unless the assignment explicitly depends on an
  announcement.
- PDF download failed: block only when the file is direct spec, rubric source,
  or required input.
- PDF text extraction failed but direct PDF reading is possible: preserve the PDF,
  record the text extraction issue, and let the Main Agent read the PDF directly.
- PDF link extraction failed: record the failure; block only when links are
  required to reach the spec/input.
- Canvas-native object too large: copy the complete relevant object. If the JSON
  is not sectioned and relevance cannot be isolated safely, copy the full source
  object rather than paraphrasing.

## Testing Strategy

Policy tests should assert:

- standard homework reconnaissance includes `reference_collector`;
- `assignment-recon` still fetches broad Canvas raw snapshots;
- announcements are part of Stage 1;
- `references/REFERENCE_INDEX.md` is the collector interface;
- Canvas-native task-relevant sources are copied verbatim under
  `references/canvas_native/`;
- normal runs do not create `reading_plan.compact.json`,
  `source_findings.compact.md`, source index appendix, source body fragments, or
  source scout receipts;
- Main Agent terminal artifacts remain `spec.md`, `rubric.md`, `review_a.json`,
  `recon_summary.md`, and `explore_context.md`;
- PDF references preserve original file, extracted text, and link annotations;
- child output is not accepted as source interpretation or final assignment
  judgment.

## Migration Notes

This design supersedes the 2026-06-13 source body audit and 2026-06-14 compact
findings source-scout designs for normal homework reconnaissance. Historical
design documents should remain as history. Runtime docs and policy tests should
be updated to describe the direct-source reference collector path as the current
contract.

Existing workbenches with old scout artifacts may be used for audit, but clean
reruns should remove stale `reading_plan.compact*`, `source_findings.compact.md`,
and source-scout appendix artifacts before running the new flow.
