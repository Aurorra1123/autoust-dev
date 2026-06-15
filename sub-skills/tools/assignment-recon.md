---
name: assignment-recon
description: Agent-led Canvas Generic assignment reconnaissance. Inspect Canvas sources through atomic canvascli commands, write a standardized spec.md, locate rubric and inputs, and review whether the assignment is sufficiently understood before any draft generation.
---

# assignment-recon

Use this tool workflow inside `do-homework [A]` to turn Canvas evidence into a
standardized assignment workbench. Its job is to answer:

1. Which Canvas/source materials define the assignment?
2. What must the student produce?
3. What references are available or blocked?
4. Is the assignment understood well enough to enter user alignment?

Runtime invariants:

- Keep Stage 1 broad: inspect all likely Canvas source surfaces before deciding
  the main spec, including assignment, rubric, syllabus, modules, pages, file
  metadata, assignment files, and announcements.
- Always dispatch `reference_collector` after Stage 1. The collector preserves
  complete original task-relevant evidence under `references/`; it does not
  interpret the assignment or write terminal reconnaissance artifacts.
- Treat `canvas/syllabus.json` as a first-class Canvas source: fetch it, read it,
  and record whether it contains assignment requirements, grading criteria,
  submission policy, late policy, academic-integrity rules, AI/tool policy, or
  other course-level constraints.
- For Canvas-native bodies such as assignment, syllabus, front page, pages, and
  announcements, raw Canvas JSON is the canonical evidence. Task-relevant
  Canvas-native source objects must be copied verbatim into
  `references/canvas_native/` with exact text exports when available.
- Write `spec.md` as a concise evidence-grounded report, not as a raw dump.
- Keep `problem.md` as compatibility only; downstream planning reads `spec.md`.
- Do not let a helper script or child worker decide the final main-spec
  judgment.
- Do not create `reading_plan.compact.json`, `source_findings.compact.md`,
  source index appendix files, source body fragments, or source scout receipts
  in standard runs.

## Capability

- `assignment_recon` - `(course_id, assignment_id, work_dir)` -> a
  Canvas Generic-style reconnaissance workbench with `spec.md`, `references/`,
  and `investigation/`

## Workbench Contract

The workflow writes this structure under `<work_dir>`:

```text
<work_dir>/
├── canvas/
│   ├── assignment.json
│   ├── rubric.json
│   ├── front-page.json
│   ├── syllabus.json
│   ├── modules.json
│   ├── module-items-<mid>.json
│   ├── announcements.json
│   ├── page-<page_url>.json
│   └── file-<file_id>.json
├── spec.md
├── problem.md
├── references/
│   ├── REFERENCE_INDEX.md
│   ├── source_docs/
│   ├── slides/
│   ├── external/
│   ├── canvas_native/
│   │   └── <slug>/
│   │       ├── source.json
│   │       ├── source.txt
│   │       └── ORIGIN.md
│   └── pdf_links.json
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   └── review_a.json
└── pipeline_design.md
```

`canvas/` stores raw JSON snapshots from atomic `canvascli` commands.
`spec.md` is the standardized reconnaissance report written by the agent after
reading the sources. `problem.md` is only a thin compatibility summary for older
tools. `references/` stores fetched PDFs, Google Docs text, starter code, data,
PPTX exports, optional Canvas convenience exports, or other materials. New workbenches
should keep source-adjacent companion files together instead of flattening every
artifact:

```text
references/
├── source_docs/
│   └── <slug>/
│       ├── <slug>.pdf
│       ├── <slug>.pdf.txt
│       └── <slug>.pdf.links.json
├── slides/
│   └── <slug>/
│       ├── <slug>.pptx
│       └── <slug>.pptx.txt
├── external/
│   └── <slug>.txt
├── canvas_native/
│   └── <slug>/
│       ├── source.json
│       ├── source.txt
│       └── ORIGIN.md
└── pdf_links.json
```

Existing flat `references/<name>.pdf` layouts remain valid. The invariant is
that companion files stay beside their source. New policy text may refer to
`references/**/*.pdf.links.json`; old `references/*.pdf.links.json` manifests
are still accepted. `references/REFERENCE_INDEX.md` is a directory index, not a
source summary; it points the Main Agent to complete original files and
verbatim Canvas-native copies.

