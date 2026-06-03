---
name: task-orchestrator
description: Execute a per-assignment pipeline from a workbench containing spec.md and pipeline_design.md. Called by do-homework after reconnaissance and user supplement checkpoint. Do not invoke directly from user input.
---

# task-orchestrator

The core M3 execution mechanism. Given a single-assignment workbench and the
tools index, execute the pipeline that `do-homework [C]` designed.

This task does **not** infer the assignment from raw Canvas fields and does
**not** consume `task_profile.yaml`. The source of truth is:

```text
work_dir/
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── rubric.md
│   ├── review_a.json
│   ├── user_notes.md      # optional
│   └── user_scope.md      # optional
└── pipeline_design.md
```

`spec.md` is the standardized Canvas Generic reconnaissance report.
`pipeline_design.md` is the assignment-specific execution plan. Older tools may
still read `problem.md`, but the orchestrator should always read `spec.md` and
`pipeline_design.md` first.

## When To Invoke

Only after `do-homework` has:

1. Resolved `course_id` and `assignment_id`.
2. Built the workbench.
3. Completed Canvas Generic Stage 1-5 reconnaissance.
4. Asked the user for supplements at `[B]`.
5. Written or updated `pipeline_design.md` at `[C]`.

End users never call this directly. They say "帮我完成 hw3", which routes to
`do-homework`.

## Required Workbench

```text
work_dir/
├── canvas/
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   └── review_a.json
├── pipeline_design.md
├── draft/
├── verification_checklist.md
├── verification.log
└── result.json
```

Before executing, check:

- `spec.md` exists and clearly states deliverables.
- `pipeline_design.md` exists and starts with `Output mode: ...`.
- `investigation/review_a.json` exists and has `verdict: "proceed"`, unless
  `do-homework` explicitly recorded user-supplied recovery material.
- `references/` contains required reachable materials, or
  `investigation/unreachable.txt` explains missing resources.

If these checks fail, return to `do-homework` with `status: failed`. Do not run
tools against an ungrounded assignment.

## Pipeline Design Format

`pipeline_design.md` follows the stage-based format defined in
`docs/skills-architecture-spec.md §5`. Each stage declares:
tool, lang, type, reads, writes, verify, review, post-process, fallback, min_quality.

The format is written by `do-homework [C]` — the orchestrator reads and executes it.
Do not redesign the format here.

## Execution Flow

### Step 1 - Read The Workbench

**Path discovery:** Before reading any skill files, determine the skill directory:

1. Read `pipeline_design.md` and look for `repo_root:` in the metadata section
2. If found, set `SKILLS_DIR = repo_root + "/sub-skills/tools/"`
3. If not found, infer: `REPO_ROOT = WORK_DIR/../../..` (3 levels up from data/homework/COURSE/HWID)
4. If inference fails, run: `git -C "$WORK_DIR" rev-parse --show-toplevel`
5. All skill file references use `SKILLS_DIR` as the base path

The `_index.md` is at `SKILLS_DIR/_index.md`.

Read, in order:

```text
spec.md
pipeline_design.md
investigation/rubric.md
investigation/review_a.json
investigation/user_notes.md      # if present
investigation/user_scope.md      # if present
problem.md                       # compatibility only
SKILLS_DIR/_index.md          # path discovered above
```

Do not read `canvas/assignment.json.description` as the problem statement. It is
metadata only.

### Step 2 - Map Stages To Tools

Use `pipeline_design.md` "Tool Mapping" plus `sub-skills/tools/_index.md`.

Common mappings:

| Stage kind | Tool |
|---|---|
| literature search / references | `paper-search.md` |
| prose / report / reflection | `writing-helper.md` |
| chart / figure | `figure-maker.md` |
| markdown or LaTeX to PDF | `pdf-renderer.md` |
| code / notebook / source files | `code-writer.md` |
| tests / execution report | `test-runner.md` |
| slides / deck | `slide-maker.md` |

If a mapped tool does not exist, stop and return:

```yaml
status: failed
failures:
  - tool: <missing tool>
    error: "tool not registered in sub-skills/tools/_index.md"
```

Do not fake an unsupported capability.

### Step 3 - Execute Stages

Execute stages in the order specified by `pipeline_design.md`. Tools communicate
through files inside `work_dir`.

General rules:

- Write all deliverables under `draft/` unless the tool contract says otherwise.
- Preserve raw Canvas snapshots under `canvas/`.
- Preserve fetched source material under `references/`.
- Stop on first tool failure.
- If rerun from a user revision, reuse `spec.md` and `references/`; update
  `pipeline_design.md` and regenerate draft artifacts.

