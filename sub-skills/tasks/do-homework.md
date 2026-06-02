---
name: do-homework
description: End-to-end homework completion. Use when the user asks "complete X assignment", "do my paper for DLED3020", "帮我做 lab 5". Runs Copilot-style Canvas reconnaissance, produces a draft via task-orchestrator, asks confirmation, optionally submits via canvascli.
---

# Do Homework

The flagship M3 task. The user asks something like:
- "帮我做 DLED3020 的 Paper Critique"
- "complete DSAA2043 Lab Assignment 1"
- "做一下 UCUG1077 的 group presentation slides"
- "写 DSAA2012 的 project report"

You go from "user names an assignment" to "draft / code / slides exists and (optionally) is submitted to Canvas". **Two and only two AskUserQuestion checkpoints**: at [B] for intent confirmation, at [E] for submission confirmation. Everything else runs without prompting the user.

## Preconditions

Before running, check the same set as `sync-status.md`:
1. `.venv/bin/canvascli version` returns 0
2. `.venv/bin/canvascli whoami` returns 0 (session valid)

If either fails, redirect to `tools/canvascli-setup.md` step 3 and stop.

Also: if the user hasn't named a specific assignment, run `sync-status.md` first to surface options, then come back here.

## Execution flow

### [A] Build the assignment workbench (no user interaction)

This step follows Canvas Copilot's "inspect all sources first" habit. It prevents the most common failure mode: treating an empty assignment description or a single attachment link as the whole prompt.

#### [A1] Resolve identifiers

Resolve the user's natural-language request to a `(course_id, assignment_id)` pair. The user usually says "DLED3020 Paper Critique" — match against `data/assignments.json` by case-insensitive substring of `name` AND course code in `context_name`. If ambiguous (multiple matches), surface the candidates via AskUserQuestion at [B] — see below.

#### [A2] Create the workbench directory

```bash
mkdir -p "data/homework/<COURSE>/<HWID>"
```

Where `<HWID>` is a short slug derived from the assignment name (e.g. `paper-critique`).

Target structure:

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
├── spec.md
├── problem.md
├── references/
├── investigation/
├── draft/
└── result.json
```

The `canvas/` directory stores raw `canvascli` JSON snapshots. `spec.md` is the main reconnaissance artifact. `problem.md` is kept as a compatibility file for current tools.

#### [A3] Run Copilot-style reconnaissance — MANDATORY

Invoke `tools/problem-extractor.md`. It will:

1. Fetch assignment, rubric, front page, syllabus, modules, every module's items, relevant pages, file metadata, and direct assignment files through atomic `canvascli` commands.
2. Store raw JSON under `<work_dir>/canvas/`.
3. Download reachable Canvas files into `<work_dir>/references/`.
4. Write `<work_dir>/spec.md` with source-by-source context and source candidates.
5. Write `<work_dir>/problem.md` as a compatibility view for downstream tools.
6. Write `<work_dir>/investigation/rubric.md`, `unreachable.txt`, and `review_a.json`.

```bash
mkdir -p "data/homework/<COURSE>/<HWID>/scripts"
# Write the script per tools/problem-extractor.md template
.venv/bin/python "data/homework/<COURSE>/<HWID>/scripts/extract_problem.py" \
    "data/homework/<COURSE>/<HWID>" "<course_id>" "<assignment_id>"
```

**Read `spec.md` and `investigation/review_a.json` immediately after they're written.** Then read `problem.md` for compatibility with the existing toolchain. Do NOT skip this read. The whole skill collapses to template-fill nonsense if you treat `assignment.description` as the problem statement.

#### [A4] Gate on reconnaissance quality

If the extractor exited non-zero, OR `review_a.json.verdict` is not `proceed`, OR both `spec.md` and `problem.md` are thin, the problem text is missing or incomplete. Surface this at [B] as a third option:

> "I checked the assignment page, rubric, course front page, syllabus, modules, pages, and linked files, but I still couldn't identify a complete spec. Options:
>   • Paste the spec text or URL yourself
>   • Point me to the correct module/page/file
>   • Stop for now"

Do NOT proceed silently to [C] when `spec.md` is thin — the deliverable will be garbage. This is the most important rule in this whole task.

### [B] Summary + intent confirmation (AskUserQuestion #1)

Read `spec.md` first, then `problem.md` (NOT `assignment.json.description` directly). Summarize for the user in 4–6 lines:
- Course + assignment name + due_at (local time) + points_possible — from `spec.md` metadata
- **Source trail**: name the sources inspected and which one appears to be the main spec. Real examples: "assignment page was empty; module Project guidelines contained `DSAA2011-26sp-project_announce-L01.pdf`" or "assignment page and Week 4 module both point to the same Google Doc spec; Week 9 slides look like supporting context."
- **Concrete problem summary**: the actual questions/problems/deliverables being asked, drawn from `spec.md` / downloaded references. NOT a paraphrase of the assignment title.
- Rubric or grading criteria in a compact list if present; say "Canvas rubric not found" if only spec-based criteria exist.
- Detected scenario: `paper` / `slides` / `math` / `lab` (use the heuristic table in `task-orchestrator.md`)

Then `AskUserQuestion`:

```
针对这份 <COURSE> <name>，你想我:
  - 完整完成草稿 (推荐)
  - 只做某几题 / 某个章节 (你告诉我具体范围)
  - 先不做，我自己看一下
