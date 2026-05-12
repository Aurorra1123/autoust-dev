"""Fetch quizzes + discussion_topics per current-term course."""
import json
from .api import CanvasClient, CURRENT_TERM, DATA_DIR


def main():
    with CanvasClient() as c:
        courses = c.current_term_courses(CURRENT_TERM)
        quizzes_out = []
        disc_out = []

        for course in courses:
            cid = course["id"]
            cname = course.get("name")
            short = cname.split(" - ")[0]
            try:
                quizzes = c.paginate(f"/api/v1/courses/{cid}/quizzes")
            except RuntimeError as e:
                if "404" in str(e):
                    quizzes = []  # course has quizzes feature disabled
                else:
                    print(f"  ! quizzes {cname}: {e}")
                    quizzes = []
            try:
                discs = c.paginate(f"/api/v1/courses/{cid}/discussion_topics")
            except RuntimeError as e:
                if "404" in str(e):
                    discs = []
                else:
                    print(f"  ! discussions {cname}: {e}")
                    discs = []

            print(f"[{short}] {len(quizzes)} quizzes, {len(discs)} discussions")
            for q in quizzes[:2]:
                print(f"    quiz · {q.get('title')} (due {q.get('due_at')})")
            for d in discs[:2]:
                print(f"    disc · {d.get('title')}")

            quizzes_out.append({
                "course_id": cid, "course_name": cname,
                "quizzes": [{
                    "id": q["id"], "title": q.get("title"),
                    "due_at": q.get("due_at"), "points": q.get("points_possible"),
                    "html_url": q.get("html_url"),
                } for q in quizzes],
            })
            disc_out.append({
                "course_id": cid, "course_name": cname,
                "discussions": [{
                    "id": d["id"], "title": d.get("title"),
                    "posted_at": d.get("posted_at"),
                    "html_url": d.get("html_url"),
                } for d in discs],
            })

        (DATA_DIR / "quizzes.json").write_text(json.dumps(quizzes_out, indent=2, ensure_ascii=False))
        (DATA_DIR / "discussions.json").write_text(json.dumps(disc_out, indent=2, ensure_ascii=False))
        print(f"\nSaved data/quizzes.json + data/discussions.json")


if __name__ == "__main__":
    main()
