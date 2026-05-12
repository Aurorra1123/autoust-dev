---
name: scraper-setup
description: One-time setup for the Canvas scraper (venv, playwright, SSO login). Use when scraper hasn't been initialized yet, or when login cookies have expired.
---

# Scraper Setup

The Canvas scraper is a Python package (`scraper/`) that talks to the HKUST(GZ) Canvas REST API using a Playwright-saved session cookie. This skill installs it and walks the user through first-time login.

## When to run this

- First time using AutoStudy in a fresh clone
- `.auth/canvas_state.json` doesn't exist
- Any scraper command returns `401 Unauthorized` (cookie expired)

## Step 1: Create venv + install dependencies

Check the user's environment first:

```bash
which python3
ls .venv 2>/dev/null
```

If `.venv/` doesn't exist:

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install playwright
```

Then install the browser. **Mainland China users likely need a proxy** — if the user has mentioned a local proxy (e.g. `127.0.0.1:6666`), use it:

```bash
# With proxy:
export http_proxy=http://127.0.0.1:6666 https_proxy=http://127.0.0.1:6666 \
       HTTP_PROXY=http://127.0.0.1:6666 HTTPS_PROXY=http://127.0.0.1:6666
.venv/bin/playwright install chromium

# Without proxy (may be slow):
.venv/bin/playwright install chromium
```

**Important**: install `chromium` (not just headless shell). The login flow needs a real browser window. Verify both exist:

```bash
ls ~/Library/Caches/ms-playwright/   # should show chromium-XXX (not just chromium_headless_shell-XXX)
```

## Step 2: First-time SSO login

The user has to log in once through the school SSO. The script polls `/api/v1/users/self` every 2s and saves the cookie automatically — no Enter-key needed.

Tell the user to run this in their **own terminal** (not via Claude Code's `!` prefix — that has no TTY for the browser):

```bash
.venv/bin/python -m scraper.login
```

What they'll see:
1. A Chromium window opens to `https://hkust-gz.instructure.com/`
2. They complete SSO in the browser
3. Script auto-detects login (polling `/api/v1/users/self`)
4. Saves `.auth/canvas_state.json`, closes browser
5. Prints `Login detected: <Name> (id=<uid>)` and `Saved storage_state to ...`

## Step 3: Verify

```bash
.venv/bin/python -m scraper.fetch_courses 2>&1 | head -10
```

Should print `Logged in as: <name>` followed by the current-term course list.

## Cookie expiration handling

When a fetch command fails with `401`:
- Tell the user "your Canvas session has expired"
- Re-run Step 2
- Do NOT silently retry or attempt to refresh — cookies are tied to SAML assertions that must be re-issued by the school IdP

## Files this skill creates

| Path | Purpose | Sensitive? |
|---|---|---|
| `.venv/` | Python virtualenv | No |
| `.auth/canvas_state.json` | Canvas session cookie | **YES — never commit, never log** |
| `~/Library/Caches/ms-playwright/` | Chromium binary | No |

`.gitignore` already excludes `.venv/`, `.auth/`, `data/`.

## Pitfalls (already burned, do not retry)

These are documented in `PITFALLS.md`. Quick reference:

- **Don't use `input()` for "press enter to continue"** — Claude Code's `!` bash has no TTY, it'll `EOFError` immediately. The login script uses polling instead.
- **Don't fall back to `/dev/tty`** — Claude Code shells return `OSError: Device not configured`.
- **Don't install `chromium --headless-shell` alone** — login needs a real browser window.
- **Don't pass `enrollment_state=active`** to Canvas API — returns 0 courses on HKUST(GZ). Filter client-side by `workflow_state == "available"` + term name.