```

If user picks "只做某几题": follow up with a single free-form question asking the scope, capture as `partial_scope: "<user text>"` in the task profile.

If user picks "先不做": stop here. Don't touch the orchestrator.

If `[A4]` flagged reconnaissance failure, add a 4th option to this AskUserQuestion: "粘贴题目内容或 spec 链接给我" — capture the user's pasted text into `<work_dir>/problem_user.md` and reference it from `task_profile.source.problem_md`.

### [C] Construct task profile (no user interaction)

Build a YAML file at `data/homework/<COURSE>/<HWID>/task_profile.yaml`. Schema follows `task-orchestrator.md`'s "Task profile schema" section:

```yaml
type: paper | slides | math | lab        # from [B] heuristic
work_dir: data/homework/<COURSE>/<HWID>/
source:
  spec_md: data/homework/<COURSE>/<HWID>/spec.md                 # PRIMARY — source-by-source context
  problem_md: data/homework/<COURSE>/<HWID>/problem.md           # compatibility view for current tools
  references_dir: data/homework/<COURSE>/<HWID>/references/      # raw + extracted reference files
  investigation_dir: data/homework/<COURSE>/<HWID>/investigation/
  assignment_json: data/homework/<COURSE>/<HWID>/canvas/assignment.json # metadata only (due_at, rubric, points)
deliverables:
  - path: data/homework/<COURSE>/<HWID>/draft/final.pdf  # adjust per scenario
    format: pdf
constraints:
  length: ~1500 words      # or whatever rubric implies
  citation_style: APA      # APA / IEEE / none
  language: en             # en / zh
  partial_scope: null      # set if user chose partial in [B]
required_capabilities:
  # paper: [compose_essay, search_papers, make_figure, render_pdf]
  # slides: [make_slides, render_pdf]
  # math: [compose_essay, render_pdf]
  # lab: [write_code, run_tests, compose_essay, render_pdf]
```

**Note on `source.spec_md` and `source.problem_md`**: new orchestration should read `spec.md` first. Current deliverable tools still treat `problem.md` as the source of truth, so `problem-extractor` writes both. `assignment_json` exists only for metadata (due_at, rubric, points) — tools that read `description` directly are buggy.

See `tools/_index.md` "Scenario → Tool chain" table for the exact `required_capabilities` per scenario.

### [D] Orchestrator runs (no user interaction unless ambiguous)

Invoke `tasks/task-orchestrator.md` with the profile. The orchestrator:
1. Matches `required_capabilities` to tools in `tools/_index.md`
2. Runs them sequentially, each writing to `work_dir`
3. Final tool (usually `pdf-renderer`) produces the deliverable

The orchestrator must NOT prompt the user. If a tool genuinely needs disambiguation, it raises back to do-homework, which adds a single inline AskUserQuestion — but this should be rare. Aim for zero extra prompts.

### [E] Draft review + submission confirmation (AskUserQuestion #2)

Once the orchestrator returns, show the user:
- The deliverable path(s)
- A one-line preview: for PDFs, file size + page count via `pdfinfo` if available; for code, file count + test pass rate
- The Canvas submission UI URL: `https://hkust-gz.instructure.com/courses/<course_id>/assignments/<assignment_id>`

Then `AskUserQuestion`:

```
草稿已经在 <path>。要现在用 canvascli 提交到 Canvas 吗?
  - 是，提交
  - 不，我自己看完再说 (推荐)
  - 重做 / 改某部分 (告诉我具体改什么)
```

If user picks "重做": capture their change request, go back to [C] with adjustments to `task_profile.yaml` (do NOT re-fetch [A]).

If user picks "不": stop. Tell them the file path one more time so they can find it.

### [F] Submit (only if user confirmed in [E])

```bash
.venv/bin/canvascli submit <assignment_id> "<deliverable_path>" -c <course_id> --pretty
```