Directory boundary: `references/` is the source evidence interface for Main
Agent reading. `investigation/` records terminal reconnaissance artifacts,
rubric findings, unreachable resources, and the investigation review. Standard
runs must not write `reading_plan.compact.json`,
`reading_plan.compact.approved.json`, `source_findings.compact.md`,
source index appendix files, source body fragments, or source scout receipts.

For Canvas-native bodies, keep the raw `canvas/*.json` snapshot and also copy
the selected task-relevant source object verbatim into
`references/canvas_native/<slug>/`. Derived readable exports must point back to
the raw JSON origin and must not replace the verbatim `source.json`.

## Non-goal: no script-led spec generation

Do **not** replace this workflow with a standalone script that writes the final
assignment spec. The production flow is agent-led, following the stages below:
the agent reads the sources, decides which source is authoritative, writes the
standardized `spec.md`, records `review_a.json`, and classifies the output mode.

If a future helper script is added, it may only reduce mechanical shell work
such as saving JSON snapshots or downloading a specific file. It must not decide
which source is the main spec, write the final `spec.md`, write
`review_a.json`, or classify the output mode.

## Stage 1 - fetch-context

Pull every read source for this assignment. Run commands from the AutoStudy repo
with the venv binary:

```bash
.venv/bin/canvascli assignment <assignment_id> -c <course_id> > "<work_dir>/canvas/assignment.json"
.venv/bin/canvascli rubric <assignment_id> -c <course_id> > "<work_dir>/canvas/rubric.json"
.venv/bin/canvascli front-page -c <course_id> > "<work_dir>/canvas/front-page.json"
.venv/bin/canvascli syllabus -c <course_id> > "<work_dir>/canvas/syllabus.json"
.venv/bin/canvascli modules -c <course_id> > "<work_dir>/canvas/modules.json"
.venv/bin/canvascli assignment-files <assignment_id> -c <course_id> > "<work_dir>/canvas/assignment-files.json"
.venv/bin/canvascli announcements > "<work_dir>/canvas/announcements.json"
```

Zero announcements is a valid checked state: keep `canvas/announcements.json`
as the Stage 1 record. If the announcements command fails or is unavailable,
record the failure in `investigation/unreachable.txt`; Stage 4 later records
the `announcements_checked` review field and decides whether the failure blocks
progress.

Then read `modules.json` and fetch items for **every** module, not only the
first apparent match:

```bash
.venv/bin/canvascli module-items <module_id> -c <course_id> > "<work_dir>/canvas/module-items-<module_id>.json"
```

For module items with `type == "Page"` and a `page_url`, fetch the page:

```bash
.venv/bin/canvascli page <page_url> -c <course_id> > "<work_dir>/canvas/page-<safe_page_url>.json"
```

For file ids found in assignment description, front page, syllabus, pages,
module item `content_id`, or `assignment-files.json`, fetch file metadata:

```bash
.venv/bin/canvascli file <file_id> > "<work_dir>/canvas/file-<file_id>.json"
```

Note: `canvascli file` takes only `<file_id>` — no `-c` flag needed because file
IDs are globally unique across courses.

Fetch `canvas/syllabus.json` even when another source already looks like the
main spec. The syllabus often contains grading language, assignment families,
submission policies, collaboration rules, AI/tool policies, or academic
integrity constraints that are not repeated on the assignment page. Stage 3
records syllabus relevance in `spec.md`; Stage 4 records review status in
`investigation/review_a.json`.

Stage 3 may cite raw fallback evidence pointers such as:

```text
canvas/syllabus.json#body_text:Assessment and Grading
canvas/syllabus.json#body_text:Grading Rubrics
canvas/syllabus.json#body_text:Course AI Policy
```

If a derived syllabus note or export is useful for a human reader, it may be
written under `references/`, but it is not required and must not become the only
evidence path. The normal downstream syllabus read interface is the preserved
Canvas-native copy under `references/canvas_native/`; raw `canvas/syllabus.json`
is a fallback when the preserved copy is missing, incomplete, or blocked.

Do not write terminal `spec.md` or `investigation/rubric.md` during Stage 1.
Stage 1 collects broad raw snapshots; Stage 2 narrows and preserves the
task-relevant source set.

## Stage 2 - collect-references

Always dispatch `reference_collector` after Stage 1 raw Canvas snapshots.

