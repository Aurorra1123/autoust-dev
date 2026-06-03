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
