---
name: do-homework
description: Homework planning workflow. Use when the user asks "complete X assignment", "do my paper for DLED3020", "帮我做 lab 5". Runs Canvas Generic-style reconnaissance, aligns with the user, writes a reviewable per-assignment pipeline, and stops before execution.
---

# Do Homework

Use this task as the stable user-facing entrypoint for one Canvas assignment.
It does not inline source reconnaissance, current-state exploration, alignment,
pipeline design, or draft execution. It routes to:

```text
sub-skills/tasks/assignment-source-intake.md
sub-skills/tasks/assignment-workflow-planner.md
sub-skills/tools/current-state-intake.md
sub-skills/tasks/task-orchestrator.md
```

## Router Responsibilities

1. Verify `.venv/bin/canvascli version` and `.venv/bin/canvascli whoami`.
2. Resolve exactly one assignment, using `scripts/select_plan_item.py` output
   when available.
3. Determine `work_dir`, `recommended_action`, and `entry_preset`.
4. Run preflight archive/startup inventory before reading old workbench files
   as task context.
5. Route to the downstream task or tool file named in the route table.
6. Stop before draft execution unless the user separately approves
   `sub-skills/tasks/task-orchestrator.md`.

## Preflight Startup Inventory

Before reading old workbench files as task context, write or refresh:

```text
<work_dir>/prelaunch_startup_inventory.json
```

The startup inventory is the boundary between current task evidence and old
process evidence. It must distinguish clean starts from retained-artifact starts
and record the accepted route:

```json
{
  "work_dir": "data/homework/<COURSE>/<assignment>",
  "entry_preset": "clean_start | retained_artifact_start",
  "route": "assignment-source-intake.md | assignment-workflow-planner.md",
  "recommended_action": "recon | review_or_execute | review_or_submit | continue",
  "retained_user_visible_artifacts": [],
  "current_source_files": [],
  "allowlisted_history_files": [],
  "forbidden_context": [],
  "archived_process_evidence": [],
  "must_not_clean_start": false
}
```

Old process evidence is forbidden by default. The router must not read appendix
artifacts, raw old process evidence, archive contents, transcripts, old stage
receipts, stale reviews, old diagnostics, prior `pipeline_design.md`, prior
`repair_plan.md`, or prior `repair_pipeline_design.md` unless
`prelaunch_startup_inventory.json` allowlists the exact file or directory and
states why it affects the current route.

## Route Table

| Input state | Entry preset | Route |
|---|---|---|
| `recommended_action: recon` | `clean_start` | Read `sub-skills/tasks/assignment-source-intake.md`, then hand off to `sub-skills/tasks/assignment-workflow-planner.md`. |
| `recommended_action: review_or_execute` or `pipeline_ready` | `retained_artifact_start` | Read `sub-skills/tasks/assignment-workflow-planner.md` for pipeline review; use `sub-skills/tools/current-state-intake.md` only for retained/current-state evidence needed by the planner; do not rerun source recon. |
| `recommended_action: review_or_submit` or `draft_ready` | `retained_artifact_start` | Read `sub-skills/tasks/assignment-workflow-planner.md` for retained artifact review; use `sub-skills/tools/current-state-intake.md`; do not clean-start by default. |
| `recommended_action: continue` or failed/interrupted work | `retained_artifact_start` | Read `sub-skills/tasks/assignment-workflow-planner.md` recovery intake; use `sub-skills/tools/current-state-intake.md`; run `sub-skills/tasks/assignment-source-intake.md` only when missing or stale source evidence is the blocker and the startup inventory records that exception. |
| Direct retained draft, prior output, feedback, repair, package, or verification request | `retained_artifact_start` | Read `sub-skills/tasks/assignment-workflow-planner.md`, which invokes `sub-skills/tools/current-state-intake.md` before repair or continuation planning. |

## Clean-Start Source Contract

Clean-start source intake must be delegated to
`sub-skills/tasks/assignment-source-intake.md`. It must preserve original source
evidence through `reference_collector` and write the terminal source artifacts
the planner needs:

```text
references/REFERENCE_INDEX.md
references/canvas_native/
references/source_docs/
references/slides/
references/external/
spec.md
investigation/rubric.md
investigation/review_a.json
investigation/recon_summary.md
investigation/explore_context.md
```

The Main Agent owns final source interpretation. For proposal/research/open-ended
work, direct-spec bodies and syllabus-relevant bodies must remain readable as
complete original evidence before planning. PDF link annotation manifests are
part of source completeness: `references/*.pdf.links.json` must be checked, and
do not treat PDF text extraction as complete when link annotations are missing.

Do not create `reading_plan.compact.json`. Do not create `source_findings.compact.md`.
Do not make legacy source-scout appendix files the coordinator interface.
Subagents must not write final `spec.md`,
`investigation/review_a.json`, `pipeline_design.md`, or user alignment
decisions.

Do not create `reading_plan.compact.approved.json`.
Do not create `investigation/_appendix/source_index.json`.
Do not create `investigation/_appendix/body_evidence_fragments/`.
Do not create `investigation/_appendix/scout_receipts/` for standard source
reconnaissance artifacts.

## Handoff

After routing, follow the downstream file exactly:

- Clean starts: `sub-skills/tasks/assignment-source-intake.md` writes terminal
  source artifacts, then `sub-skills/tasks/assignment-workflow-planner.md` owns
  user alignment and pipeline design.
- Retained-artifact starts: `sub-skills/tasks/assignment-workflow-planner.md`
  invokes `sub-skills/tools/current-state-intake.md` before repair,
  continuation, review, package, or verification planning.
- Draft execution happens only through
  `sub-skills/tasks/task-orchestrator.md` after the user approves
  `pipeline_design.md` or `repair_pipeline_design.md`.
