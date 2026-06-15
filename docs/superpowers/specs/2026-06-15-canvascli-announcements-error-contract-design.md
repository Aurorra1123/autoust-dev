# canvascli Announcements and Error Contract Design

## Status

Approved direction: change `canvascli announcements` from Canvas's implicit
recent-window behavior to the same current-term snapshot semantics used by
`courses`, `assignments`, and `files`; add explicit announcement date range
controls; centralize HTTP error handling; then update AutoStudy docs and verify
the application-layer workflows.

This design is ready for implementation planning. It covers `canvascli` data
layer changes first, followed by AutoStudy documentation and live contract
verification.

## Problem

AutoStudy depends on `canvascli` for Canvas data. The current announcements
command looks like a term-scoped snapshot command, but Canvas's announcements
REST endpoint applies its own date defaults when `start_date` and `end_date`
are omitted. As a result:

- `.venv/bin/canvascli announcements` only returns Canvas's default date
  window, not the full latest active term.
- `.venv/bin/canvascli announcements --course-id 2799` returned one AIAA2711
  announcement, while the same Canvas API call with the course term's
  `start_at` and `end_at` returned 23 announcements.
- AutoStudy assignment reconnaissance and course sync can incorrectly treat a
  partial announcement list as a complete checked state.
- Users naturally identify courses by course code or name, but the only
  scoped announcement option is `--course-id`.
- HTTP errors such as 403 currently bubble up as Python tracebacks for many
  commands.
- AutoStudy's `canvascli-api.md` documents only default and `--term`
  announcement examples even though the installed CLI supports `--course-id`.

## Evidence

Live HKUST(GZ) Canvas metadata confirms that course payloads requested with
`include[]=term` include term boundaries:

```text
AIAA2711 (L02)
term: 2025-26 Spring
start_at: 2026-01-14T16:00:00Z
end_at: 2026-06-13T16:00:00Z
```

Using those exact values against `/api/v1/announcements` for course `2799`
returned 23 announcements. The current `canvascli announcements --course-id
2799` returned only one because it sends:

```python
{"context_codes[]": ["course_2799"], "active_only": "true"}
```

without explicit dates.

The existing `canvascli.terms.is_course_active()` already uses `course.end_at`
and `course.term.end_at` to determine the active course set. The data needed to
compute a current-term announcement date range is already available in the
same course metadata path. `term.start_at` is not currently used anywhere, so
the implementation needs a small pure helper rather than a change to
`current_term_courses()` return type.

## Goals

1. `canvascli announcements` returns a complete latest-active-term
   announcement snapshot by default when selected courses expose reliable term
   dates.
2. `canvascli announcements --course-id <id>` returns announcements for the
   requested course's term by default when that course exposes reliable term
   dates.
3. Callers can override the announcement window with explicit `--start-date`
   and `--end-date`.
4. HTTP, network, and response-shape failures produce stable CLI errors instead
   of Python tracebacks.
5. AutoStudy docs describe the real announcement command contract, including
   `--course-id`, date range behavior, and error handling.
6. Verification covers unit tests in `canvascli`, live read-only Canvas probes,
   and AutoStudy workflow/doc checks.

## Non-Goals

- Adding Canvas OAuth or token authentication.
- Adding multi-profile Canvas account switching.
- Building a general natural-language course resolver in AutoStudy.
- Changing Canvas submission behavior.
- Downloading files or modifying Canvas content during verification.

## Announcement Scope Design

### Default Semantics

`canvascli announcements` should mirror the existing default scope for
`courses`, `assignments`, and `files`: latest active Canvas term.

Implementation shape:

1. Resolve courses through `client.current_term_courses(term_name)`.
2. Compute a date range from the selected courses' term metadata.
3. Call `/api/v1/announcements` with `context_codes[]`, `start_date`, and
   `end_date` when both dates are reliable.
4. Preserve existing output shape and sorting.

For a normal latest-active-term call, all selected courses should share the
same term. The date range should use the earliest available term `start_at` and
latest available term `end_at` across selected courses to avoid accidental data
loss if Canvas returns slightly mixed metadata.

### Course-Scoped Semantics

`canvascli announcements --course-id <id>` should fetch the course with
`include[]=term`, derive its term range, then query announcements for that
single course.

If a course lacks either `term.start_at` or `term.end_at`, the command should
fall back to Canvas's API default window unless the user supplied explicit
dates. The implementation must not pass only one derived date because Canvas
will apply a default for the other side and can still truncate results. The
documentation must call out this fallback because Canvas instances can omit
term dates.

### Term Range Helper

Add a pure helper in `canvascli.terms`, for example:

```python
def term_date_range(courses: Iterable[dict]) -> tuple[str, str] | None:
    ...
```

The helper should:

- Prefer `course["term"]["start_at"]` and `course["term"]["end_at"]`.
- Use `course["start_at"]` / `course["end_at"]` only as a fallback when term
  dates are missing.
- Return `None` unless it can produce both a start and an end.
- Use the earliest start and latest end across the selected courses.

Do not change `client.current_term_courses()` to return metadata wrappers. It
is already shared by assignments, files, courses, and announcements.

### Explicit Date Range

Add options:

```text
--start-date TEXT
--end-date TEXT
```

The values are passed through to Canvas. Accept Canvas-compatible dates or
datetimes such as `2026-01-14`, `2026-01-14T16:00:00Z`, and
`2026-06-13T16:00:00Z`.

Rules:

- If either explicit date is supplied, require both explicit dates.
- Explicit dates override term-derived dates.
- `--term` remains valid only for all-course listing.
- `--course-id` and `--term` should be mutually exclusive to avoid a
  misleading course/term mismatch.

