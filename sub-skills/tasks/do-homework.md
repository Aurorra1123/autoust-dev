---
name: do-homework
description: Homework planning workflow. Use when the user asks "complete X assignment", "do my paper for DLED3020", "帮我做 lab 5". Runs Canvas Generic-style reconnaissance, aligns with the user, writes a reviewable per-assignment pipeline, and stops before execution.
---

# Do Homework

Use this task when the user asks AutoStudy to work on one Canvas assignment and
produce a reviewed execution plan. It is the planning half of the homework
workflow; draft production is handled later by `tasks/task-orchestrator.md`
only after the user approves the pipeline. Typical user requests:

- "帮我做 DLED3020 的 Paper Critique"
- "complete DSAA2043 Lab Assignment 1"
- "做一下 UCUG1077 的 group presentation slides"
- "写 DSAA2012 的 project report"

The runtime contract is:

1. resolve one Canvas assignment;
2. build a workbench with current evidence;
3. investigate Canvas sources before drafting;
4. align with the user on choices Canvas cannot decide;
5. design a concrete stage pipeline;
6. stop for human pipeline review before any executor/reviewer subagents run.

Required artifact chain:

```text
prelaunch_startup_inventory.json
-> investigation/explore_manifest.json
-> investigation/scout_results/ (if scouts dispatched)
-> investigation/explore_context.md
-> investigation/source_candidates.json
-> investigation/reading_plan.json
-> investigation/source_body_audit_fragments/ (if content scouts dispatched)
-> investigation/source_body_audit.json
-> investigation/source_coverage_feedback.json
-> investigation/recon_summary.md
-> spec.md
-> investigation/rubric.md
-> references/
   -> fetched external/PDF/PPTX/source files and optional convenience exports
-> investigation/review_a.json
-> investigation/alignment_brief.md
-> pipeline_design.md
   -> Pipeline Review Status: awaiting_user_review
-> result.json
```

Actor rules:

- The Main Agent owns the task lifecycle and is the only actor that talks to the
  user.
- Subagents are temporary workers with curated prompts, bounded reads/writes,
  and receipt requirements.
- Subagents can scout during this planning workflow, but executor/reviewer
  subagents belong to `task-orchestrator.md`, not `do-homework.md`.
- Subagents do not own user alignment, final `spec.md` judgment, pipeline
  approval, or Canvas submission decisions.
- The Main Agent reviews `source_candidates.json`, approves
  `reading_plan.json`, dispatches `content_scout` Subagents, reads Subagent receipts, and
  merges content-scout fragments into `source_body_audit.json`. The Main Agent
  writes final `spec.md`, `review_a.json`, `explore_context.md`, and
  `pipeline_design.md`.
- Subagents must not write final `spec.md`, final `review_a.json`,
  `pipeline_design.md`, or user alignment decisions.

## Clean-Start Proposal Runtime Checklist

For clean-start proposal, research, or open-ended homework, read this checklist
before the longer flow below. It is the shortest contract for the behavior that
must happen at runtime.

1. Dispatch real child subagents for the three required source Subagent roles:
   `metadata_scout`, `content_scout`, and `coverage_reviewer`. Each required
   child needs a real dispatch id in `stage_reviews/child_dispatch_ledger.json`
   and a receipt path under `investigation/scout_results/`.
2. STOP before `[B]` unless all three required child subagents have real dispatch ids.
   Main-Agent source indexing, manual JSON writing, or a summary paragraph is
   recovery evidence only; it is not a successful child dispatch.
3. `metadata_scout` writes or returns the payload for
   `investigation/source_candidates.json`; `content_scout` writes or returns
   source-body fragment payloads; `coverage_reviewer` reviews after
   `source_body_audit.json` and content receipts exist.
4. A `recover` from `coverage_reviewer` is a gate failure until coverage is re-run by a child subagent.
   The Main Agent may materialize missing artifacts named by the reviewer, but
   it must not self-certify the final coverage verdict.
5. Write `investigation/recon_summary.md` as the human-readable entrance to reconnaissance.
   JSON files are machine evidence, not the user-facing completion story. The
   user-facing recon summary must state the source trail, deliverables, missing
   user decisions, skipped/recovered children, and the next question. Scale the
   amount of user-facing detail with reconnaissance depth: a tiny one-source
   task can have a short summary, but a multi-source run with several scouts,
   PDFs, timelines, methods guidance, source conflicts, or non-blocking gaps
   must expand the summary enough that the user can see the important findings
   without opening audit JSON.
6. Do not turn "simulate I am the user" into Main-Agent permission to choose the project direction.
   In normal runtime, ask the real user at `[B]`. In development validation,
   use the documented simulated-user bridge or a startup prompt that explicitly
   supplies delegated choices. If the assignment direction is open and not
   delegated, stop at `[B]` instead of writing `alignment_brief.md`.

The two user-interaction phases in this planning workflow are:

1. `[B]` after reconnaissance, where the user can add group info, oral
   instructions, dataset choice, scope, or stop.
2. `[C5]` after `pipeline_design.md` is written, where the user reviews the
   planned execution pipeline and decides whether to approve, revise, or stop.

Run mode:

- Clean start: no retained user-visible draft; enable source/spec exploration
  unless the task qualifies for recorded inline fallback.
- Retained-artifact start: current user-visible draft or prior output exists;
  enable only the artifact/history/codebase/verification scouts whose inputs
  exist and affect planning.

## Preconditions

Before running, check the same set as `sync-status.md`:

1. `.venv/bin/canvascli version` returns 0.
2. `.venv/bin/canvascli whoami` returns 0.

If either fails, redirect to `tools/canvascli-setup.md` step 3 and stop.

If the user has not named a specific assignment, run `sync-status.md` first to
surface options, then come back here.

## Execution Flow

### [A] Build The Assignment Workbench

No user interaction in `[A]`.

Runtime goal: create a current workbench that can answer three questions before
planning starts:

1. What exact Canvas assignment is this?
2. Which sources prove the requirements and deliverables?
3. Which choices still need user alignment?

Do not treat an assignment title, Canvas description, or single link as the full
problem statement unless the fetched source evidence proves it is complete.

#### [A0] Startup Inventory Rule

Before reading old workbench files as task context, write or refresh:

```text
prelaunch_startup_inventory.json
```

For a direct request with no workbench yet, first resolve the assignment and
create the workbench in `[A1]`/`[A2]`, then write this file before reading any
old active workbench evidence.

It must state:

- current user request;
- resolved course/assignment if already known;
- retained user-visible artifacts, if any;
- current source/spec/reference files allowed for this run;
- prior history files explicitly allowlisted for a process-history scout;
- forbidden context, including old stage receipts, transcripts, prior reviews,
  stale pipeline files, old diagnostics, and archive contents unless explicitly
  allowlisted;
- stale process files archived or excluded from active context.

Old process evidence is not task context by default. A scout may inspect it only
when `prelaunch_startup_inventory.json` allowlists the exact file or directory
and explains why it affects current planning.

#### Explore Mode Rules

