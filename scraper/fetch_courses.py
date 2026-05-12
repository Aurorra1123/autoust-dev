"""Fetch courses + assignments for the current term. Writes data/courses.json + data/assignments.json."""
import json
from datetime import datetime, timezone
from .api import CanvasClient, CURRENT_TERM, DATA_DIR


def main():
    with CanvasClient() as c:
        me = c.get("/api/v1/users/self")
        print(f"Logged in as: {me.get('name')} (id={me.get('id')})")

        courses = c.current_term_courses(CURRENT_TERM)
        print(f"\n[{CURRENT_TERM}] {len(courses)} courses:")
        for course in courses:
            print(f"  [{course['id']}] {course.get('name')}")

        assignments = []
        for course in courses:
            try:
                aas = c.paginate(
                    f"/api/v1/courses/{course['id']}/assignments",
                    {"order_by": "due_at", "include[]": "submission"},
                )
            except Exception as e:
                print(f"  ! {course.get('name')}: {e}")
                continue
            for a in aas:
                a["_course_name"] = course.get("name")
                a["_course_id"] = course["id"]
            assignments.extend(aas)

        now = datetime.now(timezone.utc)
        upcoming = []
        past = []
        for a in assignments:
            due = a.get("due_at")
            if not due:
                continue
            try:
                due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            except ValueError:
                continue
            (upcoming if due_dt >= now else past).append((due_dt, a))
        upcoming.sort(key=lambda x: x[0])
        past.sort(key=lambda x: x[0], reverse=True)

        def fmt(due_dt, a):
            sub = (a.get("submission") or {}).get("workflow_state", "unsubmitted")
            return f"  {due_dt.strftime('%Y-%m-%d %H:%M')}  [{a['_course_name'].split(' - ')[0]}] {a['name']}  ({sub})"

        print(f"\nUpcoming ({len(upcoming)}):")
        for due_dt, a in upcoming[:20]:
            print(fmt(due_dt, a))

        print(f"\nMost recent past ({min(10, len(past))} of {len(past)}):")
        for due_dt, a in past[:10]:
            print(fmt(due_dt, a))

        (DATA_DIR / "courses.json").write_text(json.dumps(
            [{"id": x["id"], "name": x.get("name")} for x in courses],
            indent=2, ensure_ascii=False))
        (DATA_DIR / "assignments.json").write_text(json.dumps(
            [{
                "id": a["id"],
                "name": a["name"],
                "course_id": a["_course_id"],
                "course_name": a["_course_name"],
                "due_at": a.get("due_at"),
                "html_url": a.get("html_url"),
                "submission_state": (a.get("submission") or {}).get("workflow_state"),
            } for a in assignments],
            indent=2, ensure_ascii=False))
        print(f"\nSaved data/courses.json + data/assignments.json")


if __name__ == "__main__":
    main()
