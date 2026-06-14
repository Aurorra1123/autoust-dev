---
name: task-orchestrator
description: Execute an approved per-assignment pipeline from a workbench containing spec.md, explore_context.md, a terminal agreement, and a user-approved execution plan. Use after do-homework has produced and the user has approved pipeline_design.md.
---

# task-orchestrator

The core M3.5 execution coordination mechanism. This task is written for the
Claude Code Main Agent. It runs only after `do-homework.md` has produced a
pipeline and the user has approved it. It reads the current execution plan,
creates bounded stage briefs, dispatches executor and reviewer subagents when a
stage is delegated, executes simple `delegate: main-agent` stages inline only
when the approved plan explicitly permits that mode, and aggregates evidence for
final verification.

This task does **not** infer the assignment from raw Canvas fields and does
**not** consume `task_profile.yaml`. The source of truth is:

```text
work_dir/
├── canvas/
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── explore_context.md
│   ├── explore_manifest.json
│   ├── scout_results/    # optional receipts from pre-alignment explore scouts
│   ├── rubric.md
│   ├── unreachable.txt
│   ├── review_a.json
│   ├── alignment_brief.md
│   ├── user_notes.md      # optional
│   └── user_scope.md      # optional
├── pipeline_design.md
├── stage_briefs/
├── stage_results/
└── stage_reviews/
```

`spec.md` is the standardized Canvas/source exploration report.
`investigation/explore_context.md` is the shared exploration summary.
`references/` contains readable source materials; raw Canvas snapshots stay
under `canvas/`. For Canvas-native bodies such as assignment, syllabus, front
page, and pages, raw Canvas JSON is the canonical evidence. derived readable
artifacts are optional convenience copies, not required gates.
The terminal agreement is usually `investigation/alignment_brief.md` for an
initial assignment and may be `repair_plan.md` for a retained-artifact change.
The execution plan is usually `pipeline_design.md` and may be
`repair_pipeline_design.md` for compatibility. Older tools may still read
`problem.md`, but the orchestrator should always read `spec.md`, the explore
context, the terminal agreement, and the execution plan first.

## When To Invoke

Only after `do-homework` has:

1. Resolved `course_id` and `assignment_id`.
2. Built the workbench.
3. Completed the explore stage and wrote `investigation/explore_context.md`, or
   explicitly recorded that the task was tiny enough for inline exploration.
4. Completed the alignment loop and confirmed a terminal agreement with the
   user: `investigation/alignment_brief.md` for initial assignments or
   `repair_plan.md` for retained-artifact change requests.
5. Written or updated the current execution plan from that agreement:
   `pipeline_design.md` or compatibility `repair_pipeline_design.md`.
6. Presented the execution plan to the user and recorded
   `Pipeline Review Status.status: approved_for_orchestration` inside the
   current execution plan.

End users do not call this as the first step. They start with `do-homework`;
this task is the second step after pipeline review approval.

## Required Workbench

```text
work_dir/
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
├── repair_plan.md                 # retained-artifact compatibility, optional
├── repair_pipeline_design.md      # retained-artifact compatibility, optional
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

Before executing, check:

- `investigation/explore_context.md` exists for non-trivial runs, or the Main
  Agent explicitly recorded that the task was tiny enough for inline
  exploration. When present, read it before generating stage briefs.
- If `investigation/explore_manifest.json` names dispatched scout children,
  their scout receipt paths exist under `investigation/scout_results/` or the
  manifest-listed equivalent. The orchestrator does not rerun scouts, but later
  trajectory review depends on this evidence.
- `spec.md` exists and clearly states deliverables.
- A terminal agreement exists and was confirmed by the user:
  `investigation/alignment_brief.md` for initial assignments, or `repair_plan.md`
  for retained-artifact change requests. For open-ended work, it must contain
  `Selected Approach` and `Design Skeleton` or equivalent repair scope/design
  sections specific enough to drive stage goals, reads, writes, quality
  criteria, and final review items.
- The current execution plan exists and contains `# Pipeline`, `## Output`, and
  `## Stages` sections. Prefer `pipeline_design.md`; use
  `repair_pipeline_design.md` only when the current run intentionally wrote that
  compatibility filename.
