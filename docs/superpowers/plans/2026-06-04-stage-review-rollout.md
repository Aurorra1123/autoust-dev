# Stage Review Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade AutoStudy homework execution so the Main Agent generates stage briefs, dispatches executor/reviewer subagents, records stage receipts, and validates DSAA2011 first, then UCUG1505.

**Architecture:** This is a runtime contract rollout, not a standalone framework. `docs/runtime-agent-protocol.md` remains the canonical protocol; `do-homework.md` becomes the Main Agent coordinator contract; `task-orchestrator.md` becomes the stage brief, dispatch, review, retry, and final verification contract.

**Tech Stack:** Markdown skill files, JSON examples, `python3 -m json.tool`, `rg`, `git diff --check`, real-task validation through AutoStudy workbenches.

**Spec:** `docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md`

---

## File Structure

| Action | File | Responsibility |
|---|---|---|
| Modify | `docs/runtime-agent-protocol.md` | Canonical protocol with final schema details and example links. |
| Modify | `sub-skills/tasks/do-homework.md` | Main Agent coordinator contract for homework tasks. |
| Modify | `sub-skills/tasks/task-orchestrator.md` | Stage coordinator contract for briefs, dispatch, reviews, retries, and verification. |
| Modify | `docs/skills-architecture-spec.md` | Reference stage metadata fields and review order. |
| Create | `docs/examples/runtime/stage_brief-example.md` | Executor stage brief example. |
| Create | `docs/examples/runtime/stage_result-example.json` | Executor receipt example. |
| Create | `docs/examples/runtime/stage_review-example.json` | Reviewer receipt example. |
| Modify | `docs/plans/feature-list.json` | Evidence and status update for M3.5 execution architecture. |
| Modify | `docs/progress/agent-progress.md` | Handoff note with DSAA2011-first, UCUG1505-second validation path. |

## Task 1: Canonical Protocol Schema

**Files:**
- Modify: `docs/runtime-agent-protocol.md`
- Reference: `docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md`

- [ ] **Step 1: Open the protocol and locate schema sections**

Run:

```bash
rg -n "pipeline_design|stage_brief|stage_result|stage_review|Open Design Questions" docs/runtime-agent-protocol.md
```

Expected: matches for all four runtime file interfaces and the open questions section.

- [ ] **Step 2: Update `pipeline_design.md` stage fields**

In `docs/runtime-agent-protocol.md`, under the `pipeline_design.md` section, ensure the stage example includes these fields exactly:

```markdown
### Stage 1 - Notebook Execution
- id: stage_01_notebook
- tool: sub-skills/tools/code-writer.md
- delegate: subagent
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
- quality_criteria:
  - notebook executes from a clean kernel
  - metrics used by later report stages are written to draft/metrics.json
- human_blockers:
  - dataset choice if the spec allows multiple datasets and user has not chosen
```

- [ ] **Step 3: Resolve mandatory stage receipts**

In the open design questions section, replace the question about whether `stage_results/` and `stage_reviews/` are mandatory with this decision:

```markdown
Decision: every stage writes a `stage_results/<stage_id>_result.json` receipt.
Reviewed stages also write `stage_reviews/<stage_id>_spec_review.json`; if
quality review is enabled, they write
`stage_reviews/<stage_id>_quality_review.json`.
```

- [ ] **Step 4: Add example links**

Under "Runtime File Interfaces", add:

```markdown
Concrete examples live in `docs/examples/runtime/`:

- `stage_brief-example.md`
- `stage_result-example.json`
- `stage_review-example.json`
```

- [ ] **Step 5: Verify protocol schema**

Run:

```bash
rg -n "stage_01_notebook|stage_results/<stage_id>_result.json|stage_review-example" docs/runtime-agent-protocol.md
git diff --check docs/runtime-agent-protocol.md
```

Expected: `rg` finds all three strings; `git diff --check` exits 0.

- [ ] **Step 6: Commit**

```bash
git add docs/runtime-agent-protocol.md
git commit -m "docs: finalize runtime stage schema"
```

## Task 2: Align `do-homework.md` With Main Agent Coordination

**Files:**
- Modify: `sub-skills/tasks/do-homework.md`
- Reference: `docs/runtime-agent-protocol.md`

- [ ] **Step 1: Add Main Agent role statement**

After the opening workbench flow diagram, add:

```markdown
`do-homework.md` is written for the Claude Code Main Agent. The Main Agent is
the only runtime actor that talks to the user. Subagents, when used, are
temporary workers dispatched by the Main Agent and receive precise stage briefs.
```

- [ ] **Step 2: Add stage directories to the workbench tree**

In `[A2] Create The Workbench`, replace the target structure with:

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   ├── review_a.json
│   ├── user_notes.md
│   └── user_scope.md
├── pipeline_design.md
├── stage_briefs/
├── stage_results/
├── stage_reviews/
├── draft/
├── verification_checklist.md
├── verification.log
└── result.json
```

- [ ] **Step 3: Upgrade the pipeline format example**

In `[C] Design Pipeline`, replace the stage example with:

```markdown
### Stage 1 - Notebook Execution
- id: stage_01_notebook
- tool: sub-skills/tools/code-writer.md
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
- quality_criteria:
  - notebook executes from a clean kernel
  - no fabricated metrics; report metrics must come from actual notebook output
- human_blockers:
  - dataset choice if the spec allows multiple datasets and user has not chosen

### Stage 2 - Report Draft
- id: stage_02_report
- tool: sub-skills/tools/writing-helper.md
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
```

- [ ] **Step 4: State that `pipeline_design.md` is not handed directly to executors**

Before `[D] Orchestrator Runs`, add:

```markdown
`pipeline_design.md` is the task-level plan for the Main Agent and
task-orchestrator. It is not handed directly to executor subagents. The
orchestrator converts each delegated stage into
`stage_briefs/<stage_id>_executor.md` plus reviewer briefs when review is
enabled.
```

- [ ] **Step 5: Update orchestrator outputs**

In `[D] Orchestrator Runs`, require the orchestrator to write:

```text
stage_briefs/
stage_results/
stage_reviews/
verification_checklist.md
verification.log
```

Also add:

```markdown
Do not mark the draft as ready if reviewed stages lack a passing spec
compliance review. Quality review happens only after spec compliance passes.
```

- [ ] **Step 6: Verify wording**

Run:

```bash
rg -n "Main Agent|stage_briefs|stage_results|stage_reviews|spec compliance|quality review" sub-skills/tasks/do-homework.md
git diff --check sub-skills/tasks/do-homework.md
```

Expected: `rg` finds all six concepts; diff check exits 0.

- [ ] **Step 7: Commit**

```bash
git add sub-skills/tasks/do-homework.md
git commit -m "docs: align do-homework with stage review protocol"
```

## Task 3: Rewrite `task-orchestrator.md` As Stage Coordinator

**Files:**
- Modify: `sub-skills/tasks/task-orchestrator.md`
- Reference: `docs/runtime-agent-protocol.md`

- [ ] **Step 1: Replace the role statement**

Replace the opening paragraph below `# task-orchestrator` with:

```markdown
The core M3.5 execution coordination mechanism. This task is written for the
Claude Code Main Agent. It reads the task-level `pipeline_design.md`, creates
bounded stage briefs, dispatches executor and reviewer subagents when a stage is
delegated, executes simple `delegate: main-agent` stages inline, and aggregates
evidence for final verification.
```

- [ ] **Step 2: Update the required workbench**

Replace the workbench tree with the same tree used in Task 2 Step 2, including:

```text
├── stage_briefs/
├── stage_results/
├── stage_reviews/
```

- [ ] **Step 3: Replace pipeline format sentence**

Replace the sentence listing old fields with:

```markdown
Each stage declares `id`, `tool`, `delegate`, `reads`, `writes`,
`review.spec_compliance`, `review.quality`, `max_retries`,
`quality_criteria`, and `human_blockers`. Stages may also declare `lang`,
`type`, `post-process`, `fallback`, and `min_quality`.
```

- [ ] **Step 4: Replace "Execute Stages" with "Generate Stage Briefs"**

Replace the current Step 3 body with:

```markdown
### Step 3 - Generate Stage Briefs

For each stage in `pipeline_design.md`, write:

```text
stage_briefs/<stage_id>_executor.md
```

For stages with review enabled, also write:

```text
stage_briefs/<stage_id>_spec_review.md
stage_briefs/<stage_id>_quality_review.md
```

Each executor brief must include:

- role: `executor`;
- concrete one-stage task;
- required reads;
- allowed reads;
- forbidden reads;
- declared writes;
- selected tool skill paths;
- measurable quality criteria;
- review criteria;
- context from previous stages;
- blockers and escalation rules.

Do not dispatch a subagent until its stage brief exists.
```

- [ ] **Step 5: Add executor dispatch section**

After the new Step 3, add:

```markdown
### Step 4 - Dispatch Executor Subagent Or Run Inline

If `delegate: subagent`, dispatch one executor subagent with only the executor
stage brief path and a short prompt pointing to it. The executor reports
`DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED` and writes:

```text
stage_results/<stage_id>_result.json
```

If `delegate: main-agent`, the Main Agent executes the simple stage inline but
still writes:

```text
stage_results/<stage_id>_result.json
```
```

- [ ] **Step 6: Add review loop section**

After the executor dispatch section, add:

```markdown
### Step 5 - Review In Order

For stages with review enabled:

1. Dispatch spec compliance reviewer first.
2. Write `stage_reviews/<stage_id>_spec_review.json`.
3. If verdict is `FAIL`, apply reviewer suggestions through a fix brief and
   rerun the executor while retries remain.
4. Dispatch quality reviewer only after spec compliance passes.
5. Write `stage_reviews/<stage_id>_quality_review.json`.

Never run quality review before spec compliance passes.
```

- [ ] **Step 7: Replace final verification section**

Update the final verification section so it requires:

```markdown
- every stage has a `stage_results/<stage_id>_result.json`;
- every reviewed stage has a passing spec compliance review;
- quality review is passing or explicitly skipped with reason;
- `verification.log` contains measured PASS/FAIL/SKIP lines;
- `result.json` is not marked `draft_ready` while blocking FAIL reviews remain.
```

- [ ] **Step 8: Verify orchestrator wording**

Run:

```bash
rg -n "Generate Stage Briefs|Dispatch Executor|Review In Order|stage_results|stage_reviews|Never run quality review" sub-skills/tasks/task-orchestrator.md
git diff --check sub-skills/tasks/task-orchestrator.md
```

Expected: `rg` finds all six concepts; diff check exits 0.

- [ ] **Step 9: Commit**

```bash
git add sub-skills/tasks/task-orchestrator.md
git commit -m "docs: define task orchestrator stage review loop"
```

## Task 4: Align Skills Architecture Reference

**Files:**
- Modify: `docs/skills-architecture-spec.md`
- Reference: `docs/runtime-agent-protocol.md`

- [ ] **Step 1: Add runtime protocol pointer near the top**

Add:

```markdown
Runtime handoff rules live in `docs/runtime-agent-protocol.md`. This file
defines skill structure and pipeline design conventions; the runtime protocol
defines how the Main Agent turns those plans into stage briefs, results,
reviews, and final verification evidence.
```

- [ ] **Step 2: Add stage metadata fields to the pipeline section**

In the pipeline design format section, add:

```markdown
- `id`: stable stage id, e.g. `stage_01_report`
- `delegate`: `main-agent` or `subagent`
- `review.spec_compliance`: true/false
- `review.quality`: true/false
- `max_retries`: retry count before human review
- `quality_criteria`: measurable executor and reviewer checks
- `human_blockers`: user-supplied information required before or after a stage
```

- [ ] **Step 3: Update sub-agent review guidance**

In the sub-agent review section, replace any single-reviewer model with:

```markdown
When review is enabled, the Main Agent runs reviews in order:

1. Spec compliance review: compare artifact against `spec.md`, rubric, user
   notes, and the stage brief.
2. Quality review: check artifact-specific quality only after spec compliance
   passes.

Review outputs are written under `stage_reviews/`.
```

- [ ] **Step 4: Verify architecture references**

Run:

```bash
rg -n "runtime-agent-protocol|delegate|stage_briefs|spec compliance|quality review|stage_reviews" docs/skills-architecture-spec.md
git diff --check docs/skills-architecture-spec.md
```

Expected: `rg` finds all six concepts; diff check exits 0.

- [ ] **Step 5: Commit**

```bash
git add docs/skills-architecture-spec.md
git commit -m "docs: align skills architecture with stage review protocol"
```

## Task 5: Add Runtime Examples

**Files:**
- Create: `docs/examples/runtime/stage_brief-example.md`
- Create: `docs/examples/runtime/stage_result-example.json`
- Create: `docs/examples/runtime/stage_review-example.json`
- Modify: `docs/runtime-agent-protocol.md`

- [ ] **Step 1: Create example directory**

Run:

```bash
mkdir -p docs/examples/runtime
```

Expected: command exits 0.

- [ ] **Step 2: Create stage brief example**

Write `docs/examples/runtime/stage_brief-example.md`:

```markdown
# Stage Brief: stage_02_report - Report Draft

## Role
executor

## Task
Write `draft/report.md` for the assignment using the verified Canvas spec,
rubric, user notes, and metrics generated by previous stages.

## Required Reads
- `spec.md`: assignment facts and deliverables
- `investigation/rubric.md`: grading criteria
- `investigation/user_notes.md`: user preferences and missing context resolved at checkpoint B
- `draft/metrics.json`: measured outputs from the notebook stage
- `sub-skills/tools/writing-helper.md`: prose writing contract
- `sub-skills/tools/writing-helper-report.md`: report structure guidance

## Allowed Reads
- `references/`: source materials discovered during reconnaissance
- `draft/figures/`: generated figures from previous stages

## Forbidden Reads
- `AGENTS.md`
- `docs/ROADMAP.md`
- `docs/COLLABORATION.md`
- `docs/progress/agent-progress.md`
- `docs/plans/feature-list.json`
- `docs/superpowers/`

## Writes
- `draft/report.md`: complete report draft with no unresolved forbidden placeholders
- `stage_results/stage_02_report_result.json`: executor receipt

## Tool Guidance
- `sub-skills/tools/writing-helper.md`
- `sub-skills/tools/writing-helper-report.md`
- `sub-skills/tools/humanizer.md` if `pipeline_design.md` declares `post-process: humanize`

## Quality Criteria
- Covers every rubric criterion in `investigation/rubric.md`
- Contains no `[PROBLEM N]`, `[TODO]`, or `[此处填入...]` placeholder markers
- Grounds every numeric claim in `draft/metrics.json` or a cited source

## Review Criteria
- Spec compliance: all required deliverables and rubric items are addressed
- Quality: writing is coherent, evidence-grounded, and appropriate for the course

## Context From Previous Stages
Stage 1 wrote `draft/metrics.json` with executed notebook metrics. Use those
numbers for result claims instead of inventing metrics.

## Blockers And Escalation
Return `NEEDS_CONTEXT` if a required dataset, partner name, or topic choice is
still missing from the workbench files.
```

- [ ] **Step 3: Create stage result example**

Write `docs/examples/runtime/stage_result-example.json`:

```json
{
  "stage": "stage_02_report",
  "status": "DONE",
  "summary": "Wrote a complete report draft grounded in spec, rubric, user notes, and notebook metrics.",
  "outputs": [
    {"path": "draft/report.md", "size_bytes": 18432}
  ],
  "commands_run": [
    "python3 - <<'PY'\nfrom pathlib import Path\ntext = Path('draft/report.md').read_text()\nprint(len(text.split()))\nPY"
  ],
  "verification_evidence": [
    "draft/report.md exists",
    "no forbidden placeholder markers found",
    "rubric criteria are explicitly addressed"
  ],
  "concerns": []
}
```

- [ ] **Step 4: Create stage review example**

Write `docs/examples/runtime/stage_review-example.json`:

```json
{
  "stage": "stage_02_report",
  "review_type": "spec_compliance",
  "verdict": "PASS",
  "evidence": [
    "draft/report.md addresses all rubric sections listed in investigation/rubric.md",
    "deliverable format matches spec.md requirement: report markdown for PDF rendering"
  ],
  "missing_requirements": [],
  "extra_or_unrequested_work": [],
  "fix_suggestions": []
}
```

- [ ] **Step 5: Validate examples**

