# Runtime Agent Protocol Design

> 2026-06-04 · Design spec for making AutoStudy's runtime handoffs
> Superpowers-inspired while remaining independent of Superpowers at runtime.

## Context

AutoStudy now has enough task complexity that "a skill file with a long
sequence of instructions" is no longer a stable execution model. The project
has homework reconnaissance, user clarification, dynamic pipeline design,
course material sync, course note generation, and planned stage-level
subagent execution with independent review.

The current documentation has two overlapping concerns:

1. Development documentation for the user and development agents maintaining
   AutoStudy itself.
2. Runtime documentation for the Claude Code Main Agent and its subagents while
   handling a real Canvas or study task.

These concerns must be separated. Runtime agents should not treat roadmap,
progress logs, feature lists, historical specs, or trace audits as task
instructions.

## Design References

### Superpowers

Superpowers is the workflow reference, not a runtime dependency.

AutoStudy borrows these practices:

- brainstorm before execution;
- write a stable spec before writing a plan;
- write a plan before dispatching implementation work;
- keep the Main Agent as coordinator;
- give subagents curated context instead of global history;
- review spec compliance before quality;
- require evidence before completion claims.

AutoStudy must not require users to install or invoke Superpowers for Canvas or
study tasks.

### Canvas Copilot

Canvas Copilot remains the Canvas workflow reference:

- atomic Canvas source reads;
- source-by-source assignment reconnaissance;
- workbench files;
- verification logs;
- cautious submission and automation boundaries.

### AutoPku

AutoPku remains the skill architecture reference for fixed learning pipelines
such as course note generation.

## Goals

1. Define the runtime reality clearly: AutoStudy runs inside Claude Code; only
   the Main Agent talks to the user; subagents are temporary workers dispatched
   by the Main Agent.
2. Define Development Plane vs Runtime Plane so runtime agents do not use
   development docs as task instructions.
3. Promote `docs/runtime-agent-protocol.md` to the canonical runtime handoff
   baseline.
4. Upgrade `do-homework.md` into a Main Agent coordinator contract.
5. Upgrade `task-orchestrator.md` into a stage brief generation and subagent
   review loop contract.
6. Upgrade `pipeline_design.md` from "stage list" into a task-level plan that
   generates precise stage briefs.
7. Define stage-level handoff files:
   `stage_briefs/`, `stage_results/`, and `stage_reviews/`.
8. Define executor, spec reviewer, and quality reviewer subagent contracts.
9. Keep existing M3/M3.5 verified flows valid while introducing the new
   handoff protocol incrementally.

## Non-Goals

- Do not implement a standalone multi-agent framework.
- Do not require Superpowers at runtime.
- Do not change `canvascli` API behavior.
- Do not remove historical docs in this implementation pass.
- Do not force `sync-course` and `write-course-notes` into the full
  stage-brief protocol until the homework flow is stable.
- Do not implement real subagent dispatch code outside Claude Code's native
  subagent mechanism.

## Runtime Architecture

### Actor Classes

AutoStudy runtime has two actor classes.

| Actor | Description |
|---|---|
| Main Agent | The current Claude Code session. It routes requests, coordinates work, asks the user questions, writes plans, dispatches subagents, and performs final handoff. |
| Subagent | A temporary worker dispatched by the Main Agent. It receives a precise prompt and brief, reads only allowed files, writes declared outputs, and reports back to the Main Agent. |

Subagents do not talk to the user and do not dispatch other subagents.

### Main Agent Phases

| Phase | Source of instructions | Main outputs |
|---|---|---|
| Entry routing | `skill.md` | selected task skill |
| Task coordination | `sub-skills/tasks/<task>.md` | workbench lifecycle decisions |
| Reconnaissance | `canvascli-api.md`, `assignment-recon.md` | `spec.md`, `rubric.md`, `references/`, `review_a.json` |
| Clarification | task skill + `spec.md` | `user_notes.md`, `user_scope.md` |
| Planning | `tools/_index.md`, tool contracts, workbench facts | `pipeline_design.md` |
| Stage coordination | `pipeline_design.md` | `stage_briefs/*.md` |
| Execution and review | stage briefs and reviewer contracts | `draft/*`, `stage_results/*.json`, `stage_reviews/*.json` |
| Final verification | stage receipts and artifacts | `verification.log`, `result.json` |

## Runtime File Contracts

### Workbench Shape

Homework workbenches should converge on:

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
│   ├── user_notes.md
│   └── user_scope.md
├── pipeline_design.md
├── stage_briefs/
├── stage_results/
├── stage_reviews/
├── draft/
├── verification_checklist.md
├── verification.log
└── result.json
```

`problem.md` remains compatibility-only. `spec.md` is the factual task source of
truth.

### `pipeline_design.md`

`pipeline_design.md` is a task-level plan for the Main Agent. It is not the
direct prompt for an executor subagent.

Required sections:

```markdown
# Pipeline: <course> <assignment>

## Metadata
- repo_root: <absolute repo root>
- work_dir: <absolute workbench path>
- course_id: <canvas course id>
- assignment_id: <canvas assignment id>

## Output
- mode: <doc_prose | pdf_typed | code | slides | mixed | ...>
- deliverables:
  - path: draft/<file>
    type: <artifact type>

## Constraints
- source: <spec/rubric/user_notes>
  requirement: <concrete requirement>
  verification: <how to verify>

## Stages