Apply these rules after `[A2]` creates the workbench and before `[A3]`
finishes reconnaissance.

Write the explore decision to `investigation/explore_manifest.json` before
entering `[B]`.

Use these rules:

| Situation | Required action |
|---|---|
| Canvas modules, linked files, PDFs, external specs, rubric search, or multiple possible sources must be inspected | The Main Agent marks `source_spec` as the source/spec exploration domain. Do not dispatch or accept a `source_spec` Subagent as a completed child; use the concrete Subagent roles below. |
| Non-trivial source-heavy homework needs broad Canvas/source indexing | Dispatch `metadata_scout` to write `source_candidates.json`. |
| Required or high-signal candidates need body reading | Dispatch `content_scout` Subagents with explicit `scope` values from `reading_plan.json`. |
| Proposal/research/open-ended or other multi-source tasks need coverage checking | Dispatch `coverage_reviewer` after `content_scout` Subagent receipts exist. |
| Retained user-visible draft, source code, package files, previous result, or current checks exist and affect planning | Enable only the matching artifact/codebase/process-history/verification scouts. |
| A scout input does not exist or does not affect planning | Mark that scout `SKIPPED` with a reason in `explore_manifest.json`. |
| The task is tiny and mechanically obvious, or child dispatch is unavailable/blocked | Main Agent may do inline exploration, but must record `delegation_mode: "inline_fallback"` or `executed_by: "main-agent"` with the concrete reason. |

A read-only scout is a Subagent role that independently discovers or verifies
current task facts for the Main Agent. It writes a receipt under
`investigation/scout_results/<scout_type>_result.json`. It does not talk to the
user, write the dispatch ledger, own `spec.md`, or read archive/prior-run
evidence unless the Main Agent explicitly allowlists a process-history input.

Main Agent / Subagent naming rules:

- `source_spec` is a Main Agent exploration domain, not a dispatchable Subagent
  role and not a completed child result. It may appear in legacy manifests only
  as a domain label; it must not have a successful dispatch id or receipt path.
- A non-trivial source-heavy run must dispatch real child subagents with
  `scout_type` values `metadata_scout`, `content_scout`, and
  `coverage_reviewer`.
- Main Agent inline recovery must be recorded as recovery evidence, not as a
  Subagent receipt. If a child Subagent times out or cannot be dispatched, the Main
  Agent may recover only by writing a process concern and marking the scout as
  `RECOVERED_INLINE_AFTER_TIMEOUT`, `INLINE_FALLBACK`, or equivalent. Do not
  call that a successful Subagent dispatch.
- `content_scout` is the Subagent role. Content subdivisions are `scope` values,
  not child identities: `spec_content`, `methods_content`, `theme_content`, and
  `policy_content`. Do not create successful child identities named
  `spec_content_scout`, `methods_content_scout`, `theme_content_scout`, or
  `policy_content_scout`; if legacy names appear, normalize them to
  `scout_type: content_scout` plus the matching `scope`.
- Main Agent summary is not a Subagent receipt. The Main Agent approves
  `reading_plan.json`, reads narrowed source bodies after children return,
  merges fragments into `source_body_audit.json`, writes final `spec.md`,
  `review_a.json`, `explore_context.md`, and asks the user at `[B]`.

Source/spec exploration uses three bounded Subagent roles when the task is not
tiny:

- `metadata_scout` indexes assignment, rubric, front page, syllabus, modules,
  every module item, pages, file metadata, assignment files, and external URLs.
  It writes `investigation/source_candidates.json` and may rank candidates as
  `required`, `high_signal`, `supporting`, `low_signal`, `forbidden`, or
  `blocked`. It must not mark a source as `precise_match` because it has not
  read source bodies.
- `content_scout` reads only the candidates assigned in
  `investigation/reading_plan.json`. Typical `scope` values are
  `spec_content`, `methods_content`, `theme_content`, and
  `policy_content`. Content scouts extract source body evidence, preserve
  source-adjacent companion artifacts, and write receipts plus fragments under
  `investigation/source_body_audit_fragments/`. The Main Agent merges content-scout fragments
  into `investigation/source_body_audit.json`; parallel content scouts must not
  write the shared merged audit file directly.
- `coverage_reviewer` cold-reads `source_candidates.json`,
  `reading_plan.json`, `source_body_audit.json`, content receipts,
  `references/`, and `unreachable.txt` to check for missed high-signal sources,
  forbidden reads, metadata-only evidence, and open-ended assignment coverage.

`content_scout` Subagents narrow the read set; they do not replace Main Agent source reading.
Subagent summaries are routing hints, not source evidence. The Main Agent still
owns final reconnaissance judgment: after reading Subagent receipts, it must read
the narrowed source bodies before writing or revising `spec.md`, decide the main
spec, write or revise `spec.md`, consolidate `investigation/explore_context.md`,
and run `[B]`.

