# Homework Staged Recon Routing Validation

Date: 2026-06-16

## Scope

Validated the current staged homework routing for UCUG1808-L01 `Project Proposal
Files` as an independent runtime coordinator.

- Repository: `/Users/deepwisdom/Desktop/project/autoust-test`
- Workbench: `data/homework/UCUG1808-L01`
- Course ID: `2963`
- Assignment ID: `23014`
- Route under test: `skill.md` -> `sub-skills/tasks/do-homework.md` ->
  `sub-skills/tasks/background-recon.md`
- Stop point: `[A5] Recon Briefing + Source Confirmation` boundary before
  normal alignment planning
- Not executed: `task-orchestrator.md`, draft generation, Canvas submission

The validation did not modify runtime docs. It created only this tracked
verification report plus ignored workbench evidence under `data/homework/`.

## Observed Clean-Start Read Chain

The public clean-start chain starts at `skill.md`, which routes homework work to
`sub-skills/tasks/do-homework.md`. The router then exposes exactly one
first-stage task for clean start:

```text
skill.md
-> sub-skills/tasks/do-homework.md
-> sub-skills/tasks/background-recon.md
```

`do-homework.md` states that clean start routes to
`sub-skills/tasks/background-recon.md`, and that the router must not read or
name later-stage task files. `background-recon.md` owns source intake,
recon briefing/source confirmation, and its own tail handoff.

`skill.md` contains a top-level architecture list that names later files such as
`alignment-planning.md` and `task-orchestrator.md`, but the runtime router file
does not expose them in the clean-start route.

## Router Disclosure Check

Required command:

```bash
rg -n "alignment-planning|task-orchestrator|assignment-workflow-planner|assignment-source-intake|current-state-intake|assignment-recon" sub-skills/tasks/do-homework.md
```

Result: no output; exit code `1`.

This confirms `do-homework.md` does not prematurely expose
`alignment-planning.md`, `task-orchestrator.md`, `assignment-workflow-planner`,
`assignment-source-intake`, `current-state-intake`, or `assignment-recon`.

## A5 Recon Confirmation Check

`sub-skills/tasks/background-recon.md` contains `[A5] Recon Briefing + Source
Confirmation`.

Observed contract:

- A5 runs only after terminal reconnaissance artifacts are written and `[A4]`
  passes.
- A5 requires the Main Agent to present source understanding and ask the user to
  confirm it before reading the alignment stage.
- A5 explicitly says this checkpoint is not alignment and not pipeline planning.
- A5 says topic, research question, group facts, and method choice belong to the
  later alignment loop.

Actual clean-start run reached this boundary. Workbench evidence:

- `data/homework/UCUG1808-L01/prelaunch_startup_inventory.json`
- `data/homework/UCUG1808-L01/investigation/explore_manifest.json`
- `data/homework/UCUG1808-L01/references/REFERENCE_INDEX.md`
- `data/homework/UCUG1808-L01/spec.md`
- `data/homework/UCUG1808-L01/investigation/rubric.md`
- `data/homework/UCUG1808-L01/investigation/review_a.json`
- `data/homework/UCUG1808-L01/investigation/recon_summary.md`
- `data/homework/UCUG1808-L01/investigation/explore_context.md`
- `data/homework/UCUG1808-L01/stage_reviews/child_dispatch_ledger.json`
- `data/homework/UCUG1808-L01/stage_reviews/reference_collector_receipt.json`

`review_a.json` records:

```json
{
  "verdict": "proceed_to_a5_source_confirmation",
  "reference_collector_used": true,
  "reference_collector_agent_id": "019eced6-faf5-7d12-8bae-afd2688f7cb6",
  "a5_status": "recon_briefing_ready_source_confirmation_required",
  "alignment_handoff_status": "not_executed_in_run; tail handoff target verified statically",
  "pipeline_or_draft_written": false,
  "canvas_submission_attempted": false
}
```

## Alignment Handoff Check

Required command:

```bash
rg -n "alignment-planning.md" sub-skills/tasks/background-recon.md sub-skills/tasks/existing-work-recon.md
```

Result:

```text
sub-skills/tasks/background-recon.md:750:sub-skills/tasks/alignment-planning.md
sub-skills/tasks/existing-work-recon.md:220:sub-skills/tasks/alignment-planning.md
```

This confirms the `alignment-planning.md` reveal appears only in the two
first-stage task tail handoff positions.

