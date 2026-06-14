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

- Use `metadata_scout` to inspect all likely Canvas source surfaces before
  deciding the main spec. The Main Agent's full source-body reads stay bounded
  to syllabus, direct-spec strong matches, compact findings, and exact parent
  source windows.
- Treat `canvas/syllabus.json` as a first-class Canvas source: fetch it, read it,
  and record whether it contains assignment requirements, grading criteria,
  submission policy, late policy, academic-integrity rules, AI/tool policy, or
  other course-level constraints.
- For Canvas-native bodies such as assignment, syllabus, front page, and pages,
  raw Canvas JSON is the canonical evidence. derived readable artifacts are optional convenience copies, not required gates and not authoritative sources.
  summary-only scout output must never replace raw Canvas JSON; record raw JSON
  paths and JSON-pointer or section-heading evidence in source-body audit.
- Write `spec.md` as a concise evidence-grounded report, not as a raw dump.
- Keep `problem.md` as compatibility only; downstream planning reads `spec.md`.
- Do not let a helper script or scout decide the final main-spec judgment.
- Distinguish metadata discovery from body reading. A Canvas file metadata
  record, module item title, or page link is only a candidate until
  appendix body evidence records how its body was read or why it was
  blocked/excluded and `investigation/source_findings.compact.md` summarizes the
  task-relevant result for the Main Agent.

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
│   ├── page-<page_url>.json
│   └── file-<file_id>.json
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── reading_plan.compact.json
│   ├── source_findings.compact.md
│   ├── _appendix/
│   │   ├── source_index.json
│   │   ├── body_evidence_fragments/
│   │   ├── scout_briefs/
│   │   ├── scout_receipts/
│   │   └── compatibility_aliases/
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
└── pdf_links.json
```

Existing flat `references/<name>.pdf` layouts remain valid. The invariant is
that companion files stay beside their source. New policy text may refer to
`references/**/*.pdf.links.json`; old `references/*.pdf.links.json` manifests
are still accepted. `investigation/` records candidate ranking, body-reading
evidence, compact source findings, rubric findings, unreachable resources, and
the investigation review.

Directory boundary: the `investigation/` top level is the Main Agent's compact
read interface. It may contain only `reading_plan.compact.json`,
`source_findings.compact.md`, `rubric.md`, `unreachable.txt`, `review_a.json`,
and do-homework terminal files such as `explore_manifest.json`,
`explore_context.md`, `recon_summary.md`, `alignment_brief.md`,
`user_notes.md`, and `user_scope.md`. Scout prompts, scout receipts, full
candidate lists, body fragments, source-body audit JSON, transcripts, and
compatibility aliases must live under `investigation/_appendix/`.

Main Agent read boundary: standard reconnaissance must not read
`investigation/_appendix/` as task context. The Main Agent reads
`reading_plan.compact.json`, `source_findings.compact.md`, terminal
reconnaissance files, syllabus/direct-spec source bodies, and exact source
windows listed in `parent_source_read_requests`. Appendix reads are for
recovery, audit, or debugging only; if needed, read the smallest named
artifact/window and record the reason in `review_a.json` or
`stage_reviews/process_concerns.jsonl`.

`source_findings.compact.md` is the only multi-writer parent interface in this
workflow. If content scouts write it directly, they must append only their own
scoped section, include `scout_type`, `scope`, `dispatch_id`, source paths,
fragment path, and receipt path, and must not rewrite or overwrite existing
sections.

For Canvas-native bodies, keep the raw `canvas/*.json` as the source of truth.
Optional readable exports may exist for human convenience, but they must be
marked as derived and point back to the raw JSON path and section pointer.

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
```

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

Read `canvas/syllabus.json` even when another source already looks like the main
spec. The syllabus often contains grading language, assignment families,
submission policies, collaboration rules, AI/tool policies, or academic
integrity constraints that are not repeated on the assignment page. If the
syllabus is irrelevant to the specific assignment, say so explicitly in
`spec.md` and `investigation/review_a.json`; do not leave it implicit.

After reading syllabus, record raw evidence pointers such as:

```text
canvas/syllabus.json#body_text:Assessment and Grading
canvas/syllabus.json#body_text:Grading Rubrics
canvas/syllabus.json#body_text:Course AI Policy
```

If a derived syllabus note or export is useful for a human reader, it may be
written under `references/`, but it is not required and must not become the only
evidence path. Downstream agents should read `canvas/syllabus.json` directly
when syllabus details matter.

Now write the first standardized `spec.md`. This is not raw JSON and not copied
PDF text. It is a report, in the agent's words, grounded by the sources:

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
- Modules:
- Pages:
- Files:
- External URLs:

## Syllabus Relevance
State whether `canvas/syllabus.json` adds assignment-specific requirements,
grading/rubric criteria, assessment-family context, submission or late policy,
collaboration rules, academic-integrity constraints, AI/tool policy, or no
relevant constraints for this assignment. Include raw Canvas evidence pointers
to `canvas/syllabus.json` sections.

## Main Spec Judgment
State which source appears to be the main spec and why.

## Deliverables
List concrete files / uploads / text entries the student must produce.

## Requirements / Tasks
List the actual questions, tasks, constraints, sections, datasets, or code work.

## Rubric / Grading
Briefly summarize known grading criteria. If Stage 2 is not done yet, mark this
as pending.

## Inputs / References
List required PDFs, readings, datasets, starter code, Google Docs, slides, or
other references, and whether each has been fetched into references/.

## Gaps / User Questions
List missing sources, unreachable materials, or decisions only the user can make.

## Evidence Pointers
Point to canvas/*.json and references/* paths that justify the summary.
```

Good generic result: `spec.md` explains which source is authoritative, why
nearby Canvas sources are supporting or irrelevant, what the syllabus adds or
does not add, and which concrete deliverables are required. It does not paste an
entire PDF, page, or external document.

## Stage 2 - find-rubric

Locate grading criteria in this order:

1. Canvas rubric from `canvas/rubric.json`.
2. `canvas/syllabus.json`, especially assessment tables, grading rubrics,
   academic integrity, collaboration, AI/tool policy, late/submission policy,
   and assignment-family descriptions.
3. `spec.md` and fetched reference text, searching for words such as `rubric`,
   `criteria`, `graded on`, `points breakdown`, `you will be evaluated on`, and
   `assessment`.
4. Module pages and external URLs fetched in Stage 3.

Write `<work_dir>/investigation/rubric.md`.

If grading criteria come from the syllabus, cite `canvas/syllabus.json` with a
specific body-text section pointer, not only a scout summary. A rubric search is
incomplete when the only downstream evidence is a compressed summary of syllabus
grading criteria.

If no rubric is found, write:

```text
RUBRIC NOT FOUND - use assignment/spec criteria if present
```

Do not stop only because Canvas rubric is absent. Many courses put useful
grading criteria in PDFs, pages, external specs, or the syllabus instead of the
Canvas rubric field.

## Stage 3 - locate-inputs

Fetch all materials needed to understand or execute the assignment:

- direct assignment files
- PDFs or files linked from module items or Canvas pages
- Google Docs / Google Slides / instructor external pages when publicly
  fetchable
- starter code, scaffold archives, data files, or GitHub links
- supporting slides/readings when the spec references them
- raw Canvas JSON body pointers for Canvas-native assignment/page/syllabus evidence

Save them under `<work_dir>/references/`. For PDFs, also save extracted text
beside the file when possible. Claude Code's built-in Read tool can read PDF
files directly and return their text content. Alternatively, use PyMuPDF
(`python3 -c "import fitz; ..."`) if the agent needs to extract text
programmatically. For Google Docs, attempt anonymous text export and save it
as `references/<name>.txt` or `references/<name>.md`.

### Source Candidate And Body Audit

Before treating fetched or discovered material as assignment evidence, write
metadata-level candidate ranking and the compact parent plan to:

```text
investigation/_appendix/source_index.json
investigation/reading_plan.compact.json
```

The source-reading workflow is strict sequential gates, not parallel phases:
`metadata_scout -> reading_plan.compact.json -> content_scout -> source_findings.compact.md`.
Do not dispatch `content_scout` until `metadata_scout` has produced
source index evidence and the Main Agent has approved
`reading_plan.compact.json`. Content scouts may run in parallel with each other
only after the compact reading plan assigns disjoint scopes.

`investigation/_appendix/source_index.json` records all discovered sources from
assignment, rubric, front page, syllabus, pages, module items, file metadata,
assignment files, and external URLs. Existing `source_candidates.json` and
`reading_plan.json` may remain only under
`investigation/_appendix/compatibility_aliases/`, but the Main Agent's normal
interface is `reading_plan.compact.json`. Classify each candidate as:

```text
required | high_signal | supporting | low_signal | forbidden | blocked
```

- `required`: direct assignment/spec/rubric/proposal/final-project files or
  required inputs.
- `high_signal`: title or context suggests proposal, research, methods,
  timeline, topic selection, literature review, questionnaire, field research,
  grading criteria, or submission rules.
- `supporting`: same week/module/project topic material that may inform an
  open-ended topic.
- `low_signal`: course material with no clear assignment relationship.
- `forbidden`: prior submissions, stale pipelines, old reviews, archive,
  transcripts, or startup-forbidden context.
- `blocked`: unavailable, login-walled, unparsable, or otherwise unreachable.

`reading_plan.compact.json` is the bounded plan approved by the Main Agent
before content scouts read bodies. It assigns `required` and `high_signal`
candidates, plus selected `supporting` candidates, to `content_scout` children
with explicit `scope` values such as `spec_content`, `methods_content`,
`theme_content`, or `policy_content`. These scope values are not separate
Subagent roles.

Under the Hybrid Gate Report contract, content scouts narrow the read set and
supporting sources are delegated to content scouts with exact pointers. They do
not require the Main Agent to reread every narrowed source body. Scout summaries
are routing hints, not source evidence. Before writing or revising final
`spec.md`, `investigation/rubric.md`, or `review_a.json`, the Main Agent fully
reads the syllabus and direct-spec strong matches, then reads
`source_findings.compact.md` and only the source windows named in
`parent_source_read_requests`.

A direct-spec strong match satisfies at least two of: task terms in the source
name/title, assignment-linked or `required` source placement, and opening-body
evidence of deliverable, format, deadline, sections, submission, grading, or
prompt.

The `metadata_scout` reads index-level metadata, links, titles, item context,
and short Canvas summaries. If a scout reads a full Canvas page, syllabus body,
front-page body, PDF/PPTX body, or external document body, that read must be
recorded through the body-audit path below or assigned to a `content_scout`.

After body reading, write:

```text
investigation/_appendix/body_evidence_fragments/<scope>.json
investigation/_appendix/scout_receipts/<scope>_content_result.json
investigation/source_findings.compact.md
```

Each content scout writes its own fragment under
`investigation/_appendix/body_evidence_fragments/`, writes a receipt under
`investigation/_appendix/scout_receipts/`, and may append a scoped section to
`investigation/source_findings.compact.md`. Legacy
`source_body_audit_fragments/` and `source_body_audit.json` may remain only
under `investigation/_appendix/compatibility_aliases/`. Each compact finding
records source path, relevance, what the source says, planning impact, exact
pointer, minimal quote if needed, and whether the Main Agent must read a source
window. Full appendix entries record `candidate_id`, `path_or_url`,
`origin`, `assigned_scout`, `read_mode`, `body_artifact_path`, `classification`,
`evidence_pointers`, `reading_cost`, and `reason`. Allowed body-level
classifications are:

```text
precise_match | supporting_context | weak_related | excluded | forbidden | blocked
```

Use read modes such as:

```text
raw_canvas_json | metadata_only | readable_extract | pdf_text_plus_links |
external_text_export | direct_pdf_read | keyword_windows | blocked_unreachable |
not_relevant_after_review
```

`metadata_only` must never be used as `precise_match`, rubric evidence, input
evidence, or source-context evidence. A source may become `precise_match` or
`supporting_context` only after the audit records body-read evidence or a
specific blocked/unavailable reason.

For long PDFs or PPTX decks, do not dump full text into the Main Agent context.
First save the file and extracted text, record page/slide/byte counts, search
task-sensitive terms, and summarize keyword windows around matching pages or
slides. Escalate to broader or full read only when the source is a direct spec
or the windows cannot answer the assignment question.

### PDF Link Annotation Extraction

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
fails, record the failure in `investigation/unreachable.txt` or process concerns
with the PDF path and tool error. Do not specialize this rule by URL domain,
resource type, or course. The generic contract is: preserve every URI embedded
in PDF link annotations so later spec, rubric, input, and blocker decisions can
decide whether each URL matters.

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

Do not over-download every course file. Download what was discovered from
assignment, module, page, syllabus, front page, or clear external spec links.

After Stage 3, revise `spec.md` if fetched materials changed the main spec
judgment, deliverables, rubric summary, or gaps.

## Stage 4 - review investigation

For proposal/research/open-ended assignments, run a Main Agent parent self-check
after `source_findings.compact.md` exists. The normal `[A]` path has exactly two
source-reading child roles: `metadata_scout` and `content_scout`. The Main Agent
checks the compact findings against the compact reading plan, syllabus,
direct-spec strong matches, unreachable resources, forbidden context, and
terminal artifacts.

Before writing the review verdict, run the parent self-check. Compact findings
are not a terminal reconnaissance verdict: `source_findings.compact.md` can
summarize source findings, but it does not replace `spec.md`,
`investigation/rubric.md`, or `investigation/review_a.json`. If source-body
evidence exists while terminal reconnaissance artifacts are missing, write a
recover/blocking `review_a.json` or append
`stage_reviews/process_concerns.jsonl`; the entry must name the missing
`spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` artifact
and state whether the next action is inline completion, replacement coordinator,
user recovery, or stop.
Rule for automated checks: missing `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` must write a recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`.

Reviewer must read:

```text
<work_dir>/spec.md
<work_dir>/investigation/rubric.md
<work_dir>/investigation/reading_plan.compact.json
<work_dir>/investigation/source_findings.compact.md
<work_dir>/investigation/unreachable.txt
<work_dir>/canvas/syllabus.json
<work_dir>/<direct-spec strong match source bodies>
<work_dir>/<exact parent_source_read_requests windows>
```

Canvas assignment/page/file bodies, `references/`, module indexes, appendix
evidence, and compatibility aliases are recovery/debug/audit reads unless they
are syllabus, direct-spec strong matches, or exact parent source windows.

Full candidate lists, body fragments, full source-review artifacts, raw scout
receipts, scout briefs, and compatibility aliases live under
`investigation/_appendix/`. The Main Agent must not read appendix artifacts in
standard runs; it may inspect a specific appendix artifact only for recovery,
audit, or debugging and must record why. Existing `source_candidates.json`, `reading_plan.json`, and
`source_body_audit.json` are compatibility aliases under
`investigation/_appendix/compatibility_aliases/`, not the default parent read
interface.

Write strict JSON to `<work_dir>/investigation/review_a.json`:

```json
{
  "deliverable_clear": true,
  "deliverable_summary": "One sentence describing what the student must produce.",
  "rubric_found": true,
  "rubric_sources_checked": [
    "canvas/rubric.json",
    "canvas/syllabus.json",
    "spec.md",
    "references/",
    "canvas/module-items-*.json",
    "canvas/page-*.json"
  ],
  "syllabus_checked": true,
  "syllabus_relevance": {
    "status": "relevant | not_relevant | unavailable",
    "evidence": "Brief evidence-backed relevance judgment.",
    "constraints_added": []
  },
  "inputs_complete": true,
  "compact_reading_plan_approved": true,
  "source_findings_checked": true,
  "required_high_signal_body_evidence_checked": true,
  "parent_self_check_complete": true,
  "unread_required_or_high_signal_sources": [],
  "open_ended_coverage": {
    "assignment_spec_body_read": true,
    "methods_or_topic_guidance_body_read": true,
    "supporting_topic_context_checked": true
  },
  "missing_sources": [],
  "blocking_unreachables": [],
  "verdict": "proceed",
  "recovery_actions": []
}
```

Allowed verdicts:

- `proceed` - enough grounded context exists to ask the user for supplements and
  then design the pipeline.
- `recover` - sources are probably obtainable, but another fetch, user-provided
  URL, or pasted material is needed.
- `stop` - the assignment cannot be understood or executed with available
  sources.

If `verdict != "proceed"`, do not proceed silently. Surface the gap in
`do-homework [B]`.

For proposal/research/open-ended assignments, `verdict` must not be `proceed`
unless an assignment/spec source has body-read evidence and
methods/topic-selection guidance has body-read evidence, or `review_a.json`
records why such guidance is unavailable. Supporting topic context must be read
enough to inform the topic choice or explicitly judged unnecessary. Reading
budget overruns, too-broad reading, too-narrow reading, missed sources, and
misreads must be recorded in `review_a.json` and surfaced in
`recon_summary.md`. Required or high-signal candidates left at `metadata_only`
require `recover` unless they are explicitly excluded with evidence.

## Stage 5 - classify-output

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
supplement checkpoint. Stage 5 only identifies the shape.

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
   modules, every inspected module's items, and relevant pages/files.
3. `spec.md` contains an explicit `Syllabus Relevance` judgment backed by
   `canvas/syllabus.json` raw body pointers, or `investigation/unreachable.txt`
   explains why syllabus could not be fetched.
4. `references/` contains every reachable material needed to understand the
   assignment, such as fetched PDFs, decks, external text exports, starter code,
   or datasets. Do not require `references/*syllabus*` as the evidence gate for
   Canvas-native syllabus evidence; use `canvas/syllabus.json` directly.
5. `investigation/reading_plan.compact.json`,
   `investigation/source_findings.compact.md`, and appendix evidence distinguish
   metadata discovery from body-read evidence.
6. `investigation/rubric.md` records Canvas, syllabus, or spec-based grading
   criteria, or clearly says rubric was not found. When syllabus contributes
   criteria, `investigation/rubric.md` must cite raw `canvas/syllabus.json`
   section pointers; summary-only scout output is incomplete.
7. `investigation/unreachable.txt` lists blocked resources.
8. `investigation/review_a.json` has a verdict and records syllabus relevance,
   compact source findings, appendix body evidence status, and parent self-check
   status.
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
- Rank candidates broadly, then read bodies under a bounded
  `reading_plan.compact.json`.
- Use content scouts for broad source body reading; the Main Agent remains the
  final judge but normally reads only syllabus, direct-spec strong matches,
  `source_findings.compact.md`, and explicit `parent_source_read_requests`
  before writing `spec.md`.
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
5. **Do not over-download every course file.** Download discovered assignment
   context, not arbitrary folder trees.
6. **External Google Docs may be the main spec.** Try to fetch their text; if
   blocked, record them in `unreachable.txt` and let `review_a.json` decide
   whether the block is fatal.
7. **Do not turn `spec.md` into a raw dump.** Full source text belongs in
   `references/`; `spec.md` is the decision report.
8. **Do not hide Canvas-native source bodies behind summaries.** If assignment,
   syllabus, front-page, or page JSON is fetched and used, cite the raw
   `canvas/*.json` file and body-text section pointer. Optional derived
   reference notes may help humans, but summary-only scout output must never
   replace raw Canvas JSON.
9. **Do not require Canvas-native bodies to be copied into `references/`.**
   Downstream agents should be explicitly allowed to read the relevant
   `canvas/*.json` source instead of relying on a lossy extract.
10. **Do not confuse metadata with body evidence.** `canvas/file-*.json`,
   module item titles, and source filenames create candidates; they do not prove
   relevance until appendix body evidence records a body read, exclusion, or
   blocker and `source_findings.compact.md` summarizes the task-relevant result.
