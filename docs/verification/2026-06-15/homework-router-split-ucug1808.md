# Homework Router Split UCUG1808 Validation

Date: 2026-06-15
Scope: UCUG1808-L01 `Project Proposal Files`
Workbench: `data/homework/UCUG1808-L01`

## Runtime Path

An independent runtime coordinator subagent validated the public `do-homework`
entrypoint through the clean-start route:

```text
skill.md
-> sub-skills/tasks/do-homework.md
-> sub-skills/tasks/assignment-source-intake.md
-> sub-skills/tools/assignment-recon.md
-> sub-skills/tasks/assignment-workflow-planner.md
```

The run stopped at the first `[B]` planner alignment boundary. It did not write
`pipeline_design.md`, did not approve orchestration, did not call
`task-orchestrator.md`, and did not generate draft artifacts.

`current-state-intake.md` was skipped because the route was `clean_start`.

## Evidence

- `prelaunch_startup_inventory.json` selected `entry_preset: clean_start`,
  `route: assignment-source-intake.md`, and `recommended_action: recon`.
- `stage_reviews/child_dispatch_ledger.json` recorded a real
  `reference_collector` child dispatch:
  `019ecb9c-986b-79c1-aa84-eab7511a26b0`.
- `investigation/review_a.json` recorded:
  - `reference_collector_used: true`
  - `source_scout_pipeline_used: false`
  - `announcements_checked: true`
  - `pdf_link_manifests_checked: true`
  - `verdict: proceed`
- `references/REFERENCE_INDEX.md` was present and pointed to preserved source
  docs, Canvas-native sources, and PDF link manifests.
- Announcements were screened into per-object preserved sources:
  - `references/canvas_native/announcement-26545/source.json`
  - `references/canvas_native/announcement-26229/source.json`
- No bulk `references/canvas_native/announcements/source.json` was created.
- Both preserved announcement `source.json` files had top-level JSON type
  `object`, not `array`.
- Path-level legacy artifact search found no files matching:
  - `*reading_plan.compact*`
  - `source_findings.compact.md`
  - `source_index.json`
  - `body_evidence_fragments/*`
  - `scout_receipts/*`

## Boundary Reached

The first planner alignment question was about user-owned project direction:
sport-related social issue, population/site/context, and method direction. This
is the correct stop point for an open-ended proposal assignment.

## Issue Found And Fixed

The validation exposed one contract gap: the generated
`prelaunch_startup_inventory.json` had `work_dir: null`. Root cause: the router
required determining `work_dir`, but the startup inventory JSON template did not
require persisting it, and downstream source/current-state intake docs did not
explicitly reject missing or mismatched workbench paths.

Fix:

- `do-homework.md` startup inventory template now includes `work_dir`.
- `assignment-source-intake.md` treats missing or mismatched `work_dir` as stale
  inventory and returns to router/preflight.
- `current-state-intake.md` treats missing or mismatched `work_dir` as stale
  inventory before shallow retained-artifact reconstruction.
- `tests/test_homework_router_split_policy.py` covers the workbench-path
  contract.

## Verification Commands

```bash
find data/homework/UCUG1808-L01 \( -name '*reading_plan.compact*' -o -name 'source_findings.compact.md' -o -name 'source_index.json' -o -path '*/body_evidence_fragments/*' -o -path '*/scout_receipts/*' \) -print
jq '{reference_collector_used, source_scout_pipeline_used, announcements_checked, relevant_announcements, pdf_link_manifests_checked, verdict, blocked_sources, forbidden_or_stale_sources}' data/homework/UCUG1808-L01/investigation/review_a.json
for f in data/homework/UCUG1808-L01/references/canvas_native/announcement-*/source.json; do printf '%s: ' "$f"; jq -r 'type' "$f"; done
.venv/bin/python -m pytest tests -q
```

Final test result:

```text
40 passed
```
