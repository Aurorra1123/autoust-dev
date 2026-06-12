# Stage Review Rollout Design

> 2026-06-04 · Implementation design for M3.5 Execution Architecture.
> Decision: use protocol + reviewer contracts together; validate on DSAA2011
> first, then UCUG1505. No submit in this rollout.

## Context

AutoStudy already has three related design documents:

- `docs/superpowers/specs/2026-06-04-execution-architecture-design.md`
  explains why the single-agent execution model should move to coordinator,
  executor, and reviewer roles.
- `docs/runtime-agent-protocol.md` defines the canonical runtime handoff model:
  Claude Code Main Agent coordinates; subagents consume stage briefs.
- `docs/superpowers/specs/2026-06-04-runtime-agent-protocol-design.md`
  explains how Superpowers-inspired discipline maps into AutoStudy without
  making Superpowers a runtime dependency.

The remaining work is not a new architecture. It is a focused rollout that
makes the runtime task skills actually speak the protocol: `do-homework.md`
must behave as the Main Agent coordinator contract, and `task-orchestrator.md`
must generate stage briefs, dispatch executor/reviewer subagents, record JSON
receipts, and gate final readiness on evidence.

## Goal

Move `M3.5-EXECUTION-ARCHITECTURE` from design-only to testable runtime
behavior by upgrading the homework execution docs and contracts.

The rollout should produce:

- a stage-aware homework workbench with `stage_briefs/`, `stage_results/`, and
  `stage_reviews/`;
- a `pipeline_design.md` format that includes delegation, review, retry, and
  measurable quality fields;
- executor stage briefs that are narrow enough for one subagent;
- reviewer briefs/contracts for spec compliance and artifact quality;
- a review loop where quality review runs only after spec compliance passes;
- final verification evidence before `result.json` can report `draft_ready`.

## Non-Goals

- Do not build a standalone multi-agent framework.
- Do not change `canvascli` API behavior.
- Do not implement auto-submit or test Canvas submission in this rollout.
- Do not force `sync-course` or `write-course-notes` into the full stage brief
  protocol.
- Do not delete or rewrite historical development docs.

## Selected Approach

Use "protocol + reviewer contracts" as the first implementation slice.

Compared with a minimal protocol-only pass, this adds explicit reviewer
contracts so the DSAA2011 and UCUG1505 validation can test the thing that
matters: whether independent review catches wrong or low-quality artifacts
before the Main Agent claims the draft is ready.

Compared with a full two-task implementation matrix in one step, this keeps the
first development pass smaller. DSAA2011 is the first acceptance task. UCUG1505
is the second acceptance task after DSAA2011 produces complete stage receipts.

## Runtime Roles

### Main Agent

The current Claude Code session. It is the only runtime actor that talks to the
user. It owns:

- routing through `skill.md`;
- homework lifecycle through `do-homework.md`;
- reconnaissance summary and user supplement capture;
- `pipeline_design.md`;
- stage brief generation;
- subagent dispatch;
- retry and human-blocker decisions;
- final user handoff.

The Main Agent may execute trivial `delegate: main-agent` stages inline, but it
still writes a `stage_results/<stage_id>_result.json` receipt.

### Executor Subagent

One temporary worker for one stage. It receives a prompt that points to a
single stage brief. It may read only files listed in the brief, write only
declared outputs, and must write a stage result JSON receipt.

Allowed statuses:

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

### Spec Compliance Reviewer

Independent reviewer that checks whether a stage artifact satisfies the
assignment, rubric, user notes, and stage brief. It must not trust the executor
receipt. It reads the artifact and writes:

```text
stage_reviews/<stage_id>_spec_review.json
```

Verdict is `PASS` or `FAIL`.

### Quality Reviewer

Independent reviewer that checks artifact quality only after spec compliance
passes. It writes:

```text
stage_reviews/<stage_id>_quality_review.json
```

Quality review is skipped when `pipeline_design.md` sets
`review.quality: false`, and the skip reason must be recorded.

## Runtime File Contracts

Homework workbenches should contain:

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

`spec.md` is the factual source of truth. `problem.md` is compatibility only.

## `pipeline_design.md` Requirements

The pipeline is the Main Agent's task-level plan. It is not the executor
subagent's direct prompt.

Each stage must include:

