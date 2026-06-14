# Generic Canvas Instance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make AutoStudy usable by a single local user from any Canvas LMS school by moving Canvas instance configuration into `canvascli` and updating AutoStudy to consume that contract.

**Architecture:** `canvascli` becomes the source of truth for `web_base` and `api_base`; AutoStudy asks the user for school/domain/Canvas URL and passes the selected URL to `canvascli init --canvas-url`. AutoStudy docs and scripts stop assuming HKUST(GZ), while historical validation examples remain allowed.

**Tech Stack:** Python 3.9+, Typer, requests, Playwright, stdlib `unittest`, Markdown docs, JSON backlog.

---

## File Structure

`/Users/deepwisdom/Desktop/project/canvascli`:

- Modify `canvascli/config.py`: add `CanvasInstanceConfig`, URL normalization, config persistence, and a test-safe config-dir override.
- Modify `canvascli/auth.py`: open configured `web_base` and poll configured `api_base`.
- Modify `canvascli/client.py`: route relative REST paths through the configured instance.
- Modify `canvascli/__main__.py`: add `init --canvas-url` and generic help text.
- Modify `canvascli/__init__.py`, `README.md`, `pyproject.toml`: remove HKUST(GZ)-only positioning.
- Create `tests/test_config.py`: offline URL/config tests.
- Create `tests/test_client_urls.py`: offline URL routing test.

`/Users/deepwisdom/Desktop/project/autoust`:

- Modify `scripts/select_plan_item.py`: stop fabricating HKUST(GZ) URLs.
- Modify `scripts/write_scan_plan.py`: preserve `html_url` in `plan.json`.
- Create `tests/test_select_plan_item.py`: offline selection tests.
- Create `tests/test_scan_plan_html_url.py`: offline scan-plan URL propagation test.
- Modify `sub-skills/tools/canvascli-setup.md`: first-run school/domain/URL flow.
- Modify `sub-skills/tools/canvascli-api.md`: document `init --canvas-url`.
- Modify `sub-skills/tasks/do-homework.md`: remove fixed HKUST(GZ) output URL template.
- Modify `skill.md`, `README.md`, `README.en.md`, `README.quick.md`, `docs/MARKETING.md`, `docs/ROADMAP.md`: generic Canvas LMS positioning with HKUST(GZ) validation note.
- Modify `docs/plans/feature-list.json` and `docs/progress/agent-progress.md`: record status/evidence.

## Task 1: canvascli Instance Config

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/config.py`
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `/Users/deepwisdom/Desktop/project/canvascli/tests/test_config.py`:

```python
import json
import os
import tempfile
import unittest
from pathlib import Path

from canvascli.config import (
    DEFAULT_WEB_BASE,
    CanvasInstanceConfig,
    instance_config_file,
    load_instance_config,
    normalize_canvas_url,
    save_instance_config,
)


