# Development Validation Standard

This document defines the standard workflow for development-stage runtime
validation iterations. It applies across validation assignments; DSAA2011,
UCUG1505, or any later task are targets of the same process, not special-case
workflows.

Use this standard before dispatching a runtime coordinator or validation
subagent.

## Iteration Modes

Before dispatching any runtime coordinator, the Main Agent must declare the
iteration mode:

- `full_flow`: simulate a real user asking AutoStudy to do the assignment from
  the beginning. The coordinator must perform reconnaissance, write `spec.md`,
  build or revise `pipeline_design.md`, generate draft artifacts, verify them,
  and write final receipts.
- `repair_flow`: simulate a user returning to an existing user-visible
  workbench or draft and asking for a change. The retained current artifacts are
  the object being repaired. The repair may be small or large: a one-file fix,
  a regenerated deliverable, a rerun experiment, a rewritten section, or a
  broader new version. The coordinator decides the repair scope dynamically in
  `repair_plan.md` and `repair_pipeline_design.md`.

If the user says "run the task again", "repeat the flow", or "simulate the real
user flow" without narrowing the scope, default to `full_flow`.

For `repair_flow`, the previous draft is not a forbidden leak when it is the
user-visible object being repaired and is explicitly retained in the startup
inventory. Hidden prior diagnostics, archived validation transcripts, old
trajectory reviews, old process receipts, and unstated conclusions remain
forbidden runtime context. A broad rewrite is still `repair_flow` when it is
based on the current user-visible draft; it is not a separate mode.

## Preflight Archive And No-Leak Cleanup

Before the coordinator is dispatched:

1. Archive the previous iteration's active workbench evidence under
   `archive/<iteration-id>/`.
2. Remove stale runtime evidence from the active workbench:
   `stage_briefs/`, `stage_results/`, `stage_reviews/`, `transcripts/`,
   `verification_checklist.md`, `verification.log`, `result.json`, prior
   `repair_plan.md`, prior `repair_pipeline_design.md`, coordinator identity
   sidecars, trajectory reviewer identity sidecars, and any coordinator or
   trajectory summary files.
3. For `full_flow`, also remove generated workbench content from the active
   launch directory: `canvas/`, `references/`, `investigation/`, `draft/`,
   `spec.md`, `problem.md`, and `pipeline_design.md`. These are outputs of the
   user-facing homework flow, not valid hidden startup context.
4. For `repair_flow`, keep only the files that the simulated
   user would actually have available and would intentionally ask the runtime to
   use. Record the retained file list before launch.
   For `repair_flow`, this normally includes the current draft artifacts,
   `spec.md`, `problem.md`, source references, and the concrete files needed to
   understand the current user-visible work. The exact list is task-dependent:
   a code task may retain source/tests, a report task may retain PDFs/notes, a
   notebook task may retain data/metrics, and a web/game task may retain local
   app assets. It normally excludes the old full-flow `pipeline_design.md`, old
   `stage_briefs/`, `stage_results/`, `stage_reviews/`, `transcripts/`,
   `verification.log`, prior `repair_plan.md`, prior
   `repair_pipeline_design.md`, `investigation/review_a.json` and similar
   review receipts, identity sidecars, and old trajectory verdicts from active
   startup context; those are archived first for rollback and audit. The repair
   coordinator must write a fresh `repair_plan.md` and
   `repair_pipeline_design.md` rather than editing or reusing a prior run's
   planning files in active root.
5. Do not hide user supplements in workbench files. If group id, dataset choice,
   partner names, instructor oral notes, or scope constraints are needed, pass
   them explicitly in the simulated user prompt or at the `[B]` checkpoint.
6. After cleanup, stop before coordinator dispatch and show the startup
   inventory to the human reviewer. Do not start the coordinator until the
   reviewer accepts the launch state.
7. After reviewer acceptance, write the accepted startup inventory into the
   active workbench before coordinator dispatch. Use
   `prelaunch_startup_inventory.json` for structured evidence, or
   `prelaunch_startup_inventory.txt` when preserving exact command output is
   more useful. The coordinator summary must link this artifact.

