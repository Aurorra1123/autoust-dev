# Homework Staged Recon Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename and restructure the homework routing docs so `do-homework.md` reveals only the first-stage recon task, and alignment/planning is revealed only by the first-stage file tail handoff.

**Architecture:** `do-homework.md` becomes a progressive-disclosure router with two first-stage route targets: `background-recon.md` for clean starts and `existing-work-recon.md` for retained/repair/continue starts. Both first-stage task files write terminal artifacts and then hand off to the shared `alignment-planning.md` file. The former `assignment-recon.md` contract is folded into `background-recon.md`; the former `current-state-intake.md` moves from `tools/` to `tasks/` as `existing-work-recon.md`.

**Tech Stack:** Markdown task docs, Python `pytest` policy tests, git file moves.

---

## File Map

Create or move:

- Move `sub-skills/tasks/assignment-source-intake.md` -> `sub-skills/tasks/background-recon.md`
- Move `sub-skills/tasks/assignment-workflow-planner.md` -> `sub-skills/tasks/alignment-planning.md`
- Move `sub-skills/tools/current-state-intake.md` -> `sub-skills/tasks/existing-work-recon.md`
- Remove `sub-skills/tools/assignment-recon.md` after its production contract is folded into `background-recon.md`

Modify:

- `sub-skills/tasks/do-homework.md` - router only; expose only `background-recon.md` or `existing-work-recon.md`, never `alignment-planning.md`
- `sub-skills/tools/_index.md` - remove `assignment-recon` and `current-state-intake` runtime tool entries; point pipeline guidance at `alignment-planning.md`
- `skill.md` - update runtime architecture and correct task flow
- `docs/runtime-agent-protocol.md` - update runtime file map and progressive-disclosure route contract
- `docs/canvas-pilot-reference.md` - update active homework flow names
- `docs/skills-architecture-spec.md` - update alignment/planning references
- `docs/progress/agent-progress.md` - add a short progress note for the staged routing refinement
- `tests/test_homework_router_split_policy.py` - replace old split-policy tests with staged routing tests
- `tests/test_pdf_link_annotation_policy.py` - point source recon assertions at `background-recon.md`
- `tests/test_source_body_audit_policy.py` - point source/body assertions at `background-recon.md` and alignment assertions at `alignment-planning.md`
- `tests/test_spec_hard_requirement_policy.py` - point no-downgrade planner assertions at `alignment-planning.md`

Do not edit runtime artifact names such as `spec.md`, `review_a.json`, `alignment_brief.md`, `repair_plan.md`, `pipeline_design.md`, or `repair_pipeline_design.md`.

---

### Task 1: Write Failing Staged Routing Policy Tests

**Files:**
- Modify: `tests/test_homework_router_split_policy.py`
- Modify: `tests/test_pdf_link_annotation_policy.py`
- Modify: `tests/test_source_body_audit_policy.py`
- Modify: `tests/test_spec_hard_requirement_policy.py`

- [ ] **Step 1: Replace `tests/test_homework_router_split_policy.py` with staged routing tests**

Use this complete file content:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    assert target.exists(), f"Expected policy file to exist: {path}"
    return target.read_text(encoding="utf-8")


def test_staged_route_files_exist_and_old_names_are_retired():
    assert (ROOT / "sub-skills/tasks/background-recon.md").exists()
    assert (ROOT / "sub-skills/tasks/existing-work-recon.md").exists()
    assert (ROOT / "sub-skills/tasks/alignment-planning.md").exists()

    assert not (ROOT / "sub-skills/tasks/assignment-source-intake.md").exists()
    assert not (ROOT / "sub-skills/tasks/assignment-workflow-planner.md").exists()
    assert not (ROOT / "sub-skills/tools/current-state-intake.md").exists()
    assert not (ROOT / "sub-skills/tools/assignment-recon.md").exists()


