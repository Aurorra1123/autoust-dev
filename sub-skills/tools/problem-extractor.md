---
name: problem-extractor
description: Agent-led Canvas Generic reconnaissance. Inspect Canvas sources through atomic canvascli commands, write a standardized spec.md, locate rubric and inputs, and review whether the assignment is sufficiently understood before any draft generation.
---

# problem-extractor

The data-grounding workflow for homework. It follows Canvas Copilot's
`canvas-generic` model: **the agent reads every likely source and writes a
standardized reconnaissance report**. It is not a one-shot parser and it is not
a script-generated context dump.

Real failure modes this prevents:

- DSAA2011 Project: the assignment page is empty, Canvas rubric is absent, and
  front page is disabled, but the project PDF lives in a module item.
- UCUG1505 FINAL project: the assignment page and a Week 4 module item both
  point to the same Google Doc spec; Week 9 slides are nearby context.

The correct behavior is to inspect all angles first, then decide which source is
the main spec.

## Capability

- `extract_problem` - `(course_id, assignment_id, work_dir)` -> a
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
│   ├── rubric.md
│   ├── unreachable.txt
│   └── review_a.json
└── pipeline_design.md
```

`canvas/` stores raw JSON snapshots from atomic `canvascli` commands.
`spec.md` is the standardized reconnaissance report written by the agent after
reading the sources. `problem.md` is only a thin compatibility summary for older
tools. `references/` stores fetched PDFs, Google Docs text, starter code, data,
or other materials. `investigation/` records rubric findings, unreachable
resources, and the investigation review.

## Non-goal: no script-led spec generation

Do **not** run `scripts/recon_assignment.py` as the normal homework
reconnaissance path. That script was an earlier transition experiment that
proved the atomic `canvascli` commands could reach the right sources. The
production flow is agent-led, following the stages below.

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

Good DSAA2011-style result: `spec.md` says the assignment page was empty and
the main spec is the module PDF, then lists the zip deliverables. It does not
paste the entire PDF.

Good UCUG1505-style result: `spec.md` says the assignment page and Week 4 module
both point to the same Google Doc, records whether the Google Doc content was
fetched, and distinguishes Week 9 slides as supporting context.

## Stage 2 - find-rubric

Locate grading criteria in this order:

1. Canvas rubric from `canvas/rubric.json`.
2. `spec.md` and fetched reference text, searching for words such as `rubric`,
   `criteria`, `graded on`, `points breakdown`, `you will be evaluated on`, and
   `assessment`.
3. Module pages and syllabus text.
4. External URLs fetched in Stage 3.

Write `<work_dir>/investigation/rubric.md`.

If no rubric is found, write:

```text
RUBRIC NOT FOUND - use assignment/spec criteria if present
```

Do not stop only because Canvas rubric is absent. DSAA2011 and UCUG1505 both
have useful spec-based grading criteria outside Canvas rubric.

## Stage 3 - locate-inputs

Fetch all materials needed to understand or execute the assignment:

- direct assignment files
- PDFs or files linked from module items or Canvas pages
- Google Docs / Google Slides / instructor external pages when publicly
  fetchable
- starter code, scaffold archives, data files, or GitHub links
- supporting slides/readings when the spec references them

Save them under `<work_dir>/references/`. For PDFs, also save extracted text
beside the file when possible. Claude Code's built-in Read tool can read PDF
files directly and return their text content. Alternatively, use PyMuPDF
(`python3 -c "import fitz; ..."`) if the agent needs to extract text
programmatically. For Google Docs, attempt anonymous text export and save it
as `references/<name>.txt` or `references/<name>.md`.

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

Run a cold review of the investigation. Prefer a separate reviewer/sub-agent
when the runtime supports it; otherwise reread the workbench from scratch and
answer the same questions without relying on memory.

Reviewer must read:

```text
<work_dir>/spec.md
<work_dir>/investigation/rubric.md
<work_dir>/references/
<work_dir>/investigation/unreachable.txt
```

Write strict JSON to `<work_dir>/investigation/review_a.json`:

```json
{
  "deliverable_clear": true,
  "deliverable_summary": "One sentence describing what the student must produce.",
  "rubric_found": true,
  "inputs_complete": true,
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
3. `references/` contains every reachable material needed to understand the
   assignment.
4. `investigation/rubric.md` records Canvas or spec-based grading criteria, or
   clearly says rubric was not found.
5. `investigation/unreachable.txt` lists blocked resources.
6. `investigation/review_a.json` has a verdict.
7. `pipeline_design.md` starts with the preliminary output mode.

## Source Selection Philosophy

- Inspect broadly and decide late.
- Do not stop at the first title match.
- Do not assume assignment description is authoritative.
- Do not assume modules are irrelevant when assignment description has a link.
- Treat duplicate sources as corroboration.
- Label nearby context as supporting context instead of hiding it.
- Keep Canvas API internals in `canvascli`; AutoStudy uses the CLI contract.

## Cross-references

- Called from: `tasks/do-homework.md` step `[A]`
- Consumed by: `tasks/task-orchestrator.md`, `tools/writing-helper.md`,
  `tools/code-writer.md`, and `tools/slide-maker.md`
- Depends on: `tools/canvascli-api.md` atomic context commands,
  `canvascli download`, PDF text extraction, and fetchable external URLs

## Pitfalls

1. **Assignment description can be empty.** DSAA2011 Project is the real
   example; the spec was in a module file.
2. **A valid source can appear twice.** UCUG1505 FINAL project links the same
   Google Doc from assignment description and Week 4 module item.
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