The startup inventory must include:

```bash
find data/homework/<COURSE>/<assignment> -maxdepth 2 -type f | sort
find data/homework/<COURSE>/<assignment> -maxdepth 2 -type d | sort
find data/homework/<COURSE>/<assignment>/archive/<iteration-id> -maxdepth 2 -type f | sort
```

Expected for `full_flow`: the active workbench contains no generated assignment
materials or previous verdicts except `archive/` and any deliberately empty
parent directory. The coordinator must discover or regenerate all runtime files
through the normal public skill/task surface.

The structured inventory should include:

```json
{
  "schema": "autostudy_prelaunch_startup_inventory_v1",
  "iteration_id": "<iteration-id>",
  "declared_mode": "full_flow",
  "workbench": "data/homework/<COURSE>/<assignment>",
  "human_review_accepted": true,
  "active_files_before_launch": [],
  "active_dirs_before_launch": [],
  "archive_evidence_path": "archive/<iteration-id>/",
  "retained_startup_files": [],
  "user_supplements_source": "simulated_user_prompt"
}
```

For `repair_flow`, the structured inventory should also include:

```json
{
  "declared_mode": "repair_flow",
  "rollback_archive_path": "archive/<iteration-id>/",
  "retained_startup_files": [
    "spec.md",
    "problem.md",
    "draft/project.ipynb",
    "draft/metrics.json",
    "draft/report.pdf"
  ],
  "removed_stale_evidence": [
    "stage_briefs/",
    "stage_results/",
    "stage_reviews/",
    "transcripts/",
    "repair_plan.md",
    "repair_pipeline_design.md",
    "pipeline_design.md",
    "investigation/review_a.json",
    "coordinator_identity_sidecar.json",
    "verification.log",
    "result.json"
  ],
  "repair_request_source": "simulated_user_prompt",
  "repair_scope_summary": "what the user asked to fix",
  "repair_plan_contract": {
    "user_feedback": "the concrete user-visible change request",
    "retained_context": ["current artifacts intentionally available to repair"],
    "forbidden_context": ["archive/", "old transcripts/", "old stage reviews/"],
    "repair_objectives": [
      {
        "objective": "feedback point to address",
        "evidence_source": "user feedback, current artifact, spec, or rubric",
        "success_criteria": "how this objective will be verified"
      }
    ],
    "planned_changes": [
      {
        "target": "file, directory, artifact, behavior, or deliverable to change",
        "reason": "why this target is part of the repair",
        "expected_verification": "check proving the change is correct"
      }
    ],
    "unchanged_or_out_of_scope": [
      {
        "target": "thing intentionally left unchanged",
        "reason": "why it is outside this repair"
      }
    ],
    "repair_strategy": {
      "scope_rationale": "why this repair scope is enough and why full_flow is not needed",
      "regeneration_or_rerun_steps": ["task-specific rebuild/rerun/render/check steps"],
      "dependency_order": ["order in which repaired artifacts depend on each other"],
      "stop_conditions": ["evidence that the repair can stop"]
    }
  },
  "must_not_full_rerun": true
}
```

The rollback archive is allowed for Main Agent A and post-run trajectory
reviewers. Runtime coordinator B and runtime children C must not use it as task
context unless the simulated user explicitly asks to compare against the
archived version. They should use the retained active draft files instead.

Runtime verification commands must preserve that boundary mechanically, not only
by intent. When a coordinator or child needs an active-workbench search, it
should either `cd` into the workbench and use relative paths with an explicit
archive exclusion, or use `find` with an archive prune. Do not rely on broad
absolute-path searches whose glob exclusions may fail to match nested
`archive/` paths. Safe patterns are:

```bash
cd data/homework/<COURSE>/<assignment>
rg -n "submit|canvas" . --glob '!archive/**'

find data/homework/<COURSE>/<assignment> \
  -path 'data/homework/<COURSE>/<assignment>/archive' -prune -o \
  -type f -print
```

