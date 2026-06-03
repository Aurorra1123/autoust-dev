---
name: do-homework
description: End-to-end homework completion. Use when the user asks "complete X assignment", "do my paper for DLED3020", "帮我做 lab 5". Runs Canvas Generic-style reconnaissance, designs a per-assignment pipeline, produces a draft, asks confirmation, and optionally submits via canvascli.
---

# Do Homework

The flagship M3 task. The user asks something like:

- "帮我做 DLED3020 的 Paper Critique"
- "complete DSAA2043 Lab Assignment 1"
- "做一下 UCUG1077 的 group presentation slides"
- "写 DSAA2012 的 project report"

You go from "user names an assignment" to "draft / code / slides exists and
(optionally) is submitted to Canvas".

AutoStudy follows Canvas Copilot's `canvas-generic` sequence, adapted to an
assistant-style user loop:

```text
spec.md
-> investigation/rubric.md
-> references/
-> investigation/review_a.json
-> pipeline_design.md
-> draft/
-> verification_checklist.md
-> verification.log
-> result.json
```

The two user checkpoints are:

1. `[B]` after reconnaissance, where the user can add group info, oral
   instructions, dataset choice, scope, or stop.
2. `[E]` after draft generation, where the user reviews and chooses whether to
   submit.

## Preconditions

Before running, check the same set as `sync-status.md`:

1. `.venv/bin/canvascli version` returns 0.
2. `.venv/bin/canvascli whoami` returns 0.

If either fails, redirect to `tools/canvascli-setup.md` step 3 and stop.

If the user has not named a specific assignment, run `sync-status.md` first to
surface options, then come back here.

## Execution Flow

### [A] Build The Assignment Workbench

No user interaction. This step follows Canvas Copilot's "inspect all sources
first" habit. Do not treat a Canvas assignment description, title, or single
link as the whole prompt.

#### [A1] Resolve Identifiers

Resolve the request to a `(course_id, assignment_id)` pair.

Preferred path after `sync-status`: if the user chose "plan item N", run:

```bash
.venv/bin/python scripts/select_plan_item.py --index <N> --pretty
```

Use the selector JSON directly:

```text
course_id
assignment_id
assignment_name
suggested_work_dir
recommended_action
existing_result_path
```

Do not re-match by title when this object exists.

Action handling:

| `recommended_action` | Behavior |
|---|---|
| `recon` | Continue to `[A2]`. |
| `review_or_submit` | Read `existing_result_path` and `suggested_work_dir`; help the user review, revise, or submit the existing draft instead of re-running reconnaissance by default. |
| `continue` | Inspect the previous error `result.json`; ask whether to retry before doing new work. |
| `manual_review` | Stop before `[A3]`; tell the user this item likely needs manual Canvas interaction. |

Direct natural-language path: if the user says "DLED3020 Paper Critique"
without coming from a plan item, match against `data/assignments.json` by
case-insensitive substring of `name` and course code in `context_name`. If
ambiguous, surface the candidates at `[B]`.

#### [A2] Create The Workbench

```bash
mkdir -p "data/homework/<COURSE>/<HWID>"
```

If the request came from `scripts/select_plan_item.py`, use
`suggested_work_dir` exactly so local result tracking and future scans point to
the same workbench.

