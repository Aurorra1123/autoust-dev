# Homework Router / Source Intake / Planner Split Design

> Historical note: this file records the first router split. The active staged
> routing refinement is `docs/superpowers/specs/2026-06-16-homework-staged-recon-routing-design.md`
> and `docs/superpowers/plans/2026-06-16-homework-staged-recon-routing.md`.

Date: 2026-06-15

## Approved Direction

Split the current monolithic `sub-skills/tasks/do-homework.md` into a thin
router plus two task files, with retained current-state intake extracted into a
tool workflow:

```text
sub-skills/tasks/do-homework.md                  # router / preflight only
sub-skills/tasks/assignment-source-intake.md     # clean-start source recon
sub-skills/tasks/assignment-workflow-planner.md  # alignment, planning, retained artifact flow
sub-skills/tools/current-state-intake.md         # retained-artifact current-state intake
```

This is a file-boundary refactor, not a behavior rewrite. The implementation
should move the already-debugged sections into the new files with minimal
content changes. Only routing language, handoff instructions, file names, and
tests/docs that point to the old monolithic shape should change.

## Goals

1. Keep `do-homework.md` as the stable user-facing task entrypoint.
2. Make clean-start Canvas/source reconnaissance readable in isolation.
3. Make post-recon alignment, pipeline design, and retained-artifact planning
   readable in isolation.
4. Keep retained-artifact current-state intake reusable and linkable as a tool
   workflow, parallel in shape to `assignment-recon.md`.
5. Preserve the current `reference_collector` contract exactly, including:
   Stage 1 full raw snapshots, Stage 2 narrowed preserved references,
   per-announcement Canvas-native preservation, and ledger-backed child identity.
6. Preserve the current retained-artifact behavior: existing drafts do not run
   clean-start source recon by default, but still need current-state exploration
   before alignment/planning.
7. Keep preflight archive and startup inventory as a shared entry boundary before
   route selection.

## Non-Goals

- Do not redesign `assignment-recon.md`.
- Do not redesign `reference_collector`.
- Do not change `task-orchestrator.md` execution semantics.
- Do not introduce a new source-scout pipeline.
- Do not rewrite the detailed `[B]` alignment loop or `[C]` pipeline schema
  beyond moving it to the planner file and adjusting references.
- Do not rename runtime artifacts such as `spec.md`, `review_a.json`,
  `alignment_brief.md`, `repair_plan.md`, `pipeline_design.md`, or
  `repair_pipeline_design.md`.

## Current Problem

`do-homework.md` currently carries all of these responsibilities in one long
file:

- entry routing and plan-item action handling;
- preflight startup inventory and archive boundaries;
- clean-start Canvas/source reconnaissance;
- `reference_collector` preservation and A-gate checks;
- user-facing recon summary and alignment loop;
- retained-artifact current-state exploration rules;
- pipeline design and pipeline approval handoff.

Because these concerns live together, models can incorrectly treat every
`do-homework` run as clean-start Canvas recon. That is wrong for retained
drafts, `pipeline_ready`, `draft_ready`, and repair flows. Conversely, simply
skipping recon for retained drafts is also wrong: those flows still need a
bounded current-state exploration layer before alignment/planning.

## Target File Responsibilities

### `do-homework.md` Router

The router stays as the only task file named `do-homework`. It should be short
and should not execute source recon, alignment, or planning details itself.

Responsibilities:

- Verify Canvas CLI preconditions or route to setup.
- Resolve a single assignment when needed.
- Determine `work_dir` and current `recommended_action`.
- Run shared preflight archive/startup inventory.
- Route to the correct task file.
- State that downstream task files own the actual flow.

The router owns the route table:

```text
recommended_action: recon
entry_preset: clean_start
route:
  1. sub-skills/tasks/assignment-source-intake.md
  2. sub-skills/tasks/assignment-workflow-planner.md

recommended_action: review_or_execute
state: pipeline_ready
route:
  sub-skills/tasks/assignment-workflow-planner.md#pipeline-review
no clean-start source recon

recommended_action: review_or_submit
state: draft_ready
route:
  sub-skills/tasks/assignment-workflow-planner.md#retained-artifact-review
no clean-start source recon by default

recommended_action: continue
state: failed / error / interrupted
route:
  sub-skills/tasks/assignment-workflow-planner.md#recovery-intake
run source intake only when the failure is explicitly missing or stale source evidence
```

