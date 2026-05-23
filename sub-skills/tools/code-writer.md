---
name: code-writer
description: Write Python (or other language) source files from a lab assignment spec. The agent authors the code in-context and saves it to work_dir/src/. test-runner.md handles execution.
---

# code-writer

Lab / programming assignment workhorse. Reads the assignment description + rubric, writes source files into `<work_dir>/src/`. **The agent writes the code directly** — same philosophy as `writing-helper`. This file is the spec + style guide.

## Capabilities

- `write_code` — assignment spec → src/*.py with module structure and a runnable entry point

## Inputs / Outputs

```
Input:  <work_dir>/task_profile.yaml       (language, constraints)
        <work_dir>/assignment.json         (lab spec, often with skeleton code)
        <work_dir>/spec_extras/*           (optional: starter code, data files, test cases the user provides)
Output: <work_dir>/src/<module>.py         (one file per module, runnable)
        <work_dir>/src/test_<module>.py    (one test file per module, pytest-style)
        <work_dir>/src/README.md           (how to run, expected output)
```

## Setup

No mandatory install (Python ships with the .venv). If the lab needs `numpy` / `torch` / etc., they should already be in `.venv` (matplotlib + numpy installed at MVP setup; user adds others as needed).

## Invocation (decision flow)

### Step 1 — Parse the spec

Read `assignment.json` `description`. Identify:
- Language (HKUST(GZ) labs are usually Python; some courses use C++ / Java — language goes in `task_profile.yaml`)
- Required functions / classes / entry points (look for "implement", "complete", "fill in")
- I/O contract (input format, expected output format)
- Test cases (if provided in description or `spec_extras/`)

### Step 2 — Write the code

Style rules (MVP):
- One responsibility per file. Don't dump everything into `solution.py`.
- Top of every file: a 1-line docstring stating what it does. No multi-paragraph docstrings.
- No comments unless the WHY is non-obvious (see CLAUDE.md style rules).
- Type hints on public functions.
- Use stdlib where possible. Only reach for `numpy` / external deps if the spec implies them.

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

1. **Don't include the assignment description as a docstring at top of the file.** Some labs auto-grade and the docstring tripping a keyword can cause false flags.
2. **`if __name__ == "__main__":` is mandatory** for any file that has a runnable entry — pytest imports the file, and module-level code at import time will break tests.
3. **Don't shadow stdlib names.** `solution.py` is fine; `os.py` / `sys.py` / `json.py` would break imports anywhere downstream.
4. **Path handling**: use `pathlib.Path(__file__).parent` to find files relative to the source — never hard-code `/Users/...` or `data/...`. The lab may be auto-graded in a different directory.
5. **Don't add `print()` debug statements in submitted code.** Auto-graders often parse stdout. Wrap diagnostics in `if __debug__:` or remove before submission.
6. **`random` and `numpy.random` need seeding** if the assignment requires reproducibility. Default to `seed=42` if the spec doesn't say.
7. **Be honest about gaps.** If the spec mentions something you couldn't implement, write a `TODO:` comment + a `pytest.skip` for that test — don't silently leave broken code that "looks" complete.
