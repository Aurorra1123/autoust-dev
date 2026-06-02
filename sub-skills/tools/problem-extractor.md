---
name: problem-extractor
description: Copilot-style assignment reconnaissance. Reads Canvas sources one by one through canvascli, writes spec.md plus a compatibility problem.md, downloads reachable references, and records gaps before any homework generation starts.
---

# problem-extractor

The data-grounding tool. It follows Canvas Copilot's mature pattern: **do not trust one Canvas field**. Before producing any draft / code / slides, the agent must inspect all likely sources and build a single assignment workbench.

Real failure mode this prevents:

- DSAA2011 Project: assignment description is empty, Canvas rubric is absent, front page is disabled, but the project PDF lives in a module item. An attachment-only extractor would think the assignment has no prompt.
- UCUG1505 FINAL project: assignment description links a Google Doc spec, Week 4 module item links the same spec, and Week 9 slides are nearby context. The right answer is to inspect both sources, then decide the Google Doc is the main spec and slides are supporting material.

## Capability

- `extract_problem` — `(course_id, assignment_id, work_dir)` -> Copilot-style workbench with `spec.md`, `problem.md`, `references/`, and `investigation/`

## Workbench Contract

The tool writes this structure under `<work_dir>`:

```text
<work_dir>/
├── canvas/
│   ├── assignment.json
│   ├── rubric.json
│   ├── front-page.json
│   ├── syllabus.json
│   ├── modules.json
│   ├── module-items-<mid>.json
│   ├── page-<page_url>.json
│   └── file-<file_id>.json
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   └── review_a.json
```

`canvas/` stores raw JSON snapshots from atomic `canvascli` commands. `spec.md` is the main reconnaissance artifact. `problem.md` is a compatibility file for existing tools (`writing-helper`, `code-writer`, `slide-maker`) that still expect that filename. `references/` stores downloaded files and extracted `.txt` text. `investigation/` records rubric findings, unreachable resources, and the Stage-A completeness review.

## Inputs / Outputs

```text
Input:  course_id
        assignment_id
        <work_dir>/

Output: <work_dir>/canvas/*.json
        <work_dir>/spec.md
        <work_dir>/problem.md
        <work_dir>/references/*
        <work_dir>/investigation/rubric.md
        <work_dir>/investigation/unreachable.txt
        <work_dir>/investigation/review_a.json
```

Downstream tools should read `problem.md` for now. New code should prefer `spec.md` because it contains source-by-source context, not only attachment text.

## Canvas Sources To Inspect

Run these commands from the AutoStudy repo, using the venv binary:

```bash
.venv/bin/canvascli assignment <assignment_id> -c <course_id> > "<work_dir>/canvas/assignment.json"
.venv/bin/canvascli rubric <assignment_id> -c <course_id> > "<work_dir>/canvas/rubric.json"
.venv/bin/canvascli front-page -c <course_id> > "<work_dir>/canvas/front-page.json"
.venv/bin/canvascli syllabus -c <course_id> > "<work_dir>/canvas/syllabus.json"
.venv/bin/canvascli modules -c <course_id> > "<work_dir>/canvas/modules.json"
.venv/bin/canvascli assignment-files <assignment_id> -c <course_id> > "<work_dir>/canvas/assignment-files.json"
```

Then read `modules.json` and run this for **every module**, not just the first apparent match:

```bash
.venv/bin/canvascli module-items <module_id> -c <course_id> > "<work_dir>/canvas/module-items-<module_id>.json"
```

For module items with `type == "Page"` and a `page_url`, fetch the page:

```bash
.venv/bin/canvascli page <page_url> -c <course_id> > "<work_dir>/canvas/page-<safe_page_url>.json"
```

For every file id found in assignment description, front page, syllabus, pages, module item `content_id`, or `assignment-files.json`, fetch metadata:

```bash
.venv/bin/canvascli file <file_id> > "<work_dir>/canvas/file-<file_id>.json"
```

Only after inspecting all likely sources should the agent decide which source is the main spec. Do not stop early because one exact title match was found; Canvas Copilot's mature flow reads all angles first, then judges.

## Invocation

Run the stable repository script from the AutoStudy repo root. Do not copy a
throwaway script from this markdown file; the runtime logic lives in
`scripts/recon_assignment.py` so repeated reconnaissance does not burn agent
attention or drift between sessions.

```bash
.venv/bin/python scripts/recon_assignment.py \
  --course-id "<course_id>" \
  --assignment-id "<assignment_id>" \
  --work-dir "<work_dir>"
```

Use `--refresh` only when you intentionally want to discard cached Canvas JSON
snapshots and re-query Canvas. The script exits `0` when `review_a.json.verdict`
is `proceed`, and `2` when reconnaissance could not identify enough grounded
context.

The script writes only reconnaissance artifacts. It does **not** write
`result.json`; that file belongs to `do-homework` after the user has reviewed
the reconnaissance summary and the workflow has either stopped, produced a
draft, failed, or submitted.

## Quality Bar

After this tool runs:

1. `spec.md` must include source-by-source evidence, not only a title-level summary.
2. `canvas/` must contain JSON snapshots for assignment, rubric, front page, syllabus, modules, every inspected module's items, and relevant files/pages.
3. `references/` must contain every reachable Canvas file that is plausibly part of the assignment context.
4. `investigation/unreachable.txt` must list third-party links, login walls, failed downloads, or password-protected resources.
5. `problem.md` must be non-trivial unless `review_a.json.verdict` is `recover` or `stop`.

The agent reads `spec.md` and `investigation/review_a.json` before `do-homework [B]`. If the main spec is still unclear, surface the gap at [B] instead of proceeding silently.

## Source Selection Philosophy

This tool should inspect broadly and decide late:

- Do not directly pick an exact title match and stop.
- Do not assume assignment description is authoritative.
- Do not assume modules are irrelevant when assignment description has a link.
- Do not hide nearby context such as slides, sample exams, or course pages; include it and label it as context.
- Do not put Canvas endpoint details in AutoStudy task logic. The contract is the `canvascli` commands and JSON files.

## Cross-references

- Called from: `tasks/do-homework.md` step `[A]`
- Consumed by: `tools/writing-helper.md`, `tools/code-writer.md`, `tools/slide-maker.md`, and future `task-orchestrator.md` dynamic planning
- Depends on: `tools/canvascli-api.md` atomic context commands, `canvascli download`, `pdftotext` or `pdfminer.six`

## Pitfalls

1. **Assignment description can be empty.** DSAA2011 Project is the real example; the spec was in a module file.
2. **A valid source can appear twice.** UCUG1505 FINAL project links the same Google Doc from assignment description and Week 4 module item. Treat duplicates as corroboration, not noise.
3. **Front page 404 is normal.** Some courses disable it. Record the status and keep going.
4. **Rubric can be absent from Canvas.** Search the spec and downloaded references for grading criteria before declaring it missing.
5. **Do not over-download every course file.** Download files discovered from assignment/module/page/syllabus/front-page context, not arbitrary folder trees.
6. **External Google Docs may need manual access.** Record the URL in `spec.md` and `unreachable.txt` if anonymous fetch is blocked; ask the user at [B] only if it blocks understanding the assignment.
7. **Keep `problem.md` during migration.** Existing tools still use it. Once writing/code/slides tools move to `spec.md`, this compatibility layer can shrink.
