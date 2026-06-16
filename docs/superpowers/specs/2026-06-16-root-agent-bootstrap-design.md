# Root Agent Bootstrap Design

## Context

`skill.md` is already the AutoStudy runtime entrypoint. It explains the product
contract, user-intent routing, runtime architecture, homework stage boundaries,
and safety rules. Adding `sub-skills/tasks/index.md` would duplicate part of
that role and risk creating a second task router.

Some agent runtimes load repository-root guidance files such as `AGENTS.md` or
`CLAUDE.md` before they inspect project-specific files. AutoStudy currently has
no committed root bootstrap file, so those agents may skip `skill.md` and jump
directly into `sub-skills/tasks/*.md`.

## Decision

Do not add `sub-skills/tasks/index.md`.

Add two thin root bootstrap files:

- `AGENTS.md`
- `CLAUDE.md`

Both files must point runtime agents to `skill.md` as the single project entry.
They must not duplicate homework routing, source reconnaissance, alignment,
or orchestration details.

## Runtime Boundary

The intended loading chain is:

```text
AGENTS.md / CLAUDE.md
-> skill.md
-> the task selected by skill.md
-> the current task's explicit handoff
```

`skill.md` remains responsible for user intent routing. `do-homework.md` remains
responsible for homework first-stage routing. Individual task files remain
responsible for their own tail handoffs.

## Development Boundary

The root bootstrap files are not development guides. Development work still
starts from `docs/DEVELOPMENT.md`.

The bootstrap files may mention `docs/DEVELOPMENT.md` only to distinguish runtime
agent usage from repository development.

## Test Expectations

Policy tests should verify:

- root `AGENTS.md` exists and points to `skill.md`;
- root `CLAUDE.md` exists and points to `skill.md`;
- `.gitignore` does not exclude either committed bootstrap file;
- both files stay thin bootstrap files instead of embedding task workflow detail;
- README files continue pointing developers to `docs/DEVELOPMENT.md`;
- runtime protocol distinguishes committed bootstrap files from local ignored
  developer overrides.