Before returning from reconnaissance, run a reconvergence gate. coverage
feedback is not a terminal reconnaissance verdict: `source_coverage_feedback.json`
may say the source set is covered, but the Main Agent still must write or verify
`spec.md`, `investigation/rubric.md`, and `investigation/review_a.json`. If
`source_body_audit.json` or `source_coverage_feedback.json` exists but any
terminal reconnaissance artifact is missing, the coordinator must not silently
stop or proceed to `[B]`; it must write a recover/blocking `review_a.json` or
`stage_reviews/process_concerns.jsonl` entry that names the missing
`spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` artifact
and the next recovery action.
Rule for automated checks: missing `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` must write a recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`.

If any scout is dispatched, the Main Agent records it in
`stage_reviews/child_dispatch_ledger.json` with role `explore_scout`, scout
type, prompt/brief path, receipt path, dispatch id, and timestamps.

Scout evidence must satisfy the same child-evidence contract used later for
executor/reviewer children:

- ledger row is written before waiting on the child;
- dispatch return id is the identity authority;
- receipt includes `created_at_utc`, `completed_at_utc`, status, reads, writes,
  findings, concerns, and dependency notes;
- coordinator records when the receipt was observed and accepted;
- transport failures, child-side ledger writes, identity normalization, or
  inline fallback are process concerns, not silent success.

If inline fallback is used for a non-tiny task, state in
`explore_manifest.json` that child isolation was not exercised for that scout.

#### Explore Context Minimum

Before `[B]`, write `investigation/explore_context.md` for every non-trivial
run. This file is the stable downstream context for later agents. It must
summarize:

- resolved course and assignment;
- current Canvas/source requirements;
- main spec candidates and final main-source judgment;
- fetched references and blocked/unreachable materials;
- source candidates, body-read audit coverage, and any reading budget concerns;
- available user-visible artifacts, if any;
- skipped scouts and reasons;
- stale or forbidden context that must not be passed to later children;
- planning risks and verification risks;
- user decisions needed at `[B]`.

Also write `investigation/recon_summary.md` before `[B]`. This is the
human-readable entrance for the user and reviewer. It must be concise but
depth-adaptive: summarize lightly when the investigation was light, and expand
when the investigation read multiple source bodies, dispatched multiple scouts,
downloaded PDFs/decks, found methods/timeline guidance, or identified conflicts
and non-blocking gaps. It must include:

- the source trail in plain language;
- deliverables and grading/rubric status;
- required child subagents dispatched, skipped, recovered inline, or blocked;
- whether coverage was re-run after any reviewer `recover`;
- the concrete high-signal findings from each important source body, not only
  the file title;
- source conflicts, timing differences, missing templates, blocked sources, and
  other non-blocking gaps that may affect alignment;
- user-owned decisions still needed before planning;
- the exact next `[B]` question or stop reason.

Depth scaling guidance:

- For a one-source or mechanically obvious assignment, 4-6 lines may be enough.
- For a non-trivial proposal/research/open-ended task, include separate bullets
  for main spec, methods/topic guidance, timeline/calendar facts, rubric or
  policy constraints, and gaps.
- If a PDF, deck, syllabus, or page was important enough to send to a
  `content_scout`, the recon summary must surface the source's key actionable
  findings, such as required sections, method options, timeline, formatting, or
  policy constraints. Do not collapse it into "supporting context checked."
- If coverage feedback records downstream gaps, reflect those gaps in
  `recon_summary.md` and in the chat summary at `[B]`.

Do not make users read `source_candidates.json`, `source_body_audit.json`,
`source_coverage_feedback.json`, or `review_a.json` to understand run status.
Those JSON files are audit evidence.

Do not pass raw old logs, archive files, prior reviews, or prior pipeline files
to executor/reviewer children just because a scout inspected them. Only distilled
current-run findings in `explore_context.md`, `spec.md`, or the confirmed
terminal agreement become normal downstream context.

#### [A1] Resolve Identifiers

Resolve the request to a `(course_id, assignment_id)` pair.

Preferred path after `sync-status`: if the user chose "plan item N", run:

```bash
.venv/bin/python scripts/select_plan_item.py --index <N> --pretty
```

Use the selector JSON directly:

```text
course_id
assignment_id
assignment_name
suggested_work_dir
recommended_action
existing_result_path
```

Do not re-match by title when this object exists.

Action handling:

| `recommended_action` | Behavior |
|---|---|
| `recon` | Continue to `[A2]`. |
| `review_or_execute` | Read `existing_result_path`, `suggested_work_dir`, and `pipeline_design.md`; help the user review or approve the existing pipeline. Do not rerun reconnaissance and do not execute stages inside `do-homework`. If the user approves, hand off to `task-orchestrator.md`. |
| `review_or_submit` | Read `existing_result_path` and `suggested_work_dir`; help the user review, revise, or submit the existing draft instead of re-running reconnaissance by default. |
| `continue` | Inspect the previous error `result.json`; ask whether to retry before doing new work. |
| `manual_review` | Stop before `[A3]`; tell the user this item likely needs manual Canvas interaction. |

Direct natural-language path: if the user says "DLED3020 Paper Critique"
without coming from a plan item, match against `data/sync/current/assignments.json` by
case-insensitive substring of `name` and course code in `context_name`. If
ambiguous, surface the candidates at `[B]`.

#### [A2] Create The Workbench

```bash
mkdir -p "data/homework/<COURSE>/<HWID>"
```

If the request came from `scripts/select_plan_item.py`, use
`suggested_work_dir` exactly so local result tracking and future scans point to
the same workbench.

Target structure:

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
├── prelaunch_startup_inventory.json
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── explore_context.md
│   ├── explore_manifest.json
│   ├── scout_results/
│   ├── source_body_audit_fragments/
│   ├── source_body_audit.json
│   ├── source_coverage_feedback.json
│   ├── recon_summary.md
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
│   ├── child_dispatch_ledger.json
│   └── process_concerns.jsonl
├── transcripts/
├── draft/
│   ├── figures/
│   └── render/
├── verification_checklist.md
├── verification.log
└── result.json
```

After creating directories, compute the repository root for downstream path discovery:

```bash
REPO_ROOT="$(git -C 'data/homework/<COURSE>/<HWID>' rev-parse --show-toplevel)"
echo "repo_root: ${REPO_ROOT}"
```

This `REPO_ROOT` will be injected into `pipeline_design.md` metadata at [C].
All skill file paths resolve as `REPO_ROOT/sub-skills/tools/<name>.md`.

#### [A3] Canvas Generic Reconnaissance - Mandatory

Invoke `tools/assignment-recon.md` as the source/spec workflow. This is a Main
Agent source/spec exploration domain and may be supported by the concrete
Subagent roles `metadata_scout`, `content_scout`, and `coverage_reviewer`, but
it must not be replaced by a
standalone spec-generation script. The Main Agent must read the current
evidence, including the narrowed original source bodies or exact source windows
identified by scouts, judge the main spec, write `spec.md`, and keep review
evidence in the workbench.

Follow the Canvas Generic stages:

1. **Stage 1 fetch-context**
   Read assignment, rubric, front page, syllabus, modules, every module's items,
   relevant pages, attached files, and external URLs through atomic
   `canvascli` commands. Syllabus is a first-class source, not an optional
   afterthought: read it and record whether it adds grading criteria,
   assessment-family context, submission/late policy, academic-integrity rules,
   AI/tool policy, collaboration rules, or no relevant constraints. Save raw
   JSON under `canvas/`. For Canvas-native bodies, raw Canvas JSON is the
   canonical evidence; derived readable artifacts are optional convenience
   copies, not required gates. summary-only scout output must never replace raw
   Canvas JSON. Then write a standardized `spec.md` report with
   metadata, source trail, syllabus relevance, main spec judgment, deliverables,
   requirements, rubric placeholder, inputs, gaps, and evidence pointers.

2. **Stage 2 find-rubric**
   Search Canvas rubric, `spec.md`, downloaded/fetched references, modules,
   syllabus, and external spec text. Write `investigation/rubric.md`. Do not
   mark rubric search complete until syllabus has either contributed criteria or
   been explicitly judged irrelevant/unavailable. If the syllabus contributes
   criteria, `investigation/rubric.md` must cite `canvas/syllabus.json` raw
   body-text section pointers; a scout summary alone is incomplete.

3. **Stage 3 locate-inputs**
   Download or fetch necessary PDFs, Google Doc text, starter code, datasets, or
   external spec pages into `references/`. Record blocked resources in
   `investigation/unreachable.txt`. For every fetched PDF that may affect the
   spec, save PDF link annotation manifests as
   `references/*.pdf.links.json` or nested
   `references/**/*.pdf.links.json`; do not treat PDF text extraction as complete
   until the visible text and embedded link annotations have both been checked.
   Write `investigation/source_candidates.json`,
   `investigation/reading_plan.json`, and
   `investigation/source_body_audit_fragments/`; then merge fragments into
   `investigation/source_body_audit.json` and write
   `investigation/source_coverage_feedback.json` so metadata discovery is
   separated from body-read evidence. Revise `spec.md` if fetched inputs change
   the main spec judgment.

