# Homework Staged Recon Routing Design

Date: 2026-06-16

## Approved Direction

Refine the homework split so `do-homework.md` reveals only the first required
stage for the current entry type. Downstream stages are discovered by reading
the previous stage to completion, not by preloading every related task file.

Target task files:

```text
sub-skills/tasks/do-homework.md              # router / preflight only
sub-skills/tasks/background-recon.md         # clean-start assignment background recon
sub-skills/tasks/existing-work-recon.md      # retained draft / repair / continue state recon
sub-skills/tasks/alignment-planning.md       # user alignment, brainstorm, pipeline planning
```

`sub-skills/tools/assignment-recon.md` should be folded into
`background-recon.md` and removed as a normal independent entry. The previous
`sub-skills/tools/current-state-intake.md` should move to
`sub-skills/tasks/existing-work-recon.md` because it is a routed homework stage,
not a low-level reusable tool.

Important runtime disclosure rule: `do-homework.md` must expose only the two
first-stage choices. It must not name `alignment-planning.md` as an immediate or
future file to read. The alignment stage is revealed only at the tail of
`background-recon.md` or `existing-work-recon.md`.

## Goals

1. Prevent models from reading clean-start recon, retained-state recon, and
   alignment/planning at the same time.
2. Keep `do-homework.md` as the only stable user-facing entrypoint.
3. Make clean starts and retained/repair starts differ only in their first
   recon stage.
4. Merge both first-stage paths into one shared alignment and planning stage.
5. Keep the already-debugged source preservation and retained-artifact
   boundaries intact.
6. Reduce tool/task naming ambiguity by naming files after user-visible stages,
   not implementation terms like "source intake" or "current state intake".

## Non-Goals

- Do not redesign `reference_collector`.
- Do not reintroduce metadata scout, content scout, source scout, or appendix
  scout chains.
- Do not change runtime artifact names such as `spec.md`, `review_a.json`,
  `recon_summary.md`, `alignment_brief.md`, `repair_plan.md`,
  `pipeline_design.md`, or `repair_pipeline_design.md`.
- Do not change `task-orchestrator.md` execution semantics.
- Do not loosen the rule that old process evidence is forbidden unless
  allowlisted by `prelaunch_startup_inventory.json`.
- Do not make alignment/planning responsible for Canvas source recon or existing
  work state recon.

## Current Problem

The current split names and router presentation still look parallel:

```text
assignment-source-intake.md
assignment-workflow-planner.md
current-state-intake.md
assignment-recon.md
```

Even though the intended flow is staged, `do-homework.md` lists multiple
downstream files near the top and names both main files as generic assignment
workflow pieces. A model can reasonably infer that it should read all related
files before acting. That defeats the split: the main agent spends context on
planning rules before source recon is complete, or reads retained-state rules
during a clean start.

The fix is to encode sequence in the file boundary:

- the router names only the first stage;
- the first-stage file names only the next stage at its tail;
- the next stage states what terminal artifacts it expects and refuses to run
  the previous stage's investigation.

For runtime task files, this is a progressive-disclosure contract, not merely a
renaming convention. A model starting from `do-homework.md` should see exactly
one next file for its route. It should not be able to learn the alignment file
path until after completing the first-stage recon file.

## Target Flow

### Clean Start

```text
do-homework.md
-> background-recon.md
   -> alignment-planning.md
      -> task-orchestrator.md only after user approval
```

`do-homework.md` routes clean starts only to `background-recon.md`. It must not
pre-announce `alignment-planning.md` anywhere in the runtime router.

`background-recon.md` runs clean-start Canvas/source/background reconnaissance,
preserves references, writes terminal recon artifacts, and only then ends with a
handoff such as:

```text
If this background recon completed successfully, continue by reading:
sub-skills/tasks/alignment-planning.md
```

### Retained Draft / Repair / Review / Continue

```text
do-homework.md
-> existing-work-recon.md
   -> alignment-planning.md
      -> task-orchestrator.md only after user approval
```

`do-homework.md` routes retained drafts, existing outputs, repair requests,
pipeline review, draft review, failed runs, and continue requests only to
`existing-work-recon.md`. It must not clean-start by default.

`existing-work-recon.md` reads the accepted startup inventory, explores only
current retained artifacts and allowlisted history, writes its terminal current
state artifacts, and only then ends with a handoff to `alignment-planning.md`.