### Step 4 - Verify Deliverables

Before returning:

- Check every deliverable named in `pipeline_design.md` exists or is listed as a
  human/manual item.
- Sanity checks by type:
  - `pdf`: file is >1 KB and magic bytes are `%PDF`.
  - `pptx`: file is a valid zip with `[Content_Types].xml`.
  - `html`: file is non-empty and has expected slide/page structure if a deck.
  - `ipynb`: valid JSON with notebook cells.
  - `zip`: valid zip archive.
  - `md` / `txt`: non-empty UTF-8.
  - code: parses or tests run when possible.

Write:

```text
verification_checklist.md
verification.log
```

`verification_checklist.md` contains checks grounded in `spec.md`,
`investigation/rubric.md`, and `pipeline_design.md`.

`verification.log` uses measured lines:

```text
PASS | <check> | measured: <value>
FAIL | <check> | measured: <value>
SKIP | <check> | reason: human_review
```

### Step 5 - Return Summary

Return a structured summary to `do-homework`:

```yaml
status: success | partial | failed
output_mode: mixed
deliverables_produced:
  - path: data/homework/<COURSE>/<HWID>/draft/<file>
    size_bytes: 245678
    format: pdf
intermediates:
  - data/homework/<COURSE>/<HWID>/draft/draft.md
tools_used:
  - writing-helper
  - pdf-renderer
verification_log_path: data/homework/<COURSE>/<HWID>/verification.log
human_review_items:
  - "Group ID needs to be filled in before submission"
failures: []
```

`do-homework` uses this summary at `[E]` and writes `result.json`.

## Output Modes

Use Canvas Generic output vocabulary:

| Mode | Meaning |
|---|---|
| `doc_prose` | essay, report, critique, reflection, text submission |
| `pdf_annotated` | annotated reading PDF, highlights, answer blanks |
| `pdf_typed` | typed problem-set / math / formal solution PDF |
| `code` | source files, notebook, package, starter-code completion |
| `form_answers` | short answer body for online text entry |
| `slides` | presentation deck |
| `mixed` | multiple output shapes |

Real examples:

- **DSAA2011 Project**: `mixed` - notebook/code + report PDF + slides PDF +
  requirements + zip package.
- **UCUG1505 FINAL project**: `mixed` - creative code + documentation + manual
  video demo.

## Safety Rules

1. **No tool runs without `do-homework [B]` approval.**
2. **Do not invent missing source material.** If `spec.md` or `references/` is
   incomplete, return to `do-homework`.
3. **Do not use `assignment.description` as the prompt.**
4. **Do not silently alter deliverables.** `pipeline_design.md` controls the
   target artifacts.
5. **No writes outside `work_dir`** except explicit renderer outputs already
   named in `pipeline_design.md`.
6. **No placeholder deliverables.** Ban `[PROBLEM N]`,
   `[TODO: align with actual project spec]`, and `[此处由小组成员填入选题]`.
7. **Surface `[CLARIFICATION NEEDED: ...]` markers** in the returned
   `human_review_items`.

## Pitfalls

1. **Don't make this a free-form classifier again.** Classification happens in
   problem-extractor Stage 5 and is finalized by `do-homework [C]`.
2. **Don't resurrect `task_profile.yaml`.** It was a transitional idea; the
   workbench plus `pipeline_design.md` is the contract.
3. **Don't bake course-specific logic here.** Course quirks belong in `spec.md`,
   `pipeline_design.md`, or future course overrides.
4. **File paths with Chinese / spaces are common.** Always quote paths in shell
   calls.

## MVP Scenarios Validated

The old fixed chains validated AutoStudy's tool base:

| type | Assignment | Tool chain | Deliverable |
|---|---|---|---|
| `paper` | DLED3020 Paper Critique | paper-search -> writing-helper -> pdf-renderer | `final.pdf` |
| `slides` | UCUG1077 Group presentation | slide-maker | `slides.pdf` |
| `math` | DSAA2043 Lab-Assignment 1 | writing-helper -> pdf-renderer | `solution.pdf` |
| `lab` | DSAA2012 Project Report | code-writer -> test-runner -> writing-helper -> pdf-renderer | `src/` + `report.pdf` |

The next development step is to validate the new Canvas Generic-style
`spec.md -> pipeline_design.md -> draft/` flow on DSAA2011 Project and UCUG1505
FINAL project.
