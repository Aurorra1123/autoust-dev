---
name: task-orchestrator
description: Heuristically compose a pipeline of tools to complete a heterogeneous task (report / slides / video / code / proof). Called by do-homework / write-notes / weekly-plan. Do not invoke directly from user input — the calling task must first produce a task profile.
---

# task-orchestrator

The core M3 mechanism. Given a **task profile** and the **tools index**, decide which tools to run, in what order, and execute the pipeline. Reusable across do-homework, write-notes, and future tasks.

## When to invoke

- A calling task (e.g. `do-homework`) has already:
  1. Identified the user's intent
  2. Read the assignment description / lecture slides / etc.
  3. Got user approval to proceed
- That task constructs a **task profile** (see schema below) and hands it to this orchestrator

This task is **not user-facing**. End-users say "帮我完成 hw3", which routes to `do-homework`, which calls into here. Don't try to expose this directly.

## Task profile schema

The calling task hands you a structured description:

```yaml
type: paper | slides | math | lab | video | notes | mixed
deliverables:
  - path: data/homework/<course>/<hw>/final.pdf  # what file to produce
    format: pdf | pptx | html | mp4 | ipynb | md
required_capabilities:    # verbs from tools/_index.md
  - search_papers
  - write_essay
  - make_figure
  - render_pdf
deadline: 2025-12-13T15:59:00Z   # ISO 8601, may be null
scope:
  course: DSAA2043
  course_id: 2151
  assignment: Homework 3
  assignment_id: 12345
constraints:
  word_count: 1500       # optional, type-specific
  citation_style: APA    # optional, type-specific
  language: en | zh | mixed
user_overrides:          # optional, things the user said specifically
  - "skip question 4, I'll do it myself"
  - "no charts, just text"
work_dir: data/homework/DSAA2043/hw3/
```

The `work_dir` is the orchestrator's filesystem playground. All intermediates and the final deliverable live there.

## Execution flow

### Step 1: Capability matching

Read `sub-skills/tools/_index.md`. For each verb in `required_capabilities`, find the matching tool:

```
required: [search_papers, write_essay, make_figure, render_pdf]
            ↓                ↓             ↓             ↓
tools:   paper-search    writing-helper  figure-maker  pdf-renderer
```

If a required capability has no matching tool, **stop and tell the calling task** "I can't do `search_papers` yet — no tool registered." Don't try to fake it.

### Step 2: Pipeline composition

Order tools by their data dependencies. Use this rough topology:

```
search_papers, make_figure, parse_pdf  →  (parallel, produce intermediates)
                  ↓
write_essay / solve_proof / write_code  →  (consumes intermediates)
                  ↓
render_pdf / render_slides / edit_video →  (produces final deliverable)
```

Concretely for the four MVP pipelines (see `tools/_index.md` "Scenario → Tool chain"):

**Paper pipeline** (type: paper):
```
1. paper-search    → work_dir/references.bib + references.json
2. figure-maker    → work_dir/figures/fig_N.pdf  (parallel-eligible; opt)
3. writing-helper  → work_dir/draft.md  (consumes references + figures)
4. pdf-renderer    → work_dir/final.pdf
```

**Slides pipeline** (type: slides):
```
1. figure-maker    → work_dir/figures/...  (opt)
2. slide-maker     → work_dir/slides.tex → work_dir/slides.pdf  (one tool, two phases: write .tex + compile via tectonic)
```

**Math pipeline** (type: math):
```
1. writing-helper  → work_dir/draft.md  (Markdown with inline LaTeX math via $...$)
2. pdf-renderer    → work_dir/solution.pdf
```

**Lab pipeline** (type: lab):
```
1. code-writer     → work_dir/src/*.py + work_dir/src/test_*.py
2. test-runner     → work_dir/test_report.md
3. writing-helper  → work_dir/draft.md  (lab report, embeds test_report excerpt)
4. pdf-renderer    → work_dir/report.pdf
```

**Video pipeline** (type: video):
Out of scope for AutoStudy MVP. A separate video skill will handle this. If a calling task constructs a profile with `type: video`, return early with a friendly "video pipeline lives in a different skill" message.

### Step 3: Execute

For each tool in order:

1. Read the tool's `.md` file (`sub-skills/tools/<name>.md`)
2. Construct the actual invocation using the tool's "Invocation" section
3. Run it (typically `Bash` or `Write` then `Bash`)
4. Verify the expected output file exists and is non-empty
5. If failure: log the error to `work_dir/orchestrator.log`, stop, report to caller

