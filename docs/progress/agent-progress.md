# Agent Progress

> Session-by-session handoff log. Newest entries on top. Anyone (including a future Claude session) reading this should be able to pick up cleanly.

## 2026-06-16 - Homework staged recon routing

Refined the homework router split into progressive-disclosure stages:
`do-homework.md` now routes only to `background-recon.md` for clean starts or
`existing-work-recon.md` for retained/repair/continue starts. The shared
`alignment-planning.md` stage is revealed only by the first-stage tail handoff,
so runtime agents do not preload alignment before source or existing-work recon
is complete.

## 2026-06-15 — reference_collector announcement boundary tightened

Tightened the homework reconnaissance contract after a UCUG1808 replay showed
`references/canvas_native/announcements/source.json` mirroring the full
`canvas/announcements.json` collection. The corrected contract is: Stage 1 keeps
the complete raw announcement snapshot; Stage 2 preserves only screened
task-relevant announcement objects under
`references/canvas_native/announcement-<id-or-slug>/source.json`, with
`REFERENCE_INDEX.md` origins such as `canvas/announcements.json#id=...`.

Also clarified that `reference_collector_used: true` must be backed by a real
`stage_reviews/child_dispatch_ledger.json` row, not a handwritten alias or an
empty ledger. Policy tests now cover both boundaries.

## 2026-06-15 — canvascli announcement contract synced into AutoStudy

Synchronized AutoStudy application-layer docs with fixed `canvascli` HEAD
`fd7a9a8`, whose history includes `21a39a7` for the announcements default
date-scope and concise CLI error behavior plus follow-up download/error/docs
commits. AutoStudy now documents the CLI boundary instead of copying Canvas
REST workarounds: announcements use `--course-id`, optional `--start-date` /
`--end-date`, latest-active-term complete snapshots from term dates first,
course dates second, Canvas default-window fallback only when both are
incomplete, and concise stderr / exit-code handling.

Verification installed `/Users/deepwisdom/Desktop/project/canvascli` into the
AutoStudy venv as editable. `.venv/bin/canvascli announcements --help` showed
`--course-id`, `--start-date`, and `--end-date`; live Canvas
`.venv/bin/canvascli announcements --course-id 2799` returned 23 items; forbidden
course 2177 exited 2 with empty stdout, concise `403 Forbidden` stderr, and no
Traceback. AutoStudy checks passed:
`.venv/bin/python -m pytest tests/test_source_body_audit_policy.py tests/test_pipeline_ready_scan_flow.py -q`
reported 13 passed, and `git diff --check` passed.

## 2026-06-14 — Generic Canvas instance support implemented

Implemented the first generic Canvas instance slice across `canvascli` and
AutoStudy. `canvascli init --canvas-url` now stores a web/API base pair and
keeps instance changes atomic on login failure; AutoStudy setup/API docs ask
for school/domain/Canvas URL, plan handoff preserves Canvas `html_url`, and
product positioning is generic Canvas LMS with HKUST(GZ) validation evidence.
Verification passed for both repos' unit/compile/help/json/diff checks, plus a
real browser login using a temporary `CANVASCLI_CONFIG_DIR` and HKUST(GZ) Canvas
web/API URL forms.

## 2026-06-13 — Pipeline-ready handoff and developer-entry boundary

Tightened homework reconnaissance docs after DSAA2011 runtime review: fetched
syllabus now must have raw JSON under `canvas/` plus a readable extract/text
export under `references/` when available, so downstream children and humans do
not need to parse Canvas JSON or rely only on compressed relevance notes.
Recorded `pipeline_ready` as the review-before-orchestration result state in
scan-plan tooling and moved developer-only guidance out of root `AGENTS.md`
into `docs/DEVELOPMENT.md`, leaving root `AGENTS.md` ignored for local overrides
so user-mode runtime agents do not load developer instructions.

## 2026-06-11 — Fresh-user clone target protocol

Fixed a fresh-user onboarding gap exposed by testing from an empty Codex project
folder: the prior quick start treated `~/workspace/autoust-dev` as the visible
example, which let an agent ignore the already-open empty workspace. `skill.md`,
README variants, and `PITFALLS.md` now require current-empty-folder clone first,
ask-before-clone when the target is unclear or non-empty, and treat
`~/workspace/autoust-dev` as an explicit example only. Next: rerun the public
fresh-start prompt from a new empty folder to confirm the agent chooses `git
clone ... .` or asks before choosing a different path. Changes are left
uncommitted for user review because this session requested bug analysis and a
targeted docs fix, not a commit.

## 2026-06-11 — Homework reconnaissance docs hardened

Cleaned runtime skill docs so homework reconnaissance no longer uses real
course validation cases as examples, avoiding task-specific prior-case leakage
into future runs. Strengthened syllabus handling across assignment recon and
do-homework: syllabus is now a first-class Canvas source, `spec.md` must record
syllabus relevance, `review_a.json` must report syllabus checks, and pipeline
planning may inherit syllabus constraints only through distilled current-run
evidence.

## 2026-06-11 — AIAA2711 course sync and notes generated

Synced AIAA2711 (L02) / Mathematics for AI from Canvas course `2799` into
`data/courses/AIAA2711/`: 39 files downloaded successfully, including 11 lecture
PDFs, 1 reading, and 27 other course files; Canvas returned 0 announcements and
the installed `canvascli` lacks the documented `modules` command. Generated 11
Obsidian-style Markdown lecture notes plus `notes/README.md`; verification
passed with 11/11 lecture PDFs covered by same-stem note files. Changes are
left uncommitted because the user requested local course materials and notes,
not a development commit.

## 2026-06-11 — README quick-start path cleanup

Updated `skill.md` and all README variants for beginner users: clarified that AutoStudy runs from a dedicated clone of this repository, not from a copied standalone `skill.md` or a machine-specific absolute path. At that point, quick starts still used `~/workspace/autoust-dev` as the visible example; the follow-up entry above supersedes that with the current-empty-folder-first protocol. Verification: stale path/prompt scan passes and diff whitespace checks pass.

## 2026-06-10 — Fresh-user sync-status to DSAA2011 validation

Ran a full development-validation simulation from the public user entry:
runtime coordinator B started at `skill.md`, ran `sync-status`, wrote the
2026-06-10 scan-plan artifacts, then handled the simulated user directly asking
for DSAA2011 Project even though Canvas marked it graded and omitted it from the
plan. The DSAA2011 active workbench was archived to
`archive/fresh-user-syncstatus-dsaa2011-cleanstart-2026-06-10/`, relaunched as a
clean_start with only `prelaunch_startup_inventory.json`, and regenerated
Canvas/source reconnaissance, `spec.md`, alignment, pipeline, real Student
Dropout experiments, 7 measured tuning rounds, report PDF, presentation PDF,
notebook, requirements, data evidence, and `draft/G01_StudentDropout.zip`.
`result.json` is `draft_ready`, `verification.log` records 35 PASS / 2 SKIP / 0
FAIL, and no Canvas submission was attempted.

Post-run A exported B plus all 10 runtime child transcripts by exact local
session match, then trajectory reviewer D dispatched 10 E transcript auditors.
Final process verdict was `PASS_WITH_CONCERNS`: artifact gates, child
dispatching, review ordering, transcript preservation, and no-submission checks
passed, but clean PASS is still blocked by B using a role-label coordinator
identity, transcript export requiring A fallback, one thread-limit spawn
recovery, startup/plugin reads in child transcripts, minor timestamp/schema
issues, and broader-than-ideal Canvas file metadata reconnaissance. Tracked docs
and runtime evidence were captured for follow-up review.

## 2026-06-10 — User-facing docs synced to unified runtime

Updated README, skill entry, roadmap, and marketing/messaging docs from the old
M3 MVP snapshot to the current M3.5+ assistant model: scan-plan first,
Canvas-grounded homework workbenches, post-recon alignment, dynamic
pipeline_design, executor/reviewer evidence, retained-artifact repair, and
course-material/note flows. Verification passed for feature-list JSON,
diff whitespace, and stale user-entry wording scans. Changes are intentionally
left uncommitted for user review because this session requested docs sync, not a
commit. Follow-up split README into three user-facing variants: default Chinese
full `README.md`, English full `README.en.md`, and compact Chinese
`README.quick.md`.

Follow-up sync snapshot cleanup moved the official current Canvas snapshots out
of top-level `data/*.json` into `data/sync/current/{courses,assignments,announcements}.json`;
old locally ignored top-level JSON snapshots were moved under `data/sync/archive/`.
Updated `write_scan_plan.py`, `sync-status`, `sync-course`, `do-homework`, and
user/developer docs to use the new path while preserving run-specific raw
evidence under `data/runs/<date>/raw/`.

Removed the obsolete standalone reconnaissance script and scrubbed active docs
of its path so runtime agents have only one homework reconnaissance contract:
agent-led assignment reconnaissance over atomic `canvascli` sources. Historical
progress wording was generalized where needed to avoid search-result confusion.
Renamed the former homework reconnaissance tool doc to
the assignment reconnaissance tool doc and updated tool registry, task docs,
runtime docs, README variants, and backlog references so the name matches its
current role: assignment reconnaissance rather than problem extraction.

## 2026-06-09 — Unified-flow docs prepared for branch push

Prepared the accumulated unified-flow documentation, DSAA2011 clean-start
validation evidence, and PDF figure-placement lesson for commit on
`codex/deepwisdom-updates`. Verification before staging covered
`docs/plans/feature-list.json`, Python script compilation, and `git diff --check`;
the original `tests/` directory is absent in the current worktree, so no unittest
suite was available to run.

## 2026-06-09 — DSAA2011 report figure float rendering traced

Investigated a DSAA2011 report rendering defect where the KMeans t-SNE figure
was clipped at a page boundary. Root cause was not the PNG or PDF viewer:
Pandoc converted consecutive large Markdown images into independent LaTeX
`figure` floats, and the TeX log showed `Overfull \vbox ... while \output is
active` near those figures. The report source now groups the KMeans and Ward
t-SNE plots into one atomic LaTeX figure block, rerendered PDF/zip artifacts
pass integrity checks, and `pdf-renderer.md` plus `PITFALLS.md` now warn that
`pdfimages` alone can miss clipped/drifted figures.

## 2026-06-09 — DSAA2011 clean-start unified-flow validation

Ran DSAA2011 Project as a fresh `clean_start` developer validation from an
active workbench containing only `archive/` plus accepted startup inventory.
Runtime coordinator B dispatched a pre-alignment `source_spec` explore scout,
regenerated `spec.md`/`problem.md`/references/explore evidence, used simulated
alignment supplements for the Student Dropout dataset, and produced local draft
artifacts with real code execution: executable notebook, metrics, 3-round
experiment iteration log, 13 figures, 7-page report PDF, 11-page presentation
PDF, requirements, dataset CSV, and source zip. No Canvas submission occurred;
`verification.log` records 28 PASS / 3 SKIP.

