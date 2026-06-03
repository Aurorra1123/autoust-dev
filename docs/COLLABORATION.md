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

Current approved homework direction:

- Reconnaissance follows Canvas Copilot `canvas-generic` Stage 1-5: fetch
  context, find rubric, locate inputs, review investigation, and classify output
  mode.
- This reconnaissance is agent-led. `scripts/recon_assignment.py` is historical
  transition evidence, not the production `do-homework` path.
- `spec.md` is a standardized report written after reading all sources; full
  source text belongs in `references/`, not in a raw context dump.
- `problem.md` is temporary compatibility for older tools.
- After the user supplement checkpoint, `do-homework` writes
  `pipeline_design.md`; `task-orchestrator` executes that plan instead of
  reading `task_profile.yaml`.

### Skills Architecture

AutoStudy's skills are **domain expertise supplements**, not fixed pipeline
scripts. The model already knows how to write code / write essays / render PDFs.
Skills tell it "how we do it right here" — project conventions, quality bars,
self-check lists, and composition patterns.

The complete architecture spec lives in **`docs/skills-architecture-spec.md`**.
Key design decisions:

1. **Progressive loading**: `_index.md` only shows top-level skills (code-writer,
   writing-helper, etc.). Sub-skills and language/type appendices are discovered
   by reading the parent skill file. Never flatten sub-skills into `_index.md`.

2. **Core + appendix pattern**: Each skill has a main file with shared guidance,
   plus optional appendix files for language-specific or type-specific rules
   (e.g., `code-writer-python.md`, `writing-helper-report.md`).

3. **Skills can nest skills**: writing-helper may invoke humanizer in
   post-processing; code-writer delegates to test-runner for verification.
   Nesting is conditional — the skill checks context before loading sub-skills.

4. **Preference integration**: Defaults in skill files → overridden by
   `pipeline_design.md` stage declarations (task-level) → overridden by
   `data/course-overrides/` (course-level, not yet implemented) → overridden by
   Claude Code memory (user-level, not yet implemented).

5. **Unified review framework**: Instead of per-type verification rules, all
   types share a common spec-vs-deliverable semantic diff pattern. Each skill
   provides its own Self-check list; the orchestrator or sub-agent audit reads
   spec + constraints + deliverable and returns a JSON gap array.

### Design Principles (M3.5+)

Five principles govern all post-M3.5 development. They originate from deep
reference to Canvas Copilot but serve AutoStudy's assistant-oriented identity:

1. **Assistant, not automation.** Borrow Copilot's mature mechanisms (atomic
   data access, source-by-source reconnaissance, structured state), but keep
   the user in the loop at every meaningful decision point. No batch execution,
   no unsupervised submission, no hidden automation.

2. **Dynamic skills composition, no fixed pipelines.** `pipeline_design.md` is
   designed on-the-fly by the agent after reconnaissance. `_index.md` is a
   skills registry loaded on demand, not a fixed routing table. Output modes
   (doc_prose / pdf_typed / code / slides / mixed) should eventually become
   loadable skills themselves, not preset pipelines.

3. **Multi-turn iteration.** Complex tasks rarely succeed in one session.
   Design for: (a) in-session interrupt/resume via `result.json` + workbench
   files, and (b) cross-session iterative refinement where the user can
   continue from an existing draft rather than starting over. `result.json`
   should support `revision_needed` status.

4. **Three-layer preference system.** Task-level preferences collected at
   `[B]` → stored in `investigation/user_notes.md`. Course-level preferences
   accumulated across assignments → stored in `data/course-overrides/<COURSE>.md`.
   User-level preferences → stored in Claude Code project memory
   (`~/.claude/projects/.../memory/`). Each layer has a different lifecycle
   and serves a different purpose.

5. **Review-first design.** Insert sub-agent review points wherever valuable.
   Not limited to Copilot's three fixed sub-agents (A/B/C). Each pipeline
   stage in `pipeline_design.md` can optionally declare "review after this
   stage" with specific review criteria and an acceptance checklist. This
   makes the review infrastructure composable rather than rigid.

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
