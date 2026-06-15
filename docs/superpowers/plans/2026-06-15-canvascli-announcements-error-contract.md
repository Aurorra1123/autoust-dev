# canvascli Announcements and Error Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `canvascli announcements` return complete current-term announcement snapshots when Canvas exposes term dates, add explicit announcement date controls, centralize CLI error handling, and sync AutoStudy's data-layer contract docs.

**Architecture:** Fix Canvas data behavior in `/Users/deepwisdom/Desktop/project/canvascli` first, then update `/Users/deepwisdom/Desktop/project/autoust-test` only against the new CLI contract. `canvascli` owns REST calls, default scope, date range derivation, and CLI errors; AutoStudy owns task/tool documentation and integration verification. No AutoStudy REST workaround is allowed.

**Tech Stack:** Python 3.9, `unittest`, Typer CLI, `requests`, local Canvas session via `.venv/bin/canvascli`, Markdown docs.

---

## File Structure

### canvascli

- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/terms.py`  
  Add a pure helper for selected-course term date ranges.
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/resources/announcements.py`  
  Pass term-derived or explicit `start_date`/`end_date` into Canvas announcements API.
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`  
  Add announcement date options, option validation, and a centralized CLI error boundary used by all commands that emit JSON.
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_terms.py`  
  Unit tests for date range derivation.
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_announcements.py`  
  Unit tests for announcements API parameters and course-scoped term lookup.
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_cli_errors.py`  
  Unit tests for no-traceback HTTP/network CLI failures.
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/README.md`  
  Document announcement defaults, explicit date options, and concise error behavior.

### AutoStudy

- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tools/canvascli-api.md`  
  Update the agent-facing CLI contract for announcements and errors.
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tools/assignment-recon.md`  
  Clarify that default announcements are complete current-term snapshots when Canvas exposes term dates.
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tasks/sync-course.md`  
  Prefer course-scoped announcement archive calls after the `canvascli` fix.
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/docs/PITFALLS.md`  
  Record the Canvas announcements implicit date-window pitfall.
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/docs/progress/agent-progress.md`  
  Record implementation and verification evidence.
- Optional Modify: `/Users/deepwisdom/Desktop/project/autoust-test/docs/plans/feature-list.json`  
  Update only if this feature list already tracks `canvascli` announcement behavior.

---

### Task 1: canvascli Term Date Range Helper

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/terms.py`
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_terms.py`

- [ ] **Step 1: Write failing tests for selected-course date ranges**

Create `/Users/deepwisdom/Desktop/project/canvascli/tests/test_terms.py`:

```python
import unittest

from canvascli.terms import term_date_range


class TermDateRangeTests(unittest.TestCase):
    def test_uses_earliest_term_start_and_latest_term_end(self):
        courses = [
            {
                "id": 1,
                "term": {
                    "start_at": "2026-01-14T16:00:00Z",
                    "end_at": "2026-06-13T16:00:00Z",
                },
            },
            {
                "id": 2,
                "term": {
                    "start_at": "2026-01-15T16:00:00Z",
                    "end_at": "2026-06-14T16:00:00Z",
                },
            },
        ]

        self.assertEqual(
            term_date_range(courses),
            ("2026-01-14T16:00:00Z", "2026-06-14T16:00:00Z"),
        )

    def test_falls_back_to_course_dates_when_term_dates_are_missing(self):
        courses = [
            {
                "id": 1,
                "start_at": "2026-01-10T00:00:00Z",
                "end_at": "2026-06-20T00:00:00Z",
                "term": {"name": "2025-26 Spring"},
            }
        ]

        self.assertEqual(
            term_date_range(courses),
            ("2026-01-10T00:00:00Z", "2026-06-20T00:00:00Z"),
        )

    def test_returns_none_when_any_selected_course_lacks_a_start(self):
        courses = [
            {
                "id": 1,
                "term": {"end_at": "2026-06-13T16:00:00Z"},
            }
        ]

        self.assertIsNone(term_date_range(courses))

    def test_returns_none_when_any_selected_course_lacks_an_end(self):
        courses = [
            {
                "id": 1,
                "term": {"start_at": "2026-01-14T16:00:00Z"},
            }
        ]

        self.assertIsNone(term_date_range(courses))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_terms -v
```