Process validation exported 9/9 runtime JSONL transcripts by exact local-session
agent-id match: coordinator B plus eight unique runtime children, including the
explore scout. Trajectory reviewer D dispatched eight E transcript auditors,
one per child transcript, and returned `PASS_WITH_CONCERNS`: accepted-path E
audits were PASS 1 / PASS_WITH_CONCERNS 6 / FAIL 0, while the single FAIL was
the intentionally superseded Stage 2 executor and supports B's replacement
decision. Clean PASS remains blocked by fallback transcript export, one
superseded forbidden-read child, ledger-authority identity normalization,
startup/plugin scope noise, and minor receipt/timestamp issues.

Follow-up structure report written to
`docs/verification/2026-06-09/dsaa2011-clean-start-structure-report.md`.
Post-run repo diff inspection also found runtime-era edits to
`docs/PITFALLS.md` and `sub-skills/tools/pdf-renderer.md`; the lesson about
PDF figure clipping is useful, but the write scope should be reviewed because
runtime homework children should not directly edit development docs/tool
contracts during a validation run.

## 2026-06-09 — Explore scout isolation checks synced

Closed a validation-doc gap introduced by the unified flow: pre-alignment
explore scouts are now treated as runtime children, not informal helper notes.
`development-validation-standard.md`, `runtime-agent-protocol.md`, Task 10/11,
`do-homework.md`, and `task-orchestrator.md` now require scout dispatch ledger
rows, scout receipts or manifest-listed equivalents, transcript export/audit
coverage, skipped-scout reasons, and D/E review of scout transcripts alongside
executor/reviewer children.

## 2026-06-09 — Unified flow abstraction drafted

Refactored the documented runtime model away from hard `full_flow` /
`repair_flow` branching. The shared shape is now archive/preflight, startup
inventory, explore stage, alignment contract, execution plan, and common
executor/reviewer/verification runtime. `full_flow` and `repair_flow` remain
legacy presets that map to `clean_start` and `retained_artifact_start`; scout
activation now depends on available inputs in the startup inventory. Runtime and
validation docs now name `investigation/explore_context.md` and
`investigation/explore_manifest.json` as the shared exploration interface.

## 2026-06-09 — Repair reconnaissance scout layer added

Synced repair-flow with the Superpowers-style context discipline: broad or
progress-sensitive repairs now run repair reconnaissance before `repair_plan.md`.
`runtime-agent-protocol.md`, `development-validation-standard.md`, and the Task
11 rollout plan now define read-only repair scouts for current draft state,
spec/intent, allowlisted process history, and lightweight verification, with
findings distilled into `investigation/repair_recon.md` before any repair
pipeline is planned.

## 2026-06-09 — Repair-flow alignment sync

Checked whether repair-flow had absorbed the new brainstorm-style alignment
contract from the UCUG1505 full-flow work. Full-flow was already synced, but the
repair-flow core docs still jumped too quickly from feedback to `repair_plan.md`;
`runtime-agent-protocol.md` and `development-validation-standard.md` now require
a repair alignment loop for open-ended/ambiguous/creative repairs, approach
comparison when meaningful, repair scope/design skeleton preview, and a richer
terminal `repair_plan.md` contract before `repair_pipeline_design.md`.

## 2026-06-09 — UCUG1505 full-flow local draft completed

Ran UCUG1505 FINAL project as a fresh `full_flow` local draft from a clean active
workbench without reading old Canvas submission attachments or submitting to
Canvas. Recon confirmed the Google Doc spec and documentation template, the
alignment loop selected `Parallel Me Booth`, and the pipeline produced a
structured Vite/React/TypeScript + Express source project, source zip,
342-word documentation PDF, video demo script, screenshot, verification log,
stage receipts, and `result.json` with status `draft_ready`.

Verification evidence is in `data/homework/UCUG1505/final-project/verification.log`.
Notable gates passed: `npm run verify`, backend tests, frontend/backend builds,
mock fallback generation, real API generation probe using the supplied local env
(`providerMode=real`, 4 panels, remote image URL), source zip integrity, and
secret scan with 0 source/zip hits. Remaining open items are human finalization:
partner name plus public video/code URLs. No commit was made in this session;
the only tracked uncommitted files are this progress note and the feature-list
evidence update for user review.

## 2026-06-09 — Alignment loop upgraded toward Superpowers brainstorming

UCUG1505 full-flow alignment testing showed that coordinator B2 could ask good
early questions but still converged to `alignment_brief.md` too soon after core
concept and provider choices. The missing contract was not another task
classification; it was Superpowers-style design development: each answer should
introduce new design dimensions, open-ended tasks should compare 2-3 approaches,
and the user should approve a design skeleton before the final brief.

`do-homework [B]` now defines recon summary as the user-facing compression of
`[A]` outputs, adds a design skeleton readiness audit, records
answer-driven implications in `user_notes.md`, requires approach comparison and
skeleton preview before `alignment_brief.md` for open tasks, and adds
placeholder/consistency/scope/ambiguity self-review. Runtime protocol,
task-orchestrator, and Task 10 validation prompts were updated to enforce the
same contract.

## 2026-06-08 — Development validation bridge for alignment loop

Clarified the two-line model for homework flow testing: real user-facing
runtime has only the Main Agent and its subagents, while development validation
wraps that runtime in outer Main Agent A, runtime coordinator B, child agents C,
and D/E trajectory review. `docs/development-validation-standard.md` now
requires A to bridge live simulated-user answers at `do-homework [B]` without
rewriting B's questions or turning `[DEV]` comments into user intent.

Task 10's coordinator prompt now includes explicit pause markers for testing the
multi-round alignment loop:
`WAITING_FOR_SIMULATED_USER_B_ROUND_<N>` and
`WAITING_FOR_ALIGNMENT_BRIEF_CONFIRMATION`. B may enter `[C]` only after A
forwards the user's confirmation of `investigation/alignment_brief.md`.

## 2026-06-08 — Post-recon alignment brief contract added

Redesigned `do-homework [B]` from a one-shot supplement checkpoint into a
post-recon alignment loop. The Main Agent now asks one drift-risk-reducing
question at a time, appends process notes to `investigation/user_notes.md`, and
writes `investigation/alignment_brief.md` only when it has no necessary
alignment question left; the brief must then be confirmed by the user before
`pipeline_design.md` and `task-orchestrator` run.

Updated the runtime protocol, task orchestrator, skill architecture, entry
skill, collaboration docs, AGENTS handoff, Canvas Pilot reference notes, and
feature list so confirmed `alignment_brief.md` is the task-level user-intent
input. Course-level and user-level preference layers remain pending.

## 2026-06-08 — Repair flow model simplified

Simplified the validation mode model to two active modes: `full_flow` and
`repair_flow`. Broad rewrites, dataset swaps, rerun experiments, regenerated
artifacts, and versioned outputs are now handled inside `repair_flow` when they
are based on an existing user-visible draft or workbench. The coordinator must
express the actual scope dynamically in `repair_plan.md` and
`repair_pipeline_design.md`; the plan contract is task-agnostic and records
retained context, forbidden context, repair objectives, planned changes,
unchanged/out-of-scope targets, verification criteria, dependency order, and
stop conditions rather than assuming notebook/report/slides/package artifacts.

## 2026-06-08 — DSAA2011 Task 11 repair-flow iteration 2

Ran the second DSAA2011 `repair_flow` validation as an experiment-focused
repair. The active workbench was archived to
`archive/nested-isolation-2026-06-08-repairflow-iter2-experiment-repair-rollback/`,
stale repair/runtime evidence was removed from active startup context, and
`prelaunch_startup_inventory.json` declared simulated feedback asking for
human-like iterative ML experimentation rather than another report-only repair.

Runtime repair coordinator B `019ea52f-9253-7aa0-b55c-932b48f70b29` wrote fresh
`repair_plan.md` and `repair_pipeline_design.md`, dispatched seven runtime
children, and completed a targeted repair. The notebook was modified and rerun
with zero error outputs, `draft/experiment_iteration_log.json` records four
hypothesis/change/result/decision iterations, `draft/metrics.json` now records a
constrained random forest selection, `experiment_comparison.png` was added, the
report/slides PDFs were regenerated, the zip includes metrics, experiment log,
figures, notebook, report, slides, requirements, and data, and `verification.log`
has 25 PASS lines, 0 FAIL lines, and 2 manual SKIP lines. No Canvas submission
was attempted.

Main Agent A mechanically exported 8/8 runtime ordinary-spawn JSONL transcripts
for B plus all seven C children, then trajectory reviewer D
`019ea557-3280-7673-983c-df4327af8c23` dispatched seven E transcript auditors,
one per runtime child transcript. A then exported 8/8 review-chain transcripts
for D plus all E auditors. D wrote
`stage_reviews/nested_isolation_trajectory_review_repairflow_iter2_experiment.json`
with verdict `PASS_WITH_CONCERNS`; E receipt distribution was `PASS: 2` and
`PASS_WITH_CONCERNS: 5`. Artifact gates passed, but clean process `PASS` is
blocked because B's final verification used an absolute-path `rg` command whose
archive exclusion failed and printed archive transcript/content matches into the
runtime transcript. Docs now require active-workbench searches to use relative
paths from the workbench or explicit `find ... -prune`, and to treat archive
content exposure as a clean-PASS blocker even when task decisions were not
influenced.

## 2026-06-07 — DSAA2011 Task 11 repair-flow iteration 1

Ran the first DSAA2011 `repair_flow` validation from the retained full-flow
first draft. The active workbench was archived to
`archive/nested-isolation-2026-06-07-repairflow-iter1-restart1-repair-rollback/`,
old process evidence was removed from active startup context, and
`prelaunch_startup_inventory.json` declared the simulated feedback: the first
draft was complete but the report was too short and the experiment discussion
needed more depth.

Runtime repair coordinator B wrote `repair_plan.md` and
`repair_pipeline_design.md`, dispatched a repair executor child, and the draft
was repaired without a full rerun: report Markdown grew to 3,242 words, report
PDF to 8 pages, presentation PDF to 12 pages, render provenance stayed under
`draft/render/`, the zip passed `unzip -t`, notebook error outputs remained
zero, and no Canvas submission was attempted. The original coordinator stalled
after child execution, so Main Agent A closed it and dispatched replacement
coordinator B2, which recorded `replacement_coordinator_recovery` in
`stage_reviews/child_dispatch_ledger.json`, preserved the original coordinator
and child ids, accepted current-run receipts with explicit recovery evidence,
and wrote `result.json` with status `DONE_WITH_CONCERNS`.

Main Agent A mechanically exported 5/5 runtime local-session JSONL transcripts
and 4/4 review-chain transcripts by exact propagated agent-id match. Trajectory
reviewer D `019ea21b-0e49-7480-82ac-ce3d829ac39f` dispatched three transcript
auditor children E, one per runtime child transcript, and wrote
`stage_reviews/nested_isolation_trajectory_review_repairflow_iter1_restart1.json`
with overall verdict `PASS_WITH_CONCERNS`. Artifact gates and E coverage passed,
but clean `PASS` is blocked by coordinator replacement/transport recovery,
executor accepted with transport recovery, ledger-authority child identity
normalization, and non-impacting external startup skill reads in child
transcripts.