def test_router_exposes_only_first_stage_routes():
    router = read("sub-skills/tasks/do-homework.md")

    assert "sub-skills/tasks/background-recon.md" in router
    assert "sub-skills/tasks/existing-work-recon.md" in router
    assert "prelaunch_startup_inventory.json" in router
    assert "recommended_action" in router

    assert "alignment-planning.md" not in router
    assert "task-orchestrator.md" not in router
    assert "assignment-workflow-planner.md" not in router
    assert "assignment-source-intake.md" not in router
    assert "current-state-intake.md" not in router
    assert "assignment-recon.md" not in router


def test_router_does_not_inline_source_existing_or_planner_bodies():
    router = read("sub-skills/tasks/do-homework.md")

    assert "### [B] Recon Summary + Alignment Loop" not in router
    assert "### [C] Design Pipeline" not in router
    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in router
    assert "Follow the Canvas Generic stages:" not in router
    assert "Retained Current-State Intake" not in router


def test_background_recon_owns_clean_start_and_tail_handoff_only():
    background = read("sub-skills/tasks/background-recon.md")

    assert "reference_collector" in background
    assert "canvas/announcements.json" in background
    assert "references/REFERENCE_INDEX.md" in background
    assert "references/canvas_native/" in background
    assert "investigation/review_a.json" in background
    assert "PDF Link Annotation Extraction" in background
    assert "sub-skills/tasks/alignment-planning.md" in background

    assert "### [B] Recon Summary + Alignment Loop" not in background
    assert "### [C] Design Pipeline" not in background
    assert "repair_plan.md" not in background


def test_existing_work_recon_owns_retained_state_and_tail_handoff_only():
    existing = read("sub-skills/tasks/existing-work-recon.md")

    assert "prelaunch_startup_inventory.json" in existing
    assert "retained user-visible artifacts" in existing
    assert "artifact/codebase/process-history/verification" in existing
    assert "allowlisted_history_files" in existing
    assert "investigation/explore_manifest.json" in existing
    assert "investigation/explore_context.md" in existing
    assert "investigation/repair_recon.md" in existing
    assert "must not write `spec.md`" in existing
    assert "must not run clean-start Canvas/source recon" in existing
    assert "sub-skills/tasks/alignment-planning.md" in existing

    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in existing
    assert "### [B] Recon Summary + Alignment Loop" not in existing
    assert "### [C] Design Pipeline" not in existing


def test_alignment_planning_owns_shared_alignment_and_refuses_first_stage_recon():
    planner = read("sub-skills/tasks/alignment-planning.md")

    assert "### [B] Recon Summary + Alignment Loop" in planner
    assert "### [C] Design Pipeline" in planner
    assert "repair_plan.md" in planner
    assert "repair_pipeline_design.md" in planner
    assert "Pipeline Review Status" in planner
    assert "does not run `background-recon.md`" in planner
    assert "does not run `existing-work-recon.md`" in planner

    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in planner
    assert "../tools/current-state-intake.md" not in planner


def test_startup_inventory_records_workbench_path():
    router = read("sub-skills/tasks/do-homework.md")
    background = read("sub-skills/tasks/background-recon.md")
    existing = read("sub-skills/tasks/existing-work-recon.md")

    assert '"work_dir": "data/homework/<COURSE>/<assignment>"' in router
    assert "work_dir is missing" in background
    assert "does not match the active workbench" in background
    assert "work_dir is missing" in existing
    assert "does not match the active workbench" in existing


def test_tools_index_no_longer_registers_routed_homework_stages_as_tools():
    index = read("sub-skills/tools/_index.md")

    assert "assignment-recon" not in index
    assert "current-state-intake" not in index
    assert "background-recon.md" not in index
    assert "existing-work-recon.md" not in index
    assert "alignment-planning.md [C]" in index
