# Skills Architecture Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor all AutoStudy skill files to the unified template (Contract → Guidance → Appendices → Post-processing → Self-check), fix P0 path discovery, and validate via sub-agent end-to-end test.

**Architecture:** Directory-level inference + `git rev-parse` for path discovery (P0). Each skill file restructured to the unified template with appendix files for language/type specifics. `_index.md` becomes a pure capability menu. Pipeline shapes move to `do-homework.md [C]`.

**Tech Stack:** Markdown skill files, bash for verification, sub-agent execution for end-to-end testing.

**Spec:** `docs/superpowers/specs/2026-06-03-skills-refactor-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `docs/skills-architecture-spec.md` | Add audit findings (§2.4, fallback/min_quality fields, P5 note) |
| Rewrite | `sub-skills/tools/_index.md` | Pure capability menu, no routing |
| Rewrite | `sub-skills/tools/code-writer.md` | Unified template, Python appendix reference |
| Create | `sub-skills/tools/code-writer-python.md` | Python-specific conventions (uv, project structure, notebook) |
| Rewrite | `sub-skills/tools/writing-helper.md` | Unified template, report/humanizer appendix references |
| Create | `sub-skills/tools/writing-helper-report.md` | Report-specific structure guidance |
| Create | `sub-skills/tools/humanizer.md` | Post-processing style guide for reducing AI patterns |
| Modify | `sub-skills/tools/pdf-renderer.md` | Add fallback chain + Self-check section |
| Modify | `sub-skills/tasks/do-homework.md` | Path discovery, pipeline shapes from old _index.md, new pipeline_design format |
| Modify | `sub-skills/tasks/task-orchestrator.md` | Path discovery, new pipeline_design format |

---

## Task 1: Update skills-architecture-spec.md with audit findings

**Files:**
- Modify: `docs/skills-architecture-spec.md`

- [ ] **Step 1: Add §2.4 path discovery rules after §2.3**

Insert after the `_index.md 的角色` section (after line 67, before the `---` separator). Content:

```markdown
### 2.4 路径发现规则（解决 P0）

Agent 的工作目录在 `data/homework/<COURSE>/<HWID>/`，而 skill 文件
在仓库根下。agent 必须能从工作目录找到 skill 文件。

**方案：层级推导 + git rev-parse 双保险**

```text
推导规则：
  - WORK_DIR = data/homework/<COURSE>/<HWID>/
  - REPO_ROOT = 从 WORK_DIR 向上 3 级目录
  - SKILLS_DIR = REPO_ROOT/sub-skills/tools/
  - _INDEX = SKILLS_DIR/_index.md
```

保险层：如果推导结果无效，使用 `git -C "$WORK_DIR" rev-parse --show-toplevel`
获取真实仓库根。

在 `do-homework.md [A2]` 创建工作台时，将 `REPO_ROOT` 绝对路径写入
`pipeline_design.md` 的 metadata 头。`task-orchestrator.md` Step 1 优先从
pipeline_design.md 读取 REPO_ROOT，fallback 到层级推导，再 fallback 到
`git rev-parse`。

**子代理环境注意（P5）**：Write 工具在子代理沙箱中可能被限制。
当 skill 需要写文件时，如果 Write 工具被拒绝，使用
`Bash + cat > file <<'EOF'` heredoc 作为替代方案。
```

- [ ] **Step 2: Add fallback/min_quality fields to §5 pipeline_design format**

In §5, after the bullet list of stage fields (`post-process` bullet), add:

```markdown
- `fallback`：首选工具不可用时的回退方案（防止反复试错）
- `min_quality`：最低质量门槛（如 `PDF > 10KB`、`pages >= 5`）
```

- [ ] **Step 3: Verify the file is valid markdown**

Run: `wc -l docs/skills-architecture-spec.md`
Expected: ~410 lines (increased from ~400)

- [ ] **Step 4: Commit**

```bash
git add docs/skills-architecture-spec.md
git commit -m "docs: integrate audit findings into skills architecture spec"
```

---

## Task 2: Rewrite _index.md as capability menu

**Files:**
- Rewrite: `sub-skills/tools/_index.md`

- [ ] **Step 1: Write the new _index.md**

Replace entire file with:

```markdown
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
```

- [ ] **Step 2: Verify the file reads correctly**

Run: `head -5 sub-skills/tools/_index.md`
Expected: frontmatter with `name: tools-index` and new `description`

- [ ] **Step 3: Commit**

```bash
git add sub-skills/tools/_index.md
git commit -m "refactor: rewrite _index.md as capability menu"
```

---

## Task 3: Rewrite code-writer.md with unified template

**Files:**
- Rewrite: `sub-skills/tools/code-writer.md`

- [ ] **Step 1: Write the new code-writer.md**

Replace entire file with:

```markdown
---
name: code-writer
description: Write source code from assignment spec. Provides domain guidance for code quality — language-specific conventions are in appendix files loaded on demand.
---