Follow-up cleanup tightened repair startup hygiene: old full-flow
`pipeline_design.md` is no longer retained in active root for repair starts.
It should be archived with rollback evidence, while active repair planning uses
`repair_plan.md` plus `repair_pipeline_design.md`. The completed DSAA2011 active
root was cleaned accordingly by moving the old full-flow pipeline to
`archive/nested-isolation-2026-06-07-repairflow-iter1-restart1-repair-rollback/postrun-active-cleanup/pipeline_design.full_flow.md`
with a README explaining that this was post-run organization, not a rewrite of
the launch inventory. The same cleanup moved `investigation/review_a.json` to
`postrun-active-cleanup/investigation/review_a.full_flow.json` because it is a
full-flow reconnaissance review receipt, while `investigation/rubric.md` and
`investigation/user_notes.md` remain valid repair context.

## 2026-06-07 — Repair flow validation contract drafted

Defined `repair_flow` and `revision_flow` separately from `full_flow`.
`repair_flow` starts from a user-visible first draft plus concrete feedback,
archives the active workbench as rollback evidence, removes stale process
evidence from active startup context, retains only explicit current-draft files,
and requires the coordinator to write a repair request/plan before dispatching
repair children. `revision_flow` is broader next-version work and must declare
whether outputs are edited in place or written to a versioned directory.

Added Task 11 to the stage-review rollout plan for a DSAA2011 repair-flow
validation. The suggested simulated feedback is: the first draft is complete,
but the report is too short and experiment discussion is not deep enough; repair
the current draft toward a stronger 8-9 page submission, deepen the experiment
discussion, update slides/render/package, do not submit to Canvas, and do not
redo the assignment from scratch. The B/C/A/D/E transcript evidence chain stays
the same as Task 10, while D/E additionally audit retained context, rollback
archive discipline, targeted repair scope, changed-file justification, and
no-regression gates.

## 2026-06-07 — Task 10 read-scope rule changed to blacklist-first

Clarified the clean-PASS read-scope rule after reviewing DSAA2011 iteration 9.
Stage reviewers should not be constrained by a brittle fixed whitelist of exact
files for every assignment type. Required/allowed reads are expected starting
evidence, while current-run artifacts directly relevant to the assigned stage or
reviewed deliverable may be inspected. The hard boundary is the blacklist:
archive/prior-run evidence, prior diagnostics, development-plane docs,
validation plans/progress docs, external workflow/plugin skill files as task
context, coordinator-owned ledgers, and unrelated workbench evidence. The Stage
2 spec reviewer reading report/slides render provenance under `draft/render/`
is therefore task-relevant, not a clean-PASS blocker; future E audits should
focus on whether any forbidden class was read or used as task evidence.

## 2026-06-07 — DSAA2011 Task 10 ordinary-spawn full-flow iteration 9

Ran DSAA2011 Task 10 again in `full_flow` mode with ordinary
`multi_agent_v1.spawn_agent`. The active workbench was archived to
`archive/nested-isolation-2026-06-07-fullflow-iter9-prelaunch-archive/`,
cleaned to only `archive/` plus `prelaunch_startup_inventory.json`, and the
inventory recorded `archive/` as forbidden startup context for runtime
coordinator B and runtime children C. Runtime coordinator B
`019ea141-e235-7541-a011-138db659c42a` regenerated reconnaissance,
`spec.md`, `problem.md`, `pipeline_design.md`, stage briefs, draft artifacts,
verification files, and `result.json` with status `draft_ready`; no Canvas
submission was attempted.

The post-iteration-8 fixes largely held. The runtime dispatch ledger has seven
accepted child dispatches, all with `identity_injected_at_utc`,
`receipt_observed_at_utc`, and `accepted_at_utc`; review receipts include
`review_type`, `depends_on_stage_result`, and `depends_on_spec_review`; and the
Stage 2 no-id spawn failure caused by the thread limit was recorded in ledger
`process_events` and replaced by a clean dispatch. Main Agent A mechanically
exported 8/8 runtime JSONL transcripts and 8/8 review-chain JSONL transcripts
by exact local-session id match, with zero missing or ambiguous exports.

Trajectory reviewer D `019ea16c-e635-7dc1-8e9f-2a4cf6ad9b55` dispatched seven
transcript-auditor children E, one per runtime child transcript, and returned
`PASS_WITH_CONCERNS`; all seven E receipts were `PASS_WITH_CONCERNS`. Artifact
gates passed: report Markdown references six figures, the report PDF embeds six
image objects, figures are organized under `draft/figures/`, render `.tex` and
`.log` provenance is retained under `draft/render/`, the notebook has zero
error outputs, and the zip contains the required deliverables. Remaining
clean-PASS blockers are platform startup/plugin or AGENTS context appearing in
transcripts without task influence, imprecise receipt timestamps, one limited
`draft/render/` over-read by a spec reviewer, and runtime plus review-chain
no-id spawn events from thread limits despite correct process-event recovery.

## 2026-06-07 — Post-iteration-8 clean-PASS contract hardening

Updated the validation/runtime docs after DSAA2011 Task 10 iteration 8 returned
`PASS_WITH_CONCERNS`. The scope-hygiene rule now distinguishes avoidable
runtime contamination from unavoidable host-platform startup/plugin reads:
runtime-facing prompts and stage briefs should avoid naming development workflow
frameworks, and a platform-mandated startup read with no task influence is an
environment limitation rather than a clean-PASS blocker. Active use of external
workflow skills, development docs, validation plans, prior diagnostics, or
archive evidence as task material remains a process concern or failure.

Also hardened the concrete process gaps from iteration 8. `task-orchestrator.md`
now requires stage briefs to include exact receipt JSON skeletons, reviewer
receipts to include `review_type`, `depends_on_stage_result`, and
`depends_on_spec_review`, coordinator ledgers to add `receipt_observed_at_utc`
and `accepted_at_utc` when receipts are parsed and accepted, optional child id
injection via `send_input` when available, and a coordinator-owned
`process_events` entry for spawn attempts that fail before returning a child id.
Next DSAA2011 full-flow validation should verify these changes before moving to
another assignment.

## 2026-06-07 — DSAA2011 Task 10 ordinary-spawn full-flow iteration 8

Ran DSAA2011 Task 10 again in `full_flow` mode using ordinary
`multi_agent_v1.spawn_agent`, not the inspectable Codex-thread harness. The
active workbench was emptied before launch and the accepted startup inventory
recorded `archive/` as post-run audit-only evidence forbidden to runtime
coordinator B and runtime children C. Runtime coordinator B
`019ea05c-7172-70f1-b71a-5d73a7a9f27e` regenerated Canvas reconnaissance,
`spec.md`, `problem.md`, `pipeline_design.md`, stage briefs, draft artifacts,
verification files, and `result.json` with status `draft_ready`; Canvas
submission was not performed.

Main Agent A mechanically exported 9/9 runtime local-session JSONL transcripts
from `.codex/sessions` by exact propagated agent-id match: B plus eight runtime
children, with zero missing or ambiguous exports. Trajectory reviewer D
`019ea088-42bf-7770-b9f7-399b7a09264a` dispatched eight transcript-auditor
children E, one per runtime child transcript; A then exported 9/9 review-chain
JSONL transcripts for D plus all E auditors. D wrote
`stage_reviews/nested_isolation_trajectory_review_fullflow_iter8.json` and
returned `PASS_WITH_CONCERNS`; all eight E audit receipts were
`PASS_WITH_CONCERNS`.

Artifact gates passed: report Markdown references seven figures, the report PDF
contains embedded image objects for all seven figures, render `.tex`/`.log`
provenance is preserved under `draft/render/`, the notebook has 11 executed code
cells and no error outputs, the zip contains report PDF, presentation PDF,
notebook, requirements, and data CSV, and no Canvas submission occurred.
Remaining clean-PASS blockers are process hardening items: repeated Superpowers
startup/process skill reads by B/C despite no task-context contamination, child
ledger rows missing `receipt_observed_at_utc` and `accepted_at_utc`, review
receipts missing explicit dependency fields, all child identities relying on
coordinator normalization from `agent_id: null` plus ledger authority, minor
role/delegation schema normalization in Stage 2, and one failed no-id spawn
retry visible only in the coordinator transcript rather than as a process event
in the ledger.

## 2026-06-07 — Task 10 clean-PASS gates hardened after DSAA2011 iteration 7

Hardened the Task 10 validation and runtime contracts for the five concerns
found in DSAA2011 ordinary-spawn full-flow iteration 7. The docs now require
explicit transport-recovery states and evidence checks; coordinator-only writes
to `stage_reviews/child_dispatch_ledger.json`; child receipt identity as either
an exact runtime id or `agent_id: null` plus `identity_authority`, never alias
ids such as `C4`; child scope hygiene forbidding Superpowers/development-plane
reads unless listed in the brief; and UTC timestamp fields on result/review
receipts plus dispatch ledger entries. Clean Task 10 `PASS` now requires no
transport recovery, no child-side ledger writes, no alias ids, sufficient
ordering timestamps, and no scope-hygiene drift.

## 2026-06-06 — DSAA2011 Task 10 ordinary-spawn full-flow iteration 7

Ran DSAA2011 Task 10 in `full_flow` mode from the accepted no-leak startup
inventory using ordinary `multi_agent_v1.spawn_agent`, not the inspectable
Codex-thread harness. Runtime coordinator B
`019e9c80-26c7-7a10-abde-161e62e89b8e` regenerated reconnaissance, `spec.md`,
`pipeline_design.md`, stage briefs, draft artifacts, package manifest, final
`verification.log`, and `result.json` with status `draft_ready`; Canvas
submission was not performed. Main Agent A then mechanically exported 17/17
runtime local-session JSONL transcripts from `.codex/sessions` using exact
agent-id filename matches, including B plus accepted and superseded child ids,
with zero missing or ambiguous exports.

Independent trajectory reviewer D `019e9cd6-bab9-77a3-8870-dcddc8f94d4a`
dispatched 16 transcript-auditor children E and wrote 16 transcript-body audit
receipts; A also exported D plus all E auditor JSONL transcripts under
`transcripts/review_chain/` with zero missing or ambiguous matches. D returned
`PASS_WITH_CONCERNS`: artifact gates passed (figures under `draft/figures/`,
report figures embedded, render provenance preserved, zip/manifest parity, no
Canvas submission), but process concerns remain around frequent receipt identity
normalization, Stage 4 duplicate ledger pollution, transport-recovery acceptance
for one quality reviewer, child scope hygiene drift from reading Superpowers
startup instructions, and missing `created_at` timestamps in many review
receipts.

## 2026-06-06 — Task 10 nested transcript evidence role chain clarified

