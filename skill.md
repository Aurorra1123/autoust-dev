---
name: autostudy
description: Local Canvas LMS study assistant, validated on HKUST(GZ). Sync Canvas status, plan next actions, investigate assignments, draft local deliverables, archive course materials, and generate notes with user checkpoints.
---

# AutoStudy

AutoStudy is a local academic assistant skill for students using Canvas LMS,
validated on HKUST(GZ)'s Canvas instance. It depends on `canvascli` for Canvas
data access and uses this repository's Markdown task/tool files as the runtime
contract.

## Loading Model

AutoStudy is meant to run from a dedicated clone of this repository. The
repository root is the working directory: `.venv/`, `data/`, `scripts/`, and
`sub-skills/` are all resolved relative to it.

For first-time setup, choose the clone location from the user's current agent
workspace before using any sample path:

- If the current agent workspace is an empty folder chosen by the user for this
  setup, clone AutoStudy into that folder with `git clone <repo> .`, then run
  setup there.
- If the current directory is already an AutoStudy clone, run setup in that
  directory.
- If the current directory is non-empty and not an AutoStudy clone, or if the
  current workspace is unclear, ask the user where to put the repository before
  cloning.
- Do not silently default to `~/workspace`, Desktop, Downloads, or any other
  machine-specific location. Example paths are examples only.

If the user wants to choose a folder manually, clone the repository into a
normal local folder, then open the agent there or ask the agent to use that
folder's `skill.md`:

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

- `canvascli init` opens a browser for the configured Canvas SSO and refreshes
  the saved session.
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
-> investigation/explore_manifest.json
-> references/REFERENCE_INDEX.md
-> references/source_docs/, references/slides/, references/external/
-> references/canvas_native/
-> spec.md
-> investigation/rubric.md
-> investigation/review_a.json
-> investigation/recon_summary.md
-> investigation/explore_context.md
-> investigation/alignment_brief.md or repair_plan.md
-> pipeline_design.md or repair_pipeline_design.md
-> stage_briefs/
-> stage_results/
-> stage_reviews/
-> draft/
-> verification.log
-> result.json
```

Standard homework reconnaissance always uses `reference_collector` after the
Canvas raw snapshot. The collector narrows task-relevant sources and preserves
complete original evidence under `references/`. It may download files, extract
PDF text, preserve PDF link annotations, and copy Canvas-native source JSON
blocks verbatim into `references/canvas_native/`.
Announcement arrays are collection snapshots, not source objects. Do not copy the
full `canvas/announcements.json` array into `references/canvas_native/`; preserve
only task-relevant announcement objects, one object per
`references/canvas_native/announcement-<id-or-slug>/source.json`, with
`REFERENCE_INDEX.md` raw origins such as `canvas/announcements.json#id=26545`.

The collector must not interpret the assignment, summarize requirements as the
only evidence path, or write final reconnaissance artifacts. The Main Agent
reads `references/REFERENCE_INDEX.md`, preserved reference files, and
Canvas-native `source.json` / `source.txt` copies before writing `spec.md`,
`rubric.md`, `review_a.json`, `recon_summary.md`, and `explore_context.md`.

Do not create `reading_plan.compact.json`, `reading_plan.compact.approved.json`,
`source_findings.compact.md`, source index appendix files, source body fragments,
or source scout receipts in standard runs.

Never draft from just the assignment title, Canvas description, or a single
link. Canvas assignment descriptions are often empty or incomplete. The
`problem.md` file is compatibility only; it is not the primary source.
For Canvas-native bodies such as assignment, syllabus, front page, and pages,
raw Canvas JSON remains durable backing evidence, but the normal Main Agent
read interface is the verbatim preserved copy under `references/canvas_native/`.
Derived summaries are not authoritative sources. Downstream stages that need
Canvas-native constraints should read the preserved `source.json` / `source.txt`
copies; raw `canvas/*.json` reads are recovery or explicit fallback exceptions.

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

For `do-homework [B]`, do not use the generic artifact handoff shape. Use the
conclusion-first assignment briefing required by `sub-skills/tasks/do-homework.md`:
lead with the investigation conclusions, source findings, deliverables, grading
signals, conflicts or gaps, and the next alignment question. File paths are only
a short optional audit appendix after the assignment briefing.

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