class CanvasInstanceConfigTests(unittest.TestCase):
    def test_normalizes_canvas_cloud_web_url(self):
        config = normalize_canvas_url("school.instructure.com")
        self.assertEqual(config.web_base, "https://school.instructure.com")
        self.assertEqual(config.api_base, "https://school.instructure.com/api/v1")

    def test_normalizes_school_owned_web_url(self):
        config = normalize_canvas_url("https://canvas.example.edu/login/canvas?next=/")
        self.assertEqual(config.web_base, "https://canvas.example.edu")
        self.assertEqual(config.api_base, "https://canvas.example.edu/api/v1")

    def test_normalizes_api_root_url(self):
        config = normalize_canvas_url("https://canvas.example.edu/api/v1/courses")
        self.assertEqual(config.web_base, "https://canvas.example.edu")
        self.assertEqual(config.api_base, "https://canvas.example.edu/api/v1")

    def test_rejects_missing_host(self):
        with self.assertRaises(ValueError):
            normalize_canvas_url("not a url with spaces")

    def test_load_uses_compatibility_default_without_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("CANVASCLI_CONFIG_DIR")
            os.environ["CANVASCLI_CONFIG_DIR"] = tmp
            try:
                config = load_instance_config()
            finally:
                if old is None:
                    os.environ.pop("CANVASCLI_CONFIG_DIR", None)
                else:
                    os.environ["CANVASCLI_CONFIG_DIR"] = old
        self.assertEqual(config.web_base, DEFAULT_WEB_BASE)
        self.assertEqual(config.api_base, DEFAULT_WEB_BASE + "/api/v1")

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("CANVASCLI_CONFIG_DIR")
            os.environ["CANVASCLI_CONFIG_DIR"] = tmp
            try:
                save_instance_config(CanvasInstanceConfig(
                    web_base="https://canvas.example.edu",
                    api_base="https://canvas.example.edu/api/v1",
                ))
                self.assertEqual(instance_config_file(), Path(tmp) / "canvas_instance.json")
                raw = json.loads(instance_config_file().read_text(encoding="utf-8"))
                self.assertEqual(raw["web_base"], "https://canvas.example.edu")
                loaded = load_instance_config()
            finally:
                if old is None:
                    os.environ.pop("CANVASCLI_CONFIG_DIR", None)
                else:
                    os.environ["CANVASCLI_CONFIG_DIR"] = old
        self.assertEqual(loaded.api_base, "https://canvas.example.edu/api/v1")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: FAIL or ERROR because `CanvasInstanceConfig`, `normalize_canvas_url`,
`instance_config_file`, `load_instance_config`, and `save_instance_config` are
not defined yet.

- [ ] **Step 3: Implement config support**

Replace `/Users/deepwisdom/Desktop/project/canvascli/canvascli/config.py` with:

```python
"""Configuration constants and XDG-style paths."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import platform
from urllib.parse import urlparse

DEFAULT_WEB_BASE = "https://hkust-gz.instructure.com"


@dataclass(frozen=True)
class CanvasInstanceConfig:
    """Configured Canvas web and REST roots for this local installation."""

    web_base: str
    api_base: str


def config_dir() -> Path:
    """OS-appropriate config dir following XDG / Apple conventions."""
    override = os.environ.get("CANVASCLI_CONFIG_DIR")
    if override:
        d = Path(override).expanduser()
    elif platform.system() == "Darwin":
        d = Path.home() / "Library" / "Application Support" / "canvascli"
    elif platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        d = base / "canvascli"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        d = base / "canvascli"
    d.mkdir(parents=True, exist_ok=True)
    return d


def state_file() -> Path:
    """Path to the saved Canvas session cookie."""
    return config_dir() / "state.json"


def instance_config_file() -> Path:
    """Path to the saved Canvas instance configuration."""
    return config_dir() / "canvas_instance.json"


def _root_from_parsed(parsed) -> str:
    if not parsed.netloc:
        raise ValueError("Canvas URL must include a host")
    scheme = (parsed.scheme or "https").lower()
    if scheme not in {"http", "https"}:
        raise ValueError("Canvas URL must use http or https")
    host = parsed.netloc.lower()
    return f"{scheme}://{host}"


def normalize_canvas_url(raw: str) -> CanvasInstanceConfig:
    """Normalize a Canvas login URL or API URL into web/API roots."""
    value = raw.strip()
    if not value or any(ch.isspace() for ch in value):
        raise ValueError("Canvas URL must be a single URL or host")
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    web_base = _root_from_parsed(parsed).rstrip("/")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "api" and parts[1] == "v1":
        api_base = web_base + "/api/v1"
    else:
        api_base = web_base + "/api/v1"
    return CanvasInstanceConfig(web_base=web_base, api_base=api_base)


def load_instance_config() -> CanvasInstanceConfig:
    """Load configured Canvas instance, falling back to the legacy default."""
    path = instance_config_file()
    if not path.exists():
        return normalize_canvas_url(DEFAULT_WEB_BASE)
    data = json.loads(path.read_text(encoding="utf-8"))
    web_base = str(data.get("web_base") or "").rstrip("/")
    api_base = str(data.get("api_base") or "").rstrip("/")
    if not web_base:
        return normalize_canvas_url(DEFAULT_WEB_BASE)
    if not api_base:
        api_base = web_base + "/api/v1"
    return CanvasInstanceConfig(web_base=web_base, api_base=api_base)


def save_instance_config(config: CanvasInstanceConfig) -> None:
    """Persist Canvas instance config."""
    instance_config_file().write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# Backward-compatible constant for older imports. New code should call
# load_instance_config() so tests and future commands can control the instance.
CANVAS_URL = load_instance_config().web_base
```