If a command exposes archive path names, record it as a process concern and
rerun the check with a pruned command. If a command exposes archive file
contents to a runtime coordinator or child, the run cannot be clean `PASS`; the
trajectory reviewer must judge whether the content influenced task decisions and
whether the verdict should drop to `PASS_WITH_CONCERNS` or `FAIL`.

## Coordinator Launch Boundary

The runtime coordinator must receive only:

- the simulated user's assignment request;
- explicit user supplements that would normally be provided at `[B]`;
- `skill.md`;
- `sub-skills/tasks/do-homework.md`;
- `sub-skills/tasks/task-orchestrator.md`;
- top-level tool contracts that a real AutoStudy runtime could progressively
  load.
- for `repair_flow`, the accepted startup inventory and the
  explicit user-visible retained files named in that inventory.

The coordinator must not receive:

- previous iteration stage briefs, stage receipts, review receipts, trajectory
  reviews, `verification.log`, `result.json`, or coordinator summaries;
- the Main Agent's diagnosis of prior bugs such as "report has no figures" or
  "package parity failed";
- `docs/runtime-agent-protocol.md` as its primary runtime manual;
- hidden workbench files containing user supplements that were not explicitly
  surfaced in the simulated user prompt.
- archived rollback evidence as task context, unless the user explicitly asks
  for an old-version comparison.

The Main Agent and later trajectory reviewers may use internal protocol docs as
the audit standard. The runtime coordinator should experience the same public
skill/task interface a normal AutoStudy user-facing agent would load.

After dispatch returns the coordinator's stable agent/thread id, the Main Agent
must provide that id to the coordinator if it was not known at initial prompt
time. The coordinator must record it in its summary and dispatch ledger. Generic
labels such as `main-thread-runtime-coordinator` are not sufficient as the only
coordinator identity in development validation evidence.

## Repair Coordinator Contract

For `repair_flow`, the coordinator must begin by writing a repair request
artifact, for example `repair_request.md` or `repair_plan.md`, that restates the
user feedback, the retained files it will use, the objectives it is repairing,
the targets it intends to modify, and the targets it intends to leave
unchanged. This contract is task-agnostic: it must not assume every assignment
has a notebook, report, slide deck, package, game, web app, or PDF. Those are
current-task artifacts that the coordinator names only when they actually
exist. The repair pipeline should be scoped by the user's request: do not delete
the current draft or perform a from-scratch reconnaissance unless the repair
request explicitly requires it.

The coordinator must write a repair-specific `repair_pipeline_design.md`. The
old full-flow `pipeline_design.md` is rollback/archive evidence, not active
repair startup context, unless the simulated user explicitly asks to inspect the
old pipeline plan. The repair pipeline must declare task-specific stages that
cover:

- repair diagnosis: inspect the current user-visible artifact and feedback;
- repair execution: modify only justified files, generated artifacts, behavior,
  or deliverables;
- repair verification: rerun the checks needed by the touched artifacts, such
  as tests, renders, notebook execution, browser checks, PDF checks, package
  checks, data validation, or other task-relevant gates;
- repair review: verify that the user feedback was addressed without
  regressing previously passing deliverable gates.

Each delegated repair stage still uses child subagents and the normal
executor/spec-reviewer/quality-reviewer pattern. Child briefs must identify
which current draft artifacts are allowed task context and which prior evidence
classes remain forbidden. A repair child may read and edit current draft files
that are in the retained startup list; it must not read the rollback archive,
old transcripts, old stage reviews, or prior trajectory verdicts as hidden
answers.

If the repair is a broad rewrite or new version, it is still `repair_flow`.
The coordinator must state whether it edits the current output in place or
creates a versioned output such as `draft_v2/`, and must preserve enough
provenance for reviewers to distinguish the old retained artifact from the
repaired candidate.

## Nested Transcript Evidence Roles

Task 10 validates a nested execution and nested review chain, not just whether
the Main Agent can inspect files after the run:

```text
Main Agent A
  -> runtime coordinator B
      -> execution/review child agents C1, C2, C3...

After B finishes:

Main Agent A
  -> exports B/C transcript evidence by the runtime-appropriate mechanism
  -> dispatches trajectory review coordinator D
      -> D audits B's coordinator trajectory
      -> D dispatches transcript-auditor child agents E1, E2, E3...
          -> each E audits exactly one C transcript body
```