- The current execution plan contains `## Pipeline Review Status` with
  `status: approved_for_orchestration`, non-empty `approved_at`, and non-empty
  `approved_by`. If status is `awaiting_user_review`, stop and ask the caller to
  return to the pipeline review gate instead of executing.
- Every stage's `delegate` value is treated as binding. The coordinator may not
  silently convert a `delegate: subagent` stage to inline main-agent execution.
  If subagent dispatch is unavailable, return a failed summary or require the
  pipeline to be revised and re-approved.
- `investigation/review_a.json` exists and has `verdict: "proceed"`, unless
  `do-homework` explicitly recorded user-supplied recovery material.
- `references/` contains required reachable materials, or
  `investigation/unreachable.txt` explains missing resources.
- If `investigation/review_a.json` says syllabus was available and checked,
  `spec.md`, `investigation/rubric.md`, `review_a.json`, or
  `source_findings.compact.md` cites raw `canvas/syllabus.json` section
  pointers.
- If `investigation/rubric.md`, `spec.md`, or `review_a.json` uses Canvas-native
  assignment/page/syllabus body details, later stage briefs must explicitly
  allow the relevant `canvas/*.json` reads; summary-only scout output must return
  to `do-homework` for recovery.
- If a stage depends on source details discovered by content scouts,
  required/allowed reads must include the source files, raw `canvas/*.json`
  paths, or exact `parent_source_read_requests` windows, not only `spec.md`,
  compatibility audit JSON, or scout receipts.

If these checks fail, return to `do-homework` with `status: failed`. Do not run
tools against an ungrounded assignment.

## Pipeline Design Format

`pipeline_design.md` follows the stage-based format defined in
`docs/skills-architecture-spec.md §5`. It must include
`## Pipeline Review Status` with `approved_for_orchestration` before this task
runs. Each stage declares `id`, `primary_tool`, `tools`, `tool_roles`,
`delegate`, `reads`, `writes`, `review.spec_compliance`, `review.quality`,
`max_retries`, `quality_criteria`, and `human_blockers`. Stages may also declare
`lang`, `type`, `post-process`, `fallback`, `min_quality`, and
`required_spec_constraints`. For legacy plans, `tool: <path>` is shorthand for
`primary_tool: <path>` plus `tools: [<path>]`; normalize it before generating
stage briefs.

The format is written by `do-homework [C]` — the orchestrator reads and executes it.
Do not redesign the format here.

## Execution Flow

### Step 1 - Read The Workbench

**Path discovery:** Before reading any skill files, determine the skill directory:

1. Choose the current execution plan: prefer `pipeline_design.md`; if the
   current run intentionally wrote `repair_pipeline_design.md`, use that.
2. Read the chosen execution plan and look for `repo_root:` in the metadata section.
3. If found, set `SKILLS_DIR = repo_root + "/sub-skills/tools/"`
4. If not found, infer: `REPO_ROOT = WORK_DIR/../../..` (3 levels up from data/homework/COURSE/HWID)
5. If inference fails, run: `git -C "$WORK_DIR" rev-parse --show-toplevel`
6. All skill file references use `SKILLS_DIR` as the base path

The `_index.md` is at `SKILLS_DIR/_index.md`.

Read, in order:

```text
spec.md
investigation/explore_context.md
investigation/explore_manifest.json
<EXECUTION_PLAN: pipeline_design.md or repair_pipeline_design.md>
investigation/rubric.md
investigation/review_a.json
<TERMINAL_AGREEMENT: investigation/alignment_brief.md or repair_plan.md>
investigation/user_notes.md      # if present
investigation/user_scope.md      # if present
problem.md                       # compatibility only
canvas/assignment.json           # if assignment shell details matter
canvas/syllabus.json             # if syllabus details matter
canvas/page-*.json               # if Canvas page bodies matter
SKILLS_DIR/_index.md          # path discovered above
```

Do not read `canvas/assignment.json.description` as the problem statement. It is
metadata only.

### Step 2 - Map Stages To Tools

Use the current execution plan's tool declarations plus
`sub-skills/tools/_index.md`. A stage has one `primary_tool` for ownership and
an ordered `tools` list for every top-level tool skill the executor must read and
apply. Do not drop supporting tools when generating briefs.

Common mappings:

| Stage kind | Common tool(s) |
|---|---|
| literature search / references | `paper-search.md` |
| prose / report / reflection | `writing-helper.md` |
| chart / figure | `figure-maker.md` |
| markdown or LaTeX to PDF | `pdf-renderer.md` |
| code / notebook / source files | `code-writer.md` |
| tests / execution report | `test-runner.md` |
| slides / deck | `slide-maker.md` |

Planning rule: split independent artifact boundaries into separate stages, but
combine multiple tools in one stage when one executor must produce one coherent
artifact or one stage receipt from multiple capabilities. Examples:

- code stage that must both write and run a notebook:
  `primary_tool: code-writer.md`, `tools: [code-writer.md, test-runner.md]`;
- report stage that must draft and humanize prose:
  `primary_tool: writing-helper.md`, `tools: [writing-helper.md, humanizer.md]`;
- figure-heavy report stage that must create figures before embedding them:
  include both `figure-maker.md` and `writing-helper.md`, unless figures are a
  separate artifact stage with its own receipt.

If any declared tool does not exist, stop and return:

```yaml
status: failed
failures:
  - tool: <missing tool>
    error: "tool not registered in sub-skills/tools/_index.md"
```

Do not fake an unsupported capability.

### Step 3 - Generate Stage Briefs

Before generating any stage brief, build a `hard_requirement_inventory` from
`spec.md` and authoritative references. Include explicit `must`, `required`,
`only`, `do not`, exact file/data/source/package/format/page/time/name
constraints, and rubric-critical conditions. Then diff it against
`required_spec_constraints` in the execution plan.
Use this exact gate: diff it against `required_spec_constraints`.
When a requirement came from a content scout, follow the scout pointer back to
the original source body before adding it to the inventory. scout summaries are
routing hints, not source evidence. Stage briefs must carry the same raw source
paths or exact source windows forward.

If a hard requirement appears in `hard_requirement_inventory` but is absent or
weakened in `required_spec_constraints`, stop and record `FAIL | spec
requirement drift`. Do not generate executor briefs from a pipeline that has
already downgraded the spec.

For each stage in the current execution plan, write:

```text
stage_briefs/<stage_id>_executor.md
```

For stages with review enabled, also write:

```text
stage_briefs/<stage_id>_spec_review.md
stage_briefs/<stage_id>_quality_review.md
```

Each executor brief must include:

- role: `executor`;
- concrete one-stage task;
- required reads;
- allowed reads;
- required/allowed reads must include the source files or raw `canvas/*.json` paths for constraints that came from source-body audit or content scouts;
- forbidden reads;
- forbidden writes, including `stage_reviews/child_dispatch_ledger.json`,
  other stages' receipts, trajectory audit files, and archive evidence unless
  explicitly declared;
- declared writes;
- selected tool skill paths, including `primary_tool`, every item in `tools`,
  and each `tool_roles` entry;
- relevant user intent, confirmed decisions, delegated decisions, and
  non-negotiables from the terminal agreement;
- applicable `required_spec_constraints`, including source, requirement,
  applies_to, required_evidence, status, blocker type when blocked, and
  `fallback_allowed_for_final`;
  Required fields: source, requirement, applies_to, required_evidence, status.
- applicable tool contracts copied from every selected top-level tool skill, not
  merely the filenames. Include `allowed_renderer_paths`, the selected
  `renderer_path` when known, required source artifacts, required verification
  evidence, and fallback limits.
- measurable quality criteria;
- review criteria;
- context from previous stages;
- blockers and escalation rules.
- scope hygiene: the worker is a subagent with curated runtime context. Use a
  blacklist-first read model: required/allowed reads are the expected starting
  evidence, and the worker may inspect additional current-run artifacts only
  when they are directly relevant to the assigned stage or reviewed deliverable.
  It must not read external workflow/plugin skill files, development-plane docs,
  progress logs, validation plans, archived prior runs, prior diagnostics, or
  unrelated workbench evidence. If the host platform injects startup
  instructions unrelated to the assigned stage, obey only the minimal stop/skip
  behavior required by that platform and continue from the assigned brief; do
  not use external workflow instructions as task context.