4. **Stage 4 review investigation**
   Run a cold review of `spec.md`, `investigation/rubric.md`, `references/`,
   `investigation/unreachable.txt`, `investigation/source_candidates.json`,
   `investigation/reading_plan.json`, `investigation/source_body_audit.json`,
   `investigation/source_coverage_feedback.json`, and `content_scout` Subagent receipts.
   Prefer a separate reviewer/sub-agent when available. Write strict JSON to
   `investigation/review_a.json`.

5. **Stage 5 classify-output**
   Classify the output mode (`doc_prose`, `pdf_annotated`, `pdf_typed`, `code`,
   `form_answers`, `slides`, or `mixed`) and write the preliminary first line of
   `pipeline_design.md`.

After `[A3]`, immediately read:

```text
investigation/explore_manifest.json
investigation/explore_context.md  # required for non-trivial runs unless inline fallback is recorded
investigation/source_candidates.json
investigation/reading_plan.json
investigation/source_body_audit_fragments/  # if content scouts dispatched
investigation/source_body_audit.json
investigation/source_coverage_feedback.json
investigation/recon_summary.md
canvas/assignment.json
canvas/syllabus.json
canvas/page-*.json               # if present and relevant
spec.md
investigation/rubric.md
investigation/unreachable.txt
investigation/review_a.json
pipeline_design.md
problem.md
```

Do not proceed to `[B]` until:

- `explore_manifest.json` accounts for every enabled, skipped, or inline scout.
- Non-trivial runs have `explore_context.md`, or a recorded inline-fallback
  reason.
- Every dispatched scout has a ledger row and a receipt path.
- Clean-start proposal/research/open-ended source-heavy runs have real
  dispatch ids for `metadata_scout`, `content_scout`, and
  `coverage_reviewer`; if any role was done by the Main Agent, record a recovery
  concern and do not call the run clean child-isolation evidence.
- Non-trivial source-heavy runs have `source_candidates.json`,
  `reading_plan.json`, `source_body_audit.json`, and
  `source_coverage_feedback.json`, or a recorded inline fallback reason.
- If `coverage_reviewer` returned `recover`, the missing artifacts were
  materialized and a child `coverage_reviewer` was re-run to `proceed`; Main
  Agent reconvergence cannot upgrade reviewer `recover` to final coverage
  success by itself.
- `investigation/recon_summary.md` exists and gives a user-readable status plus
  the next `[B]` question or stop reason.
- The reconvergence gate has checked terminal reconnaissance artifacts:
  `source_coverage_feedback.json` alone is insufficient, and missing `spec.md`,
  `investigation/rubric.md`, or `investigation/review_a.json` must write a
  recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`.
- `spec.md` is grounded in Canvas snapshots and fetched references, not in the
  assignment title alone.
- `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json`
  explicitly records syllabus relevance, including assignment requirements,
  grading criteria, submission policy, late policy, AI/tool policy,
  academic-integrity constraints, or a reasoned `not relevant` judgment.
- If syllabus was fetched and used, `spec.md`, `investigation/rubric.md`, or
  `review_a.json` points to `canvas/syllabus.json` raw body sections. Do not
  require `references/*syllabus*` as the evidence gate.
- If Canvas-native assignment, syllabus, front-page, or page bodies are relevant,
  source-body audit records raw `canvas/*.json` paths and section pointers;
  summary-only scout output is incomplete and blocks progression.
- If content scouts narrowed long PDFs, decks, Canvas bodies, or external text to
  exact files/pages/slides/windows, the Main Agent has read those source bodies
  or windows directly before finalizing `spec.md`; scout summaries alone are not
  sufficient.
- Any fetched PDF that was used as spec, rubric, input, or source-context
  evidence has a sibling PDF link annotation manifest under
  `references/*.pdf.links.json` or `references/**/*.pdf.links.json`, even when
  the manifest is empty.
- `proposal/research/open-ended` runs have body-read evidence for assignment/spec
  sources and methods/topic-selection guidance, or `review_a.json` records why
  such guidance is unavailable. They also record whether supporting topic context
  was checked or explicitly judged unnecessary, and whether the reading budget
  stayed bounded or required a justified overrun.

#### [A4] Gate On Reconnaissance Quality

If `review_a.json.verdict` is not `proceed`, or `spec.md` does not clearly
state deliverables and main source judgment, `[B]` is limited to recovery,
supplement, or stop. Surface this recovery prompt:

> "I checked the assignment page, rubric, course front page, syllabus, modules,
> pages, linked files, and external URLs, but I still could not identify a
> complete spec. Options: paste the spec text or URL, point me to the correct
> module/page/file, or stop for now."

Do not proceed to `[C]` until the supplied recovery material has been saved to
the workbench and `spec.md`, `investigation/review_a.json`, and
`investigation/explore_context.md` have been updated.

If syllabus could not be fetched, record the failure in `investigation/unreachable.txt`
or `stage_reviews/process_concerns.jsonl` before `[B]`. If syllabus was fetched
but not reviewed for relevance, treat the reconnaissance as incomplete and do
not proceed to `[B]`. If syllabus was fetched and reviewed but the only
downstream evidence is a lossy scout summary without raw `canvas/syllabus.json`
section pointers, treat the reconnaissance as incomplete.

### [B] Recon Summary + Alignment Loop

User-interaction phase #1.

Read `spec.md` first, then `investigation/explore_context.md`,
`investigation/recon_summary.md`, `investigation/review_a.json`, `investigation/rubric.md`,
`investigation/unreachable.txt`, `pipeline_design.md`, and `problem.md`.
Summarize with depth-adaptive detail. Use 4-6 lines only when the investigation
was genuinely simple. For non-trivial proposal/research/open-ended work, or any
run with multiple high-signal source bodies, several content scouts, downloaded
PDFs/decks, timelines, methods guidance, conflicts, or non-blocking gaps, give
the user a fuller summary with enough substance to understand the investigation
without opening the workbench:

- Course + assignment name + due date + points.
- Source trail and main spec judgment. Example: "assignment page was empty;
  a module item contained the project guidelines PDF."
- Key findings from each high-signal source body read by content scouts,
  including methods/topic guidance, timeline/calendar facts, required sections,
  formatting, and policy constraints when present.
- Syllabus relevance: constraints found there, or why it did not add
  assignment-specific requirements.
- Concrete deliverables and tasks.
- Rubric or grading criteria if found; say "Canvas rubric not found" if only
  spec-based criteria exist.
- Conflicts and non-blocking gaps from `source_coverage_feedback.json` or
  `review_a.json`, such as date conflicts, blocked pages, absent rubrics, or
  sparse slide templates.
- Output mode from `pipeline_design.md`.
- The user-decision areas you may need to align before starting, such as group
  ID, partner names, dataset choice, project concept, argument, creative
  direction, personal experience, oral instructor notes, scope, style, video
  recording, or blocked external resources.

This recon summary is not a second investigation and not a design proposal. It
is the compact user-facing view of `[A]` outputs: `spec.md`,
`investigation/explore_context.md`, `investigation/rubric.md`, `investigation/review_a.json`,
`investigation/unreachable.txt`, `references/`, `problem.md`, and the
preliminary output-mode line in `pipeline_design.md`. Its job is to tell the
user what Canvas fixed, what the sources prove, and which decisions still belong
to the user before planning.

Even when `review_a.json.verdict == "proceed"`, this checkpoint is mandatory.
`proceed` means the Canvas materials are sufficient to understand the assignment
surface. It does not mean the user's intended direction is aligned.

Runtime/user boundary:

- In normal `do-homework` runtime, the Main Agent asks the real user at `[B]`.
- In development validation, only `SIMULATED_USER_ANSWER_B_ROUND_<N>`,
  `SIMULATED_USER_ALIGNMENT_CONFIRMATION`, or explicit startup-prompt
  supplements count as simulated user input.
- A request phrased as "simulate I am the user" means exercise the runtime path;
  it does not let the Main Agent invent the user's topic choice, research
  question, group facts, approval, or alignment confirmation.
- If no valid user or simulated-user answer exists for an open assignment
  direction, stop after the recon summary and ask the `[B]` question.

The goal of `[B]` is not to classify the assignment into rigid "simple" or
"open" categories. The Main Agent must keep asking only while the current
information is not enough to start without guessing the user's core intent. For
straightforward assignments this may be one short confirmation. For open-ended
assignments, continue the loop until the Main Agent can write a stable
`alignment_brief.md` and defend why the next pipeline will not drift away from
the user's intent or project skeleton.

For open-ended projects, `[B]` has a required alignment loop:

1. Ask one clarifying question at a time.
2. After each answer, infer what new design dimensions the answer introduces.
3. Once enough raw intent is known, propose 2-3 viable approaches with
   trade-offs and a recommendation, then ask the user to choose or correct.
4. Present a concise design skeleton before the final brief.
5. Self-review the skeleton and brief for gaps, contradictions, ambiguity, and
   scope drift before asking for confirmation.

If the assignment asks the user to choose a project direction, dataset,
architecture, creative concept, user experience, research question, or other
open design variable, do not write `alignment_brief.md` until the missing
variable is either confirmed by the user or explicitly delegated to the Main
Agent and recorded as delegated.

#### [B1] Ask The Most Important Alignment Question

Before every question, run this internal alignment audit:

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
projects, also run this design skeleton readiness audit:

```text
Can I sketch these without guessing?

