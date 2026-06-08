---
name: writing-helper
description: Draft structured academic prose (essay/report/reflection) from spec + pipeline + rubric. Type-specific structure guidance in appendix files loaded on demand.
---

# writing-helper

Academic prose workhorse. Reads the assignment workbench and produces
`draft.md`. This file provides cross-type writing guidance; type-specific
structure (essay/report/reflection) is in appendix files loaded based on
`pipeline_design.md` declarations.

**Skills provide reference guidance, not hard constraints.** If the task spec
has explicit format requirements, follow the spec.

## Contract

- **reads:**
  - `spec.md` (PRIMARY)
  - `pipeline_design.md` (prose stage, deliverables, constraints)
  - `investigation/rubric.md`
  - `references/` (fetched readings, spec text, data)
  - `problem.md` (compatibility; read after spec.md)
  - `investigation/user_notes.md` (optional)
  - `investigation/user_scope.md` (optional)
  - `references.bib` (optional, from paper-search)
  - `draft/figures/*.{pdf,png}` or `figures/*.{pdf,png}` (optional, from code
    or figure-maker stages)
  - `draft/*.{pdf,png}` (compatibility scan only; prefer organized figures)
- **writes:**
  - `draft.md` (pandoc-friendly markdown with YAML frontmatter)
- **preconditions:**
  - `spec.md` and `pipeline_design.md` must exist and contain actual content

## Guidance

### Determine structure

Read spec, pipeline_design, rubric, and references. Match the prose stage
against supported structures:

| Structure | Cues | Typical sections |
|---|---|---|
| `essay` | "argue", "critique", "analyze", "thesis" | Intro (thesis) → body paragraphs → conclusion |
| `report` | "results", "methodology", "discussion", "experiment" | Abstract → Intro → Methods → Results → Discussion → Conclusion |
| `reflection` | "reflect", "experience", "learned" | Context → What happened → What I learned → Implications |

If `pipeline_design.md` declares `type`, use that. Otherwise infer from cues.
Load the matching appendix for detailed structure guidance.

### Honor length and citation style

Take from spec/pipeline_design/rubric:

- `length: ~1500 words` → aim ±10%, budget per section
- `citation_style: APA` → in-text `(Author, 2024)`, end `## References`
- `citation_style: IEEE` → in-text `[1]`, end `## References`
- `citation_style: none` → no citations; don't fake them

### Use references.bib if available

If `references.bib` exists, pull citations from it. Don't invent references.
If you need a reference not in the bib, write `[CITATION NEEDED: <description>]`
inline — surfaced at do-homework [E].

### Embed figures

For experimental reports, figures are part of the argument, not loose
attachments. Scan for generated images in this order:

1. `draft/figures/*.{pdf,png}` when the report is `draft/report.md`;
2. `figures/*.{pdf,png}` for older workbench-level figure-maker output;
3. `draft/*.{pdf,png}` only as a compatibility fallback.

If relevant figures exist, embed a representative set in the report and cite
them in text:

```markdown
![2D t-SNE projection of the standardized feature space.](figures/tsne_2d.png){width=70%}
```

Use paths relative to the markdown file. For `draft/report.md`, this usually
means `figures/<name>.png`, not `draft/figures/<name>.png`.

If useful figures exist only as flat `draft/*.png`, either move/copy them into
`draft/figures/` before writing the report or explicitly record a blocking
`auto_fixable` concern for the organizer/report stage. Do not accept a text-only
experimental report when generated plots are available unless the assignment
explicitly forbids figures or the report is already over a strict page limit.

### Write the draft

Produce `draft.md` with YAML frontmatter (pdf-renderer reads it):

```yaml
---
title: <Assignment name>
author:
date: \today
documentclass: ctexart
geometry: margin=1in
CJKmainfont: PingFang SC
monofont: Menlo
---
```

Quality bar:

- Every assertion grounded in spec/references/pipeline_design
- Specific problems get specific answers (no `[PROBLEM N]` placeholders)
- For critiques: name the paper, authors, quote specific claims
- Every section has a topic sentence
- No "As an AI" / "I will discuss" filler
- Match user's language (en/zh) — if zh, draft in Chinese, frontmatter keys stay English
- Only acceptable markers: `[CITATION NEEDED]` and `[CLARIFICATION NEEDED]`

## Appendices (loaded on demand)

| Appendix | When to load |
|---|---|
| [writing-helper-report.md](./writing-helper-report.md) | When `type: report` or report cues detected |
| `writing-helper-essay.md` (future) | When `type: essay` or essay cues detected |

## Post-processing

- Hand off to `pdf-renderer.md` with `draft.md` → `final.pdf`
- If `pipeline_design.md` declares `post-process: humanize`, or user requested
  at [B], load `humanizer.md` and apply to draft before rendering
- **Suggestion for pipeline design**: for academic reports and essays submitted
  to institutions with AI-detection tools, consider adding `post-process: humanize`
  to the pipeline_design stage. This is optional and should be the agent's judgment call.

## Self-check

- [ ] `spec.md` and `pipeline_design.md` read completely
- [ ] Draft engages with specific content from spec/references (not generic)
- [ ] Word count within ±10% of requirement (if specified)
- [ ] All rubric criteria addressed in draft
- [ ] No fabricated citations — only `references.bib` entries or `[CITATION NEEDED]`
- [ ] No `[PROBLEM N]` / `[TODO]` / `[此处填入...]` placeholders
- [ ] Language matches spec requirements (en/zh)
- [ ] Figures referenced and cited in-text (if any exist)
- [ ] Experimental reports embed representative generated figures when plots are
      available; text-only reports with available plots are flagged for repair
- [ ] For reports: data/numbers come from actual execution results, not estimates