# code-writer

Code generation workhorse. Reads the assignment workbench and writes source
files into `<work_dir>/src/`. This file provides cross-language guidance;
language-specific conventions (project structure, testing, toolchain) are
in appendix files loaded based on `pipeline_design.md` stage declarations.

**Skills provide reference guidance, not hard constraints.** If the task spec
explicitly requires a different approach, follow the spec.

## Contract

- **reads:**
  - `spec.md` (PRIMARY — standardized reconnaissance report)
  - `pipeline_design.md` (code stage, deliverables, constraints)
  - `investigation/rubric.md`
  - `references/` (starter code, data, spec PDFs/text)
  - `problem.md` (compatibility; read after spec.md)
  - `investigation/user_notes.md` (optional)
  - `investigation/user_scope.md` (optional)
- **writes:**
  - `src/<module>.py` (or .cpp/.java per lang)
  - `src/test_<module>.py` (pytest-style or equivalent)
  - `src/README.md`
- **preconditions:**
  - `spec.md` and `pipeline_design.md` must exist and contain actual content
  - Language must be determined (default: Python)

## Guidance

### Parse the spec from the workbench

Read `spec.md`, `pipeline_design.md`, rubric, and references end-to-end.
Identify:

- **Language**: Python is default. Record in pipeline_design.md if not already there.
- **Required functions / classes / entry points**: look for "implement", "complete",
  function signatures. Use those exact names — auto-graders match by name.
- **I/O contract**: input format, expected output, datasets.
- **Algorithm constraints**: complexity bounds, allowed libraries, "implement from scratch".
- **Test cases**: translate spec-provided input/output pairs into tests.

If spec names a specific dataset, paper, function, or algorithm — implement that,
not a generic equivalent. If ambiguous on a specific point, write
`[CLARIFICATION NEEDED: <question>]` as a comment and continue with a defensible default.

### Write the code

Style rules (defaults — spec overrides if it says otherwise):

- Implement what spec actually asks. Not a generic representative project.
- One responsibility per file. Don't dump everything into `solution.py`.
- Top of every file: 1-line docstring. No multi-paragraph docstrings.
- No comments unless the WHY is non-obvious.
- Type hints on public functions.
- Use stdlib where possible.
- **No `[TODO: align with actual project spec]` or equivalent placeholders.**
  Use `[CLARIFICATION NEEDED: <question>]` instead.
- `if __name__ == "__main__":` is mandatory for runnable entry points.
- Don't shadow stdlib names (no `os.py`, `json.py`, etc.).
- Use `pathlib.Path(__file__).parent` for relative paths, never hard-code absolute paths.
- No `print()` debug statements in submitted code. Wrap in `if __debug__:` or remove.
- Seed `random`/`numpy.random` with `seed=42` if spec requires reproducibility.

### Write the tests

For every public function, at least one pytest test. Tests in `src/test_<module>.py`.
One assertion per test where possible. Use `@pytest.mark.parametrize` for spec-provided
input/output pairs.

### Write the README

`src/README.md` — 5-10 lines: how to run, expected output, assumptions made.

## Appendices (loaded on demand)

