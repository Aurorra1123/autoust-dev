---
name: assignment-source-intake
description: clean-start source/spec intake
---

# Assignment Source Intake

Use this task only for `entry_preset: clean_start`. It owns clean-start
Canvas/source reconnaissance and stops after terminal source artifacts are ready
for `sub-skills/tasks/assignment-workflow-planner.md`.

Do not use this task as the normal entry for retained drafts, prior outputs,
`review_or_submit`, `review_or_execute`, or repair/continue flows. Those entries
belong to `../tools/current-state-intake.md` and the workflow planner. The only
retained-flow exception is a narrow source-evidence recovery submode where the
planner/router has identified missing, stale, or blocking source evidence and
routes back here for source intake only.

Required artifact chain:

```text
prelaunch_startup_inventory.json
-> investigation/explore_manifest.json
-> references/REFERENCE_INDEX.md
-> references/
   -> source_docs/<slug>/<slug>.pdf + .pdf.txt + .pdf.links.json
   -> slides/<slug>/<slug>.pptx + .pptx.txt
   -> external/<slug>.txt
   -> canvas_native/<slug>/source.json + source.txt + ORIGIN.md
-> spec.md
-> investigation/rubric.md
-> investigation/review_a.json
-> investigation/recon_summary.md
-> investigation/explore_context.md
-> stage_reviews/child_dispatch_ledger.json
-> stage_reviews/process_concerns.jsonl      # when recovery/blocking concerns exist
-> problem.md                                # compatibility summary, when generated in this run
```

Standard clean-start homework runs preserve source evidence under `references/`
through `reference_collector`. Legacy source-scout audit appendices may exist
only in old workbenches or explicit recovery/debug cases; they are not normal
run outputs and are not the default coordinator interface.

Directory boundary: `investigation/` top level is reserved for terminal
reconnaissance artifacts. Normal top-level files are:

```text
explore_manifest.json
explore_context.md
recon_summary.md
rubric.md
unreachable.txt
review_a.json
user_notes.md
user_scope.md
```

Do not write child prompts/briefs, legacy scout receipts, full candidate lists,
body fragments, raw audit JSON, compatibility aliases, transcripts, or process
scratch files at the `investigation/` top level.

Main Agent read boundary: in a normal clean-start run, the Main Agent reads
`references/REFERENCE_INDEX.md`, preserved reference files, Canvas-native
`source.json` / `source.txt` copies, and the terminal files listed above.
Appendix reads are allowed only for recovery, audit, or debugging; when used,
read the smallest named artifact/window and record the reason in
`investigation/review_a.json` or `stage_reviews/process_concerns.jsonl`.

Actor rules:

- The Main Agent owns the task lifecycle and is the only actor that talks to the
  user.
- Subagents are temporary workers with curated prompts, bounded reads/writes,
  and receipt requirements.
- `reference_collector` is the only standard homework reconnaissance child role.
  It is a preservation worker, not a source judge.
- The Main Agent owns final source interpretation, `spec.md`, `rubric.md`,
  `review_a.json`, `recon_summary.md`, `explore_context.md`, and source-intake
  recovery decisions.
- Subagents must not write final `spec.md`, final `review_a.json`,
  `pipeline_design.md`, or user alignment decisions.
- Normal runs must not create `reading_plan.compact.json`,
  `source_findings.compact.md`, or source-scout appendix files.

Hybrid Gate Report rule:

- The Main Agent must fully read the syllabus body and any direct-spec strong
  match source body. A direct-spec strong match satisfies at least two of: task
  terms in the source name/title, assignment-linked or `required` source
  placement, and opening-body evidence of deliverable, format, deadline,
  sections, submission, grading, or prompt.
- Supporting sources are preserved by `reference_collector`. The Main Agent
  reads `references/REFERENCE_INDEX.md`, relevant preserved reference files,
  Canvas-native `source.json` / `source.txt` copies, `recon_summary.md`, and
  terminal artifacts before making source judgments.