- [ ] **Step 4: Run config tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
python3 -m unittest discover -s tests -p 'test_config.py'
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add canvascli/config.py tests/test_config.py
git commit -m "feat: add Canvas instance configuration"
```

## Task 2: canvascli Login and Client Routing

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/auth.py`
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/client.py`
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`
- Create: `/Users/deepwisdom/Desktop/project/canvascli/tests/test_client_urls.py`

- [ ] **Step 1: Write failing URL routing tests**

Create `/Users/deepwisdom/Desktop/project/canvascli/tests/test_client_urls.py`:

```python
import json
import os
import tempfile
import unittest

from canvascli.client import CanvasClient
from canvascli.config import CanvasInstanceConfig, save_instance_config, state_file


class CanvasClientUrlTests(unittest.TestCase):
    def test_routes_canvas_api_paths_through_configured_web_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("CANVASCLI_CONFIG_DIR")
            os.environ["CANVASCLI_CONFIG_DIR"] = tmp
            try:
                save_instance_config(CanvasInstanceConfig(
                    web_base="https://canvas.example.edu",
                    api_base="https://canvas.example.edu/api/v1",
                ))
                state_file().write_text(json.dumps({"cookies": []}), encoding="utf-8")
                client = CanvasClient()
                self.assertEqual(
                    client._url("/api/v1/users/self"),
                    "https://canvas.example.edu/api/v1/users/self",
                )
                self.assertEqual(
                    client._url("/courses"),
                    "https://canvas.example.edu/api/v1/courses",
                )
                self.assertEqual(
                    client._url("https://files.example.edu/download"),
                    "https://files.example.edu/download",
                )
            finally:
                if old is None:
                    os.environ.pop("CANVASCLI_CONFIG_DIR", None)
                else:
                    os.environ["CANVASCLI_CONFIG_DIR"] = old
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
python3 -m unittest discover -s tests -p 'test_client_urls.py'
```

Expected: FAIL because `CanvasClient._url()` still uses the legacy
`CANVAS_URL` constant.

- [ ] **Step 3: Update auth login**

Edit `/Users/deepwisdom/Desktop/project/canvascli/canvascli/auth.py` so imports
and `login()` look like:

```python
import sys
import time
from playwright.sync_api import sync_playwright

from .config import load_instance_config, normalize_canvas_url, save_instance_config, state_file

POLL_INTERVAL_S = 2
TIMEOUT_S = 600


def login(canvas_url: str | None = None) -> dict:
    """Open a browser, wait for the user to complete SSO, save cookies."""
    if canvas_url:
        config = normalize_canvas_url(canvas_url)
        save_instance_config(config)
    else:
        config = load_instance_config()

    state_path = state_file()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    whoami_url = config.api_base + "/users/self"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(config.web_base + "/")

        print(f"Browser opened at {config.web_base}", file=sys.stderr, flush=True)
        print("Complete SSO login in the browser window.", file=sys.stderr, flush=True)
        print(
            "If the SSO page offers 'Remember login' / 'Trust this browser', "
            "select it to make future re-logins faster.",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"Polling {whoami_url} every {POLL_INTERVAL_S}s "
            f"(timeout {TIMEOUT_S}s)...",
            file=sys.stderr,
            flush=True,
        )

        start = time.time()
        user = None
        while time.time() - start < TIMEOUT_S:
            try:
                resp = context.request.get(whoami_url)
                if resp.ok:
                    data = resp.json()
                    if isinstance(data, dict) and data.get("id"):
                        user = data
                        break
            except Exception:
                pass
            time.sleep(POLL_INTERVAL_S)

        if not user:
            browser.close()
            raise RuntimeError(f"login not detected within {TIMEOUT_S}s")

        context.storage_state(path=str(state_path))
        browser.close()
        return user
```