| Appendix | When to load |
|---|---|
| [code-writer-python.md](./code-writer-python.md) | When `lang: python` or default (always for HKUST(GZ) labs) |
| `code-writer-cpp.md` (future) | When `lang: cpp` |

Read this parent file first, then load the matching language appendix for
toolchain-specific conventions (project structure, dependency management, testing).

## Post-processing

- Hand off to `test-runner.md` to verify code passes its own tests
- If the assignment also asks for a report, `writing-helper.md` drafts prose next
- If `pipeline_design.md` declares `post-process: humanize` for code comments,
  load `humanizer.md`

## Self-check

- [ ] `spec.md` and `pipeline_design.md` were read completely (not just title)
- [ ] Code implements what the spec asks, not a generic equivalent
- [ ] All required functions/classes from spec are implemented with exact names
- [ ] Code can run in a clean environment without errors
- [ ] Notebooks were actually executed — output cells are not fabricated estimates
- [ ] Report data metrics come from actual execution results
- [ ] No `[TODO]` / `[PROBLEM N]` / `[此处填入...]` placeholders
- [ ] Only `[CITATION NEEDED]` and `[CLARIFICATION NEEDED]` markers used
- [ ] Tests exist for every public function
- [ ] README explains how to run and expected output
```

- [ ] **Step 2: Verify structure**

Run: `grep "^## " sub-skills/tools/code-writer.md`
Expected: Contract, Guidance, Appendices, Post-processing, Self-check (all 5 sections present)

- [ ] **Step 3: Commit**

```bash
git add sub-skills/tools/code-writer.md
git commit -m "refactor: rewrite code-writer.md with unified template"
```

---

## Task 4: Create code-writer-python.md

**Files:**
- Create: `sub-skills/tools/code-writer-python.md`

- [ ] **Step 1: Write code-writer-python.md**

```markdown
---
name: code-writer-python
description: Python-specific conventions for code-writer. Loaded by code-writer.md when lang is python. Do not load from _index.md.
---

# code-writer-python

Loaded by `code-writer.md` on demand. Do not load directly from `_index.md`.

These are **reference defaults** — if the task spec explicitly requires a different
setup (e.g. "use pip instead of uv", "flat structure"), follow the spec.

## Environment management

- Default: use `uv` for Python project management (init, add, run)
- If `uv` is not available, fall back to `pip` + `venv`
- If spec says "no package manager" or "use conda", follow spec

## Project structure

Default structure for non-trivial projects (more than one file):

```text
src/
├── __init__.py
├── <module>.py          # main implementation
├── test_<module>.py     # pytest tests
└── README.md
```

For notebook-based assignments:

```text
draft/
├── <name>.ipynb         # main notebook
└── requirements.txt     # dependencies (pip freeze)
```

Do NOT dump all files flat in the work_dir root. Keep source code in `src/`
and notebooks in `draft/`.

## Notebook conventions

- Build notebooks using `nbformat` — do not manually write JSON
- **The notebook must be executed after creation** — output cells must contain
  actual execution results, not fabricated estimates
- If execution fails, fix and re-execute; do not leave empty output cells
- Include `requirements.txt` with exact versions (`pip freeze`)

## pytest conventions

- One test file per source module: `test_<module>.py`
- Use `@pytest.mark.parametrize` for data-driven tests from spec
- Use `pytest.skip` with reason for unimplemented parts (with `[CLARIFICATION NEEDED]` comment)
- Fixtures for shared setup (datasets, temp directories)
- All tests must pass for the stage to be considered complete

## Common pitfalls (Python-specific)

