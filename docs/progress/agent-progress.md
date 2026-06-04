# Agent Progress

> Session-by-session handoff log. Newest entries on top. Anyone (including a future Claude session) reading this should be able to pick up cleanly.

## 2026-06-03 — UCUG1505 end-to-end validation + DSAA2011 trajectory deep-dive

UCUG1505 Creative Coding Final Project 验证。从 canvas/ 原始数据开始，子代理完整走完侦查→设计→执行流程。**首轮 P0-P5 全部 FIXED**，无需迭代。

### 测试设计

与 DSAA2011 不同，workbench 只保留 canvas/ 原始 JSON 快照（无预写 pipeline_design.md、无预写 spec.md）。子代理从零开始侦查，测试动态 pipeline 组合能力。

### UCUG1505 验证结果

| 维度 | 状态 | 关键指标 |
|---|---|---|
| P0 Skill 读取 | FIXED | 7 个文件，三层加载顺序正确 |
| P1 Stage→Tool | FIXED | 4/4 stage 声明与执行完全一致 |
| P2 代码真实性 | FIXED | sketch.js 340行/9.8KB，完整 Particle 类 |
| P3 PDF 回退 | FIXED | pandoc→tectonic 两步法，28KB PDF |
| P4 目录结构 | FIXED | 全部在 draft/ 下 |
| P5 Write 工具 | FIXED | 11/11 Write 成功，0 Bash hack |

### DSAA2011 心路历程分析

并发派子代理深度分析 DSAA2011 两轮执行的完整行为轨迹，输出逐步追踪文档：
- 每个工具调用的行为依据（skill 指导 vs 自身判断）
- Skill 依从度 >85%，自主决策 ~25%（集中在环境调试）
- 两轮对比：Round 1 修 P3（fallback chain），Round 2 修 humanizer

### 产出文件

- `docs/pipeline-trace-audit-ucug1505.md` — UCUG1505 审计报告
- `docs/dsaa2011-execution-trajectory.md` — DSAA2011 心路历程轨迹

### 下一步

- 两个项目的技能架构验证均已完成
- 待验证项目：可考虑其他课程作业（如 DSAA2043、UCUG1077）进一步验证
- M3.5 剩余：ITERATION、SUB-AGENT-REVIEW、PREFERENCE-SYSTEM

## 2026-06-03 — Skills architecture refactoring + end-to-end validation

Completed the full skills architecture refactoring cycle triggered by the pipeline trace audit (P0-P5). Followed the superpowers workflow: brainstorm → spec → plans → subagent-driven implementation → 2-round end-to-end validation with trace analysis.

### What changed

**10 files modified/created across 6 commits:**

1. `docs/skills-architecture-spec.md` — Added §2.4 path discovery rules, fallback/min_quality fields, P5 note
2. `sub-skills/tools/_index.md` — Rewritten from routing table to pure capability menu
3. `sub-skills/tools/code-writer.md` — Restructured to unified template (Contract→Guidance→Appendices→Post-processing→Self-check)
4. `sub-skills/tools/code-writer-python.md` — New Python appendix (uv, project structure, notebook conventions)
5. `sub-skills/tools/writing-helper.md` — Restructured to unified template, added humanizer suggestion
6. `sub-skills/tools/writing-helper-report.md` — New report type appendix (data integrity rules)
7. `sub-skills/tools/pdf-renderer.md` — Added sequential fallback chain + Self-check
8. `sub-skills/tools/humanizer.md` — New post-processing skill for reducing AI patterns
9. `sub-skills/tasks/do-homework.md` — Added REPO_ROOT computation, pipeline shapes, new pipeline_design format
10. `sub-skills/tasks/task-orchestrator.md` — Added 5-step path discovery, SKILLS_DIR references

**Plus documentation:** pipeline-trace-audit.md, superpowers spec + plan

### Validation results (2 rounds on DSAA2011 ML Project)

