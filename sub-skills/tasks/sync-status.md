---
name: sync-status
description: Sync Canvas data and present a markdown summary of upcoming deadlines, assignments, and announcements. Use when the user asks "what's due", "anything new this week", "sync course status", etc.
---

# Sync Status

The flagship M2 task. The user asks something like:
- "看看这周有什么作业"
- "帮我同步课程状态"
- "what's due this week"
- "anything new from my classes"

You sync Canvas data and present a clean markdown summary. **Do not dump raw JSON to the user** — summarize.

## Preconditions

Before running, check:
1. `.venv/` exists with `canvascli` installed (test: `.venv/bin/canvascli --version`)
2. A saved session exists (test: `.venv/bin/canvascli whoami` returns 0)

If either is missing, redirect to `canvascli-setup.md`. Do NOT proceed silently.

## Execution flow

### Step 1: Refresh data

Call canvascli twice. Capture JSON to disk for the rest of the flow:

```bash
.venv/bin/canvascli courses > data/courses.json
.venv/bin/canvascli assignments > data/assignments.json
.venv/bin/canvascli announcements > data/announcements.json
```

If any returns exit code 2 with "session expired" on stderr, the cookie's gone — direct the user to re-run `canvascli init` and stop.

### Step 2: Read the JSON

Use the `Read` tool on:
- `data/courses.json` — current-term enrollment list
- `data/assignments.json` — flat list of all assignments
- `data/announcements.json` — announcements (often empty for HKUST(GZ))

### Step 3: Compute the summary

In your reply, organize by sections:

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

### Step 4: Offer next actions

After the summary, use `AskUserQuestion` to offer follow-ups:

```
What would you like to do next?
  - Download materials for one of these courses
  - See more detail on a specific assignment
  - Nothing, just wanted the overview
```

**Do NOT auto-download anything.** Files are only fetched when the user explicitly asks.

## Output format (template)

```markdown
## Canvas status — <today's date>

### 📅 Upcoming (next 14 days)
- **Mon 11-17 15:59** · DSAA2043 · Homework 3 · unsubmitted
- **Wed 11-19 23:59** · DSAA2012 · Project Milestone 2 · in_progress
- ...

### ⚠️ Overdue / unsubmitted
- **due 11-10** · UCUG1077 · Literature review · still unsubmitted

### 📣 New announcements (last 7 days)
- 11-14 · DSAA2043 · "Midterm makeup details"

### 📚 Courses (current term)
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
| `data/*.json` doesn't exist after fetch | Fetch must have failed silently — show the user the fetch command stderr |
| All sections empty | Still respond with a "you're caught up ✓" message + courses overview |
| `due_at` is `null` | Skip from time-based sections, but count in courses overview |
| Announcement `message` is HTML | Don't render HTML; just show title + posted date |

## Pitfalls

- **Don't dump raw JSON to the user** — the user wants a summary, not data
- **Don't auto-download files** — separate confirmation needed (point to `canvascli-api.md` download section)
- **Time zone**: `due_at` is UTC in JSON. Display in user's local time (assume Asia/Shanghai unless user said otherwise)
- **Sorting tuples of `(datetime, dict)`**: Python falls back to comparing the dict if datetimes match, which raises `TypeError`. Always sort with `key=lambda x: x[0]`.
- **Don't show ancient overdue items**: assignments overdue by more than 30 days are usually past-term residue. Cap the overdue window.
- **Use `.venv/bin/canvascli`** explicitly — system PATH might not have it.
