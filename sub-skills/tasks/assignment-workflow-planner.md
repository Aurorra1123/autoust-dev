---
name: assignment-workflow-planner
description: homework workflow planner
---

# Assignment Workflow Planner

This task owns user-facing intent alignment and pipeline planning. It does not
run clean-start Canvas/source reconnaissance and does not own the first full
reconnaissance-results briefing. For clean starts, this planner requires a confirmed reconnaissance briefing from
`sub-skills/tasks/assignment-source-intake.md`; then it reads the terminal
outputs to align user intent. For retained artifacts, first invoke
`../tools/current-state-intake.md`.

Clean-start planning artifact chain:

```text
prelaunch_startup_inventory.json
-> investigation/explore_manifest.json
-> references/REFERENCE_INDEX.md
-> references/
-> spec.md
-> investigation/rubric.md
-> investigation/review_a.json
-> investigation/recon_summary.md
-> investigation/explore_context.md
-> investigation/alignment_brief.md
-> pipeline_design.md
   -> Pipeline Review Status: awaiting_user_review
-> result.json                    # only when pausing, skipping, erroring, or deferring
```

Retained-artifact planning artifact chain:

```text
prelaunch_startup_inventory.json
-> investigation/explore_manifest.json
-> investigation/explore_context.md
-> investigation/repair_recon.md  # when useful
-> repair_request.md              # when useful
-> repair_plan.md
-> repair_pipeline_design.md      # when a repair/change pipeline is needed
   -> Pipeline Review Status: awaiting_user_review
-> result.json                    # only when pausing, skipping, erroring, or deferring
```

## Entry Modes

| Entry | Required read | Next action |
|---|---|---|
| clean recon | confirmed reconnaissance briefing plus `prelaunch_startup_inventory.json`, `spec.md`, `investigation/explore_context.md`, `investigation/recon_summary.md`, `investigation/review_a.json`, `references/` | run `[B]`, then `[C]` |
| retained artifact | `prelaunch_startup_inventory.json`, then `../tools/current-state-intake.md` outputs | run retained alignment, write `repair_plan.md`, then `repair_pipeline_design.md` when needed |
| pipeline review | existing result when present plus `pipeline_design.md` or `repair_pipeline_design.md` | help user approve/revise; do not execute inside planner |
| draft review | retained draft/result artifacts named in startup inventory | help user review/revise/submit path; do not clean-start by default |
| recovery | previous `result.json` plus allowlisted history | use current-state intake unless source evidence is explicitly missing/stale |

## Route Guidance

- Clean starts arrive after `sub-skills/tasks/assignment-source-intake.md` has
  written terminal source outputs and the user has confirmed the reconnaissance
  briefing. This planner reads those outputs and does not run clean-start
  Canvas/source reconnaissance.
- For `review_or_execute`, read the existing result, accepted workbench, and
  `pipeline_design.md` or `repair_pipeline_design.md`; help the user review
  or approve the existing pipeline. Do not execute stages inside this planner.
- For `review_or_submit`, read the retained draft/result artifacts named in
  startup inventory; help the user review, revise, or submit path. Do not
  clean-start by default.
- For `continue` or recovery, inspect the previous `result.json` and use
  current-state intake unless missing/stale source evidence is the blocker.

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

### [B] Alignment Loop

User-interaction phase #1.

Read `spec.md` first, then `investigation/explore_context.md`,
`investigation/recon_summary.md`, `investigation/review_a.json`,
`investigation/rubric.md`, `investigation/unreachable.txt`, and `problem.md`
when present. These files are already confirmed source-intake outputs. Use them
to ask alignment questions and write the terminal agreement; do not repeat the
full source-category evidence map from the reconnaissance confirmation
checkpoint.
Do not repeat the full source-category evidence map.