Expected: FAIL with `ImportError` or `AttributeError` because `term_date_range` does not exist yet.

- [ ] **Step 3: Implement the minimal helper**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/terms.py`, add this public helper after `available_terms()`:

```python
def term_date_range(courses: Iterable[dict]) -> tuple[str, str] | None:
    """Return earliest start and latest end for selected courses.

    Canvas term dates are preferred. Course-level dates are a fallback for
    instances that omit term bounds. If any selected course lacks either side,
    return None so callers do not trigger Canvas's implicit date defaults.
    """
    starts: list[tuple[datetime, str]] = []
    ends: list[tuple[datetime, str]] = []

    for course in courses:
        term = course.get("term") or {}
        start = term.get("start_at") or course.get("start_at")
        end = term.get("end_at") or course.get("end_at")
        if not start or not end:
            return None
        starts.append((_parse_canvas_time(start), start))
        ends.append((_parse_canvas_time(end), end))

    if not starts or not ends:
        return None

    return (
        min(starts, key=lambda item: item[0])[1],
        max(ends, key=lambda item: item[0])[1],
    )
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_terms -v
```

Expected: PASS.

- [ ] **Step 5: Run existing canvascli tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add canvascli/terms.py tests/test_terms.py
git commit -m "feat: derive Canvas term date ranges"
```

---

### Task 2: canvascli Announcement Date Scope

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/resources/announcements.py`
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_announcements.py`

- [ ] **Step 1: Write failing resource-layer tests**

Create `/Users/deepwisdom/Desktop/project/canvascli/tests/test_announcements.py`:

```python
import unittest

from canvascli.resources.announcements import list_announcements


class FakeClient:
    def __init__(self):
        self.current_term_calls = []
        self.get_calls = []
        self.paginate_calls = []
        self.term_courses = [
            {
                "id": 2799,
                "name": "AIAA2711 (L02) - Mathematics for AI",
                "term": {
                    "start_at": "2026-01-14T16:00:00Z",
                    "end_at": "2026-06-13T16:00:00Z",
                },
            }
        ]
        self.course_meta = {
            "id": 2799,
            "name": "AIAA2711 (L02) - Mathematics for AI",
            "term": {
                "start_at": "2026-01-14T16:00:00Z",
                "end_at": "2026-06-13T16:00:00Z",
            },
        }

    def current_term_courses(self, term_name=None):
        self.current_term_calls.append(term_name)
        return self.term_courses

    def get(self, path, params=None):
        self.get_calls.append((path, params))
        return self.course_meta

    def paginate(self, path, params=None):
        self.paginate_calls.append((path, params))
        return [
            {
                "id": 28133,
                "title": "Final Grades",
                "context_code": "course_2799",
                "posted_at": "2026-06-07T08:50:19Z",
                "html_url": "https://canvas.example.edu/courses/2799/discussion_topics/28133",
                "message": "<p>Done</p>",
            }
        ]


class AnnouncementScopeTests(unittest.TestCase):
    def test_default_listing_uses_term_date_range(self):
        client = FakeClient()

        result = list_announcements(client)

        self.assertEqual(result[0]["course_id"], 2799)
        self.assertEqual(client.current_term_calls, [None])
        self.assertEqual(client.paginate_calls[0][0], "/api/v1/announcements")
        self.assertEqual(
            client.paginate_calls[0][1],
            {
                "context_codes[]": ["course_2799"],
                "active_only": "true",
                "start_date": "2026-01-14T16:00:00Z",
                "end_date": "2026-06-13T16:00:00Z",
            },
        )

    def test_explicit_dates_override_term_date_range(self):
        client = FakeClient()

        list_announcements(
            client,
            start_date="2026-02-01",
            end_date="2026-02-28",
        )

        self.assertEqual(
            client.paginate_calls[0][1],
            {
                "context_codes[]": ["course_2799"],
                "active_only": "true",
                "start_date": "2026-02-01",
                "end_date": "2026-02-28",
            },
        )

    def test_missing_term_dates_passes_no_partial_date_range(self):
        client = FakeClient()
        client.term_courses = [{"id": 2799, "name": "AIAA2711", "term": {"start_at": None, "end_at": None}}]

        list_announcements(client)

        self.assertEqual(
            client.paginate_calls[0][1],
            {
                "context_codes[]": ["course_2799"],
                "active_only": "true",
            },
        )

    def test_course_id_fetches_course_with_term_include(self):
        client = FakeClient()

        list_announcements(client, course_id=2799)

        self.assertEqual(
            client.get_calls,
            [("/api/v1/courses/2799", {"include[]": "term"})],
        )
        self.assertEqual(
            client.paginate_calls[0][1]["context_codes[]"],
            ["course_2799"],
        )
        self.assertEqual(
            client.paginate_calls[0][1]["start_date"],
            "2026-01-14T16:00:00Z",
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run resource tests to verify they fail**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_announcements -v
```

