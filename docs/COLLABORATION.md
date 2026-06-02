# Collaboration Rules

This document records the working contract for AutoStudy development on the
`codex/deepwisdom-updates` branch. It exists because AutoStudy changes often
span three related projects, and small bugs can otherwise turn into tangled
cross-repo fixes.

## Project Roles

### `canvascli`: data layer

`canvascli` owns Canvas access behavior:

- login/session handling
- Canvas REST API calls and pagination
- course, assignment, announcement, file, download, and submit commands
- CLI flags and JSON output contracts
- default data scope decisions, such as which term a default command returns

If a bug is about how Canvas data is fetched, filtered, scoped, or shaped, fix it
in `canvascli` first.

### `autoust`: application layer

AutoStudy owns agent-facing workflows:

- `skill.md` entry routing
- `sub-skills/tasks/*.md` task flows
- `sub-skills/tools/*.md` tool contracts
- user confirmation points
- homework/study orchestration
- progress, roadmap, pitfalls, and developer documentation

AutoStudy depends on `canvascli` as a CLI contract. It should not copy
`canvascli` internals into skill flow docs.

### Canvas Copilot: reference project

Canvas Copilot is a design reference, not a runtime dependency.

Prefer the local clone when available:

```text
/Users/deepwisdom/Desktop/project/canvas_copilot
```

For other machines, use the public repo:

[X-isdoingreat/Canvas_pilot_public](https://github.com/X-isdoingreat/Canvas_pilot_public)

Consult Canvas Copilot before inventing new Canvas workflows, especially for:

- deep assignment/spec reconnaissance
- course scope and routing
- submission safeguards
- hooks and verification gates
- recurring automation
- public/private boundary rules

AutoStudy's distilled notes live in `docs/canvas-pilot-reference.md`.

### Reference, But Do Not Clone

Canvas Copilot is more mature in many Canvas workflow details, so new
AutoStudy Canvas behavior should start by inspecting how Canvas Copilot handles
the same problem. That includes running or reading a comparable real workflow
when possible, not guessing from memory.

But AutoStudy and Canvas Copilot have different product shapes:

- Canvas Copilot is closer to a repeatable automation system: scan Canvas,
  propose a batch plan, get approval, dispatch items, and keep strict run
  ledgers.
- AutoStudy is closer to a study assistant: it should keep the user in the
  loop, explain what it found, ask for missing context, help the user decide
  what to do next, and compose task flows around the user's current intent.

Therefore, the rule is **borrow mature mechanisms, redesign the interaction**.
For example, AutoStudy should borrow Copilot's atomic Canvas data access,
source-by-source assignment reconnaissance, workbench structure, verification
logs, and lightweight state files. It should not blindly copy Copilot's batch
automation defaults when an assistant-style checkpoint, explanation, or user
supplement step better fits AutoStudy.

When adapting a Copilot pattern, document both sides:

1. What Canvas Copilot does and why it is mature.
2. Which part AutoStudy adopts directly.
3. Which part AutoStudy changes because its assistant-oriented user experience
   is different.

## Layer Boundary

Describe `canvascli` behavior in AutoStudy as a contract, not as an
implementation.

Good AutoStudy wording:

```text
canvascli owns default term selection. AutoStudy calls the default command for
the normal current semester, and passes --term only when the user explicitly asks
for another semester.
```

Avoid AutoStudy wording that repeats the data-layer algorithm:

```text
canvascli checks field A, field B, applies grace window C, then sorts by D.
```

That implementation belongs in `canvascli` code and `canvascli` docs. Keeping it
out of AutoStudy prevents application docs from drifting when the data-layer
algorithm changes.

## Cross-Repo Change Flow

When a change touches Canvas behavior:

1. Decide whether the bug belongs to the data layer or application layer.
2. If it affects Canvas access, fix `canvascli` first.
3. Update AutoStudy only against the new `canvascli` CLI contract.
4. Do not add temporary data-fetching workarounds to AutoStudy unless explicitly
   marked as transitional and documented.
5. Verify the combined flow from AutoStudy, using `.venv/bin/canvascli`, because
   that is how AutoStudy actually calls the data layer.

Preferred commit order for coupled changes:

1. `canvascli` commit for data-layer behavior.
2. `autoust` commit for task/docs/progress synchronization.

## Branch And Commit Policy

For rapid development, both repos use the user's long-lived branch:

```text
codex/deepwisdom-updates
```

Do not open a PR for every small change. Commit completed work to this branch in
each repo. Open PRs only when the user asks for review, release, or merge.

If a previous direct-main or experimental commit needs to be backed out, preserve
it on a backup branch before resetting or replacing it.

## Verification Policy

Code changes are not done until the combined workflow has been checked.

For `canvascli`, run local checks appropriate to the change, such as:

```bash
python3 -m compileall canvascli
.venv/bin/canvascli <command> --help
```

For AutoStudy docs/config, run checks appropriate to the touched files, such as:

```bash
python3 -m json.tool docs/plans/feature-list.json
git diff --check
```

For integration, run commands from the AutoStudy repo using the AutoStudy venv:

```bash
.venv/bin/canvascli courses
.venv/bin/canvascli assignments
.venv/bin/canvascli announcements
```

If the Canvas session is expired, do not mark real E2E verification as passed.
Run `canvascli init`, let the user complete SSO, then retry. If the user cannot
refresh the session during the current session, record the verification gap in
`docs/progress/agent-progress.md`.

Record real verification evidence in the repo. Depending on size, use:

- `docs/progress/agent-progress.md`
- `docs/plans/feature-list.json`
- `docs/PITFALLS.md`
- `docs/verification/<date>/<topic>/`

Chat-only evidence does not count.

## Documentation Sync Checklist

After any feature or CLI contract change, check whether these need updates:

- `AGENTS.md` — developer rules, repo boundaries, reference project entry.
- `skill.md` — user-facing entry and safety rules.
- `sub-skills/tools/canvascli-api.md` — CLI contract and JSON shapes.
- `sub-skills/tasks/*.md` — task flow changes.
- `docs/PITFALLS.md` — reusable pitfalls and burnt-once lessons.
- `docs/progress/agent-progress.md` — what changed, verification, next step.
- `docs/plans/feature-list.json` — feature status and evidence.

Prefer docs that explain the boundary and contract. Avoid duplicating lower-layer
implementation details in upper-layer workflow docs.

## Privacy And Portability

- Never log or commit Canvas cookies, session files, tokens, or credential
  material.
- Real Canvas verification may record counts, term names, and pass/fail evidence,
  but avoid committing sensitive raw course data.
- Local paths can be mentioned when useful, but must not be the only reference
  for collaborators. Provide portable links such as GitHub repos when available.
- `data/*.json` verification snapshots are local artifacts and must remain
  gitignored.

## Term-Scope Bug Example

The 2026-06-01 term-scope fix is the model example for this workflow.

Problem:

AutoStudy's `sync-status` needed Spring data, but the old `canvascli` default
scope could return the wrong term.

Incorrect fix:

- Add Python term filtering directly to `sub-skills/tasks/sync-status.md`.
- Tell future agents to call `courses --all-terms` and reimplement scope logic in
  AutoStudy.

Correct fix:

- Move default term-scope behavior to `canvascli`.
- Add/verify explicit `--term` support in `canvascli`.
- Keep AutoStudy's task flow simple:

```bash
.venv/bin/canvascli courses > data/courses.json
.venv/bin/canvascli assignments > data/assignments.json
.venv/bin/canvascli announcements > data/announcements.json
```

- Update AutoStudy docs to describe the CLI contract, not the data-layer
  algorithm.
- Verify from AutoStudy using its `.venv/bin/canvascli`.
- Record verification in progress and feature-list docs.
