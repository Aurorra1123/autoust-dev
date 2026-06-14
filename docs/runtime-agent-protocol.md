# Runtime Agent Protocol

> Status: Draft design baseline, 2026-06-04.
> Scope: how AutoStudy should run as a Claude Code skill when handling real
> user tasks. This is not a development roadmap and not a standalone multi-agent
> framework.

## 1. Purpose

AutoStudy uses documents as runtime handoff interfaces. The goal of this
protocol is to make each agent read the right context at the right time, write
the next handoff artifact, and avoid mixing current task execution with project
development history.

The design borrows mature workflow discipline from the Superpowers plugin, but
Superpowers is a **design reference only**. AutoStudy runtime must not require
the user to install or invoke Superpowers.

Reference mapping:

| Superpowers practice | AutoStudy runtime translation |
|---|---|
| `brainstorming` | post-recon alignment loop with the user at `do-homework [B]` |
| spec document | assignment `spec.md` grounded in Canvas sources |
| `writing-plans` | `pipeline_design.md` as the task-level execution plan |
| implementer subagent | stage executor subagent with a precise `stage_brief.md` |
| spec compliance reviewer | reviewer that checks whether the artifact answers the assignment |
| code quality reviewer | reviewer that checks whether the artifact is well built |
| verification-before-completion | `verification.log` and `result.json` gates before claiming done |

## 2. Two Planes

AutoStudy has two separate documentation planes. They must not be blended.

### Development Plane

For the project developer and development agents maintaining AutoStudy itself.

Examples:

- `docs/DEVELOPMENT.md`
- `docs/COLLABORATION.md`
- `docs/ROADMAP.md`
- `docs/progress/agent-progress.md`
- `docs/plans/feature-list.json`
- `docs/superpowers/specs/*`
- pipeline audits and reference analyses

These documents answer: how should AutoStudy evolve, what has been verified, and
what should be built next?

### Runtime Plane

For the Claude Code Main Agent and subagents while solving a real user task.

Examples:

- `skill.md`
- `sub-skills/tasks/*.md`
- `sub-skills/tools/*.md`
- the current task workbench under `data/homework/...` or `data/courses/...`
- `spec.md`, `pipeline_design.md`, stage briefs, stage results, stage reviews

These documents answer: what does the user need now, what facts have been
discovered, what is the current plan, and what evidence proves the result?

Runtime agents should not use Development Plane documents as task instructions.
They may contain historical ideas, outdated plans, or future features.

## 3. Claude Code Runtime Reality

AutoStudy is not an independent multi-agent framework. It runs inside Claude
Code as a skill.

There are only two runtime actor classes:

1. **Main Agent**: the current Claude Code session. It is the only actor that
   talks directly with the user. It owns routing, planning, subagent dispatch,
   review loops, and final user handoff.
2. **Subagents**: temporary workers dispatched by the Main Agent. A subagent
   only receives the prompt/context given by the Main Agent, reports back to the
   Main Agent, and must not talk to the user or dispatch other subagents.

Therefore, "roles" in this protocol are not persistent autonomous agents. They
are either Main Agent phases or subagent prompt contracts.

## 4. Unified Run Model

Runtime validation and user-facing homework work use one composable flow:

```text
archive/preflight
-> startup_inventory
-> explore stage
-> alignment contract
-> execution plan
-> shared executor/reviewer/verification runtime
```

`full_flow` and `repair_flow` remain compatibility presets and user-facing
labels, not separate architectures:

- `full_flow` means the startup inventory has no retained user-visible draft, so
  source/spec exploration is usually the only enabled exploration capability.
- `repair_flow` means the startup inventory includes retained user-visible
  artifacts or prior progress, so artifact/history/verification exploration may
  also be enabled.

The runtime should branch on the startup inventory, not on hard-coded
`if full_flow else repair_flow` logic. If a scout input does not exist, the
coordinator records that scout as `SKIPPED` with a reason instead of inventing a
flow-specific substitute. A first run with no draft naturally skips artifact,
codebase, history, and current-verification scouts. A retained-draft run enables
only the scouts whose inputs are present and planning-relevant.

### Archive And Startup Inventory

Before a run starts, the Main Agent creates a rollback/audit boundary for any
existing active workbench evidence. Generated runtime evidence from prior runs
is archived or removed from active startup context before the coordinator plans
the next run. The startup inventory then declares:

- retained user-visible artifacts, if any;
- source/spec/reference files available to the run;
- stale process files removed from active context;
- allowlisted prior history files that scouts may read;
- forbidden context such as archive contents, old transcripts, prior reviews, or
  old diagnostics unless specifically allowlisted for exploration;
- user request and any user-supplied constraints.

Old generated artifacts are legitimate task context only when they are current
user-visible artifacts being continued or changed and are listed in the startup
inventory. Old stage receipts, transcripts, trajectory reviews, validation
diagnostics, prior `repair_plan.md`, prior `repair_pipeline_design.md`, old
`pipeline_design.md`, coordinator identity sidecars, and investigation/review
receipts are process evidence by default. They can inform planning only through
an explicit allowlisted explore scout that distills them into current-run
evidence.

### Explore Stage

The explore stage is universal. The coordinator may perform a tiny exploration
inline for a trivial request, but for non-trivial homework work it dispatches
focused read-only explorer/scout subagents with curated context.

Main Agent / Subagent taxonomy is explicit:

- Main Agent exploration domains decide which broad surfaces matter:
  `source_spec`, artifact, codebase, process history, and verification.
- `source_spec` is a Main Agent exploration domain, not a dispatchable Subagent
  role and not one completed child result.
- Non-trivial source-heavy homework expands the `source_spec` domain into three
  dispatchable Subagent roles: `metadata_scout`, `content_scout`, and
  `coverage_reviewer`.
- `content_scout` subdivisions are `scope` values, not child identities. Use
  `scope: spec_content`, `methods_content`, `theme_content`, or
  `policy_content` on a child whose `scout_type` is `content_scout`.

Available Main Agent domains and dispatchable Subagent roles are:

- source/spec exploration domain: the Main Agent owns source/spec
  reconnaissance, final main-source judgment, `spec.md`, and user-facing
  alignment. For non-trivial homework reconnaissance, this domain dispatches
  Subagent roles `metadata_scout`, `content_scout`, and `coverage_reviewer`.
  It must not dispatch or accept a successful child named `source_spec`;
- metadata_scout: index assignment, rubric, front page, syllabus, every module
  item, pages, file metadata, assignment files, and external URLs, then write
  `investigation/source_candidates.json` without making final source-body
  judgments. If it reads a full Canvas page, syllabus body, front-page body, or
  external document body, that read must be recorded as body evidence or
  assigned to a `content_scout`;