1. User-facing experience: who uses it, what happens first, what is the loop?
2. Creative or intellectual stance: tone, thesis, novelty, audience impact.
3. Core inputs and outputs: data/files/media/API inputs and final artifacts.
4. Architecture: main components, state, dependencies, and boundaries.
5. Model/tool contract: providers, request/response shape, mocks, probes, and
   secret handling if models/APIs are involved.
6. Traceability: what steps must be observable for debugging, grading, or demo.
7. Failure and fallback behavior: what happens when APIs, files, renders,
   tests, or external resources fail.
8. Verification and demo: how the result will be tested, shown, and reviewed.
```

If a missing skeleton answer would change the pipeline shape, stage boundaries,
tool choice, deliverable quality criteria, or user-facing experience, it is not
a minor default. Ask about it before writing the terminal brief.

Record the skeleton readiness result in `investigation/user_notes.md` under the
current round. Include which dimensions are fixed, delegated, not applicable, or
still blocking.

If any missing answer can change the assignment's direction, ask one question:
the single question that most reduces direction-drift risk. Do not ask a batch
of questions. Do not ask low-impact style or formatting questions while a core
topic, dataset, argument, project concept, method, scope, or personal stance is
still unclear.

Question priority:

1. Core direction choices: topic, dataset, project concept, thesis, research
   question, method, framework, or target audience.
2. User-owned material: personal experience, viewpoint, aesthetic preference,
   group context, oral instructor notes, or presentation intent.
3. Execution blockers: missing file, blocked URL, missing group info, ambiguous
   scope, unavailable code/data/template.
4. Delegation boundaries: what the user allows the model to decide and what
   must remain for human review.
5. Project skeleton gaps: user-facing flow, architecture, model/API contract,
   observability/trace, fallback behavior, demo mode, and verification strategy
   when they affect pipeline design.
6. Minor defaults: ordinary formatting, wording, standard tool choices, and
   other low-risk defaults. Ask these only if they materially affect grading or
   user identity.

Prefer open-ended questions for user-owned thinking. Prefer 2-3 options when
the user may not have a ready idea or when the choice is operational.

Example for a clear fixed-spec project:

Ask:

```text
这份作业的 spec 和交付物已经很明确。唯一会影响后续产物命名和实验内容的是
dataset / group id / 是否提交。你确认用 <dataset>、<group id>，并先只生成
本地草稿不提交吗？
```

Example for an open-ended creative or reflective project:

```text
这个项目最容易跑偏的是核心 concept。你希望作品主要表达哪种方向？

1. 偏技术展示：突出交互机制和实现完整度
2. 偏艺术表达：做一个有主题、有情绪的体验
3. 偏实用小工具：让交互服务一个明确功能

也可以直接说你自己的想法。
```

#### [B2] Record Conversation Notes, Not The Final Brief

After each answer, append process notes to:

```text
<work_dir>/investigation/user_notes.md
```

Use this structure:

```markdown
## Alignment Conversation Notes

### Round <N>
- Question:
- User answer:
- Coordinator interpretation:
- Decisions captured:
- Remaining uncertainty:
- New dimensions introduced:
- Approach implications:
- Skeleton gaps still open:
```

`user_notes.md` is a process log. It may be appended every round.
`alignment_brief.md` is not a process log and must not be rewritten after every
question. Write `alignment_brief.md` only when the Main Agent has no necessary
alignment question left.

If the user chooses partial scope, write:

```text
<work_dir>/investigation/user_scope.md
```

If the user says "you decide" or equivalent, record the decision as delegated,
not as a user-stated fact. The later `alignment_brief.md` must explain the
default strategy and why it is reasonable.

After each answer, extend the conversation from what the user actually said
rather than walking a fixed questionnaire. Example: if the user says "use a
multimodal model and image generation," the next likely uncertainty is not
formatting; it is API contract, mock fidelity, secret handling, fallback
behavior, and where model traces appear in the experience.

If the user stops, write `result.json` with `status: "skipped"`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status skipped \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --note "user stopped after reconnaissance"
```

If `[A4]` flagged reconnaissance failure and the user supplies pasted material,
save it to:

```text
<work_dir>/problem_user.md
```

Then update `spec.md`, `problem.md`, and `pipeline_design.md` so downstream
tools read the supplemented context from files, not chat memory.

#### [B3] Explore Approaches And Preview The Design Skeleton

Before writing `alignment_brief.md`, check whether the user has approved the
project skeleton. For straightforward assignments whose skeleton is fixed by the
spec, this may be a one-sentence confirmation. For open-ended assignments, it is
mandatory.