1. **`if __name__ == "__main__":` is mandatory** — pytest imports the file, module-level code breaks tests
2. **Don't shadow stdlib names** — `solution.py` is fine; `os.py`/`sys.py`/`json.py` break imports
3. **Use `pathlib`** for path handling, never hard-code paths
4. **Seed random/numpy.random** with 42 if spec requires reproducibility
5. **Don't add `print()` debug statements** — auto-graders parse stdout
6. **Function names follow spec verbatim** — if spec says `fit_ols(X, y)`, don't write `train_ordinary_least_squares(X, y)`
```

- [ ] **Step 2: Verify file exists and has correct frontmatter**

Run: `head -4 sub-skills/tools/code-writer-python.md`
Expected: frontmatter with `name: code-writer-python` and "Loaded by code-writer.md"

- [ ] **Step 3: Commit**

```bash
git add sub-skills/tools/code-writer-python.md
git commit -m "feat: add code-writer-python.md appendix"
```

---

## Task 5: Rewrite writing-helper.md with unified template

**Files:**
- Rewrite: `sub-skills/tools/writing-helper.md`

- [ ] **Step 1: Write the new writing-helper.md**

Replace entire file with:

```markdown
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
  - `figures/*.{pdf,png}` (optional, from figure-maker)
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

If `figures/fig_N.{pdf,png}` exist, reference in markdown:
`![Caption text](figures/fig_1.pdf){width=60%}` and cite in-text.

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

## Self-check

- [ ] `spec.md` and `pipeline_design.md` read completely
- [ ] Draft engages with specific content from spec/references (not generic)
- [ ] Word count within ±10% of requirement (if specified)
- [ ] All rubric criteria addressed in draft
- [ ] No fabricated citations — only `references.bib` entries or `[CITATION NEEDED]`
- [ ] No `[PROBLEM N]` / `[TODO]` / `[此处填入...]` placeholders
- [ ] Language matches spec requirements (en/zh)
- [ ] Figures referenced and cited in-text (if any exist)
- [ ] For reports: data/numbers come from actual execution results, not estimates
```

- [ ] **Step 2: Verify structure**

Run: `grep "^## " sub-skills/tools/writing-helper.md`
Expected: Contract, Guidance, Appendices, Post-processing, Self-check

- [ ] **Step 3: Commit**

```bash
git add sub-skills/tools/writing-helper.md
git commit -m "refactor: rewrite writing-helper.md with unified template"
```

---

## Task 6: Create writing-helper-report.md

**Files:**
- Create: `sub-skills/tools/writing-helper-report.md`

- [ ] **Step 1: Write writing-helper-report.md**

```markdown
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
```

- [ ] **Step 2: Verify file**

Run: `head -4 sub-skills/tools/writing-helper-report.md`
Expected: frontmatter with `name: writing-helper-report`

- [ ] **Step 3: Commit**

```bash
git add sub-skills/tools/writing-helper-report.md
git commit -m "feat: add writing-helper-report.md appendix"
```

---

## Task 7: Update pdf-renderer.md with fallback chain + Self-check

**Files:**
- Modify: `sub-skills/tools/pdf-renderer.md`

- [ ] **Step 1: Add Post-processing fallback chain section**

Insert before the existing `## Pitfalls` section:

```markdown
## Post-processing (fallback chain)

If the primary rendering path fails, try in order:

1. **Tectonic two-step** (preferred) — `pandoc → tex → tectonic → PDF`
2. **Pandoc + xelatex** — `pandoc --pdf-engine=xelatex → PDF`
3. **fpdf2 pure Python** — if neither LaTeX engine is available:
   ```bash
   pip install fpdf2
   ```
   Render a simplified text-only PDF. Record in `human_review_items`:
   "PDF rendered via fpdf2 fallback — formatting quality may be degraded."

If the final PDF is suspiciously small (<10KB for a multi-page report),
it likely failed silently. Re-run with a different path.
```

- [ ] **Step 2: Add Self-check section**

Insert after the fallback chain, before Pitfalls:

```markdown
## Self-check

- [ ] Output PDF exists and is > 1KB
- [ ] Magic bytes are `%PDF` (run: `head -c 4 output.pdf`)
- [ ] Page count matches expectations (run: `pdfinfo output.pdf | grep Pages` if available)
- [ ] Chinese characters render correctly (not tofu boxes) — open and visually verify
- [ ] No LaTeX errors in stderr output
- [ ] For multi-page documents: page count >= 3 (sanity minimum)
```

- [ ] **Step 3: Verify structure**

Run: `grep "^## " sub-skills/tools/pdf-renderer.md`
Expected: Capabilities, Inputs / Outputs, Setup, Invocation, Post-processing, Self-check, Pitfalls, What this tool is NOT for