Capture stdout — it returns the submission object with attempt number, submitted_at, etc. Show the user:
- ✓ Submitted as attempt #N at <submitted_at>
- Canvas URL to verify

If submit fails (assignment overdue / locked / etc.), tell the user the Canvas error message verbatim and offer to retry or stop. Do NOT loop automatically.

## Output format (final message to user)

After [F] (or [E] if not submitting):

```markdown
## ✓ <COURSE> <assignment name>

**Deliverable:** `data/homework/<COURSE>/<HWID>/final.pdf` (N pages, ~Mkb)
**Submission:** attempt #N, submitted_at 2026-05-23T14:32:00Z
**Canvas URL:** https://hkust-gz.instructure.com/courses/.../assignments/...

Files produced:
- final.pdf — the submitted deliverable
- draft.md — markdown source (for re-render)
- references.bib — citations used (if paper)
- figures/ — any generated figures
```

If not submitted:
```markdown
## Draft ready — <COURSE> <assignment name>

**File:** `data/homework/<COURSE>/<HWID>/final.pdf`

Not submitted. You can review and submit later via Canvas, or come back to me and say "submit it".
```

## Safety

1. **Two AskUserQuestion checkpoints only**: [B] and [E]. Don't sneak more prompts in. If you need disambiguation, batch it into [B].
2. **Never auto-submit.** Even if the user said "complete and submit" upfront, still confirm at [E].
3. **Never modify the raw Canvas JSON** under `data/homework/.../canvas/*.json`. These are snapshots of Canvas state.
4. **Stop on first orchestrator failure.** Don't silently retry. Surface the error and ask the user how to proceed.
5. **Submit failures are not retries.** A 422 or 403 from Canvas means something the user should see — don't loop.
6. **`partial_scope` is honored.** If the user said "only do problem 2", the writing-helper / code-writer must only produce that part. Don't over-deliver.
7. **Ground every deliverable in `spec.md` / `problem.md`. NEVER produce placeholder content.** This is the most important rule:
   - No `[PROBLEM N]` / `[TODO: align with actual project spec]` / `[此处由小组成员填入选题]` in any output file.
   - The two acceptable inline markers are: `[CITATION NEEDED: <topic>]` (writing-helper, when `references.bib` lacks an entry) and `[CLARIFICATION NEEDED: <specific question>]` (any tool, when `problem.md` is genuinely ambiguous on a specific point).
   - `[CLARIFICATION NEEDED]` markers are surfaced collectively at [E] — the user can answer them before submission.
   - If `spec.md` / `problem.md` is too thin to produce real content at all, you must NOT have reached [C]. See [A4].

## Pitfalls

- **Course code in `data/assignments.json` is in `context_name`, not a separate field.** Pattern: `"DLED 3020 - English Communication I (L1)"`. Strip section + dashes when matching.
- **Don't read `assignment.description` as the problem statement.** It may be empty, a file link, or one of several sources. Always go through `[A3]` to materialize `spec.md` and `problem.md`. This is the single most common cause of "the agent produced mechanical template content".
- **Don't stop at the first match.** Canvas Copilot's mature workflow checks assignment page, rubric, front page, syllabus, modules, pages, files, and external URLs before deciding which source is the spec.
- **The work_dir path can contain spaces and Chinese** (course names like "数据结构与算法"). Always double-quote shell arguments. See `docs/PITFALLS.md` #10.
- **Don't re-fetch [A] on "重做"**. The Canvas description and attachments haven't changed. Just rebuild [C] with new constraints. (If the user says "the problem changed on Canvas", do re-fetch — but ask first.)
- **`rubric` field can be `null`** even for assignments that have a rubric in the Canvas UI (rubric is associated via a separate API). If null, fall back to using the description's "Grading" section if present.
- **`submission_types` matters for [F]**. `online_upload` is what canvascli submit handles. If the assignment is `online_text_entry` or `discussion_topic`, canvascli submit will fail — say so at [E] and offer manual fallback.
- **`[CLARIFICATION NEEDED: ...]` markers** are tools' way of asking the user about a specific ambiguity in `problem.md`. Collect them all and present at [E] before submission — don't burn an AskUserQuestion checkpoint per marker.

## Cross-references

- Scenario detection heuristics: `tasks/task-orchestrator.md` "Heuristics for type inference"
- Tool capability matrix: `tools/_index.md` "Scenario → Tool chain"
- Canvas commands used: `tools/canvascli-api.md` (atomic context commands, submit)
- Submission protocol details: `tools/canvascli-api.md` submit section
