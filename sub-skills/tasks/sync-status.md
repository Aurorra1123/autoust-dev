---
name: sync-status
description: Sync Canvas data and present a markdown summary of upcoming deadlines, assignments, and announcements. Use when the user asks "what's due", "anything new this week", "sync course status", etc.
---

# Sync Status

The flagship M2 task, now with an M3.5 planning layer. The user asks something like:
- "看看这周有什么作业"
- "帮我同步课程状态"
- "what's due this week"
- "anything new from my classes"

You sync Canvas data, write a dated assistant-style plan, and present a clean markdown summary. **Do not dump raw JSON to the user** — summarize.

This task follows Canvas Copilot's scan/execute split in spirit: scan writes a
plan and then stops. AutoStudy changes the interaction shape: the plan is a
study-assistant recommendation, not a batch automation queue.

## Preconditions

Before running, check:
1. `.venv/` exists with `canvascli` installed (test: `.venv/bin/canvascli version`)
2. A saved session exists (test: `.venv/bin/canvascli whoami` returns 0)

If either is missing, redirect to `canvascli-setup.md`. Do NOT proceed silently.

## Execution flow

### Step 1: Refresh data

Call canvascli. Capture JSON to disk for the rest of the flow:

```bash
mkdir -p data/sync/current
.venv/bin/canvascli courses > data/sync/current/courses.json
.venv/bin/canvascli assignments > data/sync/current/assignments.json
.venv/bin/canvascli announcements > data/sync/current/announcements.json
```

Also copy these raw snapshots into today's run directory:

```text
data/runs/<today>/raw/
├── courses.json
├── assignments.json
└── announcements.json
```

These default to the latest active Canvas term. If the user explicitly asks for a
semester, pass the same `--term "<term name>"` to all three commands.

If any returns exit code 2 with "session expired" on stderr, the cookie's gone — direct the user to re-run `canvascli init` and stop.

### Step 2: Build the assistant plan

Invoke the stable scan-plan writer:

```bash
.venv/bin/python scripts/write_scan_plan.py
```

It reads:

- `data/sync/current/assignments.json`
- `data/sync/current/courses.json`
- `data/homework/**/result.json`

It writes:

```text
data/runs/<today>/
├── pending_assignments.json
├── plan.json
└── REPORT.md
```

`pending_assignments.json` is the factual list of actionable assignments plus
local workflow state. `plan.json` is AutoStudy's suggested next step for each
item. `REPORT.md` is the user-facing summary.

The writer does not call Canvas and does not execute homework. It only combines
the current canvascli snapshots with local `result.json` receipts.

### Step 3: Read the JSON and REPORT

Use the `Read` tool on:
- `data/sync/current/courses.json` — latest active-term enrollment list, or the requested term
- `data/sync/current/assignments.json` — flat list of assignments for the same term
- `data/sync/current/announcements.json` — announcements (often empty for HKUST(GZ))
- `data/runs/<today>/pending_assignments.json` — actionable assignments after Canvas state and local result filtering
- `data/runs/<today>/plan.json` — suggested next steps
- `data/runs/<today>/REPORT.md` — user-facing plan draft

### Step 4: Compute the summary

In your reply, organize by sections. Keep the classic Canvas overview, but make
the plan the first thing the user can act on:

**Section 0 — Recommended next steps**
- Summarize the top 3–5 items from `plan.json`
- For each: `<index> · <course_short> · <name> · <due/status> · <suggested_next_step>`
- If an item has `existing_result_status: draft_ready`, say it needs review or submission, not new reconnaissance
- If empty: explicitly say no actionable assignments were found in the current snapshot

**Section A — Upcoming deadlines (within 14 days)**
- Filter `assignments` where `due_at` is in `[now, now + 14d]` and `submission_state != "submitted"` and `submission_state != "graded"`
- Sort ascending by `due_at`
- For each: `<due_date HH:MM> · <course_short> · <name> · <submission_state>`
- If empty: explicitly say "no upcoming deadlines in the next 2 weeks ✓"

**Section B — Overdue and unsubmitted**
- `due_at` between `now - 30d` and `now` AND `submission_state == "unsubmitted"`
- Highlight clearly — these need urgent action
- **Don't show overdue items older than 30 days** — those are from past terms or abandoned, not actionable

**Section C — Recent announcements (last 7 days)**
- Filter `announcements` where `posted_at` ≥ now - 7d
- For each: `<posted_date> · <course_short> · <title>`
- If empty: "no new announcements this week"