```

- [ ] **Step 2: Update PDF link policy tests to read `background-recon.md`**

In `tests/test_pdf_link_annotation_policy.py`, make these exact substitutions:

```text
sub-skills/tools/assignment-recon.md -> sub-skills/tasks/background-recon.md
sub-skills/tasks/assignment-source-intake.md -> sub-skills/tasks/background-recon.md
```

Then update the local variable name in the PDF section test:

```python
background_recon = read("sub-skills/tasks/background-recon.md")
pdf_link_section = background_recon.split("### PDF Link Annotation Extraction", 1)[1]
```

- [ ] **Step 3: Update source-body policy tests to read new staged files**

In `tests/test_source_body_audit_policy.py`, make these exact substitutions:

```text
sub-skills/tools/assignment-recon.md -> sub-skills/tasks/background-recon.md
sub-skills/tasks/assignment-source-intake.md -> sub-skills/tasks/background-recon.md
sub-skills/tasks/assignment-workflow-planner.md -> sub-skills/tasks/alignment-planning.md
sub-skills/tools/current-state-intake.md -> sub-skills/tasks/existing-work-recon.md
```

Where a policy text list previously included both `assignment-recon.md` and
`assignment-source-intake.md`, keep only one `read("sub-skills/tasks/background-recon.md")`
entry to avoid duplicate text.

In `test_standard_homework_recon_removes_source_scout_pipeline`, keep this
assertion unchanged:

```python
assert "source_scout_pipeline_used" in policy_text
```

because `background-recon.md` must preserve the review field.

- [ ] **Step 4: Update no-downgrade planner test**

In `tests/test_spec_hard_requirement_policy.py`, change:

```python
text = read("sub-skills/tasks/assignment-workflow-planner.md")
```

to:

```python
text = read("sub-skills/tasks/alignment-planning.md")
```

- [ ] **Step 5: Run the focused tests and confirm they fail for missing new files**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_homework_router_split_policy.py \
  tests/test_pdf_link_annotation_policy.py \
  tests/test_source_body_audit_policy.py \
  tests/test_spec_hard_requirement_policy.py \
  -q
```

Expected: FAIL. The first failures should mention missing
`sub-skills/tasks/background-recon.md`, `sub-skills/tasks/existing-work-recon.md`,
or `sub-skills/tasks/alignment-planning.md`.

- [ ] **Step 6: Commit failing tests**

```bash
git add tests/test_homework_router_split_policy.py tests/test_pdf_link_annotation_policy.py tests/test_source_body_audit_policy.py tests/test_spec_hard_requirement_policy.py
git commit -m "test: require staged homework recon routing"
```

---

### Task 2: Rename Runtime Task Files and Make the Router Progressive-Disclosure Only

**Files:**
- Move: `sub-skills/tasks/assignment-source-intake.md` -> `sub-skills/tasks/background-recon.md`
- Move: `sub-skills/tasks/assignment-workflow-planner.md` -> `sub-skills/tasks/alignment-planning.md`
- Move: `sub-skills/tools/current-state-intake.md` -> `sub-skills/tasks/existing-work-recon.md`
- Modify: `sub-skills/tasks/do-homework.md`

- [ ] **Step 1: Move the three runtime files**

Run:

```bash
git mv sub-skills/tasks/assignment-source-intake.md sub-skills/tasks/background-recon.md
git mv sub-skills/tasks/assignment-workflow-planner.md sub-skills/tasks/alignment-planning.md
git mv sub-skills/tools/current-state-intake.md sub-skills/tasks/existing-work-recon.md
```

- [ ] **Step 2: Update front matter and headings**

In `sub-skills/tasks/background-recon.md`, replace the front matter and H1 with:

```markdown
---
name: background-recon
description: clean-start homework background reconnaissance
---

# Background Recon
```

In `sub-skills/tasks/existing-work-recon.md`, replace the front matter and H1 with:

```markdown
---
name: existing-work-recon
description: retained draft, repair, review, and continue state reconnaissance
---

# Existing Work Recon
```

In `sub-skills/tasks/alignment-planning.md`, replace the front matter and H1 with:

```markdown
---
name: alignment-planning
description: homework user alignment, brainstorming, and pipeline planning
---

# Alignment Planning
```

- [ ] **Step 3: Replace `do-homework.md` route disclosure**

In `sub-skills/tasks/do-homework.md`, replace the initial route list with:

```markdown
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
```

- [ ] **Step 4: Replace the startup inventory route enum**