### `assignment-source-intake.md`

This file owns clean-start source/spec reconnaissance. It receives an initialized
workbench and accepted startup inventory from the router.

It should contain the current `[A]` source path with minimal edits:

- startup assumptions for clean-start source intake;
- workbench structure relevant to source intake;
- `assignment-recon.md` invocation;
- Stage 1 raw Canvas snapshot rules;
- `reference_collector` dispatch and ledger requirements;
- preserved reference read boundary;
- `spec.md`, `rubric.md`, `review_a.json`, `recon_summary.md`,
  `explore_context.md`, and preliminary output mode;
- A-gate / parent self-check;
- terminal handoff instruction:

```text
After this file completes successfully, continue by reading:
sub-skills/tasks/assignment-workflow-planner.md
```

This file should not contain the full `[B]` alignment loop or `[C]` pipeline
design schema.

### `assignment-workflow-planner.md`

This file owns the current-task agreement and pipeline planning flow. It has two
entry modes. It may invoke tools, but it should not inline the full retained
current-state intake procedure.

Clean recon entry:

- Read the terminal outputs from `assignment-source-intake.md`.
- Present the conclusion-first recon briefing.
- Run the existing `[B]` alignment loop.
- Write and confirm `investigation/alignment_brief.md`.
- Write `pipeline_design.md`.
- Stop at pipeline review.

Retained artifact entry:

- Read `prelaunch_startup_inventory.json`.
- Invoke `sub-skills/tools/current-state-intake.md` using the accepted startup
  inventory and current request.
- Read the current-state intake outputs, not raw archived process evidence.
- Run the retained-artifact alignment loop.
- Write `repair_plan.md` as the terminal agreement for repair/change flows.
- Write `repair_pipeline_design.md` when planning a repair/change pipeline.

The planner must not delete `draft/`, silently clean-start the workbench, or
rerun Canvas/source recon unless current evidence says source/spec artifacts are
missing, stale, or blocking.

### `current-state-intake.md`

This tool workflow owns retained-artifact current-state exploration. It is the
retained-artifact counterpart to `assignment-recon.md`: `assignment-recon.md`
answers "what is the assignment source?", while `current-state-intake.md`
answers "what is the current retained state that planning may rely on?"

Inputs:

```text
<work_dir>/prelaunch_startup_inventory.json
current user request / repair request
retained user-visible artifacts named in startup inventory
allowlisted_history_files named in startup inventory
```

Responsibilities:

- Preserve retained user-visible artifacts as current task context only when the
  startup inventory names them.
- Treat old logs, prior reviews, transcripts, old stage receipts, old
  `pipeline_design.md`, prior `repair_plan.md`, and prior
  `repair_pipeline_design.md` as process evidence by default.
- Enable only relevant artifact/codebase/process-history/verification scouts.
- Record skipped scouts with concrete reasons.
- Allow process-history scouts to read only exact `allowlisted_history_files`.
- Consolidate scout results into current-run artifacts before the planner writes
  alignment or execution plans.
- Never write `spec.md`, `review_a.json`, `alignment_brief.md`,
  `repair_plan.md`, `pipeline_design.md`, or `repair_pipeline_design.md`.
- Never run clean-start Canvas/source recon; if source/spec evidence is missing
  or stale, report that as a blocker for the planner/router to handle.

Outputs:

```text
investigation/explore_manifest.json
investigation/explore_context.md
investigation/repair_recon.md       # when useful for retained-artifact compatibility
repair_request.md                   # when user feedback needs a stable file
```

The planner reads these outputs before writing `repair_plan.md` or
`repair_pipeline_design.md`.

## Shared Preflight Archive Design

Preflight belongs in the router because it must run before deciding which
downstream task owns the flow.

Every run writes or refreshes:

```text
<work_dir>/prelaunch_startup_inventory.json
```

When existing active workbench evidence needs isolation, archive it under:

```text
<work_dir>/archive/<run_id>-preflight/
  manifest.json
  moved_files/
  notes.md
```

`run_id` should be UTC timestamp based, for example
`2026-06-15T143022Z-preflight`.

Clean-start preflight:

- If a stale workbench exists and the route is clean-start recon, archive stale
  process evidence before source intake.
- Do not treat old `draft/`, old `pipeline_design.md`, old `alignment_brief.md`,
  old reviews, old transcripts, old stage results, or old `result.json` as source
  context.