The coordinator B is the authority for child identity because B receives the
child dispatch return values. B must therefore preserve every child `agent_id`
or stable transcript handle in `child_dispatch_ledger.json`, including
superseded attempts and any descendants if a child was allowed to dispatch its
own child. The Main Agent A must not rely on search to discover missing nested
threads. It must use the propagated ids from B's ledger.

`child_dispatch_ledger.json` has a single writer: the coordinator that owns the
dispatch return value. Runtime children C must not create, append, rewrite, or
normalize the ledger. A child may write only its assigned stage result/review
receipt and declared draft outputs. If a child transcript shows ledger writes,
the coordinator must preserve the polluted entry as evidence, mark it
`superseded_not_counted` or `rejected_child_side_ledger_write`, dispatch a
replacement if needed, and record a process concern. A clean Task 10 `PASS`
requires no child-side ledger writes.

For ordinary `spawn_agent` validation, transport failures are a first-class
state, not an informal excuse. If `wait_agent` returns `not_found`, a stream
disconnect, or another transport error after a child was dispatched, the
coordinator must perform the same recovery check before accepting the child:

1. The expected receipt exists and parses as strict JSON.
2. The local session JSONL for the child id exists or direct-parent transcript
   export exists.
3. The transcript or exported body contains the child assignment prompt.
4. The transcript or receipt evidence supports the claimed final status.
5. The receipt identity can be reconciled to the coordinator dispatch id.

Only then may the ledger status be `accepted_with_transport_recovery`. Missing
receipt evidence, missing transcript evidence, or unsupported final-status
claims require a replacement child or `BLOCKED`. Any
`accepted_with_transport_recovery` entry is a process concern; a clean `PASS`
requires no transport recovery entries.

Child receipt identity must not use role aliases such as `C4`,
`C4-spec-review`, or `current child`. If the child knows its exact runtime
`agent_id`, it writes that value. If it does not know the id at write time, it
must write `agent_id: null`, `agent_id_source:
"unknown_to_child_at_write_time"`, and `identity_authority:
"stage_reviews/child_dispatch_ledger.json"`. The coordinator may then add
`coordinator_authoritative_agent_id`, `identity_normalized_by_coordinator:
true`, and `original_agent_id_field`. Alias ids are schema drift and prevent a
clean `PASS` unless superseded or replaced.

All runtime receipts and ledgers used for validation must carry timestamp
evidence. Stage result/review receipts must include `created_at_utc` and
`completed_at_utc`. Dispatch ledger entries must include `dispatched_at_utc`,
`recorded_before_wait: true`, and, once known, `receipt_observed_at_utc` and
`accepted_at_utc` or `superseded_at_utc`. Review ordering must be provable from
both dependency fields and timestamps; relying only on transcript order caps
the verdict at `PASS_WITH_CONCERNS`.

Runtime child prompts and stage briefs must include an explicit scope-hygiene
rule: children are subagents with curated runtime context. The validation read
model is blacklist-first. A child may inspect current-run artifacts that are
directly relevant to its assigned stage or to the executor/reviewer output it is
judging, including generated provenance when that provenance is part of the
deliverable contract. It should not read external workflow/plugin skill files,
development-plane docs, progress docs, Task 10 plans, archive evidence, or
prior-run diagnostics unless a brief explicitly allows that forbidden class.
Runtime-facing prompts and briefs should avoid naming project-development
workflow frameworks unless the child truly needs them for the assigned stage. If
the host platform injects unavoidable startup/plugin instructions, the child may
obey only the minimal stop/skip behavior required by that platform, but it must
not use those external workflow skills as task context. A platform-mandated
startup read with no task influence is an environment limitation to record, not
by itself a clean-PASS blocker. Actively reading or applying external workflow
skills, AutoStudy validation plans, development docs, prior diagnostics, or
archive evidence as task sources is a process concern or failure depending on
impact; reading prior AutoStudy validation or archive evidence is a failure.

