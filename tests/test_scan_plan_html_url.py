import unittest

from scripts.write_scan_plan import build_plan


class ScanPlanHtmlUrlTests(unittest.TestCase):
    def test_build_plan_preserves_assignment_html_url(self):
        plan = build_plan(
            [
                {
                    "bucket": "urgent",
                    "course": "EXAMPLE101",
                    "course_id": "12",
                    "course_name": "Example Course",
                    "assignment_id": "34",
                    "assignment_name": "Research proposal",
                    "due_at": None,
                    "due_at_local": None,
                    "hours_left": None,
                    "submission_state": "unsubmitted",
                    "existing_result_status": None,
                    "existing_result_path": None,
                    "recommended_action": "recon",
                    "reason": "inspect sources before drafting",
                    "html_url": "https://canvas.example.edu/courses/12/assignments/34",
                }
            ]
        )

        self.assertEqual(
            plan["items"][0]["html_url"],
            "https://canvas.example.edu/courses/12/assignments/34",
        )


if __name__ == "__main__":
    unittest.main()