When enough raw information exists to compare plausible directions, present 2-3
approaches with trade-offs and your recommendation. Keep this concise, but make
the differences real. Example:

```text
我看到三种可行方向：

1. 展示优先：最稳，适合答辩，但真实 API 深度较浅。
2. 真实集成优先：最像产品，但需要 key、错误处理和 contract probe。
3. 创意体验优先：作品感最强，但 pipeline 和 fallback 要更精心设计。

我建议 2 + 3 的混合：...
你选这个方向吗，还是要改？
```

After the user chooses or corrects the approach, present a design skeleton
preview before the terminal brief. Cover only what matters for this assignment.
For open projects, include each applicable item below, or record why it is not
applicable:

- user-facing experience and interaction loop;
- creative direction / thesis / tone;
- architecture components and data flow;
- model/API or tool contracts, including mock/probe strategy;
- traceability / observability surface;
- failure and fallback behavior;
- expected deliverables, demo path, and verification strategy.

Ask the user whether the skeleton is right. Record the user's confirmation or
correction in `investigation/user_notes.md` with timestamp or turn summary. If
the user corrects it, append another `user_notes.md` round and update the
skeleton. Do not enter `[C]` until the user has approved either the short
fixed-spec skeleton or the richer open-project skeleton.

#### [B4] Write And Confirm `alignment_brief.md`

When the internal alignment audit no longer exposes a necessary question, write:

```text
<work_dir>/investigation/alignment_brief.md
```

Template:

```markdown
# Alignment Brief: <COURSE> <Assignment>

## Assignment Understanding
Summarize the Canvas-grounded task in the Main Agent's words.

## User Intent
State what the user wants this work to express, argue, demonstrate, or optimize.

## Confirmed Decisions
- ...

## Selected Approach
State the approach the user approved, including alternatives considered when
that mattered.

## Design Skeleton
- User-facing experience:
- Creative / intellectual direction:
- Architecture and data flow:
- Model, API, tool, or data contracts:
- Traceability / observability:
- Failure and fallback behavior:
- Verification and demo strategy:

## Delegated Decisions
- Decision:
  Default strategy:
  Reason:

## Non-Negotiables
- Content that must not be fabricated.
- Constraints or user boundaries that must not be crossed.

## Open Items For Final Review
- Items that do not block pipeline approval but must be surfaced at `[C5]` or
  later by `task-orchestrator.md` as human review items.

## Ready-To-Start Judgment
Explain why the Main Agent can now enter [C] without guessing the user's core
intent or project skeleton. Explicitly mention why the design skeleton is
sufficient to write pipeline stages with concrete goals, reads, writes, reviews,
quality criteria, and final review items.

## Self-Review
- Placeholder scan:
- Internal consistency:
- Scope check:
- Ambiguity check:

## User Confirmation
- Confirmation source:
- Confirmed by:
- Confirmation summary:
```

Before showing the brief to the user, self-review it and record the result in
`alignment_brief.md > Self-Review`:

- Placeholder scan: no TBD/TODO/empty section unless listed as a final review
  item.
- Internal consistency: selected approach, skeleton, non-negotiables, and open
  items do not contradict each other.
- Scope check: the work can be planned as one pipeline; if not, ask the user to
  narrow or stage it.
- Ambiguity check: any unresolved choice that would change stage design is asked
  before confirmation, not hidden as a delegated default.

Then show the user a concise summary and ask for confirmation. After the user
confirms, update `alignment_brief.md > User Confirmation` before entering `[C]`:

```text
我已经没有必须继续问你的问题了。下面是我写入 alignment_brief.md 的最终理解：

- ...

如果你确认，我会按这个方向进入 pipeline_design.md。
如果哪里不对，我会先修正 brief，不会开始执行。
```

If the user requests changes, append another round to `user_notes.md`, replace
`alignment_brief.md` with the corrected final brief, and ask for confirmation
again. Do not enter `[C]` until the user confirms the brief.

Hard gate: without `investigation/alignment_brief.md` containing populated
`Self-Review` and `User Confirmation` sections, do not write the final
`pipeline_design.md` and do not invoke `task-orchestrator.md`.

### [C] Design Pipeline

No executor/reviewer subagents and no draft-generation tool runs in `[C]`.
`[C]` writes the task-level execution plan only. The only user interaction after
planning is `[C5]`, where the user reviews the pipeline before any
`task-orchestrator.md` run.

Read:

```text
spec.md
investigation/explore_context.md
investigation/explore_manifest.json
investigation/rubric.md
investigation/review_a.json
canvas/assignment.json             # raw Canvas assignment evidence when assignment shell matters
canvas/syllabus.json               # raw Canvas syllabus evidence when syllabus matters
canvas/page-*.json                 # raw Canvas page evidence when page bodies matter
investigation/alignment_brief.md  # required and confirmed at [B]
investigation/user_notes.md       # if present
investigation/user_scope.md       # if present
problem_user.md                   # if present
pipeline_design.md
sub-skills/tools/_index.md
```

Use the following common pipeline shapes as **reference guidance** — the agent
composes freely based on the actual assignment, not a fixed chain.

| Scenario | type | Typical tool chain | Final deliverable |
|---|---|---|---|
| **paper** | `paper` | paper-search → figure-maker (opt) → writing-helper → pdf-renderer | `final.pdf` |
| **slides** | `slides` | figure-maker (opt) → slide-maker | `slides.pdf` |
| **math** | `math` | writing-helper (LaTeX math) → pdf-renderer | `solution.pdf` |
| **lab** | `lab` | code-writer → test-runner → writing-helper → pdf-renderer | `src/` + `report.pdf` |
| **mixed** | `mixed` | Multiple sub-pipelines composed from above | multiple files |

For mixed assignments, write multiple sub-pipelines in pipeline_design.md.

`pipeline_design.md` must contain these sections and fields:

- `# Pipeline: <COURSE> <assignment>`
- `## Metadata`
  - `repo_root`
  - `work_dir`
  - `course_id`
  - `assignment_id`
- `## Output`
  - `mode`
  - final deliverable filenames/paths
- `## Pipeline Review Status`
  - `status: awaiting_user_review`
  - `review_requested_at`
  - `approved_at: null`
  - `approved_by: null`
  - `approval_summary: null`
- `## Constraints`
  - assignment constraints from `spec.md`
  - syllabus-derived constraints only after `spec.md`, `explore_context.md`,
    `rubric.md`, or `review_a.json` confirms their relevance
  - user constraints and non-negotiables from `alignment_brief.md`
  - forbidden context rules when relevant
  - non-downgradable hard requirements from `spec.md`
- `## Stages`
  - stable stage id
  - concrete stage goal
  - `primary_tool`: the main top-level tool skill for stage ownership
  - `tools`: ordered list of all top-level tool skills the stage must use
  - `tool_roles`: why each listed tool is needed in this stage
  - `delegate`: `subagent` or `main-agent`
  - allowed reads
  - writes
  - review settings: spec compliance and quality
  - retry limit
  - quality criteria
  - human blockers
- `## Human Review Items`

