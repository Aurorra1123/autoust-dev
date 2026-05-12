---
name: autostudy
description: HKUST(GZ) academic assistant. Sync Canvas course status, list assignments, view announcements, download materials. Aimed at undergrad students using Canvas (instructure.com).
---

# AutoStudy

Academic automation skill for HKUST(GZ) students. Talks to Canvas (`hkust-gz.instructure.com`) via a saved session cookie. **All actions are local** — no cloud, no third-party API key.

## What you can ask

Try natural language. Common intents:

| User says... | What happens |
|---|---|
| "看看这周作业" / "what's due" / "同步课程状态" | → `tasks/sync-status.md` |
| "下载 DSAA2043 的 midterm 资料" / "fetch course files" | → use `scraper.download` (see `tools/scraper-api.md`) |
| "登录失败了" / "重新登录" | → `tools/scraper-setup.md` step 2 |
| (first time using AutoStudy) | → `tools/scraper-setup.md` from step 1 |

For anything not listed: read the request, decide if it's a Canvas-related query you can answer with the scraper. If not, say so clearly.

## First-time setup check

Before doing anything else, verify the environment:

```bash
ls .venv .auth/canvas_state.json 2>&1
```

- If both exist → proceed to the task
- If `.venv` missing or `canvas_state.json` missing → invoke `tools/scraper-setup.md` first
- If a scraper call returns `401` mid-task → cookies expired, redirect to `tools/scraper-setup.md` step 2

## Architecture (so you know what to read)

```
skill.md (this file)         ← entry point, intent routing
sub-skills/
├── tools/
│   ├── scraper-setup.md     ← one-time install + login
│   └── scraper-api.md       ← module reference, CLI flags, JSON shapes
└── tasks/
    └── sync-status.md       ← M2 flagship task
scraper/                     ← Python package, run via `python -m scraper.<name>`
data/                        ← JSON snapshots + downloaded files (gitignored)
.auth/                       ← session cookie (gitignored, sensitive)
```

This skill is at milestone M2. See `ROADMAP.md` for what's coming next (notes generation, homework helper, etc.).

## Safety rules (non-negotiable)

These apply to every task in this skill:

1. **Never echo or log `.auth/canvas_state.json`** or any cookie value. It's a session credential.
2. **Never auto-download or auto-submit anything.** Use `AskUserQuestion` to confirm scope first.
3. **Never auto-pick "the latest" assignment, file, or course.** The user picks explicitly.
4. **On `401` from any scraper command**: treat as session expired, redirect to `scraper-setup.md` step 2. Do not retry.
5. **Don't parse `fetch_*` stdout** — parse the JSON files in `data/`.
6. **`AskUserQuestion` only** for interactive flow. The Claude Code `!` bash channel has no TTY — Python `input()` will EOF immediately. See `PITFALLS.md` if curious why.

## Telling the user what just happened

When you finish a task, summarize what was fetched / downloaded / written in 1–2 lines:
- ✓ "Fetched 6 courses + 36 assignments → data/assignments.json"
- ✓ "Downloaded 2 PDFs to data/files/DSAA2043 (L01)/DSAA_2043_Spring_2025_Midterm_Exam/"

Be concise. The user can read the diff themselves; don't recap files.

## When in doubt

- Check `PITFALLS.md` — most surprising behaviors have been documented
- Check `ROADMAP.md` — feature is probably planned for a later milestone
- If a feature truly isn't covered, say "this isn't in the current scope" rather than improvising