Run:

```bash
python3 -m json.tool docs/examples/runtime/stage_result-example.json > /tmp/autoust-stage-result-example.json
python3 -m json.tool docs/examples/runtime/stage_review-example.json > /tmp/autoust-stage-review-example.json
rg -n "stage_brief-example|stage_result-example|stage_review-example" docs/runtime-agent-protocol.md docs/examples/runtime
git diff --check docs/runtime-agent-protocol.md docs/examples/runtime
```

Expected: JSON commands exit 0, `rg` finds all example references, diff check exits 0.

- [ ] **Step 6: Commit**

```bash
git add docs/runtime-agent-protocol.md docs/examples/runtime
git commit -m "docs: add stage review runtime examples"
```

## Task 6: Backlog And Progress Handoff

**Files:**
- Modify: `docs/plans/feature-list.json`
- Modify: `docs/progress/agent-progress.md`
- Modify: `docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md`
- Modify: `docs/superpowers/plans/2026-06-04-stage-review-rollout.md`

- [ ] **Step 1: Add feature-list evidence**

In `M3.5-EXECUTION-ARCHITECTURE.evidence`, add:

```json
"2026-06-04 docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md and docs/superpowers/plans/2026-06-04-stage-review-rollout.md select protocol + reviewer contracts, DSAA2011 first, UCUG1505 second"
```

Set status to `in-progress` after static rollout implementation lands. Keep it
`in-progress` until DSAA2011 validation produces complete stage receipts.

- [ ] **Step 2: Add progress note**

At the top of the `2026-06-04` progress section, add:

```markdown
Stage review rollout design and plan were added:
`docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md` and
`docs/superpowers/plans/2026-06-04-stage-review-rollout.md`. The selected path
is protocol + reviewer contracts, with DSAA2011 as the first draft-only real
task validation and UCUG1505 as the second validation.
```

- [ ] **Step 3: Validate JSON and diffs**

Run:

```bash
python3 -m json.tool docs/plans/feature-list.json > /tmp/autoust-feature-list-json-check.json
git diff --check docs/plans/feature-list.json docs/progress/agent-progress.md docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md docs/superpowers/plans/2026-06-04-stage-review-rollout.md
```

Expected: JSON command exits 0; diff check exits 0.

- [ ] **Step 4: Commit**

```bash
git add docs/plans/feature-list.json docs/progress/agent-progress.md docs/superpowers/specs/2026-06-04-stage-review-rollout-design.md docs/superpowers/plans/2026-06-04-stage-review-rollout.md
git commit -m "docs: plan stage review rollout"
```

## Task 7: Final Static Verification

**Files:**
- Verify all modified files from Tasks 1-6

- [ ] **Step 1: Run static checks**

Run:

```bash
python3 -m json.tool docs/plans/feature-list.json > /tmp/autoust-feature-list-json-check.json
python3 -m json.tool docs/examples/runtime/stage_result-example.json > /tmp/autoust-stage-result-example.json
python3 -m json.tool docs/examples/runtime/stage_review-example.json > /tmp/autoust-stage-review-example.json
rg -n "stage_briefs|stage_results|stage_reviews|spec compliance|quality review" docs/runtime-agent-protocol.md sub-skills/tasks/do-homework.md sub-skills/tasks/task-orchestrator.md docs/skills-architecture-spec.md
git diff --check
```

Expected:

- all JSON checks exit 0;
- `rg` finds stage directories and review-order wording in all runtime docs;
- `git diff --check` exits 0.

- [ ] **Step 2: Review final diff**

Run:

```bash
git diff --stat
git status --short
```

Expected: only planned documentation, examples, backlog, and progress files are changed.

- [ ] **Step 3: Record validation readiness**

Append to `docs/progress/agent-progress.md`:

```markdown
Static rollout verification passed. Next runtime validation should start with
DSAA2011 Machine Learning Project and stop at draft/revision evidence; do not
submit. After DSAA2011 has complete stage receipts and reviews, run UCUG1505 as
the open-ended false-pass resistance check.
```

- [ ] **Step 4: Commit final verification note**

```bash
git add docs/progress/agent-progress.md
git commit -m "docs: record stage review rollout verification"
```

## Task 8: DSAA2011 Draft-Only Runtime Validation

**Files:**
- Runtime workbench under `data/homework/DSAA2011/<assignment>/` (gitignored evidence)
- Modify: `docs/plans/feature-list.json`
- Modify: `docs/progress/agent-progress.md`

- [ ] **Step 1: Locate existing DSAA2011 workbench inputs**

Run:

```bash
find data/homework -maxdepth 4 -type f \( -name spec.md -o -name problem.md \) | sort | rg "DSAA2011|Machine|Learning|Project"
```

Expected: at least one existing DSAA2011 Machine Learning Project workbench has
`spec.md` or `problem.md`. This validation intentionally starts after
reconnaissance; do not rerun Canvas Stage 1-5 unless required inputs are missing.

- [ ] **Step 2: Preflight the reused inputs**

Run from the selected DSAA2011 workbench:

```bash
pwd
test -s spec.md
test -s problem.md || echo "problem.md absent; continue with spec.md as canonical input"
find investigation references canvas -maxdepth 2 -type f 2>/dev/null | sort | head -50
rg -n "rubric|deliverable|submit|deadline|dataset|project|report|notebook" spec.md investigation references canvas 2>/dev/null
```

Expected:

- `spec.md` exists and is non-empty;
- existing reconnaissance artifacts are available enough to generate a fresh
  `pipeline_design.md`;
- any missing assignment-critical fact is recorded as a blocker instead of
  silently filled in.

- [ ] **Step 3: Dispatch runtime validation subagent from pipeline generation**

Dispatch one fresh subagent to simulate a real AutoStudy `do-homework` runtime
from this narrowed entry point. Its brief must say:

```markdown
You are the DSAA2011 runtime validation agent.

Start from the existing DSAA2011 workbench and reused `spec.md`/reconnaissance
artifacts. Do not rerun Canvas reconnaissance unless a required local input is
missing, and if that happens stop with `NEEDS_CONTEXT`.

Delete or archive any stale `pipeline_design.md` for this validation run, then
generate a fresh `pipeline_design.md` from the existing `spec.md` and workbench
evidence. Continue through `sub-skills/tasks/task-orchestrator.md`.

Use the new runtime protocol:
- write `stage_briefs/<stage_id>_executor.md` before dispatching a stage;
- executor stages write `stage_results/<stage_id>_result.json`;
- reviewed stages run spec compliance review first;
- run quality review only after spec compliance passes;
- do not write `draft_ready` while blocking spec compliance failures remain.

Stop at draft/revision evidence. Do not submit to Canvas. Do not ask the user to
approve submission.
```

Expected: the runtime validation subagent reports the workbench path, final
status, created `pipeline_design.md`, stage count, review verdict counts, and
whether it stopped at draft/revision evidence.

- [ ] **Step 4: Verify stage evidence from the workbench**

Run from the DSAA2011 workbench:

```bash
test -s pipeline_design.md
find stage_briefs stage_results stage_reviews -type f | sort
python3 -m json.tool result.json > /tmp/autoust-dsaa2011-result.json
rg -n "PASS|FAIL|SKIP" verification.log
```

Expected:

- `pipeline_design.md` was freshly generated for this validation run;
- at least one executor brief per pipeline stage;
- one result JSON per stage;
- spec review JSON for every reviewed stage;
- quality review JSON only after spec review passes or skip reason is recorded;
- `verification.log` contains measured PASS/FAIL/SKIP lines.

- [ ] **Step 5: Dispatch independent trajectory review subagent**

Dispatch a fresh review-only subagent after the runtime validation subagent
stops. Its brief must say:

```markdown
You are the DSAA2011 runtime trajectory reviewer.

Review whether the runtime validation followed
`docs/runtime-agent-protocol.md`, `sub-skills/tasks/do-homework.md`, and
`sub-skills/tasks/task-orchestrator.md`.

Focus on the trajectory, not assignment quality alone:
- validation started from existing `spec.md`/workbench inputs, not full
  reconnaissance;
- `pipeline_design.md` was newly generated from reused inputs;
- stage briefs existed before executor work;
- executor subagents stayed within stage scope and declared reads/writes;
- stage result receipts exist for every stage;
- spec compliance review ran before quality review;
- quality review did not substitute for spec compliance;
- FAIL verdicts triggered retry/revision/error instead of false `draft_ready`;
- no Canvas submission happened or was requested;
- final `result.json` status matches the evidence.

If subagent transcripts are available, inspect the runtime validation subagent
and its nested executor/reviewer subagents. If transcripts are not available,
audit the file trail under `stage_briefs/`, `stage_results/`,
`stage_reviews/`, `verification.log`, `result.json`, and the runtime
validation summary.
```