### Spec Hard Requirements / No-Downgrade Policy

When `spec.md` or the authoritative reference states a hard requirement, the
pipeline must preserve it exactly. Hard requirements include any explicit
`must`, `required`, `only`, `do not`, exact filename/package/layout constraints,
mandated data/source/tool/template/class/style/citation rules, submission
contents, page/time limits, or grading-critical rubric conditions.

Do not rewrite a hard requirement into a softer fallback, preference, human
review item, or acceptable risk. If the current evidence is insufficient to meet
the requirement, the pipeline must represent that as a blocker.

In `pipeline_design.md`, record hard requirements in a dedicated constraint
block:

```yaml
required_spec_constraints:
  - id: report_format_style
    source: references/project_announce.pdf.txt:178
    requirement: "must use the official LaTeX style file; do not use preprint"
    applies_to:
      - draft/report.pdf
    required_evidence:
      - "render source/log proves the required style file was used"
    status: blocked
    blocker_type: external_blocker
    fallback_allowed_for_final: false
```

Planning rules:

- For every hard requirement, preserve source evidence and required verification
  evidence. A later stage brief must be able to trace back to the exact
  constraint.
- If the requirement can be satisfied with available materials, include the
  materials in allowed reads and make the required evidence part of stage
  quality criteria.
- If the requirement cannot currently be satisfied, mark the affected final
  deliverable blocked by `needs_user_input`, `manual_only`, or
  `external_blocker`. Do not mark it as a final deliverable that can pass via
  fallback.
- Fallbacks are allowed only for optional implementation mechanics or for
  clearly named preview/debug artifacts. A fallback output must not satisfy or
  replace a final deliverable governed by `fallback_allowed_for_final: false`.
- The only way to relax a hard requirement is new authoritative evidence: an
  updated spec, instructor/user-supplied file/instruction that explicitly
  changes the requirement, or a user decision to produce a non-final preview.

For mixed assignments, keep one ordered stage plan. Use stage ids and headings
to group sub-pipelines instead of creating independent uncoordinated plans.
Within a stage, `tools` is composable: use one tool for simple stages and
multiple tools when the same executor must combine capabilities to produce one
coherent stage artifact. `primary_tool` declares the stage's lead contract.
Legacy `tool: <path>` is accepted only as shorthand for
`primary_tool: <path>` plus `tools: [<path>]`; new plans should write the
expanded fields so supporting tools are auditable.

Complete `pipeline_design.md`. It is the single-assignment execution plan:

```markdown
# Pipeline: <COURSE> <assignment>

## Metadata
repo_root: <absolute path from [A2]>

## Output
- mode: mixed (code + doc_prose + slides)
- deliverables: [notebook.ipynb, report.pdf, ...]

## Constraints
- [quantifiable constraints from spec]
- [relevant syllabus constraints distilled into spec/rubric/review evidence]
- [user intent / non-negotiables from alignment_brief.md]
- [hard spec constraints, if any, with required_spec_constraints]

## Stages

### Stage 1 - Notebook Execution
- id: stage_01_notebook
- primary_tool: sub-skills/tools/code-writer.md
- tools:
  - sub-skills/tools/code-writer.md
  - sub-skills/tools/test-runner.md
- tool_roles:
  - code-writer: create the notebook/source artifact and executable cells
  - test-runner: execute validation commands and preserve run evidence
- delegate: subagent
- lang: python
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
  - test_report.md
  - test_report.json
- quality_criteria:
  - notebook executes from a clean kernel
  - test_report.json records validation commands, exit codes, and pass/fail state
  - no fabricated metrics; report metrics must come from actual notebook output
- human_blockers:
  - dataset choice if the spec allows multiple datasets and user has not chosen

### Stage 2 - Report Draft
- id: stage_02_report
- primary_tool: sub-skills/tools/writing-helper.md
- tools:
  - sub-skills/tools/writing-helper.md
  - sub-skills/tools/humanizer.md
- tool_roles:
  - writing-helper: draft the report from spec, rubric, user intent, and metrics
  - humanizer: post-process prose because this stage declares `post-process: humanize`
- delegate: subagent
- type: report
- review:
  - spec_compliance: true
  - quality: true
- max_retries: 1
- reads:
  - spec.md
  - investigation/rubric.md
  - investigation/user_notes.md
  - draft/metrics.json
- writes:
  - draft/report.md
- quality_criteria:
  - covers every rubric criterion
  - numeric claims are grounded in draft/metrics.json
- post-process: humanize
- human_blockers:
  - group member names if required by the assignment

## Human Review Items
- ...

## Pipeline Review Status
- status: awaiting_user_review
- review_requested_at: <UTC timestamp>
- approved_at: null
- approved_by: null
- approval_summary: null
```

Do not write or require `task_profile.yaml`. The orchestrator reads
`spec.md + explore_context.md + alignment_brief.md + pipeline_design.md`
directly.

`pipeline_design.md` must explicitly incorporate `alignment_brief.md`. At
minimum, its constraints, stage goals, human blockers, delegated decisions, and
final review items must reflect the confirmed alignment brief. If a planned
stage cannot be justified from `spec.md`, `investigation/explore_context.md`,
`investigation/rubric.md`, `investigation/review_a.json`,
`investigation/alignment_brief.md`, or explicitly allowed raw `canvas/*.json`
body evidence, do not include that stage. Raw Canvas content is not hidden
background when it is listed in the stage brief's allowed reads. Stage briefs
must explicitly allow relevant `canvas/*.json` reads when Canvas-native details
matter.

`pipeline_design.md` is the task-level plan for the Main Agent and
task-orchestrator. It is not handed directly to executor subagents. The
orchestrator converts each delegated stage into
`stage_briefs/<stage_id>_executor.md` plus reviewer briefs when review is
enabled.

### [C5] Pipeline Review Gate

User-interaction phase #2.

After writing `pipeline_design.md`, do **not** invoke
`tasks/task-orchestrator.md`, do not dispatch executor/reviewer children, and do
not run stage tools. Instead, present a user-facing approval brief that is
readable on its own. Do not merely point the user at `pipeline_design.md`; the
Main Agent must explain the plan in chat well enough that the user can approve
or reject it without opening the Markdown file.

The approval brief must include the complete substance of the pipeline, in a
clean review format:

1. **Context and goal**
   - Course + assignment.
   - Workbench path.
   - `alignment_brief.md` and `pipeline_design.md` paths as references only.
   - User-confirmed goal and non-negotiables.
2. **Planned outputs**
   - Output mode.
   - Every final deliverable path/name.
   - Intermediate evidence or logs that matter for grading/verification.
3. **Constraints**
   - Assignment constraints from `spec.md`.
   - Relevant rubric/syllabus constraints.
   - User constraints from `alignment_brief.md`.
   - Forbidden actions, especially Canvas submission behavior.
4. **Full stage plan**
   - For every stage, show: stage id, goal, primary tool, full tools list, tool
     roles, delegate mode, allowed reads, writes, review settings, retry limit,
     quality criteria, and human blockers.
   - If a stage is `delegate: main-agent`, explain why it is simple enough for
     inline execution. If there is no clear reason, revise the pipeline before
     asking for approval.