Expected: FAIL because `list_announcements()` does not accept `start_date`/`end_date`, does not fetch `include[]=term` for `--course-id`, and does not pass dates.

- [ ] **Step 3: Update announcement resource implementation**

Replace `/Users/deepwisdom/Desktop/project/canvascli/canvascli/resources/announcements.py` with this implementation:

```python
"""Announcements across term-scoped courses."""
from __future__ import annotations
from typing import Optional

from ..client import CanvasClient
from ..terms import term_date_range


def list_announcements(
    client: CanvasClient,
    *,
    term_name: Optional[str] = None,
    course_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list:
    if course_id is not None:
        courses = [client.get(f"/api/v1/courses/{course_id}", {"include[]": "term"})]
    else:
        courses = client.current_term_courses(term_name)
    if not courses:
        return []

    context_codes = [f"course_{c['id']}" for c in courses]
    course_names = {c["id"]: c.get("name") for c in courses}

    params = {"context_codes[]": context_codes, "active_only": "true"}
    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
    else:
        derived_range = term_date_range(courses)
        if derived_range:
            params["start_date"], params["end_date"] = derived_range

    anns = client.paginate("/api/v1/announcements", params)

    out = []
    for a in anns:
        ctx = a.get("context_code", "")
        cid = int(ctx.replace("course_", "")) if ctx.startswith("course_") else None
        out.append({
            "id": a["id"],
            "title": a.get("title"),
            "course_id": cid,
            "course_name": course_names.get(cid),
            "posted_at": a.get("posted_at"),
            "html_url": a.get("html_url"),
            "message": a.get("message"),
        })
    out.sort(key=lambda x: x.get("posted_at") or "", reverse=True)
    return out
```

- [ ] **Step 4: Add CLI options and validation**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`, update the `announcements()` command signature and body:

```python
@app.command()
def announcements(
    course_id: Optional[int] = typer.Option(None, "--course-id"),
    term: Optional[str] = typer.Option(None, "--term", help="Canvas term name for all-course listing"),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="Announcement window start date/datetime"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="Announcement window end date/datetime"),
    pretty: bool = typer.Option(False, "--pretty"),
) -> None:
    """List announcements across enrolled courses."""
    if course_id is not None and term:
        typer.echo("error: --term cannot be combined with --course-id", err=True)
        raise typer.Exit(code=2)
    if (start_date is None) != (end_date is None):
        typer.echo("error: --start-date and --end-date must be provided together", err=True)
        raise typer.Exit(code=2)
    client = _client()
    _emit_or_auth_error(
        lambda: r_anns.list_announcements(
            client,
            course_id=course_id,
            term_name=term,
            start_date=start_date,
            end_date=end_date,
        ),
        pretty,
    )
```

- [ ] **Step 5: Run resource tests to verify they pass**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_announcements -v
```

Expected: PASS.

- [ ] **Step 6: Run CLI help verification**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
.venv/bin/canvascli announcements --help
```

Expected: Help includes `--course-id`, `--term`, `--start-date`, `--end-date`, and `--pretty`.

- [ ] **Step 7: Run all canvascli tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 2**

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add canvascli/resources/announcements.py canvascli/__main__.py tests/test_announcements.py
git commit -m "fix: scope announcements to Canvas term dates"
```

---