Expected: trajectory reviewer returns `PASS`, `PASS_WITH_CONCERNS`, or `FAIL`
with concrete evidence paths and protocol deviations.

- [ ] **Step 6: Record DSAA2011 evidence**

Add evidence to `M3.5-EXECUTION-ARCHITECTURE.evidence` with the workbench path, number of stage briefs, number of result receipts, review verdict counts, and final `result.json.status`.

- [ ] **Step 7: Commit DSAA2011 validation docs**

```bash
git add docs/plans/feature-list.json docs/progress/agent-progress.md
git commit -m "docs: record DSAA2011 stage review validation"
```

## Task 9: UCUG1505 Draft-Only Runtime Validation

**Files:**
- Runtime workbench under `data/homework/UCUG1505/<assignment>/` (gitignored evidence)
- Modify: `docs/plans/feature-list.json`
- Modify: `docs/progress/agent-progress.md`

- [ ] **Step 1: Start UCUG1505 after DSAA2011 evidence exists**

Confirm DSAA2011 produced stage receipts:

```bash
rg -n "DSAA2011.*stage review" docs/plans/feature-list.json docs/progress/agent-progress.md
```

Expected: evidence exists before UCUG1505 validation starts.

- [ ] **Step 2: Run UCUG1505 through the normal homework path**

Use `sync-status` and `do-homework` for UCUG1505 Creative Coding Final Project. Stop at draft review and do not submit.

Expected: the workbench contains `spec.md`, `pipeline_design.md`, `stage_briefs/`, `stage_results/`, `stage_reviews/`, `verification.log`, and `result.json`.

- [ ] **Step 3: Verify false-pass resistance**

Run from the UCUG1505 workbench:

```bash
find stage_briefs stage_results stage_reviews -type f | sort
python3 -m json.tool result.json > /tmp/autoust-ucug1505-result.json
rg -n "video|browser|audio|manual|human|PASS|FAIL|SKIP" verification.log stage_reviews/*.json result.json
```

Expected:

- manual video/demo requirements appear as human blockers or SKIP lines;
- spec review addresses actual project requirements from `spec.md`;
- quality review does not replace spec compliance review;
- `result.json` does not hide unresolved manual requirements.

- [ ] **Step 4: Record UCUG1505 evidence**

Add evidence to `M3.5-EXECUTION-ARCHITECTURE.evidence` with the workbench path, stage count, review verdict counts, manual blockers, and final `result.json.status`.

- [ ] **Step 5: Commit UCUG1505 validation docs**

```bash
git add docs/plans/feature-list.json docs/progress/agent-progress.md
git commit -m "docs: record UCUG1505 stage review validation"
```

## Task 10: True Nested Subagent Isolation Validation

**Files:**
- Runtime workbench under `data/homework/<COURSE>/<assignment>/` or a controlled fixture workbench
- Modify: `docs/plans/feature-list.json`
- Modify: `docs/progress/agent-progress.md`
- Reference: `docs/development-validation-standard.md`
- Reference: `docs/inspectable-subagent-transcript-harness.md`

Task 10 validates this exact role chain:

```text
Main Agent A
  -> runtime coordinator B
      -> execution/review child agents C1, C2, C3...

Main Agent A
  -> mechanically exports B/C transcript evidence by propagated ids
  -> dispatches trajectory review coordinator D
      -> D audits B
      -> D dispatches transcript-auditor child agents E1, E2, E3...
          -> each E audits exactly one C transcript body
```

This is why child id propagation is mandatory. The Main Agent does not need to
discover nested children by search; it needs the coordinator's authoritative
ledger of every child id, including superseded attempts and any child-dispatched
descendants. If a child id is missing from the ledger, the run has a process
failure even if the coordinator's summary describes the child work.

For ordinary `multi_agent_v1.spawn_agent` runs, the propagated id is an agent id,
not a Codex app `read_thread` id. The Main Agent's post-run role is only to
export raw evidence by exact local-session JSONL match under
`.codex/sessions/**/<agent_id>.jsonl`; semantic trajectory review belongs to
the trajectory reviewer and its transcript-auditor children.

Ordinary `spawn_agent` validation action model:

1. B, the runtime coordinator, dispatches ordinary child agents C* with
   `multi_agent_v1.spawn_agent` and records every returned `agent_id` in
   `stage_reviews/child_dispatch_ledger.json`.
   `child_dispatch_ledger.json` is coordinator-owned; runtime children must not
   write it.
2. A, the Main Agent, waits for B to stop, then acts as a mechanical export
   broker. A reads the ledger, finds exactly one local session JSONL file for
   each C id, copies it unchanged into `transcripts/`, and writes
   `transcripts/transcript_inventory.json`. A does not perform semantic
   trajectory review over the child bodies.
3. A dispatches D, the trajectory review coordinator, after transcript export.
   D reads coordinator/process evidence, transcript inventory, and audit indexes,
   then dispatches one auditor child E per runtime child transcript. D may sample
   or inspect anomalous transcript bodies, but D must not replace E's one-child
   transcript-body audits by reading everything itself.
4. Each E audits exactly one C transcript body plus its brief and receipt, then
   writes a transcript-audit receipt. D's final verdict must be supported by
   the E receipts, not by D's receipt-only summary.

The same B/C/A/D/E evidence chain applies to `full_flow` and `repair_flow`.
What changes is the launch contract and the meaning of a
passing result:

- `full_flow`: active generated outputs are removed before launch; B must
  regenerate the assignment from scratch.
- `repair_flow`: current first-draft artifacts are intentionally retained as
  user-visible context; B must write a repair plan and avoid turning the run
  into an undeclared full rerun. The repair may be a narrow patch or a broad
  rewrite. If it creates a versioned output, B records that in the repair plan
  instead of switching to a separate mode.

- [ ] **Step 1: Confirm this is an isolation validation, not another inline fallback run**

Apply `docs/development-validation-standard.md` first. Unless the human
explicitly scopes this as `repair_flow`, run Task 10 as
`full_flow`: archive prior evidence, remove generated workbench outputs from
the active launch directory, show the startup inventory, and stop before
coordinator dispatch for human review. After the startup inventory is accepted,
write `prelaunch_startup_inventory.json` or `prelaunch_startup_inventory.txt`
into the active workbench so the later trajectory reviewer can audit the launch
state from repo evidence.

Read:

```bash
rg -n "Validation harness exception|Subagent Dispatch And Review Loop|inline_fallback" docs/runtime-agent-protocol.md sub-skills/tasks/task-orchestrator.md
```

Expected:

- `docs/runtime-agent-protocol.md` allows a development-only runtime
  coordinator subagent to dispatch child executor/reviewer subagents;
- `task-orchestrator.md` still records `inline_fallback`, but this task must
  not accept `inline_fallback` as passing isolation evidence.
- the launch mode and retained startup files have been declared, and no previous
  iteration receipts, diagnoses, draft artifacts, or generated reconnaissance
  outputs remain in the active workbench for `full_flow`.
- for `repair_flow`, the previous active workbench has been copied to a
  rollback archive first, stale execution/review/transcript evidence has been
  removed from active startup context, and the retained current-draft files are
  explicitly listed in `prelaunch_startup_inventory.json`;
- for `repair_flow`, the simulated user feedback is explicit and becomes the
  repair request. The coordinator should not infer hidden feedback from old
  validation reports or archive contents.
- if the iteration is expected to produce a clean transcript-body `PASS`, the
  dispatch method must be inspectable: either the coordinator exports child
  transcripts directly, or the coordinator preserves stable child ids whose
  local session JSONL can be exported by exact id match, or the run uses the
  inspectable Codex-thread harness in
  `docs/inspectable-subagent-transcript-harness.md`.

- [ ] **Step 2: Dispatch one runtime coordinator subagent**

