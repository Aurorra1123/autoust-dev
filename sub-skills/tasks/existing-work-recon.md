---
name: existing-work-recon
description: retained draft, repair, review, and continue state reconnaissance
---

# Existing Work Recon

Use this tool workflow when a homework request starts from an existing
workbench with retained artifacts instead of a clean-start Canvas assignment.
Its job is to answer:

1. What current workbench state already exists?
2. Which retained user-visible artifacts, source files, process notes, and
   verification records are relevant to the current request?
3. What context should the planner use before deciding whether this is a repair,
   continuation, packaging, or verification task?
4. Is a focused repair reconnaissance needed before pipeline planning?

Runtime invariants:

- Stay inside the supplied `work_dir`; do not discover a new Canvas assignment
  or create a new assignment workbench.
- Treat retained user-visible artifacts as evidence to inspect before proposing
  replacement work.
- Separate evidence into `artifact/codebase/process-history/verification`
  categories so the planner can see what kind of state supports each finding.
- Inspect only retained user-visible artifacts, source/code/package files, and
  verification outputs named or implied by startup inventory as current
  retained inputs.
- Treat transcripts, logs, old stage results, old review files, old
  `pipeline_design.md`, prior `repair_plan.md`, and prior
  `repair_pipeline_design.md` as process evidence by default, not current task
  context.
- Read process history only through an explicit `allowlisted_history_files`
  list derived from startup inventory and the current request.
- Preserve uncertainty: mark stale, missing, blocked, or conflicting evidence
  instead of filling gaps with clean-start assumptions.
- This tool must not write `spec.md`, `problem.md`,
  `investigation/review_a.json`, `investigation/alignment_brief.md`,
  `repair_plan.md`, `pipeline_design.md`, `repair_pipeline_design.md`, or
  user-facing deliverables.
- This tool must not run clean-start Canvas/source recon, call
  `assignment-recon`, fetch course-wide Canvas sources, or rewrite
  `references/` as if starting over.

## Capability

- `current_state_intake` - `(work_dir, current_request)` -> retained-artifact
  current-state evidence manifest, explore context, and optional repair
  reconnaissance.

## Inputs

- `work_dir` - Existing homework workbench directory.
- `current_request` - User's current repair, continuation, verification,
  packaging, or inspection request.
- `prelaunch_startup_inventory.json` - Startup inventory for known workbench
  files, retained outputs, and likely continuation entrypoints.
- Optional `allowlisted_history_files` - Explicit process-history paths that may
  be read for the current request.

## Outputs

Write these under `<work_dir>/investigation/`:

```text
investigation/
├── explore_manifest.json
├── explore_context.md
└── repair_recon.md        # optional, for repair requests or concrete breakage
```

`investigation/explore_manifest.json` is the structured inventory of inspected
evidence and gaps. `investigation/explore_context.md` is the planner-facing
summary. `investigation/repair_recon.md` is optional focused repair
reconnaissance, not a replacement assignment spec.

Write this at the workbench root only when the user's feedback or change request
needs a stable file:

```text
repair_request.md
```

## Stage 1 - startup-inventory

Read `prelaunch_startup_inventory.json` first. Use it to identify the current
workbench shape, retained terminal artifacts, candidate generated outputs,
existing source trees, verification files, retained startup files, and exact
allowlisted process-history files.

If the startup inventory is missing or stale, including when
`work_dir is missing` or when `work_dir does not match the active workbench`, inspect only
the active workbench root at shallow depth to identify obvious current
user-visible artifacts such as `draft/`, rendered PDFs, packages, notebooks,
source directories, tests, and verification files. Do not inspect `archive/`,
`transcripts/`, old `stage_results/`, old `stage_reviews/`, old reviews, or old
diagnostics while reconstructing this minimal inventory. Record the
missing/stale inventory as a blocker in `investigation/explore_manifest.json`;
do not switch to clean-start Canvas recon.

## Stage 2 - evidence-map

