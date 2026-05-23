---
name: test-runner
description: Execute the code written by code-writer (pytest + plain run) and capture results to a markdown report. Used by lab / coding pipelines to verify the deliverable before submission.
---

# test-runner

Runs the tests + the entry-point script that `code-writer` produced. Captures stdout/stderr/return code into a markdown report the orchestrator can show the user.

## Capabilities

- `run_tests` — execute pytest + entry point → test_report.md with pass/fail summary

## Inputs / Outputs

```
Input:  <work_dir>/src/                   (Python files from code-writer)
        <work_dir>/src/test_*.py          (pytest test files)
        <work_dir>/spec_extras/input.txt  (optional, if entry point reads stdin)
Output: <work_dir>/test_report.md         (results summary)
        <work_dir>/test_report.json       (machine-readable for orchestrator)
```

## Setup

```bash
.venv/bin/pip install pytest              # if not already
```

(The MVP `pip install matplotlib numpy arxiv` doesn't pull pytest. If you reach this step and it's missing, install it.)

## Invocation

The orchestrator calls this as a single shell pipeline. Don't write a wrapper script — inline these commands.

### Step 1 — Run pytest

```bash
cd "<work_dir>/src"
.venv/bin/python -m pytest -v --tb=short 2>&1 | tee /tmp/pytest_output.txt
PYTEST_EXIT=${PIPESTATUS[0]}
echo "exit=$PYTEST_EXIT"
```

`PYTEST_EXIT`:
- 0 = all tests passed
- 1 = some tests failed
- 5 = no tests collected (often: code-writer didn't emit test files)
- other = configuration / collection error

### Step 2 — Run the entry point (if applicable)

If `<work_dir>/src/README.md` mentions a runnable entry point and `<work_dir>/spec_extras/input.txt` exists:

```bash
cd "<work_dir>/src"
.venv/bin/python solution.py < "../spec_extras/input.txt" > /tmp/solution_stdout.txt 2>&1
SOLUTION_EXIT=$?
```

Or if no stdin input expected:

```bash
.venv/bin/python solution.py > /tmp/solution_stdout.txt 2>&1
```

### Step 3 — Write the report

The agent reads `/tmp/pytest_output.txt`, `/tmp/solution_stdout.txt`, and writes `<work_dir>/test_report.md`:

```markdown
# Test Report — <assignment name>

## Pytest
- Collected: <N> tests
- Passed: <X>
- Failed: <Y>
- Exit code: <0/1/5>

### Failures
<short list of test names + 1-line reason, or "none">

## Entry point
- Command: `python solution.py < input.txt` (or "no input")
- Exit code: <code>
- Stdout (first 500 chars):
```
<paste first 500 chars>
```

## Verdict
<one of: "ready to submit", "needs fixing — see failures above", "incomplete — no tests ran">
```

And a parallel JSON:

```json
{
  "pytest": {"collected": 5, "passed": 5, "failed": 0, "exit": 0},
  "entry_point": {"command": "python solution.py", "exit": 0, "stdout_preview": "..."},
  "verdict": "ready to submit"
}
```

## What this tool is NOT for

- ❌ Writing the tests themselves — `code-writer.md` does that
- ❌ Debugging the code if tests fail — surface the failure to the user; don't auto-loop on rewrites
- ❌ Running shell-based test harnesses (Make, scripts/run_tests.sh) — MVP is pytest only
- ❌ Coverage measurement — MVP doesn't report coverage; add it if a course rubric demands

## Pitfalls

1. **`PYTEST_EXIT=${PIPESTATUS[0]}`** is bash-specific. In `sh`/`zsh`, use `set -o pipefail` and check `$?`. If running via `Bash` tool the shell is bash, so `PIPESTATUS` works.
2. **No tests collected (exit 5) often means file naming.** pytest only picks up `test_*.py` or `*_test.py`. If `code-writer` produced `solution_tests.py`, pytest ignores it — rename or use `pytest --collect-only` to debug.
3. **`subprocess` timeouts**: if the student's code has an infinite loop, pytest hangs. Wrap with `timeout 30s` on Linux, `gtimeout 30s` on macOS (via coreutils). Skip for MVP unless you actually hit a hang.
4. **Working directory matters.** `solution.py` may read relative paths. Always `cd "<work_dir>/src"` before running.
5. **`tee` swallows stderr** unless you `2>&1` first. The template above gets this right — don't strip it.
6. **Don't run with `--exitfirst`** for the report — you want the full test count, not just the first failure.
7. **The verdict line is for the user, not the grader.** "ready to submit" only means tests pass; it does not guarantee the lab passes the actual auto-grader.
