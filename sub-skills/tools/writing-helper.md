---
name: writing-helper
description: Draft structured academic prose (essay / report / reflection) from spec.md + pipeline_design.md + rubric. The agent itself writes the markdown; this file is the spec + checklist. Output is pandoc-friendly markdown that pdf-renderer can convert to PDF.
---

# writing-helper

The paper/report/reflection workhorse. Reads the assignment workbench
(`spec.md`, `pipeline_design.md`, rubric, references, and user supplements),
then produces `draft.md` in the same `work_dir`. **The agent writes the prose
directly** — there's no subprocess and no separate LLM call. This file is the
spec the agent follows.

## Capabilities

- `write_essay` — produce structured academic markdown from assignment context

## Inputs / Outputs

```
Input:  <work_dir>/spec.md                (PRIMARY: standardized reconnaissance report)
        <work_dir>/pipeline_design.md     (deliverables, prose stage, constraints, verification plan)
        <work_dir>/investigation/rubric.md
        <work_dir>/references/            (fetched readings/spec text/data, if any)
        <work_dir>/problem.md             (compatibility summary; read after spec.md)
        <work_dir>/investigation/user_notes.md  (optional)
        <work_dir>/investigation/user_scope.md  (optional)
        <work_dir>/canvas/assignment.json (metadata only: due_at, rubric, points, submission_types)
        <work_dir>/references.bib         (optional, from paper-search)
        <work_dir>/figures/*.{pdf,png}    (optional, from figure-maker)
Output: <work_dir>/draft.md               (pandoc-friendly markdown with YAML frontmatter)
```

**Read `spec.md` first, then `pipeline_design.md`, rubric, references, user
supplements, and finally `problem.md`, completely, before writing anything.**
`spec.md` explains which source is the main spec and which sources are
supporting context. `pipeline_design.md` explains what prose artifact this tool
is responsible for. `problem.md` is only a compatibility summary. If `spec.md`
or `pipeline_design.md` is missing or thin, refuse to proceed and write a single
`[CLARIFICATION NEEDED: reconnaissance or pipeline design is incomplete]`
marker — do not pad it with template content.

## Setup

No external dependencies. Pure agent-authored markdown.

The `draft.md` must include a frontmatter block that pdf-renderer can pass through:

```yaml
---
title: <Assignment name>
author: <leave blank — student fills>
date: \today
documentclass: ctexart
geometry: margin=1in
CJKmainfont: PingFang SC
monofont: Menlo
---
```

## Invocation (decision flow)

The agent runs this entirely in-context — no shell commands required for content generation. Follow this order:

### Step 1 — Pick the structure from the pipeline and rubric

Read `spec.md`, `pipeline_design.md`, `investigation/rubric.md`, and relevant
files under `references/` end-to-end. Match the prose stage against the three
supported structures:

| Structure | Cues in problem.md / rubric | Typical sections |
|---|---|---|
| `essay` | "argue", "critique", "analyze", "thesis", "evaluate" | Intro (with thesis) -> 2-4 body paragraphs -> Conclusion |
| `report` | "results", "methodology", "discussion", "lab", "experiment" | Abstract -> Introduction -> Methods -> Results -> Discussion -> Conclusion -> References |
| `reflection` | "reflect", "experience", "learned", "personal" | Context -> What happened -> What I learned -> Implications |

If multiple cues match, follow `pipeline_design.md`. If
`investigation/user_scope.md` exists, write only the requested sections.

### Step 2 — Honor length and citation style

Take length, language, citation style, required sections, and deliverable format
from `spec.md`, `pipeline_design.md`, and `investigation/rubric.md`.

- `length: ~1500 words` -> aim +/-10%. Each section gets a rough budget.
- `citation_style: APA` -> in-text `(Author, 2024)`, end-of-doc `## References`.
- `citation_style: IEEE` -> in-text `[1]`, end-of-doc `## References`.
- `citation_style: none` -> no citations; do not fake them.

### Step 3 — Use `references.bib` if it exists