This planner does not own the first full reconnaissance-results briefing. It
may briefly restate the confirmed assignment facts only when needed to frame the
next alignment question, correct a user misunderstanding, or explain why a
missing user decision blocks planning. The normal `[B]` response starts from the
smallest user-intent question needed to avoid guessing.

Even when `review_a.json.verdict == "proceed"`, alignment is still mandatory.
`proceed` means the Canvas materials are sufficient to understand the assignment
surface. It does not mean the user's intended direction is aligned.

Runtime/user boundary:

- In normal workflow-planner runtime, the Main Agent asks the real user at `[B]`.
- In development validation, only `SIMULATED_USER_ANSWER_B_ROUND_<N>`,
  `SIMULATED_USER_ALIGNMENT_CONFIRMATION`, or explicit startup-prompt
  supplements count as simulated user input.
- A request phrased as "simulate I am the user" means exercise the runtime path;
  it does not let the Main Agent invent the user's topic choice, research
  question, group facts, approval, or alignment confirmation.
- If no valid user or simulated-user answer exists for an open assignment
  direction, stop after the recon summary and ask the `[B]` question.

The goal of `[B]` is not to classify the assignment into rigid "simple" or
"open" categories. The Main Agent must keep asking only while the current
information is not enough to start without guessing the user's core intent. For
straightforward assignments this may be one short confirmation. For open-ended
assignments, continue the loop until the Main Agent can write a stable
the current terminal agreement and defend why the next pipeline will not drift
away from the user's intent or project skeleton.

For open-ended projects, `[B]` has a required alignment loop:

1. Ask one clarifying question at a time.
2. After each answer, infer what new design dimensions the answer introduces.
3. Once enough raw intent is known, propose 2-3 viable approaches with
   trade-offs and a recommendation, then ask the user to choose or correct.
4. Present a concise design skeleton before the final brief.
5. Self-review the skeleton and brief for gaps, contradictions, ambiguity, and
   scope drift before asking for confirmation.

If the assignment asks the user to choose a project direction, dataset,
architecture, creative concept, user experience, research question, or other
open design variable, do not write `alignment_brief.md` until the missing
variable is either confirmed by the user or explicitly delegated to the Main
Agent and recorded as delegated.

#### [B1] Ask The Most Important Alignment Question

Before every question, run this internal alignment audit:

```text
Can I answer these without guessing?

1. What exactly must be delivered?
2. What does the user want this work to express, argue, demonstrate, or optimize?
3. Which choices are fixed by Canvas/spec/rubric?
4. Which choices must come from the user before work starts?
5. Which choices has the user delegated to me?
6. What must not be fabricated or hidden?
7. Can I now write pipeline stages with concrete goals and quality criteria?
8. Could a reviewer use the eventual alignment brief to detect direction drift?
```

For open-ended design, creative, research, implementation, or interactive
projects, also run this design skeleton readiness audit:

```text
Can I sketch these without guessing?

1. User-facing experience: who uses it, what happens first, what is the loop?
2. Creative or intellectual stance: tone, thesis, novelty, audience impact.
3. Core inputs and outputs: data/files/media/API inputs and final artifacts.
4. Architecture: main components, state, dependencies, and boundaries.
5. Model/tool contract: providers, request/response shape, mocks, probes, and
   secret handling if models/APIs are involved.
6. Traceability: what steps must be observable for debugging, grading, or demo.
7. Failure and fallback behavior: what happens when APIs, files, renders,
   tests, or external resources fail.
8. Verification and demo: how the result will be tested, shown, and reviewed.
```

If a missing skeleton answer would change the pipeline shape, stage boundaries,
tool choice, deliverable quality criteria, or user-facing experience, it is not
a minor default. Ask about it before writing the terminal brief.

Record the skeleton readiness result in `investigation/user_notes.md` under the
current round. Include which dimensions are fixed, delegated, not applicable, or
still blocking.

If any missing answer can change the assignment's direction, ask one question:
the single question that most reduces direction-drift risk. Do not ask a batch
of questions. Do not ask low-impact style or formatting questions while a core
topic, dataset, argument, project concept, method, scope, or personal stance is
still unclear.

