# AutoStudy

> Local HKUST(GZ) Canvas study-assistant skill.
> Sync Canvas, plan deadlines, investigate assignments, draft reviewable
> artifacts, archive course materials, and generate course notes.

Other versions:

- [Default Chinese README](./README.md)
- [Quick Chinese README](./README.quick.md)

AutoStudy is a **local skill package** for Claude Code / Codex-style agentic
coding environments. You ask in natural language; the agent reads `skill.md`,
calls the local `canvascli` data layer, writes evidence and artifacts into this
repository, and asks before key actions.

It is not a web app, hosted service, or hidden automation bot. It is closer to a
study assistant: it gathers Canvas context, explains what it found, aligns with
you when a task is open-ended, then produces local artifacts you can inspect,
edit, and decide whether to submit.

---

## What You Can Ask

```text
"看看这周有什么作业"
"同步课程状态"
"帮我完成 DSAA2011 Project，先生成本地草稿，不提交"
"继续改上次那个 report，让实验讨论更深入"
"同步 DSAA2011 的课件"
"把 DSAA2011 的 lecture notes 写出来"
```

Current user-facing tasks:

| Task | What It Does | Output |
|---|---|---|
| `sync-status` | Refreshes Canvas courses, assignments, announcements, and creates an assistant plan. It does **not** execute assignments. | `data/runs/<date>/REPORT.md`, `plan.json`, `pending_assignments.json` |
| `do-homework` | Builds a single-assignment workbench, investigates Canvas sources, aligns with you, designs a task-specific pipeline, drafts local artifacts, then asks whether to submit. | `data/homework/<COURSE>/<HWID>/` |
| `sync-course` | Archives course files, announcements, and module structure for reuse. | `data/courses/<COURSE>/` |
| `write-course-notes` | Generates Obsidian-style Markdown notes from synced lecture PDFs. | `data/courses/<COURSE>/notes/` |

The older M3 proof-of-concept scenarios, paper / slides / math / lab, have all
been validated on real HKUST(GZ) Canvas assignments. The current main line is
M3.5+: deeper Canvas reconnaissance, explicit user alignment, dynamic pipelines,
stage-level review, and resumable local workbenches.

---

## Quick Start

### 1. Load The Skill

In Claude Code or a compatible environment:

```text
Use the AutoStudy skill in /Users/deepwisdom/Desktop/project/autoust
```

On a fresh machine:

```text
Clone https://github.com/Aurorra1123/autoust-dev and use its skill.md
```

The agent should read `skill.md`, check the environment, and install missing
dependencies into the local `.venv/`.

### 2. Complete Canvas Login Once

