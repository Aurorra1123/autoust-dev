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

`do-homework.md` is written for the Claude Code Main Agent. The Main Agent is
the only runtime actor that talks to the user. Subagents, when used, are
temporary workers dispatched by the Main Agent and receive precise stage briefs.

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
│   ├── review_a.json
│   ├── alignment_brief.md
│   ├── user_notes.md
│   └── user_scope.md
├── pipeline_design.md
├── stage_briefs/
├── stage_results/
├── stage_reviews/
├── transcripts/
├── draft/
│   ├── figures/
│   └── render/
├── verification_checklist.md
├── verification.log
└── result.json
```

After creating directories, compute the repository root for downstream path discovery:

```bash
REPO_ROOT="$(git -C 'data/homework/<COURSE>/<HWID>' rev-parse --show-toplevel)"
echo "repo_root: ${REPO_ROOT}"
```

This `REPO_ROOT` will be injected into `pipeline_design.md` metadata at [C].
All skill file paths resolve as `REPO_ROOT/sub-skills/tools/<name>.md`.

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

### [B] Recon Summary + Alignment Loop

AskUserQuestion checkpoint #1.

Read `spec.md` first, then `investigation/review_a.json`,
`investigation/rubric.md`, `investigation/unreachable.txt`, `pipeline_design.md`,
and `problem.md`. Summarize in 4-6 lines:

- Course + assignment name + due date + points.
- Source trail and main spec judgment. Example: "assignment page was empty;
  module Project guidelines contained `DSAA2011-26sp-project_announce-L01.pdf`."
- Concrete deliverables and tasks.
- Rubric or grading criteria if found; say "Canvas rubric not found" if only
  spec-based criteria exist.
- Output mode from `pipeline_design.md`.
- The user-decision areas you may need to align before starting, such as group
  ID, partner names, dataset choice, project concept, argument, creative
  direction, personal experience, oral instructor notes, scope, style, video
  recording, or blocked external resources.

Even when `review_a.json.verdict == "proceed"`, this checkpoint is mandatory.
`proceed` means the Canvas materials are sufficient to understand the assignment
surface. It does not mean the user's intended direction is aligned.

The goal of `[B]` is not to classify the assignment into rigid "simple" or
"open" categories. The Main Agent must keep asking only while the current
information is not enough to start without guessing the user's core intent. For
straightforward assignments this may be one short confirmation. For open-ended
assignments, continue the loop until the Main Agent can write a stable
`alignment_brief.md` and defend why the next pipeline will not drift away from
the user's intent.

#### [B1] Ask The Most Important Alignment Question

Before every question, run this internal alignment audit:

```text
Can I answer these without guessing?

1. What exactly must be delivered?
2. What does the user want this work to express, argue, demonstrate, or optimize?
3. Which choices are fixed by Canvas/spec/rubric?
4. Which choices must come from the user before work starts?
5. Which choices has the user delegated to me?
6. What must not be fabricated or hidden?
7. Can I now write pipeline stages with concrete goals and quality criteria?
8. Could a reviewer use the eventual alignment brief to detect direction drift?
```

If any missing answer can change the assignment's direction, ask one question:
the single question that most reduces direction-drift risk. Do not ask a batch
of questions. Do not ask low-impact style or formatting questions while a core
topic, dataset, argument, project concept, method, scope, or personal stance is
still unclear.

Question priority:

1. Core direction choices: topic, dataset, project concept, thesis, research
   question, method, framework, or target audience.
2. User-owned material: personal experience, viewpoint, aesthetic preference,
   group context, oral instructor notes, or presentation intent.
3. Execution blockers: missing file, blocked URL, missing group info, ambiguous
   scope, unavailable code/data/template.
4. Delegation boundaries: what the user allows the model to decide and what
   must remain for human review.
5. Minor defaults: ordinary formatting, wording, standard tool choices, and
   other low-risk defaults. Ask these only if they materially affect grading or
   user identity.

Prefer open-ended questions for user-owned thinking. Prefer 2-3 options when
the user may not have a ready idea or when the choice is operational.

Example for a clear DSAA2011-style project:

Ask:

```text
这份作业的 spec 和交付物已经很明确。唯一会影响后续产物命名和实验内容的是
dataset / group id / 是否提交。你确认用 <dataset>、<group id>，并先只生成
本地草稿不提交吗？
```

Example for an open-ended creative or reflective project:

```text
这个项目最容易跑偏的是核心 concept。你希望作品主要表达哪种方向？