`alignment-planning.md` was read only to confirm the handoff target and entry
contract. Its entry text requires a confirmed reconnaissance briefing from
`background-recon.md` for clean starts and does not run clean-start
Canvas/source reconnaissance itself.

The actual validation run did not execute alignment planning. No
`alignment_brief.md`, `pipeline_design.md`, `stage_results/`, `draft/`, or
Canvas submit artifact was created.

## Actual Canvas Run Evidence

Canvas CLI health check:

```bash
test -d .venv && .venv/bin/canvascli version > /dev/null 2>&1 \
  && .venv/bin/canvascli whoami > /dev/null 2>&1 \
  && echo OK || echo NEEDS_SETUP
```

Result: `OK`.

Raw Canvas snapshots were fetched for assignment, rubric, front page, syllabus,
modules, all module items, assignment files, announcements, and high-signal file
metadata. The assignment still resolves as:

```json
{
  "id": 23014,
  "name": "Project Proposal Files",
  "course_id": 2963,
  "due_at": "2026-04-17T04:00:00Z"
}
```

The `reference_collector` subagent preserved:

- assignment shell, rubric status, syllabus, front-page status;
- Final project module items and Week 8 module items;
- proposal-related announcements `26545` and `26229`;
- `Writing research proposal -Group work.pdf`;
- `Final Group Research Project.pdf`;
- `Timeline& Research in Sport Social Sciences-week 8.pdf`;
- PDF text extracts and sibling `.pdf.links.json` manifests.

Key source findings:

- Canvas assignment shell requires both proposal document and slides.
- Proposal PDF specifies 1200-1500 words, proposal sections, APA7, Times New
  Roman 11, 1.5 spacing, justified alignment, and AI-use disclosure conditions.
- Week 8 methods/timeline PDF supports a focused proposal with one
  sport-related social issue, one clear research question, suitable methods, and
  proposal upload before later refinement.
- Canvas rubric is absent.
- Canvas front page returned `not_enabled_or_not_found`; this was non-blocking.
- Previous Canvas submission attachments appeared in `assignment.json` but were
  explicitly treated as forbidden clean-start context.

Forbidden legacy source-scout artifact check:

```bash
find data/homework/UCUG1808-L01 \( -path '*reading_plan.compact*' -o -name 'source_findings.compact.md' -o -path '*/_appendix/source_index.json' -o -path '*/_appendix/body_evidence_fragments/*' -o -path '*/_appendix/scout_receipts/*' \) -print
```

Result: no output.

No downstream execution artifact check:

```bash
find data/homework/UCUG1808-L01 -maxdepth 4 \( -name 'alignment_brief.md' -o -name 'pipeline_design.md' -o -name 'repair_pipeline_design.md' -o -name 'result.json' -o -path '*/draft/*' -o -path '*/stage_results/*' \) -print
```

Result: no output.

## Commands And Results

```bash
rg -n "alignment-planning|task-orchestrator|assignment-workflow-planner|assignment-source-intake|current-state-intake|assignment-recon" sub-skills/tasks/do-homework.md
```

Result: no output; exit code `1`.

```bash
rg -n "alignment-planning.md" sub-skills/tasks/background-recon.md sub-skills/tasks/existing-work-recon.md
```

Result:

```text
sub-skills/tasks/background-recon.md:750:sub-skills/tasks/alignment-planning.md
sub-skills/tasks/existing-work-recon.md:220:sub-skills/tasks/alignment-planning.md
```

```bash
.venv/bin/python -m pytest tests -q
```

Result:

```text
45 passed in 0.11s
```

```bash
jq -e . data/homework/UCUG1808-L01/prelaunch_startup_inventory.json \
  data/homework/UCUG1808-L01/investigation/explore_manifest.json \
  data/homework/UCUG1808-L01/investigation/review_a.json \
  data/homework/UCUG1808-L01/stage_reviews/reference_collector_receipt.json \
  data/homework/UCUG1808-L01/stage_reviews/child_dispatch_ledger.json > /dev/null
```

Result: exit code `0`.

## Outcome

DONE_WITH_CONCERNS.

The staged routing behavior is validated: `do-homework.md` exposes only the
first-stage clean-start route, `background-recon.md` owns A5 source
confirmation, and `alignment-planning.md` is revealed only as a tail handoff
after recon confirmation.

Concern: the actual validation run intentionally stopped before real user
alignment and did not collect a real homework user's source-confirmation answer.
This is correct for this verification scope, but it means the run proves
handoff readiness rather than executing the full next stage.