The Main Agent dispatches exactly one fresh runtime coordinator subagent. The
coordinator simulates a real user's AutoStudy Main Agent session, but it must
also receive a tool surface capable of dispatching child subagents.

If the coordinator's stable agent/thread id is only known after dispatch, the
Main Agent must send a follow-up identity-injection message before the
coordinator writes final evidence. The coordinator must record that id in
`nested_isolation_coordinator_summary.md` and `child_dispatch_ledger.json`; a
generic role label is not sufficient as the only coordinator identity.

The coordinator is simulating the user-facing runtime, not acting as a
developer reading internal design notes. Its primary runtime instructions must
come from:

- `skill.md`;
- `sub-skills/tasks/do-homework.md`;
- `sub-skills/tasks/task-orchestrator.md`;
- the selected workbench files only when the declared iteration mode is
  `repair_flow` and the files were listed in the preflight startup inventory.

Do not give `docs/runtime-agent-protocol.md` to the coordinator as its primary
runtime manual. The Main Agent may use that protocol to construct the
validation harness, and trajectory reviewers may use it as an audit standard,
but the coordinator should experience the same public skill/task surface a real
AutoStudy user-facing agent would load.

Coordinator prompt must include:

```markdown
You are the runtime coordinator subagent for true nested isolation validation.

Declared iteration mode: <full_flow | repair_flow>.

If the declared mode is `full_flow`, simulate a real user asking AutoStudy to do
the assignment from the beginning. Do not read archived prior runs, previous
stage receipts, previous verification logs, previous summaries, or hidden draft
artifacts as startup context. Perform the normal `do-homework` flow from
reconnaissance through draft generation and verification.

If the declared mode is `repair_flow`, simulate a user returning after reviewing
the first draft. Preserve the current draft as the object being repaired, write
`repair_request.md` or `repair_plan.md`, and build a repair pipeline whose
scope is justified by the user's feedback. Do not clear `draft/` or redo full
reconnaissance unless the repair request explicitly requires it. Do not use
archive evidence, old trajectory reviews, old transcripts, or prior diagnostics
as task context. If the requested repair is a broad rewrite or new version,
declare whether you are editing current outputs in place or creating a
versioned output such as `draft_v2/`, and preserve enough provenance to
distinguish the retained draft from the repaired candidate.

You must dispatch separate child subagents for delegated stages:
- one executor subagent per delegated stage;
- one spec compliance reviewer subagent per reviewed stage;
- one quality reviewer subagent only after the matching spec compliance review
  passes.

Do not execute delegated executor/reviewer work inline. If child subagent
dispatch is unavailable, stop with `BLOCKED` and write no `draft_ready` result.

For every child subagent, record its role, agent id or transcript handle, input
brief path, output receipt path, and final status in
`stage_results/<stage_id>_result.json` or
`stage_reviews/<stage_id>_<review_type>_review.json`.

Also write or update `stage_reviews/child_dispatch_ledger.json` with every
dispatch return value before waiting for the child. Include normal children,
superseded attempts, standby/empty attempts, replacement children, and any
descendant child ids if a child was allowed to dispatch another child.

`stage_reviews/child_dispatch_ledger.json` is coordinator-owned state. Child
subagents must never create, append, rewrite, or normalize this ledger. Stage
briefs must list the ledger, other stages' receipts, transcript audit files,
archive evidence, and development-plane docs as forbidden writes unless the
child is explicitly a coordinator. If a child writes to the ledger, preserve the
polluted entry, mark it `rejected_child_side_ledger_write` or
`superseded_not_counted`, dispatch a replacement if the polluted entry would
otherwise be counted, and record a process concern. A clean `PASS` requires no
child-side ledger writes.

The coordinator is the authority for child identity. Record the child agent id
returned by dispatch before waiting for the receipt. If the child receipt omits
`agent_id` but includes `agent_id_source:
"unknown_to_child_at_write_time"` and `identity_authority:
"stage_reviews/child_dispatch_ledger.json"`, add the authoritative dispatch id
to the accepted receipt or identity sidecar and record
`identity_normalized_by_coordinator: true`. If the child receipt omits both the
id and the authority fields, treat normalization as recovery and record a
process concern. If the receipt records an alias id such as `C4`,
`C4-spec-review`, or an `agent_id` that conflicts with the dispatch id, do not
count the child as clean completion; preserve the original value, reconcile the
mismatch, dispatch a replacement child, or stop the stage as `BLOCKED`.

Every child prompt and stage brief must include scope hygiene instructions:
children are subagents with curated runtime context; they must not read external
workflow/plugin skill files, development-plane docs, progress logs, Task 10
plans, archive evidence, prior-run diagnostics, or other unlisted files. Avoid
naming development workflow frameworks in runtime-facing prompts unless the
child truly needs them. If the host platform injects startup/plugin instructions
unrelated to the stage, the child may obey only the minimal stop/skip behavior
needed to continue from the assigned brief and must not use those external
workflow instructions as task context.

Every dispatch ledger entry must include `dispatched_at_utc`,
`recorded_before_wait: true`, and once known `receipt_observed_at_utc` and
`accepted_at_utc` or `superseded_at_utc`. Every stage result and review receipt
must include `created_at_utc` and `completed_at_utc`, plus dependency fields
that prove review order.

If child dispatch fails before returning a stable child id, record the failed
attempt in a coordinator-owned `process_events` array in
`stage_reviews/child_dispatch_ledger.json`, with `event_type:
"spawn_attempt_failed_no_agent_id"`, `stage_id`, `role`, `attempted_at_utc`,
tool error, recovery action, and replacement dispatch index if a retry
succeeds.

When a child receipt is first found and parsed, write
`receipt_observed_at_utc` to that dispatch entry. When the coordinator accepts
the receipt as countable stage evidence, write `accepted_at_utc`. A completed
wait status alone is not enough timestamp evidence for clean PASS.

If the runtime can export full child transcripts, save them under
`transcripts/` and record `transcript_export_path` in each receipt. If full
transcript export is unavailable, record that limitation in the coordinator
summary while preserving stable transcript handles.

If `wait_agent` returns `not_found`, stream disconnect, timeout after dispatch,
or another transport-layer error, do not accept the child from the final message
alone. You may mark a child `accepted_with_transport_recovery` only if the
expected receipt exists, parses as strict JSON, the child transcript or local
session JSONL exists, the transcript contains the assignment prompt, and the
receipt/transcript supports the claimed final status. Record `transport_error`,
`recovery_evidence`, `receipt_observed_at_utc`, and `accepted_at_utc`. If any
of these checks fail, re-prompt, dispatch a replacement child, or stop the stage
as `BLOCKED`. A clean `PASS` requires no transport recovery entries.

Transcript export must happen in the direct parent coordinator before child
agents are closed whenever that coordinator has a read/export-thread tool. Do
not omit child ids merely because the direct parent cannot export transcripts.
When direct-parent export is unavailable, the Main Agent will use the ledger ids
for post-run local-session JSONL export. Write exported transcripts under:

```text
transcripts/<stage_id>_<role>_<agent_id>.jsonl
```

and set `transcript_export_path` in the child receipt and dispatch ledger.

Record the coordinator's own stable agent id or transcript handle in
`nested_isolation_coordinator_summary.md`; do not use "current thread" alone as
the only coordinator identity.

Record the accepted `prelaunch_startup_inventory.*` path in the coordinator
summary. For `full_flow`, that inventory is part of the isolation evidence. For
`repair_flow`, it is also the contract that defines which existing files are
legitimate startup context.

Treat `Standing by`, empty final messages, and receipt-less child responses as
non-completion. Re-send the brief, dispatch a replacement child and record the
superseded attempt, or stop as `BLOCKED`; do not count standby/empty output as
passing evidence.
```

- [ ] **Step 3: Require distinct child subagent evidence**

After the coordinator run, verify from the workbench:

```bash
python3 - <<'PY'
from pathlib import Path
import json

root = Path("data/homework/<COURSE>/<assignment>")
agent_roles = []

for path in sorted((root / "stage_results").glob("*.json")):
    data = json.loads(path.read_text())
    agent_roles.append((path.as_posix(), data.get("executed_by"), data.get("agent_id"), data.get("transcript")))

for path in sorted((root / "stage_reviews").glob("*.json")):
    data = json.loads(path.read_text())
    agent_roles.append((path.as_posix(), data.get("review_type"), data.get("agent_id"), data.get("transcript")))

print(agent_roles)

missing = [item for item in agent_roles if not item[2] and not item[3]]
if missing:
    raise SystemExit(f"missing child agent evidence: {missing}")
PY
```

