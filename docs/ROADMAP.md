# AutoStudy Roadmap

> Goal: let a Canvas LMS student load one local skill in an agentic coding
> environment and get a Canvas-grounded study assistant, validated on HKUST(GZ):
> status planning, assignment reconnaissance, draft production,
> course-material archiving, notes, and eventually tutoring and reminders.

AutoStudy is deliberately local. It has no hosted backend and no project-owned
API key. Canvas access is handled by the separate `canvascli` CLI, while this
repository owns the agent-facing workflows and skill contracts.

For exact feature status and evidence, see
[`docs/plans/feature-list.json`](./plans/feature-list.json). For session
handoff, see [`docs/progress/agent-progress.md`](./progress/agent-progress.md).

---

## Product Shape

AutoStudy is an **assistant**, not a batch automation system.

Canvas Copilot is the main workflow reference, especially for source-by-source
Canvas reconnaissance, workbench structure, run ledgers, and verification
discipline. AutoStudy borrows those mature mechanisms, but changes the user
interaction: it explains findings, asks alignment questions, lets the user
decide scope, and treats drafts as inspectable local artifacts.

Superpowers is the workflow-discipline reference. AutoStudy translates its
patterns into local runtime artifacts:

| Workflow Need | AutoStudy Artifact |
|---|---|
| understand the real assignment | `spec.md`, `references/`, `investigation/rubric.md` |
| route homework startup state | `do-homework.md`, `prelaunch_startup_inventory.json` |
| clarify user intent | `investigation/user_notes.md`, `investigation/alignment_brief.md` |
| plan execution | `pipeline_design.md` or `repair_pipeline_design.md` |
| isolate work | `stage_briefs/`, executor receipts, reviewer receipts |
| verify before handoff | `verification_checklist.md`, `verification.log`, `result.json` |

---

## Milestones

```text
M1   canvascli data layer                         passing
M2   loadable AutoStudy skill + sync-status       passing
M3   first homework toolchain MVP                 passing
M3.5 Canvas Generic workbench runtime             active hardening
M4   course archive + notes, then tutor           partially passing
M5   multi-runtime + proactive reminders          pending
```

## M1 - Canvas Data Layer

Status: **passing**