- The Main Agent must not normally read legacy appendix artifacts.

## Clean-Start Proposal Runtime Checklist

For clean-start proposal, research, or open-ended homework, read this checklist
before the longer flow below. It is the shortest contract for the behavior that
must happen at runtime.

1. Fetch raw Canvas snapshots through `assignment-recon.md`.
2. Dispatch `reference_collector` for every homework run.
3. Wait for `references/REFERENCE_INDEX.md`.
4. Read preserved references, not broad raw Canvas snapshots.
5. Write terminal artifacts.
6. Write `investigation/recon_summary.md` as the human-readable entrance to reconnaissance.
   JSON files are machine evidence, not the user-facing completion story. The
   user-facing recon summary must state the source trail, deliverables, missing
   user decisions, reference collection status, blocked sources, and the next
   question. Scale the amount of user-facing detail with reconnaissance depth:
   a tiny one-source task can have a short summary, but a multi-source run with
   several preserved references, PDFs, timelines, methods guidance, source
   conflicts, or non-blocking gaps must expand the summary enough that the user
   can see the important findings without opening audit JSON.
7. Do not choose user-owned project direction, group facts, dataset choice,
   research question, or creative stance during source intake. If the assignment
   direction is open and not explicitly delegated in the current request or
   accepted startup inventory, hand off for planner alignment instead of writing
   `alignment_brief.md` here.

## [A] Run Source Intake In The Initialized Workbench

No user interaction in `[A]`.

Runtime goal: use the initialized workbench and accepted startup inventory to
answer three questions before planning starts:

1. What exact Canvas assignment is this?
2. Which sources prove the requirements and deliverables?
3. Which choices still need user alignment?

Do not treat an assignment title, Canvas description, or single link as the full
problem statement unless the fetched source evidence proves it is complete.

### [A0] Accepted Startup Inventory

This task receives an initialized workbench and accepted startup inventory from
`sub-skills/tasks/do-homework.md`. Before reading old workbench files as task
context, verify that this file already exists:

```text
prelaunch_startup_inventory.json
```

Do not resolve assignments, choose `work_dir`, create the initial workbench, run
preflight archive, or write the startup inventory here. If
`prelaunch_startup_inventory.json` is missing or stale, return to the
router/preflight step instead of continuing source intake. The inventory must
either be accepted for `entry_preset: clean_start` or explicitly route a narrow
`source_evidence_recovery` from a retained/review/repair/continue flow because
source evidence is missing, stale, or blocking.

The accepted inventory must state:

- `entry_preset: clean_start`, or `source_evidence_recovery: true` with the
  originating retained/review/repair/continue route;
- current user request;
- resolved course/assignment if already known;
- accepted current source/spec/reference files allowed for this run;
- forbidden context, including old stage receipts, transcripts, prior reviews,
  stale pipeline files, old diagnostics, and archive contents unless explicitly
  allowlisted for a blocker investigation;
- stale process files archived or excluded from active context.

Old process evidence is not task context by default. A scout may inspect it only
when `prelaunch_startup_inventory.json` allowlists the exact file or directory
and explains why it affects current source intake.

### Explore Mode Rules

Apply these rules after the workbench exists and before `[A3]` finishes
reconnaissance.

Write the explore decision to `investigation/explore_manifest.json` before
handoff to the planner.

Use these rules:

| Situation | Required action |
|---|---|
| Canvas modules, linked files, PDFs, external specs, rubric search, or multiple possible sources must be inspected | The Main Agent marks `source_spec` as the source/spec exploration domain. Do not dispatch or accept a `source_spec` Subagent as a completed child; dispatch `reference_collector` after the Canvas raw snapshot. |
| Any homework run reaches reconnaissance | Dispatch `reference_collector` to preserve complete original source evidence under `references/`, including task-relevant downloads, text extractions, PDF link manifests, and Canvas-native verbatim copies. |
| Required or high-signal candidates need body reading | The Main Agent reads `references/REFERENCE_INDEX.md` and preserved reference files after the collector returns; the collector is not a source judge. |
| The task is tiny and mechanically obvious | Main Agent may do inline source exploration, but must record `delegation_mode: "inline_fallback"` or `executed_by: "main-agent"` with the concrete reason. |
| `reference_collector` dispatch is unavailable or blocked | This is recovery evidence, not a clean `reference_collector` success. Record a process concern, preserve only what the Main Agent can preserve honestly, and do not set `reference_collector_used: true` unless a real child dispatch occurred. |

The source preservation gate is sequential: raw Canvas snapshot first,
`reference_collector` second, Main Agent interpretation third. Do not let the
collector replace Main Agent interpretation or final artifact writing.

`source_spec` is a Main Agent exploration domain, not a dispatchable Subagent
role and not a completed child result. It may appear in legacy manifests only as
a domain label; it must not have a successful dispatch id or receipt path.

A normal homework run must dispatch `reference_collector` after
`assignment-recon.md` has fetched raw Canvas snapshots.

Main Agent inline recovery must be recorded as recovery evidence, not as a
Subagent receipt. If a child Subagent times out or cannot be dispatched, the
Main Agent may recover only by writing a process concern and marking the scout
as `RECOVERED_INLINE_AFTER_TIMEOUT`, `INLINE_FALLBACK`, or equivalent. Do not
call that a successful Subagent dispatch.

`reference_collector` copies source material; it does not decide which source
controls the assignment.

Main Agent summary is not a Subagent receipt. The Main Agent reads
`references/REFERENCE_INDEX.md`, preserved reference files, and Canvas-native
`source.json` / `source.txt` copies, writes final `spec.md`, `review_a.json`,
`explore_context.md`, and hands off to the planner for user alignment.

Do not create `reading_plan.compact.json`.
Do not create `source_findings.compact.md`.
Do not create `reading_plan.compact.approved.json`.
Do not create `investigation/_appendix/source_index.json`.
Do not create `investigation/_appendix/body_evidence_fragments/`.
Do not create `investigation/_appendix/scout_receipts/` for source
reconnaissance artifacts.

Before returning from reconnaissance, run a parent self-check. Collector output
is not a terminal reconnaissance verdict: preserved source files give the Main
Agent evidence, but the Main Agent still must write or verify `spec.md`,
`investigation/rubric.md`, `investigation/review_a.json`, and
`investigation/recon_summary.md`. If source-body evidence exists but any
terminal reconnaissance artifact is missing, the coordinator must not silently
stop or hand off; it must write a recover/blocking `review_a.json` or
`stage_reviews/process_concerns.jsonl` entry that names the missing `spec.md`,
`investigation/rubric.md`, `investigation/review_a.json`, or
`investigation/recon_summary.md` artifact and the next recovery action. Rule for
automated checks: missing `spec.md`, `investigation/rubric.md`, or
`investigation/review_a.json` must write a recover/blocking `review_a.json` or
`stage_reviews/process_concerns.jsonl`.

If any child is dispatched before alignment, the Main Agent records it in
`stage_reviews/child_dispatch_ledger.json` with role, prompt/brief path, receipt
or output path, dispatch id, and timestamps. For `reference_collector`,
`explore_manifest.json` and `review_a.json` are status summaries only; they do
not replace the ledger row with a real child `agent_id` or transcript handle.
`reference_collector` writes `references/REFERENCE_INDEX.md` rather than a scout
receipt path, but its dispatch identity remains ledger-backed.

Scout evidence must satisfy the same child-evidence contract used later for
executor/reviewer children:

- ledger row is written before waiting on the child;
- dispatch return id is the identity authority;
- receipt includes `created_at_utc`, `completed_at_utc`, status, reads, writes,
  findings, concerns, and dependency notes;
