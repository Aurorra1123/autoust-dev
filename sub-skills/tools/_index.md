---
name: tools-index
description: Index of available tools. The task-orchestrator reads this to decide which tools to compose for a given task. Update this whenever you add or remove a tool.
---

# Tools Index

This is the **capability registry** for AutoStudy. The `task-orchestrator` reads this file to discover what tools exist and what each one can do. Tool implementation lives in `sub-skills/tools/<name>.md` — each markdown file contains the spec + shell/Python snippets the agent will execute directly (no separate `.py` files; same philosophy as AutoPku).

The one exception is `scraper/`, which is a real Python package — it's our equivalent of AutoPku's `pku3b` external CLI.

## How orchestrator uses this

1. Read this file to enumerate available tools
2. Match `capabilities` against the current task's `required_capabilities`
3. Read the matched tool's full `.md` file for invocation details
4. Compose a pipeline: which tool runs first, what intermediate files flow between them

## Tool registry

| Tool | File | Capabilities | Inputs | Outputs | Stability |
|---|---|---|---|---|---|
| **pdf-renderer** | [pdf-renderer.md](./pdf-renderer.md) | `render_pdf` (markdown→PDF), supports Chinese, LaTeX math, callouts | markdown file path, options (font, geometry, callouts) | PDF file path | 🟢 stable |

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
| `edit_video` | video editing / clipping / subtitles |
| `transcribe_audio` | speech-to-text |

If you need a verb not in this list, add it here when you add the tool, so future tools can refer to it consistently.

## What is NOT a tool

To avoid scope creep:

- ❌ Anything in `scraper/` — that's data acquisition, not task production
- ❌ One-off shell snippets the orchestrator can write inline
- ❌ Things that depend on services without a stable API (e.g. some unstable LLM-only hack)
- ✅ Anything that produces a tangible artifact (PDF / PPT / video / code / figure)
- ✅ Anything reused across multiple homework / task types
