---
name: canvascli-api
description: Reference for calling canvascli commands from agent flows. Use whenever you need to fetch Canvas data or perform a Canvas action.
---

# canvascli API reference

`canvascli` is the external Canvas command-line tool AutoStudy depends on. All commands are JSON-by-default — that's the contract that lets agents pipe its output into `jq` / Python / further processing.

If `canvascli` isn't installed yet, run `canvascli-setup.md` first.

## How to invoke

Always use the venv binary (assumes you've followed `canvascli-setup.md`):

```bash
.venv/bin/canvascli <command> [options]
```

Or, if the venv is activated:

```bash
canvascli <command>
```

## Output contract

- **stdout**: JSON (object or array). One line by default; `--pretty` indents.
- **stderr**: progress / status / errors. Safe to ignore when piping JSON.
- **exit code**: `0` ok · `1` runtime error · `2` user error (missing args, no session)

So the agent's typical idiom is:

```bash
.venv/bin/canvascli courses 2>/dev/null | jq '.[].name'
```

or in Python:

```python
import json, subprocess
out = subprocess.check_output([".venv/bin/canvascli", "courses"])
courses = json.loads(out)
```

## Command reference

### `init`
Explicit SSO login / refresh. This opens a browser and writes a new
`state.json`; it is not a status check. **Run in the user's own terminal or only
when the user is ready for the browser popup.**
```bash
.venv/bin/canvascli init
```

If the SSO page offers "remember login" / "trust this browser", ask the user to
select it. A successful `init` writes `state.json` either way; the checkbox only
affects whether the next SSO refresh can skip a full manual login.

### `whoami`
Verify the current saved session. Returns the user object without opening a
browser.
```bash
.venv/bin/canvascli whoami
```

### `courses`
List enrolled courses. Defaults to the latest active Canvas term.
```bash
.venv/bin/canvascli courses                  # latest active term, JSON
.venv/bin/canvascli courses --pretty         # human-readable
.venv/bin/canvascli courses --all-terms      # include past/future terms
.venv/bin/canvascli courses --term "2025-26 Spring"
```

Default term selection is owned by canvascli. AutoStudy treats it as a CLI
contract: call the default command for the normal current semester, and pass
`--term` only when the user explicitly asks for another semester.

Output shape (per item):
```json
{
  "id": 2151,
  "name": "DSAA2043 (L01) - Design and Analysis of Algorithms",
  "term": "2025-26 Fall",
  "course_code": "DSAA2043 (L01)"
}
```

### `assignments`
List assignments. Defaults to all courses in the latest active Canvas term.
```bash
.venv/bin/canvascli assignments
.venv/bin/canvascli assignments --course-id 2151
.venv/bin/canvascli assignments --term "2025-26 Spring"
```

Output shape (per item):
```json
{
  "id": 12345,
  "name": "Homework 3",
  "course_id": 2151,
  "course_name": "DSAA2043 (L01) - ...",
  "due_at": "2025-11-13T15:59:00Z",
  "points_possible": 100,
  "html_url": "https://hkust-gz.instructure.com/...",
  "submission_state": "graded",
  "submission_types": ["online_upload"]
}
```

### `assignment <id> --course-id <cid>`
Full detail of one assignment (description HTML/text, linked file ids, external URLs, submission state).
```bash
.venv/bin/canvascli assignment 12345 --course-id 2151
```

Important fields:

```json
{
  "id": 12345,
  "name": "Homework 3",
  "description": "<p>raw Canvas HTML...</p>",
  "description_html": "<p>raw Canvas HTML...</p>",
  "description_text": "plain text version",
  "description_file_ids": [475078],
  "external_urls": [{"url": "https://docs.google.com/...", "kind": "third_party", "text": "Spec"}],
  "rubric_present": false,
  "submission_types": ["online_upload"],
  "attachments_count": 0
}
```

### Copilot-style assignment context commands

These commands mirror Canvas Copilot's mature data layer. They are **atomic**: each command reads one source and prints JSON. AutoStudy must inspect all likely sources and decide which one is the main spec; do not reintroduce an `assignment-context` aggregate command in the app layer.

```bash
.venv/bin/canvascli rubric 12345 -c 2151
.venv/bin/canvascli front-page -c 2151
.venv/bin/canvascli syllabus -c 2151
.venv/bin/canvascli modules -c 2151
.venv/bin/canvascli module-items 67890 -c 2151
.venv/bin/canvascli page project-guidelines -c 2151
.venv/bin/canvascli file 475078
.venv/bin/canvascli assignment-files 12345 -c 2151
```

Use pattern:

1. Fetch `assignment`, `rubric`, `front-page`, `syllabus`, `modules`, and `assignment-files`.
2. Fetch `module-items` for every module, not only the first apparent match.
3. Fetch `page` for every module item whose type is `Page`.
4. Fetch `file` metadata for every file id discovered in assignment/front-page/syllabus/pages/module items.
5. Download only files that are plausibly part of the assignment context via `canvascli download`.

Expected output shapes:

```json
// front-page / syllabus / page
{
  "status": "ok",
  "body_html": "<p>...</p>",
  "body_text": "...",
  "body_text_bytes": 1234,
  "file_ids": [475078],
  "external_urls": [{"url": "https://...", "kind": "external", "text": "Link"}]
}
```

```json
// modules
{
  "status": "ok",
  "count": 4,
  "modules": [{"id": 12955, "name": "Project guidelines", "items_count": 4}]
}
```

```json
// module-items
{
  "status": "ok",
  "module": {"id": 12955, "name": "Project guidelines"},
  "items": [
    {"type": "File", "title": "project_announce.pdf", "content_id": 625115},
    {"type": "Page", "title": "Final project specification", "page_url": "final-project"}
  ]
}
```

Real verification anchors:

- DSAA2011 Project: assignment description is empty; module items reveal the project PDF.
- UCUG1505 FINAL project: assignment description and Week 4 module item both point to the same Google Doc spec; Week 9 slides are nearby context.

### `announcements`
List announcements across all courses in the latest active Canvas term.
```bash
.venv/bin/canvascli announcements
.venv/bin/canvascli announcements --term "2025-26 Spring"
```

Note: HKUST(GZ) instructors rarely use Canvas announcements (often 0).

### `files [--course-id <cid>]`
List files (no download). Defaults to all courses in the latest active Canvas term, optionally scoped.
```bash
.venv/bin/canvascli files --course-id 2151
.venv/bin/canvascli files --term "2025-26 Spring"
```

### `folders <course-id>`
Pre-order folder tree with file counts + sizes per folder.
```bash
.venv/bin/canvascli folders 2151
```

Output shape (per item):
```json
{
  "folder_id": 66610,
  "depth": 1,
  "name": "DSAA_2043_Spring_2025_Midterm_Exam",
  "full_name": "course files/DSAA_2043_Spring_2025_Midterm_Exam",
  "file_count": 2,
  "size_bytes": 167557
}
```

### `download` (two modes)

**Mode A — single file by id:**
```bash
.venv/bin/canvascli download 496305 -o /path/to/output.pdf
```

**Mode B — whole folder, dry-run by default:**
```bash
# plan only (dry-run)
.venv/bin/canvascli download --course-id 2151 --folder-id 66610 --dest-root data/files/

# actually download
.venv/bin/canvascli download --course-id 2151 --folder-id 66610 --dest-root data/files/ --execute

# include subfolders
.venv/bin/canvascli download --course-id 2151 --folder-id 53520 --dest-root data/files/ --recursive --execute
```

**Increments**: re-running with same arguments skips files whose `file_id + updated_at + local_path` all match the last run. State is in `~/Library/Application Support/canvascli/downloads.json`.

### `submit <assignment-id> <file> --course-id <cid>`
Submit a file to a Canvas assignment via `online_upload`.
```bash
.venv/bin/canvascli submit 12345 ~/Downloads/hw3.pdf --course-id 2151
```

**Returns**: the Canvas submission object (with `id`, `workflow_state`, etc.).

**Safety**: AutoStudy tasks must always confirm with `AskUserQuestion` before calling `submit`. canvascli itself has no confirmation prompt — that's the calling skill's responsibility.

## Safety rules (apply to every command)

1. **Never echo `state.json`** or any cookie value to the user.
2. **Treat 401 as session expiration**, not a transient error. Direct user to `canvascli-setup.md` step 3. Do not retry.
3. **Don't use `init` as a session check.** It always opens a browser. Use `whoami` or the real read command to verify the existing session.
4. **Don't auto-download or auto-submit.** Always confirm scope with `AskUserQuestion`.
5. **Don't auto-pick "the latest"** assignment / file / folder. The user picks explicitly.
6. **Pipe JSON, not stdout text.** The text in `--pretty` mode is for humans, not parsing.

## Common pitfalls

- **Run via `.venv/bin/canvascli`, not bare `canvascli`** — system PATH might not have the venv binary.
- **`state.json` and SSO remember-login are separate.** `state.json` is canvascli's saved Canvas API cookie. The SSO checkbox does not decide whether `state.json` is written; it decides whether the next browser login is fast or requires full credentials again.
- **Term scope belongs in canvascli.** AutoStudy tasks should call `courses`, `assignments`, and `announcements` directly unless the user explicitly asks for a semester, in which case pass `--term`.
- **HTTP 404 on quizzes/modules/discussions is normal** — that course turned the feature off. canvascli returns `[]` in those cases.
- **Tuples of `(datetime, dict)`** aren't sortable in Python (dict isn't comparable) — when sorting by `due_at`, always use `key=lambda x: x["due_at"]`.
- **Filenames with Chinese / spaces are common.** Always quote paths in shell calls.
- **`assignment.description` is HTML and often just an attachment link.** The real problem text lives in the linked PDF. See the Recipes section below.