- If the user explicitly says to ignore previous submitted/existing content, the
  router may archive the active workbench and rebuild the clean surface.

Retained-artifact preflight:

- Do not archive away current user-visible artifacts.
- Keep current draft/package/rendered deliverables available only when they are
  listed as retained artifacts in startup inventory.
- Archive or forbid old process evidence unless allowlisted for a
  process-history scout.
- Record the route as `assignment-workflow-planner.md`.

The startup inventory should distinguish:

```json
{
  "entry_preset": "clean_start | retained_artifact_start",
  "route": "assignment-source-intake.md | assignment-workflow-planner.md",
  "retained_user_visible_artifacts": [],
  "allowlisted_history_files": [],
  "forbidden_context": [],
  "archived_process_evidence": [],
  "must_not_clean_start": false
}
```

## Migration Strategy

Implementation should be mostly mechanical:

1. Copy the existing `[A]` workbench/source reconnaissance sections into
   `assignment-source-intake.md`.
2. Copy existing `[B]` / `[C]` sections into `assignment-workflow-planner.md`.
3. Create `sub-skills/tools/current-state-intake.md` and move retained-artifact
   startup, scout, and current-state exploration guidance there.
4. Replace the body of `do-homework.md` with router/preflight/handoff guidance.
5. Make retained-artifact entries in `assignment-workflow-planner.md` link to
   `../tools/current-state-intake.md`.
6. Update references in `skill.md`, README files, runtime protocol, validation
   docs, tools index, and policy tests.
7. Keep section wording stable unless it must change because the file boundary
   changed.

The implementation should avoid broad rewrites. If a paragraph already encodes a
debugged runtime contract, move it first and edit only the minimum necessary
cross-references.

## Read Boundaries After The Split

After clean source intake, the planner normally reads:

```text
prelaunch_startup_inventory.json
investigation/explore_manifest.json
investigation/explore_context.md
investigation/recon_summary.md
references/REFERENCE_INDEX.md
references/source_docs/**
references/slides/**
references/external/**
references/canvas_native/**/source.json
references/canvas_native/**/source.txt
spec.md
investigation/rubric.md
investigation/review_a.json
investigation/unreachable.txt
problem.md
investigation/recon_summary.md     # includes preliminary output-mode note
investigation/explore_context.md   # includes preliminary output-mode note
```

For retained-artifact planning, `current-state-intake.md` reads only current
retained artifacts and allowlisted history from the startup inventory, then
records distilled current-run findings in `explore_context.md` /
`repair_recon.md`. The planner reads those distilled outputs before alignment
and planning.

Raw `canvas/*.json` remains recovery/fallback evidence, not normal planner
context after source intake preserves task-relevant source copies.

## Testing Strategy

Policy tests should assert:

- `do-homework.md` is a router and names both downstream task files.
- `assignment-source-intake.md` contains clean-start Canvas/source recon and
  `reference_collector` requirements.
- `assignment-source-intake.md` does not contain the full `[B]` alignment loop or
  full `[C]` pipeline schema.
- `assignment-workflow-planner.md` contains `[B]` alignment, `[C]` pipeline
  design, a link to `current-state-intake.md`, and repair planning guidance.
- `current-state-intake.md` contains retained-artifact current-state intake,
  scout enable/skip rules, allowlisted history boundaries, and terminal outputs.
- retained-artifact route does not default to clean-start Canvas/source recon.
- preflight archive/startup inventory is in router guidance.
- legacy source-scout artifacts remain forbidden/stale, not normal outputs.
- existing source-intake policies still pass, including per-announcement
  preservation and ledger-backed `reference_collector` identity.

## Acceptance Criteria

The refactor is accepted when:

1. `do-homework.md` is short enough to act as a router and no longer carries the
   detailed source-intake or planner bodies.
2. Clean-start route clearly points through `assignment-source-intake.md` then
   `assignment-workflow-planner.md`.
3. Existing draft / retained artifact route clearly points directly to
   `assignment-workflow-planner.md`, which invokes `current-state-intake.md`.
4. No behavior-critical details from the current A/B/C flow are deleted; they are
   moved to the appropriate file.
5. `sub-skills/tools/_index.md` lists `current-state-intake.md` as a tool
   workflow.
6. Tests pass.
7. The final diff is understandable as a split/move refactor rather than a new
   workflow rewrite.
