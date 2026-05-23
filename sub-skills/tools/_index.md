---
name: tools-index
description: Index of available tools. The task-orchestrator reads this to decide which tools to compose for a given task. Update this whenever you add or remove a tool.
---

# Tools Index

This is the **capability registry** for AutoStudy. The `task-orchestrator` reads this file to discover what tools exist and what each one can do. Tool implementation lives in `sub-skills/tools/<name>.md` — each markdown file contains the spec + shell/Python snippets the agent will execute directly (no separate `.py` files; same philosophy as AutoPku).

The data-acquisition layer is a separate concern: `canvascli` is a sister CLI repo (`~/workspace/canvascli/`), installed into `.venv` via `pip install -e`. It is NOT a tool listed here — its commands are invoked directly by tasks (e.g. `do-homework.md` calls `canvascli assignment`).

## How orchestrator uses this

1. Read this file to enumerate available tools
2. Match `capabilities` against the current task's `required_capabilities`
3. Read the matched tool's full `.md` file for invocation details
4. Compose a pipeline: which tool runs first, what intermediate files flow between them

## Tool registry

| Tool | File | Capabilities | Inputs | Outputs | Stability |
|---|---|---|---|---|---|
| **pdf-renderer** | [pdf-renderer.md](./pdf-renderer.md) | `render_pdf` (markdown→PDF), supports Chinese, LaTeX math, callouts | markdown file path, options (font, geometry, callouts) | PDF file path | 🟢 stable |
| **writing-helper** | [writing-helper.md](./writing-helper.md) | `write_essay` (assignment + rubric → structured draft.md: essay/report/reflection) | task_profile.yaml, assignment.json, references.bib (opt) | draft.md (pandoc-friendly) | 🟡 experimental |
| **paper-search** | [paper-search.md](./paper-search.md) | `search_papers` (topic keywords → bib + json via arxiv API) | topic keywords, max_results | references.bib, references.json | 🟡 experimental |
| **figure-maker** | [figure-maker.md](./figure-maker.md) | `make_figure` (line/bar/scatter via matplotlib) | figure_spec dict | fig_N.pdf + fig_N.png in work_dir/figures/ | 🟡 experimental |
| **code-writer** | [code-writer.md](./code-writer.md) | `write_code` (lab spec → src/*.py + tests + README) | task_profile.yaml, assignment.json | work_dir/src/*.py | 🟡 experimental |
| **test-runner** | [test-runner.md](./test-runner.md) | `run_tests` (pytest + entry point → markdown report) | work_dir/src/ | test_report.md + test_report.json | 🟡 experimental |
| **slide-maker** | [slide-maker.md](./slide-maker.md) | `render_slides` (slide spec → beamer .tex → PDF via tectonic) | task_profile.yaml, assignment.json, figures/ | slides.tex + slides.pdf | 🟡 experimental |

> 🟢 stable · 🟡 experimental · 🔴 work-in-progress

## Adding a new tool

When you write a new tool:

1. Create `sub-skills/tools/<name>.md` with this frontmatter:
   ```yaml
   ---
   name: <kebab-case-name>
   description: One-line summary of what it does, for the orchestrator
   ---
   ```
2. The body must contain:
   - **Capabilities**: short list of verbs (`search_papers`, `render_pdf`, `generate_slides`, ...)
   - **Inputs / Outputs**: file paths and shapes, in plain text
   - **Setup**: any one-time install (note proxy if relevant — see `scraper-setup.md`)
   - **Invocation**: actual shell or Python snippets the agent will run
   - **Pitfalls**: anything we've burned on already
3. Add a row to the registry table above
4. If your tool depends on others (e.g. `slide-maker` calls `figure-maker` for charts), say so in the body

## Capability vocabulary (consistent verb naming)

To keep the orchestrator's matching simple, use these verbs when describing what a tool does:

| Verb | Meaning |
|---|---|
| `parse_pdf` | extract text/structure from PDF |
| `render_pdf` | produce PDF from markdown/LaTeX |
| `render_slides` | produce slides (PPTX/HTML/PDF) |
| `search_papers` | find references for a topic |
| `make_figure` | generate charts/plots |
| `write_essay` | draft structured prose (intro/body/conclusion) |
| `solve_proof` | mathematical proof / derivation |
| `write_code` | generate code with tests |
| `run_tests` | execute tests + entry point, capture results |
| `edit_video` | video editing / clipping / subtitles |
| `transcribe_audio` | speech-to-text |

If you need a verb not in this list, add it here when you add the tool, so future tools can refer to it consistently.

## What is NOT a tool

To avoid scope creep:

- ❌ Anything that talks to Canvas — that's `canvascli` (data layer, separate repo)
- ❌ One-off shell snippets the orchestrator can write inline
- ❌ Things that depend on services without a stable API (e.g. some unstable LLM-only hack)
- ✅ Anything that produces a tangible artifact (PDF / PPT / video / code / figure)
- ✅ Anything reused across multiple homework / task types

## Scenario → Tool chain

`do-homework.md` consults this table to populate `required_capabilities` per task type. Each row is a full pipeline from blank work_dir to deliverable.

| Scenario | type | Tool chain (in order) | Final deliverable |
|---|---|---|---|
| **paper** (essay / critique / report) | `paper` | `search_papers` → `make_figure` (opt) → `write_essay` → `render_pdf` | `final.pdf` |
| **slides** (group presentation, talk) | `slides` | `make_figure` (opt) → `render_slides` | `slides.pdf` |
| **math** (proof, problem set) | `math` | `write_essay` (with LaTeX math) → `render_pdf` | `solution.pdf` |
| **lab** (programming assignment) | `lab` | `write_code` → `run_tests` → `write_essay` (lab report) → `render_pdf` | `src/` + `report.pdf` |
| **video** (presentation video) | `video` | _(out of scope for AutoStudy MVP — implemented by a separate video skill, see `docs/ROADMAP.md` M3-VIDEO)_ | — |

**Math note**: MVP doesn't ship a dedicated `proof-solver` or `math-renderer` — the agent writes LaTeX directly inside the `draft.md` markdown source, and `pdf-renderer`'s existing `xelatex` / `tectonic` toolchain handles compilation. If a future course needs tikz-heavy diagrams or symbolic CAS work, add `proof-solver.md` then.
