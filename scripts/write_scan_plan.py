"""Build an assistant-style Canvas scan plan from local AutoStudy state.

The script does not talk to Canvas. It reads canvascli JSON snapshots plus
per-assignment result.json files, then writes a dated run directory with:

- pending_assignments.json: actionable assignment facts and local state
- plan.json: suggested next steps for the user to approve
- REPORT.md: user-facing summary for sync-status
- raw/*.json: copies of the canvascli snapshots used for this plan
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


TERMINAL_CANVAS_STATES = {"submitted", "graded"}
TERMINAL_RESULT_STATUSES = {"submitted", "skipped"}
LOCAL_TZ = dt.datetime.now(dt.timezone.utc).astimezone().tzinfo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assignments-json", default=Path("data/assignments.json"), type=Path)
    parser.add_argument("--courses-json", default=Path("data/courses.json"), type=Path)
    parser.add_argument("--announcements-json", default=Path("data/announcements.json"), type=Path)
    parser.add_argument("--homework-dir", default=Path("data/homework"), type=Path)
    parser.add_argument("--runs-dir", default=Path("data/runs"), type=Path)
    parser.add_argument("--date", help="Run date in YYYY-MM-DD; defaults to local today.")
    parser.add_argument(
        "--include-terminal-canvas",
        action="store_true",
        help="Include submitted/graded Canvas items for verification fixtures.",
    )
    parser.add_argument(
        "--overdue-days",
        type=int,
        default=30,
        help="Exclude unsubmitted overdue assignments older than this many days.",
    )
    return parser.parse_args()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_list(data: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get(key), list):
        return [item for item in data[key] if isinstance(item, dict)]
    return []


def parse_dt(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(LOCAL_TZ)


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def run_date(ns: argparse.Namespace) -> str:
    if ns.date:
        dt.date.fromisoformat(ns.date)
        return ns.date
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def copy_raw_snapshot(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(destination, source.read_text(encoding="utf-8"))
    return True


def course_short(course: dict[str, Any] | None, fallback_name: str | None) -> str:
    if course:
        code = course.get("course_code")
        if isinstance(code, str) and code.strip():
            return code.strip()
    name = fallback_name or ""
    match = re.search(r"\b[A-Z]{2,}[A-Z0-9]*\s*\d{3,5}\b(?:\s*\([^)]+\))?", name)
    if match:
        return re.sub(r"\s+", " ", match.group(0)).strip()
    return name.split(" - ", 1)[0].strip() or "Unknown Course"


def slugish(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "assignment"


def assignment_id(item: dict[str, Any]) -> str | None:
    value = item.get("assignment_id", item.get("id"))
    if value is None:
        return None
    return str(value)


def course_id(item: dict[str, Any]) -> str | None:
    value = item.get("course_id")
    if value is None:
        return None
    return str(value)


def result_sort_key(result: dict[str, Any]) -> str:
    value = result.get("updated_at") or result.get("completed_at") or ""
    return str(value)


def collect_results(homework_dir: Path) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    if not homework_dir.exists():
        return by_key
    for path in homework_dir.rglob("result.json"):
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(result, dict):
            continue
        cid = result.get("course_id")
        aid = result.get("assignment_id")
        if cid is None or aid is None:
            continue
        key = f"{cid}:{aid}"
        result = dict(result)
        result["_path"] = path.as_posix()
        previous = by_key.get(key)
        if previous is None or result_sort_key(result) >= result_sort_key(previous):
            by_key[key] = result
    return by_key


def bucket_for(due_at: dt.datetime | None, now: dt.datetime) -> tuple[str, float | None]:
    if due_at is None:
        return "undated", None
    hours_left = (due_at - now).total_seconds() / 3600
    if hours_left <= 0:
        return "overdue", round(hours_left, 2)
    if hours_left <= 72:
        return "urgent", round(hours_left, 2)
    if hours_left <= 168:
        return "soon", round(hours_left, 2)
    return "later", round(hours_left, 2)


def action_for(item: dict[str, Any], result: dict[str, Any] | None) -> tuple[str, str]:
    if result:
        status = result.get("status")
        if status == "draft_ready":
            return "review_or_submit", "local draft is ready; user should review or submit"
        if status == "error":
            return "continue", "previous workflow ended with an error; inspect result.json before retrying"
        if result.get("deferred_to_next_run"):
            return "recon", "user deferred this item earlier; include it again for review"

    name = str(item.get("name") or item.get("assignment_name") or "").lower()
    submission_types = item.get("submission_types") or []
    if any(word in name for word in ("project", "final", "report", "paper", "lab", "homework")):
        return "recon", "likely substantive assignment; inspect Canvas sources before drafting"
    if "online_quiz" in submission_types or "quiz" in name:
        return "manual_review", "quiz-like item may require manual Canvas interaction"
    return "recon", "unsubmitted assignment; inspect sources before deciding whether to draft"


def should_include(
    item: dict[str, Any],
    result: dict[str, Any] | None,
    due_at: dt.datetime | None,
    now: dt.datetime,
    ns: argparse.Namespace,
) -> tuple[bool, str | None]:
    canvas_state = str(item.get("submission_state") or item.get("workflow_state") or "unknown")
    if not ns.include_terminal_canvas and canvas_state in TERMINAL_CANVAS_STATES:
        return False, f"canvas_{canvas_state}"

    if result and result.get("status") in TERMINAL_RESULT_STATUSES and not result.get("deferred_to_next_run"):
        return False, f"result_{result.get('status')}"

    if due_at is not None and due_at < now - dt.timedelta(days=ns.overdue_days):
        if canvas_state not in TERMINAL_CANVAS_STATES and not ns.include_terminal_canvas:
            return False, "ancient_overdue"
    return True, None


def due_label(due_at: dt.datetime | None, hours_left: float | None) -> str:
    if due_at is None:
        return "no due date"
    if hours_left is not None and hours_left <= 0:
        return f"overdue {round(abs(hours_left))}h"
    return due_at.strftime("%a %m-%d %H:%M")


def priority_for(bucket: str, action: str) -> str:
    if action == "review_or_submit":
        return "high"
    if bucket in {"overdue", "urgent"}:
        return "high"
    if bucket == "soon":
        return "medium"
    return "normal"


def sort_key(item: dict[str, Any]) -> tuple[int, float]:
    bucket_order = {"overdue": 0, "urgent": 1, "soon": 2, "undated": 3, "later": 4}
    hours = item.get("hours_left")
    if hours is None:
        hours_value = 10**9
    else:
        hours_value = float(hours)
    return bucket_order.get(str(item.get("bucket")), 9), hours_value


def build_pending(ns: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, int]]:
    assignments = ensure_list(load_json(ns.assignments_json, []), "assignments")
    courses = ensure_list(load_json(ns.courses_json, []), "courses")
    courses_by_id = {str(course.get("id")): course for course in courses if course.get("id") is not None}
    results = collect_results(ns.homework_dir)
    now = dt.datetime.now(dt.timezone.utc).astimezone()

    pending: list[dict[str, Any]] = []
    skipped_counts: dict[str, int] = {}

    for raw in assignments:
        cid = course_id(raw)
        aid = assignment_id(raw)
        if cid is None or aid is None:
            skipped_counts["missing_id"] = skipped_counts.get("missing_id", 0) + 1
            continue
        key = f"{cid}:{aid}"
        result = results.get(key)
        parsed_due = parse_dt(raw.get("due_at"))
        include, reason = should_include(raw, result, parsed_due, now, ns)
        if not include:
            skipped_counts[reason or "filtered"] = skipped_counts.get(reason or "filtered", 0) + 1
            continue

        bucket, hours_left = bucket_for(parsed_due, now)
        action, action_reason = action_for(raw, result)
        course = courses_by_id.get(cid)
        course_name = raw.get("course_name") or (course or {}).get("name")
        short = course_short(course, course_name)
        result_status = result.get("status") if result else None

        pending.append(
            {
                "course": short,
                "course_id": cid,
                "course_name": course_name,
                "assignment_id": aid,
                "assignment_name": raw.get("name") or raw.get("assignment_name") or f"assignment-{aid}",
                "due_at": raw.get("due_at"),
                "due_at_local": parsed_due.isoformat(timespec="seconds") if parsed_due else None,
                "days_until_due": round(hours_left / 24, 2) if hours_left is not None else None,
                "hours_left": hours_left,
                "bucket": bucket,
                "points_possible": raw.get("points_possible"),
                "submission_state": raw.get("submission_state") or raw.get("workflow_state") or "unknown",
                "submission_types": raw.get("submission_types") or [],
                "html_url": raw.get("html_url"),
                "existing_result_status": result_status,
                "existing_result_path": result.get("_path") if result else None,
                "recommended_action": action,
                "reason": action_reason,
                "suggested_work_dir": f"data/homework/{slugish(short).upper()}/{slugish(str(raw.get('name') or aid))}",
            }
        )

    pending.sort(key=sort_key)
    return pending, skipped_counts


def build_plan(pending: list[dict[str, Any]]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for index, item in enumerate(pending, start=1):
        action = item["recommended_action"]
        items.append(
            {
                "index": index,
                "bucket": item["bucket"],
                "priority": priority_for(item["bucket"], action),
                "course": item["course"],
                "course_id": item["course_id"],
                "course_name": item["course_name"],
                "assignment_id": item["assignment_id"],
                "assignment_name": item["assignment_name"],
                "due_at": item["due_at"],
                "due_at_local": item["due_at_local"],
                "hours_left": item["hours_left"],
                "submission_state": item["submission_state"],
                "existing_result_status": item["existing_result_status"],
                "existing_result_path": item["existing_result_path"],
                "suggested_next_step": action,
                "why": item["reason"],
                "user_decision": None,
            }
        )
    return {"generated_at": iso_now(), "items": items}


def render_report(pending: list[dict[str, Any]], skipped_counts: dict[str, int]) -> str:
    generated = iso_now()
    lines = [
        f"# Canvas Plan - {generated}",
        "",
        "This plan is a recommendation layer. It does not execute homework until the user chooses an item.",
        "",
    ]
    if not pending:
        lines.extend(
            [
                "## Recommended Next",
                "",
                "No actionable assignments found in the current Canvas snapshot.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Recommended Next",
                "",
                "| # | Priority | Course | Assignment | Due | State | Suggested next step |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for index, item in enumerate(pending, start=1):
            lines.append(
                "| {index} | {priority} | {course} | {assignment} | {due} | {state} | {action} |".format(
                    index=index,
                    priority=priority_for(item["bucket"], item["recommended_action"]),
                    course=item["course"],
                    assignment=str(item["assignment_name"]).replace("|", "/"),
                    due=due_label(parse_dt(item["due_at"]), item["hours_left"]),
                    state=item["existing_result_status"] or item["submission_state"],
                    action=item["recommended_action"],
                )
            )
        lines.append("")

    lines.extend(
        [
            "## How To Use",
            "",
            "- Choose an item number to run `do-homework` reconnaissance or continue a draft.",
            "- Choose `skip` if you only wanted the overview.",
            "- Already drafted items should be reviewed before submission.",
            "",
            "## Scan Notes",
            "",
        ]
    )
    if skipped_counts:
        for key in sorted(skipped_counts):
            lines.append(f"- Filtered `{key}`: {skipped_counts[key]}")
    else:
        lines.append("- No assignments were filtered out.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ns = parse_args()
    try:
        date = run_date(ns)
        out_dir = ns.runs_dir / date
        pending, skipped_counts = build_pending(ns)
        plan = build_plan(pending)

        metadata = {
            "generated_at": plan["generated_at"],
            "run_date": date,
            "source": {
                "assignments_json": ns.assignments_json.as_posix(),
                "courses_json": ns.courses_json.as_posix(),
                "announcements_json": ns.announcements_json.as_posix(),
                "homework_dir": ns.homework_dir.as_posix(),
            },
            "counts": {
                "pending": len(pending),
                "filtered": skipped_counts,
            },
        }
        pending_doc = dict(metadata)
        pending_doc["assignments"] = pending
        plan = dict(metadata, **plan)

        raw_dir = out_dir / "raw"
        copied_raw = {
            "assignments": copy_raw_snapshot(ns.assignments_json, raw_dir / "assignments.json"),
            "courses": copy_raw_snapshot(ns.courses_json, raw_dir / "courses.json"),
            "announcements": copy_raw_snapshot(ns.announcements_json, raw_dir / "announcements.json"),
        }
        pending_doc["raw_snapshots"] = copied_raw
        plan["raw_snapshots"] = copied_raw

        atomic_write_json(out_dir / "pending_assignments.json", pending_doc)
        atomic_write_json(out_dir / "plan.json", plan)
        atomic_write(out_dir / "REPORT.md", render_report(pending, skipped_counts))
    except Exception as exc:
        print(f"write_scan_plan failed: {exc}", file=sys.stderr)
        return 2

    print((ns.runs_dir / date / "plan.json").as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