### Task 3: canvascli Unified CLI Error Boundary

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_cli_errors.py`

- [ ] **Step 1: Write failing no-traceback CLI error tests**

Create `/Users/deepwisdom/Desktop/project/canvascli/tests/test_cli_errors.py`:

```python
import unittest
from unittest.mock import patch

import requests
from requests import Response
from typer.testing import CliRunner

from canvascli.__main__ import app


def http_error(status_code=403, reason="Forbidden", url="https://canvas.example.edu/api/v1/courses/2177"):
    response = Response()
    response.status_code = status_code
    response.reason = reason
    response.url = url
    error = requests.HTTPError(f"{status_code} Client Error: {reason} for url: {url}")
    error.response = response
    return error


class CliErrorTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_http_403_is_concise_exit_2_without_traceback(self):
        with patch("canvascli.__main__._client", return_value=object()):
            with patch(
                "canvascli.__main__.r_anns.list_announcements",
                side_effect=http_error(403, "Forbidden"),
            ):
                result = self.runner.invoke(app, ["announcements", "--course-id", "2177"])

        self.assertEqual(result.exit_code, 2)
        combined_output = result.stdout + (result.stderr or "")
        self.assertIn("error: Canvas request failed: 403 Forbidden", combined_output)
        self.assertIn("/api/v1/courses/2177", combined_output)
        self.assertNotIn("Traceback", combined_output)

    def test_http_500_is_concise_exit_1_without_traceback(self):
        with patch("canvascli.__main__._client", return_value=object()):
            with patch(
                "canvascli.__main__.r_anns.list_announcements",
                side_effect=http_error(500, "Internal Server Error", "https://canvas.example.edu/api/v1/announcements"),
            ):
                result = self.runner.invoke(app, ["announcements"])

        self.assertEqual(result.exit_code, 1)
        combined_output = result.stdout + (result.stderr or "")
        self.assertIn("error: Canvas request failed: 500 Internal Server Error", combined_output)
        self.assertNotIn("Traceback", combined_output)

    def test_timeout_is_concise_exit_1_without_traceback(self):
        with patch("canvascli.__main__._client", return_value=object()):
            with patch(
                "canvascli.__main__.r_anns.list_announcements",
                side_effect=requests.Timeout("timed out"),
            ):
                result = self.runner.invoke(app, ["announcements"])

        self.assertEqual(result.exit_code, 1)
        combined_output = result.stdout + (result.stderr or "")
        self.assertIn("error: Canvas request failed: Timeout", combined_output)
        self.assertNotIn("Traceback", combined_output)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run error tests to verify they fail**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_cli_errors -v
```

Expected: FAIL because `_emit_or_auth_error()` only catches `AuthError`.

- [ ] **Step 3: Add centralized error formatting**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`, add imports near the top:

```python
from urllib.parse import urlparse
import requests
```

Replace `_emit_or_auth_error()` with:

```python
def _safe_url_for_error(url: str | None) -> str:
    if not url:
        return "unknown URL"
    parsed = urlparse(url)
    if not parsed.scheme:
        return url.split("?")[0]
    safe_path = parsed.path or "/"
    return safe_path


def _exit_code_for_http(status_code: int | None) -> int:
    if status_code in (400, 401, 403, 404):
        return 2
    if status_code is not None and 400 <= status_code < 500:
        return 2
    return 1


def _emit_or_auth_error(data_func, pretty: bool) -> None:
    try:
        data = data_func()
    except AuthError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=2)
    except requests.HTTPError as e:
        response = e.response
        status_code = response.status_code if response is not None else None
        reason = response.reason if response is not None else type(e).__name__
        url = _safe_url_for_error(response.url if response is not None else None)
        if status_code is None:
            typer.echo(f"error: Canvas request failed: {e}", err=True)
            raise typer.Exit(code=1)
        typer.echo(
            f"error: Canvas request failed: {status_code} {reason} for {url}",
            err=True,
        )
        raise typer.Exit(code=_exit_code_for_http(status_code))
    except (
        requests.ConnectionError,
        requests.Timeout,
        requests.SSLError,
    ) as e:
        typer.echo(f"error: Canvas request failed: {type(e).__name__}: {e}", err=True)
        raise typer.Exit(code=1)
    except RuntimeError as e:
        typer.echo(f"error: Canvas request failed: {e}", err=True)
        raise typer.Exit(code=1)
    _emit(data, pretty)
```