The collector reads raw Canvas snapshots and preserves task-relevant source
evidence under `references/`. It does not write `spec.md`,
`investigation/rubric.md`, `investigation/review_a.json`,
`investigation/recon_summary.md`, `investigation/explore_context.md`,
and must not write `source_findings.compact.md` or
`reading_plan.compact.json`.

Fetch only materials needed to understand or execute the assignment:

- direct assignment files
- PDFs or files linked from module items or Canvas pages
- Google Docs / Google Slides / instructor external pages when publicly
  fetchable
- starter code, scaffold archives, data files, or GitHub links
- supporting slides/readings when the spec references them
- Canvas-native assignment, rubric, page, syllabus, or announcement evidence

Save them under `<work_dir>/references/`. For PDFs, also save extracted text
and link annotations beside the file. Claude Code's built-in Read tool can read
PDF files directly and return their text content. Alternatively, use PyMuPDF
(`python3 -c "import fitz; ..."`) if the agent needs to extract text
programmatically. For Google Docs, attempt anonymous text export and save it
under `references/external/<slug>.txt`.

### Reference Collector

Classifications for `references/REFERENCE_INDEX.md`:

```text
direct_spec | rubric_source | syllabus_constraint | required_input |
announcement_update | supporting_only | irrelevant | forbidden_or_stale | blocked
```

The collector downloads file references only when they are direct specs, rubric
sources, required inputs, announcement updates, or directly required supporting
sources. It must not download every course file.

A direct-spec source has assignment-relevant title or origin and body-level
confirmation. Body-level confirmation can be opening text, first PDF pages,
page body, announcement body, or rubric content naming the deliverable, format,
deadline, sections, submission method, grading rule, prompt, or required input.

Write `references/REFERENCE_INDEX.md` as a directory index, not a summary. It
may list classification, reference path, raw origin, selection reason, and
companion files. The selection reason explains why the source was preserved; it
must not restate requirements or replace reading the referenced source.

The collector must not write `spec.md`, `investigation/rubric.md`,
`investigation/review_a.json`, `investigation/recon_summary.md`,
`investigation/explore_context.md`, `pipeline_design.md`, or user alignment
artifacts. It must not summarize source requirements as the evidence path.
Standard runs must not create `reading_plan.compact.json`,
`source_findings.compact.md`, source index appendix files, source body
fragments, or source scout receipts.

### Canvas-Native Preservation Contract

When task-relevant information lives in Canvas-native JSON, copy the relevant
object verbatim to:

```text
references/canvas_native/<slug>/source.json
references/canvas_native/<slug>/source.txt
references/canvas_native/<slug>/ORIGIN.md
```

`source.json` must be copied from the raw Canvas snapshot without paraphrase. If
the raw JSON has no safe section boundary, copy the complete source object.
For syllabus bodies that are not sectioned, copying the complete
`canvas/syllabus.json` object is acceptable.

`source.txt` is an exact body-text export when `body_text` or equivalent text
exists. `ORIGIN.md` may record origin, copied object id, classification, and
selection reason, but must not summarize requirements. The collector must not
paraphrase Canvas-native source contents.

The Main Agent normally reads:

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

`canvas/syllabus.json` may be read directly only when the preserved
Canvas-native syllabus reference is missing, incomplete, or blocked.

### PDF Link Annotation Extraction

This rule is part of the `reference_collector` contract.

PDF text extraction is not complete source extraction. Human readers can see and
click blue linked text because PDF viewers combine the visible text layer with
link annotations; tools such as `pdftotext` or `page.get_text()` usually return
only the visible text and omit the target URL.

For every fetched PDF that may affect the assignment spec, also extract link
annotations and save them beside the PDF:

```text
references/<name>.pdf
references/<name>.pdf.txt
references/<name>.pdf.links.json
references/source_docs/<slug>/<slug>.pdf
references/source_docs/<slug>/<slug>.pdf.txt
references/source_docs/<slug>/<slug>.pdf.links.json
```

Use PyMuPDF `page.get_links()` or an equivalent PDF annotation reader. The link
manifest should be a JSON array with generic fields:

```json
[
  {
    "source_pdf": "references/example.pdf",
    "page": 1,
    "anchor_text": "visible linked words near the link rectangle",
    "uri": "https://example.invalid/resource",
    "rect": [0, 0, 0, 0]
  }
]
```

