# Homework Router Source Intake Planner Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `do-homework.md` into a router, clean-start source intake, workflow planner, and retained current-state intake tool without changing the already-debugged runtime behavior.

**Architecture:** Keep `sub-skills/tasks/do-homework.md` as the stable user-facing entrypoint and route downstream work by `entry_preset` / `recommended_action`. Move clean-start Canvas/source reconnaissance into `sub-skills/tasks/assignment-source-intake.md`, move alignment and pipeline design into `sub-skills/tasks/assignment-workflow-planner.md`, and extract retained-artifact current-state exploration into `sub-skills/tools/current-state-intake.md`. Policy tests lock the boundaries so future agents do not reintroduce the old monolithic flow or the removed source-scout chain.

**Tech Stack:** Markdown runtime contracts, pytest policy tests, existing AutoStudy task/tool docs, existing Canvas CLI command contracts.

---

## File Structure

| Path | Responsibility |
|---|---|
| `sub-skills/tasks/do-homework.md` | Thin router: setup checks, assignment/work_dir resolution, preflight archive/startup inventory, route table, handoff instructions. |
| `sub-skills/tasks/assignment-source-intake.md` | Clean-start source/spec reconnaissance: workbench source setup, `assignment-recon.md`, `reference_collector`, A-gate terminal artifacts, handoff to planner. |
| `sub-skills/tasks/assignment-workflow-planner.md` | User-facing recon briefing, `[B]` alignment, `[C]` pipeline design, pipeline review, retained-artifact planner entry points. |
| `sub-skills/tools/current-state-intake.md` | Retained-artifact current-state intake: read startup inventory, dispatch/skip non-source scouts, write `explore_manifest.json`, `explore_context.md`, optional `repair_recon.md` and `repair_request.md`. |
| `sub-skills/tools/_index.md` | Register `current-state-intake`. |
| `skill.md`, `README.md`, `README.en.md`, `README.quick.md`, `docs/ROADMAP.md`, `docs/runtime-agent-protocol.md`, `docs/development-validation-standard.md`, `docs/COLLABORATION.md` | Update task/tool routing references and retained/current-state boundaries. |
| `tests/test_homework_router_split_policy.py` | New policy tests for the split boundaries. |
| Existing policy tests | Update read sets when assertions should include the new task/tool files instead of only `do-homework.md`. |

## Task 1: Add Boundary Policy Tests

**Files:**
- Create: `tests/test_homework_router_split_policy.py`
- Modify: existing tests only when they still assume all contracts live in `sub-skills/tasks/do-homework.md`

- [ ] **Step 1: Write failing tests**

Create `tests/test_homework_router_split_policy.py` with this content:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    assert target.exists(), f"Expected policy file to exist: {path}"
    return target.read_text(encoding="utf-8")


def test_split_files_exist_and_router_names_routes():
    router = read("sub-skills/tasks/do-homework.md")

    assert (ROOT / "sub-skills/tasks/assignment-source-intake.md").exists()
    assert (ROOT / "sub-skills/tasks/assignment-workflow-planner.md").exists()
    assert (ROOT / "sub-skills/tools/current-state-intake.md").exists()
    assert "sub-skills/tasks/assignment-source-intake.md" in router
    assert "sub-skills/tasks/assignment-workflow-planner.md" in router
    assert "prelaunch_startup_inventory.json" in router
    assert "recommended_action" in router


def test_router_does_not_inline_source_or_planner_bodies():
    router = read("sub-skills/tasks/do-homework.md")

    assert "### [B] Recon Summary + Alignment Loop" not in router
    assert "### [C] Design Pipeline" not in router
    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in router
    assert "Follow the Canvas Generic stages:" not in router


def test_source_intake_owns_clean_start_recon_only():
    source = read("sub-skills/tasks/assignment-source-intake.md")

    assert "assignment-recon.md" in source
    assert "reference_collector" in source
    assert "references/REFERENCE_INDEX.md" in source
    assert "investigation/review_a.json" in source
    assert "sub-skills/tasks/assignment-workflow-planner.md" in source
    assert "### [B] Recon Summary + Alignment Loop" not in source
    assert "### [C] Design Pipeline" not in source