- coordinator records when the receipt was observed and accepted;
- transport failures, child-side ledger writes, identity normalization, or
  inline fallback are process concerns, not silent success.

If inline fallback is used for a non-tiny source-preservation action, state in
`explore_manifest.json` that child isolation was not exercised for that action.

### Explore Context Minimum

Before planner handoff, write `investigation/explore_context.md` for every
non-trivial run. This file is the stable downstream context for later agents.
It must summarize:

- resolved course and assignment;
- current Canvas/source requirements;
- main spec candidates and final main-source judgment;
- fetched references and blocked/unreachable materials;
- preserved reference coverage and any source-read concerns;
- source inputs or required files available for planning;
- skipped source-preservation or source-recovery actions and reasons;
- stale or forbidden context that must not be passed to later children;
- source sufficiency risks and downstream verification risks;
- user decisions needed by `sub-skills/tasks/assignment-workflow-planner.md`.

Also write `investigation/recon_summary.md` before planner handoff. This is the
human-readable entrance for the user and reviewer. It must be concise but
depth-adaptive: summarize lightly when the investigation was light, and expand
when the investigation preserved multiple source bodies, downloaded PDFs/decks,
found methods/timeline guidance, or identified conflicts and non-blocking gaps.
It must include:

- the source trail in plain language;
- deliverables and grading/rubric status;
- `reference_collector` status and any source-preservation recovery actions
  skipped, recovered inline, or blocked;
- whether preserved references and the parent self-check were refreshed after
  any reviewer `recover`;
- the concrete high-signal findings from each important source body, not only
  the file title;
- source conflicts, timing differences, missing templates, blocked sources, and
  other non-blocking gaps that may affect alignment;
- user-owned decisions still needed before planning;
- the exact next planner question or stop reason.

Depth scaling guidance:

- For a one-source or mechanically obvious assignment, 4-6 lines may be enough.
- For a non-trivial proposal/research/open-ended task, include separate bullets
  for main spec, methods/topic guidance, timeline/calendar facts, rubric or
  policy constraints, and gaps.
- If a PDF, deck, syllabus, or page was important enough for
  `reference_collector` to preserve, the recon summary must surface the source's
  key actionable findings, such as required sections, method options, timeline,
  formatting, or policy constraints. Do not collapse it into "supporting context
  checked."
- If `references/REFERENCE_INDEX.md` or `review_a.json` records downstream gaps,
  reflect those gaps in `recon_summary.md` and in the planner handoff summary.

Do not make users read stale source-scout artifacts or `review_a.json` to
understand run status. `recon_summary.md` is the user-facing status entry.

Do not pass raw old logs, archive files, prior reviews, or prior pipeline files
to executor/reviewer children just because a scout inspected them. Only
distilled current-run findings in `explore_context.md`, `spec.md`, or the
confirmed terminal agreement become normal downstream context.

### [A3] Canvas Generic Reconnaissance - Mandatory

Invoke `../tools/assignment-recon.md` as the source/spec workflow. This is a Main
Agent source/spec exploration domain and may be supported by
`reference_collector`, but it must not be replaced by a standalone
spec-generation script. The Main Agent must read `references/REFERENCE_INDEX.md`,
preserved reference files, and Canvas-native `source.json` / `source.txt`
copies; it must not load broad raw Canvas snapshots as normal context after the
collector has preserved task-relevant evidence. It judges the main spec, writes
`spec.md`, and keeps review evidence in the workbench.

Required [A3] order:

1. Fetch raw Canvas snapshots through `assignment-recon.md`.
2. Dispatch `reference_collector` for every homework run.
3. Wait for `references/REFERENCE_INDEX.md`.
4. Read preserved references, not broad raw Canvas snapshots.
5. Write terminal artifacts.

Follow the Canvas Generic stages:

1. **Stage 1 fetch-context**
   Read assignment, rubric, front page, syllabus, modules, every module's items,
   announcements, relevant pages, attached files, and external URLs through
   atomic `canvascli` commands. Syllabus is a first-class source, not an optional
   afterthought. Save raw JSON under `canvas/`, including the complete
   `canvas/announcements.json` collection snapshot, but do not treat broad raw
   snapshots as the Main Agent's task context. Stage 1 may record preliminary
   source notes in `investigation/explore_manifest.json`; it does not write
   terminal `spec.md`.

2. **Stage 2 collect-references**
   Dispatch `reference_collector` to download or fetch necessary PDFs, Google
   Doc text, starter code, datasets, decks, Canvas-native bodies, or external
   spec pages into `references/`. Record blocked resources in
   `investigation/unreachable.txt`. For every fetched PDF that may affect the
   spec, save the original PDF, extracted text, and PDF link annotation manifest
   under `references/source_docs/<slug>/` as `<slug>.pdf`, `<slug>.pdf.txt`, and
   `<slug>.pdf.links.json`; do not treat PDF text extraction as complete until
   visible text and embedded link annotations have both been checked. Preserve
   relevant Canvas-native syllabus, announcement, assignment page, or Canvas page
   content verbatim under `references/canvas_native/<slug>/source.json` with
   readable `source.txt` and provenance `ORIGIN.md`. Wait for
   `references/REFERENCE_INDEX.md`.

   Announcement arrays are collection snapshots, not source objects. Do not copy
   the full `canvas/announcements.json` array into
   `references/canvas_native/announcements/source.json`. For announcements,
   `reference_collector` must screen each item and preserve only relevant
   complete announcement objects, one per
   `references/canvas_native/announcement-<id-or-slug>/source.json`, with
   `REFERENCE_INDEX.md` origins such as `canvas/announcements.json#id=26545`.

3. **Stage 3 write source judgments**
   Read `references/REFERENCE_INDEX.md` and the preserved references named
   there. Then write the standardized `spec.md` report with metadata, source
   trail, syllabus relevance, main spec judgment, deliverables, requirements,
   rubric placeholder, inputs, gaps, and evidence pointers. Search Canvas
   rubric, preserved references, syllabus copies, and external spec text. Write
   `investigation/rubric.md`. Do not mark rubric search complete until syllabus
   has either contributed criteria or been explicitly judged
   irrelevant/unavailable. If the syllabus contributes criteria,
   `investigation/rubric.md` must cite the preserved Canvas-native syllabus
   source under `references/canvas_native/`; a paraphrase or lossy summary alone
   is incomplete.

4. **Stage 4 review investigation**
   Run a cold review of `spec.md`, `investigation/rubric.md`,
   `references/REFERENCE_INDEX.md`, preserved files under `references/`,
   `investigation/unreachable.txt`, and source-judgment artifacts available at
   this stage. The Main Agent reads preserved references rather than stale
   source-scout summaries. It self-checks source sufficiency and writes strict
   JSON to `investigation/review_a.json`. Stage 5 then finalizes output-mode
   notes in `investigation/recon_summary.md` and
   `investigation/explore_context.md`.

5. **Stage 5 classify-output**
   Classify the output mode (`doc_prose`, `pdf_annotated`, `pdf_typed`, `code`,
   `form_answers`, `slides`, or `mixed`) and record the preliminary output mode
   in `investigation/recon_summary.md` and `investigation/explore_context.md`.
   Do not write the full `pipeline_design.md` schema here.

After `[A3]`, immediately read `references/REFERENCE_INDEX.md`, then read the
preserved reference files named there:

```text
references/REFERENCE_INDEX.md
references/source_docs/<indexed-slug>/
references/slides/<indexed-slug>/
references/external/<indexed-slug>.txt
references/canvas_native/<indexed-slug>/source.json
references/canvas_native/<indexed-slug>/source.txt
references/canvas_native/<indexed-slug>/ORIGIN.md
```