- content_scout: read assigned candidate source bodies from
  `investigation/reading_plan.json`, preserve extracted text and source-adjacent
  companion artifacts, and write body evidence fragments under
  `investigation/source_body_audit_fragments/`;
- coverage_reviewer: cold-read source candidates, reading plan, source body
  audit, content receipts, references, and unreachable resources to catch missed
  high-signal sources, metadata-only evidence, forbidden reads, and weak
  proposal/research/open-ended coverage;
- artifact scout: inspect current user-visible drafts, source code, packages,
  generated media, reports, slides, notebooks, or demos;
- codebase scout: inspect repository structure, scripts, dependencies, tests, and
  integration points when a runnable project exists;
- process history scout: read only allowlisted previous planning/progress
  evidence such as prior `pipeline_design.md`, `verification.log`,
  `result.json`, package manifests, or stage result summaries, then extract
  still-valid decisions, passed gates, failed gates, and known risks;
- verification scout: run or inspect lightweight current checks needed to
  understand the planning surface before execution.

When a source-reading Subagent is dispatched, it is part of the same runtime
child evidence chain as executor and reviewer children. The coordinator records
the dispatch in `stage_reviews/child_dispatch_ledger.json` with
`role: explore_scout`, `scout_type`, optional `scope`, prompt/brief path,
receipt path, and timestamps.
For proposal/research/open-ended source-heavy work, the coordinator must
dispatch real child subagents for `metadata_scout`, `content_scout`, and
`coverage_reviewer` when the runtime can spawn children. Main Agent inline
recovery must be recorded as recovery evidence, not as a Subagent receipt.
Scout receipts are written under:

```text
investigation/scout_results/<scout_type>_result.json
```

or an equivalent path named in `investigation/explore_manifest.json`. Skipped
scouts are also explicit evidence: the manifest records `status: "SKIPPED"` and
the reason. Scout children must follow the same identity, transcript,
transport-recovery, single-writer ledger, and forbidden-read rules as later
executor/reviewer children.

Explorer findings are consolidated into the stable current-run artifact:

```text
investigation/explore_context.md
investigation/explore_manifest.json
```

Compatibility outputs may also be written:

```text
spec.md                         # source/spec exploration result
problem.md                      # legacy source/spec compatibility
investigation/rubric.md          # assignment rubric or extracted criteria
references/                     # fetched source materials
                                # optional derived Canvas convenience exports
investigation/repair_recon.md    # retained-artifact/progress-focused summary
```

`explore_context.md` records current state, source requirements, available
assets, prior decisions that still apply, stale or forbidden context, likely
scope, verification risks, skipped scouts with reasons, and questions that
require user alignment. Raw prior logs, archived transcripts, prior reviews, and
old pipeline files do not become general task context just because an explorer
inspected them. Executor and reviewer children receive raw prior process files
only when the final execution plan explicitly justifies that narrow access.
Main Agent remains the final reconnaissance judge: scouts can rank, read, and
review sources, but they do not write final `spec.md`, final `review_a.json`,
pipeline approval, or user-facing alignment decisions.
Content scouts narrow the read set; they do not replace Main Agent source reading.
scout summaries are routing hints, not source evidence. The Main Agent must read
the narrowed source bodies before writing or revising `spec.md`, using raw
`canvas/*.json` bodies for Canvas-native sources and saved source text or exact
page/slide/window artifacts for PDFs, decks, or external documents.

