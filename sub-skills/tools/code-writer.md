---
name: code-writer
description: Write Python (or other language) source files from a lab assignment spec. The agent authors the code in-context and saves it to work_dir/src/. test-runner.md handles execution.
---

# code-writer

Lab / programming assignment workhorse. Reads `spec.md` / `problem.md` + rubric, writes source files into `<work_dir>/src/`. **The agent writes the code directly** — same philosophy as `writing-helper`. This file is the spec + style guide.

## Capabilities

- `write_code` — assignment spec → src/*.py with module structure and a runnable entry point

## Inputs / Outputs

```
Input:  <work_dir>/task_profile.yaml       (language, constraints)
        <work_dir>/spec.md                 (PRIMARY: source-by-source assignment context)
        <work_dir>/problem.md              (compatibility grounded problem spec)
        <work_dir>/canvas/assignment.json  (metadata only: due_at, rubric, points)
        <work_dir>/spec_extras/*           (optional: starter code, data files, test cases the user provides)
Output: <work_dir>/src/<module>.py         (one file per module, runnable)
        <work_dir>/src/test_<module>.py    (one test file per module, pytest-style)
        <work_dir>/src/README.md           (how to run, expected output)
```

**Read `spec.md` first, then `problem.md`, completely.** The workbench files contain the actual lab spec — function signatures to implement, datasets to process, algorithms to write. The assignment title alone (e.g. "Project Report") tells you nothing about what to implement. If both files are missing or thin, refuse to proceed.

## Setup

No mandatory install (Python ships with the .venv). If the lab needs `numpy` / `torch` / etc., they should already be in `.venv` (matplotlib + numpy installed at MVP setup; user adds others as needed).

## Invocation (decision flow)

### Step 1 — Parse the spec from `spec.md` / `problem.md`

Read `spec.md` and `problem.md` end-to-end. From downloaded reference sections and source candidates, identify:

- **Language**: Python is default for HKUST(GZ) labs; some courses use C++ / Java. Language goes in `task_profile.yaml`.
- **Required functions / classes / entry points**: look for "implement", "complete", "you should write", function signatures spelled out. The spec usually names them explicitly (e.g. "implement `fit(X, y)` and `predict(X)`"); use those exact names.
- **I/O contract**: input format, expected output format, datasets (often included in the attachment or referenced by name).
- **Test cases**: if the spec provides input/output pairs, translate them into pytest in Step 3.
- **Algorithm constraints**: complexity bounds, allowed libraries, "don't use sklearn", "implement from scratch", etc.

If `problem.md` references a specific dataset, paper, or algorithm by name, implement THAT — not a generic equivalent. If the spec says "implement k-means with k-means++ initialization", you write k-means++; you do not write a generic clustering library.

If the spec is ambiguous on a specific point, write `[CLARIFICATION NEEDED: <question>]` as a comment in the relevant file and continue with a defensible default. Surfaced at do-homework [E].

### Step 2 — Write the code

Style rules (MVP):
- **Implement what `problem.md` actually asks.** Not a generic representative project. If the spec is about linear regression, write linear regression; do not write "regression + clustering + classification" as a representative sampling.
- One responsibility per file. Don't dump everything into `solution.py`.
- Top of every file: a 1-line docstring stating what it does. No multi-paragraph docstrings.
- No comments unless the WHY is non-obvious (see CLAUDE.md style rules).
- Type hints on public functions.
- Use stdlib where possible. Only reach for `numpy` / external deps if the spec implies them.
- **No `[TODO: align with actual project spec]` or equivalent placeholders.** The whole point of grounding via `problem.md` is to know what to implement. If you're unsure on a specific point, use `[CLARIFICATION NEEDED: <question>]` instead.

### Step 3 — Write the tests

For every public function, write at least one pytest test. Tests live in `<work_dir>/src/test_<module>.py`. Keep them focused — one assertion per test where possible.

If the assignment provides test cases (e.g. expected input/output pairs), translate them into pytest parametrize:

```python
import pytest
from solution import solve

@pytest.mark.parametrize("inputs,expected", [
    ([1, 2, 3], 6),
    ([], 0),
    ([-1, 1], 0),
])
def test_solve(inputs, expected):
    assert solve(inputs) == expected
```

### Step 4 — Write the README

`<work_dir>/src/README.md` — 5-10 lines:

```markdown
# <Assignment name>

Run:
    python solution.py < input.txt
    pytest test_solution.py

Expected output: <one line>

Notes:
- <any assumption the agent made>
```

### Step 5 — Hand off

The orchestrator then calls `test-runner.md` to verify the code passes its own tests. After test-runner confirms, `writing-helper` (if the assignment also asks for a report) drafts the prose; pdf-renderer combines.

## What this tool is NOT for

- ❌ Running the code — that's `test-runner.md`
- ❌ Writing the lab report prose — that's `writing-helper.md`
- ❌ Setting up project infrastructure (CMake, setup.py, etc.) — MVP assumes single-file or flat-module Python labs
- ❌ Debugging student-provided broken code — only write fresh code from a fresh spec

## Pitfalls

1. **`spec.md` / `problem.md` are the spec, NOT `assignment.description`.** The description is HTML and often just a file link or empty. Reading it directly produces "implement a representative project" template code. Always read the workbench files generated by `problem-extractor`.
2. **Don't include the assignment description as a docstring at top of the file.** Some labs auto-grade and the docstring tripping a keyword can cause false flags.
3. **`if __name__ == "__main__":` is mandatory** for any file that has a runnable entry — pytest imports the file, and module-level code at import time will break tests.
4. **Don't shadow stdlib names.** `solution.py` is fine; `os.py` / `sys.py` / `json.py` would break imports anywhere downstream.
5. **Path handling**: use `pathlib.Path(__file__).parent` to find files relative to the source — never hard-code `/Users/...` or `data/...`. The lab may be auto-graded in a different directory.
6. **Don't add `print()` debug statements in submitted code.** Auto-graders often parse stdout. Wrap diagnostics in `if __debug__:` or remove before submission.
7. **`random` and `numpy.random` need seeding** if the assignment requires reproducibility. Default to `seed=42` if the spec doesn't say.
8. **Be honest about gaps.** If the spec mentions something you couldn't implement, write `[CLARIFICATION NEEDED: <question>]` as a comment + a `pytest.skip` for that test — don't silently leave broken code that "looks" complete, and don't fall back to `[TODO: align with actual project spec]`-style template placeholders.
9. **Function/class names follow `problem.md` verbatim.** If the spec says `fit_ols(X, y)`, do not write `train_ordinary_least_squares(X, y)` — auto-graders match by name.