- [ ] **Step 4: Run error tests to verify they pass**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_cli_errors -v
```

Expected: PASS.

- [ ] **Step 5: Run all canvascli tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 3**

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add canvascli/__main__.py tests/test_cli_errors.py
git commit -m "fix: report Canvas CLI errors without tracebacks"
```

---

### Task 4: Apply Error Boundary to Remaining canvascli Commands

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_cli_errors.py`

- [ ] **Step 1: Add tests for commands that currently bypass the boundary**

Append to `CliErrorTests` in `/Users/deepwisdom/Desktop/project/canvascli/tests/test_cli_errors.py`:

```python
    def test_folders_uses_concise_error_boundary(self):
        with patch("canvascli.__main__._client", return_value=object()):
            with patch(
                "canvascli.__main__.r_files.list_folder_tree",
                side_effect=http_error(404, "Not Found", "https://canvas.example.edu/api/v1/courses/999/folders"),
            ):
                result = self.runner.invoke(app, ["folders", "999"])

        self.assertEqual(result.exit_code, 2)
        combined_output = result.stdout + (result.stderr or "")
        self.assertIn("error: Canvas request failed: 404 Not Found", combined_output)
        self.assertNotIn("Traceback", combined_output)

    def test_download_plan_uses_concise_error_boundary(self):
        with patch("canvascli.__main__._client", return_value=object()):
            with patch(
                "canvascli.__main__.r_files.plan_folder_download",
                side_effect=http_error(403, "Forbidden", "https://canvas.example.edu/api/v1/courses/2177/folders"),
            ):
                result = self.runner.invoke(
                    app,
                    ["download", "--course-id", "2177", "--folder-id", "1"],
                )

        self.assertEqual(result.exit_code, 2)
        combined_output = result.stdout + (result.stderr or "")
        self.assertIn("error: Canvas request failed: 403 Forbidden", combined_output)
        self.assertNotIn("Traceback", combined_output)

    def test_submit_uses_concise_error_boundary(self):
        with self.runner.isolated_filesystem():
            with open("answer.pdf", "wb") as f:
                f.write(b"%PDF-1.4\n")
            with patch("canvascli.__main__._client", return_value=object()):
                with patch(
                    "canvascli.__main__.r_submit.submit_assignment",
                    side_effect=http_error(403, "Forbidden", "https://canvas.example.edu/api/v1/courses/2799/assignments/1/submissions"),
                ):
                    result = self.runner.invoke(
                        app,
                        ["submit", "1", "answer.pdf", "--course-id", "2799"],
                    )

        self.assertEqual(result.exit_code, 2)
        combined_output = result.stdout + (result.stderr or "")
        self.assertIn("error: Canvas request failed: 403 Forbidden", combined_output)
        self.assertNotIn("submit failed:", combined_output)
        self.assertNotIn("Traceback", combined_output)
```

- [ ] **Step 2: Run the tests to verify at least folders/download/submit fail**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_cli_errors -v
```

Expected: FAIL for commands that still bypass `_emit_or_auth_error()`.

- [ ] **Step 3: Route `folders` through `_emit_or_auth_error()`**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`, replace the `folders()` body with:

```python
    client = _client()
    _emit_or_auth_error(lambda: r_files.list_folder_tree(client, course_id), pretty)
```

- [ ] **Step 4: Route `download` through `_emit_or_auth_error()`**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`, keep the user-option validation outside the wrapper, then wrap all data work:

```python
    client = _client()

    if file_id is not None:
        if not output:
            typer.echo("error: -o/--output required for single-file download", err=True)
            raise typer.Exit(code=2)
        _emit_or_auth_error(lambda: r_files.download_file(client, file_id, output), pretty)
        return

    if course_id is None or folder_id is None:
        typer.echo(
            "error: provide a single file_id, OR both --course-id and --folder-id",
            err=True,
        )
        raise typer.Exit(code=2)

    def run_download():
        plan = r_files.plan_folder_download(
            client, course_id, folder_id, dest_root, recursive=recursive,
        )
        if not execute:
            return plan
        if not plan["to_download"]:
            return {"status": "nothing_to_download", **plan}
        result = r_files.execute_folder_download(client, plan)
        return {"plan": plan, "result": result}

    _emit_or_auth_error(run_download, pretty)
```

