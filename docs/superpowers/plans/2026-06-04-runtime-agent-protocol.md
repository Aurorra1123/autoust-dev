# Runtime Agent Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align AutoStudy documentation around a Superpowers-inspired runtime handoff protocol where Claude Code Main Agent coordinates the task and subagents consume precise stage briefs.

**Architecture:** This is a documentation/protocol implementation, not a runtime framework implementation. `docs/runtime-agent-protocol.md` and the spec define the canonical design; `do-homework.md`, `task-orchestrator.md`, and `skills-architecture-spec.md` are updated to use `pipeline_design.md` as the total plan and `stage_brief.md` as the subagent context pack.

**Tech Stack:** Markdown task skills, JSON backlog (`docs/plans/feature-list.json`), shell validation with `python3 -m json.tool`, `rg`, and `git diff --check`.

---

## File Structure

| File | Responsibility |
|---|---|
| `docs/runtime-agent-protocol.md` | Canonical runtime handoff protocol: planes, Main Agent phases, subagent contracts, runtime file interfaces. |
| `docs/superpowers/specs/2026-06-04-runtime-agent-protocol-design.md` | Design spec for the protocol implementation. |
| `sub-skills/tasks/do-homework.md` | Main Agent coordinator contract for homework tasks. |
| `sub-skills/tasks/task-orchestrator.md` | Main Agent contract for stage brief generation, subagent dispatch, review loops, and final verification. |
| `docs/skills-architecture-spec.md` | Skills and pipeline format reference aligned with the runtime protocol. |
| `docs/ROADMAP.md` | Development-plane roadmap updated to point at the protocol and remove stale M3 contradictions. |
| `docs/plans/feature-list.json` | Structured backlog evidence for M3.5 execution architecture. |
| `docs/progress/agent-progress.md` | Handoff note describing this planning pass and next implementation step. |

## Task 1: Canonicalize Protocol References

**Files:**
- Modify: `docs/runtime-agent-protocol.md`
- Modify: `AGENTS.md`
- Modify: `docs/COLLABORATION.md`
- Modify: `docs/plans/feature-list.json`
- Modify: `docs/progress/agent-progress.md`

- [ ] **Step 1: Verify runtime protocol states Superpowers is design reference only**

Run:

```bash
rg -n "design reference only|not require|not a runtime dependency" docs/runtime-agent-protocol.md docs/COLLABORATION.md AGENTS.md
```

Expected: matches in all three files confirming Superpowers is a design reference, not runtime dependency.

- [ ] **Step 2: Add missing reference text if any match is absent**

If `docs/runtime-agent-protocol.md` lacks the design-reference wording, add:

```markdown
The design borrows mature workflow discipline from the Superpowers plugin, but
Superpowers is a **design reference only**. AutoStudy runtime must not require
the user to install or invoke Superpowers.
```

If `docs/COLLABORATION.md` lacks the workflow-reference section, add a `### Superpowers: Workflow Reference` section near the Canvas Copilot reference section with:

```markdown
Superpowers is AutoStudy's reference for agent workflow discipline, not a
runtime dependency. AutoStudy should not require a user to install Superpowers
to complete Canvas or study tasks.
```

If `AGENTS.md` lacks a runtime protocol pointer, add this row under "Where things live":

```markdown
| Runtime agent handoff protocol | [docs/runtime-agent-protocol.md](./docs/runtime-agent-protocol.md) |
```

- [ ] **Step 3: Record evidence in feature-list**

Update `M3.5-EXECUTION-ARCHITECTURE.evidence` in `docs/plans/feature-list.json` to include:

```json
"2026-06-04 docs/runtime-agent-protocol.md defines the Claude Code Main Agent + subagent handoff protocol and Superpowers-inspired workflow mapping"
```

- [ ] **Step 4: Validate canonical references**

Run:

```bash
python3 -m json.tool docs/plans/feature-list.json > /tmp/autoust-feature-list-json-check.json
git diff --check
rg -n "runtime-agent-protocol|Superpowers" AGENTS.md docs/COLLABORATION.md docs/runtime-agent-protocol.md docs/plans/feature-list.json
```

Expected: JSON command exits 0, diff check exits 0, grep shows the protocol referenced from development-plane docs.

- [ ] **Step 5: Commit Task 1**

```bash
git add docs/runtime-agent-protocol.md AGENTS.md docs/COLLABORATION.md docs/plans/feature-list.json docs/progress/agent-progress.md
git commit -m "docs: establish runtime agent protocol"
```

## Task 2: Align `do-homework.md` With Main Agent Coordination

**Files:**
- Modify: `sub-skills/tasks/do-homework.md`
- Reference: `docs/runtime-agent-protocol.md`
- Reference: `docs/superpowers/specs/2026-06-04-runtime-agent-protocol-design.md`

- [ ] **Step 1: Update the opening model**

In `sub-skills/tasks/do-homework.md`, update the opening description after the workbench flow so it states:

```markdown
`do-homework.md` is written for the Claude Code Main Agent. The Main Agent is
the only runtime actor that talks to the user. Subagents, when used, are
temporary workers dispatched by the Main Agent and receive precise stage briefs.
```

- [ ] **Step 2: Add stage directories to the target workbench**

In the `[A2] Create The Workbench` target structure, insert these directories after `pipeline_design.md`:

```text
├── stage_briefs/
├── stage_results/
├── stage_reviews/
```

Expected structure snippet:

```text
├── pipeline_design.md
├── stage_briefs/
├── stage_results/
├── stage_reviews/
├── draft/
```

- [ ] **Step 3: Update `[C]` to define pipeline design as total plan**

Find the `[C]` section. Add this paragraph before invoking `task-orchestrator.md`:

```markdown
`pipeline_design.md` is the task-level plan for the Main Agent and
task-orchestrator. It is not handed directly to executor subagents. The
orchestrator converts each delegated stage into `stage_briefs/stage_<N>_<slug>.md`.
```

- [ ] **Step 4: Update `[D]` expectations**

In the execution section, require `task-orchestrator.md` to return or write:

```text
stage_briefs/
stage_results/
stage_reviews/
verification_checklist.md
verification.log
```

Also state:

```markdown
Do not mark the draft as ready if reviewed stages lack a passing spec compliance
review. Quality review happens only after spec compliance passes.
```

- [ ] **Step 5: Validate `do-homework.md` wording**

Run:

```bash
rg -n "Main Agent|stage_briefs|stage_results|stage_reviews|spec compliance" sub-skills/tasks/do-homework.md
git diff --check sub-skills/tasks/do-homework.md
```

Expected: grep finds all five protocol concepts; diff check exits 0.

- [ ] **Step 6: Commit Task 2**

```bash
git add sub-skills/tasks/do-homework.md
git commit -m "docs: align do-homework with runtime coordinator protocol"
```

## Task 3: Rewrite `task-orchestrator.md` As Stage Coordinator Contract

**Files:**
- Modify: `sub-skills/tasks/task-orchestrator.md`
- Reference: `docs/runtime-agent-protocol.md`
- Reference: `docs/superpowers/specs/2026-06-04-runtime-agent-protocol-design.md`

- [ ] **Step 1: Update role statement**

Replace the opening paragraph under `# task-orchestrator` with:

```markdown
The core M3.5 execution coordination mechanism. This task is written for the
Claude Code Main Agent. It reads the task-level `pipeline_design.md`, creates
bounded stage briefs, dispatches executor and reviewer subagents when a stage is
delegated, and aggregates evidence for final verification.
```

- [ ] **Step 2: Update required workbench**

Add these directories to the required workbench tree:

```text
├── stage_briefs/
├── stage_results/
├── stage_reviews/
```

- [ ] **Step 3: Replace "Execute Stages" with stage brief flow**