The Main Agent A owns transcript collection for the review phase. If B could not
export child transcripts directly, A acts only as a mechanical transcript export
broker before review: locate each raw transcript body, copy it unchanged under
`transcripts/`, and record provenance. A must not replace D/E's semantic review
by reading and judging every child trajectory itself. Once transcripts are
exported, D owns the independent process review and must dispatch one auditor
child E per available execution/review child transcript. A final trajectory
verdict that does not include auditor-child review of available transcript
bodies is incomplete.

D and E have different audit scopes:

- D, the trajectory review coordinator, audits process organization and coverage.
  D reads the coordinator summary/transcript, dispatch ledger, transcript
  inventory, stage brief/result/review indexes, and E audit receipts. D should
  not default to reading every child transcript body end to end; D may inspect
  transcript bodies only for sampling, anomalies, or high-risk contradictions.
- E, a transcript-auditor child, audits one runtime child C in depth. Each E
  receives exactly one C transcript body plus that C's initial prompt or
  dispatch request, stage brief, required tool docs when available, and receipt.
  E first derives that child's instruction contract, then decides whether the
  transcript supports the receipt and whether C stayed within the contract.

D must not replace E audits with a receipt-only summary. E must not broaden its
scope to audit the whole run. This division keeps the review scalable while
preserving transcript-body evidence.

## Post-Run Process Review

Every iteration must review the process, not just the artifact quality:

- Did the coordinator follow the declared mode (`full_flow` or `repair_flow`)?
- Did any retained startup file leak previous conclusions or receipts?
- Did child subagent trajectories match their declared stage and role?
- Did any child write to coordinator-owned ledgers or other forbidden files?
- Did any transport recovery occur, and if so was it justified by receipt plus
  transcript evidence rather than accepted from a final message alone?
- Did child receipts avoid alias ids and either record exact `agent_id` values
  or explicit null-plus-authority identity fields?
- Did receipts and dispatch ledger entries include timestamps sufficient to
  prove ordering?
- Did child transcripts stay within allowed runtime reads and avoid external
  workflow/plugin skill influence, development-plane scope drift, or archive
  evidence leakage? If unavoidable platform startup reads occurred, did the
  transcript show that they were not used as task context?
- Did reviewers catch workflow-design problems, not only content mistakes?
- Were blocking `auto_fixable` issues repaired before final handoff, and were
  optional polish items kept separate from repair-required blockers?
- Were skipped stages represented by explicit `SKIPPED` result receipts and
  review `SKIP` receipts?
- Were transcript exports attempted by the direct parent coordinator whenever
  the tool surface allowed it?
- If the direct parent coordinator could not export child transcripts, did the
  Main Agent attempt a post-run transcript collector fallback using the stable
  child ids/transcript handles from the dispatch ledger?
- Did the trajectory review coordinator dispatch auditor children for every
  available execution/review child transcript body?
- Did D keep coordinator-level process review separate from E's one-child
  transcript-body audits?

These checks apply when swapping DSAA2011 for any later validation assignment.
The task can change; the launch hygiene, no-leak rule, child trajectory audit,
and repair-before-handoff rule do not.

## Transcript Collector Fallback

Full transcript export has two chances in development validation:

1. **Direct-parent export first.** The coordinator that dispatched a child
   subagent should export that child's full transcript before closing it when a
   read/export-thread tool is exposed to that coordinator.
2. **Main-thread collector fallback.** If the coordinator records
   `transcript_export_path: null` because it lacked a read/export-thread tool,
   the Main Agent must try a post-run collector using the stable child ids or
   transcript handles from `child_dispatch_ledger.json`.

For Codex app validation, there are two different id domains:

- `codex_app.read_thread` accepts Codex app thread ids. These are used by normal
  Codex app threads and the inspectable Codex-thread harness.
- `multi_agent_v1.spawn_agent` returns multi-agent agent ids. Current probes show
  these ids work with `multi_agent_v1.wait_agent` / `resume_agent` for final
  status/output, but are rejected by `codex_app.read_thread` with invalid
  arguments and are not discoverable through `codex_app.list_threads`.

