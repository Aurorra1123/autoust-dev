# Skills Architecture Refactor Design

> Date: 2026-06-03
> Status: Draft — pending user approval
> Trigger: Pipeline trace audit (`docs/pipeline-trace-audit.md`) revealed P0-P5 issues;
>          skills architecture spec (`docs/skills-architecture-spec.md`) established design but not yet implemented

---

## Context

A real DSAA2011 ML Project test run (23 min, 56 tool calls, 0 skill reads) exposed
that the entire skill system was bypassed because the sub-agent couldn't find skill
files from its working directory. Combined with the previously established skills
architecture spec, this refactor implements the new template across all skill files
while fixing the root-cause path discovery problem.

**Design principles** (established in prior sessions, not re-discussed):

1. Skills are domain expertise supplements — reference guidance, not hard constraints.
   If a specific task's spec has explicit requirements, the spec takes precedence.
2. Progressive loading: `_index.md` → parent skill → appendix
3. Core + Appendix pattern: language/type specifics in separate files
4. Skills can nest skills via Post-processing conditional references
5. `pipeline_design.md` is the per-task execution contract
6. Unified template: Contract → Guidance → Appendices → Post-processing → Self-check

**Decisions from this session:**

- Full refactor of all skill files (not just P0/P1 minimum fix)
- Path discovery: directory-level inference + `git rev-parse` double fallback
- In-place rewrite, tracked via git
- Implement humanizer.md
- Validate by running DSAA2011 ML Project end-to-end with sub-agent trace analysis

---

## 1. Path Discovery (P0 Fix)

### Problem

Sub-agent works in `data/homework/<COURSE>/<HWID>/`, skills are at repo root under
`sub-skills/tools/`. All references are relative paths. Sub-agent resolves
`sub-skills/tools/_index.md` relative to its CWD → file not found → entire skill
system bypassed.

### Solution: Two-layer fallback

**Layer 1 (primary): Directory level inference**

```text
WORK_DIR = data/homework/<COURSE>/<HWID>/
REPO_ROOT = WORK_DIR/../../..           # 3 levels up
SKILLS_DIR = REPO_ROOT/sub-skills/tools/
```

Written as a rule in `task-orchestrator.md` Step 1 and `do-homework.md [D]`.

**Layer 2 (fallback): `git rev-parse --show-toplevel`**

If the inference doesn't land on a valid `sub-skills/tools/_index.md`, run:

```bash
git -C "$WORK_DIR" rev-parse --show-toplevel
```

This returns the actual repo root regardless of directory depth.

**Implementation:**

- `do-homework.md [A2]`: after creating workbench, compute REPO_ROOT and write it
  into `pipeline_design.md` metadata header
- `task-orchestrator.md` Step 1: read REPO_ROOT from pipeline_design.md header;
  fallback to directory inference; final fallback to `git rev-parse`
- All skill file references in orchestrator use `REPO_ROOT + "/sub-skills/tools/..."`

**Why no `.skills-path` file:** The user chose directory inference over a separate
dotfile. `git rev-parse` is the insurance layer. No extra files to manage.

---

## 2. _index.md Refactor: Routing Table → Capability Menu

### Current

- Fixed routing table with 5 pipeline shapes (paper/slides/math/lab/video)
- "Pipeline Design Guidance" section tells agent what chains to run

### Target

- Pure capability menu: each skill's name, one-line description, inputs, outputs
- No pipeline routing, no fixed chains
- Common pipeline shapes moved to `do-homework.md [C]` as design guidance
- Progressive discovery: only top-level skills listed; appendices NOT listed

### What stays

- Tool registry table (but trimmed to essential columns)
- Capability vocabulary table
- "What is NOT a tool" section

### What moves

- "Pipeline Design Guidance" → `do-homework.md [C]`
- "How Orchestrator Uses This" → `task-orchestrator.md` Step 1

---

## 3. pipeline_design.md Format Unification

### Problem (P1)

Current format is free-form with "Tool Mapping" as a flat list. Agent doesn't know
which tool to use per stage.

### Target format (from spec §5, single definition source)

