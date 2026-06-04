---
name: tools-index
description: Capability menu for AutoStudy tools. Read this to discover what tools exist and what each can do. Sub-skills and appendices are discovered by reading the parent skill file, not listed here.
---

# Tools Index

This is the **capability menu** for AutoStudy. Read this file to discover
available tools and their contracts. Each tool's full guidance lives in
`sub-skills/tools/<name>.md`.

**For pipeline design guidance** (common pipeline shapes, tool chaining),
see `sub-skills/tasks/do-homework.md [C]`.

## Tool registry

| Tool | File | One-line capability | Inputs | Outputs |
|---|---|---|---|---|
| **problem-extractor** | [problem-extractor.md](./problem-extractor.md) | Canvas Generic Stage 1-5 reconnaissance → spec.md + rubric + references | course_id, assignment_id, work_dir | spec.md, investigation/, references/, problem.md |
| **pdf-renderer** | [pdf-renderer.md](./pdf-renderer.md) | Markdown → PDF (Chinese, LaTeX math, code, callouts) | markdown file, options | PDF file |
| **writing-helper** | [writing-helper.md](./writing-helper.md) | Structured academic prose (essay/report/reflection) | spec.md, pipeline_design.md, rubric, references | draft.md |
| **paper-search** | [paper-search.md](./paper-search.md) | Literature search via arxiv → bib + json | keywords, max_results | references.bib, references.json |
| **figure-maker** | [figure-maker.md](./figure-maker.md) | Charts/plots via matplotlib | figure_spec dict | fig_N.pdf/png |
| **code-writer** | [code-writer.md](./code-writer.md) | Source code from spec (Python/C++/etc.) | spec.md, pipeline_design.md, references | src/*.py + tests |
| **test-runner** | [test-runner.md](./test-runner.md) | pytest execution + report | work_dir/src/ | test_report.md/json |
| **slide-maker** | [slide-maker.md](./slide-maker.md) | Presentation slides (guizang HTML or beamer) | spec.md, pipeline_design.md | slides.pdf |
| **humanizer** | [humanizer.md](./humanizer.md) | Post-processing: reduce AI-detectable patterns | draft text | revised text |

> Loading order: read this file first → read the matched tool's .md → if tool lists appendices, load relevant appendix on demand.

## Task registry

| Task | File | One-line capability | Trigger |
|---|---|---|---|
| **sync-course** | [../tasks/sync-course.md](../tasks/sync-course.md) | Persistent course material sync (files, announcements, modules) | "同步课程资料", "下载课件" |
| **write-course-notes** | [../tasks/write-course-notes.md](../tasks/write-course-notes.md) | Parallel Agent notes from lecture PDFs (Obsidian style) | "写笔记", "课程笔记" |

## Capability vocabulary

| Verb | Meaning |
|---|---|
| `extract_problem` | Canvas reconnaissance → spec.md |
| `render_pdf` | Markdown → PDF |
| `render_slides` | Slides (HTML/PDF) |
| `search_papers` | Literature search → bib |
| `make_figure` | Charts/plots |
| `write_essay` | Structured academic prose |
| `write_code` | Source code + tests |
| `run_tests` | Execute tests + report |
| `humanize` | Reduce AI patterns in text |

## What is NOT a tool

- ❌ Anything that talks to Canvas — that's `canvascli`
- ❌ One-off shell snippets the orchestrator can write inline
- ❌ Things that depend on services without a stable API
- ✅ Anything that produces a tangible artifact
- ✅ Anything reused across multiple task types

## Adding a new tool

1. Create `sub-skills/tools/<name>.md` following the unified template (Contract → Guidance → Appendices → Post-processing → Self-check)
2. Add a row to the registry table above
3. If the tool has language/type-specific variants, create `<name>-<variant>.md` as an appendix file and list it in the parent skill's Appendices section
4. Do NOT list appendix files in this registry — they are discovered through the parent skill