- active-only command discipline: when searching or listing the workbench, avoid
  broad absolute-path commands that can include `archive/` despite an intended
  exclusion. Prefer `cd <workbench> && rg ... . --glob '!archive/**'` or
  `find <workbench> -path '<workbench>/archive' -prune -o ...`. If archive path
  names are printed, record a process concern and rerun with an explicit prune;
  if archive file contents are printed into the runtime transcript, clean
  process `PASS` is blocked.
- receipt identity: write the exact runtime `agent_id` only if known. If the id
  is not known, write `agent_id: null`, `agent_id_source:
  "unknown_to_child_at_write_time"`, and `identity_authority:
  "stage_reviews/child_dispatch_ledger.json"`. Do not invent alias ids such as
  `C4`, `executor-1`, or `current child`.
- receipt schema: include a copy-paste JSON skeleton in the brief for the
  exact receipt type. Executor briefs must show `created_at_utc`,
  `completed_at_utc`, `executed_by`, `delegation_mode`,
  `delegation_deviation`, identity fields, `transcript_export_path`, status,
  outputs, and issue classification. Reviewer briefs must additionally show
  `review_type`, `depends_on_stage_result`, `depends_on_spec_review`, verdict,
  and a structured `issue_classification` object. Do not rely on prose such as
  "write appropriate metadata"; missing dependency fields are schema drift.

Tool Contract Preservation Gate:

- A stage brief that names one or more tool skills must preserve every named
  tool's non-negotiable output contract. The orchestrator may specialize the
  contracts for the current assignment, but it must not drop required source
  artifacts, renderer choices, validation commands, or fallback limits.
- For slides, copy the slide-maker renderer contract into the brief:
  `allowed_renderer_paths: [guizang, beamer]`, the selected `renderer_path` if
  chosen by the plan, required `render_command_or_script`, source artifact
  expectations (`guizang/index.html` or `slides.tex`), and font/glyph
  verification evidence. do not invent a new final renderer after dispatch. A
  PyMuPDF repair or preview fallback must be explicitly labeled and cannot be
  accepted as the final slides deliverable unless it satisfies the chosen tool
  contract and records the render script, font strategy, `pdffonts`, and
  `pdftotext` replacement-glyph evidence.
- Executor receipts for rendered artifacts must report the selected
  `renderer_path`, the exact `render_command_or_script`, any fallback reason, and
  whether the fallback is final, preview, debug, or superseded. A vague receipt
  such as "professional local fallback" is insufficient evidence for
  `draft_ready`.

Do not dispatch a subagent until its stage brief exists.

### Step 4 - Dispatch Executor Subagent Or Run Inline

If `delegate: subagent`, dispatch one executor subagent with only the executor
stage brief path and a short prompt pointing to it. The executor reports
`DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED` and writes:

```text
stage_results/<stage_id>_result.json
```

If `delegate: main-agent`, the Main Agent executes the simple stage inline but
still writes:

```text
stage_results/<stage_id>_result.json
```

Each stage result JSON must include:

- `stage`: the exact stage id from the current execution plan;
- `created_at_utc`: ISO-8601 timestamp when the child started writing the
  receipt;
- `completed_at_utc`: ISO-8601 timestamp when the receipt was finalized;
- `executed_by`: `subagent` or `main-agent`;
- `delegation_mode`: `subagent`, `main-agent`, or `inline_fallback`;
- `delegation_deviation`: `null` when execution followed the declared
  delegation mode, otherwise a concise reason.
- `agent_id` or `transcript`: required when `delegation_mode: "subagent"` so a
  trajectory reviewer can verify the child executor identity.
- `agent_id_source` and `identity_authority`: required when `agent_id` is
  `null` because the child does not know its runtime id. Alias ids are invalid.
- `transcript_export_path`: recommended when the runtime can export the full
  child transcript; if unavailable, preserve the best available transcript
  handle and record the limitation in the coordinator summary.

The coordinator is the identity and ledger authority. After dispatching a child
subagent, record the returned child agent id and expected transcript handle in
`stage_reviews/child_dispatch_ledger.json` before waiting for the receipt. The
ledger entry must include `dispatch_index`, `stage_id`, `role`, `agent_id`,
`input_brief_path`, `expected_output_receipt_path`, `dispatched_at_utc`,
`recorded_before_wait: true`, `status: "dispatched"`, and
`transcript_export_status`. If `send_input` or an equivalent messaging tool is
available after `spawn_agent`, immediately send the returned child id to the
child as an identity-injection message and record `identity_injected_at_utc` in
the ledger. If the child still cannot observe the injected id before writing
its receipt, the explicit `agent_id: null` plus ledger-authority pattern is
acceptable; invented aliases are not.