- [ ] **Step 4: Commit**

```bash
git add sub-skills/tools/pdf-renderer.md
git commit -m "refactor: add fallback chain and self-check to pdf-renderer"
```

---

## Task 8: Create humanizer.md

**Files:**
- Create: `sub-skills/tools/humanizer.md`

- [ ] **Step 1: Write humanizer.md**

```markdown
---
name: humanizer
description: Post-processing style guide for reducing AI-detectable patterns in written text. Loaded by writing-helper Post-processing when pipeline_design declares post-process: humanize. Do not load from _index.md.
---

# humanizer

Post-processing style guide. Applied after writing-helper produces a draft,
before pdf-renderer converts to PDF. This is NOT round-trip translation —
it's a structured review pass that reduces template-like and predictable patterns.

**When to load:**
- `pipeline_design.md` declares `post-process: humanize` for the stage
- User requests at do-homework [B]: "降低一下 AI 味道" or similar

**When NOT to load:**
- Code files (code-writer output) — only applies to prose
- Unless user explicitly asks for code comment humanization

## Contract

- **reads:** `draft.md` (from writing-helper or manual input)
- **writes:** revised `draft.md` (in-place or as draft_revised.md)
- **preconditions:** draft text exists

## Guidance

Read the draft and revise for these patterns:

### Sentence structure variation

- Avoid uniform subject-verb-object rhythm throughout paragraphs
- Mix sentence lengths: some short (5-8 words), some medium (15-20), occasional longer ones
- Vary sentence openers — don't start every sentence with "The" or "This"

### Vocabulary diversity

- Avoid repeating the same academic filler phrases:
  "It is important to note that", "plays a crucial role", "has significant implications"
- Use specific language instead of hedging:
  "might potentially have an effect on" → "affects"
- Don't overuse "utilize" (use "use"), "facilitate" (use "enable" or "allow")

### Paragraph rhythm

- Vary paragraph lengths — not all paragraphs should be 4-5 sentences
- Some ideas can be a single-sentence paragraph for emphasis
- Don't end every paragraph with a summary sentence

### Reduce telltale AI patterns

- Remove meta-discourse: "In this section, I will discuss..." → just discuss it
- Remove redundant signposting: "As mentioned above", "As previously stated"
- Avoid numbered lists when prose would be more natural
- Don't over-qualify: "somewhat", "rather", "relatively" used excessively
- Replace generic conclusions with specific takeaways

### What NOT to change

- Factual content and citations — these stay exactly as written
- Technical terminology specific to the domain
- The actual arguments and their logical structure
- Required formatting (sections, headings, references)

## Self-check

- [ ] No paragraph starts with "It is important to note" or similar filler
- [ ] Sentence lengths vary across the text
- [ ] No excessive hedging ("might potentially somewhat")
- [ ] No meta-discourse ("In this section I will...")
- [ ] Citations and facts unchanged
- [ ] Word count within ±5% of original (not significantly shorter/longer)
```

- [ ] **Step 2: Verify file**

Run: `head -4 sub-skills/tools/humanizer.md`
Expected: frontmatter with `name: humanizer`

- [ ] **Step 3: Commit**

```bash
git add sub-skills/tools/humanizer.md
git commit -m "feat: add humanizer.md post-processing skill"
```

---

## Task 9: Update do-homework.md — path discovery + pipeline shapes + new format

**Files:**
- Modify: `sub-skills/tasks/do-homework.md`

This is the largest modification. Three changes: path discovery in [A2],
pipeline shapes in [C], and pipeline_design format update in [C].

- [ ] **Step 1: Add REPO_ROOT computation to [A2]**

In the `[A2] Create The Workbench` section, after the `mkdir -p` command and
target structure, add:

```markdown
After creating directories, compute the repository root and save it for
downstream path discovery:

```bash
REPO_ROOT="$(git -C 'data/homework/<COURSE>/<HWID>' rev-parse --show-toplevel)"
echo "repo_root: ${REPO_ROOT}"
```

This `REPO_ROOT` will be injected into `pipeline_design.md` metadata at [C].
All skill file paths resolve as `REPO_ROOT/sub-skills/tools/<name>.md`.
```