### Course Code or Name Resolution

Do not add course-code resolution in this slice. The immediate bug is data
completeness and error handling. AutoStudy can resolve user-facing course names
by calling `canvascli courses --all-terms` or the default current-term course
list, then passing the resolved `id` to `canvascli announcements --course-id`.

This keeps `canvascli` small and preserves its current explicit-id command
style. A future slice can add `--course` if repeated user workflows justify it.

## Error Handling Design

### Central CLI Boundary

`__main__._emit_or_auth_error()` should become a general safe emit boundary,
not only an auth wrapper. It should catch:

- `AuthError`
- `requests.HTTPError`
- `requests.ConnectionError`
- `requests.Timeout`
- `requests.SSLError`
- `RuntimeError` raised by response-shape checks

The CLI should write errors to stderr and exit non-zero without tracebacks.
Successful commands continue to write JSON to stdout.

### Exit Codes

Use simple stable exit codes:

- `2`: auth, permission, not-found, and user-actionable request errors
  (`401`, `403`, `404`, invalid option combinations, missing session).
- `1`: network failures, Canvas `5xx`, invalid JSON/response-shape failures,
  and unexpected runtime errors.

The existing Typer validation and explicit option checks can keep using code
`2`.

### Error Message Format

The CLI should not emit JSON on stdout for failures because all current
commands use stdout only for successful data. Stderr should contain one concise
line:

```text
error: Canvas request failed: 403 Forbidden for /api/v1/courses/2177
```

For network failures:

```text
error: Canvas request failed: Timeout while requesting /api/v1/courses
```

Do not include cookie values, full query strings with sensitive data, or Python
tracebacks by default. A future `--debug` flag can expose stack traces if
needed, but that is out of scope.

### Existing Safe Context Helpers

`canvascli.resources.context.safe_get()` and `safe_paginate()` currently
normalize some endpoint failures into returned JSON objects for exploratory
context commands. Keep that behavior for commands where 404 means a disabled
Canvas feature, such as front pages, modules, or pages.

The new CLI boundary handles failures that still escape those helpers and all
top-level list/detail commands.

## AutoStudy Design

### API Reference

Update `sub-skills/tools/canvascli-api.md`:

- Document `announcements --course-id <cid>`.
- Document `--start-date` and `--end-date`.
- State that default announcements are intended to be current-term complete
  snapshots when Canvas exposes term dates.
- Explain the fallback when a Canvas course lacks term dates.
- Record the new stderr/exit-code error contract.

### Assignment Reconnaissance

`sub-skills/tools/assignment-recon.md` can keep calling:

```bash
.venv/bin/canvascli announcements > "<work_dir>/canvas/announcements.json"
```

After the `canvascli` fix, that command becomes the current-term complete
snapshot it already claims to collect when term dates are available. No
app-layer REST workaround should be added.

### Course Sync

`sub-skills/tasks/sync-course.md` currently archives announcements by running
global announcements and filtering by `course_id`. Once `canvascli`
announcements is fixed, that remains valid. For better efficiency, a later
refinement can call `announcements --course-id "$COURSE_ID"`, but the required
fix for this slice is documentation and verification, not a flow rewrite.

### User-Facing Course Names

AutoStudy should continue resolving user phrases like "AIAA2711" or "2177 这个
课" through course lists before calling course-id-scoped commands. The spec
does not require a new resolver implementation, but the docs should make the
agent responsibility explicit: users are not expected to know Canvas internal
ids.

## Testing and Verification

### canvascli Unit Tests

Add tests for:

- `term_date_range()` returns earliest start and latest end across selected
  courses.
- `term_date_range()` returns `None` when either side is unavailable.
- `list_announcements()` includes term-derived `start_date` and `end_date`.
- explicit date options override term-derived dates.
- missing term dates fall back to Canvas's default window by passing neither
  date.
- `--course-id` fetches course metadata with `include[]=term`.
- HTTP 403 and 404 do not print tracebacks and exit with code `2`.
- network errors exit with code `1`.

Use fake clients or Typer's `CliRunner`; do not require live Canvas for unit
tests.

### canvascli Local Verification

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall canvascli
.venv/bin/canvascli announcements --help
.venv/bin/canvascli announcements --course-id 2799
```

The live course `2799` should return the full current-term AIAA2711
announcement list, matching the 23-item probe observed during design.

Also verify a forbidden course id no longer prints a traceback:

```bash
.venv/bin/canvascli announcements --course-id 2177
```

Expected: concise stderr error, exit code `2`, empty stdout.

### AutoStudy Verification

After installing or invoking the fixed `canvascli` from AutoStudy:

```bash
.venv/bin/canvascli announcements --course-id 2799
.venv/bin/canvascli announcements
```

Then verify docs and policy tests:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py tests/test_pipeline_ready_scan_flow.py -q
```

No AutoStudy workflow should parse Python tracebacks or depend on Canvas's
implicit announcement date window.

## Rollout Order

1. Update and test `canvascli`.
2. Verify live read-only Canvas announcement behavior in `canvascli`.
3. Update AutoStudy docs to the new CLI contract.
4. Run AutoStudy policy tests.
5. Re-run the read-only AutoStudy-layer announcement commands from this
   repository's `.venv`.

## Open Decisions

No open design decisions remain. The default behavior changes to current-term
complete announcements when Canvas exposes both term start and end dates. If
term dates are incomplete, the command preserves Canvas's default behavior
rather than sending a partial date range.
