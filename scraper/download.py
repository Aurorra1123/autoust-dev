"""Folder-based file download with 3-step interactive flow and state tracking.

Three ways to use:

  1. Programmatic (for skill use):
       from download import list_courses, list_folder_tree, plan_download, execute_download

  2. CLI args (works anywhere, including pipes):
       python scraper/download.py --list                                 # list courses
       python scraper/download.py --list --course-id 2151                # list folders
       python scraper/download.py --course-id 2151 --folder-id 12345     # plan only (dry run)
       python scraper/download.py --course-id 2151 --folder-id 12345 --execute   # download
       Add --recursive to include subfolders.

  3. Interactive (only in real terminals):
       python scraper/download.py --interactive
"""
import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from .api import CanvasClient, CURRENT_TERM, DATA_DIR, ROOT

STATE_FILE = ROOT / ".state" / "downloads.json"
FILES_ROOT = DATA_DIR / "files"


def _load_state():
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text())


def _save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def safe_name(s):
    s = (s or "").strip()
    s = re.sub(r'[/\\:*?"<>|]', "_", s)
    return s[:120] or "untitled"


def _short_course(name):
    return (name or "").split(" - ")[0]


def fmt_size(n):
    if n is None:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def list_courses(client):
    """Step 1 data: returns list of {id, name, short} for current term."""
    courses = client.current_term_courses(CURRENT_TERM)
    return [{"id": c["id"], "name": c.get("name"), "short": _short_course(c.get("name"))} for c in courses]


def list_folder_tree(client, course_id):
    """Step 2 data: returns flat list of {folder_id, depth, display, file_count, size_bytes}.

    Pre-order traversal from root. Folders with no direct files AND no descendants are pruned.
    """
    folders_by_id, _files_by_folder, root_id = client.folder_tree(course_id)

    def has_anything(fid):
        f = folders_by_id[fid]
        if f["_direct_files"]:
            return True
        return any(has_anything(c) for c in f["_children"])

    out = []
    def walk(fid, depth):
        f = folders_by_id[fid]
        if not has_anything(fid):
            return
        out.append({
            "folder_id": fid,
            "depth": depth,
            "name": f.get("name"),
            "full_name": f.get("full_name"),
            "file_count": len(f["_direct_files"]),
            "size_bytes": f["_direct_size"],
        })
        for child_id in sorted(f["_children"], key=lambda i: folders_by_id[i].get("name") or ""):
            walk(child_id, depth + 1)

    if root_id:
        walk(root_id, 0)
    return out


def plan_download(client, course_id, folder_id, course_name, recursive=False):
    """Step 3 data: what would happen if you downloaded this folder?

    Returns {to_download: [...], to_skip: [...], dest_dir: Path}.
    Each item: {file_id, name, size, updated_at, url, dest_path, reason}.
    """
    folders_by_id, files_by_folder, _ = client.folder_tree(course_id)
    state = _load_state()

    short = _short_course(course_name)
    target_files = []

    def collect(fid):
        for fi in files_by_folder.get(fid, []):
            target_files.append(fi)
        if recursive:
            for child in folders_by_id[fid]["_children"]:
                collect(child)
    collect(folder_id)

    folder_name = folders_by_id[folder_id].get("name") if folder_id in folders_by_id else "unknown"
    dest_dir = FILES_ROOT / safe_name(short) / safe_name(folder_name)

    to_download = []
    to_skip = []
    for fi in target_files:
        dest_path = dest_dir / safe_name(fi.get("display_name") or f"file_{fi['id']}")
        key = str(dest_path.relative_to(FILES_ROOT))
        prior = state.get(key)
        item = {
            "file_id": fi["id"],
            "name": fi.get("display_name"),
            "size": fi.get("size"),
            "updated_at": fi.get("updated_at"),
            "url": fi.get("url"),
            "dest_path": dest_path,
            "key": key,
        }
        if prior and prior.get("file_id") == fi["id"] and prior.get("updated_at") == fi.get("updated_at") and dest_path.exists():
            item["reason"] = "already downloaded, unchanged"
            to_skip.append(item)
        else:
            item["reason"] = "new" if not prior else "updated_at changed"
            to_download.append(item)

    return {
        "to_download": to_download,
        "to_skip": to_skip,
        "dest_dir": dest_dir,
        "course_id": course_id,
        "course_name": course_name,
        "folder_id": folder_id,
        "folder_name": folder_name,
    }