Question priority:

1. Core direction choices: topic, dataset, project concept, thesis, research
   question, method, framework, or target audience.
2. User-owned material: personal experience, viewpoint, aesthetic preference,
   group context, oral instructor notes, or presentation intent.
3. Execution blockers: missing file, blocked URL, missing group info, ambiguous
   scope, unavailable code/data/template.
4. Delegation boundaries: what the user allows the model to decide and what
   must remain for human review.
5. Project skeleton gaps: user-facing flow, architecture, model/API contract,
   observability/trace, fallback behavior, demo mode, and verification strategy
   when they affect pipeline design.
6. Minor defaults: ordinary formatting, wording, standard tool choices, and
   other low-risk defaults. Ask these only if they materially affect grading or
   user identity.

Prefer open-ended questions for user-owned thinking. Prefer 2-3 options when
the user may not have a ready idea or when the choice is operational.

Example for a clear fixed-spec project:

Ask:

```text
这份作业的 spec 和交付物已经很明确。唯一会影响后续产物命名和实验内容的是
dataset / group id / 是否提交。你确认用 <dataset>、<group id>，并先只生成
本地草稿不提交吗？
```

Example for an open-ended creative or reflective project:

```text
这个项目最容易跑偏的是核心 concept。你希望作品主要表达哪种方向？

1. 偏技术展示：突出交互机制和实现完整度
2. 偏艺术表达：做一个有主题、有情绪的体验
3. 偏实用小工具：让交互服务一个明确功能

也可以直接说你自己的想法。
```

#### [B2] Record Conversation Notes, Not The Final Brief

After each answer, append process notes to:

```text
<work_dir>/investigation/user_notes.md
```

Use this structure:

```markdown
## Alignment Conversation Notes

### Round <N>
- Question:
- User answer:
- Coordinator interpretation:
- Decisions captured:
- Remaining uncertainty:
- New dimensions introduced:
- Approach implications:
- Skeleton gaps still open:
```

`user_notes.md` is a process log. It may be appended every round.
`alignment_brief.md` is not a process log and must not be rewritten after every
question. Write `alignment_brief.md` only when the Main Agent has no necessary
alignment question left.

If the user chooses partial scope, write:

```text
<work_dir>/investigation/user_scope.md
```

If the user says "you decide" or equivalent, record the decision as delegated,
not as a user-stated fact. The later `alignment_brief.md` must explain the
default strategy and why it is reasonable.

After each answer, extend the conversation from what the user actually said
rather than walking a fixed questionnaire. Example: if the user says "use a
multimodal model and image generation," the next likely uncertainty is not
formatting; it is API contract, mock fidelity, secret handling, fallback
behavior, and where model traces appear in the experience.

If the user stops, write `result.json` with `status: "skipped"`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status skipped \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --note "user stopped after reconnaissance"
```

If `[A4]` flagged reconnaissance failure and the user supplies pasted material,
save it to:

```text
<work_dir>/problem_user.md
```

Then update source-intake context files such as `spec.md`, `problem.md` when
present, `investigation/rubric.md`, `investigation/review_a.json`, and
`investigation/explore_context.md` so downstream tools read the supplemented
context from files, not chat memory. Do not write `pipeline_design.md` until
`[C]`.

#### [B3] Explore Approaches And Preview The Design Skeleton

Before writing `alignment_brief.md`, check whether the user has approved the
project skeleton. For straightforward assignments whose skeleton is fixed by the
spec, this may be a one-sentence confirmation. For open-ended assignments, it is
mandatory.

When enough raw information exists to compare plausible directions, present 2-3
approaches with trade-offs and your recommendation. Keep this concise, but make
the differences real. Example:

```text
我看到三种可行方向：

