"""List files per course; optionally download. Writes data/files.json.

By default this only LISTS files (cheap, no download). Pass --download to actually
fetch them into data/files/<course>/.
"""
import json
import sys
import re
from .api import CanvasClient, CURRENT_TERM, DATA_DIR


def safe_name(s):
    return re.sub(r"[^\w\-.]+", "_", (s or "").strip())[:80] or "untitled"


def main():
    do_download = "--download" in sys.argv

    with CanvasClient() as c:
        courses = c.current_term_courses(CURRENT_TERM)
        out = []
        files_dir = DATA_DIR / "files"
        if do_download:
            files_dir.mkdir(exist_ok=True)

        for course in courses:
            cid = course["id"]
            cname = course.get("name")
            try:
                files = c.paginate(f"/api/v1/courses/{cid}/files")
            except Exception as e:
                print(f"  ! {cname}: {e}")
                continue
            total_bytes = sum(f.get("size") or 0 for f in files)
            print(f"[{cname.split(' - ')[0]}] {len(files)} files, {total_bytes / 1024 / 1024:.1f} MB")
            for f in files[:3]:
                size = (f.get("size") or 0) / 1024
                print(f"    · {f.get('display_name')} ({size:.1f} KB)")

            out.append({
                "course_id": cid,
                "course_name": cname,
                "files": [{
                    "id": f["id"],
                    "name": f.get("display_name"),
                    "size": f.get("size"),
                    "url": f.get("url"),
                    "content_type": f.get("content-type") or f.get("content_type"),
                    "updated_at": f.get("updated_at"),
                } for f in files],
            })

            if do_download and files:
                course_dir = files_dir / safe_name(cname.split(" - ")[0])
                course_dir.mkdir(exist_ok=True)
                for f in files:
                    url = f.get("url")
                    if not url:
                        continue
                    target = course_dir / safe_name(f.get("display_name") or f"file_{f['id']}")
                    if target.exists():
                        continue
                    resp = c.get_raw(url)
                    if resp.ok:
                        target.write_bytes(resp.body())
                        print(f"      ↓ {target.name}")

        (DATA_DIR / "files.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
        print(f"\nSaved data/files.json" + (" + downloaded files" if do_download else " (use --download to fetch)"))


if __name__ == "__main__":
    main()
