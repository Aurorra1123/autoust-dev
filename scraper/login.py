"""First-time login: open a real browser, let the user complete SSO, auto-detect login, save storage_state.

We can't use input() because Bash here has no TTY stdin. Instead we poll the page:
once the user is authenticated, Canvas redirects to the dashboard at `/` (after going
through SSO), and `/api/v1/users/self` returns a JSON object with an `id` field.
We poll that endpoint every 2s and exit as soon as it succeeds.
"""
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

CANVAS_URL = "https://hkust-gz.instructure.com/"
WHOAMI_URL = "https://hkust-gz.instructure.com/api/v1/users/self"
AUTH_DIR = Path(__file__).parent.parent / ".auth"
STATE_FILE = AUTH_DIR / "canvas_state.json"
POLL_INTERVAL_S = 2
TIMEOUT_S = 600  # 10 minutes for the user to complete SSO


def main():
    AUTH_DIR.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(CANVAS_URL)
        print(f"\nBrowser opened at {CANVAS_URL}", flush=True)
        print("Complete SSO login in the browser window.", flush=True)
        print("Script will auto-detect login completion (polling every 2s, timeout 10min).", flush=True)

        start = time.time()
        user = None
        while time.time() - start < TIMEOUT_S:
            try:
                resp = context.request.get(WHOAMI_URL)
                if resp.ok:
                    data = resp.json()
                    if isinstance(data, dict) and data.get("id"):
                        user = data
                        break
            except Exception:
                pass
            time.sleep(POLL_INTERVAL_S)

        if not user:
            print(f"ERROR: login not detected within {TIMEOUT_S}s.", file=sys.stderr)
            browser.close()
            sys.exit(1)

        print(f"Login detected: {user.get('name')} (id={user.get('id')})", flush=True)
        context.storage_state(path=str(STATE_FILE))
        print(f"Saved storage_state to {STATE_FILE}", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