Updated `docs/development-validation-standard.md`,
`docs/runtime-agent-protocol.md`, and
`docs/superpowers/plans/2026-06-04-stage-review-rollout.md` to preserve the
initial nested-transcript role-chain consensus. Task 10 explicitly validates the chain
`Main Agent A -> runtime coordinator B -> runtime child agents C*`, followed by
`Main Agent A` exporting B and every C by propagated child identity, then
dispatching trajectory review coordinator D, which must dispatch one
transcript-auditor child E per exported C transcript. The key operational rule
was later corrected by controlled probes below: ordinary `spawn_agent` ids are
not Codex app `read_thread` ids. Missing child id propagation is still a process
failure, but transcript export for ordinary `spawn_agent` children must use
local-session JSONL exact-match export rather than `read_thread`.

Follow-up clarification: `read_thread` transcript collection must use cursor
pagination. A single call can return only the latest/finalize turns, so future
Task 10 full-flow runs must page older turns until the initial assignment prompt
is captured or no cursor remains. `transcripts/transcript_inventory.json` should
record page count, `pagination_complete`, and stop reason for each coordinator,
runtime child, trajectory reviewer, and transcript-auditor thread.

Second clarification after controlled probes: ordinary
`multi_agent_v1.spawn_agent` returns a multi-agent agent id, not a Codex app
`read_thread` id. The agent id works for `multi_agent_v1.wait_agent` /
`resume_agent` final status, and a full local session JSONL exists under
`.codex/sessions/**/<agent_id>.jsonl`, but `codex_app.read_thread` rejects these
ids. Inspectable Codex-thread harness children are real Codex app threads and
can be read with `read_thread`, but they create visible project conversations;
those can be archived after export, though they still exist. For the next
DSAA2011 full-flow iteration, use ordinary `spawn_agent`: A acts only as a
mechanical local-session JSONL export broker, while D/E perform semantic
transcript audits over the exported raw JSONL files.

## 2026-06-06 — DSAA2011 Task 10 iteration 6 prelaunch paused for review

Prepared the next DSAA2011 Task 10 `full_flow` validation using the inspectable
Codex-thread transcript harness. Archived the previous active iteration-5
workbench outputs to
`data/homework/DSAA2011/project/archive/nested-isolation-2026-06-06-fullflow-iter5/`
and removed generated active startup context (`canvas/`, `references/`,
`investigation/`, `draft/`, `stage_briefs/`, `stage_results/`,
`stage_reviews/`, `transcripts/`, `spec.md`, `problem.md`,
`pipeline_design.md`, prior summaries, verification files, and `result.json`).
Wrote
`data/homework/DSAA2011/project/prelaunch_startup_inventory_pending.json` with
`no_leak_check.status: PASS` and stopped before coordinator dispatch for human
startup review, per `docs/development-validation-standard.md`.

## 2026-06-06 — DSAA2011 Task 10 full-flow iteration 5 coordinator run

Follow-up transcript toolchain probe wrote evidence under
`docs/verification/2026-06-06/transcript-toolchain-probe/`. A parent subagent
spawned one nested child with marker `TRANSCRIPT_PROBE_MARKER_20260606_PARENT_CHILD`;
the child receipt exists, but the parent had no read/export transcript tool.
Main-thread `codex_app.read_thread` could read the current Codex app thread as
a control, but rejected both the top-level `multi_agent_v1` parent id and nested
child id with `invalid arguments`, and `list_threads` found no `019e9be1`
mapping. This confirms the current gap is a tool/id-domain gap, not just a
DSAA2011 workflow issue.

A second probe found an implementable workaround: inspectable Codex-thread
children. `codex_app.create_thread` threads are readable with
`codex_app.read_thread` while still active, but completed probes are not
reliably readable afterward. The working harness is therefore
pause-before-final: the child writes its receipt and `trace_bundle.json`, emits
`READY_FOR_TRANSCRIPT_EXPORT`, the parent exports `read_thread` evidence under
`transcripts/`, and only then sends a finalize message. The harness contract is
now documented in `docs/inspectable-subagent-transcript-harness.md`, with local
probe evidence in
`docs/verification/2026-06-06/transcript-toolchain-probe/inspectable_harness_probe_result.json`.

Ran Task 10 in `full_flow` mode from the accepted no-leak startup inventory
`data/homework/DSAA2011/project/prelaunch_startup_inventory.json`, with stable
coordinator id `019e9b2e-8139-7332-9a3e-f8a2affe6209` recorded in both
`nested_isolation_coordinator_summary.md` and `stage_reviews/child_dispatch_ledger.json`.
The coordinator regenerated Canvas reconnaissance, `spec.md`, `problem.md`,
`investigation/`, `pipeline_design.md`, stage briefs, draft artifacts,
`verification.log`, `result.json`, and a 21-child dispatch ledger; final
`result.json.status` is `draft_ready`, and Canvas submission was not attempted.

Nested isolation evidence is stronger than iteration 4 at the receipt level:
the ledger has 5 executors, 2 repair executors, 7 spec reviewers, and 7 quality
reviewers with zero dispatch/receipt identity mismatches after coordinator
normalization. Two blocking auto-fixable quality failures were repaired before
handoff: Stage 1 supervised preprocessing leakage and Stage 2 report figure
float/localized-label issues. Full child transcript export was still unavailable
inside the coordinator tool surface, so transcript paths remain null and the
main-thread collector fallback must use the stable child ids in the ledger.

Main-thread transcript fallback then wrote
`transcripts/transcript_inventory.json` and
`transcripts/NO_FULL_CHILD_TRANSCRIPT_EXPORTS_AVAILABLE.md`. Direct-parent
export was unavailable, and sampled `codex_app.read_thread` /
`codex_app.list_threads` probes could not map the `multi_agent` coordinator or
child ids to readable Codex app threads. Independent trajectory review wrote
`stage_reviews/nested_isolation_trajectory_review_fullflow_iter5.json` with
`PASS_WITH_CONCERNS`: receipt-level isolation and artifact gates passed, but
full child transcript bodies remain unavailable and 19 of 21 child receipts
needed coordinator normalization. Follow-up hardening is now in
`docs/development-validation-standard.md`, `docs/runtime-agent-protocol.md`,
Task 10, `task-orchestrator.md`, `pdf-renderer.md`, and `canvascli-api.md`:
fallback inventories must be machine-readable, receipt normalization is a
process concern when frequent, child-thread cleanup must preserve ledger
evidence, report reviews must catch figure float/localized-label issues, render
log sidecar policy is explicit, and `canvascli assignments` uses `--course-id`.

## 2026-06-05 — DSAA2011 Task 10 full-flow iteration 4

Ran Task 10 in `full_flow` mode from a no-leak active workbench after restoring
the Canvas session. The runtime coordinator re-created Canvas reconnaissance,
`spec.md`, `problem.md`, `investigation/`, `pipeline_design.md`, draft
artifacts, 21 stage briefs, 7 stage result receipts, 14 review receipts, and a
20-entry child dispatch ledger. Final `result.json.status` is `draft_ready`;
Canvas submission was not attempted.

Artifact quality improved over the earlier DSAA2011 runs: generated figures are
organized under `draft/figures/`, `draft/report.md` references 8 representative
figures, `pdfimages` confirms embedded report images, `draft/render/report.tex`
and `report_render_provenance.json` are present, and
`draft/G01_student_dropout.zip` matches `package_manifest.json` by entries,
sizes, and SHA256 hashes. The coordinator triggered and re-reviewed two
blocking auto-fixable repairs: Stage 1 notebook inline-figure/warning cleanup
and Stage 2 report confusion-matrix coverage.

Independent trajectory review wrote
`stage_reviews/nested_isolation_trajectory_review_fullflow_iter4.json` with
verdict `PASS_WITH_CONCERNS`: receipt-level isolation passed with 20 distinct
child ids and no ledger/receipt identity mismatches, but no full child
transcript exports were available, so no transcript-auditor subagents could be
dispatched. New process hardening from this run: future full-flow launches must
write a `prelaunch_startup_inventory.*` artifact, inject the coordinator's
stable thread id into coordinator evidence after dispatch, separate
blocking-auto-fixable issues from optional polish, and record PDF log-sidecar
absence through render provenance rather than leaving it ambiguous.

Follow-up tool inspection found that the Main Agent can read at least some
nested child threads directly by ledger id with Codex `read_thread`, even when
`list_threads` cannot discover those ids and the coordinator lacked an
export-thread tool. The validation standard, runtime protocol, and Task 10 now
require a two-level transcript collector: direct-parent coordinator export
first, then Main Agent / trajectory reviewer fallback from
`child_dispatch_ledger.json` stable child ids before declaring full child
transcripts unavailable.

## 2026-06-05 — Task 10 full-flow launch hygiene clarified

During DSAA2011 Task 10 iteration-4 preflight, the intended validation mode was
clarified: "run the task again" means a full real-user flow unless explicitly
scoped as resume or repair. The active workbench must therefore not retain
generated `draft/`, `canvas/`, `references/`, `investigation/`, `spec.md`, or
`pipeline_design.md` as hidden startup context for `full_flow`; those files are
outputs of the user-facing homework flow and can leak prior conclusions.

`docs/development-validation-standard.md` now holds the cross-task Development
Validation Standard, and Task 10 references it instead of carrying the standard
inline. It requires declaring `full_flow`, `resume_flow`, or `repair_flow`,
archiving prior evidence, cleaning no-leak startup files according to that
mode, stopping before coordinator dispatch for human review of the startup
inventory, passing user supplements explicitly rather than hiding them in
workbench files, and applying the same child trajectory/process review standard
when changing from DSAA2011 to any later validation task.

## 2026-06-05 — DSAA2011 report/asset quality gap analysis

Follow-up inspection of the DSAA2011 draft found that `draft/report.md` has no
image references and `pdfimages` reports 0 embedded images in
`report_G01_dropout.pdf`, while the notebook, slides, and zip contain 12 plot
PNGs. Root cause: the notebook saved plots as flat `draft/*.png`, while
`writing-helper.md` expected organized `figures/*` assets and the report quality
review treated a text-only report as acceptable because other deliverables had
the visuals. Tool contracts now prefer `draft/figures/`, require experimental
reports to embed representative available figures, classify available-but-omitted
figures as an `auto_fixable` quality issue, and add `pdfimages`/visual checks to
report verification.

The current report PDF was rendered through pandoc's native XeLaTeX path
(`Creator: LaTeX via pandoc`, `Producer: xdvipdfmx`). No `.tex` file is present
because `pandoc --pdf-engine=xelatex` uses temporary intermediate TeX by
default; this was not an intentional deletion. `pdf-renderer.md` now requires
render-engine provenance in receipts, optional `draft/render/` sidecars for
debuggable TeX/log output, and resource-path handling for report-local figures.
Transcript export handling was also clarified: top-level subagent threads can
be read with Codex `read_thread`, but nested child/grandchild ids from a
coordinator were not discoverable from the main thread, so transcript export
must be performed by the direct parent coordinator before closing children when
that tool surface is available.

