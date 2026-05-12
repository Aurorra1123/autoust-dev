"""Fetch modules + items per course. Writes data/modules.json (one entry per course)."""
import json
from .api import CanvasClient, CURRENT_TERM, DATA_DIR


def main():
    with CanvasClient() as c:
        courses = c.current_term_courses(CURRENT_TERM)
        out = []
        for course in courses:
            cid = course["id"]
            cname = course.get("name")
            try:
                mods = c.paginate(f"/api/v1/courses/{cid}/modules", {"include[]": "items"})
            except Exception as e:
                print(f"  ! {cname}: {e}")
                continue
            for m in mods:
                if "items" not in m or m["items"] is None:
                    try:
                        m["items"] = c.paginate(f"/api/v1/courses/{cid}/modules/{m['id']}/items")
                    except Exception as e:
                        print(f"  ! items for {cname} / {m.get('name')}: {e}")
                        m["items"] = []
            out.append({"course_id": cid, "course_name": cname, "modules": mods})

            total_items = sum(len(m.get("items") or []) for m in mods)
            print(f"[{cname.split(' - ')[0]}] {len(mods)} modules, {total_items} items")
            for m in mods[:3]:
                items = m.get("items") or []
                print(f"    - {m.get('name')} ({len(items)} items)")
                for it in items[:2]:
                    print(f"        · [{it.get('type')}] {it.get('title')}")

        (DATA_DIR / "modules.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
        print(f"\nSaved data/modules.json")


if __name__ == "__main__":
    main()