If `<work_dir>/references.bib` exists (from paper-search), pull citations from there. Don't invent references. If you need a reference the bib doesn't have, write `[CITATION NEEDED: <description>]` inline — `pdf-renderer` will surface this so the user / paper-search can fill it later.

### Step 4 — Embed figures if any

If `<work_dir>/figures/fig_N.{pdf,png}` exist (from figure-maker), reference them in the markdown:

```markdown
![Caption text](figures/fig_1.pdf){width=60%}
```

Cite the figure in-text (`see Figure 1`).

### Step 5 — Write the draft

Produce `<work_dir>/draft.md`. Quality bar (non-negotiable):

- **Every assertion is grounded in `spec.md`, `references/`, and
  `pipeline_design.md`.** If the assignment asks "critique this paper X", the
  draft engages with X's actual arguments, not with a generic "the paper makes
  some claims" gloss.
- **Specific problems get specific answers.** If `spec.md` lists Problem 1
  (prove BST height bound), Problem 2 (solve recurrence), Problem 3 (DP table),
  the draft has a section per problem with a real proof / derivation — not a
  `[PROBLEM N]` placeholder.
- **For papers/critiques**: name the paper. Name its authors. Quote (with citation) at least one specific claim from the paper. Generic "this paper discusses..." sentences fail the quality bar.
- **No `[PROBLEM N]` / `[TODO: ...]` / `[此处填入...]` placeholders.** The only acceptable markers:
  - `[CITATION NEEDED: <topic>]` — when `references.bib` lacks a needed entry. Surfaced at [E].
  - `[CLARIFICATION NEEDED: <specific question about spec.md or user_scope.md>]` — when the grounded workbench is genuinely ambiguous on a specific point. Surfaced at [E].
- Every section has a topic sentence.
- No "As an AI" / "I will discuss" filler.
- Use rubric criteria as section emphasis (if rubric says "30% argument quality", make the argument explicit).
- Match the user's chosen language (`en` / `zh`) — if `zh`, the draft is in Chinese, but the YAML frontmatter stays English keys.

### Step 6 — Hand off

After writing, the orchestrator calls `pdf-renderer` with `<work_dir>/draft.md` → `<work_dir>/final.pdf`. Don't render the PDF from writing-helper itself.

## What this tool is NOT for

- ❌ Generating slides — use `slide-maker.md`
- ❌ Writing code — use `code-writer.md`
- ❌ Doing the LaTeX math itself — `pdf-renderer` handles math when the markdown source uses `$...$`
- ❌ Researching citations — use `paper-search.md` first, then this tool reads `references.bib`

## Pitfalls

1. **Don't fake citations.** If you write `(Smith, 2023)` without a real `references.bib` entry, the bibliography is broken. Use `[CITATION NEEDED]` placeholders instead.
2. **Match the language.** If `spec.md` is in Chinese and rubric mentions "中文写作", the draft must be Chinese — `pdf-renderer` ctexart handles both, but mismatched language gets points off.
3. **`spec.md` and `pipeline_design.md` are the source of truth, NOT `assignment.description`.** The description is HTML and often just a file link or empty. Reading it directly produces "the assignment is about X" template content. Always read the workbench files generated by `problem-extractor`.
4. **`investigation/user_scope.md` is binding.** If the user said "only problem 2 and 4", do NOT write 1 and 3 even if the rubric says they're required. The user knows what they want.
5. **Don't auto-conclude with "In conclusion, ..." for short reflections.** Reflections are personal — let the structure follow the rubric, not a rigid 5-paragraph template.
6. **Frontmatter `date: \today`** — keep the backslash; pdf-renderer's LaTeX will resolve it. Don't replace with a literal date unless the user asked.
7. **Engage with specific content.** A paper critique that doesn't name the paper, its authors, or quote a single sentence from it is failing the quality bar regardless of word count.
8. **If `spec.md` or `pipeline_design.md` is missing or thin**, STOP. Write a single-line draft.md containing `[CLARIFICATION NEEDED: reconnaissance or pipeline design was incomplete]` and return. Do not pad with template content.