In `sub-skills/tasks/do-homework.md`, update the JSON route field to:

```json
  "route": "background-recon.md | existing-work-recon.md",
```

- [ ] **Step 5: Replace the route table**

In `sub-skills/tasks/do-homework.md`, replace the current route table with:

```markdown
## Route Table

| Input state | Entry preset | First-stage route |
|---|---|---|
| `recommended_action: recon` | `clean_start` | Read `sub-skills/tasks/background-recon.md`. |
| `recommended_action: review_or_execute` or `pipeline_ready` | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`; do not rerun source recon. |
| `recommended_action: review_or_submit` or `draft_ready` | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`; do not clean-start by default. |
| `recommended_action: continue` or failed/interrupted work | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`; run clean-start source recon only if that stage reports missing/stale source evidence as a blocker and the router accepts a new route. |
| Direct retained draft, prior output, feedback, repair, package, or verification request | `retained_artifact_start` | Read `sub-skills/tasks/existing-work-recon.md`. |
```

- [ ] **Step 6: Replace the router handoff section**

In `sub-skills/tasks/do-homework.md`, replace `## Handoff` with:

```markdown
## Handoff

After route selection, read only the first-stage route named in the route table.
Do not preload, inspect, or name later-stage task files from this router. The
first-stage task owns the next handoff after it writes its terminal artifacts.
```

- [ ] **Step 7: Remove forbidden later-stage names from the router**

Run:

```bash
rg -n "alignment-planning|task-orchestrator|assignment-workflow-planner|assignment-source-intake|current-state-intake|assignment-recon" sub-skills/tasks/do-homework.md
```

Expected: no output.

- [ ] **Step 8: Run the staged router test**

Run:

```bash
.venv/bin/python -m pytest tests/test_homework_router_split_policy.py -q
```

Expected: still FAIL because `background-recon.md` does not yet contain the
folded `assignment-recon.md` contract and old references remain in moved files.

- [ ] **Step 9: Commit the file moves and router disclosure change**

```bash
git add -A sub-skills/tasks sub-skills/tools/current-state-intake.md
git commit -m "docs: route homework to staged recon tasks"
```

---

### Task 3: Fold `assignment-recon.md` Into `background-recon.md` and Retire the Tool Entry

**Files:**
- Modify: `sub-skills/tasks/background-recon.md`
- Delete: `sub-skills/tools/assignment-recon.md`
- Modify: `sub-skills/tools/_index.md`

- [ ] **Step 1: Insert the assignment recon production contract into `background-recon.md`**

Open `sub-skills/tools/assignment-recon.md` and copy its production sections
into `sub-skills/tasks/background-recon.md` under the existing clean-start
runtime checklist, before the detailed `[A]` flow.

Preserve these exact headings or phrases in `background-recon.md`:

```markdown
## Canvas Evidence Recon Contract

Runtime invariants:

- Keep Stage 1 broad: inspect all likely Canvas source surfaces before deciding
  the main spec, including assignment, rubric, syllabus, modules, pages, file
  metadata, assignment files, and announcements.
- Always dispatch `reference_collector` after Stage 1. The collector preserves
  complete original task-relevant evidence under `references/`; it does not
  interpret the assignment or write terminal reconnaissance artifacts.
- Treat `canvas/syllabus.json` as a first-class Canvas source: fetch it, read it,
  and record whether it contains assignment requirements, grading criteria,
  submission policy, late policy, academic-integrity rules, AI/tool policy, or
  other course-level constraints.
```

Keep the existing `Stage 1 - fetch-context` commands, the announcements error
contract, the module/page/file fetch guidance, the reference preservation
contract, the `reference_collector` review fields, and the
`### PDF Link Annotation Extraction` section.

- [ ] **Step 2: Remove internal references to `assignment-recon.md` from `background-recon.md`**

Replace any sentence that says to invoke or fetch through `assignment-recon.md`
with this wording:

```markdown
Fetch raw Canvas snapshots through the Canvas Evidence Recon Contract in this
file.
```

Run:

```bash
rg -n "assignment-recon.md|assignment_recon" sub-skills/tasks/background-recon.md
```

Expected: no output.

- [ ] **Step 3: Add the tail handoff in `background-recon.md`**

At the end of `sub-skills/tasks/background-recon.md`, add this exact section:

```markdown
## Tail Handoff

If background recon completed successfully and all terminal artifacts are
written, continue by reading:

```text
sub-skills/tasks/alignment-planning.md
```

Do not execute draft stages from this file. Alignment, user-owned decisions,
pipeline design, and pipeline review belong to the next stage.
```

- [ ] **Step 4: Delete `sub-skills/tools/assignment-recon.md`**

Run:

```bash
git rm sub-skills/tools/assignment-recon.md
```

- [ ] **Step 5: Remove recon/current-state rows from `sub-skills/tools/_index.md`**

In `sub-skills/tools/_index.md`, remove these tool rows:

```markdown
| **assignment-recon** | [assignment-recon.md](./assignment-recon.md) | Canvas Generic Stage 1-5 reconnaissance → spec.md + rubric + references | course_id, assignment_id, work_dir | spec.md, investigation/, references/, problem.md |
| **current-state-intake** | [current-state-intake.md](./current-state-intake.md) | Retained-artifact current-state intake -> explore context + repair recon | work_dir, current_request | investigation/explore_manifest.json, investigation/explore_context.md, optional investigation/repair_recon.md, optional repair_request.md |
```

Replace:

```markdown
see `sub-skills/tasks/assignment-workflow-planner.md [C]`.
```

with:

```markdown
see `sub-skills/tasks/alignment-planning.md [C]`.
```

Replace the retained-artifact loading note:

```markdown
> For retained-artifact requests, load `current-state-intake` before repair or
> continuation planning.
```

with:

```markdown
> Retained-artifact reconnaissance is a routed task stage, not a tool registry
> entry. Start from `sub-skills/tasks/do-homework.md`.
```

Remove these capability vocabulary rows:

```markdown
| `assignment_recon` | Canvas reconnaissance → spec.md |
| `current_state_intake` | Retained-artifact current state -> explore context |
```

- [ ] **Step 6: Run focused source recon tests**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_homework_router_split_policy.py \
  tests/test_pdf_link_annotation_policy.py \
  tests/test_source_body_audit_policy.py \
  -q
```

Expected: some tests may still FAIL due old references in `existing-work-recon.md`,
`alignment-planning.md`, `skill.md`, or `docs/runtime-agent-protocol.md`.

- [ ] **Step 7: Commit the background recon merge**

```bash
git add -A sub-skills/tasks/background-recon.md sub-skills/tools/assignment-recon.md sub-skills/tools/_index.md
git commit -m "docs: fold assignment recon into background recon"
```

---

### Task 4: Convert `existing-work-recon.md` Into the Retained First-Stage Task

**Files:**
- Modify: `sub-skills/tasks/existing-work-recon.md`
- Modify: `sub-skills/tasks/alignment-planning.md`

- [ ] **Step 1: Update the entry language in `existing-work-recon.md`**

At the top of `sub-skills/tasks/existing-work-recon.md`, replace old tool
language with:

```markdown
Use this task only for retained drafts, existing outputs, repair requests,
pipeline review, draft review, failed runs, and continue flows after
`sub-skills/tasks/do-homework.md` accepts the startup inventory.

This is a first-stage routed homework task. It is not a tool registry entry and
it must not run clean-start Canvas/source reconnaissance.
```

- [ ] **Step 2: Replace any old planner/tool path references**

In `sub-skills/tasks/existing-work-recon.md`, make these substitutions:

```text
sub-skills/tasks/assignment-workflow-planner.md -> sub-skills/tasks/alignment-planning.md
assignment-workflow-planner.md -> alignment-planning.md
../tools/current-state-intake.md -> sub-skills/tasks/existing-work-recon.md
current-state-intake.md -> existing-work-recon.md
```

- [ ] **Step 3: Add the tail handoff in `existing-work-recon.md`**

At the end of `sub-skills/tasks/existing-work-recon.md`, add:

```markdown
## Tail Handoff

