# Agent Progress

> Session-by-session handoff log. Newest entries on top. Anyone (including a future Claude session) reading this should be able to pick up cleanly.

## 2026-06-01 — Clarified Canvas login/session mental model

Validated that `canvascli init` is a login/refresh command, not a session health check: it always opens Chromium and writes a new `state.json` after successful SSO. The correct health check is `.venv/bin/canvascli whoami`, which returned the Canvas user from the current saved session without requiring browser login. Docs now distinguish `state.json` (canvascli's saved Canvas API cookie) from the SSO "remember login" checkbox (controls how smooth the next SSO refresh is), and explicitly tell agents not to run `init` just to test status. Reran the documented flow after the docs change: Step 0 reported `venv: ok`, `canvascli: ok`, `session: ok`; then `courses` returned 7 Spring courses, `assignments` returned 57 assignments across 6 courses, and `announcements` returned 5 items, all without running `init`.

## 2026-06-01 — Split term-scope fix across canvascli + AutoStudy docs

Reviewed the `eca80a5` AutoStudy hardening commit and moved the root fix back to the data layer: `canvascli` now owns default latest-active-term selection plus explicit `--term` overrides. AutoStudy docs were updated to keep `sync-status` simple (`courses` / `assignments` / `announcements`) and document the CLI contract instead of reimplementing term filtering in skill flow. Verification after refreshing `canvascli init`: default AutoStudy flow returned 7 Spring courses / 57 assignments / 5 announcements; explicit `--term "2025-26 Spring"` returned 7 courses / 57 assignments.

## 2026-05-23 / 24 — MVP day: 4 flagship scenarios E2E + guizang slides + docs

### What changed

Pushed AutoStudy to **MVP (M3 core)**: the four flagship homework scenarios — **paper / slides / math / lab** — each ran end-to-end on a real HKUST(GZ) Canvas assignment and produced a real deliverable. Plus integrated the upstream [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) as the default slides path.

### Real-assignment evidence (under `data/homework/`, gitignored)

| Scenario | Course / assignment | Deliverable | Bytes / pages |
|---|---|---|---|
| **paper** | DLED3020 Paper Critique (id 14250) | `DLED3020/paper-critique/final.pdf` | 45,684 B / 3 pp / PDF v1.5 |
| **slides (beamer)** | UCUG1077 Group presentation (id 14297) | `UCUG1077/group-presentation/slides.pdf` | 82,370 B / 10 pp |
| **slides (guizang)** | same | `UCUG1077/group-presentation/guizang/{index.html, slides_guizang.pdf}` | 47,443 B HTML (Style A · Kraft Paper · 10 sections) + 1,674,228 B PDF (1600×900) |
| **math** | DSAA2043 Lab-Assignment 1 (id 17284) | `DSAA2043/lab-assignment-1/solution.pdf` | 49,390 B / PDF v1.5 |
| **lab** | DSAA2012 Project Report (id 18361) | `DSAA2012/project-report/{src/*.py, tests/, test_report.md, report.pdf}` | report.pdf 43,553 B / 3 pp; pytest 14/14 pass / exit=0 |

### New + updated skill files

- `sub-skills/tasks/do-homework.md` — flagship MVP task: `[A]` canvascli fetch → `[B]` AskUserQuestion intent → `[C]` task profile + orchestrator → `[D]` deliverable → `[E]` AskUserQuestion submit → `[F]` `canvascli submit`. Only two interaction points.
- `sub-skills/tools/writing-helper.md` — agent writes essay / report / reflection drafts directly. `[CITATION NEEDED]` placeholders enforced when references.bib is missing entries.
- `sub-skills/tools/paper-search.md` — arxiv Python package wrapped as a templated script (`scripts/run_paper_search.py`) → references.bib + references.json.
- `sub-skills/tools/figure-maker.md` — matplotlib line/bar/scatter with CJK font config.
- `sub-skills/tools/code-writer.md` + `test-runner.md` — Python source + pytest with `test_report.{md,json}`.
- `sub-skills/tools/slide-maker.md` — **rewritten**: default path wraps guizang-ppt-skill (HTML magazine / Swiss + Playwright PDF print); LaTeX-beamer kept as fallback for strict-PDF academic work.
- `sub-skills/tools/_index.md` — tool registry expanded to 7 entries; new `run_tests` verb; new "Scenario → Tool chain" table; video row marked OUT OF SCOPE.
- `sub-skills/tasks/task-orchestrator.md` — type vocabulary aligned (`paper | slides | math | lab | video | notes | mixed`); MVP scenarios validated table replaces the "minimum viable" placeholder.

### Submit interface (M3-SUBMIT)

`canvascli/canvascli/resources/submit.py` — the 3-step Canvas upload protocol is implemented at the code layer:

1. POST `/api/v1/courses/:cid/assignments/:aid/submissions/self/files` → `{upload_url, upload_params}`
2. POST `upload_url` with multipart (`upload_params` + file), handles 302 redirect confirm
3. POST `/api/v1/courses/:cid/assignments/:aid/submissions` with `submission[submission_type]=online_upload` + `submission[file_ids][]=<file_id>`

Code path verified by reading the file. **Not yet exercised against a real unexpired assignment.** Flipping `M3-SUBMIT` from `partially-verified` → `passing` requires the user to provide a sandbox / unexpired assignment for one real round-trip.

### Dependencies installed

- AutoStudy `.venv`: `matplotlib`, `numpy`, `arxiv`, `pytest` (via Tsinghua mirror — the default proxy at 127.0.0.1:6666 had SSL EOF errors against pypi.org).
- `~/.claude/skills/guizang-ppt-skill/` — git clone from op7418's upstream. Shared across all decks the agent makes.
- `tectonic` (brew, pre-existing) — used by both pdf-renderer and the slides beamer fallback.
- Playwright + chromium (pre-existing in `.venv`) — used by the new guizang PDF export.

### Pitfalls burned in this push (added inline to relevant `.md`)

1. `pip install` via the user's default proxy (127.0.0.1:6666) hit `SSLError(SSLEOFError)` against pypi.org. Workaround: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`.
2. `data/` is gitignored — `git commit -f` against it was rejected (correctly). Evidence lives in commit messages + `feature-list.json` `evidence[]` arrays + (eventually) `docs/verification/` if it gets substantial enough.
3. `$\LaTeX$` inside a markdown `- [ ]` checkbox list breaks tectonic with `\spacefactor in math mode` (the `\LaTeX` macro calls `\@` which clashes with math mode). Fix: write plain text "LaTeX".
4. `\bm` from the `bm` package overflows tectonic's mathchar range under certain font setups. Fix: use `\mathbf{}` instead, drop the `bm` package.
5. Subprocess-launched sub-agents in a sandboxed environment can't `git clone` (network blocked) or write to `~/.claude/skills/`. The parent agent must do the install outside the sandbox.
6. guizang Playwright PDF export needs `localStorage.setItem('guizang-ppt-low-power','1')` *before* navigation completes, otherwise WebGL canvases fight the print loop and produce black pages.

### Where to look next

- `M3-SUBMIT` → ask user for a sandbox assignment id, run one real `canvascli submit`, flip status to `passing`.
- `M4-TUTOR` is the next milestone — Interactive Tutor with persistent `data/mastery/<course>.json`. AutoStudy.pdf has the design.
- `M3-VIDEO` is OUT OF SCOPE for this repo — user is building a separate video skill.

### Open uncertainties

- guizang Style B (Swiss) integration hasn't been exercised — only Style A was used. Should work since slide-maker.md documents both paths.
- The lab scenario built a representative numpy project (regression + clustering); the real DSAA2012 assignment is in an attached PDF the agent didn't have access to. `[TODO: align with actual project spec]` markers are in `src/`.

---

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
