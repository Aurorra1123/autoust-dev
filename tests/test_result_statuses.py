from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.write_scan_plan import action_for


REPO_ROOT = Path(__file__).resolve().parents[1]


class HomeworkResultStatusTests(unittest.TestCase):
    def test_write_homework_result_accepts_revision_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp) / "DSAA2011" / "project"
            draft_dir = work_dir / "draft"
            draft_dir.mkdir(parents=True)
            deliverable = draft_dir / "report.md"
            deliverable.write_text("draft needs revision\n", encoding="utf-8")
            verification_log = work_dir / "verification.log"
            verification_log.write_text("FAIL | report style | missing style file\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/write_homework_result.py",
                    "--work-dir",
                    str(work_dir),
                    "--status",
                    "revision_needed",
                    "--course",
                    "DSAA2011",
                    "--course-id",
                    "2973",
                    "--assignment-id",
                    "21641",
                    "--assignment-name",
                    "Project",
                    "--draft-path",
                    str(deliverable),
                    "--verification-log",
                    str(verification_log),
                    "--human-review-item",
                    "Obtain the official LaTeX style file.",
                    "--note",
                    "draft generated but quality review requires revision",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads((work_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "revision_needed")
            self.assertEqual(result["course_id"], "2973")
            self.assertIn("Obtain the official LaTeX style file.", result["human_review_items"])

    def test_revision_needed_scan_action_continues_existing_workbench(self) -> None:
        action, reason = action_for(
            {
                "name": "Project",
                "submission_types": ["online_upload"],
            },
            {
                "status": "revision_needed",
            },
        )

        self.assertEqual(action, "continue")
        self.assertIn("revision", reason)


if __name__ == "__main__":
    unittest.main()