1. 偏技术展示：突出交互机制和实现完整度
2. 偏艺术表达：做一个有主题、有情绪的体验
3. 偏实用小工具：让交互服务一个明确功能

也可以直接说你自己的想法。
```

#### [B2] Record Conversation Notes, Not The Final Brief

After each answer, append process notes to:

```text
<work_dir>/investigation/user_notes.md
```

Use this structure:

```markdown
## Alignment Conversation Notes

### Round <N>
- Question:
- User answer:
- Coordinator interpretation:
- Decisions captured:
- Remaining uncertainty:
```

`user_notes.md` is a process log. It may be appended every round.
`alignment_brief.md` is not a process log and must not be rewritten after every
question. Write `alignment_brief.md` only when the Main Agent has no necessary
alignment question left.

If the user chooses partial scope, write:

```text
<work_dir>/investigation/user_scope.md
```

If the user says "you decide" or equivalent, record the decision as delegated,
not as a user-stated fact. The later `alignment_brief.md` must explain the
default strategy and why it is reasonable.

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

#### [B3] Write And Confirm `alignment_brief.md`

When the internal alignment audit no longer exposes a necessary question, write:

```text
<work_dir>/investigation/alignment_brief.md
```

Template:

```markdown
# Alignment Brief: <COURSE> <Assignment>

## Assignment Understanding
Summarize the Canvas-grounded task in the Main Agent's words.

## User Intent
State what the user wants this work to express, argue, demonstrate, or optimize.

## Confirmed Decisions
- ...

## Delegated Decisions
- Decision:
  Default strategy:
  Reason:

## Non-Negotiables
- Content that must not be fabricated.
- Constraints or user boundaries that must not be crossed.

## Open Items For Final Review
- Items that do not block execution but must be surfaced at [E].

## Ready-To-Start Judgment
Explain why the Main Agent can now enter [C] without guessing the user's core
intent.
```

Then show the user a concise summary and ask for confirmation:

```text
我已经没有必须继续问你的问题了。下面是我写入 alignment_brief.md 的最终理解：

- ...

如果你确认，我会按这个方向进入 pipeline_design.md。
如果哪里不对，我会先修正 brief，不会开始执行。
```

If the user requests changes, append another round to `user_notes.md`, replace
`alignment_brief.md` with the corrected final brief, and ask for confirmation
again. Do not enter `[C]` until the user confirms the brief.

Hard gate: without a confirmed `investigation/alignment_brief.md`, do not write
the final `pipeline_design.md` and do not invoke `task-orchestrator.md`.

### [C] Design Pipeline

No user interaction.

Read:

```text
spec.md
investigation/rubric.md
investigation/review_a.json
investigation/alignment_brief.md  # required and confirmed at [B]
investigation/user_notes.md       # if present
investigation/user_scope.md       # if present
problem_user.md                   # if present
pipeline_design.md
sub-skills/tools/_index.md
```

Use the following common pipeline shapes as **reference guidance** — the agent
composes freely based on the actual assignment, not a fixed chain.

| Scenario | type | Typical tool chain | Final deliverable |
|---|---|---|---|
| **paper** | `paper` | paper-search → figure-maker (opt) → writing-helper → pdf-renderer | `final.pdf` |
| **slides** | `slides` | figure-maker (opt) → slide-maker | `slides.pdf` |
| **math** | `math` | writing-helper (LaTeX math) → pdf-renderer | `solution.pdf` |
| **lab** | `lab` | code-writer → test-runner → writing-helper → pdf-renderer | `src/` + `report.pdf` |
| **mixed** | `mixed` | Multiple sub-pipelines composed from above | multiple files |

For mixed assignments, write multiple sub-pipelines in pipeline_design.md.

Complete `pipeline_design.md`. It is the single-assignment execution plan,
modeled after Canvas Copilot:

```markdown
# Pipeline: <COURSE> <assignment>

## Metadata
repo_root: <absolute path from [A2]>

## Output
- mode: mixed (code + doc_prose + slides)
- deliverables: [notebook.ipynb, report.pdf, ...]

## Constraints
- [quantifiable constraints from spec]
- [user intent / non-negotiables from alignment_brief.md]