| Issue | Original Audit | Round 1 | Round 2 |
|-------|---------------|---------|---------|
| P0: Skill reads | 0 reads | 8 reads | 13 reads |
| P1: Stage→Tool mapping | Missing | Full mapping | Full + humanizer |
| P2: Notebook execution | Fabricated | 36/37 cells | 25/25 cells, 0 errors |
| P3: PDF fallback | 4 failures | PARTIAL (skipped checks) | FIXED (sequential checks) |
| P4: Directory structure | Non-standard | All in draft/ | All in draft/ |
| P5: Write sandbox | Blocked | heredoc workaround | heredoc workaround |
| Humanizer | N/A | Not declared | Declared + applied |

Round 2 verification.log: 20 PASS / 4 FAIL (PDF quality — test environment limitation with no working LaTeX engine, not an architecture issue).

### Key design principle reinforced

Skills are domain expertise supplements — reference guidance, not hard constraints. Task spec always takes precedence over skill defaults. The model follows skills as best practice, but specific assignment requirements override.

### Where to look next

- Feature list: `docs/plans/feature-list.json` M3.5-SKILLS-ARCHITECTURE and M3.5-DYNAMIC-PIPELINE both now `passing`
- Audit report: `docs/pipeline-trace-audit.md`
- Design spec: `docs/superpowers/specs/2026-06-03-skills-refactor-design.md`
- Remaining M3.5 items: M3.5-ITERATION (pending), M3.5-PREFERENCE-SYSTEM (pending), M3.5-SUB-AGENT-REVIEW (pending)

## 2026-06-03 — Skills architecture design + Copilot per-type skill deep dive

Deep-dived into all six Canvas Copilot per-type skills (canvas-ics33, canvas-essay, canvas-reading-annotation, canvas-zybooks, canvas-inside, canvas-humanizer) and analyzed their complete pipelines — reconnaissance, generation, and verification stages differ significantly across types.

Key design decisions established through brainstorming with user:

1. **Skills are domain expertise supplements**, not fixed pipeline scripts. The model already knows how to write code/essays; skills provide project conventions, quality bars, and composition patterns.

2. **Progressive loading**: `_index.md` only shows top-level skills. Sub-skills and appendices (code-writer-python.md, writing-helper-essay.md, humanizer.md) are discovered by reading the parent skill file. Never flatten sub-skills into `_index.md`.

3. **Core + appendix pattern**: Main skill file has shared guidance; language-specific (code-writer-python.md) or type-specific (writing-helper-report.md) details go in separate files loaded on demand.

4. **Skills can nest skills**: writing-helper may invoke humanizer in post-processing; code-writer delegates to test-runner. Nesting is conditional — checked against `pipeline_design.md` declarations and user preferences.

5. **Preference integration via pipeline_design.md**: Language, type, constraints, review flags are declared per-stage in `pipeline_design.md`. This is the task-level preference mechanism (course-level and user-level preferences are future work).

Created `docs/skills-architecture-spec.md` — the authoritative design document for all skill file structure, loading mechanism, composition patterns, pipeline_design format, and preference system integration. Updated COLLABORATION.md (Skills Architecture section), AGENTS.md (skills architecture rules), ROADMAP.md (development priorities), and canvas-pilot-reference.md (Section 7: per-type skill deep pipeline analysis with cross-skill common patterns).

## 2026-06-03 — Establish M3.5+ design principles and Copilot 11-stage gap analysis

Deep-dived into the Canvas Copilot reference project at `/Users/deepwisdom/Desktop/project/canvas_copilot/`. Previous sessions only read the distilled notes in `docs/canvas-pilot-reference.md`; this session read the actual Copilot codebase including `canvas-generic` SKILL.md (11 stages, 3 sub-agents, verification retry loop), framework skills (scan/execute/skip/bootstrap/setup), per-course generic skills, hooks system, and 2026-06-01 real run records.

Key findings: Copilot's `canvas-generic` has 11 stages (0-11), not just the 5 that AutoStudy has been referencing. Stages 6-10 (pipeline design, generate, verification checklist, verify+retry, verification review) are missing from AutoStudy. The 3 sub-agents (A: investigation review, B: verification checklist design, C: verification coverage review) are also not yet implemented.