- [ ] **Step 2: Add pipeline design guidance to [C]**

In the `[C] Design Pipeline` section, after the read list that currently ends with
`sub-skills/tools/_index.md`, add the pipeline shapes guidance (moved from old _index.md):

```markdown
Use the following common pipeline shapes as **reference guidance** — the agent
composes freely based on the actual assignment, not a fixed chain.

| Scenario | type | Typical tool chain | Final deliverable |
|---|---|---|---|
| **paper** | `paper` | paper-search → figure-maker (opt) → writing-helper → pdf-renderer | `final.pdf` |
| **slides** | `slides` | figure-maker (opt) → slide-maker | `slides.pdf` |
| **math** | `math` | writing-helper (LaTeX math) → pdf-renderer | `solution.pdf` |
| **lab** | `lab` | code-writer → test-runner → writing-helper → pdf-renderer | `src/` + `report.pdf` |
| **mixed** | `mixed` | Multiple sub-pipelines composed from above | multiple files |

For mixed assignments, write multiple sub-pipelines in pipeline_design.md.
Each sub-pipeline is a sequence of stages.
```

- [ ] **Step 3: Update pipeline_design.md format in [C]**

Replace the existing pipeline_design template block in [C] with:

```markdown
Complete `pipeline_design.md` using the new stage-based format:

```markdown
# Pipeline: <COURSE> <assignment>

## Metadata
repo_root: <absolute path from [A2]>

## Output
- mode: mixed (code + doc_prose + slides)
- deliverables: [notebook.ipynb, report.pdf, ...]

## Constraints
- [quantifiable constraints from spec]

## Stages

### Stage 1 — <name>
- tool: code-writer
- lang: python
- reads: spec.md §3, references/project_announce.pdf
- writes: draft/notebook.ipynb
- verify: notebook executes without errors
- review: false

### Stage 2 — <name>
- tool: writing-helper
- type: report
- reads: spec.md, rubric.md, draft/notebook.ipynb outputs
- writes: draft/report.md
- verify: covers every rubric criterion
- review: true
- post-process: humanize     # optional
- fallback: if pdf-renderer fails → fpdf2 + quality note
- min_quality: PDF > 10KB, pages >= 5

## Human Review Items
- ...
```

Do not write or require `task_profile.yaml`. The orchestrator reads
`spec.md + pipeline_design.md` directly.
```

- [ ] **Step 4: Verify the three changes are present**

Run: `grep -c "REPO_ROOT" sub-skills/tasks/do-homework.md`
Expected: >= 2 (computation in [A2] + reference in [C])

Run: `grep -c "repo_root:" sub-skills/tasks/do-homework.md`
Expected: >= 1 (in pipeline_design template)

Run: `grep "paper.*paper-search" sub-skills/tasks/do-homework.md`
Expected: 1 match (pipeline shapes table)

- [ ] **Step 5: Commit**

```bash
git add sub-skills/tasks/do-homework.md
git commit -m "refactor: add path discovery, pipeline shapes, and new format to do-homework"
```

---

## Task 10: Update task-orchestrator.md — path discovery + new format

**Files:**
- Modify: `sub-skills/tasks/task-orchestrator.md`

- [ ] **Step 1: Add path discovery to Step 1**

In Step 1 "Read The Workbench", before the read list, add:

```markdown
**Path discovery:** Before reading any skill files, determine the skill directory:

1. Read `pipeline_design.md` and look for `repo_root:` in the metadata section
2. If found, set `SKILLS_DIR = repo_root + "/sub-skills/tools/"`
3. If not found, infer: `REPO_ROOT = WORK_DIR/../../..` (3 levels up from data/homework/COURSE/HWID)
4. If inference fails, run: `git -C "$WORK_DIR" rev-parse --show-toplevel`
5. All skill file references use `SKILLS_DIR` as the base path

The `_index.md` is at `SKILLS_DIR/_index.md`.
```

- [ ] **Step 2: Update the read list in Step 1 to use SKILLS_DIR**

