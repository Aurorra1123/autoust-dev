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
One-time SSO login. **Run in user's own terminal**, not from agent.
```bash
.venv/bin/canvascli init
```

### `whoami`
Verify current session. Returns user object.
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
Full detail of one assignment (description HTML, rubric, submission state).
```bash
.venv/bin/canvascli assignment 12345 --course-id 2151
```

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
3. **Don't auto-download or auto-submit.** Always confirm scope with `AskUserQuestion`.
4. **Don't auto-pick "the latest"** assignment / file / folder. The user picks explicitly.
5. **Pipe JSON, not stdout text.** The text in `--pretty` mode is for humans, not parsing.

## Common pitfalls

- **Run via `.venv/bin/canvascli`, not bare `canvascli`** — system PATH might not have the venv binary.
- **Term scope belongs in canvascli.** AutoStudy tasks should call `courses`, `assignments`, and `announcements` directly unless the user explicitly asks for a semester, in which case pass `--term`.
- **HTTP 404 on quizzes/modules/discussions is normal** — that course turned the feature off. canvascli returns `[]` in those cases.
- **Tuples of `(datetime, dict)`** aren't sortable in Python (dict isn't comparable) — when sorting by `due_at`, always use `key=lambda x: x["due_at"]`.
- **Filenames with Chinese / spaces are common.** Always quote paths in shell calls.
- **`assignment.description` is HTML and often just an attachment link.** The real problem text lives in the linked PDF. See the Recipes section below.

## Recipes

### Extract the real problem text from an assignment with PDF attachments

Canvas's `description` field on many assignments is just an `<a>...pdf</a>` link wrapping the real problem statement. Reading `description` directly is the most common cause of agents producing template / placeholder content.

**Don't write your own extractor inline** — use `sub-skills/tools/problem-extractor.md`. It:

1. Scans `description` HTML for file IDs in two embedding styles (`href="...files/<id>"` and `data-api-endpoint="...files/<id>"`)
2. Calls `canvascli download <fid> -o <work_dir>/attachments/<filename>` for each
3. Extracts text (PDF → `pdftotext` or `pdfminer.six`)
4. Writes `<work_dir>/problem.md` with frontmatter + inline plain-text description + per-attachment `## Attached:` sections + rubric

Downstream tools (`writing-helper`, `code-writer`, `slide-maker`) consume `problem.md`, not `assignment.json.description`. This is the spec's only guarantee against `[PROBLEM N]` template output.

### One-liner: list file IDs embedded in a description

If you need a quick lookup without running the full extractor:

```bash
python -c '
import json, re, sys
d = json.load(open(sys.argv[1]))
desc = d.get("description") or ""
ids = set(re.findall(r"/files/(\d+)", desc))
print(*sorted(ids), sep="\n")
' data/homework/<COURSE>/<HW>/assignment.json
```

### Download a single attachment by ID with the real filename

`canvascli download` writes to the path you give. To preserve the original filename, pull the title from the description HTML first:

```python
import json, re
data = json.load(open("assignment.json"))
desc = data["description"] or ""
# Title and ID often appear together in a link tag
for m in re.finditer(r'title="([^"]+)"[^>]*?/files/(\d+)', desc):
    print(m.group(2), m.group(1))   # → "475078 DSAA2043_Assignment_1.pdf"
```

Then:

```bash
.venv/bin/canvascli download 475078 -o attachments/DSAA2043_Assignment_1.pdf
```