Verification after the contract changes: `python3 -m json.tool` passed for
`docs/plans/feature-list.json`, runtime receipt examples, current
`data/homework/DSAA2011/project/result.json`, and all JSON files under current
`stage_results/` and `stage_reviews/`. The child dispatch ledger re-check found
9 accepted child receipts, 9 transcript audit receipts, no `stage`/agent-id
mismatches, and trajectory verdict `PASS_WITH_CONCERNS`; `git diff --check`
reported no whitespace issues for the tracked files touched in this follow-up.

## 2026-06-05 — DSAA2011 Task 10 iteration 3 passed receipt-level isolation

Re-ran Task 10 on `data/homework/DSAA2011/project` after archiving iteration 2
evidence to `archive/nested-isolation-2026-06-05-iter2/`. The coordinator
regenerated a 5-stage `pipeline_design.md`, wrote 15 stage briefs, 5 stage
result receipts, 10 review receipts, `child_dispatch_ledger.json`,
`verification.log`, `result.json`, and a new
`nested_isolation_coordinator_summary.md`. Three executor, three spec reviewer,
and three quality reviewer child receipts matched the coordinator-authoritative
dispatch ledger for `stage`, `agent_id`, and transcript handle; no inline
fallback appeared. Stage 4/5 package repair and post-repair verification were
represented by first-class `SKIPPED` result receipts and review `SKIP`
receipts because package/current-file hashes already matched.

The independent trajectory reviewer dispatched 9 per-child receipt-level
auditor subagents under `stage_reviews/transcript_audits_iter3/` and returned
`PASS_WITH_CONCERNS`: receipt-level nested isolation, identity consistency,
review ordering, skip receipts, and package parity checks passed. The verdict
cannot rise to `PASS` because full child transcript bodies/exports are still
unavailable. Remaining process observations: standby-only child responses are
still common and must remain superseded attempts in the ledger; completed child
agents should be closed between waves to avoid thread pressure; `verification.log`
should not use `FAIL` for the correct decision to withhold `draft_ready`; and
transcript-audit receipt field types need to stay explicit.

## 2026-06-05 — DSAA2011 Task 10 iteration 2 failed on identity drift

Re-ran Task 10 on `data/homework/DSAA2011/project` after archiving the previous
Task 10 evidence to `archive/nested-isolation-2026-06-05-iter1/`. The runtime
coordinator regenerated `pipeline_design.md`, produced 18 stage briefs, 4 stage
result receipts, 8 review receipts, and repaired a blocking `auto_fixable`
Stage 2 coverage gap through `stage_02a_content_coverage_repair` before final
handoff. Package/current-file parity was checked and already matched, so the
package repair stage did not trigger; `result.json.status` remains
`revision_needed` only for external/manual/skipped-submission items.

The independent trajectory reviewer dispatched 12 transcript-auditor subagents
and returned `FAIL`, not `PASS_WITH_CONCERNS`, because the Stage 2 executor
receipt recorded `agent_id: 2896E6E0-DFB6-43C2-80D8-6CDC06EFA33D` while the
coordinator summary recorded child agent id
`019e9619-aa14-7023-a4be-230271a0a729` for the same transcript handle. This
exposed a new workflow gap: child receipts cannot be trusted to self-report
agent identity. The protocol, `task-orchestrator.md`, and Task 10 now require
coordinator-authoritative dispatch ids, receipt normalization before acceptance,
identity mismatch handling as `BLOCKED`, and first-class `SKIPPED` receipts for
conditional stages whose trigger is false. Other process observations: full
transcript exports are still unavailable, many receipts drifted from `stage` to
`stage_id`, and the coordinator hit a child-thread limit that required cleanup.

## 2026-06-05 — DSAA2011 true nested subagent isolation validation

Ran Task 10 on `data/homework/DSAA2011/project` with a runtime coordinator
subagent simulating the real AutoStudy Main Agent flow. The coordinator archived
old inline/runtime artifacts to
`archive/nested-isolation-2026-06-05-prep-old-inline/`, regenerated
`pipeline_design.md` with `nested_subagents_policy:
true_child_subagents_required_no_inline_fallback`, generated 15 stage briefs,
and dispatched distinct child executor/spec-reviewer/quality-reviewer subagents
for all five stages.

Evidence now includes 5 executor receipts, 5 spec review receipts, 5 quality
review receipts, `nested_isolation_coordinator_summary.md`,
`stage_reviews/nested_isolation_trajectory_review.json`, `verification.log`,
`verification_checklist.md`, and `result.json`. Local verification and an
independent main-thread trajectory reviewer both returned
`PASS_WITH_CONCERNS`: no `inline_fallback` or `main-agent` execution appeared in
the current receipts, every normal receipt preserved `agent_id`/`transcript`,
and quality reviews depended on matching PASS spec reviews. Keep
`M3.5-EXECUTION-ARCHITECTURE` in-progress for now while running the second true
nested validation on UCUG1505. The DSAA2011 concerns were folded back into
`docs/runtime-agent-protocol.md`, `sub-skills/tasks/task-orchestrator.md`, the
runtime examples, and Task 10: full transcript exports are now preferred when
available, coordinator identity must be stable, and standby/empty child-agent
responses are non-completion anomalies rather than passing evidence. Task 10
was further tightened so the runtime coordinator uses the user-facing
`skill.md` / task docs instead of treating `docs/runtime-agent-protocol.md` as a
runtime manual, while the trajectory reviewer uses the protocol only as an audit
standard and dispatches one transcript-auditor subagent per available child
transcript before making a final verdict.

The same DSAA2011 run exposed a more important workflow gap: the model detected
an auto-fixable package parity issue (`G01_dropout.zip` contained a notebook
that differed from the freshly executed on-disk notebook) but the Stage 5 brief
was verification-only, had `max_retries: 0`, and allowed only receipt writes.
The issue was therefore recorded as a concern instead of triggering a package
rebuild and re-review. The protocol and `task-orchestrator.md` now define
repair-before-revision: reviewers classify issues as `auto_fixable`,
`needs_user_input`, `manual_only`, `external_blocker`, or `acceptable_risk`;
blocking `auto_fixable` issues must trigger a fix executor or bounded repair
stage before final handoff and must not be hidden inside `revision_needed`.

## 2026-06-04 — UCUG1505 runtime validation false-pass check

Archived stale UCUG1505 runtime evidence under `data/homework/UCUG1505/final-project/archive/runtime-validation-2026-06-04/`, regenerated a fresh pipeline with 15 stage briefs, 5 stage results, 8 reviews, `verification_checklist.md`, `verification.log`, and `result.json`. Localhost browser validation actually loaded the p5.js draft and captured zero dev-log entries, but microphone/audio interaction, public video upload/link, public code link, and exact documentation-template compliance remain blockers; `scripts/write_homework_result.py --status revision_needed` succeeded and no Canvas submission happened.

Iteration 2 archived that runtime evidence under `data/homework/UCUG1505/final-project/archive/runtime-validation-2026-06-04-iter1/`, regenerated `pipeline_design.md`, 15 stage briefs, 5 stage results, 10 review/skip receipts, `verification_checklist.md`, `verification.log`, and `result.json`. The code package link is now detected in both `draft/documentation.md` and extracted `draft/documentation.pdf` text; final status remains `revision_needed` via `scripts/write_homework_result.py` because no public YouTube/Vimeo URL or local video exists, the official template is still unreachable, microphone interaction is manual, and Browser screenshot/pixel proof still hit tooling limits.

Uncommitted changes remain because this validation updated local/gitignored UCUG1505 runtime evidence plus the ongoing protocol rollout docs already in the worktree; no commit was requested.
`M3.5-EXECUTION-ARCHITECTURE` remains `in-progress`, not `passing`, because
DSAA2011/UCUG1505 validated the file-based protocol and false-pass resistance
through inline fallback, but true nested executor/reviewer subagent isolation
still needs one preserved transcript/evidence run.
Follow-up clarified the gap in plain terms: normal runtime docs already require
the Main Agent to dispatch executor/spec-reviewer/quality-reviewer subagents,
but the validation harness had used a runtime coordinator subagent while the
protocol still said ordinary subagents must not dispatch children. Added a
development-only validation harness exception in `docs/runtime-agent-protocol.md`
and Task 10 in
`docs/superpowers/plans/2026-06-04-stage-review-rollout.md`; Task 10 requires
real child executor/reviewer subagent ids or transcripts and treats
`inline_fallback` as non-passing isolation evidence.

## 2026-06-04 — DSAA2011 runtime validation iteration 3

DSAA2011 iteration-2 runtime evidence was archived under `data/homework/DSAA2011/project/archive/runtime-validation-2026-06-04-iter2/`, then iteration 3 regenerated `pipeline_design.md`, 15 stage briefs, 5 stage results, 10 stage reviews, `verification_checklist.md`, `verification.log`, and `result.json`. Fresh notebook execution passed with `.venv/bin/jupyter nbconvert --to notebook --execute --inplace .../draft/project_G01_dropout.ipynb`; markdown/PDF both document the missing official LaTeX style file, so final state is `revision_needed` via `scripts/write_homework_result.py`, with no Canvas submission.

Uncommitted changes remain because this session adds gitignored/local runtime evidence plus ongoing protocol rollout edits already present in the worktree; next validation should run UCUG1505 as the open-ended false-pass check before marking execution architecture passing.

## 2026-06-04 — Course archive + notes pipeline, execution architecture design

Stage review rollout design and plan were added:
`docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md` and
`docs/superpowers/plans/2026-06-04-stage-review-rollout.md`. The selected path
is protocol + reviewer contracts, with DSAA2011 as the first draft-only real
task validation and UCUG1505 as the second validation.

Added course-level learning workflows alongside homework workflows: `sync-course` persistently archives Canvas course materials into `data/courses/<COURSE>/`, and `write-course-notes` generates Obsidian-style Markdown notes from archived lecture PDFs via a parallel Agent Team pattern. Both skills are registered in `skill.md` and `sub-skills/tools/_index.md`.

DSAA2011 acceptance evidence from the latest commits: `sync-course` synced 70 files (14 lectures, 8 readings, 48 other), fixed real Canvas filename classification (`-L` / `_L` patterns and `name` vs `display_name`), and `write-course-notes` generated 14 notes. Also wrote `docs/superpowers/specs/2026-06-04-execution-architecture-design.md`, which proposes the next execution architecture: coordinator + per-stage executor agents + independent reviewer agents.

Follow-up design alignment established Superpowers as a design reference, not a runtime dependency. Added `docs/runtime-agent-protocol.md` as the runtime handoff baseline: Claude Code Main Agent owns user interaction and subagent dispatch; subagents consume precise stage briefs and report back only to the Main Agent.

Wrote the Superpowers-style spec and implementation plan for this direction:
`docs/superpowers/specs/2026-06-04-runtime-agent-protocol-design.md` and
`docs/superpowers/plans/2026-06-04-runtime-agent-protocol.md`.

