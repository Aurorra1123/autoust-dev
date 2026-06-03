---
name: writing-helper-report
description: Report-type structure guidance for writing-helper. Loaded by writing-helper.md when type is report. Do not load from _index.md.
---

# writing-helper-report

Loaded by `writing-helper.md` on demand. Do not load directly from `_index.md`.

## Standard scientific report structure

When the task type is `report`, use this section structure as a reference:

1. **Abstract** — 150-250 words summarizing the entire work
2. **Introduction** — context, motivation, objectives
3. **Methods / Methodology** — what was done and how (algorithms, datasets, tools)
4. **Results** — findings with figures/tables. **Data must come from actual
   execution results, not estimates or fabricated values.**
5. **Discussion** — interpret results, compare with expectations, limitations
6. **Conclusion** — summary of findings, future work
7. **References** — only entries from `references.bib`

Not every report needs all sections. Follow spec/pipeline_design/rubric for
which sections are required and their relative weight.

## Report-specific guidance

- **Figures and tables**: each gets a number (Figure 1, Table 1) and a caption.
  Referenced in text as "see Figure 1". Use `figures/` outputs from figure-maker.
- **Data integrity**: if the report presents experimental results (accuracy, loss,
  timing), these numbers must come from actual code execution in a prior stage.
  Never estimate metrics like "accuracy ~0.75 based on typical sklearn performance".
- **LaTeX math in markdown**: use `$...$` for inline and `$$...$$` for display
  equations. pdf-renderer handles compilation.
- **Code snippets**: keep them short and focused. Don't paste entire source files
  into the report — reference the file path instead.
