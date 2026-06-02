"""Write the per-assignment AutoStudy result.json state receipt.

This script intentionally records workflow state only. Reconnaissance evidence
stays in spec.md, problem.md, and investigation/review_a.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any


VALID_STATUSES = {"skipped", "draft_ready", "submitted", "error"}
TERMINAL_SUCCESS_STATUSES = {"draft_ready", "submitted"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUSES))
    parser.add_argument("--course")
    parser.add_argument("--course-id")
    parser.add_argument("--assignment-id")
    parser.add_argument("--assignment-name")
    parser.add_argument("--spec-md", type=Path)
    parser.add_argument("--problem-md", type=Path)
    parser.add_argument("--draft-path", type=Path)
    parser.add_argument("--deliverable", action="append", default=[], type=Path)
    parser.add_argument("--verification-log", type=Path)
    parser.add_argument("--human-review-item", action="append", default=[])
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--submitted-at")
    parser.add_argument("--submission-attempt", type=int)
    parser.add_argument("--canvas-url")
    parser.add_argument("--deferred-to-next-run", action="store_true")
    parser.add_argument(
        "--allow-missing-deliverables",
        action="store_true",
        help="Allow draft_ready/submitted results to reference deliverables that do not exist yet.",
    )
    return parser.parse_args()


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def display_path(path: Path | None, cwd: Path) -> str | None:
    if path is None:
        return None
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    try:
        return resolved.relative_to(cwd).as_posix()
    except ValueError:
        return resolved.as_posix()


def default_existing_path(work_dir: Path, name: str) -> Path | None:
    path = work_dir / name
    return path if path.exists() else None


def read_review_a(work_dir: Path) -> dict[str, Any] | None:
    path = work_dir / "investigation" / "review_a.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def clean_strings(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value and value.strip()]


def validate(ns: argparse.Namespace, deliverables: list[Path]) -> list[str]:
    errors: list[str] = []
    if ns.status in TERMINAL_SUCCESS_STATUSES and not deliverables:
        errors.append(f"{ns.status} requires --draft-path or at least one --deliverable")
    if ns.status == "submitted" and not (ns.submitted_at or ns.canvas_url):
        errors.append("submitted requires --submitted-at or --canvas-url")
    if ns.status in {"skipped", "error"} and not clean_strings(ns.note):
        errors.append(f"{ns.status} should include at least one --note")
    if not ns.allow_missing_deliverables:
        for path in deliverables:
            if not path.exists():
                errors.append(f"deliverable does not exist: {path}")
            elif path.is_file() and path.stat().st_size == 0:
                errors.append(f"deliverable is empty: {path}")
    return errors


def build_result(ns: argparse.Namespace) -> dict[str, Any]:
    cwd = Path.cwd().resolve()
    work_dir = ns.work_dir
    work_dir.mkdir(parents=True, exist_ok=True)

    spec_md = ns.spec_md or default_existing_path(work_dir, "spec.md")
    problem_md = ns.problem_md or default_existing_path(work_dir, "problem.md")
    deliverables = list(ns.deliverable)
    if ns.draft_path and ns.draft_path not in deliverables:
        deliverables.insert(0, ns.draft_path)

    errors = validate(ns, deliverables)
    if errors:
        raise ValueError("\n".join(errors))

    result: dict[str, Any] = {
        "status": ns.status,
        "work_dir": display_path(work_dir, cwd),
        "updated_at": iso_now(),
    }

    for key, value in (
        ("course", ns.course),
        ("course_id", ns.course_id),
        ("assignment_id", ns.assignment_id),
        ("assignment_name", ns.assignment_name),
        ("canvas_url", ns.canvas_url),
        ("submitted_at", ns.submitted_at),
        ("submission_attempt", ns.submission_attempt),
    ):
        if value is not None:
            result[key] = value

    spec_value = display_path(spec_md, cwd)
    problem_value = display_path(problem_md, cwd)
    if spec_value:
        result["spec_md"] = spec_value
    if problem_value:
        result["problem_md"] = problem_value
    if ns.draft_path:
        result["draft_path"] = display_path(ns.draft_path, cwd)
    if deliverables:
        result["deliverables"] = [display_path(path, cwd) for path in deliverables]
    if ns.verification_log:
        result["verification_log_path"] = display_path(ns.verification_log, cwd)

    human_review_items = clean_strings(ns.human_review_item)
    if human_review_items:
        result["human_review_items"] = human_review_items

    notes = clean_strings(ns.note)
    if notes:
        result["notes"] = "\n".join(notes)

    if ns.deferred_to_next_run:
        result["deferred_to_next_run"] = True

    review_a = read_review_a(work_dir)
    if review_a and review_a.get("verdict"):
        result["review_a_verdict"] = review_a.get("verdict")

    return result


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ns = parse_args()
    try:
        result = build_result(ns)
        out_path = ns.work_dir / "result.json"
        atomic_write_json(out_path, result)
    except Exception as exc:
        print(f"write_homework_result failed: {exc}", file=sys.stderr)
        return 2
    print(out_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