Target structure:

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   └── review_a.json
├── pipeline_design.md
├── draft/
├── verification_checklist.md
├── verification.log
└── result.json
```

#### [A3] Canvas Generic Reconnaissance - Mandatory

Invoke `tools/problem-extractor.md` as an agent-led workflow. Do **not** run
`scripts/recon_assignment.py` as the normal path. That script is historical
transition evidence, not the production reconnaissance contract.

Follow the Canvas Generic stages:

1. **Stage 1 fetch-context**
   Read assignment, rubric, front page, syllabus, modules, every module's items,
   relevant pages, attached files, and external URLs through atomic
   `canvascli` commands. Save raw JSON under `canvas/`. Then write a
   standardized `spec.md` report with metadata, source trail, main spec
   judgment, deliverables, requirements, rubric placeholder, inputs, gaps, and
   evidence pointers.

2. **Stage 2 find-rubric**
   Search Canvas rubric, `spec.md`, downloaded/fetched references, modules,
   syllabus, and external spec text. Write `investigation/rubric.md`.

3. **Stage 3 locate-inputs**
   Download or fetch necessary PDFs, Google Doc text, starter code, datasets, or
   external spec pages into `references/`. Record blocked resources in
   `investigation/unreachable.txt`. Revise `spec.md` if fetched inputs change
   the main spec judgment.

4. **Stage 4 review investigation**
   Run a cold review of `spec.md`, `investigation/rubric.md`, `references/`, and
   `investigation/unreachable.txt`. Prefer a separate reviewer/sub-agent when
   available. Write strict JSON to `investigation/review_a.json`.

5. **Stage 5 classify-output**
   Classify the output mode (`doc_prose`, `pdf_annotated`, `pdf_typed`, `code`,
   `form_answers`, `slides`, or `mixed`) and write the preliminary first line of
   `pipeline_design.md`.

After `[A3]`, immediately read:

```text
spec.md
investigation/rubric.md
investigation/unreachable.txt
investigation/review_a.json
pipeline_design.md
problem.md
```

Do not skip this read. The whole skill collapses into template content if you
generate from the assignment title or Canvas description.

#### [A4] Gate On Reconnaissance Quality

If `review_a.json.verdict` is not `proceed`, or `spec.md` does not clearly
state deliverables and main source judgment, surface this at `[B]` as a recovery
option:

> "I checked the assignment page, rubric, course front page, syllabus, modules,
> pages, linked files, and external URLs, but I still could not identify a
> complete spec. Options: paste the spec text or URL, point me to the correct
> module/page/file, or stop for now."

Do not proceed silently to `[C]` when `spec.md` is thin.

### [B] Recon Summary + User Supplements

AskUserQuestion checkpoint #1.

Read `spec.md` first, then `investigation/review_a.json`,
`investigation/rubric.md`, and `problem.md`. Summarize in 4-6 lines:

- Course + assignment name + due date + points.
- Source trail and main spec judgment. Example: "assignment page was empty;
  module Project guidelines contained `DSAA2011-26sp-project_announce-L01.pdf`."
- Concrete deliverables and tasks.
- Rubric or grading criteria if found; say "Canvas rubric not found" if only
  spec-based criteria exist.
- Output mode from `pipeline_design.md`.
- Gaps or human decisions, such as group ID, partner names, dataset choice,
  video recording, oral instructor notes, or blocked external resources.

Even when `review_a.json.verdict == "proceed"`, this checkpoint is mandatory.
`proceed` means the Canvas materials are sufficient to start; it does not mean
the user has no extra group information, instructor oral notes, preferred
dataset, formatting preference, or scope constraint.

Ask:

```text
针对这份 <COURSE> <name>，我已经完成侦查。你想我:
  - 继续完整做草稿，暂无额外补充 (推荐)
  - 我有补充要求 / 组队信息 / 老师口头要求
  - 只做某几题 / 某个章节
  - 先不做，我自己看一下
```

If the user provides supplements, write them to:

```text
<work_dir>/investigation/user_notes.md
```

If the user chooses partial scope, write:

```text
<work_dir>/investigation/user_scope.md
```

If the user stops, write `result.json` with `status: "skipped"`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status skipped \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --note "user stopped after reconnaissance"
```

If `[A4]` flagged reconnaissance failure and the user supplies pasted material,
save it to:

```text
<work_dir>/problem_user.md
```

Then update `spec.md`, `problem.md`, and `pipeline_design.md` so downstream
tools read the supplemented context from files, not chat memory.

### [C] Design Pipeline

No user interaction.

Read:

```text
spec.md
investigation/rubric.md
investigation/review_a.json
investigation/user_notes.md       # if present
investigation/user_scope.md       # if present
problem_user.md                   # if present
pipeline_design.md
sub-skills/tools/_index.md
```

Complete `pipeline_design.md`. It is the single-assignment execution plan,
modeled after Canvas Copilot:

```text
Output mode: mixed (code + doc_prose + slides)

## Deliverables
- draft/<expected file>

## Pipeline Stages
### Sub-pipeline A: code
...

### Sub-pipeline B: doc_prose
...

## Tool Mapping
- code-writer
- test-runner
- writing-helper
- slide-maker
- pdf-renderer

## Verification Plan
- ...

## Human Review Items
- ...
```

Do not write or require `task_profile.yaml`. The orchestrator reads
`spec.md + pipeline_design.md` directly.

### [D] Orchestrator Runs

Invoke `tasks/task-orchestrator.md` with the workbench path. The orchestrator:

1. Reads `spec.md`, `pipeline_design.md`, `investigation/rubric.md`, and
   `problem.md`.
2. Maps stages to tools in `tools/_index.md`.
3. Runs the tools, each writing inside `work_dir`.
4. Writes `verification_checklist.md` and `verification.log`.
5. Returns a structured summary with deliverables and `human_review_items`.