If a spawn attempt fails before returning a child id, record it in the ledger
metadata `process_events` array rather than silently relying on transcript
memory. Use `event_type: "spawn_attempt_failed_no_agent_id"` with `stage_id`,
`role`, `attempted_at_utc`, `tool_error`, `recovery_action`, and
`replacement_dispatch_index` once known.

Child subagents must not write this ledger. When the receipt arrives, normalize
it before counting the stage complete:

- if `stage` is missing or differs from the pipeline stage id, re-prompt the
  child or write a superseded malformed-receipt record;
- if `agent_id` is `null` with `agent_id_source:
  "unknown_to_child_at_write_time"` and `identity_authority:
  "stage_reviews/child_dispatch_ledger.json"`, add
  `coordinator_authoritative_agent_id` or normalize the receipt to the dispatch
  id before final verification;
- if `agent_id` is missing without the null-plus-authority fields, add the
  authoritative id only as recovery and record a process concern;
- if `agent_id` is an alias such as `C4`, `stage-reviewer`, or `current child`,
  preserve it as `original_agent_id_field`, normalize to the dispatch id, and
  record schema drift; repeated alias ids should trigger prompt/template
  tightening before the next run;
- if `agent_id` conflicts with the dispatch id, do not accept the receipt as
  completion. Reconcile the mismatch, dispatch a replacement child, or mark the
  stage `BLOCKED`;
- if only a transcript handle is available, keep it in both the receipt and the
  coordinator summary and record that full transcript export was unavailable.
- once the receipt file exists and parses, write `receipt_observed_at_utc` to
  the ledger entry. Once identity, status/verdict, and required outputs are
  accepted for counting, write `accepted_at_utc`. Do not use `completed_at_utc`
  or `wait_status` as a substitute for these fields.

Normalization is a fallback, not a target state. Stage briefs should instruct
children to emit `stage`, timestamps, role/status or verdict,
`issue_classification`, `transcript`, `transcript_export_path`, and either the
exact `agent_id` or the explicit null-plus-authority identity fields directly
in their receipt. If many receipts need coordinator normalization, record a
process concern in the coordinator summary so the next prompt/template can be
tightened.

If waiting for a child returns `not_found`, stream disconnect, timeout after
dispatch, or another transport-layer failure, do not accept the child from the
final message alone. First check that the expected receipt exists and parses,
the child transcript or local session JSONL exists, the transcript contains the
assignment prompt, and the receipt/transcript evidence supports the claimed
final status. Only then may the ledger status become
`accepted_with_transport_recovery`, with `transport_error`,
`recovery_evidence`, `receipt_observed_at_utc`, and `accepted_at_utc` recorded.
If those checks fail, re-prompt, dispatch a replacement child, or mark the
stage `BLOCKED`.

If a read/export-thread tool is available to the coordinator, export the child
transcript before closing that child and write it under:

```text
transcripts/<stage_id>_<role>_<agent_id>.json
```

Then set `transcript_export_path` in the accepted receipt and dispatch ledger.
Do not rely on a later main-thread reviewer to recover nested child transcripts:
grandchild thread ids may not be visible outside the coordinator that spawned
them.

If child-thread limits or open-descendant limits occur, close completed child
agents only after the ledger records their stable ids, receipt paths, final
statuses, and transcript export status. Do not close a child before preserving
the identity evidence needed for later audit.

For development validation runs, also preserve the coordinator's own stable
agent/thread id. If the parent can only know that id after dispatch, the parent
must send it to the coordinator before final evidence is written. Record it in
the coordinator summary and dispatch ledger; a generic role label such as
`main-thread-runtime-coordinator` is not enough by itself.

Do not treat a child subagent response such as `Standing by`, an empty final
message, or a message that lacks the required receipt as completion. Re-send the
brief, dispatch a replacement child and record the superseded attempt, or mark
the stage `BLOCKED`. Standby/empty responses are anomalies, not passing
executor evidence.

### Step 5 - Review In Order

