import unittest

from scripts.select_plan_item import build_selection


class SelectPlanItemTests(unittest.TestCase):
    def test_missing_html_url_stays_null(self):
        selection = build_selection(
            "2026-06-14",
            {
                "index": 1,
                "course_id": "12",
                "assignment_id": "34",
                "assignment_name": "Research proposal",
                "suggested_next_step": "recon",
            },
            None,
        )

        self.assertIsNone(selection["canvas_url"])

    def test_existing_html_url_is_preserved(self):
        selection = build_selection(
            "2026-06-14",
            {
                "index": 1,
                "course_id": "12",
                "assignment_id": "34",
                "assignment_name": "Research proposal",
                "html_url": "https://canvas.example.edu/courses/12/assignments/34",
                "suggested_next_step": "recon",
            },
            None,
        )

        self.assertEqual(
            selection["canvas_url"],
            "https://canvas.example.edu/courses/12/assignments/34",
        )


if __name__ == "__main__":
    unittest.main()