Replace the existing `### Step 3 - Execute Stages` body with:

````markdown
### Step 3 - Generate Stage Briefs

For each stage in `pipeline_design.md`, write one stage brief under:

```text
stage_briefs/stage_<N>_<slug>.md
```

Each brief must include:

- role: `executor`
- concrete one-stage task
- required reads
- allowed reads
- forbidden reads
- declared writes
- selected tool skill paths
- measurable quality criteria
- review criteria
- context from previous stages
- blockers and escalation rules

Do not dispatch a subagent until its stage brief exists.
````

- [ ] **Step 4: Add executor dispatch section**

After the stage brief section, add:

```markdown
### Step 4 - Dispatch Executor Subagent Or Run Inline

If `delegate: subagent`, dispatch one executor subagent with only the stage
brief and a short prompt pointing to it. The executor reports `DONE`,
`DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED` and writes
`stage_results/<stage_id>_result.json`.

If `delegate: main-agent`, the Main Agent executes the simple stage inline but
still writes a `stage_results/<stage_id>_result.json` receipt.
```

- [ ] **Step 5: Add review loop section**

Add:

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

- [ ] **Step 6: Update final verification step**

Ensure final verification requires:

```markdown
- every delegated stage has a `stage_results/<stage_id>_result.json`;
- every reviewed stage has passing spec compliance review;
- quality review is passing or explicitly skipped with reason;
- `verification.log` contains measured PASS/FAIL/SKIP lines;
- `result.json` is not marked `draft_ready` while blocking FAIL reviews remain.
```

- [ ] **Step 7: Validate orchestrator wording**

Run:

```bash
rg -n "Generate Stage Briefs|Dispatch Executor|Review In Order|stage_results|stage_reviews|Never run quality review" sub-skills/tasks/task-orchestrator.md
git diff --check sub-skills/tasks/task-orchestrator.md
```

Expected: grep finds all protocol sections and diff check exits 0.

- [ ] **Step 8: Commit Task 3**

```bash
git add sub-skills/tasks/task-orchestrator.md
git commit -m "docs: define stage coordinator and review loop"
```

## Task 4: Align Skills Architecture And Roadmap

**Files:**
- Modify: `docs/skills-architecture-spec.md`
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Add runtime protocol pointer to skills architecture**

Near the top of `docs/skills-architecture-spec.md`, add:

```markdown
Runtime handoff rules live in `docs/runtime-agent-protocol.md`. This file
defines skill structure and pipeline design conventions; the runtime protocol
defines how the Main Agent turns those plans into subagent stage briefs,
results, reviews, and final verification evidence.
```

- [ ] **Step 2: Upgrade pipeline design section**

In `docs/skills-architecture-spec.md §5`, add these stage fields to the list of supported fields:

```markdown
- `id`: stable stage id, e.g. `stage_01_notebook`
- `delegate`: `main-agent` or `subagent`
- `review.spec_compliance`: true/false
- `review.quality`: true/false
- `max_retries`: retry count before human review
- `quality_criteria`: measurable checks used by executor and reviewers
- `human_blockers`: user-supplied information required before or after the stage
```

- [ ] **Step 3: Update sub-agent review section**

In `docs/skills-architecture-spec.md §8.3`, replace the single "spawn 1 audit agent" model with:

```markdown
When review is enabled, the Main Agent runs reviews in order:

1. Spec compliance review: compare artifact against `spec.md`, rubric, user notes, and stage brief.
2. Quality review: check artifact-specific quality only after spec compliance passes.

Review outputs are written under `stage_reviews/`.
```

- [ ] **Step 4: Remove stale M3 status contradictions from roadmap**

In `docs/ROADMAP.md`, change the M3 report pipeline table rows for `paper-search`, `figure-maker`, and `writing-helper` from `待写` to `✅ 已完成`.

Also add a short M3.5 note:

```markdown
Current execution architecture direction is defined in `docs/runtime-agent-protocol.md`: `pipeline_design.md` is the task-level plan, and delegated stages receive generated `stage_briefs/*.md`.
```

- [ ] **Step 5: Validate architecture references**

Run:

```bash
rg -n "runtime-agent-protocol|delegate|stage_briefs|spec compliance|quality review" docs/skills-architecture-spec.md docs/ROADMAP.md
git diff --check docs/skills-architecture-spec.md docs/ROADMAP.md
```

Expected: grep finds protocol references and new stage terms; diff check exits 0.

- [ ] **Step 6: Commit Task 4**

```bash
git add docs/skills-architecture-spec.md docs/ROADMAP.md
git commit -m "docs: align skills architecture with runtime protocol"
```

## Task 5: Add Protocol Schema Examples

**Files:**
- Create: `docs/examples/runtime/stage_brief-example.md`
- Create: `docs/examples/runtime/stage_result-example.json`
- Create: `docs/examples/runtime/stage_review-example.json`
- Modify: `docs/runtime-agent-protocol.md`

- [ ] **Step 1: Create stage brief example**

Create `docs/examples/runtime/stage_brief-example.md` with:

```markdown
# Stage Brief: stage_01_report - Report Draft

## Role
executor

## Task
Write `draft/report.md` for the assignment using the verified Canvas spec, rubric, and user notes.

## Required Reads
- `spec.md`: assignment facts and deliverables
- `investigation/rubric.md`: grading criteria
- `investigation/user_notes.md`: user preferences and missing context resolved at checkpoint B
- `sub-skills/tools/writing-helper.md`: prose writing contract

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
- `draft/report.md`: complete report draft with no unresolved placeholders
- `stage_results/stage_01_report_result.json`: executor receipt

## Tool Guidance
- `sub-skills/tools/writing-helper.md`
- `sub-skills/tools/writing-helper-report.md`
- `sub-skills/tools/humanizer.md` if `pipeline_design.md` declares `post-process: humanize`

## Quality Criteria
- Covers every rubric criterion in `investigation/rubric.md`
- Contains no forbidden placeholder markers
- Grounds every numeric claim in a source or previous stage output

## Review Criteria
- Spec compliance: all required deliverables and rubric items are addressed
- Quality: writing is coherent, evidence-grounded, and appropriate for the course

## Context From Previous Stages
Stage 0 reconnaissance found the main spec in `references/project_spec.pdf`. The user asked for concise academic English.

## Blockers And Escalation
Return `NEEDS_CONTEXT` if a required dataset, partner name, or topic choice is still missing.
```

- [ ] **Step 2: Create stage result example**

Create `docs/examples/runtime/stage_result-example.json` with:

```json
{
  "stage": "stage_01_report",
  "status": "DONE",
  "summary": "Wrote a complete report draft grounded in spec, rubric, and user notes.",
  "outputs": [
    {"path": "draft/report.md", "size_bytes": 18432}
  ],
  "commands_run": [
    "python3 - <<'PY'\\nfrom pathlib import Path\\ntext = Path('draft/report.md').read_text()\\nprint(len(text.split()))\\nPY"
  ],
  "verification_evidence": [
    "report.md exists",
    "no forbidden placeholder markers found",
    "rubric criteria are explicitly addressed"
  ],
  "concerns": []
}
```

- [ ] **Step 3: Create stage review example**

Create `docs/examples/runtime/stage_review-example.json` with:

```json
{
  "stage": "stage_01_report",
  "review_type": "spec_compliance",
  "verdict": "PASS",
  "evidence": [
    "draft/report.md addresses all three rubric sections",
    "deliverable format matches spec.md requirement: report markdown for PDF rendering"
  ],
  "issues": [],
  "fix_suggestions": []
}
```

- [ ] **Step 4: Link examples from runtime protocol**

In `docs/runtime-agent-protocol.md`, add under "Runtime File Interfaces":

```markdown
Concrete examples live in `docs/examples/runtime/`:

- `stage_brief-example.md`
- `stage_result-example.json`
- `stage_review-example.json`
```

- [ ] **Step 5: Validate examples**

Run:

```bash
python3 -m json.tool docs/examples/runtime/stage_result-example.json > /tmp/autoust-stage-result-example.json
python3 -m json.tool docs/examples/runtime/stage_review-example.json > /tmp/autoust-stage-review-example.json
rg -n "stage_brief-example|stage_result-example|stage_review-example" docs/runtime-agent-protocol.md docs/examples/runtime
git diff --check docs/runtime-agent-protocol.md docs/examples/runtime
```

Expected: JSON files parse, grep finds all example references, diff check exits 0.

- [ ] **Step 6: Commit Task 5**

```bash
git add docs/runtime-agent-protocol.md docs/examples/runtime
git commit -m "docs: add runtime stage handoff examples"
```

## Task 6: Final Documentation Verification

**Files:**
- Modify: `docs/progress/agent-progress.md`
- Modify: `docs/plans/feature-list.json`

- [ ] **Step 1: Update progress note**

Add to the latest `2026-06-04` progress section:

```markdown
Runtime protocol implementation plan written at `docs/superpowers/plans/2026-06-04-runtime-agent-protocol.md`. Next implementation should align `do-homework.md`, `task-orchestrator.md`, `skills-architecture-spec.md`, and roadmap against the Main Agent + stage brief protocol.
```

- [ ] **Step 2: Update feature-list evidence**

In `M3.5-EXECUTION-ARCHITECTURE.evidence`, add:

```json
"2026-06-04 docs/superpowers/specs/2026-06-04-runtime-agent-protocol-design.md and docs/superpowers/plans/2026-06-04-runtime-agent-protocol.md define the implementation path"
```

- [ ] **Step 3: Run full static verification**

Run:

```bash
python3 -m json.tool docs/plans/feature-list.json > /tmp/autoust-feature-list-json-check.json
python3 -m json.tool docs/examples/runtime/stage_result-example.json > /tmp/autoust-stage-result-example.json
python3 -m json.tool docs/examples/runtime/stage_review-example.json > /tmp/autoust-stage-review-example.json
rg -n "canvascli --version" .
rg -n "待写" docs/ROADMAP.md docs/skills-architecture-spec.md
git diff --check
```

Expected:

- all JSON checks exit 0;
- `rg -n "canvascli --version" .` exits 1 with no matches;
- `rg -n "待写" docs/ROADMAP.md docs/skills-architecture-spec.md` exits 1 or only reports intentionally future appendix files such as `code-writer-cpp.md`;
- `git diff --check` exits 0.

- [ ] **Step 4: Review final diff**

Run:

```bash
git diff --stat
git status --short
```

Expected: only planned documentation files are modified or created.

- [ ] **Step 5: Commit Task 6**

```bash
git add docs/progress/agent-progress.md docs/plans/feature-list.json
git commit -m "docs: record runtime protocol implementation plan"
```

## Self-Review

Spec coverage:

- Development vs Runtime plane separation: covered by Tasks 1 and 4.
- Main Agent vs subagent runtime reality: covered by Tasks 1, 2, and 3.
- `pipeline_design.md` as total plan: covered by Tasks 2, 3, and 4.
- `stage_brief.md` as subagent context pack: covered by Tasks 3 and 5.
- Executor/spec reviewer/quality reviewer contracts: covered by Tasks 3, 4, and 5.
- Verification evidence before completion: covered by Tasks 3 and 6.

Placeholder scan:

- No unfinished placeholder markers are used.
- Commands have exact expected outcomes.
- File paths are exact.

Type consistency:

- Stage directories consistently use `stage_briefs/`, `stage_results/`, and `stage_reviews/`.
- Review types consistently use `spec_compliance`, `quality`, and `final`.
- Executor statuses consistently use `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, and `BLOCKED`.