Static rollout implementation upgraded `do-homework.md`, `task-orchestrator.md`,
`docs/skills-architecture-spec.md`, `docs/runtime-agent-protocol.md`, and
`docs/examples/runtime/` around stage briefs/results/reviews. Next runtime
validation should start with DSAA2011 Machine Learning Project and stop at
draft/revision evidence; do not submit. After DSAA2011 has complete stage
receipts and reviews, run UCUG1505 as the open-ended false-pass resistance
check.

Static verification passed for `docs/plans/feature-list.json`, runtime example
JSON, stage review terminology across runtime docs, and `git diff --check`.
The rollout is intentionally stopped before real DSAA2011 validation.

Runtime validation start point was narrowed: reuse
`data/homework/DSAA2011/project/` and its existing `spec.md`, `canvas/`,
`investigation/`, and `references/` artifacts; do not rerun reconnaissance.
The DSAA2011 validation subagent should regenerate `pipeline_design.md` first,
then run the new stage brief/result/review protocol, followed by an independent
trajectory review subagent.

## 2026-06-03 — UCUG1505 end-to-end validation + DSAA2011 trajectory deep-dive

UCUG1505 Creative Coding Final Project 验证。从 canvas/ 原始数据开始，子代理完整走完侦查→设计→执行流程。**首轮 P0-P5 全部 FIXED**，无需迭代。

### 测试设计

与 DSAA2011 不同，workbench 只保留 canvas/ 原始 JSON 快照（无预写 pipeline_design.md、无预写 spec.md）。子代理从零开始侦查，测试动态 pipeline 组合能力。

### UCUG1505 验证结果

| 维度 | 状态 | 关键指标 |
|---|---|---|
| P0 Skill 读取 | FIXED | 7 个文件，三层加载顺序正确 |
| P1 Stage→Tool | FIXED | 4/4 stage 声明与执行完全一致 |
| P2 代码真实性 | FIXED | sketch.js 340行/9.8KB，完整 Particle 类 |
| P3 PDF 回退 | FIXED | pandoc→tectonic 两步法，28KB PDF |
| P4 目录结构 | FIXED | 全部在 draft/ 下 |
| P5 Write 工具 | FIXED | 11/11 Write 成功，0 Bash hack |

### DSAA2011 心路历程分析

并发派子代理深度分析 DSAA2011 两轮执行的完整行为轨迹，输出逐步追踪文档：
- 每个工具调用的行为依据（skill 指导 vs 自身判断）
- Skill 依从度 >85%，自主决策 ~25%（集中在环境调试）
- 两轮对比：Round 1 修 P3（fallback chain），Round 2 修 humanizer

### 产出文件

- `docs/pipeline-trace-audit-ucug1505.md` — UCUG1505 审计报告
- `docs/dsaa2011-execution-trajectory.md` — DSAA2011 心路历程轨迹

### 下一步

- 两个项目的技能架构验证均已完成
- 待验证项目：可考虑其他课程作业（如 DSAA2043、UCUG1077）进一步验证
- M3.5 剩余：ITERATION、SUB-AGENT-REVIEW、PREFERENCE-SYSTEM

## 2026-06-03 — Skills architecture refactoring + end-to-end validation

Completed the full skills architecture refactoring cycle triggered by the pipeline trace audit (P0-P5). Followed the superpowers workflow: brainstorm → spec → plans → subagent-driven implementation → 2-round end-to-end validation with trace analysis.

### What changed

**10 files modified/created across 6 commits:**

1. `docs/skills-architecture-spec.md` — Added §2.4 path discovery rules, fallback/min_quality fields, P5 note
2. `sub-skills/tools/_index.md` — Rewritten from routing table to pure capability menu
3. `sub-skills/tools/code-writer.md` — Restructured to unified template (Contract→Guidance→Appendices→Post-processing→Self-check)
4. `sub-skills/tools/code-writer-python.md` — New Python appendix (uv, project structure, notebook conventions)
5. `sub-skills/tools/writing-helper.md` — Restructured to unified template, added humanizer suggestion
6. `sub-skills/tools/writing-helper-report.md` — New report type appendix (data integrity rules)
7. `sub-skills/tools/pdf-renderer.md` — Added sequential fallback chain + Self-check
8. `sub-skills/tools/humanizer.md` — New post-processing skill for reducing AI patterns
9. `sub-skills/tasks/do-homework.md` — Added REPO_ROOT computation, pipeline shapes, new pipeline_design format
10. `sub-skills/tasks/task-orchestrator.md` — Added 5-step path discovery, SKILLS_DIR references

**Plus documentation:** pipeline-trace-audit.md, superpowers spec + plan

### Validation results (2 rounds on DSAA2011 ML Project)

| Issue | Original Audit | Round 1 | Round 2 |
|-------|---------------|---------|---------|
| P0: Skill reads | 0 reads | 8 reads | 13 reads |
| P1: Stage→Tool mapping | Missing | Full mapping | Full + humanizer |
| P2: Notebook execution | Fabricated | 36/37 cells | 25/25 cells, 0 errors |
| P3: PDF fallback | 4 failures | PARTIAL (skipped checks) | FIXED (sequential checks) |
| P4: Directory structure | Non-standard | All in draft/ | All in draft/ |
| P5: Write sandbox | Blocked | heredoc workaround | heredoc workaround |
| Humanizer | N/A | Not declared | Declared + applied |

Round 2 verification.log: 20 PASS / 4 FAIL (PDF quality — test environment limitation with no working LaTeX engine, not an architecture issue).

### Key design principle reinforced

Skills are domain expertise supplements — reference guidance, not hard constraints. Task spec always takes precedence over skill defaults. The model follows skills as best practice, but specific assignment requirements override.

### Where to look next

- Feature list: `docs/plans/feature-list.json` M3.5-SKILLS-ARCHITECTURE and M3.5-DYNAMIC-PIPELINE both now `passing`
- Audit report: `docs/pipeline-trace-audit.md`
- Design spec: `docs/superpowers/specs/2026-06-03-skills-refactor-design.md`
- Remaining M3.5 items: M3.5-ITERATION (pending), M3.5-PREFERENCE-SYSTEM (pending), M3.5-SUB-AGENT-REVIEW (pending)

## 2026-06-03 — Skills architecture design + Copilot per-type skill deep dive

Deep-dived into all six Canvas Copilot per-type skills (canvas-ics33, canvas-essay, canvas-reading-annotation, canvas-zybooks, canvas-inside, canvas-humanizer) and analyzed their complete pipelines — reconnaissance, generation, and verification stages differ significantly across types.

Key design decisions established through brainstorming with user:

1. **Skills are domain expertise supplements**, not fixed pipeline scripts. The model already knows how to write code/essays; skills provide project conventions, quality bars, and composition patterns.

2. **Progressive loading**: `_index.md` only shows top-level skills. Sub-skills and appendices (code-writer-python.md, writing-helper-essay.md, humanizer.md) are discovered by reading the parent skill file. Never flatten sub-skills into `_index.md`.

3. **Core + appendix pattern**: Main skill file has shared guidance; language-specific (code-writer-python.md) or type-specific (writing-helper-report.md) details go in separate files loaded on demand.

4. **Skills can nest skills**: writing-helper may invoke humanizer in post-processing; code-writer delegates to test-runner. Nesting is conditional — checked against `pipeline_design.md` declarations and user preferences.

5. **Preference integration via pipeline_design.md**: Language, type, constraints, review flags are declared per-stage in `pipeline_design.md`. This is the task-level preference mechanism (course-level and user-level preferences are future work).

Created `docs/skills-architecture-spec.md` — the authoritative design document for all skill file structure, loading mechanism, composition patterns, pipeline_design format, and preference system integration. Updated COLLABORATION.md (Skills Architecture section), AGENTS.md (skills architecture rules), ROADMAP.md (development priorities), and canvas-pilot-reference.md (Section 7: per-type skill deep pipeline analysis with cross-skill common patterns).

## 2026-06-03 — Establish M3.5+ design principles and Copilot 11-stage gap analysis

Deep-dived into the Canvas Copilot reference project at `/Users/deepwisdom/Desktop/project/canvas_copilot/`. Previous sessions only read the distilled notes in `docs/canvas-pilot-reference.md`; this session read the actual Copilot codebase including `canvas-generic` SKILL.md (11 stages, 3 sub-agents, verification retry loop), framework skills (scan/execute/skip/bootstrap/setup), per-course generic skills, hooks system, and 2026-06-01 real run records.

Key findings: Copilot's `canvas-generic` has 11 stages (0-11), not just the 5 that AutoStudy has been referencing. Stages 6-10 (pipeline design, generate, verification checklist, verify+retry, verification review) are missing from AutoStudy. The 3 sub-agents (A: investigation review, B: verification checklist design, C: verification coverage review) are also not yet implemented.

User clarified five design principles for M3.5+ development:
1. **Assistant, not automation** — borrow Copilot's mechanisms but keep user-in-loop
2. **Dynamic skills composition** — no fixed pipelines, leverage Claude Code's agent ability to compose skills on-the-fly for complex tasks
3. **Multi-turn iteration** — complex tasks won't be done well in one session; design for in-session interrupt/resume AND cross-session iterative refinement; `result.json` should support `revision_needed`
4. **Three-layer preference system** — task-level (`[B]` collection) → course-level (overlay) → user-level (Claude Code memory)
5. **Review-first design** — composable sub-agent review points per pipeline stage, not limited to Copilot's fixed 3

Documents updated: ROADMAP.md (added "设计理念" section under M3.5), COLLABORATION.md (added Design Principles section), AGENTS.md (added principle summary), canvas-pilot-reference.md (added Section 6: full 11-stage comparison table and architecture diff table).

## 2026-06-02 — Adopt agent-led Canvas Generic homework flow

User approved replacing the script-led reconnaissance direction with Canvas Copilot `canvas-generic` style agent-led Stage 1-5: fetch context, find rubric, locate inputs, review investigation, and classify output mode. Docs now define `spec.md` as the standardized reconnaissance report, `problem.md` as compatibility only, and `pipeline_design.md` as the do-homework -> task-orchestrator execution contract; standalone script-led spec generation is not the production path.

Validated the new agent-led flow on two real Canvas cases. DSAA2011 Project inspected assignment/rubric/front-page/syllabus/all 4 modules and 69 items, found the main spec in module 12955 file 625115, downloaded the project-module PDFs, wrote `spec.md`, `rubric.md`, `review_a.json`, and a mixed `pipeline_design.md`; orchestrator dry-run stopped correctly on group/dataset/style-file blockers. UCUG1505 FINAL project inspected assignment/rubric/front-page/syllabus/all 14 modules and 64 items, confirmed the assignment page and Week 4 module point to the same Google Doc, fetched the spec plus documentation template, wrote the same workbench files, and dry-run stopped correctly on partner/concept/code/video blockers.