User clarified five design principles for M3.5+ development:
1. **Assistant, not automation** — borrow Copilot's mechanisms but keep user-in-loop
2. **Dynamic skills composition** — no fixed pipelines, leverage Claude Code's agent ability to compose skills on-the-fly for complex tasks
3. **Multi-turn iteration** — complex tasks won't be done well in one session; design for in-session interrupt/resume AND cross-session iterative refinement; `result.json` should support `revision_needed`
4. **Three-layer preference system** — task-level (`[B]` collection) → course-level (overlay) → user-level (Claude Code memory)
5. **Review-first design** — composable sub-agent review points per pipeline stage, not limited to Copilot's fixed 3

Documents updated: ROADMAP.md (added "设计理念" section under M3.5), COLLABORATION.md (added Design Principles section), AGENTS.md (added principle summary), canvas-pilot-reference.md (added Section 6: full 11-stage comparison table and architecture diff table).

## 2026-06-02 — Adopt agent-led Canvas Generic homework flow

User approved replacing the script-led reconnaissance direction with Canvas Copilot `canvas-generic` style agent-led Stage 1-5: fetch context, find rubric, locate inputs, review investigation, and classify output mode. Docs now define `spec.md` as the standardized reconnaissance report, `problem.md` as compatibility only, and `pipeline_design.md` as the do-homework -> task-orchestrator execution contract; `scripts/recon_assignment.py` is historical transition evidence, not the production path.

Validated the new agent-led flow on two real Canvas cases. DSAA2011 Project inspected assignment/rubric/front-page/syllabus/all 4 modules and 69 items, found the main spec in module 12955 file 625115, downloaded the project-module PDFs, wrote `spec.md`, `rubric.md`, `review_a.json`, and a mixed `pipeline_design.md`; orchestrator dry-run stopped correctly on group/dataset/style-file blockers. UCUG1505 FINAL project inspected assignment/rubric/front-page/syllabus/all 14 modules and 64 items, confirmed the assignment page and Week 4 module point to the same Google Doc, fetched the spec plus documentation template, wrote the same workbench files, and dry-run stopped correctly on partner/concept/code/video blockers.

Because no sub-agent reviewer tool is available in this runtime, Stage 4 used cold self-review and recorded `review_method: cold_read_self_review_no_sub_agent_available` in both local `review_a.json` files. `M3.5-WORKDIR-STRUCTURE`, `M3.5-DEEP-RECON`, and `M3.5-PIPELINE-DESIGN` are now marked `passing`; the generated `data/homework/...` workbenches remain gitignored local evidence, with durable evidence recorded in `docs/plans/feature-list.json`. Next: improve the do-homework user supplement UX and turn these dry-run blockers into a smooth execution/revision loop.

## 2026-06-02 — Stable plan-item handoff for do-homework

Added `scripts/select_plan_item.py` so a user choice like "do plan item 1" is resolved from `data/runs/<today>/plan.json` plus `pending_assignments.json` into a stable handoff object for `do-homework`: `course_id`, `assignment_id`, `assignment_name`, `recommended_action`, `existing_result_path`, and `suggested_work_dir`. Updated `sync-status.md`, `do-homework.md`, and `docs/canvas-pilot-reference.md` to use this selector instead of asking the agent to re-match assignment titles after the user has picked a numbered item.

Verification used `/tmp/autoust-select-plan-fixture-2` to cover `recon`, `review_or_submit`, `manual_review`, `continue/error`, and invalid-index behavior; `py_compile` passed for the selector and the existing M3.5 scripts. The selector also ran against cached real live-scan plans under `/tmp/autoust-flow-real/runs` and `/tmp/autoust-flow-real/runs-after-skip`, resolving UCUG1600 plan items before and after a skipped-result filtered the first assignment out. A full DSAA2011 Machine Learning Project simulation under `/tmp/autoust-ml-flow` built a one-item plan, selected `2973:21641`, ran real reconnaissance to `review_a.verdict=proceed`, wrote `status=skipped`, and confirmed the rerun plan filtered the item as `result_skipped`.