1. 展示优先：最稳，适合答辩，但真实 API 深度较浅。
2. 真实集成优先：最像产品，但需要 key、错误处理和 contract probe。
3. 创意体验优先：作品感最强，但 pipeline 和 fallback 要更精心设计。

我建议 2 + 3 的混合：...
你选这个方向吗，还是要改？
```

After the user chooses or corrects the approach, present a design skeleton
preview before the terminal brief. Cover only what matters for this assignment.
For open projects, include each applicable item below, or record why it is not
applicable:

- user-facing experience and interaction loop;
- creative direction / thesis / tone;
- architecture components and data flow;
- model/API or tool contracts, including mock/probe strategy;
- traceability / observability surface;
- failure and fallback behavior;
- expected deliverables, demo path, and verification strategy.

Ask the user whether the skeleton is right. Record the user's confirmation or
correction in `investigation/user_notes.md` with timestamp or turn summary. If
the user corrects it, append another `user_notes.md` round and update the
skeleton. Do not enter `[C]` until the user has approved either the short
fixed-spec skeleton or the richer open-project skeleton.

#### [B4] Write And Confirm The Terminal Agreement

When the internal alignment audit no longer exposes a necessary question, write
the terminal agreement for the current entry:

```text
clean recon:       <work_dir>/investigation/alignment_brief.md
retained artifact: <work_dir>/repair_plan.md
```

Template:

```markdown
# Alignment Brief: <COURSE> <Assignment>

## Assignment Understanding
Summarize the Canvas-grounded task in the Main Agent's words.

## User Intent
State what the user wants this work to express, argue, demonstrate, or optimize.

## Confirmed Decisions
- ...

## Selected Approach
State the approach the user approved, including alternatives considered when
that mattered.

## Design Skeleton
- User-facing experience:
- Creative / intellectual direction:
- Architecture and data flow:
- Model, API, tool, or data contracts:
- Traceability / observability:
- Failure and fallback behavior:
- Verification and demo strategy:

## Delegated Decisions
- Decision:
  Default strategy:
  Reason:

## Non-Negotiables
- Content that must not be fabricated.
- Constraints or user boundaries that must not be crossed.

## Open Items For Final Review
- Items that do not block pipeline approval but must be surfaced at `[C5]` or
  later by `task-orchestrator.md` as human review items.

## Ready-To-Start Judgment
Explain why the Main Agent can now enter [C] without guessing the user's core
intent or project skeleton. Explicitly mention why the design skeleton is
sufficient to write pipeline stages with concrete goals, reads, writes, reviews,
quality criteria, and final review items.

## Self-Review
- Placeholder scan:
- Internal consistency:
- Scope check:
- Ambiguity check:

## User Confirmation
- Confirmation source:
- Confirmed by:
- Confirmation summary:
```

For retained-artifact entries, use the same section structure in
`repair_plan.md`, with `Changed Targets`, `Unchanged Retained Context`, and
`Forbidden Context` added when useful.

Before showing the brief to the user, self-review it and record the result in
the terminal agreement's `Self-Review` section:

- Placeholder scan: no TBD/TODO/empty section unless listed as a final review
  item.
- Internal consistency: selected approach, skeleton, non-negotiables, and open
  items do not contradict each other.
- Scope check: the work can be planned as one pipeline; if not, ask the user to
  narrow or stage it.
- Ambiguity check: any unresolved choice that would change stage design is asked
  before confirmation, not hidden as a delegated default.

Then show the user a concise summary and ask for confirmation. After the user
confirms, update the terminal agreement's `User Confirmation` before entering
`[C]`:

```text
我已经没有必须继续问你的问题了。下面是我写入 terminal agreement 的最终理解：

- ...