The orchestrator must not prompt the user. If it cannot execute the planned
pipeline, stop and write `result.json` with `status: "error"`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status error \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --note "<short failure summary>"
```

### [E] Draft Review + Submission Confirmation

AskUserQuestion checkpoint #2.

Once the orchestrator returns, show the user:

- Deliverable path(s).
- A one-line preview: for PDFs, file size + page count via `pdfinfo` if
  available; for code, file count + test pass rate.
- Human review items from the orchestrator.
- Canvas submission URL:
  `https://hkust-gz.instructure.com/courses/<course_id>/assignments/<assignment_id>`

Ask:

```text
草稿已经在 <path>。要现在用 canvascli 提交到 Canvas 吗?
  - 是，提交
  - 不，我自己看完再说 (推荐)
  - 重做 / 改某部分 (告诉我具体改什么)
```

If user picks "重做", capture the change request, update
`investigation/user_notes.md` or `pipeline_design.md`, and rerun from `[C]`.
Do not re-fetch `[A]` unless the user says Canvas changed.

If user picks "不", write `result.json` with `status: "draft_ready"`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status draft_ready \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --draft-path "<primary_deliverable_path>" \
  --deliverable "<primary_deliverable_path>" \
  --verification-log "data/homework/<COURSE>/<HWID>/verification.log" \
  --human-review-item "<anything the user must still check before submitting>" \
  --note "draft generated; user chose to review manually before submission"
```

### [F] Submit

Only if the user confirmed at `[E]`.

```bash
.venv/bin/canvascli submit <assignment_id> "<deliverable_path>" -c <course_id> --pretty
```

Capture stdout. Show the user:

- Submitted attempt number.
- `submitted_at`.
- Canvas URL to verify.

If submit succeeds, write `result.json` with `status: "submitted"`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status submitted \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --draft-path "<submitted_deliverable_path>" \
  --deliverable "<submitted_deliverable_path>" \
  --verification-log "data/homework/<COURSE>/<HWID>/verification.log" \
  --submitted-at "<submitted_at_from_canvas>" \
  --submission-attempt "<attempt_number>" \
  --canvas-url "https://hkust-gz.instructure.com/courses/<course_id>/assignments/<assignment_id>"
```

If submit fails, write `result.json` with `status: "error"` and the Canvas
error message in `notes`. Do not loop automatically.

## Output Format

After `[F]`, or `[E]` if not submitting:

```markdown
## <COURSE> <assignment name>

**Deliverable:** `data/homework/<COURSE>/<HWID>/draft/...`
**Status:** draft_ready / submitted / skipped / error
**Canvas URL:** https://hkust-gz.instructure.com/courses/.../assignments/...

Human review items:
- ...
```

## Safety

1. **Two AskUserQuestion checkpoints only**: `[B]` and `[E]`.
2. **Never auto-submit.** Even if the user said "complete and submit" upfront,
   confirm at `[E]`.
3. **Never modify raw Canvas JSON** under `canvas/*.json`.
4. **Do not run script-led reconnaissance** as the normal path.
5. **Stop on first orchestrator failure.**
6. **Submit failures are not retries.**
7. **Honor partial scope.**
8. **Ground every deliverable in `spec.md`, `references/`, and
   `pipeline_design.md`.** Do not produce `[PROBLEM N]`, `[TODO: align with
   actual project spec]`, or `[此处由小组成员填入选题]` placeholders. The only
   acceptable markers are `[CITATION NEEDED: ...]` and
   `[CLARIFICATION NEEDED: ...]`, both surfaced at `[E]`.

## Pitfalls

- **Don't read `assignment.description` as the problem statement.** It may be
  empty, a file link, a Google Doc link, or one hint among many.
- **Don't stop at the first match.** Canvas Copilot checks assignment page,
  rubric, front page, syllabus, modules, pages, files, and external URLs before
  deciding which source is the spec.
- **Don't turn `spec.md` into a raw dump.** Full PDF or Google Doc text belongs
  in `references/`; `spec.md` is the standardized report.
- **Google Docs can be the main spec.** Try to fetch text. If blocked, record it
  in `unreachable.txt` and let `review_a.json` decide whether it blocks work.
- **Course code in `data/assignments.json` is in `context_name`, not a separate
  field.**
- **The work_dir path can contain spaces and Chinese.** Always quote shell
  arguments.
- **`submission_types` matters for `[F]`.** `online_upload` is what
  `canvascli submit` handles.
- **`[CLARIFICATION NEEDED: ...]` markers** are batched at `[E]`, not asked one
  by one.

## Cross-references

- Reconnaissance: `tools/problem-extractor.md`
- Pipeline execution: `tasks/task-orchestrator.md`
- Tool capability matrix: `tools/_index.md`
- Canvas commands: `tools/canvascli-api.md`
- Submission protocol: `tools/canvascli-api.md`