## Recipes

### Build a homework workbench before generation

Canvas's `description` field may be an attachment link, a Google Doc link, an empty string, or only a small hint. Reading it directly is the most common cause of agents producing template / placeholder content.

**Don't write your own extractor inline** — use `sub-skills/tools/problem-extractor.md`. It follows Canvas Copilot's source-by-source workflow:

1. Calls the atomic context commands above.
2. Stores raw CLI JSON under `<work_dir>/canvas/`.
3. Downloads reachable Canvas files into `<work_dir>/references/`.
4. Writes `<work_dir>/spec.md` as the full source-by-source assignment context.
5. Writes `<work_dir>/problem.md` as a compatibility view for existing tools.
6. Writes `<work_dir>/investigation/{rubric.md,unreachable.txt,review_a.json}`.

Downstream tools currently consume `problem.md`, but new orchestration should read `spec.md` first.

### One-liner: list file IDs embedded in a saved assignment snapshot

If you need a quick lookup without running the full extractor:

```bash
python -c '
import json, re, sys
d = json.load(open(sys.argv[1]))
desc = d.get("description") or ""
ids = set(re.findall(r"/files/(\d+)", desc))
print(*sorted(ids), sep="\n")
' data/homework/<COURSE>/<HW>/canvas/assignment.json
```

### Download a single attachment by ID with the real filename

`canvascli download` writes to the path you give. To preserve the original filename, pull the title from the description HTML first:

```python
import json, re
data = json.load(open("canvas/assignment.json"))
desc = data["description"] or ""
# Title and ID often appear together in a link tag
for m in re.finditer(r'title="([^"]+)"[^>]*?/files/(\d+)', desc):
    print(m.group(2), m.group(1))   # → "475078 DSAA2043_Assignment_1.pdf"
```

Then:

```bash
.venv/bin/canvascli download 475078 -o references/DSAA2043_Assignment_1.pdf
```