## File Responsibilities

### `do-homework.md`

The router is intentionally thin.

Responsibilities:

- Verify Canvas CLI prerequisites when the route needs Canvas.
- Resolve exactly one assignment when needed.
- Determine `work_dir`, `recommended_action`, and `entry_preset`.
- Run or refresh preflight archive and `prelaunch_startup_inventory.json`.
- Route to exactly one first-stage task file.
- Stop describing the full downstream flow.
- Avoid naming `alignment-planning.md`, `task-orchestrator.md`, or any later
  stage file. The router may say "follow the routed file to completion for its
  handoff", but it must not provide the later file path.

Route table:

```text
clean_start / recommended_action: recon
  read sub-skills/tasks/background-recon.md

retained_artifact_start / review_or_execute / pipeline_ready
  read sub-skills/tasks/existing-work-recon.md

retained_artifact_start / review_or_submit / draft_ready
  read sub-skills/tasks/existing-work-recon.md

retained_artifact_start / continue / failed / interrupted / repair
  read sub-skills/tasks/existing-work-recon.md
```

The router may mention that first-stage files own their own handoff, but it
must not name `alignment-planning.md` or list it as an immediate or future read
target.

### `background-recon.md`

This is the clean-start "task background reconnaissance" stage. It replaces
`assignment-source-intake.md` as the routed clean-start task and absorbs the
production behavior from `assignment-recon.md`.

Responsibilities:

- Require an accepted `prelaunch_startup_inventory.json`.
- Fetch broad Canvas source snapshots: assignment, rubric, syllabus, modules,
  module items, relevant pages, assignment files, front page, and
  announcements.
- Treat syllabus and announcements as first-class sources.
- Dispatch `reference_collector` for every homework run.
- Preserve complete task-relevant original evidence under `references/`,
  including Canvas-native `source.json`, `source.txt`, and `ORIGIN.md`.
- Keep the three reference preservation levels: original file, extracted text,
  and link/annotation manifests when applicable.
- Keep `references/REFERENCE_INDEX.md` as the source evidence entrance.
- Write terminal clean-start artifacts:

```text
spec.md
investigation/rubric.md
investigation/review_a.json
investigation/recon_summary.md
investigation/explore_context.md
investigation/unreachable.txt       # when needed
problem.md                          # compatibility only, when generated
stage_reviews/child_dispatch_ledger.json
stage_reviews/process_concerns.jsonl # when needed
```

Boundaries:

- It does not run user alignment.
- It does not write `alignment_brief.md`, `pipeline_design.md`,
  `repair_plan.md`, or `repair_pipeline_design.md`.
- It does not create `reading_plan.compact.json`,
  `reading_plan.compact.approved.json`, `source_findings.compact.md`, or normal
  source-scout appendix files.
- It does not let child workers decide the final source judgment.

Handoff:

- The only downstream task named inside this file should be the tail handoff to
  `alignment-planning.md`.

### `existing-work-recon.md`

This is the retained/current work reconnaissance stage. It replaces
`current-state-intake.md` and moves it from `tools/` to `tasks/`.

Responsibilities:

- Require an accepted `prelaunch_startup_inventory.json`.
- Read only retained user-visible artifacts named in startup inventory.
- Read allowlisted history only when the startup inventory names exact files or
  directories and gives a reason.
- Explore current drafts, generated outputs, accepted feedback, failed stage
  state, package state, verification state, and repair requests.
- Record skipped scouts with concrete reasons.
- Consolidate the current state into terminal artifacts:

```text
investigation/explore_manifest.json
investigation/explore_context.md
investigation/repair_recon.md       # when useful
repair_request.md                   # when user feedback needs a stable file
stage_reviews/process_concerns.jsonl # when needed
```

Boundaries:

- It does not run clean-start Canvas/source recon.
- It does not write `spec.md`, final `review_a.json`,
  `alignment_brief.md`, `repair_plan.md`, `pipeline_design.md`, or
  `repair_pipeline_design.md`.
- It reports missing/stale source evidence as a blocker instead of silently
  rerunning clean-start source recon.

Handoff:

- The file ends by directing the agent to `alignment-planning.md` after current
  state recon is complete.

### `alignment-planning.md`

This is the shared second stage for both clean starts and retained/repair
starts.

Clean-start inputs:

```text
prelaunch_startup_inventory.json
references/REFERENCE_INDEX.md
references/
spec.md
investigation/rubric.md
investigation/review_a.json
investigation/recon_summary.md
investigation/explore_context.md
investigation/unreachable.txt       # when present
problem.md                          # when present
```

Retained/repair inputs:

```text
prelaunch_startup_inventory.json
investigation/explore_manifest.json
investigation/explore_context.md
investigation/repair_recon.md       # when present
repair_request.md                   # when present
accepted retained artifacts named by startup inventory
```

Responsibilities:

- Present a conclusion-first briefing to the user.
- Ask for user-owned decisions before planning.
- Run alignment/brainstorming with the user.
- Write `investigation/alignment_brief.md` for clean-start work.
- Write `repair_plan.md` for retained/repair/change work.
- Write `pipeline_design.md` or `repair_pipeline_design.md`.
- Stop at `Pipeline Review Status: awaiting_user_review`.
- Direct execution only to `task-orchestrator.md` after user approval.

Boundaries:

- It does not run `background-recon.md`.
- It does not run `existing-work-recon.md`.
- It reads terminal artifacts from the first stage and treats missing required
  artifacts as blockers.
- It may route back to the router only when the first-stage artifacts are
  missing, stale, or contradict the accepted startup inventory.

## Naming Rationale

Use stage names that communicate what the model should be doing now:

- `background-recon.md` instead of `assignment-source-intake.md`: the stage is
  broader than source copying; it determines the task background from Canvas,
  syllabus, rubric, announcements, and matched files.
- `existing-work-recon.md` instead of `current-state-intake.md`: the stage is
  specifically about understanding existing drafts, outputs, repair requests,
  and current workbench state.
- `alignment-planning.md` instead of `assignment-workflow-planner.md`: the stage
  starts with user alignment/brainstorming and ends by writing a plan. It is not
  a generic workflow file to preload.

`alignment-brainstorm.md` was considered, but `alignment-planning.md` better
captures the full responsibility: user alignment plus the terminal pipeline
design artifact.

## Compatibility and Documentation Updates

Implementation must update references in:

- `skill.md`
- `README*.md` when present
- `docs/runtime-agent-protocol.md`
- `docs/canvas-pilot-reference.md`
- `docs/skills-architecture-spec.md`
- `docs/progress/agent-progress.md`
- `sub-skills/tools/_index.md`
- tests that assert old file names or old route language
- existing superpowers specs/plans that would otherwise teach the old shape

The old 2026-06-15 split spec remains historical context. New runtime docs
should point to this staged routing design as the active refinement.

## Testing Requirements

Add or update policy tests that verify:

1. `do-homework.md` routes clean starts to `background-recon.md` only.
2. `do-homework.md` routes retained/repair/review/continue starts to
   `existing-work-recon.md` only.
3. `do-homework.md` does not contain `alignment-planning.md` or otherwise name
   the alignment stage file.
4. `background-recon.md` contains the production Canvas/source recon contract
   formerly exposed through `assignment-recon.md`.
5. `background-recon.md` ends with a tail handoff to `alignment-planning.md`.
6. `existing-work-recon.md` lives in `sub-skills/tasks/`, not
   `sub-skills/tools/`, and ends with a tail handoff to
   `alignment-planning.md`.
7. `alignment-planning.md` refuses to run first-stage recon and requires
   terminal first-stage artifacts.
8. The old forbidden artifacts remain forbidden in normal runs:
   `reading_plan.compact.json`, `reading_plan.compact.approved.json`,
   `source_findings.compact.md`, and source-scout appendix outputs.

After implementation, run the full test suite:

```bash
.venv/bin/python -m pytest tests -q
```

Then rerun a clean-start homework validation through the proposal/recon slice
and confirm the observed read chain is:

```text
do-homework.md
-> background-recon.md
-> alignment-planning.md
```

For a retained/repair validation, confirm the observed read chain is:

```text
do-homework.md
-> existing-work-recon.md
-> alignment-planning.md
```

## Open Implementation Notes

- Prefer `git mv` for renamed files so review shows continuity.
- If removing `assignment-recon.md` causes too much documentation churn, it may
  temporarily become a tiny compatibility redirect. It must not remain in the
  tool registry as a normal runtime entry.
- Preserve detailed wording from the existing files wherever it encodes
  previously validated behavior. The change is primarily boundary, naming, and
  read-order control.