If existing work recon completed successfully and the terminal current-state
artifacts are written, continue by reading:

```text
sub-skills/tasks/alignment-planning.md
```

Do not run clean-start Canvas/source recon from this file. If source evidence is
missing or stale, report that blocker in `investigation/explore_context.md` or
`stage_reviews/process_concerns.jsonl` and return to the router.
```

- [ ] **Step 4: Update retained entry language in `alignment-planning.md`**

In `sub-skills/tasks/alignment-planning.md`, replace old retained-current-state
section text that says:

```markdown
For retained artifacts, first read:

```text
../tools/current-state-intake.md
```
```

with:

```markdown
For retained artifacts, this planner must arrive after
`sub-skills/tasks/existing-work-recon.md` has written terminal current-state
artifacts. Do not invoke retained-state recon from this planner. If required
current-state artifacts are missing, stop and return to the router or the
first-stage recon task.
```

- [ ] **Step 5: Add explicit first-stage refusal language in `alignment-planning.md`**

Near the top of `sub-skills/tasks/alignment-planning.md`, add:

```markdown
This stage does not run `background-recon.md` and does not run
`existing-work-recon.md`. It reads terminal artifacts from whichever first-stage
task completed. Missing first-stage artifacts are blockers, not permission to
silently perform the first-stage investigation here.
```

- [ ] **Step 6: Run the staged router test**

Run:

```bash
.venv/bin/python -m pytest tests/test_homework_router_split_policy.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit the existing-work stage conversion**

```bash
git add sub-skills/tasks/existing-work-recon.md sub-skills/tasks/alignment-planning.md
git commit -m "docs: make existing work recon a routed task"
```

---

### Task 5: Sync Runtime Docs and Public Skill Architecture

**Files:**
- Modify: `skill.md`
- Modify: `docs/runtime-agent-protocol.md`
- Modify: `docs/canvas-pilot-reference.md`
- Modify: `docs/skills-architecture-spec.md`
- Modify: `docs/progress/agent-progress.md`

- [ ] **Step 1: Update runtime architecture in `skill.md`**

Replace the homework task/tool map with:

```text
skill.md
├── sub-skills/tasks/
│   ├── sync-status.md          # Canvas snapshot -> assistant plan
│   ├── do-homework.md          # Router / preflight / first-stage route selection
│   ├── background-recon.md     # Clean-start homework background recon
│   ├── existing-work-recon.md  # Retained draft / repair / continue recon
│   ├── alignment-planning.md   # User alignment, brainstorm, pipeline planning
│   ├── task-orchestrator.md    # Stage execution/review from approved execution plan
│   ├── sync-course.md          # Persistent course material archive
│   └── write-course-notes.md   # Notes from synced lecture PDFs
├── sub-skills/tools/
│   ├── canvascli-setup.md
│   ├── canvascli-api.md
│   ├── _index.md
│   ├── code-writer.md
│   ├── writing-helper.md
│   ├── pdf-renderer.md
│   ├── slide-maker.md
│   └── ...
└── data/                       # Local snapshots, plans, workbenches, drafts
```

Replace the runtime homework file map with:

```text
do-homework.md = router/preflight/first-stage route selection
background-recon.md = clean-start task background recon
existing-work-recon.md = retained/repair/continue current work recon
alignment-planning.md = user alignment, brainstorming, pipeline planning
```

- [ ] **Step 2: Update `docs/runtime-agent-protocol.md`**

Replace old runtime map text:

```text
assignment-source-intake.md = clean-start source/spec intake
assignment-workflow-planner.md = alignment/planning/retained planner
current-state-intake.md = retained current-state exploration tool
```

with:

```text
background-recon.md = clean-start task background recon
existing-work-recon.md = retained/repair/continue current work recon
alignment-planning.md = shared user alignment, brainstorming, and pipeline planning
```

Add this progressive-disclosure rule near the homework routing section:

```markdown
`do-homework.md` names only the first-stage task for the accepted route. It must
not name `alignment-planning.md`; alignment is revealed only by the tail handoff
inside `background-recon.md` or `existing-work-recon.md`.
```

- [ ] **Step 3: Update old file names across docs**

Run:

```bash
rg -n "assignment-source-intake|assignment-workflow-planner|current-state-intake|assignment-recon" skill.md docs sub-skills tests
```

For runtime docs and tests, replace old names with:

```text
assignment-source-intake.md -> background-recon.md
assignment-workflow-planner.md -> alignment-planning.md
current-state-intake.md -> existing-work-recon.md
assignment-recon.md -> background-recon.md
```

For historical specs/plans under `docs/superpowers/specs/` and
`docs/superpowers/plans/`, do not rewrite old design history wholesale. Add a
short note at the top of the 2026-06-15 split spec and plan:

```markdown
> Historical note: this file records the first router split. The active staged
> routing refinement is `docs/superpowers/specs/2026-06-16-homework-staged-recon-routing-design.md`
> and `docs/superpowers/plans/2026-06-16-homework-staged-recon-routing.md`.
```

- [ ] **Step 4: Add progress note**

Append this paragraph to `docs/progress/agent-progress.md`:

```markdown
### 2026-06-16 - Homework staged recon routing

Refined the homework router split into progressive-disclosure stages:
`do-homework.md` now routes only to `background-recon.md` for clean starts or
`existing-work-recon.md` for retained/repair/continue starts. The shared
`alignment-planning.md` stage is revealed only by the first-stage tail handoff,
so runtime agents do not preload alignment before source or existing-work recon
is complete.
```

- [ ] **Step 5: Run reference scan**

Run:

```bash
rg -n "assignment-source-intake|assignment-workflow-planner|current-state-intake|assignment-recon" skill.md docs/runtime-agent-protocol.md docs/canvas-pilot-reference.md docs/skills-architecture-spec.md docs/progress/agent-progress.md sub-skills tests
```

Expected: no output, except historical notes in archived superpowers specs/plans
when the command is expanded to include `docs/superpowers/`.

- [ ] **Step 6: Run focused docs policy tests**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_source_body_audit_policy.py \
  tests/test_pdf_link_annotation_policy.py \
  tests/test_spec_hard_requirement_policy.py \
  -q
```

Expected: PASS.

- [ ] **Step 7: Commit runtime doc sync**

```bash
git add skill.md docs/runtime-agent-protocol.md docs/canvas-pilot-reference.md docs/skills-architecture-spec.md docs/progress/agent-progress.md docs/superpowers/specs/2026-06-15-homework-router-source-intake-planner-split-design.md docs/superpowers/plans/2026-06-15-homework-router-source-intake-planner-split.md
git commit -m "docs: sync staged homework routing references"
```

---

### Task 6: Full Test Suite and Static Route Audit

**Files:**
- No intended source edits unless tests expose a missed reference or contradiction.

- [ ] **Step 1: Run full tests**

Run:

```bash
.venv/bin/python -m pytest tests -q
```

Expected: all tests PASS.

- [ ] **Step 2: Audit router does not leak later stages**

Run:

```bash
rg -n "alignment-planning|task-orchestrator|assignment-workflow-planner|assignment-source-intake|current-state-intake|assignment-recon" sub-skills/tasks/do-homework.md
```

Expected: no output.

- [ ] **Step 3: Audit first-stage files contain only tail handoff to alignment**

Run:

```bash
rg -n "alignment-planning.md" sub-skills/tasks/background-recon.md sub-skills/tasks/existing-work-recon.md
```

Expected: each first-stage file contains the path only in tail handoff or explicit handoff boundary language.

- [ ] **Step 4: Audit alignment does not run first-stage recon**

Run:

```bash
rg -n "does not run `background-recon.md`|does not run `existing-work-recon.md`|Missing first-stage artifacts are blockers" sub-skills/tasks/alignment-planning.md
```

Expected: all three phrases are present.

- [ ] **Step 5: Fix any missed references with targeted edits**

If a command above fails, edit only the file reported by the failing command.
For example, if `do-homework.md` still contains `alignment-planning.md`, remove
the path and replace the sentence with:

```markdown
Follow the routed first-stage task to completion; that task owns its own tail
handoff.
```

Re-run the failed command until it matches the expected output.

- [ ] **Step 6: Commit any audit fixes**

If Step 5 changed files:

```bash
git add sub-skills docs skill.md tests
git commit -m "docs: tighten staged route audit"
```

If Step 5 changed no files, do not create an empty commit.

---

### Task 7: Validation Run on Homework Flow Slice

**Files:**
- Modify: `docs/verification/2026-06-16/homework-staged-recon-routing.md`
- Runtime may create ignored files under `data/homework/`.

- [ ] **Step 1: Create verification directory**

Run:

```bash
mkdir -p docs/verification/2026-06-16
```

- [ ] **Step 2: Run a clean-start homework validation through A / first alignment handoff**

Use the project’s normal `do-homework` invocation path for a clean-start UCUG1808 proposal-style task. Stop after confirming the first-stage chain reaches the alignment handoff; do not execute draft stages.

The observed runtime read chain must be:

```text
do-homework.md
-> background-recon.md
-> alignment-planning.md
```

The observed router phase must not read or mention `alignment-planning.md` before `background-recon.md` reaches its tail handoff.

- [ ] **Step 3: Write verification report**

Create `docs/verification/2026-06-16/homework-staged-recon-routing.md` with:

```markdown
# Homework Staged Recon Routing Verification

