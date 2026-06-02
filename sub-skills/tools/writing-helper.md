---
name: writing-helper
description: Draft structured academic prose (essay / report / reflection) from spec.md/problem.md + rubric. The agent itself writes the markdown; this file is the spec + checklist. Output is pandoc-friendly markdown that pdf-renderer can convert to PDF.
---

# writing-helper

The paper/report/reflection workhorse. Reads a `task_profile.yaml` + `spec.md` / `problem.md`, produces `draft.md` in the same `work_dir`. **The agent writes the prose directly** — there's no subprocess, no LLM call. This file is the spec the agent follows.

## Capabilities

- `write_essay` — produce structured academic markdown from assignment context

## Inputs / Outputs

```
Input:  <work_dir>/task_profile.yaml      (constraints: length, citation_style, language, partial_scope)
        <work_dir>/spec.md                (PRIMARY: source-by-source assignment context)
        <work_dir>/problem.md             (compatibility problem text from problem-extractor)
        <work_dir>/canvas/assignment.json (metadata only: due_at, rubric, points, submission_types)
        <work_dir>/references.bib         (optional, from paper-search)
        <work_dir>/figures/*.{pdf,png}    (optional, from figure-maker)
Output: <work_dir>/draft.md               (pandoc-friendly markdown with YAML frontmatter)
```

**Read `spec.md` first, then `problem.md`, completely, before writing anything.** `spec.md` shows where the assignment was found and which sources are main spec vs supporting context; `problem.md` is the compatibility view older tools consume. If both are missing or thin, refuse to proceed and write a single `[CLARIFICATION NEEDED: problem statement was not grounded; do-homework [A3] failed]` marker — do NOT pad it with template content.

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

### Step 1 — Pick the structure from the rubric

Read `spec.md` and `problem.md` end-to-end. Then read `canvas/assignment.json` plus `investigation/rubric.md` if present. Match the assignment against the three supported structures:

| Structure | Cues in problem.md / rubric | Typical sections |
|---|---|---|
| `essay` | "argue", "critique", "analyze", "thesis", "evaluate"  | Intro (with thesis) → 2-4 body paragraphs → Conclusion |
| `report` | "results", "methodology", "discussion", "lab", "experiment" | Abstract → Introduction → Methods → Results → Discussion → Conclusion → References |
| `reflection` | "reflect", "experience", "learned", "personal" | Context → What happened → What I learned → Implications |

If multiple cues match, default to `essay`. If `partial_scope` is set in `task_profile.yaml`, write only the requested sections.

### Step 2 — Honor length and citation style

- `length: ~1500 words` → aim ±10%. Each section gets a rough budget (essay: 200/1000/300; report: 100/300/300/400/300/200).
- `citation_style: APA` → in-text `(Author, 2024)`, end-of-doc `## References` with hanging indent.
- `citation_style: IEEE` → in-text `[1]`, end-of-doc `## References` with numeric list.
- `citation_style: none` → no citations; don't fake them.

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

- **Every assertion is grounded in `spec.md` / `problem.md`.** If the assignment asks "critique this paper X", the draft engages with X's actual arguments (as found in the downloaded reference sections), not with a generic "the paper makes some claims" gloss.
- **Specific problems get specific answers.** If `problem.md` lists Problem 1 (prove BST height bound), Problem 2 (solve recurrence), Problem 3 (DP table), the draft has a section per problem with a real proof / derivation — NOT a `[PROBLEM N]` placeholder.
- **For papers/critiques**: name the paper. Name its authors. Quote (with citation) at least one specific claim from the paper. Generic "this paper discusses..." sentences fail the quality bar.
- **No `[PROBLEM N]` / `[TODO: ...]` / `[此处填入...]` placeholders.** The only acceptable markers:
  - `[CITATION NEEDED: <topic>]` — when `references.bib` lacks a needed entry. Surfaced at [E].
  - `[CLARIFICATION NEEDED: <specific question about problem.md>]` — when `problem.md` is genuinely ambiguous on a specific point. Surfaced at [E].
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
2. **Match the language.** If `problem.md` is in Chinese and rubric mentions "中文写作", the draft must be Chinese — `pdf-renderer` ctexart handles both, but mismatched language gets points off.
3. **`spec.md` / `problem.md` are the source of truth, NOT `assignment.description`.** The description is HTML and often just a file link or empty. Reading it directly produces "the assignment is about X" template content. Always read the workbench files generated by `problem-extractor`.
4. **`partial_scope` is binding.** If the user said "only problem 2 and 4", do NOT write 1 and 3 even if the rubric says they're required. The user knows what they want.
5. **Don't auto-conclude with "In conclusion, ..." for short reflections.** Reflections are personal — let the structure follow the rubric, not a rigid 5-paragraph template.
6. **Frontmatter `date: \today`** — keep the backslash; pdf-renderer's LaTeX will resolve it. Don't replace with a literal date unless the user asked.
7. **Engage with specific content.** A paper critique that doesn't name the paper, its authors, or quote a single sentence from it is failing the quality bar regardless of word count.
8. **If `problem.md` is missing or thin** (< 1 KB), STOP. Write a single-line draft.md containing `[CLARIFICATION NEEDED: problem.md was not grounded — do-homework [A3] failed or extraction yielded no text]` and return. Do not pad with template content.
