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
└── scripts/
    └── extract_problem.py
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

The agent writes `<work_dir>/scripts/extract_problem.py` from the template below and runs it:

```bash
mkdir -p "<work_dir>/scripts"
.venv/bin/python "<work_dir>/scripts/extract_problem.py" "<work_dir>" "<course_id>" "<assignment_id>"
```

Template:

```python
"""Copilot-style Canvas assignment reconnaissance for AutoStudy."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from html import unescape
from pathlib import Path

WORK_DIR = Path(sys.argv[1])
COURSE_ID = sys.argv[2]
ASSIGNMENT_ID = sys.argv[3]
CANVASCLI = ".venv/bin/canvascli"

CANVAS_DIR = WORK_DIR / "canvas"
REFERENCES_DIR = WORK_DIR / "references"
INVESTIGATION_DIR = WORK_DIR / "investigation"
for path in (CANVAS_DIR, REFERENCES_DIR, INVESTIGATION_DIR):
    path.mkdir(parents=True, exist_ok=True)


def safe_name(value: str, fallback: str = "item") -> str:
    value = re.sub(r"[/\\:*?\"<>|]", "_", (value or "").strip())
    value = re.sub(r"\s+", "_", value)
    return value[:140] or fallback


def run_json(args: list[str], out_path: Path) -> object:
    if out_path.exists() and out_path.stat().st_size > 0:
        return json.loads(out_path.read_text())
    out = subprocess.check_output([CANVASCLI, *args], stderr=subprocess.PIPE)
    out_path.write_bytes(out)
    return json.loads(out)


def html_to_text(html: str | None) -> str:
    if not html:
        return ""
    text = re.sub(r"(?i)<br\s*/?>", "\n", html)
    text = re.sub(r"(?i)</(p|div|li|h[1-6]|tr)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def file_ids_from_text(text: str | None) -> set[int]:
    ids: set[int] = set()
    for raw in re.findall(r"/(?:courses/\d+/)?files/(\d+)", text or ""):
        try:
            ids.add(int(raw))
        except ValueError:
            pass
    return ids


def urls_from_text(text: str | None) -> set[str]:
    pattern = r'https?://[^\s"\'<>)] +'.replace(" ", "")
    return {unescape(u.rstrip(".,;")) for u in re.findall(pattern, text or "")}


def extract_text(path: Path) -> str:
    try:
        head = path.read_bytes()[:4]
    except Exception:
        head = b""
    if path.suffix.lower() == ".pdf" or head == b"%PDF":
        if shutil.which("pdftotext"):
            return subprocess.check_output(["pdftotext", "-layout", str(path), "-"]).decode("utf-8", errors="replace")
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
        except ImportError:
            return ""
        return pdfminer_extract(str(path))
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""


assignment = run_json(["assignment", ASSIGNMENT_ID, "-c", COURSE_ID], CANVAS_DIR / "assignment.json")
rubric = run_json(["rubric", ASSIGNMENT_ID, "-c", COURSE_ID], CANVAS_DIR / "rubric.json")
front_page = run_json(["front-page", "-c", COURSE_ID], CANVAS_DIR / "front-page.json")
syllabus = run_json(["syllabus", "-c", COURSE_ID], CANVAS_DIR / "syllabus.json")
modules = run_json(["modules", "-c", COURSE_ID], CANVAS_DIR / "modules.json")
assignment_files = run_json(["assignment-files", ASSIGNMENT_ID, "-c", COURSE_ID], CANVAS_DIR / "assignment-files.json")

module_items: list[dict] = []
for module in (modules.get("modules") or []) if isinstance(modules, dict) else []:
    mid = module.get("id")
    if not mid:
        continue
    data = run_json(["module-items", str(mid), "-c", COURSE_ID], CANVAS_DIR / f"module-items-{mid}.json")
    for item in data.get("items") or []:
        item["_module_name"] = (data.get("module") or {}).get("name") or module.get("name")
        module_items.append(item)

def item_candidate_reason(item: dict, assignment_name: str | None) -> str | None:
    """Return why a module item is likely assignment context, or None.

    We inspect every module item but only download/fetch bodies for likely
    assignment context. This keeps the flow Copilot-like without pulling an
    entire course file archive.
    """
    text = " ".join(str(item.get(k) or "") for k in ("title", "type", "external_url", "html_url", "_module_name")).lower()
    assignment_words = [
        w.lower()
        for w in re.findall(r"[A-Za-z0-9]+", assignment_name or "")
        if len(w) >= 3 and w.lower() not in {"the", "and", "for", "with", "assignment"}
    ]
    for word in assignment_words:
        if word in text:
            return f"assignment word: {word}"
    source_words = (
        "spec", "specification", "guideline", "guidelines", "requirement",
        "requirements", "announce", "announcement", "project", "final",
        "report", "presentation", "rubric", "criteria",
    )
    for word in source_words:
        if word in text:
            return f"source word: {word}"
    return None


pages: list[dict] = []
for item in module_items:
    page_url = item.get("page_url")
    if item.get("type") == "Page" and page_url and item_candidate_reason(item, assignment.get("name") if isinstance(assignment, dict) else ""):
        page = run_json(["page", str(page_url), "-c", COURSE_ID], CANVAS_DIR / f"page-{safe_name(str(page_url))}.json")
        pages.append(page)

file_ids: set[int] = set()
for blob in (assignment, front_page, syllabus, *pages):
    if isinstance(blob, dict):
        for key in ("description", "description_html", "body_html", "body_text"):
            file_ids.update(file_ids_from_text(str(blob.get(key) or "")))
        for fid in blob.get("file_ids") or []:
            try:
                file_ids.add(int(fid))
            except (TypeError, ValueError):
                pass

for item in module_items:
    if item.get("type") == "File" and item.get("content_id") and item_candidate_reason(item, assignment.get("name") if isinstance(assignment, dict) else ""):
        try:
            file_ids.add(int(item["content_id"]))
        except (TypeError, ValueError):
            pass

for f in (assignment_files.get("files") or []) if isinstance(assignment_files, dict) else []:
    try:
        file_ids.add(int(f.get("id")))
    except (TypeError, ValueError):
        pass

file_meta: dict[int, dict] = {}
for fid in sorted(file_ids):
    try:
        meta = run_json(["file", str(fid)], CANVAS_DIR / f"file-{fid}.json")
    except subprocess.CalledProcessError:
        meta = {"id": fid, "error": "file_metadata_failed"}
        (CANVAS_DIR / f"file-{fid}.json").write_text(json.dumps(meta))
    if isinstance(meta, dict):
        file_meta[fid] = meta

downloaded: list[tuple[dict, Path, str]] = []
unreachable: list[str] = []
for fid, meta in sorted(file_meta.items()):
    if meta.get("error"):
        unreachable.append(f"file {fid}: metadata error {meta.get('error')}")
        continue
    name = meta.get("display_name") or meta.get("filename") or f"file_{fid}"
    local = REFERENCES_DIR / safe_name(name, f"file_{fid}")
    if not local.exists():
        try:
            subprocess.check_call([CANVASCLI, "download", str(fid), "-o", str(local)])
        except subprocess.CalledProcessError:
            unreachable.append(f"file {fid} ({name}): download failed")
            continue
    text = extract_text(local).strip()
    if text:
        local.with_suffix(local.suffix + ".txt").write_text(text)
    downloaded.append((meta, local, text))

external_urls: set[str] = set()
for blob in (assignment, front_page, syllabus, *pages):
    if not isinstance(blob, dict):
        continue
    for item in blob.get("external_urls") or []:
        if isinstance(item, dict) and item.get("url"):
            external_urls.add(str(item["url"]))
    for key in ("description", "description_html", "description_text", "body_html", "body_text"):
        external_urls.update(urls_from_text(str(blob.get(key) or "")))
for item in module_items:
    if item.get("external_url"):
        external_urls.add(str(item["external_url"]))

assignment_name = assignment.get("name") if isinstance(assignment, dict) else ""
points = assignment.get("points_possible") if isinstance(assignment, dict) else ""
due_at = assignment.get("due_at") if isinstance(assignment, dict) else ""
submission_types = assignment.get("submission_types") if isinstance(assignment, dict) else []

rubric_lines: list[str] = []
if isinstance(rubric, dict) and rubric.get("rubric_present") and rubric.get("rubric"):
    for item in rubric.get("rubric") or []:
        rubric_lines.append(f"- {item.get('description', '')} ({item.get('points', '?')} pts)")
else:
    rubric_lines.append("RUBRIC NOT FOUND - use assignment/module/syllabus criteria if present")

(INVESTIGATION_DIR / "rubric.md").write_text("# Rubric\n\n" + "\n".join(rubric_lines) + "\n")
(INVESTIGATION_DIR / "unreachable.txt").write_text("\n".join(unreachable) if unreachable else "No unreachable resources.\n")

source_notes: list[str] = []
desc_text = assignment.get("description_text") or html_to_text(assignment.get("description") or "") if isinstance(assignment, dict) else ""
source_notes.append(f"- Assignment description text bytes: {len(desc_text.encode('utf-8'))}")
source_notes.append(f"- Canvas rubric present: {bool(isinstance(rubric, dict) and rubric.get('rubric_present'))}")
source_notes.append(f"- Front page status: {front_page.get('status') if isinstance(front_page, dict) else 'unknown'}")
source_notes.append(f"- Syllabus text bytes: {syllabus.get('body_text_bytes') if isinstance(syllabus, dict) else 0}")
source_notes.append(f"- Modules inspected: {len(modules.get('modules') or []) if isinstance(modules, dict) else 0}")
source_notes.append(f"- Module items inspected: {len(module_items)}")
source_notes.append(f"- Files downloaded: {len(downloaded)}")
source_notes.append(f"- External URLs found: {len(external_urls)}")

module_hit_lines: list[str] = []
needle_words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", assignment_name or "") if len(w) >= 3]
for item in module_items:
    title = item.get("title") or ""
    hay = " ".join(str(item.get(k) or "") for k in ("title", "type", "external_url", "html_url", "_module_name")).lower()
    hit = any(w in hay for w in needle_words)
    reason = item_candidate_reason(item, assignment_name)
    if hit or reason or item.get("type") in ("Page", "ExternalUrl"):
        module_hit_lines.append(
            f"- module={item.get('_module_name') or item.get('module_id')} | "
            f"type={item.get('type')} | title={title} | reason={reason or 'listed context'} | "
            f"content_id={item.get('content_id') or ''} | page_url={item.get('page_url') or ''} | "
            f"external_url={item.get('external_url') or ''}"
        )

reference_lines: list[str] = []
for meta, local, text in downloaded:
    reference_lines.append(
        f"- `{local.name}` — file_id={meta.get('id')}, "
        f"name={meta.get('display_name') or meta.get('filename')}, text_bytes={len(text.encode('utf-8'))}"
    )

spec_parts = [
    f"# {assignment_name or 'Assignment'}",
    "",
    "## Assignment metadata",
    f"- Course ID: {COURSE_ID}",
    f"- Assignment ID: {ASSIGNMENT_ID}",
    f"- Points: {points}",
    f"- Due: {due_at}",
    f"- Submission types: {submission_types}",
    "",
    "## Recon summary",
    *source_notes,
    "",
    "## Assignment description",
    desc_text or "_(empty)_",
    "",
    "## Front page",
    (front_page.get("body_text") or "_(empty or unavailable)_") if isinstance(front_page, dict) else "_(unavailable)_",
    "",
    "## Syllabus",
    (syllabus.get("body_text") or "_(empty)_") if isinstance(syllabus, dict) else "_(unavailable)_",
    "",
    "## Module hits and source candidates",
    "\n".join(module_hit_lines) if module_hit_lines else "_(no relevant module items found)_",
    "",
    "## Canvas pages fetched",
]
for page in pages:
    spec_parts += [
        f"### {page.get('title') or page.get('page_url')}",
        page.get("body_text") or "_(empty)_",
        "",
    ]
spec_parts += [
    "## References downloaded",
    "\n".join(reference_lines) if reference_lines else "_(none)_",
    "",
]
for meta, local, text in downloaded:
    if text:
        spec_parts += [f"### Reference text: {local.name}", text[:20000], ""]
spec_parts += [
    "## External URLs",
    "\n".join(f"- {url}" for url in sorted(external_urls)) if external_urls else "_(none)_",
    "",
    "## Rubric",
    "\n".join(rubric_lines),
    "",
    "## Unreachable resources",
    "\n".join(unreachable) if unreachable else "No unreachable resources.",
    "",
]

(WORK_DIR / "spec.md").write_text("\n".join(spec_parts))

problem_parts = [
    "---",
    f"assignment_name: {assignment_name or ''}",
    f"assignment_id: {ASSIGNMENT_ID}",
    f"course_id: {COURSE_ID}",
    f"due_at: {due_at or ''}",
    f"points_possible: {points or ''}",
    f"submission_types: {submission_types}",
    "source: spec.md",
    "---",
    "",
    f"# {assignment_name or 'Assignment'}",
    "",
    "This compatibility file is generated from `spec.md`. Downstream tools should treat the sections below as the grounded problem text.",
    "",
    "## Inline description",
    desc_text or "_(empty)_",
    "",
    "## Source candidates",
    "\n".join(module_hit_lines) if module_hit_lines else "_(none)_",
    "",
]
for meta, local, text in downloaded:
    problem_parts += [
        f"## Attached: {local.name}",
        "",
        text if text else "_(extraction failed or unsupported format)_",
        "",
    ]
problem_parts += ["## Rubric", "", "\n".join(rubric_lines), ""]
(WORK_DIR / "problem.md").write_text("\n".join(problem_parts))

review = {
    "deliverable_clear": bool(desc_text or downloaded or external_urls or module_hit_lines),
    "rubric_found": bool(isinstance(rubric, dict) and rubric.get("rubric_present")),
    "inputs_complete": not bool(unreachable),
    "missing_sources": [],
    "unreachable_resources": unreachable,
    "blocking_unreachables": [],
    "verdict": "proceed" if (desc_text or downloaded or external_urls or module_hit_lines) else "recover",
}
(INVESTIGATION_DIR / "review_a.json").write_text(json.dumps(review, indent=2, ensure_ascii=False))

print(f"Wrote {WORK_DIR / 'spec.md'} ({(WORK_DIR / 'spec.md').stat().st_size} bytes)")
print(f"Wrote {WORK_DIR / 'problem.md'} ({(WORK_DIR / 'problem.md').stat().st_size} bytes)")
print(f"Downloaded references: {len(downloaded)}")
print(f"External URLs: {len(external_urls)}")
print(f"Verdict: {review['verdict']}")

if review["verdict"] != "proceed":
    sys.exit(2)
```

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