- [ ] **Step 5: Route `submit` through `_emit_or_auth_error()`**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`, replace the `submit()` body with:

```python
    client = _client()
    _emit_or_auth_error(
        lambda: r_submit.submit_assignment(client, course_id, assignment_id, file),
        pretty,
    )
```

- [ ] **Step 6: Run focused error tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_cli_errors -v
```

Expected: PASS.

- [ ] **Step 7: Run all canvascli tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 4**

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add canvascli/__main__.py tests/test_cli_errors.py
git commit -m "fix: use CLI error boundary for file and submit commands"
```

---

### Task 5: canvascli Documentation and Live Verification

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/README.md`

- [ ] **Step 1: Update README command examples**

In `/Users/deepwisdom/Desktop/project/canvascli/README.md`, update the announcements section to include:

````markdown
### Announcements

```bash
canvascli announcements
canvascli announcements --course-id 2799
canvascli announcements --term "2025-26 Spring"
canvascli announcements --start-date 2026-01-14 --end-date 2026-06-13
```

By default, `announcements` follows the same current-term scope as `courses`,
`assignments`, and `files`. When Canvas exposes `term.start_at` and
`term.end_at`, those dates are sent to Canvas so the command returns the full
term announcement window instead of Canvas's implicit recent-window default.
If a Canvas instance omits term dates, `canvascli` falls back to Canvas's
default announcement window unless explicit dates are provided.
```
````

- [ ] **Step 2: Document concise error behavior**

Add this under the README output contract or troubleshooting section:

```markdown
Errors are written to stderr and successful JSON remains the only stdout
contract. HTTP 401 asks for `canvascli init`; 403/404 user-actionable request
errors exit with code 2; network and Canvas 5xx failures exit with code 1.
Python tracebacks are not printed for normal Canvas request failures.
```

- [ ] **Step 3: Run offline verification**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -m compileall canvascli
.venv/bin/canvascli announcements --help
```

Expected: tests pass, compile passes, help shows the new date options.

- [ ] **Step 4: Run live read-only Canvas verification**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
.venv/bin/canvascli whoami
.venv/bin/canvascli announcements --course-id 2799 > /tmp/canvascli-ann-2799.json
python3 - <<'PY'
import json
anns = json.load(open('/tmp/canvascli-ann-2799.json'))
print(len(anns))
print(anns[0]["title"] if anns else "NO_ANNOUNCEMENTS")
print(anns[-1]["title"] if anns else "NO_ANNOUNCEMENTS")
PY
```

Expected: the count is `23` for the current live AIAA2711 probe, unless Canvas data changes after this plan. If the count differs, inspect whether Canvas data changed before changing code.

- [ ] **Step 5: Verify forbidden course error is concise**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
set +e
.venv/bin/canvascli announcements --course-id 2177 > /tmp/canvascli-forbidden.out 2> /tmp/canvascli-forbidden.err
code=$?
set -e
printf 'exit=%s\n' "$code"
cat /tmp/canvascli-forbidden.out
cat /tmp/canvascli-forbidden.err
```

Expected: `exit=2`, empty stdout, stderr contains `error: Canvas request failed: 403 Forbidden` and `/api/v1/courses/2177`, and no `Traceback`.

- [ ] **Step 6: Commit Task 5**

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add README.md
git commit -m "docs: describe announcement date scope and errors"
```

---

### Task 6: AutoStudy Contract Docs Sync

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tools/canvascli-api.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tools/assignment-recon.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tasks/sync-course.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/docs/PITFALLS.md`

- [ ] **Step 1: Update `canvascli-api.md` announcements contract**

In `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tools/canvascli-api.md`, replace the current `### announcements` section with:

````markdown
### `announcements`
List announcements across courses. Defaults to the latest active Canvas term,
matching `courses`, `assignments`, and `files`.

```bash
.venv/bin/canvascli announcements
.venv/bin/canvascli announcements --course-id 2151
.venv/bin/canvascli announcements --term "2025-26 Spring"
.venv/bin/canvascli announcements --start-date 2026-01-14 --end-date 2026-06-13
```