Build an evidence map with these top-level categories:

```text
artifact
codebase
process-history
verification
```

For each evidence item, record path, category, freshness, why it is relevant to
`current_request`, and whether it is complete enough for planner use. Include
retained user-visible artifacts such as reports, notebooks, slides, packages,
figures, exported PDFs, and submitted-ready bundles when present.

Process history must be limited to `allowlisted_history_files`. If relevant
history is implied but not allowlisted, record it as blocked or omitted rather
than reading arbitrary transcripts.

## Stage 3 - inspect-current-state

Read the high-signal evidence from Stage 2. Prefer current retained artifacts
and verification results over earlier drafts when they conflict. For codebase
evidence, inspect source, tests, build scripts, notebooks, package metadata, and
generated outputs only when they are named or implied by startup inventory as
retained startup files for the current request. Do not use archived or old
process files as codebase evidence unless they are exact
`allowlisted_history_files` and are reported as process-history findings.

Write `investigation/explore_manifest.json` with:

- `work_dir`
- `current_request`
- `allowlisted_history_files`
- `scout_coverage` for `artifact`, `codebase`, `process_history`, and
  `verification`, each with `status: "enabled" | "skipped" |
  "inline_fallback"`, reason, and input paths
- `scout_receipts` for every enabled scout, including ledger row reference and
  receipt path
- `skipped_scouts` with concrete reasons
- `inline_fallbacks` with the executor and reason when child dispatch is not
  used
- `inspected_evidence`
- `retained_user_visible_artifacts`
- `current_state_findings`
- `missing_or_blocked_evidence`
- `recommended_next_action`

## Stage 4 - write-explore-context

Write `investigation/explore_context.md` for the workflow planner. Keep it
concise and evidence-grounded:

- current request summary
- retained artifact inventory
- codebase state
- relevant process-history findings
- verification status
- stale, missing, or conflicting evidence
- recommended planner posture: repair, continue, package, verify, or ask user

This context is planner input. It must not write `spec.md`,
`investigation/review_a.json`, `investigation/alignment_brief.md`,
`repair_plan.md`, `pipeline_design.md`, or `repair_pipeline_design.md`; it must
not run clean-start Canvas/source recon.

## Stage 5 - optional-repair-recon

If the current request is a repair request, or retained evidence shows a
specific breakage that would change the next plan, write
`investigation/repair_recon.md`.

The repair reconnaissance should include:

- broken or suspect artifact
- expected behavior or deliverable state
- observed failure or evidence gap
- likely affected files
- verification command or manual check to rerun
- repair risks and blockers

Do not write `investigation/repair_recon.md` for ordinary continuation or
packaging requests unless current retained evidence shows a concrete breakage
that would change the next plan. In those cases, `investigation/explore_context.md`
is the handoff artifact.

If the user's feedback or requested change is not already captured in a stable
current-run file, write `repair_request.md` at the workbench root. It preserves
the concrete user request for the planner; it is not a repair plan.

## Self-check

Before handing off to the planner, confirm:

- `investigation/explore_manifest.json` exists and categorizes inspected
  evidence as artifact/codebase/process-history/verification.
- `investigation/explore_manifest.json` records every scout class as enabled,
  skipped, or inline_fallback with a concrete reason.
- Every enabled scout has a `stage_reviews/child_dispatch_ledger.json` row and
  a receipt path, or inline fallback is recorded with a reason.
- `investigation/explore_context.md` exists and summarizes retained
  user-visible artifacts.
- `investigation/repair_recon.md` exists only when a focused repair path is
  needed.
- `repair_request.md` exists only when the user's feedback or change request
  needs a stable root-level file.
- The run did not create or modify `spec.md`.
- The run did not create or modify `investigation/review_a.json`,
  `investigation/alignment_brief.md`, `repair_plan.md`,
  `pipeline_design.md`, or `repair_pipeline_design.md`.
- The run did not execute clean-start Canvas/source reconnaissance.
