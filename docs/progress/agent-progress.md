# Agent Progress

> Session-by-session handoff log. Newest entries on top. Anyone (including a future Claude session) reading this should be able to pick up cleanly.

## 2026-05-14 — Docs harness adoption (light)

### What changed

- Added this file (`docs/progress/agent-progress.md`)
- Added `docs/plans/feature-list.json` — structured backlog mirroring ROADMAP M1–M5 with explicit `status` per feature
- Added `AGENTS.md` at repo root — developer-facing entry, distinct from `skill.md` (user-facing)

### Why

Adopted the lightweight slice of [Aurorra1123/ust-dev `harness-best-practice`](https://github.com/Aurorra1123/ust-dev/commit/59761756ebcd01d68a4b62729b4e03f09948dc63):

- A persistent log for cross-session handoff (this file)
- A structured backlog with verification status (`feature-list.json`)
- A separate developer entry (`AGENTS.md`) so `skill.md` can stay focused on end-user agent usage

Skipped `docs/{standards,adr,architecture,verification,exec-plan}` — at AutoStudy's current scale, ROADMAP and PITFALLS already cover what those would, and adding them now is overhead. Revisit when a new contributor can't ramp up without them.

### Where to look next

- Repo file layout: `AGENTS.md` "Where things live" section
- M3 remaining work: `ROADMAP.md` M3 section, numbered list near the bottom
- Backlog status: `docs/plans/feature-list.json`

---

## 2026-05-13 — Big day: M2 lockdown → canvascli extraction → M3 foundation

This was actually one long session that produced 6 commits on AutoStudy + 1 commit on a brand-new sister repo (`canvascli`). The arc:

### Phase A: M2 lockdown (commit `7e6725e`)

Verified that a fresh agent reading `skill.md` can run `sync-status.md` end-to-end and produce a clean 5-section markdown summary. This was the first proof that the skill-as-markdown architecture actually works — agent honored safety rules, did not auto-download, used AskUserQuestion for next-action.

Two real bugs surfaced during validation, both captured in `sub-skills/tasks/sync-status.md` Pitfalls:

- Python tuple `(datetime, dict)` sort raises TypeError when datetimes equal (dict isn't comparable). Fix: always pass `key=lambda x: x[0]`.
- "Overdue" shouldn't list assignments overdue >30 days — past-term residue, not actionable. Added 30-day cap.

### Phase B: M3 design (commits `e2845fe`, `106f95b`)

Reframed M3 as a three-layer architecture (task → orchestrator → tools) after discussing heterogeneous output scenarios (report / slides / video / proof / code). Wrote `MARKETING.md` documenting the five flagship scenarios that anchor external narrative — informs which tools to build in what order.

### Phase C: M3 foundation (commit `37b7daf`)

Built the skeleton:

- `sub-skills/tools/_index.md` — capability registry + verb vocabulary
- `sub-skills/tools/pdf-renderer.md` — first production-grade tool (tectonic two-step path, since user has tectonic but no xelatex; ctexart + PingFang SC + Menlo for Chinese)
- `sub-skills/tasks/task-orchestrator.md` — pipeline composer reading task profile, matching capabilities, executing tools that communicate via files in `data/homework/.../`

End-to-end smoke test: minimal task profile → orchestrator matches `render_pdf` → pdf-renderer two-step → real PDF on disk (48 KB, valid `%PDF-1.5` magic). The three-layer architecture works.

### Phase D: canvascli extraction (commit `90072ac` here + `0385f54` in new repo)

Studied `sshwy/pku3b` source code (user cloned it locally to `pku3b/` for inspection) and decided AutoStudy should extract its `scraper/` package the same way AutoPku depends on pku3b. New independent repo at `~/workspace/canvascli/`.

- typer-based CLI, 11 flat top-level commands (init / version / whoami / courses / assignments / assignment / announcements / files / folders / download / submit)
- **JSON-by-default** output, `--pretty` for human-readable (improvement over pku3b's ANSI text)
- Cookie auth via Playwright (no stored password; safer than pku3b's plaintext config)
- Hardcoded `hkust-gz.instructure.com` (not multi-instance)
- `submit` implements Canvas's three-step upload protocol — M3 do-homework can use it directly

AutoStudy deleted its `scraper/`, replaced `scraper-setup.md` / `scraper-api.md` with `canvascli-setup.md` / `canvascli-api.md`, and updated `sync-status.md` to shell out to `canvascli courses/assignments/announcements`. End-to-end re-verified: identical output, no SSL warnings.

### Phase E: ROADMAP rewrite (commit `9964365`)

Old ROADMAP described an in-repo scraper that no longer existed. Rewrote with the canvascli extraction folded in, M1/M2 marked complete, M3 sub-tasks marked with current status, and a new cross-stage principle separating data acquisition (canvascli) from skill orchestration (AutoStudy).

### What's next (start of next session, read this first)

M3 remaining work, in recommended order:

1. **`sub-skills/tasks/do-homework.md`** — write the skeleton. End-to-end target: user says "complete DLED3020 Assessment Task 3", agent uses canvascli to fetch the assignment description + rubric, presents summary, asks confirmation, runs orchestrator to produce a PDF draft, asks confirmation again, submits via `canvascli submit`.
2. **`sub-skills/tools/writing-helper.md`** — once do-homework has a real flow, the draft quality needs an actual tool. Without it, the orchestrator output is a placeholder.
3. Add `paper-search.md` and `figure-maker.md` to complete the Report pipeline.
4. Validate the full Report pipeline against a real (low-stakes) HKUST(GZ) assignment.

### Open uncertainties for next session

- `canvascli submit` works in code but hasn't been tested against a real Canvas assignment yet. Worth testing on a low-stakes assignment before relying on it in `do-homework`.
- The `data/homework/test/output.pdf` from the orchestrator smoke test was visually confirmed by the user but isn't archived. If we adopt `docs/verification/` later, this is the kind of artifact that belongs there.

---

## Earlier work (pre-2026-05-13)

Repo bootstrap, scraper iterations, M1/M2 design exploration — captured in `plan.md` (the original brief) and `AutoStudy.pdf` (the design document). Not re-narrated here.
