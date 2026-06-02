"""Copilot-style Canvas assignment reconnaissance for AutoStudy.

This script is the stable runtime version of the problem-extractor flow.
It reads Canvas sources through atomic canvascli commands, writes a
source-by-source workbench, and stops before any homework generation.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from html import unescape
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", required=True)
    parser.add_argument("--assignment-id", required=True)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument(
        "--canvascli",
        default=".venv/bin/canvascli",
        help="Path to the canvascli executable, relative to the current directory.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refetch Canvas JSON snapshots even when cached files already exist.",
    )
    return parser.parse_args()


def safe_name(value: str, fallback: str = "item") -> str:
    value = re.sub(r"[/\\:*?\"<>|]", "_", (value or "").strip())
    value = re.sub(r"\s+", "_", value)
    return value[:140] or fallback


def run_json(canvascli: str, args: list[str], out_path: Path, *, refresh: bool) -> Any:
    if out_path.exists() and out_path.stat().st_size > 0 and not refresh:
        return json.loads(out_path.read_text())
    try:
        out = subprocess.check_output([canvascli, *args], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"canvascli {' '.join(args)} failed: {err}") from exc
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
            return subprocess.check_output(["pdftotext", "-layout", str(path), "-"]).decode(
                "utf-8", errors="replace"
            )
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
        except ImportError:
            return ""
        return pdfminer_extract(str(path))
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""


def should_download_file(meta: dict[str, Any]) -> tuple[bool, str]:
    content_type = str(meta.get("content_type") or "").lower()
    name = str(meta.get("display_name") or meta.get("filename") or "").lower()
    suffix = Path(name).suffix.lower()
    if content_type.startswith(("image/", "video/", "audio/")):
        return False, f"skipped media content_type={content_type}"
    text_like_suffixes = {
        ".pdf",
        ".txt",
        ".md",
        ".csv",
        ".tsv",
        ".json",
        ".yaml",
        ".yml",
        ".py",
        ".ipynb",
        ".r",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".html",
        ".htm",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".zip",
    }
    if suffix in text_like_suffixes:
        return True, "downloadable context file"
    if content_type in {
        "application/pdf",
        "application/json",
        "text/plain",
        "text/markdown",
        "text/html",
        "text/csv",
    }:
        return True, "downloadable context content_type"
    return False, f"skipped unsupported content_type={content_type or 'unknown'}"


def item_candidate_reason(item: dict[str, Any], assignment_name: str | None) -> str | None:
    """Return why a module item is likely assignment context, or None."""
    text = " ".join(
        str(item.get(k) or "")
        for k in ("title", "type", "external_url", "html_url", "_module_name")
    ).lower()
    assignment_words = [
        w.lower()
        for w in re.findall(r"[A-Za-z0-9]+", assignment_name or "")
        if len(w) >= 3 and w.lower() not in {"the", "and", "for", "with", "assignment"}
    ]
    for word in assignment_words:
        if word in text:
            return f"assignment word: {word}"
    source_words = (
        "spec",
        "specification",
        "guideline",
        "guidelines",
        "requirement",
        "requirements",
        "announce",
        "announcement",
        "project",
        "final",
        "report",
        "presentation",
        "rubric",
        "criteria",
    )
    for word in source_words:
        if word in text:
            return f"source word: {word}"
    return None


def dict_get_text(blob: Any, key: str) -> str:
    if not isinstance(blob, dict):
        return ""
    value = blob.get(key)
    return str(value or "")


def main() -> int:
    ns = parse_args()
    work_dir = ns.work_dir
    canvas_dir = work_dir / "canvas"
    references_dir = work_dir / "references"
    investigation_dir = work_dir / "investigation"
    for path in (canvas_dir, references_dir, investigation_dir):
        path.mkdir(parents=True, exist_ok=True)

    assignment = run_json(
        ns.canvascli,
        ["assignment", ns.assignment_id, "-c", ns.course_id],
        canvas_dir / "assignment.json",
        refresh=ns.refresh,
    )
    rubric = run_json(
        ns.canvascli,
        ["rubric", ns.assignment_id, "-c", ns.course_id],
        canvas_dir / "rubric.json",
        refresh=ns.refresh,
    )
    front_page = run_json(
        ns.canvascli,
        ["front-page", "-c", ns.course_id],
        canvas_dir / "front-page.json",
        refresh=ns.refresh,
    )
    syllabus = run_json(
        ns.canvascli,
        ["syllabus", "-c", ns.course_id],
        canvas_dir / "syllabus.json",
        refresh=ns.refresh,
    )
    modules = run_json(
        ns.canvascli,
        ["modules", "-c", ns.course_id],
        canvas_dir / "modules.json",
        refresh=ns.refresh,
    )
    assignment_files = run_json(
        ns.canvascli,
        ["assignment-files", ns.assignment_id, "-c", ns.course_id],
        canvas_dir / "assignment-files.json",
        refresh=ns.refresh,
    )

    module_items: list[dict[str, Any]] = []
    for module in (modules.get("modules") or []) if isinstance(modules, dict) else []:
        mid = module.get("id")
        if not mid:
            continue
        data = run_json(
            ns.canvascli,
            ["module-items", str(mid), "-c", ns.course_id],
            canvas_dir / f"module-items-{mid}.json",
            refresh=ns.refresh,
        )
        for item in data.get("items") or []:
            item["_module_name"] = (data.get("module") or {}).get("name") or module.get("name")
            module_items.append(item)

    assignment_name = dict_get_text(assignment, "name")
    pages: list[dict[str, Any]] = []
    for item in module_items:
        page_url = item.get("page_url")
        if (
            item.get("type") == "Page"
            and page_url
            and item_candidate_reason(item, assignment_name)
        ):
            page = run_json(
                ns.canvascli,
                ["page", str(page_url), "-c", ns.course_id],
                canvas_dir / f"page-{safe_name(str(page_url))}.json",
                refresh=ns.refresh,
            )
            pages.append(page)

    file_ids: set[int] = set()
    file_reasons: dict[int, set[str]] = {}

    def add_file_id(fid_raw: Any, reason: str) -> None:
        try:
            fid = int(fid_raw)
        except (TypeError, ValueError):
            return
        file_ids.add(fid)
        file_reasons.setdefault(fid, set()).add(reason)

    for label, blob in (
        ("assignment", assignment),
        ("front-page", front_page),
        ("syllabus", syllabus),
        *[(f"page:{page.get('page_url') or page.get('title')}", page) for page in pages],
    ):
        if isinstance(blob, dict):
            for key in ("description", "description_html", "body_html", "body_text"):
                for fid in file_ids_from_text(str(blob.get(key) or "")):
                    add_file_id(fid, f"{label}.{key}")
            for fid in blob.get("file_ids") or []:
                add_file_id(fid, f"{label}.file_ids")

    for item in module_items:
        if (
            item.get("type") == "File"
            and item.get("content_id")
            and item_candidate_reason(item, assignment_name)
        ):
            add_file_id(item["content_id"], f"module item: {item.get('title') or item.get('id')}")

    for f in (assignment_files.get("files") or []) if isinstance(assignment_files, dict) else []:
        add_file_id(f.get("id"), "assignment-files")

    file_meta: dict[int, dict[str, Any]] = {}
    for fid in sorted(file_ids):
        try:
            meta = run_json(
                ns.canvascli,
                ["file", str(fid)],
                canvas_dir / f"file-{fid}.json",
                refresh=ns.refresh,
            )
        except RuntimeError as exc:
            meta = {"id": fid, "error": "file_metadata_failed", "message": str(exc)}
            (canvas_dir / f"file-{fid}.json").write_text(json.dumps(meta, indent=2))
        if isinstance(meta, dict):
            file_meta[fid] = meta

    downloaded: list[tuple[dict[str, Any], Path, str]] = []
    unreachable: list[str] = []
    inspected_not_downloaded: list[str] = []
    for fid, meta in sorted(file_meta.items()):
        if meta.get("error"):
            unreachable.append(f"file {fid}: metadata error {meta.get('error')}")
            continue
        name = meta.get("display_name") or meta.get("filename") or f"file_{fid}"
        should_download, reason = should_download_file(meta)
        if not should_download:
            inspected_not_downloaded.append(
                f"file {fid} ({name}): {reason}; sources={sorted(file_reasons.get(fid, []))}"
            )
            continue
        local = references_dir / safe_name(name, f"file_{fid}")
        if not local.exists() or ns.refresh:
            try:
                subprocess.check_call([ns.canvascli, "download", str(fid), "-o", str(local)])
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

    points = dict_get_text(assignment, "points_possible")
    due_at = dict_get_text(assignment, "due_at")
    submission_types = assignment.get("submission_types") if isinstance(assignment, dict) else []

    rubric_lines: list[str] = []
    if isinstance(rubric, dict) and rubric.get("rubric_present") and rubric.get("rubric"):
        for item in rubric.get("rubric") or []:
            rubric_lines.append(f"- {item.get('description', '')} ({item.get('points', '?')} pts)")
    else:
        rubric_lines.append("RUBRIC NOT FOUND - use assignment/module/syllabus criteria if present")

    (investigation_dir / "rubric.md").write_text("# Rubric\n\n" + "\n".join(rubric_lines) + "\n")
    (investigation_dir / "unreachable.txt").write_text(
        "\n".join(unreachable) if unreachable else "No unreachable resources.\n"
    )

    desc_text = ""
    if isinstance(assignment, dict):
        desc_text = assignment.get("description_text") or html_to_text(assignment.get("description") or "")

    source_notes = [
        f"- Assignment description text bytes: {len(desc_text.encode('utf-8'))}",
        f"- Canvas rubric present: {bool(isinstance(rubric, dict) and rubric.get('rubric_present'))}",
        f"- Front page status: {front_page.get('status') if isinstance(front_page, dict) else 'unknown'}",
        f"- Syllabus text bytes: {syllabus.get('body_text_bytes') if isinstance(syllabus, dict) else 0}",
        f"- Modules inspected: {len(modules.get('modules') or []) if isinstance(modules, dict) else 0}",
        f"- Module items inspected: {len(module_items)}",
        f"- Files downloaded: {len(downloaded)}",
        f"- Files inspected but not downloaded: {len(inspected_not_downloaded)}",
        f"- External URLs found: {len(external_urls)}",
    ]

    module_hit_lines: list[str] = []
    needle_words = [
        w.lower()
        for w in re.findall(r"[A-Za-z0-9]+", assignment_name or "")
        if len(w) >= 3
    ]
    for item in module_items:
        title = item.get("title") or ""
        hay = " ".join(
            str(item.get(k) or "")
            for k in ("title", "type", "external_url", "html_url", "_module_name")
        ).lower()
        hit = any(w in hay for w in needle_words)
        reason = item_candidate_reason(item, assignment_name)
        if hit or reason or item.get("type") in ("Page", "ExternalUrl"):
            module_hit_lines.append(
                f"- module={item.get('_module_name') or item.get('module_id')} | "
                f"type={item.get('type')} | title={title} | reason={reason or 'listed context'} | "
                f"content_id={item.get('content_id') or ''} | page_url={item.get('page_url') or ''} | "
                f"external_url={item.get('external_url') or ''}"
            )

    reference_lines = [
        f"- `{local.name}` - file_id={meta.get('id')}, "
        f"name={meta.get('display_name') or meta.get('filename')}, "
        f"text_bytes={len(text.encode('utf-8'))}"
        for meta, local, text in downloaded
    ]

    spec_parts = [
        f"# {assignment_name or 'Assignment'}",
        "",
        "## Assignment metadata",
        f"- Course ID: {ns.course_id}",
        f"- Assignment ID: {ns.assignment_id}",
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
        (front_page.get("body_text") or "_(empty or unavailable)_")
        if isinstance(front_page, dict)
        else "_(unavailable)_",
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
        "## Files inspected but not downloaded",
        "\n".join(f"- {line}" for line in inspected_not_downloaded)
        if inspected_not_downloaded
        else "_(none)_",
        "",
    ]
    for _meta, local, text in downloaded:
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

    spec_path = work_dir / "spec.md"
    problem_path = work_dir / "problem.md"
    spec_path.write_text("\n".join(spec_parts))

    problem_parts = [
        "---",
        f"assignment_name: {assignment_name or ''}",
        f"assignment_id: {ns.assignment_id}",
        f"course_id: {ns.course_id}",
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
    for _meta, local, text in downloaded:
        problem_parts += [
            f"## Attached: {local.name}",
            "",
            text if text else "_(extraction failed or unsupported format)_",
            "",
        ]
    problem_parts += ["## Rubric", "", "\n".join(rubric_lines), ""]
    problem_path.write_text("\n".join(problem_parts))

    review = {
        "deliverable_clear": bool(desc_text or downloaded or external_urls or module_hit_lines),
        "rubric_found": bool(isinstance(rubric, dict) and rubric.get("rubric_present")),
        "inputs_complete": not bool(unreachable),
        "missing_sources": [],
        "unreachable_resources": unreachable,
        "inspected_not_downloaded": inspected_not_downloaded,
        "blocking_unreachables": [],
        "verdict": "proceed" if (desc_text or downloaded or external_urls or module_hit_lines) else "recover",
    }
    review_path = investigation_dir / "review_a.json"
    review_path.write_text(json.dumps(review, indent=2, ensure_ascii=False))

    summary = {
        "work_dir": str(work_dir),
        "spec_md": str(spec_path),
        "problem_md": str(problem_path),
        "review_a_json": str(review_path),
        "references_downloaded": len(downloaded),
        "external_urls": len(external_urls),
        "module_items_inspected": len(module_items),
        "verdict": review["verdict"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if review["verdict"] == "proceed" else 2


if __name__ == "__main__":
    sys.exit(main())
