---
name: autostudy
description: HKUST(GZ) Canvas study assistant. Sync Canvas status, plan next actions, investigate assignments, draft local deliverables, archive course materials, and generate notes with user checkpoints.
---

# AutoStudy

AutoStudy is a local academic assistant skill for HKUST(GZ) students using
Canvas (`hkust-gz.instructure.com`). It depends on `canvascli` for Canvas data
access and uses this repository's Markdown task/tool files as the runtime
contract.

## Loading Model

AutoStudy is meant to run from a dedicated clone of this repository. The
repository root is the working directory: `.venv/`, `data/`, `scripts/`, and
`sub-skills/` are all resolved relative to it.

For a first-time user, clone the repository into a normal local folder, then
open the agent there or ask the agent to use that folder's `skill.md`:

```bash
git clone https://github.com/Aurorra1123/autoust-dev.git ~/workspace/autoust-dev
cd ~/workspace/autoust-dev
```

Do not assume any machine-specific absolute path. Do not copy only `skill.md`
without the rest of the repository; the task and tool contracts live under
`sub-skills/`.

The product posture is **assistant, not hidden automation**:

- explain what Canvas says;
- ask before scope-changing actions;
- ground homework in source evidence;
- produce local drafts and verification evidence;
- never submit without explicit user confirmation.

## What The User Can Ask

| User says... | Route |
|---|---|
| "看看这周作业" / "what's due" / "同步课程状态" | `sub-skills/tasks/sync-status.md` |
| "帮我完成 <COURSE> Project" / "做一下 lab" / "写这个 report" | `sub-skills/tasks/do-homework.md` |
| "继续改上次那个草稿" / "根据反馈修一下 report" | `sub-skills/tasks/do-homework.md` retained-artifact / repair path |
| "同步 <COURSE> 的资料" / "下载课件" / "sync course materials" | `sub-skills/tasks/sync-course.md` |
| "写 <COURSE> 的笔记" / "generate course notes" | `sub-skills/tasks/write-course-notes.md` |
| "登录失败了" / "重新登录" | Check `whoami`; if expired, use `sub-skills/tools/canvascli-setup.md` Step 3 |
| First time using AutoStudy | `sub-skills/tools/canvascli-setup.md` |

For unlisted Canvas-related requests, inspect `sub-skills/tools/canvascli-api.md`
and decide whether the request can be answered with the CLI contract. If it is
not in current scope, say so clearly.

## First-Time Setup Check

Before any task, run this from the AutoStudy repository root:

```bash
test -d .venv && .venv/bin/canvascli version > /dev/null 2>&1 \
  && .venv/bin/canvascli whoami > /dev/null 2>&1 \
  && echo OK || echo NEEDS_SETUP
```

- If `OK`, proceed to the requested task.
- If `NEEDS_SETUP`, read `sub-skills/tools/canvascli-setup.md` and execute the
  missing steps. It includes a Step 0 detection block.
- If a Canvas command fails with 401 / "session expired", only refresh login
  through `canvascli init`; do not retry the original task until login succeeds.

Important login model:

- `canvascli init` opens a browser for HKUST(GZ) SSO and refreshes the saved
  session.
- It is not a health check. Use `.venv/bin/canvascli whoami` for that.
- The saved session lives at `~/Library/Application Support/canvascli/state.json`
  on macOS. Treat it as a credential.
- The SSO "remember login" checkbox only affects how smooth the next browser
  refresh is; it does not decide whether `state.json` exists.

## Runtime Architecture

```text
skill.md
├── sub-skills/tasks/
│   ├── sync-status.md          # Canvas snapshot -> assistant plan
│   ├── do-homework.md          # Assignment workbench + alignment + draft flow
│   ├── task-orchestrator.md    # Stage execution/review from pipeline_design.md
│   ├── sync-course.md          # Persistent course material archive
│   └── write-course-notes.md   # Notes from synced lecture PDFs
├── sub-skills/tools/
│   ├── canvascli-setup.md
│   ├── canvascli-api.md
│   ├── assignment-recon.md
│   ├── _index.md
│   ├── code-writer.md
│   ├── writing-helper.md
│   ├── pdf-renderer.md
│   ├── slide-maker.md
│   └── ...
└── data/                       # Local snapshots, plans, workbenches, drafts
```

