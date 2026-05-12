"""Fetch announcements for current-term courses. Writes data/announcements.json."""
import json
from .api import CanvasClient, CURRENT_TERM, DATA_DIR


def main():
    with CanvasClient() as c:
        courses = c.current_term_courses(CURRENT_TERM)
        context_codes = [f"course_{course['id']}" for course in courses]
        if not context_codes:
            print("no courses for current term")
            return

        anns = c.paginate(
            "/api/v1/announcements",
            {"context_codes[]": context_codes, "active_only": "true"},
        )

        course_by_id = {course["id"]: course.get("name") for course in courses}
        for a in anns:
            ctx = a.get("context_code", "")
            cid = int(ctx.replace("course_", "")) if ctx.startswith("course_") else None
            a["_course_id"] = cid
            a["_course_name"] = course_by_id.get(cid)

        anns.sort(key=lambda x: x.get("posted_at") or "", reverse=True)
        print(f"Announcements: {len(anns)} across {len(courses)} courses")
        for a in anns[:15]:
            posted = (a.get("posted_at") or "?")[:16].replace("T", " ")
            short_course = (a.get("_course_name") or "?").split(" - ")[0]
            print(f"  {posted}  [{short_course}] {a.get('title')}")
        if len(anns) > 15:
            print(f"  ... and {len(anns) - 15} more")

        (DATA_DIR / "announcements.json").write_text(json.dumps(
            [{
                "id": a["id"],
                "title": a.get("title"),
                "course_id": a["_course_id"],
                "course_name": a["_course_name"],
                "posted_at": a.get("posted_at"),
                "html_url": a.get("html_url"),
                "message": a.get("message"),
            } for a in anns],
            indent=2, ensure_ascii=False))
        print(f"\nSaved data/announcements.json")


if __name__ == "__main__":
    main()