Reconnaissance ends only after the coordinator passes a reconvergence gate.
coverage feedback is not a terminal reconnaissance verdict: a covered
`source_body_audit.json` / `source_coverage_feedback.json` pair does not replace
`spec.md`, `investigation/rubric.md`, or `investigation/review_a.json`. If those
terminal artifacts are missing, the coordinator must write a recover/blocking
`review_a.json` or `stage_reviews/process_concerns.jsonl` that names the missing
`spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` artifact
before it stops, asks for recovery, dispatches a replacement, or proceeds.
Rule for automated checks: missing `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` must write a recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`.

### Alignment Contract

After exploration, the Main Agent aligns with the user over the gaps that affect
planning. The mechanism is shared:

- ask one drift-risk-reducing question at a time when the explore context is not
  specific enough to plan;
- record each round in `investigation/user_notes.md`, `repair_notes.md`, or an
  equivalent current-run notes file;
- present 2-3 viable approaches with trade-offs and a recommendation when the
  request could reasonably be solved in different ways;
- preview a scope/design skeleton before treating the terminal agreement as
  final;
- confirm with the user before dispatching execution stages when the choice
  affects artifact boundaries, creative direction, architecture, data contracts,
  or demonstration strategy.

Initial assignments usually write the terminal agreement to
`investigation/alignment_brief.md`. Retained-artifact change requests usually
write it to `repair_plan.md`. Both are the same kind of agreement: they record
selected approach, alternatives considered when relevant, retained/forbidden
context, changed and unchanged targets, scope/design skeleton, verification
gates, stop conditions, and remaining open items. An old
`alignment_brief.md` can remain background only when the current agreement says
which parts still apply.

### Execution Plan

After the terminal agreement is confirmed, the coordinator writes an execution
plan. `pipeline_design.md` and `repair_pipeline_design.md` are compatibility
names for the same stage schema. The plan must derive from
`explore_context.md` plus the terminal agreement, then dispatch the shared
executor/reviewer/verification runtime described below.

Validation harness exception: a development session may explicitly dispatch a
fresh "runtime coordinator" subagent to simulate a real user's Main Agent
session. In that harness, the coordinator must be given a tool surface that can
dispatch child scout/executor/reviewer subagents, and it may dispatch those
child subagents only for the validation run. If the coordinator cannot dispatch child
subagents, the run may still validate file contracts through `inline_fallback`,
but it does not validate true scout/executor/reviewer isolation.

This exception creates a second, development-only line around the normal runtime
line. In real user-facing work there is only the Main Agent and its subagents:
the Main Agent talks to the user during `do-homework [B]` and writes the
confirmed `alignment_brief.md`. In development validation, the current session
is outer Main Agent A, which launches coordinator B to simulate that real Main
Agent. A may prepare clean startup evidence, inject B's stable id, bridge live
simulated-user answers during `[B]`, export transcripts, and dispatch trajectory
reviewers. A must not feed B hidden development diagnoses, rewrite B's
alignment questions, or turn the human reviewer's development comments into user
intent. The detailed launch and bridge rules live in
`docs/development-validation-standard.md`.

Validation evidence must be stable enough for another agent to audit later. The
runtime coordinator summary must record a stable coordinator agent id or
transcript handle; "current thread" alone is not sufficient. The coordinator is
the authority for child identity because it receives the child dispatch return
value. Child subagents may include their own `agent_id` when they know it, but
the coordinator must verify it against the dispatch return before accepting the
receipt. The happy path is exact child identity at write time. If the child
does not know its runtime id, it must write `agent_id: null`,
`agent_id_source: "unknown_to_child_at_write_time"`, and
`identity_authority: "stage_reviews/child_dispatch_ledger.json"`. It must not
invent role aliases such as `C4`, `executor-1`, or `current child`. If the child
omitted the id and the null-plus-authority fields, the coordinator may add the
authoritative id or write an identity sidecar before final verification, but
that normalization is a process concern. If the child recorded a different id,
the stage is `BLOCKED` until the mismatch is reconciled by a replacement child
or an explicit superseded-attempt record. Child subagent receipts must record
`agent_id` or `transcript`, and when the runtime can export full child
transcripts the coordinator should also save them under `transcripts/` and
record `transcript_export_path`. If full transcript export is not available,
the coordinator must state that limitation in the summary and preserve the best
available handle.

The child dispatch ledger is coordinator-owned state. Only the coordinator that
called `spawn_agent` or the equivalent dispatch primitive may create, append,
rewrite, or normalize `stage_reviews/child_dispatch_ledger.json`. Runtime child
subagents write only their assigned receipt and declared outputs. Stage briefs
must list `stage_reviews/child_dispatch_ledger.json`, other stage receipts, and
trajectory-audit files as forbidden writes unless the child is explicitly a
coordinator. If a child writes to the ledger, the coordinator preserves the
evidence, marks that row `rejected_child_side_ledger_write` or
`superseded_not_counted`, and dispatches a replacement when the polluted entry
would otherwise be counted.

Transport recovery is explicit. If waiting for a child returns `not_found`,
stream disconnect, timeout after dispatch, or another transport-layer failure,
the coordinator must not accept the child from the final message alone. It may
mark the ledger `accepted_with_transport_recovery` only when the expected
receipt exists, the receipt parses, the transcript or local session JSONL for
the child id exists, the transcript contains the assignment prompt, and the
receipt/transcript evidence supports the claimed final status. Otherwise the
coordinator re-prompts, dispatches a replacement, or marks the stage `BLOCKED`.
Transport recovery is acceptable for robustness, but clean validation should
aim for normal `accepted` statuses.
Filesystem receipts without transcript evidence are recovery evidence, not clean
child-isolation validation. They may unblock a run when paired with explicit
process concerns, but they cannot by themselves prove that the scout boundary was
validated.

Every receipt and dispatch record needs ordering evidence. Scout result
receipts and stage result/review receipts use `created_at_utc` and
`completed_at_utc`; dispatch ledger entries use `dispatched_at_utc`,
`recorded_before_wait`, and when applicable `receipt_observed_at_utc`,
`accepted_at_utc`, or `superseded_at_utc`. Review ordering should be provable
from dependency fields and timestamps, not only from prose or transcript
sequence.

Runtime children operate inside curated context. Child prompts and briefs must
state required reads, task-relevant read scope, and forbidden reads/writes. The
read-scope model is blacklist-first, not a brittle fixed whitelist: a child may
inspect current-run artifacts that are directly relevant to its assigned stage
or scout assignment, or to the executor/reviewer output it is judging, especially generated
provenance files needed to verify that output. Development-plane documents,
progress logs, validation plans, archive evidence, prior-run diagnostics, and
external workflow/plugin skill files remain forbidden unless the brief
explicitly allows them. Runtime-facing briefs should avoid naming development
workflow frameworks; naming them can itself pull a runtime child toward
irrelevant context. If the host platform injects unavoidable startup/plugin
instructions, the child should obey only the minimal stop/skip behavior needed
to continue with the assigned brief and must not treat those external workflow
instructions as task context. A platform-mandated startup read with no task
influence is an environment limitation for reviewers to note, not by itself a
clean-PASS blocker. On platforms where startup skill rules require an explicit
read of a workflow skill file, such as a `using-superpowers` startup check, E
auditors should classify the read as nonblocking environment noise when the
transcript shows the child immediately returned to the assigned runtime brief
and did not use that workflow skill as assignment evidence or process
authority. A voluntary read or use of development workflow skills, validation
plans, progress logs, prior diagnostics, or archive evidence as task material is
scope drift and may block a clean validation verdict.

Runtime search commands must also respect the curated context boundary. A
coordinator or child should not run broad absolute-path searches and assume
`archive/` is excluded by intent; glob exclusions can fail when the path shape
does not match. For active-workbench checks, either `cd` into the workbench and
search relative paths with `--glob '!archive/**'`, or use `find` with an
explicit `archive` prune. If a command prints archive path names, record a
process concern and rerun the check with a pruned command. If it prints archive
file contents into the runtime transcript, clean process `PASS` is blocked even
when the content did not influence the assignment artifact.

Transcript export has a required identity chain. The direct parent that
dispatched a child should export that child's transcript when an
export/read-thread tool is available to the parent. If the direct parent cannot
export, it must still preserve the authoritative child `agent_id` or stable
transcript handle in the dispatch ledger. The parent must also preserve any
descendant ids if it allowed a child to dispatch another child. A later agent
cannot reliably discover missing nested threads by search; it must locate and
export transcript evidence from the propagated ids.

If the coordinator cannot export child transcripts, the Main Agent must attempt
a post-run collector fallback using the stable child `agent_id` or transcript
handles in the dispatch ledger before it dispatches the trajectory reviewer. In
Codex app, distinguish Codex app thread ids from ordinary
`multi_agent_v1.spawn_agent` agent ids. Codex app thread ids can be exported
with `codex_app.read_thread`; ordinary multi-agent ids currently cannot. For
ordinary `spawn_agent` children, the fallback is exact local-session JSONL
export from `.codex/sessions/**/<timestamp>-<agent_id>.jsonl`. If either
fallback succeeds, export the transcript body under `transcripts/`, add
`transcript_export_path` through receipt normalization or sidecar evidence, and
dispatch transcript-body auditors. Only after direct-parent export,
Codex-thread `read_thread` where applicable, and local-session exact-match
export all fail may the trajectory review treat full transcripts as unavailable.

Codex `read_thread` exports must follow pagination cursors. The first response
may contain only recent/final turns; a collector that does not request older
pages can miss the child assignment prompt, tool-output summaries, and
intermediate corrections. Local-session JSONL exports do not use cursors; their
inventory entries must instead record exact source path, line count, and whether
the initial task message and final answer are present.

The review chain is itself nested. After the runtime coordinator finishes, the
Main Agent exports the coordinator transcript and every child transcript it can
locate from the ledger. This export is a mechanical evidence-broker step, not a
semantic review. The Main Agent then dispatches a trajectory review
coordinator, and that reviewer dispatches one transcript-auditor child for each
available runtime child transcript. The reviewer must audit the coordinator's
trajectory and must not replace per-child transcript-body audits with a summary
or receipt-only check.

The trajectory reviewer and transcript-auditor children have separate scopes.
The trajectory reviewer audits coordinator-level process coverage: declared
iteration mode and the matching launch/context contract, ledger completeness,
identity consistency, transcript inventory coverage, repair/review ordering,
skipped-stage receipts, and whether the final verdict is supported by auditor
receipts. It may sample or inspect child transcript bodies for anomalies, but it
should not default to reading all child bodies end to end. Each
transcript-auditor child receives exactly one runtime child transcript, the
child's initial instruction context, brief, required tool docs when available,
and receipt. The auditor first derives the child-specific instruction contract,
then judges whether the transcript supports the receipt and stayed inside that
contract.

Fallback failure must itself be auditable. The collector writes
`transcripts/transcript_inventory.json` with every child id/role/receipt and
one of: `exported`, `read_failed`, `not_discoverable`, or `not_exported`. Prefer
per-child attempts. A short-circuit is acceptable only when the tool boundary
rejects the id class consistently, and the inventory records the sampled ids,
exact tool errors, discovery attempts, and why the remaining children inherit
the same status.

Development validation runs that need transcript-body PASS may use the
inspectable harness in `docs/inspectable-subagent-transcript-harness.md`:
dispatch child workers as readable Codex threads, require them to pause at
`READY_FOR_TRANSCRIPT_EXPORT`, export `read_thread` JSON and a child-written
trace bundle while the thread is still active, then send a finalize message.
This harness is a fallback for platforms where ordinary nested subagent ids
cannot be propagated or their local-session JSONL cannot be exported after
completion. If the harness is used in Codex app, generated child threads may be
archived after transcript export to reduce visible project-thread clutter, but
they are still real Codex app conversations.

A child subagent response such as `Standing by`, an empty final message, or a
message without the required receipt is not completion evidence. The coordinator
must either re-send the scout/stage brief to that child, dispatch a replacement
child and record the superseded attempt, or stop the unit as `BLOCKED`. Standby
or empty responses may be recorded as anomalies, but they must not be counted as
a passing scout/executor/reviewer result.

Coordinator dispatch attempts that fail before returning a child id must still
be auditable. Record them in a coordinator-owned `process_events` array in
`stage_reviews/child_dispatch_ledger.json`, not as normal child dispatch rows.
Each no-id event should include `event_type:
"spawn_attempt_failed_no_agent_id"`, `stage_id`, `role`, `attempted_at_utc`,
the exact tool error or resource-limit message, `recovery_action`, and the
replacement `dispatch_index` when a retry succeeds. This prevents resource
pressure from disappearing into the coordinator transcript while keeping the
child dispatch list limited to attempts with stable child identities.

When the coordinator observes and accepts a child receipt, it must update the
ledger immediately: `receipt_observed_at_utc` is the time the receipt file was
first found and parsed, and `accepted_at_utc` is the time the coordinator
decided the receipt can count for the stage. `completed_at_utc` from
`wait_agent` is useful transport evidence, but it is not a substitute for
receipt observation and acceptance timestamps.

When a validation coordinator's stable id is known only after the dispatch call
returns, the Main Agent must send an identity-injection message before the
coordinator writes final evidence. The coordinator records that id in
`nested_isolation_coordinator_summary.md` and any dispatch ledger. Placeholder
labels such as `main-thread-runtime-coordinator` may be kept as role labels, but
they are not enough as the only auditable coordinator identity.

Coordinator-level recovery is separate from child transport recovery. If the
runtime coordinator itself repeatedly times out, stalls after a child has
completed, or must be closed to release multi-agent capacity, the Main Agent may
dispatch a replacement coordinator only after preserving the original
coordinator id, existing ledger, child ids, receipts, and transcript handles.
The replacement coordinator may read current-run process evidence needed to
recover the run, such as the current ledger, current receipts, repair/request
plan, transcript inventory, and sidecar identity files, but it must not read
archive/prior-run evidence as task context. The ledger must record a
coordinator-level `replacement_coordinator_recovery` process event with the
previous coordinator id, replacement coordinator id, observed time, recovery
scope, and reason. A run that requires coordinator replacement may still be
auditable and may pass with concerns, but it is not a clean process `PASS`.

## 5. Main Agent Phases

### Phase 0: Entry Routing

Runtime entry: `skill.md`.

The Main Agent classifies the user request and opens the corresponding task
skill:

- `sync-status.md` for Canvas status and homework planning.
- `do-homework.md` for single-assignment work.
- `sync-course.md` for course material archiving.
- `write-course-notes.md` for notes from archived lecture PDFs.

The entry router should not execute task logic by itself. It routes and applies
global safety rules.

### Phase 1: Task Coordination

Runtime entry: the selected `sub-skills/tasks/<task>.md`.

The Main Agent owns the task lifecycle. For `do-homework`, this means:

- resolve the course and assignment;
- create or resume the workbench;
- coordinate Canvas reconnaissance;
- summarize findings and ask the user for supplements;
- write the task-level plan;
- create stage briefs;
- dispatch executor and reviewer subagents;
- aggregate verification evidence;
- ask the user whether to review, revise, or submit.

The task skill is written for the Main Agent, not for subagents.

### Phase 2: Reconnaissance Coordination

Primary runtime contracts:

- `sub-skills/tools/canvascli-api.md`
- `sub-skills/tools/assignment-recon.md`
- the current assignment workbench

The Main Agent may perform reconnaissance directly or dispatch a focused
reconnaissance helper, but the output contract is stable:

```text
work_dir/
├── canvas/
├── spec.md
├── problem.md                  # compatibility only
├── references/
│   ├── source_docs/            # PDFs and source-adjacent text/link companions
│   ├── slides/                 # PPTX decks and extracted slide text
│   ├── external/               # fetched external text exports
│   └── pdf_links.json          # optional aggregate of PDF link annotations
└── investigation/
    ├── source_candidates.json
    ├── reading_plan.json
    ├── source_body_audit_fragments/
    ├── source_body_audit.json
    ├── source_coverage_feedback.json
    ├── rubric.md
    ├── unreachable.txt
    └── review_a.json