If a PDF has no external links, write an empty `[]` manifest. If link extraction
fails, record the failure in `investigation/unreachable.txt` with the PDF path
and tool error. Do not specialize this rule by URL domain, resource type, or
course. The generic contract is: preserve every URI embedded in PDF link
annotations so later spec, rubric, input, and blocker decisions can decide
whether each URL matters.

When useful, also write an aggregate `references/pdf_links.json` that concatenates
all per-PDF link records for quick review; the sibling `*.pdf.links.json`
manifests remain the source-adjacent evidence. New workbenches may store these
manifests under nested source directories, so review using
`references/**/*.pdf.links.json` while accepting legacy flat
`references/*.pdf.links.json`.

Record resources that cannot be fetched in
`<work_dir>/investigation/unreachable.txt`, with a short reason:

```text
<url or file id> - login wall / download failed / password required / content unclear
```

Do not over-download every course file. Download only direct, rubric, input,
announcement, or directly required supporting sources discovered from
assignment, module, page, syllabus, front page, announcement, or clear external
spec links.

After Stage 2, the Main Agent reads the preserved references and writes or
revises `spec.md` in Stage 3 if the collected materials changed the main spec
judgment, deliverables, rubric summary, or gaps.

## Stage 3 - write source judgments

After `reference_collector` has produced `references/REFERENCE_INDEX.md`, the
Main Agent reads the index and the preserved references named there. Then write
the standardized `spec.md`. This is not raw JSON and not copied PDF text. It is
a Main Agent report, in the agent's words, grounded by the preserved sources:

```text
# <COURSE> - <Assignment>

## Assignment Metadata
- Course:
- Course ID:
- Assignment:
- Assignment ID:
- Points:
- Due:
- Submission types:
- Allowed extensions:

## Source Trail
- Assignment page:
- Canvas rubric:
- Front page:
- Syllabus:
- Announcements:
- Modules:
- Pages:
- Files:
- External URLs:

## Syllabus Relevance
State whether the preserved syllabus source adds assignment-specific
requirements, grading/rubric criteria, assessment-family context, submission or
late policy, collaboration rules, academic-integrity constraints, AI/tool
policy, or no relevant constraints for this assignment. Cite
`references/canvas_native/<slug>/source.json` / `source.txt` when preserved, or
record why raw `canvas/syllabus.json` fallback was required.

## Main Spec Judgment
State which source appears to be the main spec and why.

## Deliverables
List concrete files / uploads / text entries the student must produce.

## Requirements / Tasks
List the actual questions, tasks, constraints, sections, datasets, or code work.

## Rubric / Grading
Briefly summarize known grading criteria and cite the preserved source paths.

## Inputs / References
List required PDFs, readings, datasets, starter code, Google Docs, slides, or
other references, and whether each has been fetched into references/.

## Gaps / User Questions
List missing sources, unreachable materials, or decisions only the user can make.

## Evidence Pointers
Point to `references/REFERENCE_INDEX.md`, preserved reference paths,
`references/canvas_native/**/source.json`, and terminal Canvas shell files that
justify the summary.
```

Good generic result: `spec.md` explains which source is authoritative, why
nearby Canvas sources are supporting or irrelevant, what the syllabus adds or
does not add, and which concrete deliverables are required. It does not paste an
entire PDF, page, or external document.

Locate grading criteria in this order:

1. Canvas rubric from `canvas/rubric.json`.
2. Preserved syllabus constraints under `references/canvas_native/`, especially
   assessment tables, grading rubrics, academic integrity, collaboration,
   AI/tool policy, late/submission policy, and assignment-family descriptions.
3. Preserved reference text, searching for words such as `rubric`, `criteria`,
   `graded on`, `points breakdown`, `you will be evaluated on`, and
   `assessment`.
4. Preserved Canvas-native pages, announcements, and external URLs.

Write `<work_dir>/investigation/rubric.md`.

If grading criteria come from the syllabus, cite the preserved
`references/canvas_native/<slug>/source.json` copy with a specific body-text
section pointer, or record why raw `canvas/syllabus.json` fallback was required.
A rubric search is incomplete when the only downstream evidence is a compressed
summary of syllabus grading criteria.

If no rubric is found, write:

```text
RUBRIC NOT FOUND - use assignment/spec criteria if present
```

Do not stop only because Canvas rubric is absent. Many courses put useful
grading criteria in PDFs, pages, external specs, announcements, or the syllabus
instead of the Canvas rubric field.