Then read the terminal source-intake artifacts produced in this run:

```text
investigation/explore_manifest.json
investigation/explore_context.md  # required for non-trivial runs
investigation/recon_summary.md
spec.md
investigation/rubric.md
investigation/unreachable.txt
investigation/review_a.json
stage_reviews/child_dispatch_ledger.json
stage_reviews/process_concerns.jsonl  # when recovery/blocking concerns exist
problem.md                  # compatibility only, when generated in this run
```

Do not normally read broad raw Canvas snapshots or stale appendix artifacts
after `[A3]`:

```text
canvas/*.json
Do not read investigation/_appendix/source_index.json
Do not read investigation/_appendix/body_evidence_fragments/
Do not read investigation/_appendix/scout_briefs/
Do not read investigation/_appendix/scout_receipts/
Do not read investigation/_appendix/compatibility_aliases/
```

Read source-scout appendix artifacts only for stale-workbench cleanup, recovery,
or audit. A normal parent self-check must use `references/REFERENCE_INDEX.md`,
preserved reference files, Canvas-native `source.json` / `source.txt` copies,
`recon_summary.md`, and terminal artifacts; it must not inspect source-scout
appendix fragments or source-scout receipts just to gather more context.

Do not hand off to the planner until:

- `explore_manifest.json` accounts for each source-intake domain,
  `reference_collector` dispatch, skipped source-preservation action, or inline
  source recovery.
- Non-trivial runs must have `investigation/explore_context.md`; any
  inline-fallback reason belongs inside that file and
  `investigation/explore_manifest.json`.
- On a clean-success path, the `reference_collector` dispatch must be recorded
  in `stage_reviews/child_dispatch_ledger.json` with a real child `agent_id` or
  transcript handle; a handwritten alias such as
  `reference_collector_<course>_<assignment>` is not clean evidence. An empty
  dispatch ledger cannot prove `reference_collector_used: true`.
- If `reference_collector` was unavailable or blocked and the Main Agent used
  inline recovery, `review_a.json.reference_collector_used` must not be `true`;
  the run must be marked as recovery/blocking evidence in `review_a.json` or
  `stage_reviews/process_concerns.jsonl`.
- `references/REFERENCE_INDEX.md` exists.
- `references/canvas_native/` contains verbatim source copies for relevant
  Canvas-native syllabus, announcement, assignment page, or Canvas page content.
  Relevant announcements must be preserved as individual
  `references/canvas_native/announcement-<id-or-slug>/source.json` objects, not
  as the full `canvas/announcements.json` array.
- PDFs that affect the assignment have original PDF, `.pdf.txt`, and
  `.pdf.links.json` companions.
- `investigation/recon_summary.md` exists and gives a user-readable status plus
  the next planner question or stop reason.
- On a clean-success path, `review_a.json` records
  `reference_collector_used: true`, `source_scout_pipeline_used: false`,
  `announcements_checked`, `reference_index_checked`, `downloaded_references`,
  `canvas_native_sources`, and `pdf_link_manifests_checked`. On a recovery path
  where no real `reference_collector` child ran, it must record the blocker
  instead of claiming clean collector use.
- `review_a.json` includes these fields when complete:

```json
{
  "announcements_checked": true,
  "reference_collector_used": true,
  "source_scout_pipeline_used": false,
  "assignment_shell_checked": true,
  "rubric_checked": true,
  "syllabus_checked": true,
  "reference_index_checked": true,
  "canvas_native_sources": [],
  "downloaded_references": [],
  "pdf_link_manifests_checked": true,
  "direct_spec_sources": [],
  "rubric_sources": [],
  "required_inputs": [],
  "relevant_announcements": [],
  "blocked_sources": [],
  "forbidden_or_stale_sources": [],
  "supporting_sources_skipped": [],
  "inputs_complete": true,
  "parent_self_check_complete": true,
  "verdict": "proceed"
}
```