def test_workflow_planner_owns_alignment_pipeline_and_retained_entry():
    planner = read("sub-skills/tasks/assignment-workflow-planner.md")

    assert "### [B] Recon Summary + Alignment Loop" in planner
    assert "### [C] Design Pipeline" in planner
    assert "../tools/current-state-intake.md" in planner
    assert "repair_plan.md" in planner
    assert "repair_pipeline_design.md" in planner
    assert "Pipeline Review Status" in planner
    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in planner


def test_current_state_intake_tool_boundary():
    text = read("sub-skills/tools/current-state-intake.md")

    assert "prelaunch_startup_inventory.json" in text
    assert "retained user-visible artifacts" in text
    assert "artifact/codebase/process-history/verification" in text
    assert "allowlisted_history_files" in text
    assert "investigation/explore_manifest.json" in text
    assert "investigation/explore_context.md" in text
    assert "investigation/repair_recon.md" in text
    assert "must not write `spec.md`" in text
    assert "must not run clean-start Canvas/source recon" in text


def test_tools_index_registers_current_state_intake():
    index = read("sub-skills/tools/_index.md")

    assert "current-state-intake" in index
    assert "[current-state-intake.md](./current-state-intake.md)" in index
    assert "retained" in index
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_homework_router_split_policy.py -q
```

Expected: tests fail because `assignment-source-intake.md`, `assignment-workflow-planner.md`, and `current-state-intake.md` do not exist yet.

- [ ] **Step 3: Commit tests**

```bash
git add tests/test_homework_router_split_policy.py
git commit -m "test: cover homework router split boundaries"
```

Expected: one test-only commit.

## Task 2: Create `current-state-intake.md`

**Files:**
- Create: `sub-skills/tools/current-state-intake.md`
- Modify: `sub-skills/tools/_index.md`

- [ ] **Step 1: Create the tool workflow file**

Create `sub-skills/tools/current-state-intake.md` with this structure and wording:

````markdown
---
name: current-state-intake
description: Retained-artifact current-state intake. Read startup inventory, retained user-visible artifacts, and allowlisted history; dispatch or skip bounded non-source scouts; write current-run explore context before repair planning.
---

# current-state-intake

Use this tool workflow from `sub-skills/tasks/assignment-workflow-planner.md`
when a run starts from retained artifacts, a prior draft, a previous result,
user feedback, `review_or_submit`, `review_or_execute`, or recovery/continue
state.

It answers:

1. Which retained user-visible artifacts are valid current task context?
2. Which prior files are forbidden process evidence unless explicitly allowlisted?
3. Which artifact, codebase, process-history, or verification scouts are needed?
4. What current-state facts must the planner know before writing `repair_plan.md`
   or `repair_pipeline_design.md`?

Runtime invariants:

- Read `<work_dir>/prelaunch_startup_inventory.json` first.
- Only retained user-visible artifacts named in startup inventory are current
  task context.
- Old logs, prior reviews, transcripts, old stage receipts, old
  `pipeline_design.md`, prior `repair_plan.md`, and prior
  `repair_pipeline_design.md` are process evidence by default.
- Process-history scouts may read only exact `allowlisted_history_files` named
  in startup inventory.
- Enable only artifact/codebase/process-history/verification scouts whose inputs
  exist and affect planning.
- Record skipped scouts with a concrete reason.
- Write current-run findings to `investigation/explore_manifest.json` and
  `investigation/explore_context.md`.
- Write `investigation/repair_recon.md` when a retained artifact or prior
  progress summary would reduce planning ambiguity.
- Write `repair_request.md` when the user's feedback/change request needs a
  stable file.
- Subagents and this tool workflow must not write `spec.md`,
  `investigation/review_a.json`, `investigation/alignment_brief.md`,
  `repair_plan.md`, `pipeline_design.md`, or `repair_pipeline_design.md`.
- This tool must not run clean-start Canvas/source recon. If source/spec
  evidence is missing, stale, or blocking, write the blocker into
  `investigation/explore_context.md` and return control to the planner.

## Capability

- `current_state_intake` - `(work_dir, current_request)` -> current-run
  retained-state evidence under `investigation/` plus optional `repair_request.md`.

## Inputs

```text
<work_dir>/prelaunch_startup_inventory.json
current user request / repair request
retained_startup_files or retained_user_visible_artifacts from startup inventory
allowlisted_history_files from startup inventory
```

## Outputs

```text
<work_dir>/investigation/explore_manifest.json
<work_dir>/investigation/explore_context.md
<work_dir>/investigation/repair_recon.md    # optional, retained-artifact compatibility
<work_dir>/repair_request.md                # optional, stable user feedback/change request
```

## Stage 1 - Read Startup Inventory

Open `prelaunch_startup_inventory.json` and extract:

- `entry_preset`
- `route`
- retained artifact list
- `allowlisted_history_files`
- `forbidden_context`
- archived/removed stale evidence
- current user request or repair request source
- non-source scout inputs, when present

If `entry_preset` is not `retained_artifact_start`, stop and report that this
tool is not the correct entry path.

## Stage 2 - Decide Scout Coverage

Use this table:

| Evidence class | Enable when | Output expectation |
|---|---|---|
| `artifact` | retained draft/package/rendered/current result exists and affects the next plan | current artifact status, missing pieces, user-visible quality risks |
| `codebase` | retained artifact includes runnable code, app, notebook, tests, package, or dependencies | repo/package layout, runnable commands, dependency risks |
| `process_history` | exact `allowlisted_history_files` exist and affect planning | distilled prior decisions/results only; no raw archive leakage |
| `verification` | lightweight checks can reveal current state without doing the actual task | current pass/fail surface and verification risks |

Every scout is either `enabled`, `skipped`, or `inline_fallback` in
`investigation/explore_manifest.json`.

## Stage 3 - Dispatch Or Inline Fallback

For each enabled non-source scout:

1. Dispatch a read-only child with one evidence class.
2. Record the dispatch in `stage_reviews/child_dispatch_ledger.json` with role
   `explore_scout`, scout type, and real `agent_id` or `transcript_handle`.
3. Require a receipt under
   `investigation/_appendix/scout_receipts/<scout_type>_result.json` or an
   equivalent path listed in `explore_manifest.json`.

If child dispatch is unavailable or the request is mechanically tiny, inline
fallback is allowed only when `explore_manifest.json` records
`delegation_mode: "inline_fallback"` or `executed_by: "main-agent"` plus the
specific reason.

## Stage 4 - Consolidate Current-State Evidence

Write `investigation/explore_context.md` with:

- current retained artifacts that planning may use;
- current request or repair request;
- source/spec/reference files still valid for this run;
- prior decisions that still apply;
- stale or forbidden context;
- enabled and skipped scouts with reasons;
- current verification surface;
- likely scope;
- questions that require user alignment;
- blockers, including missing or stale source/spec evidence.

When useful, write `investigation/repair_recon.md` as a retained-artifact
compatibility summary. It may summarize current draft status, prior decisions,
passed checks, failed checks, and known risks, but must label stale or forbidden
context.

## Stage 5 - Self-Check

Before returning to the planner, verify:

- `explore_manifest.json` exists and accounts for every scout class.
- `explore_context.md` exists.
- Every enabled scout has a ledger row and receipt path, or inline fallback is
  recorded.
- Process-history evidence came only from `allowlisted_history_files`.
- No raw archive, old transcript, old review, or prior diagnostic became general
  planner context.
- No final planning artifact was written by this tool.
````

- [ ] **Step 2: Register the tool**

Add this row to `sub-skills/tools/_index.md` after `assignment-recon`:

````markdown
| **current-state-intake** | [current-state-intake.md](./current-state-intake.md) | Retained-artifact current-state intake -> explore context + repair recon | work_dir, current_request | investigation/explore_manifest.json, investigation/explore_context.md, optional repair_request.md |
````

Add this capability vocabulary row:

````markdown
| `current_state_intake` | Retained-artifact current state -> explore context |
````

- [ ] **Step 3: Run boundary tests**

```bash
.venv/bin/python -m pytest tests/test_homework_router_split_policy.py -q
```

Expected: tests still fail for missing task files, but `test_current_state_intake_tool_boundary` and `test_tools_index_registers_current_state_intake` pass.

- [ ] **Step 4: Commit**

```bash
git add sub-skills/tools/current-state-intake.md sub-skills/tools/_index.md
git commit -m "docs: add current-state intake tool"
```

## Task 3: Create Clean-Start Source Intake Task

**Files:**
- Create: `sub-skills/tasks/assignment-source-intake.md`
- Source sections: `sub-skills/tasks/do-homework.md` current clean-start intro, required artifact chain, `[A] Build The Assignment Workbench`, `[A3] Canvas Generic Reconnaissance - Mandatory`, `[A4] Gate On Reconnaissance Quality`

- [ ] **Step 1: Create the task header and scope**

Create `sub-skills/tasks/assignment-source-intake.md` with:

````markdown
---
name: assignment-source-intake
description: Clean-start homework source/spec intake. Use after do-homework router has created a workbench and accepted startup inventory for a clean-start assignment.
---

# Assignment Source Intake

Use this task only for `entry_preset: clean_start`. It owns clean-start
Canvas/source reconnaissance and stops after terminal source artifacts are ready
for `sub-skills/tasks/assignment-workflow-planner.md`.

Do not use this task for retained drafts, prior outputs, `review_or_submit`,
`review_or_execute`, or repair/continue flows unless the planner/router has
identified missing or stale source evidence as a blocker.
````

- [ ] **Step 2: Move the clean-start source contract**

Move the existing clean-start source sections from `do-homework.md` into this
file with only cross-reference edits:

```text
Required artifact chain
Directory boundary
Main Agent read boundary
Actor rules
Hybrid Gate Report rule
Clean-Start Proposal Runtime Checklist
[A] Build The Assignment Workbench
[A0] Startup Inventory Rule when it describes accepted clean-start inventory
Explore Mode Rules only where source intake needs them
[A3] Canvas Generic Reconnaissance - Mandatory
[A4] Gate On Reconnaissance Quality
```

Keep exact policy strings that existing tests assert, including:

```text
reference_collector
references/REFERENCE_INDEX.md
references/canvas_native/
Do not create `reading_plan.compact.json`
Do not create `source_findings.compact.md`
Subagents must not write final `spec.md`
proposal/research/open-ended
PDF link annotation manifests
references/*.pdf.links.json
do not treat PDF text extraction as complete
Spec Hard Requirements / No-Downgrade Policy
required_spec_constraints
fallback_allowed_for_final: false
```

- [ ] **Step 3: Add terminal handoff**

At the end of `assignment-source-intake.md`, add:

````markdown
## Terminal Handoff

After this file completes successfully, continue by reading:

```text
sub-skills/tasks/assignment-workflow-planner.md
```

Do not execute draft-production stages here. This task ends when source intake
has produced the terminal reconnaissance artifacts and the next action is
planner alignment or recovery.
````

- [ ] **Step 4: Run focused tests**

```bash
.venv/bin/python -m pytest tests/test_homework_router_split_policy.py tests/test_source_body_audit_policy.py tests/test_pdf_link_annotation_policy.py tests/test_spec_hard_requirement_policy.py -q
```

Expected: split tests still fail until planner/router are created; old policy tests may fail where they still read only `do-homework.md`.

- [ ] **Step 5: Commit**

```bash
git add sub-skills/tasks/assignment-source-intake.md
git commit -m "docs: add assignment source intake task"
```

## Task 4: Create Workflow Planner Task

**Files:**
- Create: `sub-skills/tasks/assignment-workflow-planner.md`
- Source sections: `sub-skills/tasks/do-homework.md` current `[B]`, `[C]`, output/pipeline review sections, retained/review/continue action guidance

- [ ] **Step 1: Create the task header and entry modes**

Create `sub-skills/tasks/assignment-workflow-planner.md` with:

````markdown
---
name: assignment-workflow-planner
description: Homework workflow planner. Use after clean source intake, or directly for retained artifacts, review/submit, review/execute, and recovery flows.
---

# Assignment Workflow Planner

This task owns user-facing agreement and pipeline planning. It does not run
clean-start Canvas/source reconnaissance. For clean starts, read the terminal
outputs from `sub-skills/tasks/assignment-source-intake.md`. For retained
artifacts, first invoke `../tools/current-state-intake.md`.

## Entry Modes

| Entry | Required read | Next action |
|---|---|---|
| clean recon | `prelaunch_startup_inventory.json`, `spec.md`, `investigation/explore_context.md`, `investigation/recon_summary.md`, `investigation/review_a.json`, `references/` | run `[B]`, then `[C]` |
| retained artifact | `prelaunch_startup_inventory.json`, then `../tools/current-state-intake.md` outputs | run retained alignment, write `repair_plan.md`, then `repair_pipeline_design.md` when needed |
| pipeline review | existing `pipeline_design.md` or `repair_pipeline_design.md` | help user approve/revise; do not execute inside planner |
| draft review | retained draft/result artifacts named in startup inventory | help user review/revise/submit path; do not clean-start by default |
| recovery | previous `result.json` plus allowlisted history | use current-state intake unless source evidence is explicitly missing/stale |
````

- [ ] **Step 2: Move `[B]` alignment**

Move the current `### [B] Recon Summary + Alignment Loop` section from
`do-homework.md` into this file. Keep the conclusion-first briefing rule and the
runtime/user boundary intact.

- [ ] **Step 3: Move `[C]` pipeline planning**

Move the current `### [C] Design Pipeline`, output format, pipeline review
status, and handoff-to-orchestrator guidance from `do-homework.md` into this
file. Preserve current artifact names:

```text
investigation/alignment_brief.md
repair_plan.md
pipeline_design.md
repair_pipeline_design.md
result.json
Pipeline Review Status: awaiting_user_review
```

- [ ] **Step 4: Add retained current-state invocation**

Before the retained-artifact alignment path, add:

````markdown
## Retained Current-State Intake

For retained artifacts, previous results, user feedback, `review_or_submit`,
`review_or_execute`, or recovery/continue entries, first read:

```text
../tools/current-state-intake.md
```

Run that tool against the accepted `prelaunch_startup_inventory.json` and the
current request. Then read:

```text
investigation/explore_manifest.json
investigation/explore_context.md
investigation/repair_recon.md       # when present
repair_request.md                   # when present
```

Do not read raw archived process evidence unless `prelaunch_startup_inventory.json`
allowlists exact paths for process-history exploration.
````

- [ ] **Step 5: Run focused tests**

```bash
.venv/bin/python -m pytest tests/test_homework_router_split_policy.py -q
```

Expected: planner tests pass except router-specific assertions that still depend on shrinking `do-homework.md`.

- [ ] **Step 6: Commit**

```bash
git add sub-skills/tasks/assignment-workflow-planner.md
git commit -m "docs: add assignment workflow planner task"
```

## Task 5: Replace `do-homework.md` With Router

**Files:**
- Modify: `sub-skills/tasks/do-homework.md`

- [ ] **Step 1: Replace body with router contract**

Rewrite `do-homework.md` as a concise router. Preserve the front matter name and description, then include:

````markdown
# Do Homework

Use this task as the stable user-facing entrypoint for one Canvas assignment.
It does not inline source reconnaissance, alignment, pipeline design, or draft
execution. It routes to:

```text
sub-skills/tasks/assignment-source-intake.md
sub-skills/tasks/assignment-workflow-planner.md
```

## Router Responsibilities

1. Verify `.venv/bin/canvascli version` and `.venv/bin/canvascli whoami`.
2. Resolve one assignment, using `scripts/select_plan_item.py` output when
   available.
3. Determine `work_dir`, `recommended_action`, and `entry_preset`.
4. Run preflight archive/startup inventory.
5. Route to the downstream task file.
6. Stop before draft execution unless the user separately approves
   `sub-skills/tasks/task-orchestrator.md`.

## Preflight Startup Inventory

Before reading old workbench files as task context, write or refresh:

```text
<work_dir>/prelaunch_startup_inventory.json
```

It must distinguish:

```json
{
  "entry_preset": "clean_start | retained_artifact_start",
  "route": "assignment-source-intake.md | assignment-workflow-planner.md",
  "retained_user_visible_artifacts": [],
  "allowlisted_history_files": [],
  "forbidden_context": [],
  "archived_process_evidence": [],
  "must_not_clean_start": false
}
```

Old process evidence is not task context by default. A process-history scout may
inspect it only when the startup inventory allowlists exact files or directories.

## Route Table

| Input state | Route |
|---|---|
| `recommended_action: recon`, `entry_preset: clean_start` | read `sub-skills/tasks/assignment-source-intake.md`, then `sub-skills/tasks/assignment-workflow-planner.md` |
| `recommended_action: review_or_execute` / `pipeline_ready` | read `sub-skills/tasks/assignment-workflow-planner.md#pipeline-review`; do not rerun source recon |
| `recommended_action: review_or_submit` / `draft_ready` | read `sub-skills/tasks/assignment-workflow-planner.md#retained-artifact-review`; do not clean-start by default |
| `recommended_action: continue` / failed or interrupted | read `sub-skills/tasks/assignment-workflow-planner.md#recovery-intake`; run source intake only when missing/stale source evidence is the blocker |
| direct retained draft or feedback request | read `sub-skills/tasks/assignment-workflow-planner.md`, which invokes `../tools/current-state-intake.md` |

## Required Source Contract

Clean-start source intake must still use `reference_collector`,
`references/REFERENCE_INDEX.md`, `references/canvas_native/`, complete original
source preservation, `spec.md`, `investigation/rubric.md`,
`investigation/review_a.json`, and `investigation/explore_context.md`.

Do not create `reading_plan.compact.json` or `source_findings.compact.md` in
standard runs. Subagents must not write final `spec.md`,
`investigation/review_a.json`, `pipeline_design.md`, or user alignment decisions.

## Handoff

After routing, follow the downstream file. Draft execution happens only through
`sub-skills/tasks/task-orchestrator.md` after the user approves
`pipeline_design.md` or `repair_pipeline_design.md`.
````

- [ ] **Step 2: Preserve tested policy phrases in router or move tests**

If existing tests require policy phrases that now belong in source intake, update
the tests to read both files instead of duplicating all text in the router.

Use this pattern in tests:

```python
policy_text = "\n".join(
    [
        read("sub-skills/tasks/do-homework.md"),
        read("sub-skills/tasks/assignment-source-intake.md"),
        read("sub-skills/tasks/assignment-workflow-planner.md"),
        read("sub-skills/tools/current-state-intake.md"),
        read("sub-skills/tools/assignment-recon.md"),
        read("docs/runtime-agent-protocol.md"),
    ]
)
```

- [ ] **Step 3: Run focused tests**

```bash
.venv/bin/python -m pytest tests/test_homework_router_split_policy.py tests/test_source_body_audit_policy.py tests/test_pdf_link_annotation_policy.py tests/test_spec_hard_requirement_policy.py -q
```

Expected: all focused tests pass.

- [ ] **Step 4: Commit**

```bash
git add sub-skills/tasks/do-homework.md tests
git commit -m "docs: make do-homework route split flows"
```

## Task 6: Synchronize Entry Docs And Runtime Docs

**Files:**
- Modify: `skill.md`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `README.quick.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/COLLABORATION.md`
- Modify: `docs/runtime-agent-protocol.md`
- Modify: `docs/development-validation-standard.md`
- Modify: `docs/superpowers/specs/2026-06-15-homework-router-source-intake-planner-split-design.md` if implementation wording changed

- [ ] **Step 1: Update skill architecture tree**

In `skill.md`, update the runtime architecture tree so tasks include:

```text
do-homework.md                  # Router / preflight / route selection
assignment-source-intake.md     # Clean-start source/spec recon
assignment-workflow-planner.md  # Alignment, planning, retained artifact flow
```

and tools include:

```text
current-state-intake.md
```

- [ ] **Step 2: Update user flow wording**

In `skill.md`, keep `do-homework.md` as the user route, but change the retained draft paragraph to:

```markdown
For retained drafts or user feedback, `do-homework.md` routes directly to
`assignment-workflow-planner.md`, which invokes
`sub-skills/tools/current-state-intake.md`. Preserve only user-visible artifacts
declared in startup inventory, write a current `repair_plan.md`, then plan
through `repair_pipeline_design.md` when appropriate.
```

- [ ] **Step 3: Update README files**

In `README.md`, `README.en.md`, and `README.quick.md`, update the repository
structure and status language to mention:

```text
assignment-source-intake.md
assignment-workflow-planner.md
current-state-intake.md
```

Keep the public task name as `do-homework`; do not present the new internal
files as separate user commands.

- [ ] **Step 4: Update runtime protocol**

In `docs/runtime-agent-protocol.md`, add or adjust the homework file mapping so:

```text
do-homework.md = router/preflight
assignment-source-intake.md = clean-start source/spec intake
assignment-workflow-planner.md = alignment/planning/retained planner
current-state-intake.md = retained current-state exploration tool
```

Also update retained-artifact sections to say the planner invokes the tool and
then reads `explore_context.md` / `repair_recon.md`.

- [ ] **Step 5: Update validation standard**

In `docs/development-validation-standard.md`, replace references that imply
`do-homework.md [B]` owns retained current-state exploration with:

```text
do-homework router -> assignment-workflow-planner.md -> current-state-intake.md -> repair_plan.md / repair_pipeline_design.md
```

Keep existing startup inventory, no-leak cleanup, scout ledger, and allowlisted
history rules intact.

- [ ] **Step 6: Run documentation search**

```bash
rg -n "do-homework \\[A\\]|do-homework \\[B\\]|do-homework \\[C\\]|assignment-source-intake|assignment-workflow-planner|current-state-intake|source_findings.compact|reading_plan.compact" skill.md README*.md docs sub-skills tests
```

Expected:

- `do-homework [A/B/C]` appears only in historical docs or compatibility language, or has been changed to the new files.
- `source_findings.compact` and `reading_plan.compact` appear only in forbidden/stale contexts.
- new files are referenced in entry docs and runtime docs.

- [ ] **Step 7: Run tests and commit**

```bash
.venv/bin/python -m pytest tests -q
git add skill.md README.md README.en.md README.quick.md docs sub-skills/tools/_index.md tests
git commit -m "docs: sync homework split documentation"
```

Expected: full policy test suite passes.

## Task 7: Run Subagent Validation On UCUG1808 To A/B Boundary

**Files:**
- Runtime output only under `data/homework/UCUG1808-L01/` or a fresh test workbench
- Do not commit `data/homework/**` unless the repo already tracks a required fixture

- [ ] **Step 1: Clean the target workbench if needed**

Before validation, inspect:

```bash
find data/homework/UCUG1808-L01 -maxdepth 3 -type f | sort | sed -n '1,200p'
git status --short -- data/homework/UCUG1808-L01
```

If the directory is untracked runtime output, remove it for a clean run:

```bash
rm -rf data/homework/UCUG1808-L01
```

Do not remove tracked or user-edited files without checking `git status`.

- [ ] **Step 2: Dispatch an independent coordinator worker**

Use a fresh subagent/worker as the do-homework coordinator. The main agent must
not act as the coordinator for this validation.

Prompt:

```text
You are validating the AutoStudy do-homework split in /Users/deepwisdom/Desktop/project/autoust-test.

Use the repository skill/task docs, starting at skill.md and sub-skills/tasks/do-homework.md.
Run the UCUG1808 Project Proposal Files homework flow only through source intake and the first planner alignment boundary. Stop before draft execution.

You must:
- treat do-homework.md as the router;
- for clean start, read assignment-source-intake.md and then assignment-workflow-planner.md;
- use assignment-recon.md Stage 1 and reference_collector rules;
- preserve task-relevant references under references/;
- not create reading_plan.compact.json or source_findings.compact.md;
- write terminal recon artifacts;
- report whether current-state-intake.md was skipped because this is clean start;
- stop at the first user alignment / pipeline review boundary, not execute stages.

Return:
- command/prompt path used;
- files created under data/homework/UCUG1808-L01;
- whether source intake used reference_collector;
- whether announcements were screened per relevant object;
- whether no legacy compact/source-scout files appeared;
- whether the route handoff matched the split docs;
- any blockers.
```

- [ ] **Step 3: Main-agent audit**

After the worker returns, inspect:

```bash
find data/homework/UCUG1808-L01 -maxdepth 4 -type f | sort
find data/homework/UCUG1808-L01/project-proposal-files -maxdepth 4 -type f | sort
rg -n "reading_plan.compact|source_findings.compact|content_scout|metadata_scout" data/homework/UCUG1808-L01 || true
```

Expected:

- no `reading_plan.compact*.json`;
- no `source_findings.compact.md`;
- no old metadata/content scout chain;
- `references/REFERENCE_INDEX.md` exists;
- task-relevant Canvas-native announcements are individual preserved objects when relevant, not full `announcements/source.json`;
- planner boundary is reached without draft execution.

- [ ] **Step 4: Record validation note**

Create a short tracked validation note only if this repo already keeps such notes
for development runs. Preferred path:

```text
docs/superpowers/validation/2026-06-15-homework-router-split-ucug1808.md
```

If there is no validation notes directory or local policy says not to track runtime
validation notes, summarize the validation only in the final response and do not
commit runtime `data/` output.

- [ ] **Step 5: Commit validation docs if created**

```bash
git add docs/superpowers/validation/2026-06-15-homework-router-split-ucug1808.md
git commit -m "test: validate homework router split on UCUG1808"
```

Skip this commit if no validation doc was created.

## Task 8: Final Review, Squash Policy, And Push

**Files:**
- All changed docs/tests

- [ ] **Step 1: Self-review diff**

```bash
git status --short
git diff --check
git diff --stat
git diff -- sub-skills/tasks/do-homework.md sub-skills/tasks/assignment-source-intake.md sub-skills/tasks/assignment-workflow-planner.md sub-skills/tools/current-state-intake.md
```

Expected: no whitespace errors; diff reads as a split/move plus docs/tests, not a broad behavior rewrite.

- [ ] **Step 2: Full tests**

```bash
.venv/bin/python -m pytest tests -q
```

Expected: all tests pass.

- [ ] **Step 3: Review commit granularity**

User preference: one coherent task commit, not many tiny commits. If execution produced many micro-commits, squash them into one or a small number of coherent commits before final push:

```bash
git log --oneline --decorate -8
```

Acceptable final shape:

```text
docs: split homework router and intake flows
```

or at most:

```text
docs: add homework split policy tests
docs: split homework router and intake flows
test: validate homework split on UCUG1808
```

- [ ] **Step 4: Push current branch**

```bash
git status --short --branch
git push origin codex/deepwisdom-updates
```

Expected: branch is pushed; no uncommitted implementation docs/tests remain. Runtime `data/homework/**` output may remain untracked/ignored unless explicitly cleaned.

## Self-Review Checklist

- Spec coverage: the plan covers router, source intake, planner, current-state tool, docs, tests, and UCUG1808 validation.
- Boundary coverage: retained current-state intake lives in `sub-skills/tools/current-state-intake.md`; planner links to it instead of inlining the full workflow.
- No source-scout regression: tests keep `reading_plan.compact` and `source_findings.compact` forbidden/stale.
- Subagent validation: UCUG1808 validation explicitly requires an independent coordinator worker.
- Commit policy: plan warns to avoid noisy micro-commits and squash if needed.