When Canvas exposes `term.start_at` and `term.end_at`, `canvascli` passes those
dates to Canvas so the default command returns the full current-term
announcement window instead of Canvas's implicit recent-window default. If term
dates are missing, `canvascli` falls back to Canvas's default announcement
window unless explicit `--start-date` and `--end-date` are provided.

Users are not expected to know Canvas internal course IDs. Agents should
resolve course names/codes through `courses` first, then pass the resolved
`id` to `--course-id` when a course-scoped announcement call is needed.

Note: some Canvas instances rarely use announcements, so 0 results can still be
normal after the command has checked the correct scope.
```
````

- [ ] **Step 2: Update `canvascli-api.md` output and error contract**

In the output contract section of `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tools/canvascli-api.md`, ensure it says:

```markdown
- **stdout**: JSON success payload only.
- **stderr**: progress / status / errors. Canvas request failures are concise
  one-line errors, not Python tracebacks.
- **exit code**: `0` ok · `1` runtime/network/Canvas 5xx error · `2` user,
  auth, permission, not-found, or argument error.
```

- [ ] **Step 3: Clarify assignment reconnaissance announcement command**

In `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tools/assignment-recon.md`, replace the sentence after the announcements command with:

```markdown
With the fixed `canvascli` contract, the default announcements command is a
latest-active-term snapshot when Canvas exposes term dates. Zero announcements
is still a valid checked state: keep `canvas/announcements.json` as the Stage 1
record. If the command fails or Canvas lacks access, record the concise CLI
error in `investigation/unreachable.txt`; Stage 4 later records the
`announcements_checked` review field and decides whether the failure blocks
progress.
```

- [ ] **Step 4: Prefer course-scoped announcement sync**

In `/Users/deepwisdom/Desktop/project/autoust-test/sub-skills/tasks/sync-course.md`, update section `2f. Archive announcements` to use:

```bash
.venv/bin/canvascli announcements --course-id "$COURSE_ID" 2>/dev/null > /tmp/course_announcements.json
.venv/bin/python -c "
import json
course_ann = json.load(open('/tmp/course_announcements.json'))
course_ann = course_ann if isinstance(course_ann, list) else []
ann_path = '$COURSE_DIR/canvas_sync/announcements.json'
try:
    existing = json.load(open(ann_path))
    existing_ids = {a.get('id') for a in existing}
except (FileNotFoundError, json.JSONDecodeError):
    existing = []
    existing_ids = set()
merged = existing + [a for a in course_ann if a.get('id') not in existing_ids]
json.dump(merged, open(ann_path, 'w'), ensure_ascii=False, indent=2)
print(f'Announcements: {len(course_ann)} new, {len(merged)} total')
"
```

- [ ] **Step 5: Add the pitfall**

In `/Users/deepwisdom/Desktop/project/autoust-test/docs/PITFALLS.md`, add:

```markdown
## Canvas announcements have an implicit date window

Canvas's `/api/v1/announcements` endpoint applies default `start_date` and
`end_date` values when callers omit them. A command can therefore look like a
complete course announcement sync while only returning recent announcements.
AutoStudy should rely on `canvascli announcements`, whose contract is to use
the current term's full date range when Canvas exposes term dates. Do not
reimplement announcement REST calls in task docs.
```

- [ ] **Step 6: Run AutoStudy policy tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py tests/test_pipeline_ready_scan_flow.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 6**

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
git add sub-skills/tools/canvascli-api.md sub-skills/tools/assignment-recon.md sub-skills/tasks/sync-course.md docs/PITFALLS.md
git commit -m "docs: sync announcement CLI contract"
```

---

### Task 7: Cross-Repo Integration Verification and Progress Records

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/autoust-test/docs/progress/agent-progress.md`
- Optional Modify: `/Users/deepwisdom/Desktop/project/autoust-test/docs/plans/feature-list.json`

- [ ] **Step 1: Install or expose fixed canvascli to AutoStudy**

From AutoStudy, verify which `canvascli` is used:

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
.venv/bin/python -m pip show canvascli
.venv/bin/canvascli version
```

