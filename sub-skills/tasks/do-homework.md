---
name: do-homework
description: End-to-end homework completion. Use when the user asks "complete X assignment", "do my paper for DLED3020", "帮我做 lab 5". Pulls description + rubric from Canvas, produces a draft via task-orchestrator, asks confirmation, optionally submits via canvascli.
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

### [A] Pull assignment detail (no user interaction)

Resolve the assignment to a `(course_id, assignment_id)` pair. The user usually says "DLED3020 Paper Critique" — match against `data/assignments.json` by case-insensitive substring of `name` AND course code in `context_name`. If ambiguous (multiple matches), surface the candidates via AskUserQuestion at [B] — see below.

Once resolved, fetch the full assignment object:

```bash
.venv/bin/canvascli assignment <assignment_id> -c <course_id> > data/homework/<COURSE>/<HWID>/assignment.json
```

Where `<HWID>` is a short slug derived from the assignment name (e.g. `paper-critique`). Create the dir first:

```bash
mkdir -p "data/homework/<COURSE>/<HWID>"
```

The JSON includes `description` (HTML body), `rubric` (criteria), `points_possible`, `due_at`, `submission_types`. Keep raw HTML — downstream tools will strip / parse as needed.

### [B] Summary + intent confirmation (AskUserQuestion #1)

Read `assignment.json`. Summarize for the user in 4–6 lines:
- Course + assignment name + due_at (local time) + points_possible
- One-paragraph plain-text summary of `description` (strip HTML mentally, keep meaning)
- Rubric in a compact list if present (criterion → points)
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

### [C] Construct task profile (no user interaction)

Build a YAML file at `data/homework/<COURSE>/<HWID>/task_profile.yaml`. Schema follows `task-orchestrator.md`'s "Task profile schema" section:

```yaml
type: paper | slides | math | lab        # from [B] heuristic
work_dir: data/homework/<COURSE>/<HWID>/
source:
  assignment_json: data/homework/<COURSE>/<HWID>/assignment.json
deliverables:
  - path: data/homework/<COURSE>/<HWID>/final.pdf  # adjust per scenario
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
3. **Never modify the assignment JSON** under `data/homework/.../assignment.json`. It's a snapshot of Canvas state.
4. **Stop on first orchestrator failure.** Don't silently retry. Surface the error and ask the user how to proceed.
5. **Submit failures are not retries.** A 422 or 403 from Canvas means something the user should see — don't loop.
6. **`partial_scope` is honored.** If the user said "only do problem 2", the writing-helper / code-writer must only produce that part. Don't over-deliver.

## Pitfalls

- **Course code in `data/assignments.json` is in `context_name`, not a separate field.** Pattern: `"DLED 3020 - English Communication I (L1)"`. Strip section + dashes when matching.
- **Assignment `description` is raw HTML.** Some are 50KB+ of nested divs. Don't paste the whole thing to the user; extract the meaningful text via lxml or BeautifulSoup, fall back to regex `<[^>]+>` strip.
- **`due_at` is ISO 8601 UTC.** Convert to local (`Asia/Shanghai`, +08:00) when showing the user. Past `due_at` does NOT mean you can't fetch the assignment — it just means submit will likely 403.
- **The work_dir path can contain spaces and Chinese** (course names like "数据结构与算法"). Always double-quote shell arguments. See `docs/PITFALLS.md` #10.
- **Don't re-fetch [A] on "重做"**. The Canvas description hasn't changed. Just rebuild [C] with new constraints.
- **`rubric` field can be `null`** even for assignments that have a rubric in the Canvas UI (rubric is associated via a separate API). If null, fall back to using the description's "Grading" section if present.
- **`submission_types` matters for [F]**. `online_upload` is what canvascli submit handles. If the assignment is `online_text_entry` or `discussion_topic`, canvascli submit will fail — say so at [E] and offer manual fallback.

## Cross-references

- Scenario detection heuristics: `tasks/task-orchestrator.md` "Heuristics for type inference"
- Tool capability matrix: `tools/_index.md` "Scenario → Tool chain"
- Canvas commands used: `tools/canvascli-api.md` (assignment, submit)
- Submission protocol details: `tools/canvascli-api.md` submit section
