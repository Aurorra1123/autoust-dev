---
name: canvascli-api
description: Reference for calling canvascli commands from agent flows. Use whenever you need to fetch Canvas data or perform a Canvas action.
---

# canvascli API reference

`canvascli` is the external Canvas command-line tool AutoStudy depends on. Data-returning commands are JSON-by-default — that's the contract that lets agents pipe their output into `jq` / Python / further processing.

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

- **stdout**: JSON success payload only for data-returning commands. One line by default; `--pretty` indents.
- **stderr**: progress / status / errors; not part of the JSON payload. Do not parse it as data; save it when the exit code is non-zero.
- **exit code**: `0` ok · `1` runtime / network / Canvas 5xx · `2` user / auth / permission / not found / argument error.

Exceptions:

- `version` prints plain text, not JSON.
- `init` opens the login flow and writes login/status messages to stderr; it
  has no JSON payload.

So the agent's typical idiom for data-returning commands is:

```bash
set -o pipefail
.venv/bin/canvascli courses | jq '.[].name'
```

or in Python:

```python
import json, subprocess
out = subprocess.check_output([".venv/bin/canvascli", "courses"])
courses = json.loads(out)
```

## Command reference

### `version`
Print the installed canvascli version as plain text.
```bash
.venv/bin/canvascli version
```

### `init`
Explicit SSO login / refresh. This opens a browser and writes a new
`state.json`; it is not a status check and does not emit JSON. **Run in the
user's own terminal or only when the user is ready for the browser popup.**
```bash
.venv/bin/canvascli init
.venv/bin/canvascli init --canvas-url "https://canvas.example.edu"
.venv/bin/canvascli init --canvas-url "https://school.instructure.com/api/v1"
```

If the SSO page offers "remember login" / "trust this browser", ask the user to
select it. A successful `init` writes `state.json` either way; the checkbox only
affects whether the next SSO refresh can skip a full manual login.

`canvascli` stores the normalized Canvas web root and API root outside the repo
next to the saved session cookie. AutoStudy should read Canvas-provided
`html_url` values and must not reconstruct school-specific assignment URLs from
course and assignment IDs.

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

`assignments` uses `--course-id`; do not assume every command has the same
short option aliases. When a command example and the installed CLI disagree,
run `<command> --help` and follow the installed CLI contract, then record the
drift as a docs/tool concern.

Output shape (per item):
```json
{
  "id": 12345,
  "name": "Homework 3",
  "course_id": 2151,
  "course_name": "DSAA2043 (L01) - ...",
  "due_at": "2025-11-13T15:59:00Z",
  "points_possible": 100,
  "html_url": "https://canvas.example.edu/courses/2151/assignments/12345",
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
4. Fetch `file` metadata for every file id discovered in assignment/front-page/syllabus/pages/module items. Note: `canvascli file` takes only `<file_id>` — no `-c` flag needed because file IDs are globally unique across courses.
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

Generic reconnaissance patterns:

- Assignment descriptions may be empty while module items reveal the real spec
  file.
- The same valid spec link may appear from multiple Canvas surfaces. Treat
  duplicates as corroboration and still distinguish nearby supporting context.

### `announcements`
List announcements for a course or across all courses in the latest active
Canvas term.
```bash
.venv/bin/canvascli announcements
.venv/bin/canvascli announcements --course-id 2151
.venv/bin/canvascli announcements --course-id 2151 --start-date 2025-09-01 --end-date 2025-12-20
.venv/bin/canvascli announcements --term "2025-26 Spring"
```

Default scope is a latest-active-term complete snapshot when canvascli can
derive a date range: first from `term.start_at` / `term.end_at`, then from the
course `start_at` / `end_at` if term dates are incomplete. Only when both term
and course dates are incomplete does canvascli let Canvas use its default
announcements window. Pass `--start-date` / `--end-date` only when the user
explicitly asks for a custom date range.

Users do not need to know Canvas internal course IDs. Agents should first run
`courses`, match the user's course name/code, and then pass the resolved id as
`--course-id <cid>`. Some Canvas instances rarely use announcements, so 0
results can be a valid checked state.

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
6. **Pipe compact data-command JSON for automation.** Reserve `--pretty` for human inspection; it is still JSON but parsers should not require it. Do not parse `version` or `init` as JSON.
7. **Request failures are concise.** Runtime/user failures write a short stderr
   message and exit non-zero; do not expect or parse Python tracebacks.

## Common pitfalls

- **Run via `.venv/bin/canvascli`, not bare `canvascli`** — system PATH might not have the venv binary.
- **`state.json` and SSO remember-login are separate.** `state.json` is canvascli's saved Canvas API cookie. The SSO checkbox does not decide whether `state.json` is written; it decides whether the next browser login is fast or requires full credentials again.
- **Term scope belongs in canvascli.** AutoStudy tasks should call `courses`, `assignments`, and `announcements` directly unless the user explicitly asks for a semester, in which case pass `--term`.
- **Do not reimplement announcements REST windows in AutoStudy.** The
  announcements default date scope, term-date then course-date fallback
  behavior, and `--start-date` / `--end-date` contract belong in canvascli.
- **Concise request failures are normal.** Auth, permission, not-found,
  argument, network, and Canvas 5xx errors go to stderr without a traceback;
  branch on the exit code and save the stderr text when an audit trail is
  needed.
- **HTTP 404 on quizzes/modules/discussions is normal** — that course turned the feature off. canvascli returns `[]` in those cases.
- **Tuples of `(datetime, dict)`** aren't sortable in Python (dict isn't comparable) — when sorting by `due_at`, always use `key=lambda x: x["due_at"]`.
- **Filenames with Chinese / spaces are common.** Always quote paths in shell calls.
- **`assignment.description` is HTML and often just an attachment link.** The real problem text lives in the linked PDF. See the Recipes section below.

## Recipes

### Build a homework workbench before generation

Canvas's `description` field may be an attachment link, a Google Doc link, an empty string, or only a small hint. Reading it directly is the most common cause of agents producing template / placeholder content.

**Don't write your own extractor inline** — use
`sub-skills/tools/assignment-recon.md`. It follows Canvas Copilot's
Canvas Generic workflow, adapted to AutoStudy's CLI boundary:

1. Calls atomic context commands above: `assignment`, `rubric`,
   `front-page`, `syllabus`, `modules`, `module-items`, `page`, `file`, and
   `assignment-files`, and `announcements`.
2. Stores raw CLI JSON under `<work_dir>/canvas/`.
3. Runs `reference_collector` to preserve task-relevant source evidence under
   `<work_dir>/references/`.
4. Writes `<work_dir>/spec.md` as the Main Agent reconnaissance report, not a
   raw dump.
5. Finds grading criteria into `<work_dir>/investigation/rubric.md`.
6. Downloads or fetches needed inputs into `<work_dir>/references/`, and logs
   blocked resources in `<work_dir>/investigation/unreachable.txt`.
7. Writes `<work_dir>/investigation/review_a.json` after a cold investigation
   review.
8. Starts `<work_dir>/pipeline_design.md` with the output mode, then keeps
   `<work_dir>/problem.md` only as a compatibility summary for older tools.

Do not use or recreate an `assignment-context` aggregate command. The mature
pattern is atomic data access, raw CLI JSON stored under `<work_dir>/canvas/`,
`reference_collector` preservation of task-relevant original evidence under
`<work_dir>/references/`, and Main Agent source/spec judgment in
`<work_dir>/spec.md`.
Downstream tools should read `spec.md` and `pipeline_design.md` first;
`problem.md` is temporary compatibility.

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