### Stage 1 - <name>
- id: stage_01_<slug>
- tool: <top-level tool skill>
- delegate: main-agent | subagent
- review:
  - spec_compliance: true | false
  - quality: true | false
- max_retries: <integer>
- reads:
  - <path>
- writes:
  - <path>
- quality_criteria:
  - <measurable criterion>
- human_blockers:
  - <blocker surfaced to user if unresolved>

## Final Verification
- <measured check>
```

### `stage_brief.md`

`stage_brief.md` is the curated context pack for one subagent task.

Required sections:

```markdown
# Stage Brief: <stage id> - <stage name>

## Role
executor | spec_reviewer | quality_reviewer

## Task
<one-stage objective>

## Required Reads
- <path>: <why required>

## Allowed Reads
- <path or directory>: <allowed scope>

## Forbidden Reads
- AGENTS.md
- docs/ROADMAP.md
- docs/COLLABORATION.md
- docs/progress/agent-progress.md
- docs/plans/feature-list.json
- docs/superpowers/
- unrelated workbench files

## Writes
- <exact path>: <expected content>

## Tool Guidance
- <tool skill path>
- <appendix path, if selected by Main Agent>

## Quality Criteria
- <measurable criterion>

## Review Criteria
- <spec compliance criterion>
- <artifact quality criterion>

## Context From Previous Stages
<short summaries and output paths>

## Blockers And Escalation
Return NEEDS_CONTEXT or BLOCKED when <specific condition>.
```

### `stage_result.json`

Executor receipt:

```json
{
  "stage": "stage_01_notebook",
  "status": "DONE",
  "summary": "Notebook created and executed.",
  "outputs": [
    {"path": "draft/project.ipynb", "size_bytes": 12345}
  ],
  "commands_run": [
    "python -m nbconvert --execute draft/project.ipynb --to notebook --inplace"
  ],
  "verification_evidence": [
    "25/25 cells executed",
    "0 execution errors"
  ],
  "concerns": []
}
```

Allowed statuses:

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

### `stage_review.json`

Reviewer receipt:

```json
{
  "stage": "stage_01_notebook",
  "review_type": "spec_compliance",
  "verdict": "PASS",
  "evidence": ["All required deliverables are present."],
  "issues": [],
  "fix_suggestions": []
}
```

Allowed verdicts:

- `PASS`
- `FAIL`

Review types:

- `spec_compliance`
- `quality`
- `final`

## Review Model

Review happens in order:

1. Spec compliance review: did the artifact satisfy the assignment, rubric,
   stage brief, and user notes?
2. Quality review: is the artifact well built for its type?

Quality review should not run until spec compliance passes. Polishing the wrong
artifact is wasted work.

If a review fails:

1. Main Agent records reviewer evidence.
2. Main Agent writes or updates a fix brief.
3. Main Agent redispatches the executor if retries remain.
4. Main Agent records a human review item if retries are exhausted or a blocker
   needs user input.

## Required Documentation Updates

This design requires updates to:

| File | Required change |
|---|---|
| `docs/runtime-agent-protocol.md` | Keep as canonical runtime handoff protocol. |
| `docs/skills-architecture-spec.md` | Update pipeline format and review model to point to this protocol. |
| `sub-skills/tasks/do-homework.md` | Reframe as Main Agent coordinator contract and add stage directories to workbench. |
| `sub-skills/tasks/task-orchestrator.md` | Reframe as stage brief generation, subagent dispatch, review loop, and final verification contract. |
| `sub-skills/tools/_index.md` | Clarify that tool contracts may be referenced from stage briefs. |
| `docs/ROADMAP.md` | Mark this as the current M3.5 execution architecture direction and remove stale status contradictions. |
| `docs/progress/agent-progress.md` | Record the spec and implementation plan. |
| `docs/plans/feature-list.json` | Add evidence to `M3.5-EXECUTION-ARCHITECTURE`. |

## Acceptance Criteria

The implementation is accepted when:

1. Development Plane and Runtime Plane are explicitly separated in docs.
2. Runtime docs state that Superpowers is design reference only.
3. `do-homework.md` tells the Main Agent to create `stage_briefs/`,
   `stage_results/`, and `stage_reviews/`.
4. `pipeline_design.md` format includes enough metadata to generate stage
   briefs.
5. `task-orchestrator.md` describes the Main Agent's stage brief generation and
   executor/reviewer loop.
6. Stage executor, spec reviewer, and quality reviewer contracts are present in
   runtime docs.
7. The review order is explicitly spec compliance before quality.
8. Verification rules require measured evidence before `result.json` can mark
   `draft_ready`.
9. `docs/plans/feature-list.json` remains valid JSON.
10. `git diff --check` passes.

## Rollout Strategy

Roll out in documentation-first phases:

1. Establish the canonical runtime protocol and spec.
2. Align architecture docs (`skills-architecture-spec.md`, `ROADMAP.md`).
3. Align runtime task docs (`do-homework.md`, `task-orchestrator.md`).
4. Add sample stage brief/result/review schemas.
5. Validate docs with static checks and targeted grep checks.
6. Use the updated docs as the basis for later real DSAA2011/UCUG1505 runtime
   validation.

## Self-Review

- Placeholder scan: no unfinished placeholder markers.
- Scope check: this spec covers documentation and protocol alignment only; real
  runtime validation is a later implementation task.
- Internal consistency: Main Agent remains the only user-facing coordinator;
  subagents receive curated stage briefs and report back only to Main Agent.