Expected:

- executor receipts identify executor child subagents;
- spec review receipts identify spec reviewer child subagents;
- quality review receipts identify quality reviewer child subagents or an
  explicit `SKIP` receipt after failed spec compliance;
- child agent ids/transcripts are not all the same actor;
- no delegated stage uses `delegation_mode: "inline_fallback"` for a passing
  isolation claim.
- standby-only, empty, or receipt-less child responses are either remediated or
  recorded as non-passing anomalies;
- coordinator identity is stable enough for another agent to audit.
- child `agent_id` values in receipts match the coordinator's authoritative
  dispatch records, or use the explicit `agent_id: null` plus
  `identity_authority` pattern before coordinator normalization; alias ids such
  as `C4` are schema drift and block clean PASS.
- no child wrote to `stage_reviews/child_dispatch_ledger.json` or other
  coordinator-owned ledger/audit files.
- no child relied on development-plane docs, archive evidence, prior-run
  diagnostics, or external workflow/plugin skill context as task evidence. The
  read model is blacklist-first: current-run artifacts directly relevant to the
  assigned stage or reviewed deliverable may be inspected even when the brief
  does not enumerate every generated file. If an unavoidable platform startup
  read occurred, auditors should verify it was not used as task context rather
  than treating the read itself as a blocker.
- ledger and receipt timestamps prove dispatch, receipt observation, acceptance,
  and spec-review-before-quality-review ordering.
- transport recovery entries are absent for clean PASS; if present, they are
  justified by receipt plus transcript evidence and cap the verdict at
  `PASS_WITH_CONCERNS`.
- blocking `auto_fixable` issues are not left as final
  `PASS_WITH_CONCERNS`/`revision_needed` items; the coordinator either fixes
  them through a repair stage and reruns review, or records why the issue was
  misclassified and is not actually auto-fixable.
- conditional repair/verification stages whose trigger is false write
  `status: "SKIPPED"` stage result receipts with `skip_reason`, plus explicit
  review `SKIP` receipts when review files were declared.

- [ ] **Step 4: Dispatch independent trajectory review subagent with transcript auditors**

Dispatch a fresh review-only trajectory reviewer subagent after the coordinator
stops. The trajectory reviewer may use `docs/runtime-agent-protocol.md`,
`sub-skills/tasks/do-homework.md`, `sub-skills/tasks/task-orchestrator.md`, Task
10, and all preserved workbench evidence as its audit standard.

The trajectory reviewer must not rely only on receipt JSON when full child
transcripts are available. It must first build a transcript-audit inventory:

- coordinator transcript or stable coordinator handle;
- every executor child transcript/export path;
- every spec reviewer child transcript/export path;
- every quality reviewer child transcript/export path, or explicit SKIP receipt;
- any superseded/retried child attempts, including standby/empty-message
  anomalies.

Transcript collection is two-level:

1. Prefer direct-parent coordinator exports under `transcripts/`.
2. If the coordinator lacked a read/export-thread tool and receipts have
   `transcript_export_path: null`, the Main Agent must attempt a post-run
   collector fallback using each stable child id/transcript handle from
   `child_dispatch_ledger.json`. For ordinary `multi_agent_v1.spawn_agent`
   children, this means exact local-session JSONL export from
   `.codex/sessions/**/<agent_id>.jsonl`. For inspectable Codex-thread children,
   this means `read_thread(threadId=<child_thread_id>, includeOutputs=true)`
   with pagination.

When fallback succeeds, save the transcript bodies under:

```text
transcripts/<stage_id>_<role>_<agent_id>.jsonl
```

and use those files as the available child transcripts for transcript-auditor
dispatch. For Codex-thread `read_thread` exports, the collector must use cursor
pagination; a one-page read is not enough because it may capture only the
final/finalize turns. For ordinary `spawn_agent` local-session exports, record
the exact session JSONL path, line count, and checks for initial prompt/final
answer. Do not report `NO_FULL_CHILD_TRANSCRIPT_EXPORTS_AVAILABLE` until
direct-parent export, Codex-thread `read_thread` where applicable, and
local-session exact-match export have been attempted and failed.

If fallback fails, write `transcripts/transcript_inventory.json` before the
trajectory verdict. The inventory must list every ledger child id, role, receipt
path, and collector status. Prefer per-child read/list attempts. If the thread
tool rejects the id class before any child can be read, try the local-session
JSONL exact-match export before declaring the child unavailable. Document the
sampled ids, exact tool errors, local-session search paths, and explicit
short-circuit reason for applying `not_exported` to the remaining children.

Then it must dispatch parallel transcript-auditor subagents: exactly one fresh
auditor for each available child subagent transcript. Each auditor receives only
one child transcript plus that child's brief and receipt, and writes a receipt
under:

```text
stage_reviews/transcript_audits/<stage_id>_<role>_transcript_audit.json
```

Each transcript-audit receipt must include:

- `audited_child_agent_id`;
- `audited_child_transcript`;
- `brief_path`;
- `receipt_path`;
- `verdict`: `PASS`, `PASS_WITH_CONCERNS`, `FAIL`, or `BLOCKED`;
- `role_scope_findings`: whether the child stayed within executor,
  spec-reviewer, or quality-reviewer scope;
- `instruction_adherence_findings`: whether the child followed the provided
  skill/task/stage brief instructions;
- `evidence_match_findings`: whether the transcript actually supports the JSON
  receipt;
- `forbidden_action_findings`: Canvas submission attempts, inline fallback,
  reviewer work inside executor, quality review before spec PASS, or other
  role leakage;
- `concerns` and `fix_suggestions`;
- `evidence_limitations`: array of strings. Use an empty array when none are
  known; do not write a scalar string.
- `timestamp_findings`: whether the audited receipt and ledger entry include
  `created_at_utc`, `completed_at_utc`, `dispatched_at_utc`,
  `receipt_observed_at_utc`, and acceptance/supersession timestamps where
  applicable.
- `forbidden_write_findings`: whether the child wrote only allowed outputs and
  did not modify `child_dispatch_ledger.json`, other stages' receipts, or
  trajectory-audit files.
- `transport_recovery_findings`: if the ledger status is
  `accepted_with_transport_recovery`, whether receipt plus transcript evidence
  justifies that status.

Each transcript auditor must first derive the audited child's instruction
contract from:

- the child's initial prompt or dispatch request;
- the assigned stage brief;
- required reads and required tool docs referenced by the prompt/brief;
- receipt or trace schema requirements;
- role/stage boundary;
- allowed reads and writes;
- forbidden reads, forbidden actions, and out-of-scope work;
- forbidden writes, especially coordinator-owned ledgers, other child receipts,
  transcript inventories, trajectory audit files, and archive evidence;
- finalization, pause, or receipt protocol.

Then the auditor checks the transcript against that derived contract. Generic
fallback checks still apply: forbidden Canvas submission or hidden-context use,
role bleed across executor/spec-reviewer/quality-reviewer/repair work,
unsupported receipt claims, widened repair scope, and unexplained evidence
limitations such as truncated outputs, missing files, or unavailable sidecars.

If full child transcript export is unavailable, the trajectory reviewer must say
so explicitly and record which collector levels were attempted. The run may
still pass receipt-level isolation, but the final verdict must be no stronger
than `PASS_WITH_CONCERNS`, and the missing full transcript audit must be
recorded as an evidence limitation. If either collector level succeeds but the
transcripts are not preserved, return `FAIL`.

Trajectory reviewer brief must say:

```markdown
You are the nested isolation trajectory reviewer.

Audit whether the runtime coordinator actually dispatched separate child
executor, spec reviewer, and quality reviewer subagents. Inline fallback does
not count as passing evidence for this task.

Check:
- coordinator transcript or summary;
- child agent ids/transcript handles;
- coordinator dispatch records and receipt identity fields, checking that child
  `agent_id` values do not contradict the coordinator's authoritative dispatch
  ids;
- full child transcript exports when available;
- transcript collector fallback attempts from ledger child ids when direct
  coordinator exports are unavailable;
- `transcripts/transcript_inventory.json`, including per-child collector status
  or a documented invalid-id short-circuit rule;
- transcript-audit receipts under `stage_reviews/transcript_audits/`;
- `stage_briefs/`;
- `stage_results/`;
- `stage_reviews/`;
- `verification.log`;
- `result.json`.
- issue classifications in review receipts and final result: `auto_fixable`,
  `needs_user_input`, `manual_only`, `external_blocker`, and
  `acceptable_risk`.

Before returning your final verdict, dispatch one transcript-auditor subagent
per available child transcript. Use those audit receipts to verify that each
child's full conversation stayed within role, followed the brief, and supports
the written receipt.

Do not collapse this into a single receipt-level review. The Main Agent should
have exported the runtime coordinator transcript and every readable child
transcript before dispatching you. Your job is to review the coordinator
trajectory and to delegate one child-transcript audit per exported runtime child
transcript.

Do not default to reading every child transcript body yourself. Your primary
inputs are the coordinator/process evidence, dispatch ledger, transcript
inventory, stage artifacts, and E audit receipts. You may inspect child
transcript bodies for sampling, anomalies, contradictions, or high-risk stages,
but the one-child transcript-body verdict belongs to E.

Your coordinator-level checks include:
- declared iteration mode and whether the coordinator followed that mode's
  launch/context contract. For `full_flow`, check clean startup/no-leak and
  from-scratch generation. For `repair_flow`, check retained files, explicit
  user-visible context, repair scope, and whether the coordinator avoided
  turning the run into an undeclared full rerun. If the repair created a new
  version, check versioning/provenance and whether the coordinator avoided
  mixing old and repaired artifacts incoherently;
- coordinator identity and child identity consistency;
- child receipt identity source quality: exact id or explicit
  null-plus-authority fields are acceptable, alias ids are not clean evidence;
- ledger coverage for normal, superseded, standby, replacement, repair, and
  skipped attempts;
- ledger single-writer discipline: child-side writes to coordinator-owned
  ledgers are process failures unless rejected and replaced;
- transport recovery discipline: `accepted_with_transport_recovery` requires
  receipt plus transcript evidence and prevents clean PASS;
- receipt and ledger timestamp coverage, including `created_at_utc`,
  `completed_at_utc`, `dispatched_at_utc`, `receipt_observed_at_utc`, and
  acceptance/supersession timestamps;
- scope hygiene: runtime children must not rely on external workflow/plugin
  skills, development docs, prior validation plans, progress logs, or
  archive/prior-run evidence as task evidence. Current-run artifacts directly
  relevant to the assigned stage or reviewed deliverable are in scope unless
  the brief explicitly forbids them; platform-mandated startup reads with no
  task influence should be recorded as environment limitations rather than
  clean-PASS blockers;
- transcript inventory coverage and export provenance;
- one E audit receipt per available child transcript;
- blocking `auto_fixable` repair-before-handoff behavior;
- spec-review-before-quality-review ordering;
- explicit `SKIPPED` receipts for false-trigger conditional stages;
- artifact workflow concerns from this run, using the task's actual deliverable
  contract rather than DSAA2011-only assumptions;
- for `repair_flow`, whether the user feedback was translated into a repair
  request and repair pipeline, whether only justified artifacts were modified,
  whether the repaired draft still passes prior artifact gates, and whether the
  final result clearly distinguishes repaired files from archived rollback
  evidence;
- final verdict support from E receipts and coordinator-level evidence.

Also verify the repair-before-handoff rule. Any blocking issue classified as
`auto_fixable` must have triggered a fix executor or repair stage before final
handoff. Do not accept a final `revision_needed` whose only blockers are
auto-fixable artifacts such as stale package contents, missing generated
headings, or derived files that can be regenerated from local inputs.

Return PASS only if executor/reviewer work was performed by distinct child
subagents, transcript-body audits are available and passing, no important
process concerns remain, no transport recovery was needed, no child-side ledger
writes occurred, child identity fields are exact or explicit null-plus-authority
with coordinator-authoritative ledger support, timestamps prove review ordering,
and runtime children avoided forbidden reads/writes while keeping extra reads
directly tied to current-run stage evidence. Unavoidable platform-startup/plugin
reads do not block PASS when transcripts show they did not influence task
execution. A platform-required `using-superpowers` startup check is environment
noise, not avoidable external workflow-skill use, when the child only performs
startup/skip behavior and then grounds all task work in the assigned brief and
active assignment artifacts. Return PASS_WITH_CONCERNS if artifact gates and
transcript-body audits pass but minor/moderate process concerns remain,
including justified transport recovery, avoidable external workflow-skill use,
frequent identity normalization caused by missing identity injection where
available, or timestamp gaps. Return FAIL if the run used inline fallback,
receipt evidence is not supported by transcript audits, transcripts should have
been preserved but were not, child identity evidence is missing or
contradictory, a child-side ledger write was counted as authoritative,
unsupported transport recovery was accepted, prior validation/archive evidence
leaked into runtime work, or a blocking auto-fixable issue was carried into
final handoff without a repair attempt. Return BLOCKED if the environment does
not expose child subagent dispatch.
```

- [ ] **Step 5: Record isolation evidence**

Add evidence to `M3.5-EXECUTION-ARCHITECTURE.evidence` with:

- workbench path;
- declared iteration mode and startup inventory;
- coordinator agent id/transcript;
- executor child agent ids/transcripts;
- spec reviewer child agent ids/transcripts;
- quality reviewer child agent ids/transcripts or SKIP receipts;
- transcript export paths, or an explicit note that transcript-body evidence was
  unavailable;
- whether transcript export was attempted by the direct parent coordinator, and
  if not, which runtime tool was missing;
- transcript-audit receipt paths and verdicts for every child transcript that
  was available;
- standby/empty child-agent anomalies and how they were handled;
- auto-fixable issues found, repair executor/repair-stage receipts, and
  post-repair review verdicts;
- conditional stage skip receipts and review SKIP receipts, when stage triggers
  are false;
- final trajectory reviewer verdict.

Only after this evidence exists may `M3.5-EXECUTION-ARCHITECTURE.status` move
from `in-progress` to `passing`.

## Task 11: Repair Flow Nested Validation

**Files:**
- Runtime workbench under `data/homework/<COURSE>/<assignment>/`
- Modify: `docs/plans/feature-list.json`
- Modify: `docs/progress/agent-progress.md`
- Reference: `docs/development-validation-standard.md`
- Reference: Task 10 above for the B/C/A/D/E transcript evidence chain

Task 11 validates that AutoStudy can handle a user returning after a first
draft and asking for repair. It is not a full rerun and should not be judged by
the `full_flow` clean-start rule. The repair size is not pre-classified: the
coordinator must derive the scope from user feedback and express it in
`repair_plan.md` plus `repair_pipeline_design.md`. A repair may be a small
patch, regenerated artifact, rerun experiment, rewritten section, or broad
versioned change.

Repair-flow role chain:

```text
Main Agent A
  -> archives current active workbench as rollback evidence
  -> keeps explicit current-draft files active as user-visible context
  -> dispatches runtime repair coordinator B
      -> B writes repair_request.md / repair_plan.md
      -> B dispatches repair executor/reviewer child agents C*

Main Agent A
  -> mechanically exports B/C transcript evidence
  -> dispatches trajectory review coordinator D
      -> D audits repair scope and dispatches E transcript auditors
          -> each E audits exactly one C transcript body
```

Suggested first validation target: use the current DSAA2011 full-flow draft and
simulate this user feedback:

```text
The first draft is complete, but the report is too short and the experiment
discussion is not deep enough. Based on the current draft, improve the report
toward a stronger 8-9 page submission, deepen the experiment/result discussion,
add or refine notebook analysis only where it supports the improved report, then
update slides, render provenance, and the final zip. Do not submit to Canvas and
do not redo the whole assignment from scratch.
```

- [ ] **Step 1: Prepare repair startup state**

Apply `docs/development-validation-standard.md` with
`declared_mode: repair_flow`.

Before dispatching B:

1. Copy the whole active first-draft workbench to
   `archive/<iteration-id>-repair-rollback/`.