If the AutoStudy venv still points at the old installed package, install the local fixed data layer:

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
.venv/bin/python -m pip install -e /Users/deepwisdom/Desktop/project/canvascli
```

Expected: `.venv/bin/canvascli` imports the fixed local package.

- [ ] **Step 2: Run AutoStudy-layer read-only Canvas verification**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
.venv/bin/canvascli whoami
.venv/bin/canvascli announcements --course-id 2799 > /tmp/autostudy-ann-2799.json
.venv/bin/python - <<'PY'
import json
anns = json.load(open('/tmp/autostudy-ann-2799.json'))
print(len(anns))
print(anns[0]["title"] if anns else "NO_ANNOUNCEMENTS")
print(anns[-1]["title"] if anns else "NO_ANNOUNCEMENTS")
PY
```

Expected: count matches the fixed `canvascli` live verification, expected `23` for the current AIAA2711 probe unless Canvas data changed.

- [ ] **Step 3: Run AutoStudy default snapshot smoke test**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
.venv/bin/canvascli announcements > /tmp/autostudy-ann-default.json
.venv/bin/python - <<'PY'
import json
anns = json.load(open('/tmp/autostudy-ann-default.json'))
print(len(anns))
print(sorted({a.get("course_id") for a in anns if a.get("course_id")})[:10])
PY
```

Expected: command succeeds with JSON stdout. The exact count may vary with Canvas data, but it should no longer be constrained to Canvas's implicit recent-window behavior when term dates exist.

- [ ] **Step 4: Record progress evidence**

Append a dated entry to `/Users/deepwisdom/Desktop/project/autoust-test/docs/progress/agent-progress.md`:

```markdown
## 2026-06-15 — canvascli announcement scope and error contract

Fixed `canvascli` announcement scope so default announcement listings use the
selected Canvas term's full date range when term dates are available. Added
explicit `--start-date/--end-date` controls and centralized CLI request error
handling so HTTP/network failures no longer print Python tracebacks. Synced
AutoStudy's `canvascli-api`, assignment reconnaissance, course sync, and
pitfall docs to the new data-layer contract.

Verification:
- canvascli unittest discover: PASS
- canvascli compileall: PASS
- canvascli live AIAA2711 `announcements --course-id 2799`: 23 announcements if Canvas data is unchanged; otherwise record the observed integer and note that Canvas data changed
- forbidden `--course-id 2177`: concise stderr, exit 2, no traceback
- AutoStudy policy tests: PASS
- AutoStudy `.venv/bin/canvascli announcements --course-id 2799`: same observed count as the canvascli live verification
```

- [ ] **Step 5: Check feature list relevance**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
rg -n "announcement|announcements|canvascli" docs/plans/feature-list.json
```

If the feature list has a relevant `canvascli` or sync-status entry, update its evidence with the same concise verification record. Then validate JSON:

```bash
python3 -m json.tool docs/plans/feature-list.json > /tmp/feature-list.json
```

Expected: JSON validation succeeds. If no relevant entry exists, do not edit the feature list.

- [ ] **Step 6: Run final diff checks**

Run both repos:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git status --short
git diff --check

cd /Users/deepwisdom/Desktop/project/autoust-test
git status --short
git diff --check
```

Expected: only intentional committed or staged changes remain; no whitespace errors.

- [ ] **Step 7: Commit Task 7 AutoStudy records**

```bash
cd /Users/deepwisdom/Desktop/project/autoust-test
git add docs/progress/agent-progress.md docs/plans/feature-list.json
git commit -m "docs: record announcement contract verification"
```

If `feature-list.json` was not edited, omit it from `git add`.

---

## Final Verification Checklist

- [ ] `canvascli` has commits for data-layer behavior before AutoStudy docs commits.
- [ ] `canvascli announcements --course-id 2799` returns the full current-term announcement list when term dates are present.
- [ ] `canvascli announcements --course-id 2177` exits non-zero without a Python traceback.
- [ ] AutoStudy docs describe `canvascli` behavior as a contract, not by duplicating lower-layer implementation details.
- [ ] AutoStudy verification runs through `/Users/deepwisdom/Desktop/project/autoust-test/.venv/bin/canvascli`.
- [ ] No Canvas cookies, session files, raw sync snapshots, or credential material are committed.