Date: 2026-06-16

## Scope

Validated the progressive-disclosure homework routing contract after the staged
recon refactor.

## Clean-Start Read Chain

Observed:

```text
do-homework.md
-> background-recon.md
-> alignment-planning.md
```

Router disclosure check:

- `do-homework.md` routed to `background-recon.md`.
- `do-homework.md` did not name `alignment-planning.md`.
- `background-recon.md` revealed `alignment-planning.md` only at the tail
  handoff after terminal recon artifacts were ready.

## Commands

```bash
.venv/bin/python -m pytest tests -q
rg -n "alignment-planning|task-orchestrator|assignment-workflow-planner|assignment-source-intake|current-state-intake|assignment-recon" sub-skills/tasks/do-homework.md
```

## Result

The staged routing boundary is acceptable if tests pass, the router leak scan
returns no output, and the observed clean-start read chain matches the sequence
above.
```

If the validation run finds any issue, replace the `## Result` paragraph with
the concrete failure and fix it before committing.

- [ ] **Step 4: Commit verification report**

```bash
git add docs/verification/2026-06-16/homework-staged-recon-routing.md
git commit -m "test: validate staged homework routing"
```

---

### Task 8: Final Review Before Handoff

**Files:**
- No intended edits unless review finds a missed contradiction.

- [ ] **Step 1: Show final branch status**

Run:

```bash
git status --short --branch
```

Expected: clean worktree or only ignored `data/homework/` runtime files.

- [ ] **Step 2: Show commits created by this plan**

Run:

```bash
git log --oneline --decorate -8
```

Expected: one commit per implementation task, with messages matching this plan.

- [ ] **Step 3: Final old-name scan**

Run:

```bash
rg -n "assignment-source-intake|assignment-workflow-planner|current-state-intake|assignment-recon" skill.md docs/runtime-agent-protocol.md docs/canvas-pilot-reference.md docs/skills-architecture-spec.md sub-skills tests
```

Expected: no output.

- [ ] **Step 4: Final test run**

Run:

```bash
.venv/bin/python -m pytest tests -q
```

Expected: all tests PASS.

- [ ] **Step 5: Report result**

In the final implementation response, report:

```text
Implemented staged homework routing.
Clean-start first stage: background-recon.md.
Retained/repair first stage: existing-work-recon.md.
Shared second stage: alignment-planning.md, revealed only by first-stage tail handoff.
Tests: .venv/bin/python -m pytest tests -q -> PASS.
Validation: docs/verification/2026-06-16/homework-staged-recon-routing.md.
```