Because no sub-agent reviewer tool is available in this runtime, Stage 4 used cold self-review and recorded `review_method: cold_read_self_review_no_sub_agent_available` in both local `review_a.json` files. `M3.5-WORKDIR-STRUCTURE`, `M3.5-DEEP-RECON`, and `M3.5-PIPELINE-DESIGN` are now marked `passing`; the generated `data/homework/...` workbenches remain gitignored local evidence, with durable evidence recorded in `docs/plans/feature-list.json`. Next: improve the do-homework user supplement UX and turn these dry-run blockers into a smooth execution/revision loop.

## 2026-06-02 — Stable plan-item handoff for do-homework

Added `scripts/select_plan_item.py` so a user choice like "do plan item 1" is resolved from `data/runs/<today>/plan.json` plus `pending_assignments.json` into a stable handoff object for `do-homework`: `course_id`, `assignment_id`, `assignment_name`, `recommended_action`, `existing_result_path`, and `suggested_work_dir`. Updated `sync-status.md`, `do-homework.md`, and `docs/canvas-pilot-reference.md` to use this selector instead of asking the agent to re-match assignment titles after the user has picked a numbered item.

Verification used `/tmp/autoust-select-plan-fixture-2` to cover `recon`, `review_or_submit`, `manual_review`, `continue/error`, and invalid-index behavior; `py_compile` passed for the selector and the existing M3.5 scripts. The selector also ran against cached real live-scan plans under `/tmp/autoust-flow-real/runs` and `/tmp/autoust-flow-real/runs-after-skip`, resolving UCUG1600 plan items before and after a skipped-result filtered the first assignment out. A full DSAA2011 Machine Learning Project simulation under `/tmp/autoust-ml-flow` built a one-item plan, selected `2973:21641`, ran real reconnaissance to `review_a.verdict=proceed`, wrote `status=skipped`, and confirmed the rerun plan filtered the item as `result_skipped`.

## 2026-06-02 — Assistant-style scan-plan implementation started

Started M3.5-SCAN-PLAN after reviewing Canvas Copilot's `canvas-scan` and run-state schema again: AutoStudy borrows the scan/execute boundary but keeps `sync-status` as a recommendation step, not a batch executor. Added `scripts/write_scan_plan.py` to combine local canvascli snapshots with `data/homework/**/result.json` and write `data/runs/<today>/pending_assignments.json`, `plan.json`, and `REPORT.md`; `sync-status.md` now points to this writer and explicitly stops before do-homework unless the user chooses one item.

Verification wrote plans under `/tmp/autoust-scan-plan-current3`, `/tmp/autoust-scan-plan-with-results3`, and `/tmp/autoust-scan-plan-default-terminal3`. Current real Canvas snapshot produced raw snapshot copies plus 3 actionable items after filtering 44 graded, 6 submitted, and 4 ancient-overdue assignments; DSAA2011/UCUG1505 fixture checks confirmed `draft_ready -> review_or_submit`, `skipped -> filtered`, and Canvas `graded` wins over stale local draft state in default mode. Checks passed: `py_compile` for all scripts, `json.tool` for feature-list and generated plan files, and the DSAA/UCUG fixture assertions. Next: final review with the user before committing.

Post-commit real flow verification refreshed Canvas login through the working 127.0.0.1:7890 proxy after `whoami` reported an expired session. A live scan under `/tmp/autoust-flow-real` fetched 7 courses, 57 assignments, and 5 announcements, then selected plan item 1 (`UCUG1600 Final Report`, 2798:23536), ran the then-current transitional reconnaissance helper to `review_a.verdict: proceed`, wrote `result.json status=skipped`, and reran scan-plan to confirm assignment 23536 disappeared from the plan (`before ['23536', '23537', '20629']`, `after ['23537', '20629']`).

## 2026-06-02 — Result writer + assistant-shaped Copilot adaptation rule

Recorded the collaboration rule that Canvas Copilot is a mature reference but not a blueprint to clone: AutoStudy should borrow mechanisms such as atomic data access, deep reconnaissance, workbenches, verification logs, and state files while redesigning the interaction around an assistant-style user loop. Added `scripts/write_homework_result.py` as the stable writer for single-assignment `result.json`; `do-homework.md` now calls it for `skipped`, `draft_ready`, `submitted`, and `error` paths.

Verification used existing real recon workbenches copied to `/tmp/autoust-result-verify/`: DSAA2011 Project produced a `draft_ready` result with a fake notebook fixture, `verification_log_path`, two `human_review_items`, and `review_a_verdict: proceed`; UCUG1505 FINAL project produced a `skipped` result with notes and `review_a_verdict: proceed`. Checks passed for the result writer, feature-list JSON, both smoke `result.json` files, and diff whitespace. Committed as `c4ae2a4 feat: add homework result state writer`. Next: build assistant-style `pending_assignments.json` / `plan.json` support for `sync-status`.

## 2026-06-02 — Transitional recon helper + post-recon user supplement gate

Turned the Copilot-style reconnaissance template into a transitional helper for early validation. This direction was later superseded by the agent-led assignment reconnaissance workflow, and the helper has since been removed so runtime agents do not confuse it with the production path. `do-homework.md [B]` explicitly performs a mandatory reconnaissance summary + user supplement checkpoint even when `review_a.json.verdict == "proceed"`; user supplements now flow through `investigation/user_notes.md` and the confirmed alignment contract.

Real Canvas verification used `/tmp/autoust-recon-script-verify/`: DSAA2011 Project produced `spec.md` 66,322 B / `problem.md` 155,415 B, inspected 4 modules and 69 module items, confirmed assignment description 0 B, downloaded `DSAA2011-26sp-project_announce-L01.pdf` plus nearby module PDFs, and `review_a` returned `proceed`. UCUG1505 FINAL project produced `spec.md` 22,527 B / `problem.md` 14,274 B, inspected 14 modules and 64 module items, recorded the Final project Google Doc plus Week 9 slides, skipped front-page GIF media as inspected-not-downloaded, and `review_a` returned `proceed`. A canvascli retry bug surfaced during `whoami` (`requests.SSLError` should be `requests.exceptions.SSLError`) and was fixed in the canvascli repo.

## 2026-06-02 — Final-review cleanup for M3.5 recon evidence

Cleaned up review risks in the M3.5 workbench docs: canvascli README now shows the required `assignment <aid> -c <cid>` form, the Canvas Pilot reference tail no longer describes the old modules-only/problem.md-only direction, and the tool registry/backlog now use the `spec.md` + atomic-context wording. Rechecked `/tmp/autoust-recon-verify/dsaa2011`: `spec.md` is 45,709 B, `problem.md` is 107,322 B, assignment description is empty, front page is 404/not enabled, modules count is 4, module 12955 contains the project PDF, 3 references downloaded, and file 688370 metadata failed; `review_a.json` lists that file under `blocking_unreachables` while the recon verdict still remained `proceed`.

## 2026-06-01 — Adopt Canvas Copilot workbench direction for deep assignment reconnaissance

Reviewed Canvas Copilot's real DSAA2011 Project run at `/Users/deepwisdom/Desktop/project/canvas_copilot/runs/2026-06-01/DSAA2011_L01_-_Machine_Learning__Project`. The user approved copying its single-assignment workbench shape: `spec.md`, `references/`, `investigation/`, `pipeline_design.md`, `draft/`, `verification_checklist.md`, `verification.log`, and `result.json`. AutoStudy will migrate from the current flat `data/homework/<COURSE>/<HWID>/` layout toward a compatible structure with `canvas/` raw CLI snapshots, `spec.md` as the main reconnaissance artifact, and `problem.md` kept temporarily for existing tools.

The data-layer direction is now explicitly Copilot-style atomic commands, not `assignment-context`: `assignment`, `rubric`, `front-page`, `syllabus`, `modules`, `module-items`, `page`, `file`, and `assignment-files`. DSAA2011 Project and UCUG1505 FINAL project are the two required real verification cases for the upcoming AutoStudy integration. Backlog now has M3.5 items for atomic context, workdir structure, deep recon, and result.json.

Implemented the AutoStudy documentation side of that migration: `canvascli-api.md`, the assignment reconnaissance doc, `do-homework.md`, `task-orchestrator.md`, `_index.md`, `skill.md`, and `PITFALLS.md` now describe the spec-first workbench. Verification used the copied probe template under `/tmp/autoust-recon-verify/assignment_recon_probe.py` and ran real Canvas cases: DSAA2011 Project produced a 45,709 B `spec.md`, inspected module 12955, and downloaded the project announcement PDF; UCUG1505 FINAL project produced a 19,771 B `spec.md`, found the Google Doc spec in both assignment description and Week 4 module item, and listed Week 9 slides as project context. One design correction from verification: inspect every module item, but only download likely assignment-context files instead of every course file.

## 2026-06-01 — Clarified Canvas login/session mental model