如果你确认，我会按这个方向进入 pipeline planning。
如果哪里不对，我会先修正 brief，不会开始执行。
```

If the user requests changes, append another round to `user_notes.md`, replace
the terminal agreement with the corrected final brief, and ask for confirmation
again. Do not enter `[C]` until the user confirms the brief.

Hard gate: without the current entry's terminal agreement containing populated
`Self-Review` and `User Confirmation` sections, do not write the final
`pipeline_design.md` / `repair_pipeline_design.md` and do not invoke
`task-orchestrator.md`.

### [C] Design Pipeline

No executor/reviewer subagents and no draft-generation tool runs in `[C]`.
`[C]` writes the task-level execution plan only. The only user interaction after
planning is `[C5]`, where the user reviews the pipeline before any
`task-orchestrator.md` run.

Read:

```text
spec.md
investigation/explore_context.md
investigation/explore_manifest.json
investigation/rubric.md
investigation/review_a.json
references/canvas_native/**/source.json  # preserved Canvas-native evidence
references/canvas_native/**/source.txt   # preserved Canvas-native body text
canvas/assignment.json             # fallback only for URL/metadata shell fields or missing preserved copies; record the reason
canvas/page-*.json                 # fallback only when no preserved Canvas-native copy exists; record the reason
investigation/alignment_brief.md   # clean recon terminal agreement, required and confirmed at [B]
repair_plan.md                     # retained-artifact terminal agreement, required and confirmed at [B] for retained entries
investigation/user_notes.md       # if present
investigation/user_scope.md       # if present
problem_user.md                   # if present
sub-skills/tools/_index.md
```

In `[C]`, write `pipeline_design.md` for clean recon entries and
`repair_pipeline_design.md` for retained-artifact repair/change entries. Existing
`pipeline_design.md` or `repair_pipeline_design.md` is read only for
pipeline-review entries.

Use the following common pipeline shapes as **reference guidance** — the agent
composes freely based on the actual assignment, not a fixed chain.

| Scenario | type | Typical tool chain | Final deliverable |
|---|---|---|---|
| **paper** | `paper` | paper-search → figure-maker (opt) → writing-helper → pdf-renderer | `final.pdf` |
| **slides** | `slides` | figure-maker (opt) → slide-maker | `slides.pdf` |
| **math** | `math` | writing-helper (LaTeX math) → pdf-renderer | `solution.pdf` |
| **lab** | `lab` | code-writer → test-runner → writing-helper → pdf-renderer | `src/` + `report.pdf` |
| **mixed** | `mixed` | Multiple sub-pipelines composed from above | multiple files |

For mixed assignments, write multiple sub-pipelines in the current execution
plan file.

The current execution plan file, `pipeline_design.md` for clean entries or
`repair_pipeline_design.md` for retained entries, must contain these sections
and fields:

- `# Pipeline: <COURSE> <assignment>`
- `## Metadata`
  - `repo_root`
  - `work_dir`
  - `course_id`
  - `assignment_id`
- `## Output`
  - `mode`
  - final deliverable filenames/paths
- `## Pipeline Review Status`
  - `status: awaiting_user_review`
  - `review_requested_at`
  - `approved_at: null`
  - `approved_by: null`
  - `approval_summary: null`
- `## Constraints`
  - assignment constraints from `spec.md`
  - syllabus-derived constraints only after `spec.md`, `explore_context.md`,
    `rubric.md`, or `review_a.json` confirms their relevance
  - user constraints and non-negotiables from the current terminal agreement
  - forbidden context rules when relevant
  - non-downgradable hard requirements from `spec.md`
- `## Stages`
  - stable stage id
  - concrete stage goal
  - `primary_tool`: the main top-level tool skill for stage ownership
  - `tools`: ordered list of all top-level tool skills the stage must use
  - `tool_roles`: why each listed tool is needed in this stage
  - `delegate`: `subagent` or `main-agent`
  - allowed reads
  - writes
  - review settings: spec compliance and quality
  - retry limit
  - quality criteria
  - human blockers
- `## Human Review Items`

### Spec Hard Requirements / No-Downgrade Policy