```markdown
# Pipeline: <COURSE> <assignment>

## Metadata
repo_root: <absolute path to repo root>    # injected by do-homework [A2]

## Output
- mode: mixed (code + doc_prose + slides)
- deliverables: [notebook.ipynb, report.pdf, ...]

## Constraints
- [quantifiable constraints extracted from spec]

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
- lang: en
- reads: spec.md, investigation/rubric.md, draft/notebook.ipynb outputs
- writes: draft/report.md
- verify: covers every rubric criterion, word count meets requirement
- review: true
- post-process: humanize     # optional
- fallback: if pdf-renderer fails → fpdf2 + quality downgrade note
- min_quality: PDF > 10KB, pages >= 5

## Human Review Items
- ...
```

`repo_root` in metadata solves path discovery (P0) at the source — every downstream
consumer reads it.

---

## 4. Unified Skill Template

Every skill file follows this structure. Skills provide **reference guidance** —
the model follows them as best practice, but specific task requirements in spec
always take precedence.

```markdown
---
name: <skill-name>
description: <one-line capability summary>
---

# <skill-name>

## Contract
- reads: [what files this skill reads from the workbench]
- writes: [what files this skill writes to the workbench]
- preconditions: [what must be true before this skill runs]

## Guidance
[Core domain guidance — "how we recommend doing it right here"]
[Reference quality, not hard constraints. Task spec overrides.]

## Appendices (loaded on demand)
- [list of appendix files with one-line descriptions]
[Agent reads parent skill first, then decides if appendix is needed]

## Post-processing
[Optional next steps after completion]
[Conditional references to other skills, e.g. "if post-process: humanize"]

## Self-check
- [ ] [verification item 1]
- [ ] [verification item 2]
```

Appendix files follow:

```markdown
---
name: <parent>-<specific>
description: <one-line summary, notes which parent loads it>
---

# <parent>-<specific>

Loaded by `<parent>` on demand. Do not load directly from `_index.md`.

## [Specific language/type/scenario guidance]
```

---

## 5. File-by-File Refactor Plan

### 5.1 Files to rewrite in-place (7 files)

#### `sub-skills/tools/_index.md`
- Remove: "Pipeline Design Guidance" section, "How Orchestrator Uses This"
- Keep: Tool registry (trimmed), capability vocabulary, "What is NOT a tool"
- Add: One-line note pointing to `do-homework.md [C]` for pipeline design guidance
- Role: Pure capability menu for agent to discover available tools

#### `sub-skills/tools/code-writer.md`
- Restructure to: Contract → Guidance → Appendices → Post-processing → Self-check
- Guidance: keep current Steps 1-5 as reference flow, not rigid script
- Appendices: list `code-writer-python.md` as on-demand
- Post-processing: mention test-runner handoff, optional humanizer
- Self-check: add verification items from audit P2 (code must execute, data not fabricated)

#### `sub-skills/tools/writing-helper.md`
- Restructure to same template
- Appendices: list `writing-helper-report.md` as on-demand
- Post-processing: optional humanizer if pipeline declares it
- Self-check: add items (no fabricated citations, rubric coverage)

#### `sub-skills/tools/pdf-renderer.md`
- Keep: existing tectonic/pandoc/xelatex paths (well-tested)
- Add: Post-processing fallback chain (tectonic → pandoc+xelatex → fpdf2)
- Add: Self-check (PDF > 1KB, magic bytes %PDF, page count)

#### `sub-skills/tasks/do-homework.md`
- [A2]: add repo_root computation and injection into pipeline_design.md
- [C]: add pipeline design guidance (common pipeline shapes from old _index.md)
- [C]: reference new pipeline_design.md format (stages with tool/reads/writes/verify)
- [D]: pass repo_root to task-orchestrator
- Cross-references: update to use absolute paths via repo_root

#### `sub-skills/tasks/task-orchestrator.md`
- Step 1: add path discovery (read repo_root from pipeline_design → fallback inference → fallback git rev-parse)
- Step 2: update pipeline_design format to new stage-based format
- Remove: old Pipeline Design Format section (now in do-homework [C])
- Cross-references: all skill paths via SKILLS_DIR