## 2026-06-02 — Assistant-style scan-plan implementation started

Started M3.5-SCAN-PLAN after reviewing Canvas Copilot's `canvas-scan` and run-state schema again: AutoStudy borrows the scan/execute boundary but keeps `sync-status` as a recommendation step, not a batch executor. Added `scripts/write_scan_plan.py` to combine local canvascli snapshots with `data/homework/**/result.json` and write `data/runs/<today>/pending_assignments.json`, `plan.json`, and `REPORT.md`; `sync-status.md` now points to this writer and explicitly stops before do-homework unless the user chooses one item.

Verification wrote plans under `/tmp/autoust-scan-plan-current3`, `/tmp/autoust-scan-plan-with-results3`, and `/tmp/autoust-scan-plan-default-terminal3`. Current real Canvas snapshot produced raw snapshot copies plus 3 actionable items after filtering 44 graded, 6 submitted, and 4 ancient-overdue assignments; DSAA2011/UCUG1505 fixture checks confirmed `draft_ready -> review_or_submit`, `skipped -> filtered`, and Canvas `graded` wins over stale local draft state in default mode. Checks passed: `py_compile` for all scripts, `json.tool` for feature-list and generated plan files, and the DSAA/UCUG fixture assertions. Next: final review with the user before committing.

Post-commit real flow verification refreshed Canvas login through the working 127.0.0.1:7890 proxy after `whoami` reported an expired session. A live scan under `/tmp/autoust-flow-real` fetched 7 courses, 57 assignments, and 5 announcements, then selected plan item 1 (`UCUG1600 Final Report`, 2798:23536), ran `scripts/recon_assignment.py` to `review_a.verdict: proceed`, wrote `result.json status=skipped`, and reran scan-plan to confirm assignment 23536 disappeared from the plan (`before ['23536', '23537', '20629']`, `after ['23537', '20629']`).

## 2026-06-02 — Result writer + assistant-shaped Copilot adaptation rule

Recorded the collaboration rule that Canvas Copilot is a mature reference but not a blueprint to clone: AutoStudy should borrow mechanisms such as atomic data access, deep reconnaissance, workbenches, verification logs, and state files while redesigning the interaction around an assistant-style user loop. Added `scripts/write_homework_result.py` as the stable writer for single-assignment `result.json`; `do-homework.md` now calls it for `skipped`, `draft_ready`, `submitted`, and `error` paths, while `recon_assignment.py` remains reconnaissance-only.

Verification used existing real recon workbenches copied to `/tmp/autoust-result-verify/`: DSAA2011 Project produced a `draft_ready` result with a fake notebook fixture, `verification_log_path`, two `human_review_items`, and `review_a_verdict: proceed`; UCUG1505 FINAL project produced a `skipped` result with notes and `review_a_verdict: proceed`. Checks passed: `python3 -m py_compile scripts/recon_assignment.py scripts/write_homework_result.py`, `python3 -m json.tool docs/plans/feature-list.json`, `python3 -m json.tool` on both smoke `result.json` files, and `git diff --check`. Committed as `c4ae2a4 feat: add homework result state writer`. Next: build assistant-style `pending_assignments.json` / `plan.json` support for `sync-status`.

## 2026-06-02 — Stable recon runtime + post-recon user supplement gate

Turned the Copilot-style reconnaissance template into a stable runtime script at `scripts/recon_assignment.py`. `problem-extractor.md` now invokes that script instead of asking the agent to copy a markdown template, and `do-homework.md [B]` now explicitly performs a mandatory reconnaissance summary + user supplement checkpoint even when `review_a.json.verdict == "proceed"`; user supplements are written to `investigation/user_notes.md` and carried into `task_profile.yaml.user_overrides`.