2. Remove stale process evidence from active startup context:
   `stage_briefs/`, `stage_results/`, `stage_reviews/`, `transcripts/`,
   old `verification.log`, old `verification_checklist.md`, old `result.json`,
   old `repair_plan.md`, old `repair_pipeline_design.md`, old coordinator
   identity sidecars, old trajectory reviewer identity sidecars, old coordinator
   summaries, and old trajectory reviews.
3. Keep user-visible first-draft context in active workbench, normally:
   `canvas/`, `references/`, `spec.md`, `problem.md`, `draft/`, and any current
   metrics/notebook/report files the simulated user would reasonably ask the
   system to repair. From `investigation/`, retain user-facing notes/rubric
   context such as `rubric.md` and `user_notes.md`, but archive/remove
   `investigation/review_a.json` and similar review receipts. Archive/remove the
   old full-flow `pipeline_design.md`; it is process evidence from the first
   draft, not a required active repair input.
4. Write `prelaunch_startup_inventory.json` with:
   `declared_mode: repair_flow`, `rollback_archive_path`,
   `retained_startup_files`, `removed_stale_evidence`,
   `repair_request_source`, `repair_scope_summary`, and
   `must_not_full_rerun: true`.

The rollback archive is for A and post-run D audit. Runtime B/C must not read it
as task context unless the simulated user explicitly asks for archive
comparison.

- [ ] **Step 2: Dispatch repair coordinator B**

B must use the public runtime surface (`skill.md`, `do-homework.md`,
`task-orchestrator.md`) plus the accepted repair startup inventory and retained
current-draft files. B must not use internal validation docs or archive evidence
as task context.

B must write:

- `repair_request.md` or `repair_plan.md`, restating user feedback and repair
  scope using task-agnostic fields: retained context, forbidden context, repair
  objectives, planned changes, unchanged/out-of-scope targets, verification
  criteria, dependency order, and stop conditions;
- a repair-specific `repair_pipeline_design.md`; do not edit or reuse the archived
  full-flow `pipeline_design.md` as the active repair plan;
- stage briefs for repair executor/reviewer children;
- stage results/reviews;
- updated draft artifacts, render provenance, zip, verification files, and
  `result.json`.

Expected repair stages for this DSAA2011 validation may include the following,
but these are examples for the current assignment, not the generic repair-flow
contract:

- diagnosis: inspect current notebook/metrics/report/slides and identify which
  changes directly answer the feedback;
- notebook repair: add or refine analysis only where it supports deeper
  experiment discussion;
- report repair: expand report toward 8-9 pages with stronger experiment
  reasoning, model comparison, error analysis, limitations, and implications;
- slides/package repair: update slides and zip after report/notebook changes;
- verification: rerun notebook/PDF/zip checks needed by touched artifacts.

Do not accept a repair run that deletes the first draft and silently performs a
full-flow rerun. Rerunning a notebook or regenerating PDFs is allowed when it is
needed to repair touched artifacts.

- [ ] **Step 3: Verify repair child evidence**

Use the same child-dispatch ledger, identity injection, receipt timestamp,
dependency field, process-event, and transcript-export rules as Task 10. The
repair-specific checks are:

- every child brief states whether it is repair diagnosis, repair execution,
  repair spec review, repair quality review, or verification;
- each child reads only retained current-draft files and task-relevant generated
  artifacts, while avoiding rollback archive and prior validation evidence;
- repair executors modify only justified files;
- review children check both the new user feedback and preservation of prior
  artifact gates;
- `result.json` makes clear this is a repaired draft, not a fresh first draft.

- [ ] **Step 4: Dispatch D/E repair trajectory review**

After A exports B/C transcripts, dispatch D. D must dispatch one E per available
repair child transcript and aggregate E receipts.

D's repair-specific audit checks:

- the retained startup files match the accepted repair inventory;
- B wrote a repair request/plan before dispatching repair children;
- B did not use rollback archive, old transcripts, old stage reviews, or prior
  trajectory verdicts as task context;
- repair stages are scoped to the user feedback rather than an undeclared
  full rerun;
- changed files are justified by the repair request;
- untouched or regenerated deliverables still pass required artifact gates;
- final package and verification evidence correspond to the repaired draft.
- if the original repair coordinator timed out or was replaced, the ledger
  records a coordinator-level recovery event with previous/replacement
  coordinator ids, the replacement reads only current-run recovery evidence, and
  D treats the replacement as a process concern that blocks clean `PASS` but can
  still support `PASS_WITH_CONCERNS` when evidence is complete.

Clean `repair_flow` PASS does not require every artifact to be globally optimal.
It requires that the user-requested repair was addressed, the repair scope was
controlled, nested child evidence and transcript-body audits are complete, and
previously passing critical gates did not regress.

## Subagent Dispatch Plan

Use fresh subagents in this order:

1. **Protocol Subagent**: Task 1 and Task 5. Owns canonical schema and examples.
2. **Homework Coordinator Subagent**: Task 2. Owns `do-homework.md`.
3. **Orchestrator Subagent**: Task 3. Owns `task-orchestrator.md`.
4. **Architecture Reference Subagent**: Task 4 and Task 6. Owns skills architecture, backlog, and progress sync.
5. **Review Subagent**: Task 7. Reads all changed docs and verifies protocol consistency.
6. **Runtime Validation Subagent DSAA2011**: Task 8 after static docs pass. Starts from existing workbench inputs, regenerates `pipeline_design.md`, and does not rerun reconnaissance.
7. **Trajectory Review Subagent DSAA2011**: Task 8 Step 5. Reviews the runtime validation trajectory and nested subagent evidence against the protocol.
8. **Runtime Validation Subagent UCUG1505**: Task 9 after DSAA2011 evidence exists.
9. **Nested Isolation Coordinator Subagent**: Task 10. Must dispatch distinct child executor/spec-reviewer/quality-reviewer subagents. If child dispatch is unavailable, it returns `BLOCKED`; inline fallback is not passing evidence.
10. **Nested Isolation Transcript Auditor Subagents**: Task 10 Step 4. One fresh auditor per available child transcript; may run in parallel. Each checks a single child conversation against its brief, receipt, role scope, forbidden actions, and evidence consistency.
11. **Nested Isolation Trajectory Review Subagent**: Task 10 Step 4. Independently verifies child subagent ids/transcripts, dispatches transcript auditors when full transcripts are available, aggregates their receipts, and rejects inline fallback as isolation evidence.
12. **Repair Flow Coordinator Subagent**: Task 11. Starts from retained first-draft context, writes a repair plan, and dispatches repair executor/reviewer children without performing an undeclared full rerun.
13. **Repair Flow Transcript Auditor Subagents**: Task 11 Step 4. One fresh auditor per available repair child transcript.
14. **Repair Flow Trajectory Review Subagent**: Task 11 Step 4. Audits retained context, repair scope, changed-file justification, nested child evidence, and no-regression gates.

The Main Agent reviews each subagent result before dispatching the next task.
Do not run DSAA2011 or UCUG1505 validation until Tasks 1-7 pass.

## Self-Review

Spec coverage:

- Main Agent coordinator contract: Tasks 2 and 3.
- Stage brief generation: Tasks 1, 3, and 5.
- Executor receipt contract: Tasks 1, 3, and 5.
- Spec compliance before quality review: Tasks 1, 2, 3, 4, 5, and 7.
- DSAA2011 first, UCUG1505 second: Tasks 8 and 9.
- DSAA2011 starts after reconnaissance, regenerates `pipeline_design.md`, and receives independent trajectory review: Task 8.
- True executor/reviewer subagent isolation, with distinct child agent evidence:
  Task 10.
- Repair-flow startup, rollback archive, retained first-draft context, targeted
  repair pipeline, and nested repair trajectory review: Task 11.
- No submit in rollout: Tasks 8 and 9.

Placeholder scan:

- No unfinished `TBD` or `TODO` markers are used.
- Generic paths are schema examples, not missing implementation details.

Type consistency:

- Stage ids consistently use `stage_01_notebook` and `stage_02_report` in examples.
- Stage directories consistently use `stage_briefs/`, `stage_results/`, and `stage_reviews/`.
- Review types consistently use `spec_compliance` and `quality`.
- Executor statuses consistently use `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, and `BLOCKED`.
