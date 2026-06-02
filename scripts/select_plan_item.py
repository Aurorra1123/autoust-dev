"""Select one actionable item from an AutoStudy scan plan.

The script is intentionally local-only: it reads data/runs/<date>/plan.json and
pending_assignments.json, then prints the selected assignment identity for
do-homework. It does not call Canvas, run reconnaissance, or write result.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, required=True, help="1-based plan item index to select.")
    parser.add_argument("--date", help="Run date in YYYY-MM-DD; defaults to local today.")
    parser.add_argument("--runs-dir", default=Path("data/runs"), type=Path)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def local_date() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RuntimeError(f"missing required file: {path}") from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {path}: {exc}") from None


def require_dict(data: Any, path: Path) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return data


def item_key(item: dict[str, Any]) -> tuple[str | None, str | None]:
    cid = item.get("course_id")
    aid = item.get("assignment_id")
    return (str(cid) if cid is not None else None, str(aid) if aid is not None else None)


def find_plan_item(plan: dict[str, Any], index: int) -> dict[str, Any]:
    items = plan.get("items")
    if not isinstance(items, list):
        raise RuntimeError("plan.json is missing an items list")
    if not items:
        raise RuntimeError("plan.json has no actionable items")
    for item in items:
        if isinstance(item, dict) and item.get("index") == index:
            return item
    available = [str(item.get("index")) for item in items if isinstance(item, dict) and item.get("index") is not None]
    hint = ", ".join(available) if available else "none"
    raise RuntimeError(f"plan item index {index} not found; available indices: {hint}")


def find_pending_item(pending_doc: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any] | None:
    assignments = pending_doc.get("assignments")
    if not isinstance(assignments, list):
        return None
    selected_key = item_key(selected)
    if selected_key[0] is None or selected_key[1] is None:
        return None
    for item in assignments:
        if isinstance(item, dict) and item_key(item) == selected_key:
            return item
    return None


def normalized_action(plan_item: dict[str, Any], pending_item: dict[str, Any] | None) -> str:
    value = plan_item.get("suggested_next_step")
    if value is None and pending_item is not None:
        value = pending_item.get("recommended_action")
    return str(value or "unknown")


def build_selection(date: str, plan_item: dict[str, Any], pending_item: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(pending_item or {})
    merged.update(plan_item)
    action = normalized_action(plan_item, pending_item)
    cid, aid = item_key(merged)
    if cid is None or aid is None:
        raise RuntimeError("selected plan item is missing course_id or assignment_id")

    canvas_url = merged.get("html_url")
    if not canvas_url:
        canvas_url = f"https://hkust-gz.instructure.com/courses/{cid}/assignments/{aid}"

    existing_status = merged.get("existing_result_status")
    result_path = merged.get("existing_result_path")

    return {
        "run_date": date,
        "index": merged.get("index"),
        "course": merged.get("course"),
        "course_id": cid,
        "course_name": merged.get("course_name"),
        "assignment_id": aid,
        "assignment_name": merged.get("assignment_name"),
        "due_at": merged.get("due_at"),
        "due_at_local": merged.get("due_at_local"),
        "submission_state": merged.get("submission_state"),
        "existing_result_status": existing_status,
        "existing_result_path": result_path,
        "recommended_action": action,
        "requires_recon": action == "recon",
        "requires_error_review": action == "continue",
        "requires_manual_review": action == "manual_review",
        "has_existing_draft": existing_status == "draft_ready",
        "suggested_work_dir": merged.get("suggested_work_dir"),
        "canvas_url": canvas_url,
        "why": merged.get("why") or merged.get("reason"),
        "user_decision": merged.get("user_decision"),
    }


def main() -> int:
    ns = parse_args()
    date = ns.date or local_date()
    try:
        dt.date.fromisoformat(date)
        run_dir = ns.runs_dir / date
        plan_path = run_dir / "plan.json"
        pending_path = run_dir / "pending_assignments.json"
        plan = require_dict(load_json(plan_path), plan_path)
        pending_doc = require_dict(load_json(pending_path), pending_path)
        plan_item = find_plan_item(plan, ns.index)
        pending_item = find_pending_item(pending_doc, plan_item)
        selection = build_selection(date, plan_item, pending_item)
    except Exception as exc:
        print(f"select_plan_item failed: {exc}", file=sys.stderr)
        return 2

    if ns.pretty:
        print(json.dumps(selection, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(selection, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