For stages with review enabled:

1. Dispatch spec compliance reviewer first.
2. Write `stage_reviews/<stage_id>_spec_review.json`.
3. If verdict is `FAIL`, or if the reviewer finds a blocking `auto_fixable`
   concern, apply reviewer suggestions through a fix brief and rerun the
   executor while retries remain.
4. Dispatch quality reviewer only after spec compliance passes.
5. Write `stage_reviews/<stage_id>_quality_review.json`.

Never run quality review before spec compliance passes.
If spec compliance still fails after retries, do not run a normal quality
review. You may write `stage_reviews/<stage_id>_quality_review.json` with
`verdict: "SKIP"` and `skip_reason` to make the withheld quality review
auditable. A quality `SKIP` receipt does not unblock `draft_ready`.

Each review JSON must include:

- `stage`: the exact stage id from the current execution plan;
- `review_type`: `spec_compliance` or `quality`;
- `created_at_utc`: ISO-8601 timestamp when the reviewer started writing the
  receipt;
- `completed_at_utc`: ISO-8601 timestamp when the review receipt was finalized;
- `depends_on_stage_result`: the stage result receipt reviewed;
- `depends_on_spec_review`: `null` for spec compliance review, and the passing
  spec review JSON path for quality review.
- `agent_id` or `transcript`: required for normal reviewer subagent receipts;
  for `verdict: "SKIP"`, use `null` and include `skip_reason`.
- `agent_id_source` and `identity_authority`: required when a reviewer child
  does not know its exact runtime id. Alias ids are invalid and must be
  normalized as schema drift.
- `transcript_export_path`: recommended when the full reviewer transcript can be
  exported; otherwise keep the transcript handle and record the export
  limitation in the coordinator summary.
- `issue_classification`: object with `auto_fixable`, `needs_user_input`,
  `manual_only`, `external_blocker`, and `acceptable_risk` lists.
  When useful, add `blocking_auto_fixable` and `optional_polish` lists to avoid
  mixing repair-required issues with nonblocking polish suggestions.

Apply the same identity normalization to reviewer receipts before accepting a
review verdict. A reviewer receipt with a conflicting `agent_id` is not a
passing review, even if its verdict says `PASS`.

Classify every concern before final handoff:

- `auto_fixable`: the current agent can fix it with existing local context and
  allowed writes. Examples: rebuild a zip after a notebook rerun, add a missing
  report heading, regenerate a derived PDF/package from available files.
- `needs_user_input`: the user must provide missing facts, preferences, files,
  credentials, or decisions.
- `manual_only`: human or real-world validation is required, such as live
  presentation/Q&A quality.
- `external_blocker`: a required external resource is unavailable in the
  workbench, such as an official course style file.
- `acceptable_risk`: non-blocking concern that can be disclosed without
  preventing a draft-ready handoff.

Do not put blocking `auto_fixable` issues directly into `revision_needed`. Fix
them first, then rerun the relevant executor/reviewer loop. If the current stage
brief forbids the needed write, add a bounded repair stage or revise the
current execution plan before final handoff. Optional polish items must be marked
separately, or moved to `acceptable_risk` with `blocking: false`, so later
auditors do not confuse them with unrepaired blockers. Only `needs_user_input`,
`manual_only`, and `external_blocker` issues may remain as `revision_needed`
items after automatic repairs are exhausted.

Spec hard requirement no-downgrade gate:

- If the current execution plan declares `required_spec_constraints`, or if
  `spec.md` contains explicit `must`, `required`, `only`, `do not`, exact file,
  data, format, source, package, page/time, or rubric-critical requirements, the
  coordinator must treat those as blocking spec-compliance requirements.
- Verify the same requirement is preserved across
  `spec -> pipeline -> stage brief -> artifact -> verification`. Stage briefs
  may add implementation detail, but they must not weaken, omit, or reclassify a
  hard requirement as a fallback, acceptable risk, or optional human review item.
- If a hard requirement cannot be met with current evidence, classify the issue
  as `needs_user_input`, `manual_only`, or `external_blocker`; the coordinator
  must not mark `draft_ready`.
- A fallback output is only preview/debug when it does not satisfy the exact
  hard requirement. It may be generated for review, but it must not be named,
  packaged, or verified as the final deliverable governed by that requirement.