When `spec.md` or the authoritative reference states a hard requirement, the
pipeline must preserve it exactly. Hard requirements include any explicit
`must`, `required`, `only`, `do not`, exact filename/package/layout constraints,
mandated data/source/tool/template/class/style/citation rules, submission
contents, page/time limits, or grading-critical rubric conditions.

Do not rewrite a hard requirement into a softer fallback, preference, human
review item, or acceptable risk. If the current evidence is insufficient to meet
the requirement, the pipeline must represent that as a blocker.

In the current execution plan file, record hard requirements in a dedicated
constraint block:

```yaml
required_spec_constraints:
  - id: report_format_style
    source: references/project_announce.pdf.txt:178
    requirement: "must use the official LaTeX style file; do not use preprint"
    applies_to:
      - draft/report.pdf
    required_evidence:
      - "render source/log proves the required style file was used"
    status: blocked
    blocker_type: external_blocker
    fallback_allowed_for_final: false
```

Planning rules:

- For every hard requirement, preserve source evidence and required verification
  evidence. A later stage brief must be able to trace back to the exact
  constraint.
- If the requirement can be satisfied with available materials, include the
  materials in allowed reads and make the required evidence part of stage
  quality criteria.
- If the requirement cannot currently be satisfied, mark the affected final
  deliverable blocked by `needs_user_input`, `manual_only`, or
  `external_blocker`. Do not mark it as a final deliverable that can pass via
  fallback.
- Fallbacks are allowed only for optional implementation mechanics or for
  clearly named preview/debug artifacts. A fallback output must not satisfy or
  replace a final deliverable governed by `fallback_allowed_for_final: false`.
- The only way to relax a hard requirement is new authoritative evidence: an
  updated spec, instructor/user-supplied file/instruction that explicitly
  changes the requirement, or a user decision to produce a non-final preview.

For mixed assignments, keep one ordered stage plan. Use stage ids and headings
to group sub-pipelines instead of creating independent uncoordinated plans.
Within a stage, `tools` is composable: use one tool for simple stages and
multiple tools when the same executor must combine capabilities to produce one
coherent stage artifact. `primary_tool` declares the stage's lead contract.
Legacy `tool: <path>` is accepted only as shorthand for
`primary_tool: <path>` plus `tools: [<path>]`; new plans should write the
expanded fields so supporting tools are auditable.

Complete `pipeline_design.md` or `repair_pipeline_design.md`. It is the
single-assignment execution plan:

```markdown
# Pipeline: <COURSE> <assignment>

## Metadata
repo_root: <absolute path from [A2]>

## Output
- mode: mixed (code + doc_prose + slides)
- deliverables: [notebook.ipynb, report.pdf, ...]

## Constraints
- [quantifiable constraints from spec]
- [relevant syllabus constraints distilled into spec/rubric/review evidence]
- [user intent / non-negotiables from the current terminal agreement]
- [hard spec constraints, if any, with required_spec_constraints]

## Stages

### Stage 1 - Notebook Execution
- id: stage_01_notebook
- primary_tool: sub-skills/tools/code-writer.md
- tools:
  - sub-skills/tools/code-writer.md
  - sub-skills/tools/test-runner.md
- tool_roles:
  - code-writer: create the notebook/source artifact and executable cells
  - test-runner: execute validation commands and preserve run evidence
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
  - test_report.md
  - test_report.json
- quality_criteria:
  - notebook executes from a clean kernel
  - test_report.json records validation commands, exit codes, and pass/fail state
  - no fabricated metrics; report metrics must come from actual notebook output
- human_blockers:
  - dataset choice if the spec allows multiple datasets and user has not chosen

### Stage 2 - Report Draft
- id: stage_02_report
- primary_tool: sub-skills/tools/writing-helper.md
- tools:
  - sub-skills/tools/writing-helper.md
  - sub-skills/tools/humanizer.md
- tool_roles:
  - writing-helper: draft the report from spec, rubric, user intent, and metrics
  - humanizer: post-process prose because this stage declares `post-process: humanize`
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

## Human Review Items
- ...

## Pipeline Review Status
- status: awaiting_user_review
- review_requested_at: <UTC timestamp>
- approved_at: null
- approved_by: null
- approval_summary: null
```