Therefore, when Task 10 uses ordinary `multi_agent_v1.spawn_agent`, the
Main-thread collector fallback is local-session export, not `read_thread` by
agent id. For each propagated `agent_id`, locate exactly one
`.codex/sessions/**/<timestamp>-<agent_id>.jsonl` file, copy it unchanged under
`transcripts/`, and record the source path, line count, and exact-match rule in
`transcripts/transcript_inventory.json`. Do not use fuzzy `rg ... | head -1`
matching; ambiguous or missing session files are collector failures.

When the propagated id is a Codex app thread id, `read_thread` collection must
paginate. A single `read_thread` call may return only the most recent turns and
can therefore capture only the final/finalize exchange. The collector must
follow older-page cursors until no cursor remains, or until it has evidence that
the thread's initial assignment prompt and all visible intermediate messages
have been captured. Record pagination status in
`transcripts/transcript_inventory.json` for every exported coordinator, child,
and auditor thread.

When fallback succeeds, write each exported transcript to:

```text
transcripts/<stage_id>_<role>_<agent_id>.jsonl
```

Then update or sidecar the relevant receipt/ledger evidence with
`transcript_export_path`. The trajectory review coordinator must then dispatch
one transcript-body auditor child per available transcript. Only when both the
direct-parent export and main-thread collector fallback fail may the run record
`NO_FULL_CHILD_TRANSCRIPT_EXPORTS_AVAILABLE` and cap the verdict at
`PASS_WITH_CONCERNS`.

Transcript-auditor children must derive a child-specific instruction contract
before judging. The contract comes from the child's initial prompt, dispatch
request, stage brief, required reads, required tool docs, receipt/trace schema,
role/stage boundary, task-relevant current-run read scope, forbidden
reads/actions, allowed writes, forbidden writes, and finalization protocol. E
then checks whether the transcript followed that contract. E should not treat a
directly relevant current-run artifact read as a concern merely because the
brief did not enumerate that exact file; the concern is reading a forbidden
class such as archive/prior-run/development evidence, or using host-injected
workflow context as task evidence. Generic safety checks such as forbidden
Canvas submission, role bleed, unsupported receipt claims, and unexplained
evidence limitations remain fallback checks, but the primary rubric is the
child's own instruction contract.

The trajectory review coordinator must check at least:

- declared iteration mode and the context/launch contract for that mode;
- coordinator identity and child-dispatch identity consistency;
- ledger coverage for normal, superseded, standby, replacement, repair, and
  skipped attempts;
- transcript inventory coverage for every auditable child;
- one E audit receipt per available child transcript;
- repair-before-handoff handling for blocking `auto_fixable` issues;
- spec-review before quality-review ordering;
- explicit `SKIPPED` receipts when conditional stages do not run;
- artifact-quality workflow concerns surfaced by the current task/run;
- final verdict support from E receipts and coordinator-level process evidence.

When fallback fails, the failure evidence must be machine-readable. Write
`transcripts/transcript_inventory.json` with every ledger child id, role,
receipt path, and collector status. Prefer a per-child read/list attempt. If
the platform rejects the id format at the tool boundary, try the local-session
JSONL exact-match export before declaring the child unavailable. The inventory
must name sampled ids, tool errors, local-session search patterns, and the reason
any remaining children inherit the same `not_exported` status.

## Inspectable Thread Harness For Clean PASS

If a development validation run is expected to reach a clean transcript-body
`PASS`, do not use a child-dispatch surface whose children cannot be exported or
read by either direct-parent export, Codex app `read_thread`, or local-session
JSONL exact-match export. Use
`docs/inspectable-subagent-transcript-harness.md` or an equivalent platform
transcript export API only when ordinary child ids cannot be propagated and
their local sessions cannot be exported.

The inspectable harness dispatches each executor/reviewer as a readable Codex
thread, keeps it active at `READY_FOR_TRANSCRIPT_EXPORT`, exports
`codex_app.read_thread` output under `transcripts/`, records a child-written
trace bundle, and only then finalizes the child. This remains a fallback harness
for platforms or tool surfaces where ordinary nested child ids cannot be read.
