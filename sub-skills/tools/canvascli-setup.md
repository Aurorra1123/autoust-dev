---
name: canvascli-setup
description: One-time setup for canvascli, the Canvas LMS command-line client AutoStudy depends on. Use when canvascli isn't installed, or when the saved session has expired.
---

# canvascli setup

AutoStudy talks to Canvas through [`canvascli`](https://github.com/Aurorra1123/canvascli), an external command-line tool. It's a separate git repository so it can be reused by other agents (Codex, Kimi Code, anything that shells out).

This skill installs canvascli and walks the user through one-time SSO login.

## When to run this

- First time using AutoStudy in a fresh clone
- `canvascli --version` is "command not found"
- Any `canvascli` call returns "Canvas session expired" or HTTP 401

## Step 1: Clone canvascli + install in the AutoStudy venv

```bash
# 1. Clone the canvascli repo somewhere predictable
git clone https://github.com/Aurorra1123/canvascli.git ~/workspace/canvascli

# 2. Create AutoStudy's venv if it doesn't exist
test -d .venv || python3 -m venv .venv

# 3. Install canvascli (editable) into AutoStudy's venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ~/workspace/canvascli
```

After installation, `canvascli` is on PATH for any process started inside that venv. Test it:

```bash
.venv/bin/canvascli version
.venv/bin/canvascli --help
```

**Note**: `canvascli` uses `version` as a subcommand (not `--version` flag), following typer convention.

## Step 2: Install Chromium for the SSO login flow

canvascli's `init` command launches a real browser to handle SSO. It depends on Playwright; Chromium needs to be installed once:

```bash
.venv/bin/pip install playwright    # if not already pulled in as dependency
.venv/bin/playwright install chromium
```

**If pulls are slow** (Mainland China), set HTTP proxy env vars before `playwright install`:

```bash
export http_proxy=http://127.0.0.1:6666 https_proxy=http://127.0.0.1:6666 \
       HTTP_PROXY=http://127.0.0.1:6666 HTTPS_PROXY=http://127.0.0.1:6666
.venv/bin/playwright install chromium
```

## Step 3: One-time SSO login

Run this in your **own terminal** (not via Claude Code's `!` prefix — `init` opens a browser and that needs a real TTY environment):

```bash
.venv/bin/canvascli init
```

What happens:
1. Chromium opens to `https://hkust-gz.instructure.com/`
2. You complete SSO
3. Script polls `/api/v1/users/self` every 2s, auto-detects login
4. Saves cookie to `~/Library/Application Support/canvascli/state.json` (macOS) or `~/.config/canvascli/state.json` (Linux)
5. Closes the browser

You should see (in stderr): `logged in as <Your Name> (id=<uid>)` and `session saved to <path>`.

## Step 4: Verify

```bash
.venv/bin/canvascli whoami --pretty
```

Should print your Canvas user info as JSON. If you see "No saved session" — Step 3 didn't succeed; re-run it.

## Cookie expiration

When a `canvascli` call fails with "Canvas session expired" or HTTP 401:

- Tell the user "your Canvas session has expired"
- Re-run Step 3
- **Do NOT silently retry or attempt to refresh.** Canvas cookies expire when the SAML assertion at the school IdP expires; only a new SSO can re-issue them.

## Files this skill creates

| Path | Purpose | Sensitive? |
|---|---|---|
| `~/workspace/canvascli/` | Source of the CLI tool | No (public repo) |
| `.venv/` | Python virtualenv for AutoStudy | No |
| `~/Library/Application Support/canvascli/state.json` | Canvas session cookie | **YES — never log, never commit** |
| `~/Library/Caches/ms-playwright/` | Chromium binary | No |

AutoStudy's `.gitignore` already excludes `.venv/`. The cookie lives outside the repo (in the user's home Application Support dir), so it can never accidentally leak into git.

## Pitfalls

1. **Don't run `canvascli init` from Claude Code's `!` bash channel.** That bash has no TTY (`/dev/tty` returns "Device not configured"), but `init` is fine because it uses Playwright polling instead of `input()`. However: the browser window still needs the user to interact, so the user runs `init` themselves in their terminal — the agent doesn't drive `init`.
2. **Don't use `enrollment_state=active`** — canvascli already filters client-side by term name.
3. **Treat HTTP 404 as "feature disabled".** Some courses turn off Quizzes / Modules / Discussions; canvascli returns empty arrays rather than failing.

## What's not covered here

- Multi-instance Canvas support (e.g. HKUST main campus, overseas) — explicitly out of scope; canvascli hardcodes `hkust-gz.instructure.com` for now.
- Token-based API auth (Canvas does support personal access tokens but we use cookie SSO instead).
