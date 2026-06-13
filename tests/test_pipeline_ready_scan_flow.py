import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_python(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(ROOT / ".venv" / "bin" / "python"), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pipeline_ready_scan_plan_surfaces_review_or_execute_high_priority(tmp_path: Path):
    write_json(
        tmp_path / "assignments.json",
        [
            {
                "id": 88,
                "course_id": 42,
                "name": "Final Project",
                "due_at": None,
                "submission_state": "unsubmitted",
            }
        ],
    )
    write_json(tmp_path / "courses.json", [{"id": 42, "course_code": "DSAA2011", "name": "DSAA2011"}])
    write_json(tmp_path / "announcements.json", [])
    write_json(
        tmp_path / "homework" / "DSAA2011" / "final-project" / "result.json",
        {
            "status": "pipeline_ready",
            "course_id": "42",
            "assignment_id": "88",
            "work_dir": "data/homework/DSAA2011/final-project",
            "updated_at": "2026-06-13T00:00:00+08:00",
        },
    )

    result = run_python(
        str(ROOT / "scripts" / "write_scan_plan.py"),
        "--assignments-json",
        str(tmp_path / "assignments.json"),
        "--courses-json",
        str(tmp_path / "courses.json"),
        "--announcements-json",
        str(tmp_path / "announcements.json"),
        "--homework-dir",
        str(tmp_path / "homework"),
        "--runs-dir",
        str(tmp_path / "runs"),
        "--date",
        "2026-06-13",
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    plan = json.loads((tmp_path / "runs" / "2026-06-13" / "plan.json").read_text(encoding="utf-8"))
    item = plan["items"][0]
    assert item["suggested_next_step"] == "review_or_execute"
    assert item["priority"] == "high"


def test_pipeline_ready_selector_marks_existing_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "2026-06-13"
    write_json(
        run_dir / "plan.json",
        {
            "items": [
                {
                    "index": 1,
                    "course_id": "42",
                    "assignment_id": "88",
                    "assignment_name": "Final Project",
                    "existing_result_status": "pipeline_ready",
                    "existing_result_path": "data/homework/DSAA2011/final-project/result.json",
                    "suggested_next_step": "review_or_execute",
                }
            ]
        },
    )
    write_json(
        run_dir / "pending_assignments.json",
        {
            "assignments": [
                {
                    "course_id": "42",
                    "assignment_id": "88",
                    "suggested_work_dir": "data/homework/DSAA2011/final-project",
                }
            ]
        },
    )

    result = run_python(
        str(ROOT / "scripts" / "select_plan_item.py"),
        "--index",
        "1",
        "--date",
        "2026-06-13",
        "--runs-dir",
        str(tmp_path / "runs"),
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    selection = json.loads(result.stdout)
    assert selection["recommended_action"] == "review_or_execute"
    assert selection["has_existing_pipeline"] is True
    assert selection["has_existing_draft"] is False


def test_pipeline_ready_user_docs_use_runtime_status_names_and_action():
    sync_status = read("sub-skills/tasks/sync-status.md")
    readme_en = read("README.en.md")

    assert "`review_or_execute`" in sync_status
    assert "`pipeline_ready`" in readme_en
    assert "`draft_ready`" in readme_en
    assert "pipeline-ready" not in readme_en
    assert "draft-ready" not in readme_en