Do not write or require `task_profile.yaml`. The orchestrator reads
`spec.md + explore_context.md + terminal agreement + execution plan` directly.
For clean entries, the terminal agreement is `alignment_brief.md` and the
execution plan is `pipeline_design.md`. For retained entries, the terminal
agreement is `repair_plan.md` and the execution plan is
`repair_pipeline_design.md`.

The execution plan must explicitly incorporate the current terminal agreement.
At minimum, its constraints, stage goals, human blockers, delegated decisions,
and final review items must reflect the confirmed `alignment_brief.md` or
`repair_plan.md`. If a planned stage cannot be justified from `spec.md`,
`investigation/explore_context.md`, `investigation/rubric.md`,
`investigation/review_a.json`, the current terminal agreement, or explicitly
allowed preserved references, do not include that stage. Canvas-native content
is not hidden background when its preserved
`references/canvas_native/**/source.json` path is listed in the stage brief's
allowed reads. Raw `canvas/*.json` reads are recovery or fallback exceptions
and must be named explicitly when no preserved source copy exists.

The execution plan is the task-level plan for the Main Agent and
task-orchestrator. It is not handed directly to executor subagents. The
orchestrator converts each delegated stage into
`stage_briefs/<stage_id>_executor.md` plus reviewer briefs when review is
enabled.

### [C5] Pipeline Review Gate

User-interaction phase #2.

After writing `pipeline_design.md` or `repair_pipeline_design.md`, do **not** invoke
`tasks/task-orchestrator.md`, do not dispatch executor/reviewer children, and do
not run stage tools. Instead, present a user-facing approval brief that is
readable on its own. Do not merely point the user at the execution plan file;
the Main Agent must explain the plan in chat well enough that the user can
approve or reject it without opening the Markdown file.

The approval brief must include the complete substance of the pipeline, in a
clean review format:

1. **Context and goal**
   - Course + assignment.
   - Workbench path.
   - Terminal agreement and execution plan paths as references only.
   - User-confirmed goal and non-negotiables.
2. **Planned outputs**
   - Output mode.
   - Every final deliverable path/name.
   - Intermediate evidence or logs that matter for grading/verification.
3. **Constraints**
   - Assignment constraints from `spec.md`.
   - Relevant rubric/syllabus constraints.
   - User constraints from the current terminal agreement.
   - Forbidden actions, especially Canvas submission behavior.
4. **Full stage plan**
   - For every stage, show: stage id, goal, primary tool, full tools list, tool
     roles, delegate mode, allowed reads, writes, review settings, retry limit,
     quality criteria, and human blockers.
   - If a stage is `delegate: main-agent`, explain why it is simple enough for
     inline execution. If there is no clear reason, revise the pipeline before
     asking for approval.
5. **How task-orchestrator will execute it**
   - Ground this section in `tasks/task-orchestrator.md`; do not summarize from
     memory or use generic "subagents will run" wording.
   - State that `task-orchestrator.md` will first verify
     `Pipeline Review Status.status: approved_for_orchestration`.
   - It will generate `stage_briefs/<stage_id>_executor.md` and reviewer briefs.
   - It will dispatch executor subagents for `delegate: subagent` stages.
   - It will record child dispatches in
     `stage_reviews/child_dispatch_ledger.json`.
   - For reviewed stages, it will run spec-compliance review first, then quality
     / code review only after spec compliance passes.
   - If review finds blocking auto-fixable issues, it will send a bounded fix
     brief back through the executor loop while retries remain.
   - It will write `stage_results/`, `stage_reviews/`,
     `verification_checklist.md`, `verification.log`, and final `result.json`.
   - It will not submit to Canvas.