For conditional repair or verification stages whose trigger is false, write a
`stage_results/<stage_id>_result.json` receipt with `status: "SKIPPED"`,
`skip_reason`, and the evidence that made the trigger false. A skipped reviewed
stage should also write explicit review `SKIP` receipts when review files were
declared, so later audits do not have to infer skipped execution from
`verification.log` alone.

As with executor receipts, standby-only, empty, or receipt-less reviewer output
is not a review verdict. Re-prompt or replace the reviewer child, or stop with a
blocked review state; do not infer `PASS` from a silent or malformed response.

### Step 6 - Verify Deliverables

Before returning:

- Check every deliverable named in the current execution plan exists or is listed as a
  human/manual item.
- Check every stage has a `stage_results/<stage_id>_result.json`, including
  conditional stages skipped with `status: "SKIPPED"` and `skip_reason`.
- Check every reviewed stage has a passing spec compliance review.
- Check quality review is passing or explicitly skipped with reason.
- Check `verification.log` contains measured PASS/FAIL/SKIP lines.
- Check `result.json` is not marked `draft_ready` while blocking FAIL reviews
  remain.
- Check `result.json` is not marked `revision_needed` because of unresolved
  `auto_fixable` issues that the current agent could repair.
- Check hard spec requirements:
  - For each `required_spec_constraints` item, verify the artifact and
    verification evidence satisfy the exact source requirement.
  - If a hard requirement is missing from a stage brief, record
    `FAIL | spec requirement drift` and withhold `draft_ready`.
  - If a fallback artifact exists for a hard requirement, verify it is labeled as
    preview/debug only and excluded from final deliverable/package checks unless
    the authoritative spec explicitly permits that fallback.
  - Do not accept generic checks, such as file exists, magic bytes, page count,
    or image count, when the spec requires more specific evidence.
- Sanity checks by type:
  - `pdf`: file is >1 KB and magic bytes are `%PDF`.
  - report PDF with available generated figures: `pdfimages -list` or visual
    inspection confirms representative figures are embedded, or the absence is
    classified as an `auto_fixable` quality issue for a report/asset repair
    stage.
  - report PDF organization: if the report uses many figures, extracted text or
    visual inspection should confirm important figures have not floated into an
    unrelated later section; fixable float drift is a quality issue.
  - English report PDF labels: if the report is otherwise English, localized
    table-of-contents or figure labels should be fixed or classified as
    nonblocking professionalism risk with evidence.
  - slides PDF rendering: record `pdffonts` and `pdftotext` evidence, verify font embedding
    or an explicit font strategy, and scan extracted text for
    replacement-glyph symptoms such as Unicode replacement characters, tofu
    boxes, or unexpected line-leading question marks. If the source deck does not
    contain those literal characters but the PDF extraction does, classify it as
    an `auto_fixable` rendering issue and rerender before packaging.
  - `pptx`: file is a valid zip with `[Content_Types].xml`.
  - `html`: file is non-empty and has expected slide/page structure if a deck.
  - `ipynb`: valid JSON with notebook cells.
  - `zip`: valid zip archive.
  - `md` / `txt`: non-empty UTF-8.
  - code: parses or tests run when possible.

Write:

```text
verification_checklist.md
verification.log
```

`verification_checklist.md` contains checks grounded in `spec.md`,
`investigation/explore_context.md`, `investigation/rubric.md`, the terminal
agreement, and the current execution plan.

`verification.log` uses measured lines:

```text
PASS | <check> | measured: <value>
FAIL | <check> | measured: <value>
SKIP | <check> | reason: human_review
```

Use `FAIL` only for checks that failed and require repair, revision, user input,
or external resolution. When a check proves that `draft_ready` should not be set
because remaining items are manual, external, or intentionally skipped, record
that as `PASS | draft_ready withheld | measured: status=revision_needed` or as
an `INFO` line if the local verifier supports it. Do not write a misleading
`FAIL | draft_ready eligibility` line for the correct `revision_needed` state.

### Step 7 - Return Summary

Before returning, write `result.json` for the execution outcome:

- `draft_ready` only when every blocking spec compliance review passed, quality
  reviews passed or were explicitly skipped with nonblocking reasons, hard spec
  requirement no-downgrade gates passed, all required deliverables exist, and
  `verification.log` has no blocking `FAIL`.