**Crucial: tools communicate via files, not return values.** Each tool reads its inputs from disk and writes outputs to disk. This makes the pipeline:
- Inspectable (the user can `ls work_dir/` and see what's done)
- Resumable (if step 3 fails, step 1-2 results are still there)
- Replaceable (the user can hand-edit `draft.md` between writing-helper and pdf-renderer)

### Step 4: Verify deliverable

Before returning to the calling task:

- Check every path in `deliverables` exists and is non-empty
- Sanity checks by type:
  - `pdf`: file is > 1 KB, magic bytes are `%PDF`
  - `pptx`: file is a valid zip with `[Content_Types].xml`
  - `mp4`: ffprobe returns a duration > 0
  - `md`: file is non-empty UTF-8
- If any check fails, report which step likely caused it (last successful intermediate)

### Step 5: Return summary

Hand back to the calling task a structured summary:

```yaml
status: success | partial | failed
deliverables_produced:
  - path: data/homework/DSAA2043/hw3/final.pdf
    size_bytes: 245678
    pages: 12   # if applicable
intermediates:
  - work_dir/references.json
  - work_dir/figures/fig1.pdf
  - work_dir/draft.md
tools_used:
  - paper-search
  - figure-maker
  - writing-helper
  - pdf-renderer
duration_sec: 87
failures: []   # or list of {tool, error}
```

The calling task uses this summary to present the result to the user.

## Heuristics for type inference

If the calling task is unsure of the task type, use these signals from the assignment description:

| Signals in description / rubric | Inferred type |
|---|---|
| "essay", "report", "review", "critique", "paper", "annotated bibliography", "reflection" | `paper` |
| "presentation", "slides", "PPT", "deck", "pitch", "demo" | `slides` |
| "prove", "show that", "derive", "complexity analysis", math expressions (`$...$` density) | `math` |
| "implement", "code", "write a function", "OJ", "submit code", `.py` / `.cpp` / `.ipynb` files | `lab` |
| "video", "screencast", "demo recording", "summary video" | `video` (→ defer to video skill) |
| "notes", "study guide", "summarize the lecture" | `notes` (→ falls back to `paper` pipeline) |
| Multiple of the above | `mixed` — pick the highest-weight one or run sub-orchestrations |

Real examples from the 4 MVP validation runs:

- **DLED3020 Paper Critique** — description says "critically evaluate this paper" → `paper` (essay structure, citation_style=APA)
- **UCUG1077 Group presentation** — submission_types includes "online_upload" + description mentions "PPT" → `slides`
- **DSAA2043 Lab-Assignment 1** — title contains "Lab" + description has "prove that... Big-O" → split: `math` for the proof portion, `lab` for the code portion. Default to `math` if mixed and rubric weights theory > implementation.
- **DSAA2012 Project Report** — description says "report" + "implementation" + "experiments" → `lab` (because the code is the core; the report is one section of the deliverable)

Confidence < 0.7? Hand back to caller and ask the user explicitly.

## Safety rules

1. **No tool runs without user approval at the calling-task level.** The orchestrator assumes the calling task has already done [B] confirmation.
2. **Stop on first failure, do not silently fall back.** A missing capability or a tool error must be surfaced, not papered over.
3. **No tool may write outside `work_dir`** (one exception: `pdf-renderer` writing the final PDF to a path explicitly in `deliverables`).
4. **Don't cache stale intermediates.** If the calling task re-invokes orchestrator with the same work_dir, regenerate everything unless the caller passes `resume: true`.

## Pitfalls

1. **Don't make this an `Agent` tool call (sub-agent).** Sub-agents are expensive; the orchestrator is plain markdown + the main agent executing it. Keep it cheap.
2. **Don't extend capability vocabulary ad-hoc.** New verbs go into `_index.md` first, then tools reference them.
3. **Don't bake course-specific logic here.** If "DSAA2043 wants final.pdf in single column" — that goes in `do-homework.md`'s task-profile construction, not here.
4. **File paths with Chinese / spaces are common** (see `docs/PITFALLS.md` #10). Always quote paths in shell calls.

## MVP scenarios validated

The orchestrator was validated end-to-end on 4 real HKUST(GZ) assignments:

| type | Assignment | Tool chain | Deliverable |
|---|---|---|---|
| `paper` | DLED3020 Paper Critique | paper-search → writing-helper → pdf-renderer | `final.pdf` |
| `slides` | UCUG1077 Group presentation | slide-maker (tectonic) | `slides.pdf` |
| `math` | DSAA2043 Lab-Assignment 1 | writing-helper → pdf-renderer | `solution.pdf` |
| `lab` | DSAA2012 Project Report | code-writer → test-runner → writing-helper → pdf-renderer | `src/` + `report.pdf` |

Earlier smoke test (M3 foundation, before MVP) used `type: notes` with only `render_pdf` to validate the three-layer architecture skeleton. That trace lives at `data/homework/test/`.

## Future: parallelization

When two tools have no data dependency (e.g. `make-figure` and `paper-search` in the report pipeline), they can run in parallel. M3 first version runs sequential; parallel comes later when we add runtime detection (M5a, see `docs/ROADMAP.md`).