## Stage 4 - review investigation

For proposal/research/open-ended assignments, run a Main Agent parent self-check
after `reference_collector` has produced `references/REFERENCE_INDEX.md`. The
normal `[A]` path has exactly one standard source-preservation child role:
`reference_collector`. The Main Agent checks preserved references,
Canvas-native source copies, downloaded files, PDF link manifests, unreachable
resources, forbidden/stale sources, and terminal artifacts.

Before writing the review verdict, run the parent self-check. The reference
index is not a terminal reconnaissance verdict: it is a directory index for
complete original evidence and must not summarize requirements as a substitute
for source reading. If preserved source evidence exists while terminal
reconnaissance artifacts are missing, write a recover/blocking `review_a.json`
or append `stage_reviews/process_concerns.jsonl`; the entry must name the
missing `spec.md`, `investigation/rubric.md`, or
`investigation/review_a.json` artifact and state whether the next action is
inline completion, replacement coordinator, user recovery, or stop.
Rule for automated checks: missing `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` must write a recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`.

Reviewer must read:

```text
<work_dir>/spec.md
<work_dir>/investigation/rubric.md
<work_dir>/investigation/unreachable.txt
<work_dir>/references/REFERENCE_INDEX.md
<work_dir>/references/source_docs/**/*
<work_dir>/references/slides/**/*
<work_dir>/references/external/**/*
<work_dir>/references/canvas_native/**/source.json
<work_dir>/references/canvas_native/**/source.txt
<work_dir>/canvas/assignment.json
<work_dir>/canvas/rubric.json
```

Broad module indexes, unrelated file metadata, previous submissions, stale
pipelines, old reviews, transcripts, and previous draft outputs are
recovery/debug/audit reads unless the user explicitly allowlists them.

Write strict JSON to `<work_dir>/investigation/review_a.json`:

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

Allowed verdicts:

- `proceed` - enough grounded context exists to ask the user for supplements and
  then design the pipeline.
- `recover` - sources are probably obtainable, but another fetch, user-provided
  URL, or pasted material is needed.
- `blocked` - assignment shell, direct-spec source, required download, or
  required source body is missing or unreadable and no local recovery path is
  currently available.
- `stop` - the assignment cannot be understood or executed with available
  sources.

If `verdict != "proceed"`, do not proceed silently. Surface the gap in
`do-homework [B]`.

For proposal/research/open-ended assignments, `verdict` must not be `proceed`
unless the Main Agent has read the preserved direct-spec source and any
available methods/topic-selection guidance, or `review_a.json` records why such
guidance is unavailable. Supporting topic context must be preserved and read
enough to inform the topic choice or explicitly judged unnecessary. Reading
budget overruns, too-broad reading, too-narrow reading, missed sources, and
misreads must be recorded in `review_a.json` and surfaced in
`recon_summary.md`. Required source candidates that are blocked or unavailable
require `recover` unless they are explicitly excluded with evidence.

## After Stage 4 - classify-output

Classify the output mode from `spec.md`, `investigation/rubric.md`,
`canvas/assignment.json`, and `references/`.

Use Canvas Generic modes:

| Mode | Typical signals |
|---|---|
| `doc_prose` | essay, report, critique, reflection, text submission |
| `pdf_annotated` | annotated reading PDF, highlights, margin notes, answer blanks |
| `pdf_typed` | problem set, math notation, typed PDF solution |
| `code` | source files, starter code, autograder, `.py` / `.js` / `.ipynb` |
| `form_answers` | short question list for online text entry |
| `slides` | presentation deck, PPT, PDF slides |
| `mixed` | multiple deliverable shapes |

Write the preliminary classification at the top of
`<work_dir>/pipeline_design.md`:

```text
Output mode: mixed (code + doc_prose + slides)

