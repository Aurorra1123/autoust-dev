---
name: scraper-api
description: Reference for calling the Canvas scraper modules. Use whenever you need to fetch data from Canvas or download files.
---

# Scraper API Reference

The scraper is a Python package at `scraper/`. All modules are invoked as `python -m scraper.<name>` from the repo root, using `.venv/bin/python`.

If `.auth/canvas_state.json` doesn't exist, run `scraper-setup.md` first.

## Modules at a glance

| Module | Purpose | Output |
|---|---|---|
| `scraper.login` | One-time SSO, saves cookie | `.auth/canvas_state.json` |
| `scraper.fetch_courses` | Courses + assignments | `data/courses.json`, `data/assignments.json` |
| `scraper.fetch_announcements` | Announcements across courses | `data/announcements.json` |
| `scraper.fetch_modules` | Module structure per course | `data/modules.json` |
| `scraper.fetch_files` | File listing (no download) | `data/files.json` |
| `scraper.fetch_quizzes_discussions` | Quizzes + discussions | `data/quizzes.json`, `data/discussions.json` |
| `scraper.download` | Folder-based file download | `data/files/<course>/<folder>/...`, `.state/downloads.json` |

All `fetch_*` modules print a human-readable summary to stdout, and write structured JSON to `data/`. The JSON is the authoritative source — parse it, don't parse stdout.

## Common pattern (typical task)

```bash
# 1. Make sure data is fresh
.venv/bin/python -m scraper.fetch_courses
.venv/bin/python -m scraper.fetch_announcements

# 2. Read JSON, process, present to user
cat data/assignments.json | jq '.[] | select(.submission_state == "unsubmitted")'
```

## Module: `scraper.fetch_courses`

Fetches current-term courses + all their assignments (with submission state).

**Run**: `.venv/bin/python -m scraper.fetch_courses`

**Output JSON shape**:
```json
// data/courses.json
[{"id": 2151, "name": "DSAA2043 (L01) - Design and Analysis of Algorithms"}, ...]

// data/assignments.json
[{
  "id": 12345,
  "name": "Homework 3",
  "course_id": 2151,
  "course_name": "DSAA2043 (L01) - ...",
  "due_at": "2025-11-13T15:59:00Z",   // ISO 8601 UTC; may be null
  "html_url": "https://hkust-gz.instructure.com/...",
  "submission_state": "graded"   // or: submitted, unsubmitted, pending_review, null
}, ...]
```

**Current term is hardcoded** in `scraper/api.py:CURRENT_TERM`. Update there when the term rolls over.

## Module: `scraper.fetch_announcements`

**Run**: `.venv/bin/python -m scraper.fetch_announcements`

**Output**: `data/announcements.json` — flat list, sorted by `posted_at` descending. Includes `message` (HTML, may need sanitization before showing to user).

**Note**: HKUST(GZ) instructors rarely use Canvas announcements (seen 0/6 in 2025-26 Fall). Don't be surprised if empty.

## Module: `scraper.fetch_modules`

**Run**: `.venv/bin/python -m scraper.fetch_modules`

**Output**: `data/modules.json` — `[{course_id, course_name, modules: [{name, items: [...]}]}]`. Item types: `File`, `Assignment`, `Quiz`, `Page`, `ExternalUrl`, etc.

**Coverage caveat**: ~half of courses don't use Modules. Don't assume every course has them.

## Module: `scraper.fetch_files`

**Run**: `.venv/bin/python -m scraper.fetch_files` (no download, just lists)

**Output**: `data/files.json` — per-course file listings with size + url + content_type.

**This is the most reliable view of course materials** — even courses that don't use Modules still have everything under Files.

## Module: `scraper.download`

Folder-based downloader with state tracking. **Three CLI modes** — pick based on what the task needs.

### List courses
```bash
.venv/bin/python -m scraper.download --list
# →   [2515] DLED3020 (L01)  —  ...
#     [2387] DSAA2012 (L01)  —  Deep Learning
```

### List folders in a course
```bash
.venv/bin/python -m scraper.download --list --course-id 2151
# → [folder_id] indent name (file_count, size)
#   [53520]  course files  (26 files, 41.6 MB)
#   [66610]    DSAA_2043_Spring_2025_Midterm_Exam  (2 files, 163.6 KB)
#   [63181]    Paper Exercises  (8 files, 3.1 MB)
```

### Dry-run plan (default — no download)
```bash
.venv/bin/python -m scraper.download --course-id 2151 --folder-id 66610
# Prints: which files would be downloaded, which would be skipped (already present + unchanged)
```

### Execute download
```bash
.venv/bin/python -m scraper.download --course-id 2151 --folder-id 66610 --execute
# Add --recursive to include subfolders.
```

**Increments**: re-running with same args skips files where local path exists AND `file_id` AND `updated_at` all match. State is in `.state/downloads.json`.

**Files land at**: `data/files/<course_short>/<folder_name>/<file>`. Both folder names are sanitized for filesystem (only `/ \ : * ? " < > |` are replaced; Chinese characters and spaces are preserved).

### Programmatic use (from a tool/task skill)

```python
from scraper.api import CanvasClient
from scraper.download import list_courses, list_folder_tree, plan_download, execute_download

with CanvasClient() as c:
    courses = list_courses(c)
    tree = list_folder_tree(c, course_id=2151)
    plan = plan_download(c, course_id=2151, folder_id=66610, course_name="DSAA2043 ...")
    if plan["to_download"]:
        execute_download(c, plan)
```

Use this when you need to drive the 3-step flow with `AskUserQuestion` instead of CLI flags.

## Safety rules

1. **Never download without asking the user.** Use `AskUserQuestion` to confirm course + folder + scope.
2. **Never log or echo `.auth/canvas_state.json`** or any cookie value.
3. **Don't auto-pick "the latest" anything** — the user must explicitly choose.
4. **Treat `401` as cookie expiration** — point user back to `scraper-setup.md` step 2, don't retry.
5. **Don't parse stdout from `fetch_*` modules** — parse the JSON files in `data/`.
