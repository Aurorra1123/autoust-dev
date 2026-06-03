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
| "看看这周作业" / "what's due" / "同步课程状态" | → `sub-skills/tasks/sync-status.md` |
| "帮我完成 DLED3020 paper critique" / "做一下 DSAA2012 lab" | → `sub-skills/tasks/do-homework.md` |
| "下载 DSAA2043 的 midterm 资料" / "fetch course files" | → use `canvascli download` (see `sub-skills/tools/canvascli-api.md`) |
| "登录失败了" / "重新登录" | → first check `.venv/bin/canvascli whoami`; only run `canvascli-setup.md` step 3 if the saved session is missing/expired |
| (first time using AutoStudy) | → `sub-skills/tools/canvascli-setup.md` from step 1 |

For anything not listed: read the request, decide if it's a Canvas-related query you can answer with canvascli. If not, say so clearly.

## First-time setup check

Before doing anything else, verify the environment by running this in the AutoStudy working directory:

```bash
test -d .venv && .venv/bin/canvascli version > /dev/null 2>&1 \
  && .venv/bin/canvascli whoami > /dev/null 2>&1 \
  && echo OK || echo NEEDS_SETUP
```

- If `OK` → proceed to the task.
- If `NEEDS_SETUP` → **invoke `sub-skills/tools/canvascli-setup.md`** and execute every step that's missing (it has a Step 0 detection block that tells you exactly which steps to skip). Come back here when `whoami` succeeds.
- If a canvascli call returns "session expired" / 401 mid-task → only Step 3 of `canvascli-setup.md` is needed. Do not retry the failed call until the user has re-logged in.

The setup involves one user-facing step (`canvascli init` opens a real browser for HKUST(GZ) SSO). Everything else — venv creation, `pip install git+https://github.com/Aurorra1123/canvascli`, Chromium download — the agent runs end-to-end via `Bash`.

Important login model: `canvascli init` is an explicit login/refresh command,
not a health check. To test whether the current saved session works, run
`.venv/bin/canvascli whoami` or the real read command (`courses`,
`assignments`, etc.). A successful `init` writes `state.json` whether or not the
user selected the SSO "remember login" checkbox; that checkbox only affects how
smoothly the next SSO refresh goes after the saved session is missing or
expired.

## Architecture (so you know what to read)

```
skill.md (this file)              ← entry point, intent routing
sub-skills/
├── tools/
│   ├── canvascli-setup.md        ← one-time install + login
│   ├── canvascli-api.md          ← command reference, JSON shapes
│   ├── _index.md                 ← tool registry (M3 orchestrator reads this)
│   ├── problem-extractor.md      ← Canvas Generic recon → spec.md + rubric + references
│   ├── pdf-renderer.md           ← markdown → PDF (pandoc + tectonic)
│   ├── writing-helper.md         ← essay / report / reflection drafts
│   ├── paper-search.md           ← arxiv search → references.bib
│   ├── figure-maker.md           ← matplotlib charts → fig_*.pdf
│   ├── code-writer.md            ← lab src/ + tests
│   ├── test-runner.md            ← pytest + entry-point → test_report.md
│   └── slide-maker.md            ← guizang HTML deck (default) or LaTeX beamer
└── tasks/
    ├── sync-status.md            ← M2 flagship task
    ├── task-orchestrator.md      ← M3 pipeline executor from pipeline_design.md
    └── do-homework.md            ← MVP flagship: real Canvas assignment E2E
data/                             ← JSON snapshots + downloaded files (gitignored)
```

Note: the Canvas data layer lives in a separate repo,
[canvascli](https://github.com/Aurorra1123/canvascli) (open source, MIT). It's installed
into the local `.venv` with `pip install git+https://github.com/Aurorra1123/canvascli`.
Same philosophy as AutoPku's `pku3b` — keep the data acquisition tool independent so it
can serve other agents too.

This skill is at **MVP (M3 core)**: the 4 flagship homework scenarios — paper / slides / math / lab — have each been validated end-to-end on real HKUST(GZ) Canvas assignments. The current M3.5 work is upgrading homework handling to Canvas Generic-style reconnaissance (`spec.md -> investigation/ -> pipeline_design.md`) while keeping AutoStudy's assistant-style user checkpoints. See `docs/ROADMAP.md` for what's coming next.

## Safety rules (non-negotiable)

These apply to every task in this skill:

1. **Never echo or log canvascli's saved session** (`~/Library/Application Support/canvascli/state.json`). It's a credential.
2. **Never auto-download or auto-submit anything.** Use `AskUserQuestion` to confirm scope first.
3. **Never auto-pick "the latest" assignment, file, or course.** The user picks explicitly.
4. **On session expiration / 401 from any canvascli command**: redirect to `canvascli-setup.md` step 3. Do not retry. Do not run `canvascli init` just to check status; use `whoami` for that.
5. **Capture canvascli's JSON to disk** (e.g. `canvascli courses > data/courses.json`), then read and summarize. Don't try to summarize from stdout buffers directly.
6. **`AskUserQuestion` only** for interactive flow. The Claude Code `!` bash channel has no TTY — Python `input()` will EOF immediately. See `docs/PITFALLS.md` if curious why.
7. **Ground homework deliverables in `spec.md`, `references/`, and `pipeline_design.md`, not the assignment title.** Canvas's `assignment.description` may be empty, a file link, a Google Doc link, or only one hint among many. Before producing any draft / code / slides, `do-homework.md [A3]` must run the agent-led `tools/problem-extractor.md` workflow: inspect assignment, rubric, front page, syllabus, every module's items, pages, files, and external URLs; write a standardized `spec.md`; find rubric criteria in `investigation/rubric.md`; locate inputs under `references/`; cold-review the investigation in `investigation/review_a.json`; and start `pipeline_design.md` with the output mode. `problem.md` is only a compatibility summary for older tools. **Never produce deliverables containing `[PROBLEM N]` / `[TODO: align with actual project spec]` / `[此处由小组成员填入选题]` placeholders.** The only acceptable inline markers are `[CITATION NEEDED: ...]` and `[CLARIFICATION NEEDED: ...]`, both surfaced for user resolution at the [E] checkpoint.

## Telling the user what just happened

When you finish a task, summarize what was fetched / downloaded / written in 1–2 lines:
- ✓ "Fetched 6 courses + 36 assignments → data/assignments.json"
- ✓ "Downloaded 2 PDFs to data/files/DSAA2043 (L01)/DSAA_2043_Spring_2025_Midterm_Exam/"

Be concise. The user can read the diff themselves; don't recap files.

## When in doubt

- Check `docs/PITFALLS.md` — most surprising behaviors have been documented
- Check `docs/ROADMAP.md` — feature is probably planned for a later milestone
- If a feature truly isn't covered, say "this isn't in the current scope" rather than improvising