6. **Approval risks and review items**
   - Anything the user must check before execution.
   - Any missing external resource, manual-only item, or accepted fallback.
   - Any part of the plan that may be expensive, slow, or likely to require
     iteration.

Keep the approval brief concise enough to read, but do not omit a stage or hide
execution mechanics behind "see markdown." If the pipeline is long, use a
numbered stage table plus short per-stage details. The approval brief is the
review surface; the execution plan file is the audit artifact.

Use this response shape:

```markdown
**Pipeline Approval Brief**

**Goal**
- ...

**Deliverables**
- ...

**Non-Negotiables**
- ...

**Execution Stages**
| # | Stage | Tools | Delegate | Writes | Reviews | Retry | Human blockers |
|---|---|---|---|---|---|---|---|
| 1 | ... | primary: ...; supporting: ... | subagent | ... | spec + quality | 1 | ... |

**Stage Details**
1. `<stage_id>` — <goal>
   - Reads: ...
   - Writes: ...
   - Quality criteria: ...
   - Why this delegate mode: ...

**How Orchestration Will Work If Approved**
- Validate `Pipeline Review Status.status == approved_for_orchestration`.
- Generate executor/reviewer briefs from this pipeline.
- Dispatch executor subagents for delegated stages.
- Run spec review before quality/code review.
- Iterate executor fixes while retries remain.
- Verify deliverables and write `result.json`.
- Canvas submission will not happen here.

**Approval Risks / Manual Review Items**
- ...

你要怎么处理?
- 通过，进入 task-orchestrator 执行
- 先修改 pipeline（告诉我改哪里）
- 暂停，不执行
```

If the user asks to modify the pipeline:

- If the change alters intent, selected approach, design skeleton,
  non-negotiables, or human-owned facts, return to `[B4]`, update and reconfirm
  the current terminal agreement, then rerun `[C]`.
- If it changes only execution details within the confirmed brief, append the
  request to `investigation/user_notes.md`, update the current execution plan
  file, keep `Pipeline Review Status.status: awaiting_user_review`, and ask for
  review again.

If the user pauses, write `result.json` with `status: "pipeline_ready"` and
`--deferred-to-next-run`:

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/<COURSE>/<HWID>" \
  --status pipeline_ready \
  --course "<COURSE>" \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --assignment-name "<assignment_name>" \
  --deliverable "data/homework/<COURSE>/<HWID>/<pipeline_design.md|repair_pipeline_design.md>" \
  --human-review-item "Pipeline awaits user approval before task-orchestrator execution" \
  --note "pipeline generated; task-orchestrator not run" \
  --deferred-to-next-run \
  --allow-missing-deliverables
```

If the user approves execution, update `pipeline_design.md` or
`repair_pipeline_design.md`:

```text
## Pipeline Review Status
- status: approved_for_orchestration
- review_requested_at: <existing timestamp>
- approved_at: <UTC timestamp>
- approved_by: user
- approval_summary: <one-line confirmation>
```

Then hand off to `tasks/task-orchestrator.md` with the workbench path. This is
a new workflow phase owned by `task-orchestrator.md`; it is not part of
`assignment-workflow-planner.md` execution.

## Output Format

Use the selected plan item's `canvas_url` or `canvas/assignment.json.html_url`;
never reconstruct a host-specific Canvas URL from course and assignment IDs.

After `[C5]`:

```markdown
## <COURSE> <assignment name>

**Pipeline:** `data/homework/<COURSE>/<HWID>/<pipeline_design.md|repair_pipeline_design.md>`
**Status:** pipeline_ready / skipped / error
**Canvas URL:** <assignment html_url, or "not available" if Canvas did not provide one>

Human review items:
- Review the execution plan before orchestration.
- ...

Next step:
- If approved, run `tasks/task-orchestrator.md` with this workbench.
```