AutoStudy uses the separate [`canvascli`](https://github.com/Aurorra1123/canvascli)
data layer. The first run opens a browser for HKUST(GZ) SSO:

```bash
.venv/bin/canvascli init
```

The saved Canvas session is stored locally:

```text
~/Library/Application Support/canvascli/state.json
```

That file is a credential. Agents must not print it, copy it into chat, or
commit it. To check whether the saved session still works, run:

```bash
.venv/bin/canvascli whoami
```

`canvascli init` is a login/refresh command, not a health check.

### 3. Start With Status

The safest first request is:

```text
看看这周有什么作业
```

AutoStudy will:

1. fetch Canvas courses, assignments, and announcements;
2. save current sync snapshots under `data/sync/current/`;
3. write a dated run under `data/runs/<date>/`;
4. show numbered next-step recommendations;
5. wait for you to choose whether to start an assignment.

If you choose a numbered item, AutoStudy uses `scripts/select_plan_item.py` to
resolve exact Canvas IDs and the suggested workbench. After a numbered selection,
the agent should not re-match by title.

---

## How Homework Works Now

AutoStudy does not generate from the assignment title. The current homework
contract is:

```text
Canvas sources
-> spec.md
-> investigation/explore_context.md
-> investigation/alignment_brief.md or repair_plan.md
-> pipeline_design.md or repair_pipeline_design.md
-> stage_briefs/
-> stage_results/ and stage_reviews/
-> draft/
-> verification.log
-> result.json
```

In plain language:

1. **Explore**: inspect assignment page, rubric, course front page, syllabus,
   modules, module items, files, pages, and external links through `canvascli`.
2. **Write the spec**: summarize the real assignment requirements in `spec.md`;
   put fetched PDFs, Google Docs, starter code, datasets, and other source
   material under `references/`.
3. **Align with you**: ask only the questions needed to avoid guessing your
   topic, group info, dataset, architecture, style, or scope.
4. **Confirm the agreement**: write final task intent to
   `investigation/alignment_brief.md` for a new assignment, or `repair_plan.md`
   when improving an existing draft.
5. **Design the pipeline**: write a custom `pipeline_design.md` from the spec
   and confirmed intent. There is no fixed "paper pipeline" or "lab pipeline";
   tools are composed per assignment.
6. **Execute and review**: generate stage briefs, dispatch executors/reviewers
   when useful, record receipts, run checks, and collect artifacts under
   `draft/`.
7. **Ask before submission**: Canvas submission is never automatic.

This is why a complex project can produce a notebook, report PDF, slides,
requirements file, source zip, verification log, and human review items in the
same workbench.

---

## Course Materials And Notes

To sync reusable course context:

```text
同步 DSAA2011 的资料
```

This routes to `sync-course`, confirms scope, then archives files and Canvas
structure under:

```text
data/courses/<COURSE>/
├── materials/
├── canvas_sync/
├── notes/
├── meta.json
└── index.md
```

Then:

```text
写 DSAA2011 的课程笔记
```

routes to `write-course-notes`, which reads lecture PDFs from the course archive
and writes structured Markdown notes under `notes/`.

---

## Repository Map

```text
AutoStudy/
├── skill.md                         # User-facing skill entry and routing
├── AGENTS.md                        # Developer handoff and repo rules
├── README.md                        # Default Chinese README
├── README.en.md                     # English full README
├── README.quick.md                  # Chinese quick README
├── scripts/
│   ├── write_scan_plan.py           # Canvas snapshot -> plan/report
│   ├── select_plan_item.py          # Numbered plan item -> exact handoff
│   └── write_homework_result.py     # Stable result.json writer
├── sub-skills/
│   ├── tasks/
│   │   ├── sync-status.md
│   │   ├── do-homework.md
│   │   ├── task-orchestrator.md
│   │   ├── sync-course.md
│   │   └── write-course-notes.md
│   └── tools/
│       ├── canvascli-setup.md
│       ├── canvascli-api.md
│       ├── assignment-recon.md
│       ├── code-writer.md
│       ├── writing-helper.md
│       ├── pdf-renderer.md
│       ├── slide-maker.md
│       └── ...
├── docs/
│   ├── ROADMAP.md
│   ├── COLLABORATION.md
│   ├── runtime-agent-protocol.md
│   ├── skills-architecture-spec.md
│   ├── PITFALLS.md
│   ├── plans/feature-list.json
│   └── progress/agent-progress.md
└── data/                            # Local Canvas snapshots and artifacts
```

`data/` is a local workspace and is gitignored. It may contain course files,
assignment drafts, verification logs, and result receipts.
Current Canvas sync snapshots live under `data/sync/current/`, while each
scan-plan run keeps its own copied evidence under `data/runs/<date>/raw/`.

---

## Current Status

Passing and usable:

- Canvas data layer via `canvascli`.
- `sync-status` scan-plan flow.
- `do-homework` workbench, reconnaissance, alignment, dynamic pipeline, and
  local draft flow.
- M3 tools: prose, code, figures, tests, slides, PDF rendering, humanizer.
- Course material sync and course-note generation.
- `result.json` receipts for skipped, draft-ready, submitted, and error states.

Still being hardened:

- Clean process validation for the unified executor/reviewer runtime.
- Retained-artifact repair and multi-turn iteration ergonomics.
- Course-level and user-level preference memory.
- Real Canvas submission E2E on a safe, unexpired sandbox assignment.
- Multi-runtime support beyond the current Claude Code-oriented skill surface.

Detailed status:

- [docs/ROADMAP.md](./docs/ROADMAP.md)
- [docs/plans/feature-list.json](./docs/plans/feature-list.json)

---

## Safety And Academic Integrity

- AutoStudy never auto-submits to Canvas.
- `sync-status` proposes a plan but never auto-executes plan items.
- Broad downloads, homework drafting, and file submission should have user
  confirmation points.
- AutoStudy should not fabricate group details, datasets, personal experience,
  partner names, instructor oral instructions, or inaccessible source material.
- Drafts are local artifacts for you to inspect, revise, and own.
- The intended use is to reduce repetitive work and improve traceability, not to
  hide responsibility from the student.

When unsure, AutoStudy should stop and explain uncertainty instead of guessing.

---

## Contributing

For development work, start with [AGENTS.md](./AGENTS.md). It explains the
boundary between AutoStudy and `canvascli`, the Canvas Copilot reference, branch
policy, progress/backlog updates, and verification rules.