The Canvas data layer is the separate
[`canvascli`](https://github.com/Aurorra1123/canvascli) repository. AutoStudy
uses it as a CLI contract; do not copy Canvas REST implementation details into
task flow docs.

## Correct Task Flow

### Status / Planning

For "what's due" style requests:

1. Read and follow `sub-skills/tasks/sync-status.md`.
2. Write current Canvas snapshots to `data/sync/current/*.json`.
3. Run `scripts/write_scan_plan.py`.
4. Present the user-facing plan from `data/runs/<today>/REPORT.md`.
5. Do not execute any plan item until the user chooses one.

If the user chooses a numbered item, run:

```bash
.venv/bin/python scripts/select_plan_item.py --index <N> --pretty
```

Pass the returned `course_id`, `assignment_id`, `suggested_work_dir`, and
`recommended_action` into the next task. Do not re-match by title when the
selector has returned an exact object.

### Homework / Drafting

For "do this assignment" style requests, read `sub-skills/tasks/do-homework.md`.
The required source-of-truth chain is:

```text
prelaunch_startup_inventory.json
-> investigation/explore_context.md
-> investigation/explore_manifest.json
-> spec.md
-> investigation/rubric.md
-> references/
-> investigation/review_a.json
-> investigation/alignment_brief.md or repair_plan.md
-> pipeline_design.md or repair_pipeline_design.md
-> stage_briefs/
-> stage_results/
-> stage_reviews/
-> draft/
-> verification.log
-> result.json
```

Never draft from just the assignment title, Canvas description, or a single
link. Canvas assignment descriptions are often empty or incomplete. The
`problem.md` file is compatibility only; it is not the primary source.

The user-facing checkpoints are:

1. After exploration, summarize what was found and run the alignment loop.
2. After draft generation and verification, ask what the user wants to do next,
   including whether to submit.

For open-ended or creative work, keep the alignment loop alive until you can
write a concrete `alignment_brief.md` with selected approach, design skeleton,
constraints, delegated decisions, human review items, and stop conditions.

For retained drafts or user feedback, treat the run as a retained-artifact
start: preserve only user-visible artifacts declared in startup inventory,
write a current `repair_plan.md`, then plan through
`repair_pipeline_design.md` when appropriate.

## Safety Rules

1. **Never echo or log `state.json`** or any Canvas cookie/token material.
2. **Never auto-submit to Canvas.** `canvascli submit` is only called after the
   user explicitly confirms the exact file and assignment.
3. **Never auto-execute a `sync-status` plan item.** The plan is a
   recommendation, not approval.
4. **Never auto-pick "latest" assignment/course/file** when several candidates
   exist. Show the candidates or use `select_plan_item.py`.
5. **Confirm broad downloads.** `sync-course` must ask for course scope before
   downloading materials.
6. **Use the workbench.** Capture CLI JSON to disk, read files back, and produce
   stable artifacts. Do not summarize from a long stdout buffer as if it were
   evidence.
7. **Ask only necessary questions, one decision at a time.** Straightforward
   assignments need little alignment; open-ended projects need enough alignment
   to avoid guessing.
8. **Do not fabricate user-owned facts.** Group IDs, partner names, datasets,
   personal experience, instructor oral instructions, video URLs, and public
   links must come from the user or be explicitly marked as unresolved human
   review items.
9. **Do not leave template placeholders in deliverables.** Forbidden examples:
   `[PROBLEM N]`, `[TODO: align with actual project spec]`,
   `[此处由小组成员填入选题]`. Acceptable markers are specific
   `[CITATION NEEDED: ...]` or `[CLARIFICATION NEEDED: ...]` items surfaced for
   user review.
10. **If unsure, stop and explain the uncertainty.** Do not silently invent a
    workflow outside the skill's current scope.

## Telling The User What Happened

When finishing a task, keep the handoff compact:

- what was fetched or written;
- where the main artifact lives;
- what remains for the user, if anything;
- whether Canvas submission happened.

Examples:

```text
Fetched 7 courses, 57 assignments, and 5 announcements. The recommended plan is in data/runs/2026-06-10/REPORT.md.
```

```text
Draft artifacts are ready under data/homework/<COURSE>/<ASSIGNMENT>/draft/. No Canvas submission was attempted.
```

## When In Doubt

- `docs/PITFALLS.md` records known failure modes.
- `docs/ROADMAP.md` records current feature status and future direction.
- `docs/runtime-agent-protocol.md` records the unified execution/review model.
- `docs/COLLABORATION.md` records the boundary between AutoStudy and
  `canvascli`.
