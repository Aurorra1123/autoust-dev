---
name: tools-index
description: Capability menu for AutoStudy tools. Read this to discover what tools exist and what each can do. Sub-skills and appendices are discovered by reading the parent skill file, not listed here.
---

# Tools Index

This is the **capability menu** for AutoStudy. Read this file to discover
available tools and their contracts. Each tool's full guidance lives in
`sub-skills/tools/<name>.md`.

**For pipeline design guidance** (common pipeline shapes, tool chaining),
see `sub-skills/tasks/alignment-planning.md [C]`.

## Tool registry

| Tool | File | One-line capability | Inputs | Outputs |
|---|---|---|---|---|
| **pdf-renderer** | [pdf-renderer.md](./pdf-renderer.md) | Markdown → PDF (Chinese, LaTeX math, code, callouts) | markdown file, options | PDF file |
| **writing-helper** | [writing-helper.md](./writing-helper.md) | Structured academic prose (essay/report/reflection) | spec.md, execution plan, rubric, references | draft.md |
| **literature-search** | [literature-search.md](./literature-search.md) | Scholarly source discovery with provider fallback, access-depth reporting, and BibTeX output | assignment context, query angles, provider availability | literature/*, references.bib |
| **figure-maker** | [figure-maker.md](./figure-maker.md) | Charts/plots via matplotlib | figure_spec dict | fig_N.pdf/png |
| **code-writer** | [code-writer.md](./code-writer.md) | Source code from spec (Python/C++/etc.) | spec.md, execution plan, references | src/*.py + tests |
| **test-runner** | [test-runner.md](./test-runner.md) | pytest execution + report | work_dir/src/ | test_report.md/json |
| **slide-maker** | [slide-maker.md](./slide-maker.md) | Presentation slides (guizang HTML or beamer) | spec.md, execution plan | slides.pdf |
| **humanizer** | [humanizer.md](./humanizer.md) | Post-processing: reduce AI-detectable patterns | draft text | revised text |

> Loading order: read this file first → read every matched top-level tool's .md
> from the stage `tools` list → if a tool lists appendices, load relevant
> appendix files on demand. For legacy single-tool stages, `tool` means
> `tools: [tool]`.
> `primary_tool` is the stage ownership/lead contract; `tools` is the complete
> ordered list of top-level tool contracts the stage must preserve.
> Retained-artifact reconnaissance is a routed task stage, not a tool registry
> entry. Start from `sub-skills/tasks/do-homework.md`.

## Task registry

| Task | File | One-line capability | Trigger |
|---|---|---|---|
| **sync-course** | [../tasks/sync-course.md](../tasks/sync-course.md) | Persistent course material sync (files, announcements, modules) | "同步课程资料", "下载课件" |
| **write-course-notes** | [../tasks/write-course-notes.md](../tasks/write-course-notes.md) | Parallel Agent notes from lecture PDFs (Obsidian style) | "写笔记", "课程笔记" |

## Capability vocabulary

| Verb | Meaning |
|---|---|
| `render_pdf` | Markdown → PDF |
| `render_slides` | Slides (HTML/PDF) |
| `search_literature` | Scholarly source discovery → audit report + bib |
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