def execute_download(client, plan):
    """Actually download what plan_download() returned."""
    plan["dest_dir"].mkdir(parents=True, exist_ok=True)
    state = _load_state()
    results = {"downloaded": [], "failed": []}

    for item in plan["to_download"]:
        try:
            resp = client.get_raw(item["url"])
            if not resp.ok:
                print(f"  ! {item['name']}: HTTP {resp.status}")
                results["failed"].append({**item, "error": f"HTTP {resp.status}"})
                continue
            item["dest_path"].write_bytes(resp.body())
            state[item["key"]] = {
                "file_id": item["file_id"],
                "course_id": plan["course_id"],
                "size": item["size"],
                "updated_at": item["updated_at"],
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  ↓ {item['name']} ({fmt_size(item['size'])})")
            results["downloaded"].append(item)
        except Exception as e:
            print(f"  ! {item['name']}: {e}")
            results["failed"].append({**item, "error": str(e)})

    _save_state(state)
    return results


# ─── CLI mode ───────────────────────────────────────────────────────────────

def _pick(prompt, options, label_fn):
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {label_fn(opt)}")
    while True:
        raw = _read_input("  > ")
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  please enter 1..{len(options)}")


def _confirm(prompt):
    raw = _read_input(f"{prompt} [y/N]: ").lower()
    return raw in ("y", "yes")


def _read_input(prompt):
    """Read a line from the user, falling back to /dev/tty if stdin is not a tty.

    This lets the script work both when launched normally and when launched from
    a wrapper (like Claude Code's `! ` bash) where stdin is piped.
    """
    if sys.stdin.isatty():
        return input(prompt).strip()
    try:
        with open("/dev/tty", "r+") as tty:
            tty.write(prompt)
            tty.flush()
            return tty.readline().rstrip("\n").strip()
    except OSError:
        raise RuntimeError(
            "No TTY available for input. Run this script directly in your terminal, "
            "or use the programmatic API (list_courses / plan_download / execute_download)."
        )


def cli_main():
    with CanvasClient() as client:
        courses = list_courses(client)
        if not courses:
            print("No courses in current term.")
            return
        course = _pick(
            f"[{CURRENT_TERM}] which course?",
            courses,
            lambda c: f"{c['short']}  —  {c['name']}",
        )

        tree = list_folder_tree(client, course["id"])
        if not tree:
            print("No folders with files in this course.")
            return
        print(f"\nFolders in {course['short']}:")
        for entry in tree:
            indent = "  " * entry["depth"]
            print(f"  {indent}· {entry['name']}  ({entry['file_count']} files, {fmt_size(entry['size_bytes'])})")

        folder = _pick(
            "which folder?",
            tree,
            lambda e: f"{'  ' * e['depth']}{e['name']}  ({e['file_count']} files, {fmt_size(e['size_bytes'])})",
        )

        recursive = False
        # If folder has descendants with files, ask
        folders_by_id, _, _ = client.folder_tree(course["id"])
        if folders_by_id[folder["folder_id"]]["_children"]:
            recursive = _confirm("include subfolders?")

        plan = plan_download(client, course["id"], folder["folder_id"], course["name"], recursive=recursive)

        print(f"\nDownload plan:")
        print(f"  destination: {plan['dest_dir']}")
        print(f"  to download: {len(plan['to_download'])} files ({fmt_size(sum(i['size'] or 0 for i in plan['to_download']))})")
        print(f"  to skip:     {len(plan['to_skip'])} files (already downloaded, unchanged)")
        if plan["to_download"]:
            print("\n  files to fetch (first 10):")
            for item in plan["to_download"][:10]:
                print(f"    + {item['name']}  ({fmt_size(item['size'])})  [{item['reason']}]")
            if len(plan["to_download"]) > 10:
                print(f"    ... and {len(plan['to_download']) - 10} more")

        if not plan["to_download"]:
            print("\nNothing to download.")
            return

        if not _confirm("\nconfirm download?"):
            print("cancelled.")
            return

        print("\ndownloading...")
        results = execute_download(client, plan)
        print(f"\ndone: {len(results['downloaded'])} downloaded, {len(results['failed'])} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Canvas course files.")
    parser.add_argument("--interactive", action="store_true", help="Interactive 3-step flow (needs real TTY)")
    parser.add_argument("--list", action="store_true", help="List courses, or folders if --course-id is set")
    parser.add_argument("--course-id", type=int, help="Course id to operate on")
    parser.add_argument("--folder-id", type=int, help="Folder id to download")
    parser.add_argument("--recursive", action="store_true", help="Include subfolders")
    parser.add_argument("--execute", action="store_true", help="Actually download (default: dry-run plan)")
    args = parser.parse_args()

    if args.interactive:
        cli_main()
        sys.exit(0)

    with CanvasClient() as client:
        if args.list and not args.course_id:
            for course in list_courses(client):
                print(f"  [{course['id']}] {course['short']}  —  {course['name']}")
            sys.exit(0)

        if args.list and args.course_id:
            tree = list_folder_tree(client, args.course_id)
            for entry in tree:
                indent = "  " * entry["depth"]
                print(f"  [{entry['folder_id']}]  {indent}{entry['name']}  ({entry['file_count']} files, {fmt_size(entry['size_bytes'])})")
            sys.exit(0)

        if args.course_id and args.folder_id:
            courses = list_courses(client)
            course = next((c for c in courses if c["id"] == args.course_id), None)
            if not course:
                print(f"ERROR: course {args.course_id} not in current-term enrollments", file=sys.stderr)
                sys.exit(1)

            plan = plan_download(
                client, args.course_id, args.folder_id, course["name"],
                recursive=args.recursive,
            )
            print(f"\nplan for [{course['short']}] / folder {args.folder_id} ({plan['folder_name']}):")
            print(f"  dest: {plan['dest_dir']}")
            print(f"  to download: {len(plan['to_download'])} files ({fmt_size(sum(i['size'] or 0 for i in plan['to_download']))})")
            print(f"  to skip:     {len(plan['to_skip'])} (already downloaded, unchanged)")
            for item in plan["to_download"][:15]:
                print(f"    + {item['name']}  ({fmt_size(item['size'])})  [{item['reason']}]")
            if len(plan["to_download"]) > 15:
                print(f"    ... and {len(plan['to_download']) - 15} more")

            if args.execute:
                if not plan["to_download"]:
                    print("\nnothing to download.")
                    sys.exit(0)
                print("\ndownloading...")
                results = execute_download(client, plan)
                print(f"\ndone: {len(results['downloaded'])} downloaded, {len(results['failed'])} failed")
            else:
                print("\n(dry-run; pass --execute to download)")
            sys.exit(0)

        parser.print_help()
        sys.exit(1)