## Stages

### Stage 1 - Notebook Execution
- id: stage_01_notebook
- tool: sub-skills/tools/code-writer.md
- delegate: subagent
- lang: python
- review:
  - spec_compliance: true
  - quality: true
- max_retries: 1
- reads:
  - spec.md
  - investigation/rubric.md
  - references/
- writes:
  - draft/project.ipynb
  - draft/metrics.json
- quality_criteria:
  - notebook executes from a clean kernel
  - no fabricated metrics; report metrics must come from actual notebook output
- human_blockers:
  - dataset choice if the spec allows multiple datasets and user has not chosen

### Stage 2 - Report Draft
- id: stage_02_report
- tool: sub-skills/tools/writing-helper.md
- delegate: subagent
- type: report
- review:
  - spec_compliance: true
  - quality: true
- max_retries: 1
- reads:
  - spec.md
  - investigation/rubric.md
  - investigation/user_notes.md
  - draft/metrics.json
- writes:
  - draft/report.md
- quality_criteria:
  - covers every rubric criterion
  - numeric claims are grounded in draft/metrics.json
- post-process: humanize
- human_blockers:
  - group member names if required by the assignment

## Human Review Items
- ...
```

Do not write or require `task_profile.yaml`. The orchestrator reads
`spec.md + alignment_brief.md + pipeline_design.md` directly.

`pipeline_design.md` must explicitly incorporate `alignment_brief.md`. At
minimum, its constraints, stage goals, human blockers, delegated decisions, and
final review items must reflect the confirmed alignment brief. If a planned
stage cannot be justified from `spec.md`, `investigation/rubric.md`, or
`investigation/alignment_brief.md`, do not include that stage.

`pipeline_design.md` is the task-level plan for the Main Agent and
task-orchestrator. It is not handed directly to executor subagents. The
orchestrator converts each delegated stage into
`stage_briefs/<stage_id>_executor.md` plus reviewer briefs when review is
enabled.

### [D] Orchestrator Runs

Invoke `tasks/task-orchestrator.md` with the workbench path. The orchestrator:

1. Reads `spec.md`, `pipeline_design.md`, `investigation/rubric.md`, and
   `problem.md`.
2. Maps stages to tools in `tools/_index.md`.
3. Converts delegated stages into `stage_briefs/` executor and reviewer briefs.
4. Runs the tools, each writing inside `work_dir`.
5. Requires `stage_results/` receipts for every stage.
6. Requires `stage_reviews/` receipts for reviewed stages.
7. Writes `verification_checklist.md` and `verification.log`.
8. Returns a structured summary with deliverables and `human_review_items`.

For delegated subagent stages, `task-orchestrator.md` also owns the child
dispatch ledger and receipt evidence contract. Stage briefs must include
allowed reads, forbidden reads, forbidden writes, scope hygiene, and child
identity instructions. Child subagents must not write
`stage_reviews/child_dispatch_ledger.json` or other coordinator-owned audit
files. Stage result/review receipts must include UTC timestamps, dependency
fields, and either an exact runtime `agent_id` or explicit `agent_id: null` plus
`identity_authority: "stage_reviews/child_dispatch_ledger.json"` when the child
does not know its id. Any transport recovery, identity normalization, or
child-side ledger write must be recorded as a process concern rather than
silently folded into `draft_ready`.

Do not mark the draft as ready if reviewed stages lack a passing spec
compliance review. Quality review happens only after spec compliance passes.

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

If user picks "不", write `result.json` with `status: "draft_ready"` only when
the orchestrator summary is `status: success`, every blocking spec compliance
review passed, and `verification.log` has no blocking `FAIL` lines. If the
summary is `partial` or a reviewed stage has unresolved failures, write
`result.json` with `status: "revision_needed"` or `status: "error"` and surface
the blocking review items instead of claiming the draft is ready.

Passing draft-ready path:

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

Revision-needed path:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status revision_needed \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --draft-path "<primary_deliverable_path_if_any>" \
  --verification-log "data/homework/<COURSE>/<HWID>/verification.log" \
  --human-review-item "<blocking spec review failure or human blocker>" \
  --note "draft generated but stage reviews or verification require revision"
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
**Status:** draft_ready / revision_needed / submitted / skipped / error
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