```

`spec.md` is the factual decision report for the assignment. It must be grounded
in Canvas sources and fetched references, not in the assignment title. For
Canvas-native bodies such as assignment, syllabus, front page, and pages, raw
Canvas JSON is the canonical evidence. derived readable artifacts are optional
convenience copies, not required gates and not authoritative sources.
summary-only scout output must never replace raw Canvas JSON; downstream stages
that need Canvas-native constraints must be explicitly allowed to read the
relevant `canvas/*.json` files and cite raw JSON pointers.

Fetched PDFs are rich source objects, not just text files. The visible text layer
does not necessarily contain URLs behind linked words. Reconnaissance must
preserve PDF link annotations by writing `references/*.pdf.links.json` or
`references/**/*.pdf.links.json` beside spec/rubric/input PDFs, using generic
fields such as source PDF path, page, anchor text, URI, and rectangle. Later
stages may decide which URLs matter, but the reconnaissance layer must not drop
them while converting PDFs into text.

Do not require `references/*syllabus*` as the evidence gate for Canvas-native
syllabus evidence. If a readable syllabus note exists, treat it as a derived
index into `canvas/syllabus.json`, not a replacement for the raw source.
`source_candidates.json` is metadata-level recall. `reading_plan.json` is the
Main Agent-approved bounded body-reading budget. Each content scout writes a
fragment under `source_body_audit_fragments/`; Main Agent merges those fragments
into `source_body_audit.json` so parallel children never write the same merged
JSON file. `source_body_audit.json` proves whether a candidate was read via
`metadata_only`, `pdf_text_plus_links`, `keyword_windows`,
`external_text_export`, `readable_extract`, or a blocked/unreachable mode.
Sources left at `metadata_only` cannot be used as precise assignment, rubric,
input, or source-context evidence.
If a source body read found relevant Canvas-native content but the only
downstream artifact is a compressed relevance summary, the coverage reviewer
must block progress until the audit points to the raw `canvas/*.json` body
section and later stage briefs explicitly allow that raw file to be read.
For every required or high-signal source that will influence assignment
understanding, the audit must say which original source body or exact source
window the Main Agent should read; a paraphrase-only fragment is not enough.

### Phase 3: User Alignment

Superpowers reference: `brainstorming`.

AutoStudy translation: after reconnaissance, the Main Agent runs the
`do-homework [B]` alignment loop.

The purpose is not generic conversation and not rigid task classification. It is
to decide whether the current Canvas facts plus user intent are sufficient to
start the project without guessing the user's core direction or project
skeleton. Simple assignments may need one confirmation. Open-ended assignments
require as many focused rounds as needed before planning starts.

The first user-facing message is a recon summary: a compact explanation of what
`spec.md`, `investigation/rubric.md`, `investigation/review_a.json`,
`investigation/unreachable.txt`, `references/`, `problem.md`, and the
preliminary output-mode line in `pipeline_design.md` prove. It is not a second
investigation and not a design proposal; it tells the user which facts are fixed
by Canvas and which decisions still need alignment.

Before each user question, the Main Agent performs an internal alignment audit:

```text
Can I answer these without guessing?

1. What exactly must be delivered?
2. What does the user want this work to express, argue, demonstrate, or optimize?
3. Which choices are fixed by Canvas/spec/rubric?
4. Which choices must come from the user before work starts?
5. Which choices has the user delegated to me?
6. What must not be fabricated or hidden?
7. Can I now write pipeline stages with concrete goals and quality criteria?
8. Could a reviewer use the eventual alignment brief to detect direction drift?
```

For open-ended design, creative, research, implementation, or interactive
projects, the Main Agent also checks whether it can sketch the project skeleton
without guessing:

- user-facing experience and interaction loop;
- creative or intellectual stance;
- core inputs, outputs, files, media, APIs, and final artifacts;
- architecture components, state, dependencies, and boundaries;
- model/tool contracts, mocks, probes, and secret handling;
- traceability/observability needed for debugging, grading, or demo;
- failure and fallback behavior;
- verification and demo strategy.

If a missing skeleton answer would change the pipeline shape, stage boundaries,
tool choice, deliverable quality criteria, or user-facing experience, it is not
a minor default.

If a missing answer could change the assignment direction, the Main Agent asks
exactly one question: the question that most reduces direction-drift risk. It
prioritizes:

- group or partner information;
- topic, dataset, project concept, thesis, research question, method, framework,
  or target audience;
- personal experience, viewpoint, aesthetic preference, group context,
  presentation intent, or oral instructor notes;
- preferred scope;
- missing external materials;
- style or format preferences;
- user-facing flow, architecture, model/API contract, observability/trace,
  fallback behavior, demo mode, and verification strategy when they affect
  pipeline design;
- whether to stop, draft, revise, or submit.

After each answer, the Main Agent records not only remaining uncertainty but
also new dimensions introduced, approach implications, and skeleton gaps still
open. This makes the loop extend from the user's answer rather than walking a
fixed checklist.

Before the terminal brief for an open-ended task, the Main Agent must present
2-3 viable approaches with trade-offs and a recommendation when meaningful, then
preview the design skeleton. The user approves or corrects that skeleton before
the terminal `alignment_brief.md` is written.

Process notes from each round go to:

```text
investigation/user_notes.md
investigation/user_scope.md      # optional, when scope is narrowed
```

`user_notes.md` is a process log. It may be appended every round. It should
record the question, user answer, coordinator interpretation, captured
decisions, and remaining uncertainty. If the user says "you decide," the
coordinator records a delegated decision rather than treating it as a user-stated
fact.

When the Main Agent has no necessary alignment question left, it writes the
terminal brief:

```text
investigation/alignment_brief.md
```

`alignment_brief.md` is the stable post-recon agreement for the task. It is
written only at the terminal alignment step, not after every round. It records:

- assignment understanding;
- user intent;
- confirmed decisions;
- selected approach and alternatives considered when relevant;
- design skeleton;
- delegated decisions and default strategy;
- non-negotiables;
- open items for final review;
- ready-to-start judgment.

Before confirmation, the Main Agent self-reviews the brief for placeholders,
contradictions, scope overreach, and unresolved ambiguity that would change
stage design.

The Main Agent then summarizes the brief and asks the user to confirm. If the
user corrects it, the Main Agent appends another `user_notes.md` round, replaces
`alignment_brief.md`, and asks again. Planning cannot start until the user has
confirmed `alignment_brief.md`.

### Phase 4: Task-Level Planning

Superpowers reference: `writing-plans`.

AutoStudy translation: `pipeline_design.md`.

`pipeline_design.md` is the total plan for the current task. It is written by
the Main Agent after reading:

- `spec.md`
- `investigation/rubric.md`
- `investigation/alignment_brief.md`
- `investigation/user_notes.md`
- `investigation/user_scope.md`, if present
- `sub-skills/tools/_index.md`
- relevant top-level tool contracts

No confirmed `investigation/alignment_brief.md` means no final
`pipeline_design.md`. A final `pipeline_design.md` still does not authorize
execution until the user reviews it and `Pipeline Review Status.status` becomes
`approved_for_orchestration`.

`pipeline_design.md` is for the Main Agent and Stage Coordinator phase. It is
not the executor subagent's direct instruction file.

Required responsibilities:

- name the output mode and final deliverables;
- list constraints and rubric-derived quality requirements;
- define ordered stages;
- map each stage to one `primary_tool` and an ordered `tools` list of all
  top-level tool skills required by that stage;
- normalize legacy `tool: <path>` as `primary_tool: <path>` plus
  `tools: [<path>]`;
- declare stage reads and writes;
- declare verification criteria;
- declare whether the stage needs review;
- declare retry limits or human blockers.
- include `Pipeline Review Status`, initially `awaiting_user_review`, with
  approval fields that must be populated before `task-orchestrator.md` runs.

After writing `pipeline_design.md`, the planner stops for user review. Stage
brief generation is a separate `task-orchestrator.md` phase.

### Phase 5: Stage Brief Generation

Superpowers reference: subagent implementer prompt with curated context.

AutoStudy translation: the Main Agent converts each `pipeline_design.md` stage
into precise executor and reviewer stage briefs.

Recommended structure:

```text
work_dir/
├── stage_briefs/
│   ├── <stage_id>_executor.md
│   ├── <stage_id>_spec_review.md
│   └── <stage_id>_quality_review.md
├── stage_results/
└── stage_reviews/
```

The stage brief is the subagent's true entry point. It must contain enough
context for one stage, but not the whole project history. Executor briefs are
always written; reviewer briefs are written when review is enabled.

Minimum fields:

```markdown
# Stage Brief: <stage_id> - <stage name>

## Role
executor | spec_reviewer | quality_reviewer

## Task
One-stage objective in concrete terms.

## Required Reads
- exact/path: why this file matters

## Allowed Reads
- task-relevant current-run files/directories the child is expected to inspect.
  This is not an exhaustive whitelist; forbidden reads below are the hard
  boundary.

## Forbidden Reads
- development docs and unrelated workbench files

## Writes
- exact/output/path: expected content

## Tool Guidance
- primary top-level tool skill path
- ordered top-level tool skill paths for the stage
- role of each selected tool in this stage
- appendix skill paths, if already selected by the Main Agent

## Quality Criteria
- measurable criterion

## Review Criteria
- spec compliance criteria
- artifact quality criteria

## Context From Previous Stages
Short summaries only; do not paste large artifacts unless necessary.

## Blockers And Escalation
When to report `NEEDS_CONTEXT` or `BLOCKED` instead of guessing.
```

### Phase 6: Subagent Dispatch And Review Loop

Superpowers reference: `subagent-driven-development`.

AutoStudy translation:

1. Main Agent dispatches one executor subagent with one stage brief.
2. Executor writes artifacts and `stage_results/<stage_id>_result.json`.
3. Main Agent dispatches a spec compliance reviewer if review is required.
4. Only after spec compliance passes, Main Agent dispatches a quality reviewer.
5. If a reviewer fails the stage, or if a reviewer finds a blocking
   auto-fixable concern, Main Agent writes or updates a fix brief and
   redispatches the executor, respecting retry limits.
6. If retry limits are exhausted, Main Agent records the remaining issue as a
   human review item only when it truly needs user input, manual action, or an
   unavailable external resource.

Review order matters:

```text
Spec compliance first: did we solve the right assignment?
Quality review second: is the solution well built?
```

This prevents polishing the wrong artifact.

Reviewers must classify every issue they find:

- `auto_fixable`: the agent can fix it with existing local context and allowed
  writes, such as rebuilding a zip after a notebook rerun, adding a missing
  report heading, or regenerating a derived artifact from already available
  files.
- `needs_user_input`: the agent needs information only the user can provide.
- `manual_only`: the issue requires human or real-world validation, such as live
  presentation/Q&A quality.
- `external_blocker`: a required external resource is unavailable, such as an
  official course style file that is not in the workbench.
- `acceptable_risk`: a non-blocking concern that should be surfaced but does not
  prevent `draft_ready`.

Spec hard requirements are blocking spec-compliance requirements. If the
authoritative assignment source says a final deliverable must/required/only do
something, or gives exact file, data, source, package, format, page/time, naming,
template, style, class, citation, or rubric-critical requirements, the pipeline
should declare `required_spec_constraints`. Missing evidence is a blocker, not
`acceptable_risk`. This is a no-downgrade rule: the requirement must remain
intact across `spec -> pipeline -> stage brief -> artifact -> verification`.
Fallback output is only preview/debug unless the authoritative spec explicitly
allows it as final.

When a review schema needs finer detail, split `auto_fixable` into
`blocking_auto_fixable` and `optional_polish`. A blocking auto-fixable issue is
one that affects a required deliverable, package parity, or final submission
readiness; it must not be left as `PASS_WITH_CONCERNS` and must not be converted
directly into `revision_needed`. The coordinator must dispatch a fix executor,
then rerun the relevant spec/quality reviews. Optional polish may remain as
`acceptable_risk` only when the review explicitly records `blocking: false` and
the artifact still meets the assignment requirements.

### Phase 7: Final Verification And User Handoff

Superpowers reference: `verification-before-completion`.

AutoStudy translation:

The Main Agent must gather evidence before telling the user a draft is ready.

Required outputs:

```text
verification_checklist.md
verification.log
result.json
```

`verification.log` records measured checks, for example:

```text
PASS | report.pdf exists | measured: 28642 bytes
PASS | report.pdf magic bytes | measured: %PDF
FAIL | rubric coverage | measured: criterion 3 missing
FAIL | spec requirement drift | measured: source=spec.md:178; pipeline=fallback renderer
SKIP | video upload | reason: requires user recording
```

Use `FAIL` only for a check that failed and requires repair, revision, user
input, or external resolution. If the measured evidence proves the correct
final status is `revision_needed` rather than `draft_ready`, record that as a
passing gate, for example:

```text
PASS | draft_ready withheld | measured: result_status=revision_needed; remaining_items=manual_or_external
```

Do not use a misleading `FAIL | draft_ready eligibility` line when withholding
`draft_ready` is the expected behavior.

For deliverables governed by `required_spec_constraints`, final verification
must check the exact evidence required by the source requirement. Generic checks
such as file existence, `%PDF` magic bytes, page count, image count, or notebook
JSON validity are insufficient when the spec demands more specific evidence. If
only a fallback artifact exists, the final status must be `revision_needed` with
the appropriate blocker, and the fallback output must be labeled as preview/debug
rather than as the final submission artifact.

Rendered PDF deliverables also need artifact-quality evidence, not only content
presence. For slides and reports, final verification should record `pdffonts`
and `pdftotext` output, check font embedding or the declared font strategy, and
scan for replacement-glyph symptoms such as Unicode replacement characters, tofu
boxes, or unexpected line-leading question marks. A slide deck whose Markdown
source uses normal list markers but whose PDF extraction shows line-leading
question marks is an `auto_fixable` render failure, not `draft_ready` evidence.
If a fallback renderer is used, the stage receipt must preserve the exact render
script/command and explain whether the output is final, preview, debug, or
superseded.

`result.json` is the task receipt used by later scans and sessions. It should
distinguish at least:

- `pipeline_ready`
- `draft_ready`
- `revision_needed`
- `submitted`
- `skipped`
- `error`

The Main Agent then asks the user whether to review, revise, submit, or stop.

## 6. Subagent Contracts

### Executor Subagent

Purpose: produce one stage artifact.

Allowed:

- read `stage_brief.md`;
- read files listed in required or allowed reads;
- inspect additional current-run artifacts only when they are directly relevant
  to the assigned stage or to validating declared outputs;
- read selected tool skill files named in the brief;
- write only declared outputs;
- report `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.

Forbidden:

- talk to the user;
- dispatch other subagents;
- read Development Plane docs;
- redesign the whole pipeline;
- write outside declared paths;
- hide uncertainty.

### Spec Compliance Reviewer Subagent

Purpose: verify that the artifact satisfies the assignment, rubric, and stage
requirements.

It must not trust the executor's report. It reads the actual artifact and the
brief, then compares against `spec.md`, rubric, and declared criteria.

Output:

```json
{
  "verdict": "PASS",
  "evidence": ["..."],
  "missing_requirements": [],
  "extra_or_unrequested_work": [],
  "fix_suggestions": []
}
```

or:

```json
{
  "verdict": "FAIL",
  "evidence": ["..."],
  "missing_requirements": ["..."],
  "extra_or_unrequested_work": ["..."],
  "fix_suggestions": ["..."]
}
```

### Quality Reviewer Subagent

Purpose: verify that a spec-compliant artifact is high quality for its type.

Quality checks depend on the artifact:

- code: execution, tests, structure, reproducibility;
- report: argument quality, evidence grounding, citation integrity, style;
- PDF: valid file, page count, rendering quality, no tofu CJK output, `pdffonts`
  / `pdftotext` checks, no replacement-glyph failures;
- slides: structure, visual coherence, export validity, font embedding or font
  strategy evidence, no unexpected line-leading question marks;
- notes: conceptual accuracy, useful organization, appropriate depth.

It runs only after spec compliance passes.

### Final Reviewer Subagent

Optional. Used for large tasks where the Main Agent wants a fresh read of all
stage results and deliverables before the user handoff.

It should check for cross-stage consistency, not redo every local review.

## 7. Runtime File Interfaces

Concrete examples live in `docs/examples/runtime/`:

- [`stage_brief-example.md`](examples/runtime/stage_brief-example.md)
- [`stage_result-example.json`](examples/runtime/stage_result-example.json)
- [`stage_review-example.json`](examples/runtime/stage_review-example.json)

### Task Workbench

For homework:

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
├── spec.md
├── problem.md
├── references/
│   └── <fetched external/source materials>
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   ├── review_a.json
│   ├── alignment_brief.md
│   ├── user_notes.md
│   └── user_scope.md
├── pipeline_design.md
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

For course-level tasks, `data/courses/<COURSE>/` has a different shape, but the
same principle applies: persistent source archive first, then derived outputs.

### `pipeline_design.md`

Task-level plan owned by the Main Agent.

It may be long and strategic. It can mention all stages and global dependencies.
It should not be handed to a subagent as its only instruction.

Example stage:

```markdown
### Stage 1 - Notebook Execution
- id: stage_01_notebook
- primary_tool: sub-skills/tools/code-writer.md
- tools:
  - sub-skills/tools/code-writer.md
  - sub-skills/tools/test-runner.md
- tool_roles:
  - code-writer: produce the notebook/source artifact
  - test-runner: execute notebook/tests and write verification evidence
- delegate: subagent
- review:
  - spec_compliance: true
  - quality: true
- max_retries: 1
- reads:
  - spec.md
  - investigation/rubric.md
  - references/
- writes:
  - draft/project.ipynb
  - draft/metrics.json
- quality_criteria:
  - notebook executes from a clean kernel
  - metrics used by later report stages are written to draft/metrics.json
- human_blockers:
  - dataset choice if the spec allows multiple datasets and user has not chosen
```

### Stage Brief Files

Stage-level instructions owned by the Main Agent and consumed by subagents.

Executor briefs use:

```text
stage_briefs/<stage_id>_executor.md
```

Reviewed stages also use:

```text
stage_briefs/<stage_id>_spec_review.md
stage_briefs/<stage_id>_quality_review.md
```

Each brief must be precise, bounded, and executable. If a subagent cannot do
the task by reading the brief and allowed files, the brief is incomplete.

### `stage_result.json`

Executor output receipt. Required fields:

```json
{
  "stage": "stage_02_report",
  "status": "DONE",
  "created_at_utc": "2026-06-04T14:20:00Z",
  "completed_at_utc": "2026-06-04T14:29:00Z",
  "executed_by": "subagent",
  "delegation_mode": "subagent",
  "delegation_deviation": null,
  "agent_id": "agent-id-or-null",
  "agent_id_source": "exact_runtime_id | unknown_to_child_at_write_time",
  "identity_authority": "stage_reviews/child_dispatch_ledger.json",
  "transcript": "transcript-handle-or-null",
  "transcript_export_path": "transcripts/stage_02_report_executor.md",
  "summary": "...",
  "outputs": [{"path": "draft/report.md", "size_bytes": 12345}],
  "commands_run": ["..."],
  "verification_evidence": ["..."],
  "concerns": []
}
```

`stage` is the canonical stage identifier and must match `pipeline_design.md`.
Do not rely on `stage_id` alone. A coordinator may preserve `stage_id` as a
compatibility alias, but it must normalize or reject receipts whose canonical
`stage` field is missing or inconsistent.

If a stage declared `delegate: subagent` but the Main Agent had to execute it
inline, set `executed_by: "main-agent"`, `delegation_mode: "inline_fallback"`,
and explain the reason in `delegation_deviation`.

For `delegation_mode: "subagent"`, the coordinator must treat its dispatch
return value as authoritative identity evidence. If a child receipt omits
`agent_id` but includes `agent_id_source:
"unknown_to_child_at_write_time"` and `identity_authority:
"stage_reviews/child_dispatch_ledger.json"`, the coordinator may normalize the
receipt to the dispatch id and record `identity_normalized_by_coordinator:
true`. If the child omitted both the id and the authority fields, normalization
is recovery and must be recorded as a process concern. If a child receipt
records an alias id such as `C4` or an `agent_id` that conflicts with the
dispatch id, the receipt is not accepted as clean evidence; the coordinator
must preserve the original value, reconcile it, supersede it with a replacement
child, or mark the stage `BLOCKED`.

Receipt normalization is a recovery path, not the happy path. If a validation
run requires normalization for many child receipts, record that as a process
concern and tighten the next child prompt/template so `stage`, timestamps,
role/status or verdict, `issue_classification`, `transcript`,
`transcript_export_path`, and either the exact `agent_id` or explicit
null-plus-authority identity fields are emitted by the child without
coordinator repair.

`created_at_utc` and `completed_at_utc` are required for stage results. They
make repair loops and review ordering auditable without relying on transcript
order alone.

When the coordinator hits a child-thread or open-descendant limit, it may close
completed children only after the dispatch ledger has preserved stable ids,
receipt paths, final statuses, and transcript export status. Closing completed
children is lifecycle management; it must not erase the evidence needed for
later receipt or transcript audit.

`transcript_export_path` is optional only when the platform cannot export full
child transcripts. In that case, keep `transcript` as the stable handle and
document the export limitation in the coordinator summary.

Conditional stages whose trigger is false still write a result receipt:

```json
{
  "stage": "stage_04_package_repair",
  "status": "SKIPPED",
  "created_at_utc": "2026-06-04T15:00:00Z",
  "completed_at_utc": "2026-06-04T15:00:00Z",
  "skip_reason": "package/current-file hashes already match",
  "trigger_evidence": ["stage_03_package_spec_review.json verdict=PASS"],
  "executed_by": null,
  "delegation_mode": "skipped",
  "delegation_deviation": null,
  "agent_id": null,
  "transcript": null
}
```

### `stage_review.json`

Reviewer output receipt. Required fields:

```json
{
  "stage": "stage_02_report",
  "review_type": "spec_compliance",
  "created_at_utc": "2026-06-04T14:30:00Z",
  "completed_at_utc": "2026-06-04T14:34:00Z",
  "depends_on_stage_result": "stage_results/stage_02_report_result.json",
  "depends_on_spec_review": null,
  "agent_id": "agent-id-or-null",
  "agent_id_source": "exact_runtime_id | unknown_to_child_at_write_time",
  "identity_authority": "stage_reviews/child_dispatch_ledger.json",
  "transcript": "transcript-handle-or-null",
  "transcript_export_path": "transcripts/stage_02_report_spec_review.md",
  "verdict": "PASS",
  "evidence": ["..."],
  "issue_classification": {
    "auto_fixable": [],
    "needs_user_input": [],
    "manual_only": [],
    "external_blocker": [],
    "acceptable_risk": []
  },
  "missing_requirements": [],
  "extra_or_unrequested_work": [],
  "fix_suggestions": []
}
```

`stage` is required here too and must match the reviewed stage. Review receipts
with only `stage_id` are schema drift; the coordinator must normalize them
before counting the review complete.

Review receipts with legacy `created_at` but no `created_at_utc` are schema
drift. The coordinator may preserve `created_at` as a compatibility alias, but
accepted receipts must contain UTC timestamp fields before final verification.

For `review_type: "quality"`, `depends_on_spec_review` must point to the
passing `stage_reviews/<stage_id>_spec_review.json`. This makes review ordering
auditable from files even when subagent transcripts are unavailable.

If spec compliance fails, the Main Agent must not run a normal quality review.
It may still write a quality `SKIP` audit receipt with `skip_reason` and
`depends_on_spec_review` pointing to the failed spec review. A quality `SKIP`
receipt is evidence that quality review was intentionally withheld; it is not a
quality pass and must not unblock `draft_ready`.

For conditional stages skipped before execution, write explicit review `SKIP`
receipts for any declared reviews when those review files are expected by the
pipeline. This keeps "every declared stage/review has a receipt" auditable
without reading coordinator prose.

`result.json.status: "revision_needed"` is reserved for remaining issues after
the coordinator has exhausted allowed automatic repairs. It is appropriate for
user input, manual-only work, or unavailable external resources. It is not
appropriate for known auto-fixable artifact issues that the current agent could
repair before handoff.

## 8. Forbidden Context Rules

Runtime agents should not read these as task instructions:

- `AGENTS.md` if a local ignored developer override exists at the repo root
- `docs/DEVELOPMENT.md`
- `docs/ROADMAP.md`
- `docs/COLLABORATION.md`
- `docs/progress/agent-progress.md`
- `docs/plans/feature-list.json`
- `docs/superpowers/specs/*`
- `docs/superpowers/plans/*`
- pipeline trace audits
- reference comparison documents
- external workflow/plugin skill files unless a runtime brief explicitly lists
  them as required for that assignment stage

Exception: a development session may read those files when modifying AutoStudy
itself. That is Development Plane work, not runtime task execution.

Subagents are stricter than the Main Agent. A subagent should read only the
files named in its brief.

## 9. Design Implications For Existing Docs

This protocol should eventually drive these updates:

- `skill.md`: stay as runtime entry and safety router; do not grow into a
  development history document.
- `do-homework.md`: become the Main Agent coordinator contract.
- `task-orchestrator.md`: become the Main Agent stage-brief and subagent-review
  loop contract.
- `docs/skills-architecture-spec.md`: reference this protocol for stage brief
  and review design.
- `docs/ROADMAP.md`: point to this protocol as the current M3.5 execution
  architecture direction, but stay in the Development Plane.

## 10. Open Design Questions And Decisions

1. Should stage briefs be generated as Markdown only, or Markdown plus a
   machine-readable JSON sidecar?
2. Decision: every stage writes a `stage_results/<stage_id>_result.json`
   receipt, including conditional stages skipped with `status: "SKIPPED"`.
   Reviewed stages also write
   `stage_reviews/<stage_id>_spec_review.json`; if quality review is enabled,
   they write `stage_reviews/<stage_id>_quality_review.json` or explicit
   `SKIP` receipts when review is intentionally withheld or the stage trigger is
   false.
3. How much of `spec.md` should be summarized into each stage brief versus
   referenced as a required read?
4. Should course-level flows (`sync-course`, `write-course-notes`) use the same
   stage brief protocol, or a lighter fixed-pipeline variant?
5. Which artifact types need specialized quality reviewer templates first:
   code, report, PDF, slides, or notes?
