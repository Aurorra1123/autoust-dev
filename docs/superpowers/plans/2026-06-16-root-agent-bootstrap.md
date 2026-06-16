# Root Agent Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add thin root `AGENTS.md` and `CLAUDE.md` bootstrap files that direct agents to `skill.md` without creating a second task index.

**Architecture:** `skill.md` remains the single runtime route map. Root bootstrap files only redirect agent runtimes to `skill.md` and distinguish runtime usage from repository development. Existing policy tests are updated to encode the new boundary.

**Tech Stack:** Markdown documentation plus pytest policy tests.

---

### Task 1: Encode The New Bootstrap Boundary

**Files:**
- Modify: `tests/test_developer_entry_boundary.py`
- Modify: `docs/runtime-agent-protocol.md`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing policy test**

Replace the old root-AGENTS absence assertion with a test that expects both root bootstrap files to exist, point to `skill.md`, avoid embedding task workflow detail, and preserve `docs/DEVELOPMENT.md` as the developer entry.
Also assert `.gitignore` does not ignore committed `AGENTS.md` or `CLAUDE.md`.

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_developer_entry_boundary.py -q
```

Expected: fail because `AGENTS.md` and `CLAUDE.md` do not exist yet and runtime protocol still describes root `AGENTS.md` as only a local ignored developer override.

- [ ] **Step 3: Update runtime protocol**

Clarify that committed root `AGENTS.md` / `CLAUDE.md` are bootstrap pointers to
`skill.md`, while local ignored developer overrides or development docs remain
forbidden runtime context.

- [ ] **Step 4: Remove obsolete ignore rule**

Remove the old `AGENTS.md` entry from `.gitignore` so the committed bootstrap can
be tracked normally.

- [ ] **Step 5: Run the test again**

Run:

```bash
.venv/bin/python -m pytest tests/test_developer_entry_boundary.py -q
```

Expected: still fail until root bootstrap files are added.

### Task 2: Add Thin Root Bootstrap Files

**Files:**
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Test: `tests/test_developer_entry_boundary.py`

- [ ] **Step 1: Add `AGENTS.md`**

Create a short bootstrap file that tells agents to read `skill.md` first, not to
preload task files, and to use `docs/DEVELOPMENT.md` only for repository
development.

- [ ] **Step 2: Add `CLAUDE.md`**

Create the same boundary for Claude Code style startup.

- [ ] **Step 3: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_developer_entry_boundary.py -q
```

Expected: pass.

- [ ] **Step 4: Run full tests**

Run:

```bash
.venv/bin/python -m pytest tests -q
```

Expected: all tests pass.