- The reconvergence gate has checked terminal reconnaissance artifacts: missing
  `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` must
  write a recover/blocking `review_a.json` or
  `stage_reviews/process_concerns.jsonl`.
- `spec.md` is grounded in Canvas snapshots and fetched references, not in the
  assignment title alone.
- `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json`
  explicitly records syllabus relevance, including assignment requirements,
  grading criteria, submission policy, late policy, AI/tool policy,
  academic-integrity constraints, or a reasoned `not relevant` judgment.
- If syllabus was fetched and used, `spec.md`, `investigation/rubric.md`, or
  `review_a.json` points to the preserved Canvas-native syllabus copy under
  `references/canvas_native/`.
- If Canvas-native assignment, syllabus, front-page, or page bodies are
  relevant, `references/canvas_native/` records verbatim `source.json`, readable
  `source.txt`, and provenance `ORIGIN.md`; summary-only output without
  preserved source copies is incomplete and blocks progression.
- Non-empty `review_a.json.relevant_announcements` entries must all be
  preserved `references/canvas_native/announcement-<id-or-slug>/source.json`
  paths. When no announcement is relevant, `relevant_announcements` must be
  `[]`.
- Any fetched PDF that was used as spec, rubric, input, or source-context
  evidence has sibling PDF link annotation manifests under
  `references/*.pdf.links.json` or `references/**/*.pdf.links.json`, even when
  the manifest is empty.
- `proposal/research/open-ended` runs have body-read evidence for
  assignment/spec sources and methods/topic-selection guidance, or
  `review_a.json` records why such guidance is unavailable. They also record
  whether supporting topic context was checked or explicitly judged unnecessary,
  and whether the reading budget stayed bounded or required a justified overrun.

### Spec Hard Requirements / No-Downgrade Policy

When `spec.md` or the authoritative reference states a hard requirement, source
intake must preserve the exact evidence so the planner cannot downgrade it later.
Hard requirements include any explicit `must`, `required`, `only`, `do not`,
exact filename/package/layout constraints, mandated
data/source/tool/template/class/style/citation rules, submission contents,
page/time limits, or grading-critical rubric conditions.

Do not rewrite a hard requirement into a softer fallback, preference, human
review item, or acceptable risk. If the current evidence is insufficient to meet
the requirement, the source artifacts must represent that as a blocker.

Record hard requirements in `spec.md` so downstream planning can preserve a
dedicated constraint block such as:

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

### [A4] Gate On Reconnaissance Quality

If `review_a.json.verdict` is not `proceed`, or `spec.md` does not clearly
state deliverables and main source judgment, planner alignment is limited to
recovery, supplement, or stop. Surface this recovery prompt:

> "I checked the assignment page, rubric, course front page, syllabus, modules,
> pages, linked files, and external URLs, but I still could not identify a
> complete spec. Options: paste the spec text or URL, point me to the correct
> module/page/file, or stop for now."

Do not proceed to planner pipeline design until the supplied recovery material
has been saved to the workbench and `spec.md`, `investigation/rubric.md`,
`investigation/review_a.json`, and `investigation/explore_context.md` have been
updated.

If syllabus could not be fetched, record the failure in
`investigation/unreachable.txt` or `stage_reviews/process_concerns.jsonl`
before planner handoff. If syllabus was fetched but not reviewed for relevance,
treat the reconnaissance as incomplete and do not hand off for normal planning.
If syllabus was fetched and reviewed but the only downstream evidence is a
paraphrase without a complete preserved Canvas-native source copy under
`references/canvas_native/`, or a documented blocked reason, treat the
reconnaissance as incomplete.

## Terminal Handoff

After this file completes successfully, continue by reading:

```text
sub-skills/tasks/assignment-workflow-planner.md
```

Do not execute draft-production stages here. This task ends when source intake
has produced the terminal reconnaissance artifacts and the next action is
planner alignment or recovery.