- `revision_needed` when deliverables exist but remaining blockers are
  `needs_user_input`, `manual_only`, `external_blocker`, or explicitly accepted
  nonblocking risks.
- `error` when execution cannot produce a coherent draft or when required stage
  evidence is missing/malformed after retries.

Never submit to Canvas from this task. The caller may ask the user about
submission after reading the summary and `result.json`.

Return a structured summary to the caller:

```yaml
status: success | partial | failed
output_mode: mixed
deliverables_produced:
  - path: data/homework/<COURSE>/<HWID>/draft/<file>
    size_bytes: 245678
    format: pdf
intermediates:
  - data/homework/<COURSE>/<HWID>/draft/draft.md
tools_used:
  - writing-helper
  - pdf-renderer
verification_log_path: data/homework/<COURSE>/<HWID>/verification.log
human_review_items:
  - "Group ID needs to be filled in before submission"
failures: []
```

The caller shows this summary to the user and handles any later submission
confirmation outside `task-orchestrator.md`.

## Output Modes

Use Canvas Generic output vocabulary:

| Mode | Meaning |
|---|---|
| `doc_prose` | essay, report, critique, reflection, text submission |
| `pdf_annotated` | annotated reading PDF, highlights, answer blanks |
| `pdf_typed` | typed problem-set / math / formal solution PDF |
| `code` | source files, notebook, package, starter-code completion |
| `form_answers` | short answer body for online text entry |
| `slides` | presentation deck |
| `mixed` | multiple output shapes |

Generic examples:

- **Machine-learning course project**: `mixed` - notebook/code + report PDF + slides PDF +
  requirements + zip package.
- **Creative coding final project**: `mixed` - creative code + documentation + manual
  video demo.

## Safety Rules

1. **No tool runs without pipeline approval.** `pipeline_design.md` must contain
   `Pipeline Review Status.status: approved_for_orchestration` before any stage
   brief, executor, reviewer, or verification tool runs.
2. **Do not invent missing source material.** If `spec.md` or `references/` is
   incomplete, return to `do-homework`.
3. **Do not pass raw Canvas JSON as hidden background.** If assignment,
   syllabus, front-page, or page body details matter, list the relevant
   `canvas/*.json` files in the stage brief's allowed reads. stage briefs must explicitly allow relevant `canvas/*.json` reads. summary-only scout output is not enough.
4. **Do not use `assignment.description` as the prompt.**
5. **Do not silently alter deliverables.** The approved execution plan controls
   the target artifacts.
6. **No writes outside `work_dir`** except explicit renderer outputs already
   named in the current execution plan.
7. **No placeholder deliverables.** Ban `[PROBLEM N]`,
   `[TODO: align with actual project spec]`, and `[此处由小组成员填入选题]`.
8. **Surface `[CLARIFICATION NEEDED: ...]` markers** in the returned
   `human_review_items`.

## Pitfalls

1. **Don't make this a free-form classifier again.** Classification happens in
   assignment-recon Stage 5 and is finalized by `do-homework [C]`.
2. **Don't resurrect `task_profile.yaml`.** It was a transitional idea; the
   workbench plus current execution plan is the contract.
3. **Don't bake course-specific logic here.** Course quirks belong in `spec.md`,
   the execution plan, or future course overrides.
4. **File paths with Chinese / spaces are common.** Always quote paths in shell
   calls.

## MVP Scenarios Validated

The old fixed chains validated AutoStudy's tool base:

| type | Assignment | Tool chain | Deliverable |
|---|---|---|---|
| `paper` | DLED3020 Paper Critique | paper-search -> writing-helper -> pdf-renderer | `final.pdf` |
| `slides` | UCUG1077 Group presentation | slide-maker | `slides.pdf` |
| `math` | DSAA2043 Lab-Assignment 1 | writing-helper -> pdf-renderer | `solution.pdf` |
| `lab` | DSAA2012 Project Report | code-writer -> test-runner -> writing-helper -> pdf-renderer | `src/` + `report.pdf` |

The next development step is to validate the unified
`startup inventory -> explore_context -> terminal agreement -> execution plan -> draft/`
flow on representative mixed-output assignments without baking those validation
targets into runtime behavior.