Change `sub-skills/tools/_index.md` in the read list to:

```text
SKILLS_DIR/_index.md          # path discovered above
```

- [ ] **Step 3: Update Step 2 to use SKILLS_DIR**

Change `sub-skills/tools/_index.md` references in Step 2 to use `SKILLS_DIR`.

- [ ] **Step 4: Replace Pipeline Design Format section**

Replace the old Pipeline Design Format section with a reference to the new format:

```markdown
## Pipeline Design Format

`pipeline_design.md` follows the stage-based format defined in
`docs/skills-architecture-spec.md §5`. Each stage declares:
tool, lang, type, reads, writes, verify, review, post-process, fallback, min_quality.

The format is written by `do-homework [C]` — the orchestrator reads and executes it.
Do not redesign the format here.
```

- [ ] **Step 5: Verify changes**

Run: `grep -c "SKILLS_DIR" sub-skills/tasks/task-orchestrator.md`
Expected: >= 3

Run: `grep "repo_root" sub-skills/tasks/task-orchestrator.md`
Expected: at least 1 match

- [ ] **Step 6: Commit**

```bash
git add sub-skills/tasks/task-orchestrator.md
git commit -m "refactor: add path discovery and new format to task-orchestrator"
```

---

## Task 11: Validate with sub-agent end-to-end test

**Files:**
- Read-only: all modified files from Tasks 1-10
- Output: trace analysis report

- [ ] **Step 1: Spawn execution sub-agent**

Spawn a sub-agent with the following task:

> Run the do-homework flow on the DSAA2011 ML Project workbench at
> `data/homework/DSAA2011/project/`. The workbench already has canvas/ and
> references/ data from a previous run. Start from `[C] Design Pipeline` —
> skip reconnaissance since spec.md and investigation/ already exist.
>
> Your working directory should be `data/homework/DSAA2011/project/`.
> First read `sub-skills/tasks/do-homework.md` to understand the flow.
> Follow [C] → [D] → [E] stages.
>
> Context: Group G01, Student Dropout dataset, group members Alice Chen/Bob Li/Carol Wang/Dave Zhang.

Capture the full JSONL trace for analysis.

- [ ] **Step 2: Spawn trace analysis sub-agent**

Spawn a second sub-agent to analyze the execution trace:

> Analyze the following JSONL execution trace from a DSAA2011 ML Project test run.
> Check for these specific issues from the original audit:
>
> P0: Were skill files actually read? (grep for Read tool calls to sub-skills/)
> P1: Does pipeline_design.md have stage→tool mapping? (tool/reads/writes per stage)
> P2: Was the notebook actually executed? (grep for python execution of .ipynb)
> P3: Did PDF rendering use the fallback chain? (check for tectonic/pandoc/fpdf2 attempts)
> P4: Was standard directory structure used? (check for workbench/ or non-standard dirs)
>
> Also check:
> - Were Self-check items verified?
> - Were appendices loaded when needed (code-writer-python, writing-helper-report)?
> - Was humanizer loaded if declared in pipeline_design?
>
> Return a structured report: for each P0-P5, status (FIXED/PARTIAL/UNFIXED)
> and evidence. Plus any new issues found.

- [ ] **Step 3: Review analysis and decide**

If all P0-P5 show FIXED → proceed to Task 12.
If any show PARTIAL or UNFIXED → fix the issue and re-run from Step 1.

---

## Task 12: Update progress docs

**Files:**
- Modify: `docs/progress/agent-progress.md`
- Modify: `docs/plans/feature-list.json`
- Modify: `COLLABORATION.md` (if needed)

- [ ] **Step 1: Update agent-progress.md**

Add a new entry at the top documenting this refactoring session:
what was changed, audit findings addressed, test results.

- [ ] **Step 2: Update feature-list.json**

Add or update the skills architecture feature entry with status reflecting
the completed refactor and test results.

- [ ] **Step 3: Final commit**

```bash
git add docs/progress/agent-progress.md docs/plans/feature-list.json
git commit -m "docs: record skills architecture refactor completion"
```