**Section D — Courses overview** (always include, short)
- Brief table: course_short · n_assignments · n_unsubmitted

### Step 5: Offer next actions

After the summary, use `AskUserQuestion` to offer follow-ups:

```
What would you like to do next?
  - Start reconnaissance / do-homework for plan item <N>
  - Continue or review a draft_ready item
  - See more detail on a specific assignment
  - Nothing, just wanted the overview
```

If the user chooses a numbered plan item, resolve it through the stable selector
before starting any homework workflow:

```bash
.venv/bin/python scripts/select_plan_item.py --index <N> --pretty
```

Use the selector output as the handoff object for `do-homework.md`. Do not
re-match the assignment by title when the selector has returned `course_id`,
`assignment_id`, and `suggested_work_dir`.

Selector actions:

| `recommended_action` | Behavior |
|---|---|
| `recon` | Start `do-homework.md` with the selected identifiers. |
| `review_or_submit` | Read `existing_result_path` / `suggested_work_dir` and help the user review or submit the existing draft instead of re-running reconnaissance by default. |
| `continue` | Inspect the previous `result.json` error or revision-needed state and ask the user whether to retry. |
| `manual_review` | Tell the user the item likely needs manual Canvas interaction; do not treat it like a normal draftable homework item. |

**Do NOT auto-download anything.** Files are only fetched when the user explicitly asks.
**Do NOT auto-execute plan items.** `sync-status` proposes; `do-homework` acts
only after the user picks one item.

## Output format (template)

```markdown
## Canvas status — <today's date>

### ✅ Suggested plan
1. **COURSE1234 · Project** — no due date · graded on Canvas · local draft_ready → review_or_submit
2. **CORE1000 · Final Report** — overdue · unsubmitted → recon

### 📅 Upcoming (next 14 days)
- **Mon 11-17 15:59** · COURSE2000 · Homework 3 · unsubmitted
- **Wed 11-19 23:59** · COURSE3000 · Project Milestone 2 · in_progress
- ...

### ⚠️ Overdue / unsubmitted
- **due 11-10** · UCUG1077 · Literature review · still unsubmitted

### 📣 New announcements (last 7 days)
- 11-14 · DSAA2043 · "Midterm makeup details"

### 📚 Courses (selected term)
| Course | Total assignments | Unsubmitted |
|---|---|---|
| DSAA2043 | 9 | 1 |
| DSAA2012 | 6 | 0 |
| ... | ... | ... |
```

Keep tone informative but not noisy. The user wants to scan in 5 seconds.

## Edge cases

| Situation | Behavior |
|---|---|
| `data/sync/current/*.json` doesn't exist after fetch | Fetch must have failed silently — show the user the fetch command stderr |
| `data/runs/<today>/plan.json` missing | Re-run `scripts/write_scan_plan.py`; if it fails, show the short stderr and fall back to classic summary |
| User selects an invalid plan index | Run `scripts/select_plan_item.py --index <N>`; show its short stderr and ask for a valid item number |
| All sections empty | Still respond with a "you're caught up ✓" message + courses overview |
| `due_at` is `null` | Skip from time-based sections, but count in courses overview |
| Announcement `message` is HTML | Don't render HTML; just show title + posted date |

## Pitfalls

- **Don't dump raw JSON to the user** — the user wants a summary, not data
- **Don't auto-download files** — separate confirmation needed (point to `canvascli-api.md` download section)
- **Don't auto-execute plan items** — scan/status and do-homework are separate. The plan is a recommendation, not approval.
- **Time zone**: `due_at` is UTC in JSON. Display in user's local time (assume Asia/Shanghai unless user said otherwise)
- **Sorting tuples of `(datetime, dict)`**: Python falls back to comparing the dict if datetimes match, which raises `TypeError`. Always sort with `key=lambda x: x[0]`.
- **Don't show ancient overdue items**: assignments overdue by more than 30 days are usually past-term residue. Cap the overdue window.
- **Don't reimplement term filtering here**: canvascli owns latest-active-term detection and explicit `--term` selection.
- **Use `.venv/bin/canvascli`** explicitly — system PATH might not have it.
- **Canvas terminal state wins**: if Canvas says submitted/graded, `write_scan_plan.py` filters it out even if an old local `result.json` says `draft_ready`.
- **Use `scripts/select_plan_item.py` for numbered choices**: don't manually
  reconstruct `course_id` / `assignment_id` from the rendered markdown table.