Real Canvas verification used `/tmp/autoust-recon-script-verify/`: DSAA2011 Project produced `spec.md` 66,322 B / `problem.md` 155,415 B, inspected 4 modules and 69 module items, confirmed assignment description 0 B, downloaded `DSAA2011-26sp-project_announce-L01.pdf` plus nearby module PDFs, and `review_a` returned `proceed`. UCUG1505 FINAL project produced `spec.md` 22,527 B / `problem.md` 14,274 B, inspected 14 modules and 64 module items, recorded the Final project Google Doc plus Week 9 slides, skipped front-page GIF media as inspected-not-downloaded, and `review_a` returned `proceed`. A canvascli retry bug surfaced during `whoami` (`requests.SSLError` should be `requests.exceptions.SSLError`) and was fixed in the canvascli repo.

## 2026-06-02 — Final-review cleanup for M3.5 recon evidence

Cleaned up review risks in the M3.5 workbench docs: canvascli README now shows the required `assignment <aid> -c <cid>` form, the Canvas Pilot reference tail no longer describes the old modules-only/problem.md-only direction, and the tool registry/backlog now use the `spec.md` + atomic-context wording. Rechecked `/tmp/autoust-recon-verify/dsaa2011`: `spec.md` is 45,709 B, `problem.md` is 107,322 B, assignment description is empty, front page is 404/not enabled, modules count is 4, module 12955 contains the project PDF, 3 references downloaded, and file 688370 metadata failed; `review_a.json` lists that file under `blocking_unreachables` while the recon verdict still remained `proceed`.

## 2026-06-01 — Adopt Canvas Copilot workbench direction for deep assignment reconnaissance

Reviewed Canvas Copilot's real DSAA2011 Project run at `/Users/deepwisdom/Desktop/project/canvas_copilot/runs/2026-06-01/DSAA2011_L01_-_Machine_Learning__Project`. The user approved copying its single-assignment workbench shape: `spec.md`, `references/`, `investigation/`, `pipeline_design.md`, `draft/`, `verification_checklist.md`, `verification.log`, and `result.json`. AutoStudy will migrate from the current flat `data/homework/<COURSE>/<HWID>/` layout toward a compatible structure with `canvas/` raw CLI snapshots, `spec.md` as the main reconnaissance artifact, and `problem.md` kept temporarily for existing tools.

The data-layer direction is now explicitly Copilot-style atomic commands, not `assignment-context`: `assignment`, `rubric`, `front-page`, `syllabus`, `modules`, `module-items`, `page`, `file`, and `assignment-files`. DSAA2011 Project and UCUG1505 FINAL project are the two required real verification cases for the upcoming AutoStudy integration. Backlog now has M3.5 items for atomic context, workdir structure, deep recon, and result.json.

Implemented the AutoStudy documentation side of that migration: `canvascli-api.md`, `problem-extractor.md`, `do-homework.md`, `task-orchestrator.md`, `_index.md`, `skill.md`, and `PITFALLS.md` now describe the spec-first workbench. Verification used the script template copied from `problem-extractor.md` into `/tmp/autoust-recon-verify/extract_problem.py` and ran real Canvas cases: DSAA2011 Project produced a 45,709 B `spec.md`, inspected module 12955, and downloaded the project announcement PDF; UCUG1505 FINAL project produced a 19,771 B `spec.md`, found the Google Doc spec in both assignment description and Week 4 module item, and listed Week 9 slides as project context. One design correction from verification: inspect every module item, but only download likely assignment-context files instead of every course file.

## 2026-06-01 — Clarified Canvas login/session mental model

Validated that `canvascli init` is a login/refresh command, not a session health check: it always opens Chromium and writes a new `state.json` after successful SSO. The correct health check is `.venv/bin/canvascli whoami`, which returned the Canvas user from the current saved session without requiring browser login. Docs now distinguish `state.json` (canvascli's saved Canvas API cookie) from the SSO "remember login" checkbox (controls how smooth the next SSO refresh is), and explicitly tell agents not to run `init` just to test status.

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