- `id`: stable id such as `stage_01_notebook`;
- `tool`: top-level tool skill path or name;
- `delegate`: `main-agent` or `subagent`;
- `reads`: exact files or directories;
- `writes`: exact output paths;
- `review.spec_compliance`: boolean;
- `review.quality`: boolean;
- `max_retries`: integer;
- `quality_criteria`: measurable checks;
- `human_blockers`: information that requires user input if unresolved.

Optional fields:

- `lang` for code stages;
- `type` for prose or artifact type;
- `post-process` such as `humanize`;
- `fallback` for renderer/tool fallback paths;
- `min_quality` for quick measurable gates.

## Stage Brief Requirements

For every stage, the Main Agent writes:

```text
stage_briefs/<stage_id>_executor.md
```

Executor briefs must include:

- role: `executor`;
- one-stage task;
- required reads with reasons;
- allowed reads;
- forbidden reads;
- declared writes;
- selected tool guidance paths;
- measurable quality criteria;
- review criteria;
- context from previous stages;
- blockers and escalation rules.

For reviewed stages, the Main Agent also writes reviewer briefs:

```text
stage_briefs/<stage_id>_spec_review.md
stage_briefs/<stage_id>_quality_review.md
```

Reviewer briefs must forbid mutation and must require reading the actual
artifact, not only the executor receipt.

## Review Loop

For each stage:

1. Generate executor brief.
2. Run executor subagent or inline execution.
3. Require `stage_results/<stage_id>_result.json`.
4. If spec review is enabled, run spec compliance review.
5. If spec review fails and retries remain, write a fix brief and rerun the
   executor.
6. Run quality review only after spec compliance passes.
7. If retries are exhausted, record a human review item and prevent
   `draft_ready` unless the pipeline explicitly permits partial output.

The invariant is:

```text
Spec compliance first. Quality review second.
```

## Validation Plan

### Acceptance 1: DSAA2011 First

Use DSAA2011 Machine Learning Project as the first real task because it stresses
mixed deliverables and cross-stage dependencies: notebook/code, generated
metrics, report/PDF, and possibly packaging or slides.

Passing evidence:

- `pipeline_design.md` contains stage ids, delegation, review flags, retries,
  quality criteria, and human blockers;
- every delegated stage has an executor brief and result JSON;
- every reviewed stage has a spec review JSON;
- quality review does not run before spec compliance passes;
- final verification log contains measured PASS/FAIL/SKIP lines;
- `result.json` is not `draft_ready` while blocking review failures remain.

### Acceptance 2: UCUG1505 Second

Use UCUG1505 Creative Coding Final Project after DSAA2011 passes. It stresses
open-ended assignment interpretation and false-pass resistance.

Passing evidence:

- spec review checks the actual creative project requirements, not generic code
  quality;
- quality review checks browser/runtime plausibility when possible;
- unresolved manual requirements, such as video recording, are surfaced as
  human blockers instead of hidden.

## Documentation Updates

Implementation should update:

- `docs/runtime-agent-protocol.md` with final schema details if missing;
- `sub-skills/tasks/do-homework.md` as the Main Agent coordinator contract;
- `sub-skills/tasks/task-orchestrator.md` as the stage coordinator and review
  loop contract;
- `docs/skills-architecture-spec.md` with stage metadata fields;
- `docs/examples/runtime/` with brief/result/review examples;
- `docs/plans/feature-list.json` evidence for M3.5 execution architecture;
- `docs/progress/agent-progress.md` handoff notes.

## Risks

### Risk: brief bloat

Mitigation: stage briefs reference required files and summarize prior context
instead of pasting large artifacts.

### Risk: reviewer rubber-stamping

Mitigation: reviewer contracts require artifact reads, evidence arrays, and
explicit missing requirements.

### Risk: runtime docs reading development history

Mitigation: every stage brief includes forbidden reads for `AGENTS.md`,
roadmaps, progress logs, feature lists, and `docs/superpowers/`.

### Risk: first test is too large

Mitigation: DSAA2011 is first because it is known and richly documented, but
the first rollout stops at draft/revision evidence and does not submit.

## Acceptance Criteria

- Static docs align on Main Agent, executor, spec reviewer, and quality reviewer
  terminology.
- `do-homework.md` and `task-orchestrator.md` both mention the stage
  directories and review order.
- Example JSON files parse with `python3 -m json.tool`.
- `git diff --check` passes.
- DSAA2011 validation can be started with no further architecture design work.
- UCUG1505 validation is documented as the second real-task test.
