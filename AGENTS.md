# AGENTS.md

> Entry + constraints for **developers** of AutoStudy. If you're using AutoStudy as a skill (i.e. you're an end-user agent loading it to do Canvas tasks), read [skill.md](./skill.md) instead.

## Who reads this

This file is for the next person (or agent) who picks up AutoStudy development — extending tasks, adding tools, fixing bugs. Two different audiences, two different entry points:

| Audience | Entry | Asks |
|---|---|---|
| **Skill user** (agent doing Canvas tasks for the user) | [`skill.md`](./skill.md) | "What can I do for this HKUST(GZ) student right now?" |
| **Skill developer** (this file) | `AGENTS.md` | "How is this repo organized? What's the current state? Where do I write things?" |

If you only read `skill.md`, you'd think the repo is a runtime tool. Reading this file first tells you it's also an evolving project with its own roadmap, conventions, and verification rituals.

## Sister repo

The Canvas data layer (`canvascli`) lives at **`~/workspace/canvascli/`** (or wherever the user cloned it). It's a separate git repo, installed into AutoStudy's `.venv` via `pip install -e`. When you change Canvas access behavior, that work belongs in `canvascli/`, not here.

For the full three-project workflow, branch policy, verification rules, and
documentation-sync checklist, read `docs/COLLABORATION.md`.

Layer boundary:

- `canvascli` is the data layer: Canvas login/session, REST API calls, pagination, course/assignment/file/announcement/submission commands, and stable JSON output.
- `autoust` is the application layer: skill routing, task orchestration, study/homework workflows, user confirmation points, and documentation for agents.

When a bug or feature request touches both, land the data-layer change in `canvascli` first, then update AutoStudy docs/tasks against the new CLI contract. For rapid development, keep both repos on the user's long-lived update branch (`codex/deepwisdom-updates`) and commit there; open a PR only when the user asks for review or release.

## Reference project

Canvas Copilot is the design reference for this project. Prefer the local clone at **`/Users/deepwisdom/Desktop/project/canvas_copilot`** when it exists; otherwise use the public repo [X-isdoingreat/Canvas_pilot_public](https://github.com/X-isdoingreat/Canvas_pilot_public). Before inventing a new Canvas workflow, inspect how Canvas Copilot solved similar problems, especially around deep assignment reconnaissance, submission safeguards, hooks, tests, and recurring automation.

AutoStudy's distilled notes live in `docs/canvas-pilot-reference.md`. Treat that file as the first stop for "what should we borrow from Canvas Copilot?" and go to the source repo when implementation details matter.

## Start-of-session checklist

Run through these before touching code:

1. Read `docs/progress/agent-progress.md` — what just happened and where we left off
2. Read `docs/plans/feature-list.json` — the structured backlog with status
3. Check `git log --oneline | head -10` — recent commits across both repos (`AutoStudy` and `~/workspace/canvascli`)
4. Re-verify one or two recently-passed features by re-running them. If a regression slipped in, **flip status back to `untested` first**, then start work
5. Pick exactly one in-progress or pending feature to push forward

## End-of-session checklist

Don't close out a session without:

- [ ] Updating `docs/progress/agent-progress.md` (1–3 sentences on what changed and what's next)
- [ ] Updating the status of any feature you touched in `docs/plans/feature-list.json`
- [ ] Capturing verification evidence somewhere (in-line commit body, screenshot path noted, or `docs/verification/<date>/<topic>/` if substantial)
- [ ] No uncommitted changes (or if there are, explain in progress note why)

## Where things live

| What | Where |
|---|---|
| Roadmap (the big picture) | [docs/ROADMAP.md](./docs/ROADMAP.md) |
| Skill entry for end-users | [skill.md](./skill.md) at repo root |
| Marketing scenarios | [docs/MARKETING.md](./docs/MARKETING.md) |
| Burnt-once pitfalls | [docs/PITFALLS.md](./docs/PITFALLS.md) |
| Backlog with status | `docs/plans/feature-list.json` |
| Session handoff notes | `docs/progress/agent-progress.md` |
| Skill tool/task docs | `sub-skills/{tools,tasks}/*.md` |

We're deliberately **not** maintaining `docs/standards/` or `docs/adr/` yet. ROADMAP and PITFALLS already cover what they would, at this scale. Add them if/when they become genuinely needed (i.e. a new contributor can't ramp up without them).

## Rules of thumb

- **Verification before "passing"**: never flip a feature from in-progress to passing without something concrete to point to (a commit, a tested artifact, a screenshot).
- **Pitfalls go to `docs/PITFALLS.md` or the relevant sub-skill `.md`**, not into chat or commit messages. The next agent won't read your commit body.
- **Don't write features that require canvascli changes without confirming the canvascli repo state first.** They evolve together.
- **Repo > chat**: anything worth knowing twice goes to a file, not the conversation.

## Influences

The two-tier (entry / docs) layout follows the pattern in [Aurorra1123/ust-dev `harness-best-practice` skill](https://github.com/Aurorra1123/ust-dev/commit/59761756ebcd01d68a4b62729b4e03f09948dc63) — minus the parts that don't fit AutoStudy yet (`adr/`, `architecture/`, `verification/`, `exec-plan/`). We adopt only `progress/` and `plans/` for now; the rest is overhead at our current size.
