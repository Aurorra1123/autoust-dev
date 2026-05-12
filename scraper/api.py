"""Canvas API client. Wraps playwright's authenticated request context.

Usage:
    with CanvasClient() as c:
        me = c.get("/api/v1/users/self")
        courses = c.paginate("/api/v1/courses", {"include[]": "term"})
"""
import sys
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

CANVAS = "https://hkust-gz.instructure.com"
ROOT = Path(__file__).parent.parent
AUTH_DIR = ROOT / ".auth"
STATE_FILE = AUTH_DIR / "canvas_state.json"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


class CanvasClient:
    def __init__(self, state_file=STATE_FILE):
        if not state_file.exists():
            print(f"ERROR: {state_file} not found. Run scraper/login.py first.", file=sys.stderr)
            sys.exit(1)
        self._state_file = state_file
        self._pw = None
        self._browser = None
        self._ctx = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._ctx = self._browser.new_context(storage_state=str(self._state_file))
        return self

    def __exit__(self, *exc):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def _url(self, path, params=None):
        url = f"{CANVAS}{path}" if path.startswith("/") else path
        if params:
            sep = "&" if "?" in url else "?"
            url += sep + urlencode(params, doseq=True)
        return url

    def get(self, path, params=None):
        """Single GET returning parsed JSON. Raises on non-2xx."""
        resp = self._ctx.request.get(self._url(path, params))
        if not resp.ok:
            raise RuntimeError(f"GET {path} -> {resp.status} {resp.status_text}")
        return resp.json()

    def get_raw(self, path, params=None):
        """Single GET returning the raw response (for file downloads, headers)."""
        return self._ctx.request.get(self._url(path, params))

    def paginate(self, path, params=None):
        """Follow Canvas Link headers, return concatenated list of items."""
        params = dict(params or {})
        params.setdefault("per_page", 100)
        url = self._url(path, params)
        items = []
        while url:
            resp = self._ctx.request.get(url)
            if not resp.ok:
                raise RuntimeError(f"GET {url} -> {resp.status}")
            chunk = resp.json()
            if not isinstance(chunk, list):
                raise RuntimeError(f"paginate expected list, got {type(chunk).__name__} from {url}")
            items.extend(chunk)
            url = None
            link = resp.headers.get("link", "")
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
                    break
        return items

    def current_term_courses(self, term_name):
        """Filter active enrollments by term name (e.g. '2025-26 Fall')."""
        all_courses = self.paginate("/api/v1/courses", {"include[]": "term"})
        return [
            c for c in all_courses
            if c.get("name")
            and c.get("workflow_state") == "available"
            and (c.get("term") or {}).get("name") == term_name
        ]

    def list_folders(self, course_id):
        """All folders in a course (flat list, includes parent_folder_id)."""
        return self.paginate(f"/api/v1/courses/{course_id}/folders")

    def list_files(self, course_id):
        return self.paginate(f"/api/v1/courses/{course_id}/files")

    def folder_tree(self, course_id):
        """Return (folders_by_id, files_by_folder_id, root_id).

        Each folder dict gets extra fields:
          _direct_files: list of file dicts directly in this folder
          _direct_size:  sum of those files' sizes (no recursion)
          _children:     list of child folder ids
        """
        folders = self.list_folders(course_id)
        files = self.list_files(course_id)

        folders_by_id = {f["id"]: f for f in folders}
        for f in folders:
            f["_direct_files"] = []
            f["_direct_size"] = 0
            f["_children"] = []

        files_by_folder = {}
        for fi in files:
            fid = fi.get("folder_id")
            files_by_folder.setdefault(fid, []).append(fi)
            if fid in folders_by_id:
                folders_by_id[fid]["_direct_files"].append(fi)
                folders_by_id[fid]["_direct_size"] += fi.get("size") or 0

        root_id = None
        for f in folders:
            pid = f.get("parent_folder_id")
            if pid and pid in folders_by_id:
                folders_by_id[pid]["_children"].append(f["id"])
            elif pid is None:
                root_id = f["id"]

        return folders_by_id, files_by_folder, root_id


CURRENT_TERM = "2025-26 Fall"
