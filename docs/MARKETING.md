# AutoStudy Messaging Notes

> Purpose: explain AutoStudy to users without promising unsafe automation.
> The product story should match the current runtime: Canvas-grounded,
> user-aligned, locally inspectable study assistance.

---

## Core Positioning

Short version:

> AutoStudy is a local Canvas LMS study assistant for agentic coding
> environments, validated on HKUST(GZ)'s Canvas instance. It scans deadlines,
> investigates assignments, asks for your intent, drafts local artifacts, and
> keeps verification evidence before you decide what to submit.

One-sentence Chinese version:

> AutoStudy 是跑在 Claude Code / Codex 里的本地 Canvas LMS 学业助手，已在 HKUST(GZ) 的 Canvas 实例上验证：同步 Canvas、规划 ddl、侦查作业要求、生成可审核草稿、整理课件和笔记，全程保留用户确认点。

What makes it different:

- It reads Canvas sources deeply instead of trusting assignment titles.
- It writes a local workbench, not just chat text.
- It asks alignment questions before open-ended work.
- It composes tools dynamically per assignment.
- It keeps logs, receipts, and verification files for later review.

---

## What To Demonstrate

### 1. Canvas Status To Action Plan

User prompt:

```text
看看这周有什么作业
```

Show:

- Canvas courses/assignments/announcements are refreshed.
- `data/runs/<date>/REPORT.md` is created.
- The user sees a numbered plan.
- The agent waits instead of auto-executing.

Message:

> AutoStudy turns Canvas noise into an actionable plan, but the student still
> chooses what happens next.

### 2. Assignment Reconnaissance

User prompt:

```text
帮我看看 DSAA2011 Project 到底要交什么
```

Show:

- assignment page, rubric, syllabus, modules, files, and links are checked;
- `spec.md` explains the real source trail;
- `references/` contains fetched materials;
- `investigation/rubric.md` and `unreachable.txt` are written.

Message:

> It does not guess from the title. It investigates where the actual spec lives.

### 3. Open-Ended Project Alignment

User prompt:

```text
帮我做 UCUG1505 final project，先出本地草稿
```

Show:

- the agent summarizes Canvas requirements;
- asks for project concept / partner / provider / demo constraints as needed;
- compares possible approaches;
- writes `investigation/alignment_brief.md`;
- only then writes `pipeline_design.md`.

Message:

> The agent does not silently invent your creative direction. It helps you make
> the decision, records it, and uses that record as the plan contract.

### 4. Mixed Deliverable Draft

Show a workbench that contains:

```text
draft/
├── notebook.ipynb
├── report.pdf
├── presentation.pdf
├── requirements.txt
└── source.zip
verification.log
result.json
```

Message:

> A complex assignment is handled as a small project: code, report, slides,
> package, checks, and human review items live together.

### 5. Course Archive And Notes

User prompts:

```text
同步 DSAA2011 的资料
写 DSAA2011 的课程笔记
```

Show:

- `data/courses/<COURSE>/materials/`;
- `canvas_sync/` metadata;
- `index.md`;
- `notes/*.md` with formulas, callouts, and concept diagrams.

Message:

> AutoStudy is not only for assignments. It also builds reusable course context
> for notes and future tutoring.

---

## Tone

Use:

- "assistant"
- "local workbench"
- "source-grounded"
- "asks before acting"
- "draft for review"
- "verification evidence"
- "student remains responsible"

Avoid:

- "fully automatic homework machine"
- "one-click submit"
- "guaranteed grade"
- "replace studying"
- "solves everything in five minutes"

The right promise is not "AutoStudy does your schoolwork for you." The right
promise is:

> AutoStudy handles the boring, error-prone project-management layer so the
> student can spend attention on choices, review, and learning.

---

## Academic Integrity Line

Recommended public wording:

> AutoStudy drafts and organizes local artifacts, but it does not remove student
> responsibility. You must review the work, resolve unclear facts, decide what
> to submit, and follow your course's academic integrity rules. AutoStudy should
> not fabricate personal experience, group details, datasets, citations, or
> instructor instructions.

For demos involving assignment completion, always show one of:

- the alignment question before generation;
- the final "review before submit" checkpoint;
- the local `verification.log`;
- a human review item still requiring user action.

This makes the product feel honest and safer.

---

## Audience

Primary:

- Students using Canvas LMS who want a local, source-grounded agent workflow.
- Students who already use AI tools but want deeper file-aware workflows.
- Students overloaded by deadlines, course PDFs, reports, projects, and group
  deliverables.

Secondary:

- HKUST(GZ) students, where the current workflow has real validation evidence.
- Students at other Canvas-based schools using one configured Canvas instance.
- Agent / skill ecosystem users interested in local workflow design.

---

## Feature Matrix For Public Docs

| Capability | Status | Public Wording |
|---|---|---|
| Canvas status scan | usable | "Plan your next actions from current Canvas data." |
| Assignment reconnaissance | usable and hardening | "Find the actual spec across Canvas sources." |
| Draft generation | usable and hardening | "Produce local drafts with verification evidence." |
| Canvas submission | code-level verified, needs safe real E2E | "Available only after explicit confirmation; final live verification pending." |
| Course material sync | usable | "Archive lecture files and Canvas structure locally." |
| Course notes | usable | "Generate Markdown notes from synced lecture PDFs." |
| Tutor / mastery tracking | planned | "Future interactive review layer." |
| Proactive reminders | planned | "Future opt-in reminder layer." |

---

## Demo Scripts

### 30-Second Status Demo

1. User asks: "看看这周有什么作业".
2. Agent runs `sync-status`.
3. Screen shows `REPORT.md` with top recommended actions.
4. User chooses item 1.
5. Agent resolves exact IDs with `select_plan_item.py`.

End line:

> "It plans first. It does not run homework until you choose."

### 60-Second Homework Demo

1. User asks to draft a project.
2. Agent shows source trail: assignment page empty, module PDF found, rubric
   absent or extracted.
3. Agent asks the one user-owned question that affects the plan.
4. Agent writes `alignment_brief.md`.
5. Agent generates `pipeline_design.md`.
6. Show `draft/` and `verification.log`.
7. Show "No Canvas submission was attempted."

End line:

> "The output is not a chat answer. It is a traceable local workbench."

### 45-Second Notes Demo

1. User syncs a course.
2. Show lecture PDFs categorized under `materials/`.
3. User asks for course notes.
4. Show generated Markdown with callouts, LaTeX, and a Mermaid concept map.

End line:

> "Course context becomes reusable study material."

---

## Do Not Promise

- 100% automatic success on any assignment.
- Automatic Canvas submission.
- Hidden background execution after a status scan.
- No login.
- No review needed.
- Compliance with every course policy by default.
- Guaranteed compatibility with every Canvas school or SSO configuration.

---

## Assets To Prepare Later

- Screenshot of `sync-status` report.
- Screenshot of a `spec.md` source trail.
- Screenshot of an `alignment_brief.md` design skeleton.
- Screenshot of a mixed `draft/` folder.
- Short screen recording of course-note generation.
- A public-safe sample workbench with sensitive Canvas content removed.