5. **How task-orchestrator will execute it**
   - Ground this section in `tasks/task-orchestrator.md`; do not summarize from
     memory or use generic "subagents will run" wording.
   - State that `task-orchestrator.md` will first verify
     `Pipeline Review Status.status: approved_for_orchestration`.
   - It will generate `stage_briefs/<stage_id>_executor.md` and reviewer briefs.
   - It will dispatch executor subagents for `delegate: subagent` stages.
   - It will record child dispatches in
     `stage_reviews/child_dispatch_ledger.json`.
   - For reviewed stages, it will run spec-compliance review first, then quality
     / code review only after spec compliance passes.
   - If review finds blocking auto-fixable issues, it will send a bounded fix
     brief back through the executor loop while retries remain.
   - It will write `stage_results/`, `stage_reviews/`,
     `verification_checklist.md`, `verification.log`, and final `result.json`.
   - It will not submit to Canvas.
6. **Approval risks and review items**
   - Anything the user must check before execution.
   - Any missing external resource, manual-only item, or accepted fallback.
   - Any part of the plan that may be expensive, slow, or likely to require
     iteration.

Keep the approval brief concise enough to read, but do not omit a stage or hide
execution mechanics behind "see markdown." If the pipeline is long, use a
numbered stage table plus short per-stage details. The approval brief is the
review surface; `pipeline_design.md` is the audit artifact.

Use this response shape:

```markdown
**Pipeline Approval Brief**

**Goal**
- ...

**Deliverables**
- ...

**Non-Negotiables**
- ...

**Execution Stages**
| # | Stage | Tools | Delegate | Writes | Reviews | Retry | Human blockers |
|---|---|---|---|---|---|---|---|
| 1 | ... | primary: ...; supporting: ... | subagent | ... | spec + quality | 1 | ... |

**Stage Details**
1. `<stage_id>` — <goal>
   - Reads: ...
   - Writes: ...
   - Quality criteria: ...
   - Why this delegate mode: ...

**How Orchestration Will Work If Approved**
- Validate `Pipeline Review Status.status == approved_for_orchestration`.
- Generate executor/reviewer briefs from this pipeline.
- Dispatch executor subagents for delegated stages.
- Run spec review before quality/code review.
- Iterate executor fixes while retries remain.
- Verify deliverables and write `result.json`.
- Canvas submission will not happen here.

**Approval Risks / Manual Review Items**
- ...

你要怎么处理?
- 通过，进入 task-orchestrator 执行
- 先修改 pipeline（告诉我改哪里）
- 暂停，不执行
```

If the user asks to modify the pipeline:

- If the change alters intent, selected approach, design skeleton,
  non-negotiables, or human-owned facts, return to `[B4]`, update and reconfirm
  `alignment_brief.md`, then rerun `[C]`.
- If it changes only execution details within the confirmed brief, append the
  request to `investigation/user_notes.md`, update `pipeline_design.md`, keep
  `Pipeline Review Status.status: awaiting_user_review`, and ask for review
  again.

If the user pauses, write `result.json` with `status: "pipeline_ready"` and
`--deferred-to-next-run`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status pipeline_ready \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --deliverable "data/homework/<COURSE>/<HWID>/pipeline_design.md" \
  --human-review-item "Pipeline awaits user approval before task-orchestrator execution" \
  --note "pipeline generated; task-orchestrator not run" \
  --deferred-to-next-run \
  --allow-missing-deliverables
```

If the user approves execution, update `pipeline_design.md`:

```text
## Pipeline Review Status
- status: approved_for_orchestration
- review_requested_at: <existing timestamp>
- approved_at: <UTC timestamp>
- approved_by: user
- approval_summary: <one-line confirmation>
```

Then hand off to `tasks/task-orchestrator.md` with the workbench path. This is
a new workflow phase owned by `task-orchestrator.md`; it is not part of
`do-homework.md` execution.

## Output Format

Use the selected plan item's `canvas_url` or `canvas/assignment.json.html_url`;
never reconstruct a host-specific Canvas URL from course and assignment IDs.

After `[C5]`:

```markdown
## <COURSE> <assignment name>

**Pipeline:** `data/homework/<COURSE>/<HWID>/pipeline_design.md`
**Status:** pipeline_ready / skipped / error
**Canvas URL:** <assignment html_url, or "not available" if Canvas did not provide one>

Human review items:
- Review pipeline_design.md before orchestration.
- ...

Next step:
- If approved, run `tasks/task-orchestrator.md` with this workbench.
```

## Safety

1. **Two user-interaction phases only**: `[B]` alignment may be multi-round;
   `[C5]` asks for pipeline approval, revision, or pause. Do not prompt the user
   from `[A]` or `[C]`.
2. **Never auto-execute.** Even if the user said "complete it" upfront, stop
   after `pipeline_design.md` until the user approves orchestration.
3. **Never auto-submit.** Canvas submission is outside this planning task and
   still requires an explicit later confirmation after draft verification.
4. **Never modify raw Canvas JSON** under `canvas/*.json`.
5. **Do not run script-led reconnaissance** as the normal path.
6. **Honor partial scope.**
7. **Ground every planned stage in `spec.md`, `references/`,
   `alignment_brief.md`, and `pipeline_design.md`.** Do not write
   `[PROBLEM N]`, `[TODO: align with actual project spec]`, or
   `[此处由小组成员填入选题]` placeholders into the pipeline. The only acceptable
   markers are `[CITATION NEEDED: ...]` and `[CLARIFICATION NEEDED: ...]`, both
   surfaced as human review items.

## Pitfalls

- **Don't read `assignment.description` as the problem statement.** It may be
  empty, a file link, a Google Doc link, or one hint among many.
- **Don't stop at the first match.** Check assignment page, rubric, front page,
  syllabus, modules, pages, files, and external URLs before deciding which
  source is the spec.
- **Don't turn `spec.md` into a raw dump.** Full PDF or Google Doc text belongs
  in `references/`; `spec.md` is the standardized report.
- **Google Docs can be the main spec.** Try to fetch text. If blocked, record it
  in `unreachable.txt` and let `review_a.json` decide whether it blocks work.
- **Course code in `data/sync/current/assignments.json` is in `context_name`, not a separate
  field.**
- **The work_dir path can contain spaces and Chinese.** Always quote shell
  arguments.
- **`submission_types` matters later.** `online_upload` is what
  `canvascli submit` handles, but submission is not part of `do-homework.md`.
- **`[CLARIFICATION NEEDED: ...]` markers** are batched at `[C5]`, not asked one
  by one.

## Cross-references

- Reconnaissance: `tools/assignment-recon.md`
- Pipeline execution: `tasks/task-orchestrator.md`
- Tool capability matrix: `tools/_index.md`
- Canvas commands: `tools/canvascli-api.md`
- Submission protocol: `tools/canvascli-api.md`