Reason:
- spec requires ...
- submission type allows ...
- references include ...
```

Full pipeline stages are designed later by `do-homework [C]` after the user
supplement checkpoint. This post-review classification only identifies the
shape.

## Thin problem.md compatibility

After `spec.md` is stable, write `<work_dir>/problem.md` as a short
compatibility file for older tools. It should point to `spec.md`, summarize
deliverables and requirements, and list reference paths. It must not paste
entire PDFs or replace `spec.md` as the source of truth.

## Quality Bar

Before returning to `do-homework [B]`:

1. `spec.md` is a standardized report with concrete deliverables and source
   trail.
2. `canvas/` contains snapshots for assignment, rubric, front page, syllabus,
   modules, announcements, every inspected module's items, and relevant
   pages/files.
3. `spec.md` contains an explicit `Syllabus Relevance` judgment backed by
   preserved `references/canvas_native/<slug>/source.json` / `source.txt`
   pointers, or records why raw `canvas/syllabus.json` fallback was required.
   If the syllabus could not be fetched, `investigation/unreachable.txt`
   explains why.
4. `references/REFERENCE_INDEX.md` exists and is a directory index, not a
   summary of requirements.
5. `references/` contains every reachable material needed to understand the
   assignment, such as fetched PDFs, decks, external text exports, starter code,
   datasets, and verbatim Canvas-native copies under `references/canvas_native/`.
6. `investigation/rubric.md` records Canvas, syllabus, or spec-based grading
   criteria, or clearly says rubric was not found. When syllabus contributes
   criteria, `investigation/rubric.md` must cite preserved
   `references/canvas_native/` section pointers, or record why raw
   `canvas/syllabus.json` fallback was required; summary-only output is
   incomplete.
7. `investigation/unreachable.txt` lists blocked resources.
8. `investigation/review_a.json` has a verdict and records
   `announcements_checked`, `reference_collector_used`,
   `source_scout_pipeline_used: false`, `reference_index_checked`,
   `canvas_native_sources`, `downloaded_references`, and
   `pdf_link_manifests_checked`.
9. `pipeline_design.md` starts with the preliminary output mode.
10. The parent self-check has confirmed that missing `spec.md`,
    `investigation/rubric.md`, or `investigation/review_a.json` forces a
    recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`
    record instead of a silent stop.

## Source Selection Philosophy

- Inspect broadly and decide late.
- Do not stop at the first title match.
- Do not assume assignment description is authoritative.
- Do not assume modules are irrelevant when assignment description has a link.
- Treat duplicate sources as corroboration.
- Label nearby context as supporting context instead of hiding it.
- Rank candidates broadly, then preserve task-relevant originals under
  `references/`.
- Use `reference_collector` for source preservation; the Main Agent remains the
  final judge and reads `references/REFERENCE_INDEX.md`, preserved references,
  Canvas-native source copies, and terminal Canvas shells before writing
  `spec.md`.
- Keep Canvas API internals in `canvascli`; AutoStudy uses the CLI contract.

## Cross-references

- Called from: `tasks/do-homework.md` step `[A]`
- Consumed by: `tasks/task-orchestrator.md`, `tools/writing-helper.md`,
  `tools/code-writer.md`, and `tools/slide-maker.md`
- Depends on: `tools/canvascli-api.md` atomic context commands,
  `canvascli download`, PDF text extraction, and fetchable external URLs

## Pitfalls

1. **Assignment description can be empty.** The real spec may live in a module
   file, page, external document, or syllabus.
2. **A valid source can appear twice.** Treat duplicate links across assignment
   descriptions, modules, pages, or syllabus as corroboration, not confusion.
3. **Front page 404 is normal.** Record it and keep going.
4. **Rubric can be absent from Canvas.** Search spec, references, modules, and
   syllabus before declaring it missing.
5. **Do not over-download every course file.** Download direct, rubric, input,
   announcement, or directly required supporting sources, not arbitrary folder
   trees.
6. **External Google Docs may be the main spec.** Try to fetch their text; if
   blocked, record them in `unreachable.txt` and let `review_a.json` decide
   whether the block is fatal.
7. **Do not turn `spec.md` into a raw dump.** Full source text belongs in
   `references/`; `spec.md` is the decision report.
8. **Do not hide Canvas-native source bodies behind summaries.** If assignment,
   syllabus, front-page, page, or announcement JSON is task-relevant, copy the
   raw source object verbatim into `references/canvas_native/<slug>/source.json`
   and cite that preserved source copy.
9. **Do not paraphrase Canvas-native requirements in `ORIGIN.md`.** It may
   record origin, id, classification, and selection reason only.
10. **Do not confuse metadata with source evidence.** `canvas/file-*.json`,
   module item titles, and source filenames create candidates; they become
   source evidence only when the collector preserves the complete original
   source or records a specific blocker.