- [ ] **Step 4: Update client URL routing**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/client.py`:

1. Replace `from .config import CANVAS_URL, state_file` with:

```python
from .config import load_instance_config, state_file
```

2. Add this line in `CanvasClient.__init__` before the state-path check:

```python
self._instance = load_instance_config()
```

3. Replace `_url()` with:

```python
def _url(self, path: str, params: dict | None = None) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    elif path.startswith("/api/v1"):
        url = self._instance.web_base + path
    elif path.startswith("/"):
        url = self._instance.api_base + path
    else:
        url = path
    if params:
        sep = "&" if "?" in url else "?"
        url += sep + urlencode(params, doseq=True)
    return url
```

- [ ] **Step 5: Add CLI option**

In `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__main__.py`:

1. Change Typer help text to:

```python
help="Canvas LMS command-line client.",
```

2. Change `init()` to:

```python
@app.command()
def init(
    canvas_url: Optional[str] = typer.Option(
        None,
        "--canvas-url",
        help="Canvas login URL or Canvas API root for this installation.",
    ),
) -> None:
    """One-time SSO login. Opens a browser window."""
    from .auth import login
    try:
        user = login(canvas_url=canvas_url)
    except Exception as e:
        typer.echo(f"login failed: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"logged in as {user.get('name')} (id={user.get('id')})", err=True)
    typer.echo(f"session saved to {state_file()}", err=True)
```

- [ ] **Step 6: Run tests and help check**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m compileall canvascli
.venv/bin/canvascli init --help
```

Expected: tests pass, compile succeeds, help includes `--canvas-url`.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add canvascli/auth.py canvascli/client.py canvascli/__main__.py tests/test_client_urls.py
git commit -m "feat: route Canvas requests through configured instance"
```

## Task 3: canvascli Docs and Metadata

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/canvascli/__init__.py`
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/README.md`
- Modify: `/Users/deepwisdom/Desktop/project/canvascli/pyproject.toml`

- [ ] **Step 1: Update package copy**

Change HKUST(GZ)-only wording to generic Canvas LMS wording:

```text
Canvas LMS command-line client with browser-based SSO login, persistent cookie
storage, and JSON-by-default output.
```

Keep a compatibility note in README:

```text
The legacy default instance remains https://hkust-gz.instructure.com so existing
AutoStudy users keep working until they configure another Canvas URL with a
command such as canvascli init --canvas-url https://canvas.example.edu.
```

- [ ] **Step 2: Verify no active HKUST-only scope remains**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
rg -n "HKUST\\(GZ\\) only|Hard-coded for HKUST|Multi-instance support not in scope|client for HKUST" .
```

Expected: no matches. Historical compatibility mentions of HKUST(GZ) are
acceptable when they explicitly say "legacy default" or "validated".

- [ ] **Step 3: Commit Task 3**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
git add canvascli/__init__.py README.md pyproject.toml
git commit -m "docs: describe canvascli as generic Canvas LMS client"
```

## Task 4: AutoStudy Plan Handoff URL Safety

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/autoust/scripts/select_plan_item.py`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/scripts/write_scan_plan.py`
- Create: `/Users/deepwisdom/Desktop/project/autoust/tests/test_select_plan_item.py`
- Create: `/Users/deepwisdom/Desktop/project/autoust/tests/test_scan_plan_html_url.py`

- [ ] **Step 1: Write failing selection tests**

Create `/Users/deepwisdom/Desktop/project/autoust/tests/test_select_plan_item.py`:

```python
import unittest

from scripts.select_plan_item import build_selection


class SelectPlanItemTests(unittest.TestCase):
    def test_missing_html_url_stays_null(self):
        plan_item = {
            "index": 1,
            "course_id": 12,
            "assignment_id": 34,
            "assignment_name": "Essay",
            "suggested_next_step": "recon",
        }
        result = build_selection("2026-06-14", plan_item, None)
        self.assertIsNone(result["canvas_url"])

    def test_existing_html_url_is_preserved(self):
        plan_item = {
            "index": 1,
            "course_id": 12,
            "assignment_id": 34,
            "html_url": "https://canvas.example.edu/courses/12/assignments/34",
        }
        result = build_selection("2026-06-14", plan_item, None)
        self.assertEqual(
            result["canvas_url"],
            "https://canvas.example.edu/courses/12/assignments/34",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: FAIL because the script currently fabricates an HKUST(GZ) URL.

- [ ] **Step 3: Write failing scan-plan propagation test**

Create `/Users/deepwisdom/Desktop/project/autoust/tests/test_scan_plan_html_url.py`:

```python
import unittest

from scripts.write_scan_plan import build_plan


class ScanPlanHtmlUrlTests(unittest.TestCase):
    def test_plan_items_preserve_html_url(self):
        pending = [
            {
                "bucket": "upcoming",
                "recommended_action": "recon",
                "course": "GEN101",
                "course_id": 12,
                "course_name": "General Course",
                "assignment_id": 34,
                "assignment_name": "Essay",
                "due_at": None,
                "due_at_local": None,
                "hours_left": None,
                "submission_state": "unsubmitted",
                "existing_result_status": None,
                "existing_result_path": None,
                "reason": "needs reconnaissance",
                "html_url": "https://canvas.example.edu/courses/12/assignments/34",
            }
        ]
        plan = build_plan(pending)
        self.assertEqual(
            plan["items"][0]["html_url"],
            "https://canvas.example.edu/courses/12/assignments/34",
        )
```

- [ ] **Step 4: Run scan-plan test to verify it fails**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
python3 -m unittest tests.test_scan_plan_html_url -v
```

Expected: FAIL because `build_plan()` does not include `html_url`.

- [ ] **Step 5: Preserve html_url in plan items**

In `/Users/deepwisdom/Desktop/project/autoust/scripts/write_scan_plan.py`, add
this field inside the item dict built by `build_plan()`:

```python
"html_url": item.get("html_url"),
```

Place it near the assignment identity fields:

```python
"assignment_id": item["assignment_id"],
"assignment_name": item["assignment_name"],
"html_url": item.get("html_url"),
"due_at": item["due_at"],
```

- [ ] **Step 6: Remove fabricated fallback**

In `/Users/deepwisdom/Desktop/project/autoust/scripts/select_plan_item.py`,
replace:

```python
canvas_url = merged.get("html_url")
if not canvas_url:
    canvas_url = f"https://hkust-gz.instructure.com/courses/{cid}/assignments/{aid}"
```

with:

```python
canvas_url = merged.get("html_url") or None
```

- [ ] **Step 7: Run tests**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
python3 -m unittest tests.test_select_plan_item tests.test_scan_plan_html_url -v
python3 -m compileall scripts/select_plan_item.py
python3 -m compileall scripts/write_scan_plan.py
```

Expected: PASS.

- [ ] **Step 8: Commit Task 4**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
git add scripts/select_plan_item.py scripts/write_scan_plan.py tests/test_select_plan_item.py tests/test_scan_plan_html_url.py
git commit -m "fix: preserve Canvas URLs in plan handoff"
```

## Task 5: AutoStudy Setup and API Contract Docs

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/autoust/sub-skills/tools/canvascli-setup.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/sub-skills/tools/canvascli-api.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/sub-skills/tasks/do-homework.md`

- [ ] **Step 1: Update setup flow**

In `canvascli-setup.md`, replace the HKUST(GZ)-only Step 3 text with a first-run
branch that says:

```markdown
## Step 3: Configure Canvas instance and log in

If `.venv/bin/canvascli whoami` already works, do not ask for school or URL.

If there is no saved session yet, ask the user one question:

> 你在哪个学校用 Canvas？学校名、域名，或者 Canvas 登录页网址都行。

If the answer is a Canvas-looking URL, normalize it mentally and run:

```bash
.venv/bin/canvascli init --canvas-url "https://canvas.example.edu"
```

If the answer is a school name or domain, search for `<school> Canvas login`.
Prefer hosts shaped like `canvas.<domain>`, `<school>.instructure.com`, or other
Canvas login pages. If the result is clear, run `init --canvas-url` with that
URL. If it is unclear, ask for the direct Canvas login page URL.

For an expired session on an already configured instance, run:

```bash
.venv/bin/canvascli init
```
```

Also replace the pitfall `HKUST(GZ) only` with:

```markdown
5. **Single configured Canvas instance.** This slice supports one Canvas
   instance per local installation. To change schools, run
   `canvascli init --canvas-url <new-url>` and complete browser login again.
```

- [ ] **Step 2: Update API reference**

Add this under `init` in `canvascli-api.md`:

```markdown
Fresh setup can configure the Canvas instance and login in one command:

```bash
.venv/bin/canvascli init --canvas-url "https://canvas.example.edu"
.venv/bin/canvascli init --canvas-url "https://school.instructure.com/api/v1"
```

`canvascli` stores the normalized web/API roots outside the repo next to the
session cookie. AutoStudy should use Canvas JSON fields such as `html_url` when
it needs a browser link; it should not reconstruct school-specific URLs.
```

- [ ] **Step 3: Update do-homework output template**

In `sub-skills/tasks/do-homework.md`, add this sentence before the output
example:

```markdown
Use the selected plan item's `canvas_url` or `canvas/assignment.json.html_url`;
never reconstruct a host-specific Canvas URL from course and assignment IDs.
```

Then replace:

```markdown
**Canvas URL:** https://hkust-gz.instructure.com/courses/.../assignments/...
```

with:

```markdown
**Canvas URL:** <assignment html_url, or "not available" if Canvas did not provide one>
```

- [ ] **Step 4: Verify setup docs no longer claim HKUST-only**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
rg -n "HKUST\\(GZ\\) only|hardcodes `hkust-gz|Opening browser at https://hkust-gz|https://hkust-gz.instructure.com/courses/\\.\\.\\./assignments" sub-skills/tools/canvascli-setup.md sub-skills/tools/canvascli-api.md sub-skills/tasks/do-homework.md
```

Expected: no matches.

- [ ] **Step 5: Commit Task 5**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
git add sub-skills/tools/canvascli-setup.md sub-skills/tools/canvascli-api.md sub-skills/tasks/do-homework.md
git commit -m "docs: add generic Canvas setup contract"
```

## Task 6: AutoStudy Public Positioning

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/autoust/skill.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/README.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/README.en.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/README.quick.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/docs/MARKETING.md`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/docs/ROADMAP.md`

- [ ] **Step 1: Replace active HKUST-only product copy**

Use this pattern for current product descriptions:

```text
AutoStudy is a local Canvas LMS study assistant, validated on HKUST(GZ)'s Canvas
instance.
```

Chinese equivalent:

```text
AutoStudy 是本地 Canvas LMS 学业助手，已在 HKUST(GZ) 的 Canvas 实例上验证。
```

Do not rewrite historical validation entries that intentionally name real
HKUST(GZ) test assignments.

- [ ] **Step 2: Search for active HKUST-only wording**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
rg -n "HKUST\\(GZ\\) Canvas 本地学业助手|HKUST\\(GZ\\) Canvas study|Canvas \\(`hkust-gz\\.instructure\\.com`\\)|HKUST\\(GZ\\) SSO" skill.md README.md README.en.md README.quick.md docs/MARKETING.md docs/ROADMAP.md
```

Expected: no matches in active setup/product copy. Historical validation
sections may still mention HKUST(GZ) when the wording is clearly about evidence.

- [ ] **Step 3: Commit Task 6**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
git add skill.md README.md README.en.md README.quick.md docs/MARKETING.md docs/ROADMAP.md
git commit -m "docs: position AutoStudy as generic Canvas assistant"
```

## Task 7: Cross-Repo Verification and Backlog Sync

**Files:**
- Modify: `/Users/deepwisdom/Desktop/project/autoust/docs/plans/feature-list.json`
- Modify: `/Users/deepwisdom/Desktop/project/autoust/docs/progress/agent-progress.md`

- [ ] **Step 1: Run canvascli verification**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/canvascli
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m compileall canvascli
.venv/bin/canvascli init --help
git diff --check
```

Expected: tests pass, compile succeeds, help includes `--canvas-url`, diff check
has no whitespace errors.

- [ ] **Step 2: Run AutoStudy verification**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m json.tool docs/plans/feature-list.json >/dev/null
python3 -m compileall scripts/select_plan_item.py scripts/write_scan_plan.py
git diff --check
```

Expected: tests pass, JSON parses, compile succeeds, diff check has no
whitespace errors.

- [ ] **Step 3: Update feature-list evidence**

Capture the short commit ids first:

```bash
canvascli_commit=$(git -C /Users/deepwisdom/Desktop/project/canvascli log -1 --format=%h)
autostudy_commit=$(git -C /Users/deepwisdom/Desktop/project/autoust log -1 --format=%h)
printf '%s\n' "$canvascli_commit" "$autostudy_commit"
```

Then update the generic Canvas feature entry in `docs/plans/feature-list.json`.
Set `status` to `passing`. Set `evidence` to three strings built exactly like
this, using the two command outputs:

```text
"canvascli commit " + canvascli_commit + ": configurable Canvas instance with URL normalization tests"
"AutoStudy commit " + autostudy_commit + ": setup/API docs, scan-plan URL propagation, do-homework URL template, and select_plan_item tests"
Verification: canvascli unittest/compile/help/diff-check; AutoStudy unittest/json/compile/diff-check
```

- [ ] **Step 4: Update progress note**

Add a top entry to `docs/progress/agent-progress.md`:

```markdown
## 2026-06-14 — Generic Canvas instance support implemented

Implemented the first generic Canvas instance slice across `canvascli` and
AutoStudy: `canvascli init --canvas-url` now stores a web/API base pair,
AutoStudy setup docs ask for school/domain/Canvas URL, and plan selection no
longer fabricates HKUST(GZ) links. Verification passed for canvascli unit tests,
compile/help checks, AutoStudy selection tests, JSON syntax, and diff checks.
```

- [ ] **Step 5: Commit Task 7**

Run:

```bash
cd /Users/deepwisdom/Desktop/project/autoust
git add docs/plans/feature-list.json docs/progress/agent-progress.md
git commit -m "docs: record generic Canvas instance verification"
```

## Final Review

- [ ] Confirm both repos are on `codex/deepwisdom-updates`.
- [ ] Confirm `git status --short --branch` in both repos has no unexpected
  uncommitted files except user-owned local files such as `.DS_Store`.
- [ ] Confirm commit order is `canvascli` data-layer commits first, then
  AutoStudy application/docs commits.
- [ ] Summarize exact verification commands and results for the user.
