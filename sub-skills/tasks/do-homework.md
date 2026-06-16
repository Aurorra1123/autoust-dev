---
name: do-homework
description: Homework planning workflow. Use when the user asks "complete X assignment", "do my paper for DLED3020", "帮我做 lab 5". Runs Canvas Generic-style reconnaissance, aligns with the user, writes a reviewable per-assignment pipeline, and stops before execution.
---

# Do Homework

Use this task as the stable user-facing entrypoint for one Canvas assignment.
It does not inline source reconnaissance, retained-work exploration, alignment,
pipeline design, or draft execution. It routes to exactly one first-stage task
file:

```text
clean start -> sub-skills/tasks/background-recon.md
retained / repair / review / continue -> sub-skills/tasks/existing-work-recon.md
```

Do not read or name later-stage files from this router. Follow the routed
first-stage task to completion; that task owns its own tail handoff.

Clean-start source confirmation is handled inside the routed first-stage task,
not in this router.

## Router Responsibilities

1. Verify `.venv/bin/canvascli version` and `.venv/bin/canvascli whoami`.
2. Resolve exactly one assignment, using `scripts/select_plan_item.py` output
   when available.
3. Determine `work_dir`, `recommended_action`, and `entry_preset`.
4. Run preflight archive/startup inventory before reading old workbench files
   as task context.
5. Route to the first-stage task file named in the route table.
6. Stop there; the first-stage task owns any later handoff.

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
  "route": "background-recon.md | existing-work-recon.md",
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

| Input state | Entry preset | First-stage route |
|---|---|---|
| `recommended_action: recon` | `clean_start` | Read `sub-skills/tasks/background-recon.md`; it owns recon briefing/source confirmation and its own tail handoff. |
| `recommended_action: review_or_execute` or `pipeline_ready` | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`; do not rerun source recon. |
| `recommended_action: review_or_submit` or `draft_ready` | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`; do not clean-start by default. |
| `recommended_action: continue` or failed/interrupted work | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`; run clean-start source recon only if that stage reports missing/stale source evidence as a blocker and the router accepts a new route. |
| Direct retained draft, prior output, feedback, repair, package, or verification request | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`. |

## Handoff

After route selection, read only the first-stage route named in the route table.
Do not preload, inspect, or name later-stage task files from this router. The
first-stage task owns the next handoff after it writes its terminal artifacts
and completes any required user confirmation checkpoint.