The old in-repo scraper was extracted into
[`canvascli`](https://github.com/Aurorra1123/canvascli), an independent CLI with
JSON output by default.

Owned by `canvascli`:

- SSO login and saved Canvas session.
- Canvas REST calls and pagination.
- Current-term defaults and explicit `--term`.
- Atomic context commands such as assignment, rubric, front page, syllabus,
  modules, module items, page, file, assignment files.
- Canvas file download and submit protocol.

AutoStudy treats this as a CLI contract. Canvas access behavior should be fixed
in `canvascli` first, then reflected here.

## M2 - Loadable Skill And Status Planning

Status: **passing**

The first stable user flow is still the safest starting point:

```text
"看看这周有什么作业"
```

Current `sync-status` behavior:

1. fetch courses, assignments, announcements;
2. save raw snapshots under `data/`;
3. run `scripts/write_scan_plan.py`;
4. write `data/runs/<date>/pending_assignments.json`, `plan.json`, `REPORT.md`;
5. show a concise recommendation list;
6. wait for the user to choose a next action.

Important boundary: `sync-status` proposes; it does not execute homework. A
numbered plan item must be resolved through `scripts/select_plan_item.py` before
handoff to `do-homework`.

## M3 - Homework Toolchain MVP

Status: **passing historical base**

M3 proved that AutoStudy can produce real artifacts on real HKUST(GZ) Canvas
assignments:

| Scenario | Validated Capability |
|---|---|
| paper/report | academic prose + references + PDF render |
| slides | guizang HTML/PDF deck plus beamer fallback |
| math | LaTeX/math prose rendered through PDF |
| lab/code | source code, tests, report, and package-style outputs |

The M3 tools remain active:

- `assignment-recon`
- `writing-helper`
- `paper-search`
- `figure-maker`
- `code-writer`
- `test-runner`
- `slide-maker`
- `pdf-renderer`
- `humanizer`

What changed after M3: these tools are no longer chained by a fixed scenario
table. They are composed through `pipeline_design.md` after reconnaissance and
user alignment.

Remaining M3 verification gap:

- `canvascli submit` has code-level verification, but still needs one safe real
  unexpired/sandbox Canvas submission run before the feature is marked fully
  passing.

## M3.5 - Current Main Line

Status: **active hardening**

M3.5 is the major architecture shift from "can produce a draft" to "can
understand, plan, execute, review, and resume a homework workflow without
silently drifting."

### 1. Workbench Structure

Every assignment gets a durable local workbench:

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
├── prelaunch_startup_inventory.json
├── spec.md
├── problem.md
├── references/
│   ├── REFERENCE_INDEX.md
│   ├── source_docs/
│   ├── slides/
│   ├── external/
│   └── canvas_native/
│       └── announcement-<id-or-slug>/
│           ├── source.json
│           ├── source.txt
│           └── ORIGIN.md
├── investigation/
│   ├── explore_context.md
│   ├── explore_manifest.json
│   ├── recon_summary.md
│   ├── rubric.md
│   ├── unreachable.txt
│   ├── review_a.json
│   ├── user_notes.md
│   └── alignment_brief.md
├── pipeline_design.md
├── repair_plan.md
├── repair_pipeline_design.md
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

`spec.md` is the source-grounded assignment report. `problem.md` remains only
for compatibility with older tools.
Legacy source-scout artifacts such as `reading_plan.compact.json`,
`source_findings.compact.md`, `investigation/_appendix/source_index.json`,
`body_evidence_fragments/`, and source-scout receipts are stale/recovery/debug
only, not normal workbench outputs.

### 2. Unified Runtime Flow

The current runtime model is:

```text
do-homework.md router/preflight/route selection
-> startup inventory
-> clean start: assignment-source-intake.md source/spec intake
-> retained artifact: assignment-workflow-planner.md
   -> current-state-intake.md
   -> repair_plan.md / repair_pipeline_design.md
-> alignment contract
-> execution plan
-> executor/reviewer runtime
-> verification and result receipt
```

`full_flow` and `repair_flow` are now compatibility labels:

- clean start: no retained draft; source/spec exploration is normally enabled.
- retained-artifact start: the user intentionally continues or repairs existing
  visible artifacts; artifact/history/verification scouts may be enabled when
  inputs are present and declared.

The runtime branches on startup inventory, not hard-coded mode logic.

`do-homework` remains the public homework command. The split files are internal
runtime contracts:

- `do-homework.md`: router, preflight, and route selection.
- `assignment-source-intake.md`: clean-start source/spec intake.
- `assignment-workflow-planner.md`: alignment, planning, and retained artifact flow.
- `current-state-intake.md`: retained current-state exploration tool.

### 3. Canvas Generic Reconnaissance

For clean starts, `do-homework.md` routes to `assignment-source-intake.md` for
agent-led reconnaissance. Stage 1 fetches likely Canvas source surfaces through
atomic `canvascli` commands. Then the always-on `reference_collector` child
preserves task-relevant original evidence under `references/`, and the Main
Agent reads `references/REFERENCE_INDEX.md`, preserved source files, and
Canvas-native source copies before writing terminal reconnaissance artifacts:

- assignment page and attachments;
- Canvas rubric;
- course front page;
- syllabus;
- modules and every module item;
- announcements as a raw `canvas/announcements.json` collection snapshot;
- Canvas pages;
- files;
- external URLs such as Google Docs.

For announcements, `references/canvas_native/` stores only screened relevant
objects, one per `announcement-<id-or-slug>/source.json`; it must not mirror the
full `canvas/announcements.json` array.

The output is not a raw dump. It is a structured judgment:

- what sources were checked;
- what the main spec is;
- what deliverables are required;
- what grading criteria exist;
- what inputs were fetched;
- what is unreachable or missing.

### 4. User Alignment

After reconnaissance, `assignment-workflow-planner.md` aligns with the user
before execution.

For simple tasks this can be one confirmation. For open-ended assignments, the
agent asks one drift-reducing question at a time, compares approaches when
useful, previews a design skeleton, then writes and confirms:

```text
investigation/alignment_brief.md
```

For retained-artifact repairs, the equivalent terminal agreement is usually:

```text
repair_plan.md
```

That retained route is `do-homework.md` router ->
`assignment-workflow-planner.md` -> `current-state-intake.md` ->
`repair_plan.md` / `repair_pipeline_design.md`.

No confirmed terminal agreement means no final execution plan and no draft run.

### 5. Dynamic Pipeline And Review

`pipeline_design.md` or `repair_pipeline_design.md` is written after the
confirmed agreement. It declares:

- output mode and deliverables;
- constraints from spec/rubric/user intent;
- stages;
- tool mapping;
- reads and writes;
- delegation mode;
- review points;
- retry limits;
- human blockers.

`task-orchestrator` then writes stage briefs, dispatches executors and reviewers
when useful, records receipts, and verifies outputs.

### 6. Current Validation State

Validated in real Canvas-style workbenches:

- DSAA2011 project clean-start flows through reconnaissance, alignment,
  notebook/report/slides/package generation, verification, and transcript
  export.
- DSAA2011 repair flows cover report-depth repair and experiment-iteration
  repair.
- UCUG1505 final-project flow covers open-ended alignment, app generation,
  documentation, package, real API probe, mock fallback, and human video/code
  review items.

Status remains **in progress** because process clean-PASS still requires
hardening around forbidden archive exposure, child identity normalization,
startup/plugin context noise, receipt timestamps, and transcript evidence
discipline.

## M4 - Course Archive, Notes, Tutor

Status: **partially passing**

Passing:

- `sync-course` archives course files, announcements, modules, and index files
  under `data/courses/<COURSE>/`.
- `write-course-notes` generates Obsidian-style Markdown notes from synced
  lecture PDFs.

Pending:

- interactive tutor;
- weakness review;
- `data/mastery/<course>.json`;
- Socratic hint progression;
- durable mastery tracking.

## M5 - Multi-Runtime And Proactive Use

Status: **pending**

Planned:

- runtime adapters for Codex / Kimi-style subagents;
- proactive deadline checks;
- user-controlled reminders;
- better cross-session resume UX.

`canvascli` already helps portability because any agent that can shell out can
use the data layer. M5 is mostly about subagent dispatch and reminder mechanics.

---

## Design Principles

1. **Assistant, not automation.** Keep the user informed and in control.
2. **Dynamic skill composition.** Plan from the actual assignment, not a fixed
   pipeline table.
3. **Multi-turn iteration.** Existing drafts should be continued or repaired,
   not discarded by default.
4. **Three-layer preferences.** Task-level alignment is implemented; course and
   user preference layers are still pending.
5. **Review-first design.** Add stage-level review wherever it reduces false
   confidence.

---

## Near-Term Priorities

1. Harden `M3.5-EXECUTION-ARCHITECTURE` to a clean validation pass.
2. Improve retained-artifact repair and user-facing resume flows.
3. Implement course-level preference overlays.
4. Add interactive tutor tasks on top of synced course materials and notes.
5. Complete one safe real Canvas submission E2E for `M3-SUBMIT`.

---

## Out Of Scope

- hosted web UI;
- central backend or database;
- multi-user collaboration;
- automatic course registration or enrollment changes;
- hosted multi-account or multi-instance Canvas management;
- direct OJ/external-site submission without explicit user approval and a
  separate safety review.