#### `docs/skills-architecture-spec.md`
- Add §2.4: path discovery rules (from audit recommendation)
- Update §5: add fallback/min_quality fields to pipeline_design format
- Add P5 note: sub-agent Write tool limitation + heredoc workaround

### 5.2 Files to create (3 files)

#### `sub-skills/tools/code-writer-python.md`
- Parent: `code-writer.md`
- Contents: Python-specific project conventions
  - uv for environment management (default, can be overridden by spec)
  - Project structure: src/ + tests/ + README.md (not flat)
  - pytest conventions (fixtures, parametrize, skip markers)
  - Notebook-specific: must execute and validate outputs (P2 fix)
  - These are reference defaults — if spec says "use pip + flat structure", follow spec

#### `sub-skills/tools/writing-helper-report.md`
- Parent: `writing-helper.md`
- Contents: Report type-specific structure guidance
  - Standard scientific report sections
  - Figure/table referencing conventions
  - Data must come from actual execution results (P2 fix)
  - LaTeX math in markdown conventions

#### `sub-skills/tools/humanizer.md`
- Loaded by: writing-helper Post-processing, or pipeline_design post-process declaration
- Role: **post-processing style guide** — tells the model how to adjust already-written
  text to reduce template-like and predictable patterns. NOT a round-trip translation step.
- Contents:
  - Sentence structure variation (avoid uniform subject-verb-object)
  - Vocabulary diversity (avoid overused academic filler phrases)
  - Paragraph rhythm variation (mix short and long sentences)
  - Avoid telltale AI patterns (numbered lists for everything, hedging with "it is
    important to note", meta-discourse like "In this section I will...")
  - Conditional: only loaded if pipeline_design declares `post-process: humanize`
    or user requests it at [B]

### 5.3 Files NOT modified

These files are adequate as-is or only need minor touches:
- `slide-maker.md` — already closest to template, 15 pitfalls, 2 paths
- `figure-maker.md` — stable, no audit issues
- `paper-search.md` — stable, has fallback already
- `test-runner.md` — minor: add hand-off section
- `canvascli-api.md` / `canvascli-setup.md` — data layer, not skill architecture
- `problem-extractor.md` — reconnaissance, not post-recon pipeline
- `sync-status.md` — separate task, not affected

---

## 6. Sub-agent Environment Notes (P5)

The audit found that Write tool is restricted in sub-agent sandbox. Workaround:

- In skill Guidance sections, note: "If Write tool is restricted, use
  `Bash + cat > file <<'EOF' ... EOF` heredoc as alternative"
- The orchestrator should execute pipeline stages directly (not spawn sub-agents
  for each tool), which avoids sandbox restrictions
- If sub-agents are used for review (review: true stages), they are read-only
  and don't need Write access

---

## 7. Verification Plan

After refactoring, run the same test as the audit:

1. **Sub-agent execution**: spawn agent to run do-homework on DSAA2011 ML Project
   - Verify: skill files are read (P0 fixed)
   - Verify: pipeline_design.md has stage→tool mapping (P1 fixed)
   - Verify: notebook executes with real data (P2 fixed)
   - Verify: PDF generation uses fallback chain (P3 fixed)
   - Verify: standard directory structure used (P4 fixed)

2. **Sub-agent trace analysis**: spawn another agent to analyze JSONL execution trace
   - Compare against audit report timeline
   - Check: every skill file mentioned in pipeline_design is actually read
   - Check: Self-check items are verified
   - Collect any new issues

3. **Iteration loop**: fix issues → re-test → re-analyze → repeat until clean

---

## 8. Execution Order

1. Update `docs/skills-architecture-spec.md` (add audit findings)
2. Rewrite `_index.md` (capability menu)
3. Rewrite `code-writer.md` → create `code-writer-python.md`
4. Rewrite `writing-helper.md` → create `writing-helper-report.md`
5. Update `pdf-renderer.md` (fallback chain + self-check)
6. Create `humanizer.md`
7. Rewrite `do-homework.md` (path discovery + pipeline format + pipeline shapes)
8. Rewrite `task-orchestrator.md` (path discovery + new format)
9. Validate: sub-agent test → trace analysis → iterate
10. Update progress docs (agent-progress.md, feature-list.json, COLLABORATION.md)