Validated that `canvascli init` is a login/refresh command, not a session health check: it always opens Chromium and writes a new `state.json` after successful SSO. The correct health check is `.venv/bin/canvascli whoami`, which returned the Canvas user from the current saved session without requiring browser login. Docs now distinguish `state.json` (canvascli's saved Canvas API cookie) from the SSO "remember login" checkbox (controls how smooth the next SSO refresh is), and explicitly tell agents not to run `init` just to test status.

## 2026-06-01 — Split term-scope fix across canvascli + AutoStudy docs

Reviewed the `eca80a5` AutoStudy hardening commit and moved the root fix back to the data layer: `canvascli` now owns default latest-active-term selection plus explicit `--term` overrides. AutoStudy docs were updated to keep `sync-status` simple (`courses` / `assignments` / `announcements`) and document the CLI contract instead of reimplementing term filtering in skill flow. Verification after refreshing `canvascli init`: default AutoStudy flow returned 7 Spring courses / 57 assignments / 5 announcements; explicit `--term "2025-26 Spring"` returned 7 courses / 57 assignments.

## 2026-05-23 / 24 — MVP day: 4 flagship scenarios E2E + guizang slides + docs

### What changed

Pushed AutoStudy to **MVP (M3 core)**: the four flagship homework scenarios — **paper / slides / math / lab** — each ran end-to-end on a real HKUST(GZ) Canvas assignment and produced a real deliverable. Plus integrated the upstream [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) as the default slides path.

### Real-assignment evidence (under `data/homework/`, gitignored)

| Scenario | Course / assignment | Deliverable | Bytes / pages |
|---|---|---|---|
| **paper** | DLED3020 Paper Critique (id 14250) | `DLED3020/paper-critique/final.pdf` | 45,684 B / 3 pp / PDF v1.5 |
| **slides (beamer)** | UCUG1077 Group presentation (id 14297) | `UCUG1077/group-presentation/slides.pdf` | 82,370 B / 10 pp |
| **slides (guizang)** | same | `UCUG1077/group-presentation/guizang/{index.html, slides_guizang.pdf}` | 47,443 B HTML (Style A · Kraft Paper · 10 sections) + 1,674,228 B PDF (1600×900) |
| **math** | DSAA2043 Lab-Assignment 1 (id 17284) | `DSAA2043/lab-assignment-1/solution.pdf` | 49,390 B / PDF v1.5 |
| **lab** | DSAA2012 Project Report (id 18361) | `DSAA2012/project-report/{src/*.py, tests/, test_report.md, report.pdf}` | report.pdf 43,553 B / 3 pp; pytest 14/14 pass / exit=0 |

### New + updated skill files

- `sub-skills/tasks/do-homework.md` — flagship MVP task: `[A]` canvascli fetch → `[B]` AskUserQuestion intent → `[C]` task profile + orchestrator → `[D]` deliverable → `[E]` AskUserQuestion submit → `[F]` `canvascli submit`. Only two interaction points.
- `sub-skills/tools/writing-helper.md` — agent writes essay / report / reflection drafts directly. `[CITATION NEEDED]` placeholders enforced when references.bib is missing entries.
- `sub-skills/tools/paper-search.md` — arxiv Python package wrapped as a templated script (`scripts/run_paper_search.py`) → references.bib + references.json.
- `sub-skills/tools/figure-maker.md` — matplotlib line/bar/scatter with CJK font config.
- `sub-skills/tools/code-writer.md` + `test-runner.md` — Python source + pytest with `test_report.{md,json}`.
- `sub-skills/tools/slide-maker.md` — **rewritten**: default path wraps guizang-ppt-skill (HTML magazine / Swiss + Playwright PDF print); LaTeX-beamer kept as fallback for strict-PDF academic work.
- `sub-skills/tools/_index.md` — tool registry expanded to 7 entries; new `run_tests` verb; new "Scenario → Tool chain" table; video row marked OUT OF SCOPE.
- `sub-skills/tasks/task-orchestrator.md` — type vocabulary aligned (`paper | slides | math | lab | video | notes | mixed`); MVP scenarios validated table replaces the "minimum viable" placeholder.

### Submit interface (M3-SUBMIT)

`canvascli/canvascli/resources/submit.py` — the 3-step Canvas upload protocol is implemented at the code layer:

1. POST `/api/v1/courses/:cid/assignments/:aid/submissions/self/files` → `{upload_url, upload_params}`
2. POST `upload_url` with multipart (`upload_params` + file), handles 302 redirect confirm
3. POST `/api/v1/courses/:cid/assignments/:aid/submissions` with `submission[submission_type]=online_upload` + `submission[file_ids][]=<file_id>`

Code path verified by reading the file. **Not yet exercised against a real unexpired assignment.** Flipping `M3-SUBMIT` from `partially-verified` → `passing` requires the user to provide a sandbox / unexpired assignment for one real round-trip.

### Dependencies installed

- AutoStudy `.venv`: `matplotlib`, `numpy`, `arxiv`, `pytest` (via Tsinghua mirror — the default proxy at 127.0.0.1:6666 had SSL EOF errors against pypi.org).
- `~/.claude/skills/guizang-ppt-skill/` — git clone from op7418's upstream. Shared across all decks the agent makes.
- `tectonic` (brew, pre-existing) — used by both pdf-renderer and the slides beamer fallback.
- Playwright + chromium (pre-existing in `.venv`) — used by the new guizang PDF export.

### Pitfalls burned in this push (added inline to relevant `.md`)

1. `pip install` via the user's default proxy (127.0.0.1:6666) hit `SSLError(SSLEOFError)` against pypi.org. Workaround: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`.
2. `data/` is gitignored — `git commit -f` against it was rejected (correctly). Evidence lives in commit messages + `feature-list.json` `evidence[]` arrays + (eventually) `docs/verification/` if it gets substantial enough.
3. `$\LaTeX$` inside a markdown `- [ ]` checkbox list breaks tectonic with `\spacefactor in math mode` (the `\LaTeX` macro calls `\@` which clashes with math mode). Fix: write plain text "LaTeX".
4. `\bm` from the `bm` package overflows tectonic's mathchar range under certain font setups. Fix: use `\mathbf{}` instead, drop the `bm` package.
5. Subprocess-launched sub-agents in a sandboxed environment can't `git clone` (network blocked) or write to `~/.claude/skills/`. The parent agent must do the install outside the sandbox.
6. guizang Playwright PDF export needs `localStorage.setItem('guizang-ppt-low-power','1')` *before* navigation completes, otherwise WebGL canvases fight the print loop and produce black pages.

### Where to look next

- `M3-SUBMIT` → ask user for a sandbox assignment id, run one real `canvascli submit`, flip status to `passing`.
- `M4-TUTOR` is the next milestone — Interactive Tutor with persistent `data/mastery/<course>.json`. AutoStudy.pdf has the design.
- `M3-VIDEO` is OUT OF SCOPE for this repo — user is building a separate video skill.

### Open uncertainties

- guizang Style B (Swiss) integration hasn't been exercised — only Style A was used. Should work since slide-maker.md documents both paths.
- The lab scenario built a representative numpy project (regression + clustering); the real DSAA2012 assignment is in an attached PDF the agent didn't have access to. `[TODO: align with actual project spec]` markers are in `src/`.

---

## 2026-05-14 — Docs harness adoption (light)

### What changed

- Added this file (`docs/progress/agent-progress.md`)
- Added `docs/plans/feature-list.json` — structured backlog mirroring ROADMAP M1–M5 with explicit `status` per feature
- Added `AGENTS.md` at repo root — developer-facing entry, distinct from `skill.md` (user-facing)

### Why

Adopted the lightweight slice of [Aurorra1123/ust-dev `harness-best-practice`](https://github.com/Aurorra1123/ust-dev/commit/59761756ebcd01d68a4b62729b4e03f09948dc63):

- A persistent log for cross-session handoff (this file)
- A structured backlog with verification status (`feature-list.json`)
- A separate developer entry (`AGENTS.md`) so `skill.md` can stay focused on end-user agent usage

Skipped `docs/{standards,adr,architecture,verification,exec-plan}` — at AutoStudy's current scale, ROADMAP and PITFALLS already cover what those would, and adding them now is overhead. Revisit when a new contributor can't ramp up without them.

### Where to look next

- Repo file layout: `AGENTS.md` "Where things live" section
- M3 remaining work: `ROADMAP.md` M3 section, numbered list near the bottom
- Backlog status: `docs/plans/feature-list.json`

---

## 2026-05-13 — Big day: M2 lockdown → canvascli extraction → M3 foundation

This was actually one long session that produced 6 commits on AutoStudy + 1 commit on a brand-new sister repo (`canvascli`). The arc:

### Phase A: M2 lockdown (commit `7e6725e`)

Verified that a fresh agent reading `skill.md` can run `sync-status.md` end-to-end and produce a clean 5-section markdown summary. This was the first proof that the skill-as-markdown architecture actually works — agent honored safety rules, did not auto-download, used AskUserQuestion for next-action.

Two real bugs surfaced during validation, both captured in `sub-skills/tasks/sync-status.md` Pitfalls:

- Python tuple `(datetime, dict)` sort raises TypeError when datetimes equal (dict isn't comparable). Fix: always pass `key=lambda x: x[0]`.
- "Overdue" shouldn't list assignments overdue >30 days — past-term residue, not actionable. Added 30-day cap.

### Phase B: M3 design (commits `e2845fe`, `106f95b`)

Reframed M3 as a three-layer architecture (task → orchestrator → tools) after discussing heterogeneous output scenarios (report / slides / video / proof / code). Wrote `MARKETING.md` documenting the five flagship scenarios that anchor external narrative — informs which tools to build in what order.

### Phase C: M3 foundation (commit `37b7daf`)

Built the skeleton:

- `sub-skills/tools/_index.md` — capability registry + verb vocabulary
- `sub-skills/tools/pdf-renderer.md` — first production-grade tool (tectonic two-step path, since user has tectonic but no xelatex; ctexart + PingFang SC + Menlo for Chinese)
- `sub-skills/tasks/task-orchestrator.md` — pipeline composer reading task profile, matching capabilities, executing tools that communicate via files in `data/homework/.../`

End-to-end smoke test: minimal task profile → orchestrator matches `render_pdf` → pdf-renderer two-step → real PDF on disk (48 KB, valid `%PDF-1.5` magic). The three-layer architecture works.

### Phase D: canvascli extraction (commit `90072ac` here + `0385f54` in new repo)

Studied `sshwy/pku3b` source code (user cloned it locally to `pku3b/` for inspection) and decided AutoStudy should extract its `scraper/` package the same way AutoPku depends on pku3b. New independent repo at `~/workspace/canvascli/`.

- typer-based CLI, 11 flat top-level commands (init / version / whoami / courses / assignments / assignment / announcements / files / folders / download / submit)
- **JSON-by-default** output, `--pretty` for human-readable (improvement over pku3b's ANSI text)
- Cookie auth via Playwright (no stored password; safer than pku3b's plaintext config)
- Hardcoded `hkust-gz.instructure.com` (not multi-instance)
- `submit` implements Canvas's three-step upload protocol — M3 do-homework can use it directly

AutoStudy deleted its `scraper/`, replaced `scraper-setup.md` / `scraper-api.md` with `canvascli-setup.md` / `canvascli-api.md`, and updated `sync-status.md` to shell out to `canvascli courses/assignments/announcements`. End-to-end re-verified: identical output, no SSL warnings.

### Phase E: ROADMAP rewrite (commit `9964365`)

Old ROADMAP described an in-repo scraper that no longer existed. Rewrote with the canvascli extraction folded in, M1/M2 marked complete, M3 sub-tasks marked with current status, and a new cross-stage principle separating data acquisition (canvascli) from skill orchestration (AutoStudy).

### What's next (start of next session, read this first)

M3 remaining work, in recommended order:

1. **`sub-skills/tasks/do-homework.md`** — write the skeleton. End-to-end target: user says "complete DLED3020 Assessment Task 3", agent uses canvascli to fetch the assignment description + rubric, presents summary, asks confirmation, runs orchestrator to produce a PDF draft, asks confirmation again, submits via `canvascli submit`.
2. **`sub-skills/tools/writing-helper.md`** — once do-homework has a real flow, the draft quality needs an actual tool. Without it, the orchestrator output is a placeholder.
3. Add `paper-search.md` and `figure-maker.md` to complete the Report pipeline.
4. Validate the full Report pipeline against a real (low-stakes) HKUST(GZ) assignment.

### Open uncertainties for next session

- `canvascli submit` works in code but hasn't been tested against a real Canvas assignment yet. Worth testing on a low-stakes assignment before relying on it in `do-homework`.
- The `data/homework/test/output.pdf` from the orchestrator smoke test was visually confirmed by the user but isn't archived. If we adopt `docs/verification/` later, this is the kind of artifact that belongs there.

---

## Earlier work (pre-2026-05-13)

Repo bootstrap, scraper iterations, M1/M2 design exploration — captured in `plan.md` (the original brief) and `AutoStudy.pdf` (the design document). Not re-narrated here.
