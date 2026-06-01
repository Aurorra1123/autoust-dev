---
name: canvascli-setup
description: Bootstrap canvascli (the Canvas LMS CLI AutoStudy depends on) and walk the user through one-time SSO. Run this when canvascli is missing or when a saved session has expired.
---

# canvascli setup

AutoStudy talks to Canvas through [`canvascli`](https://github.com/Aurorra1123/canvascli) — a separate open-source Python CLI. This skill installs canvascli into AutoStudy's local venv and gets the user logged in.

**This skill is meant to be executed by the agent**, not read by the user. Each step is a concrete shell action; only Step 3 (`canvascli init`) requires the user to do something themselves (interact with the SSO browser window).

## When to run this

Invoke this skill if any of the following is true:

- A fresh clone of AutoStudy (no `.venv/` yet)
- `which canvascli` and `.venv/bin/canvascli version` both fail
- Any `canvascli` call returns "Canvas session expired" or HTTP 401 → jump to **Step 3** only

## Step 0: Detect what's missing

Run this first so you know which steps to skip:

```bash
test -d .venv && echo "venv: ok" || echo "venv: MISSING"
.venv/bin/canvascli version 2>/dev/null && echo "canvascli: ok" || echo "canvascli: MISSING"
.venv/bin/canvascli whoami >/dev/null 2>&1 && echo "session: ok" || echo "session: MISSING"
```

Branch:

- All three `ok` → setup is already done, return to the calling task.
- `venv: MISSING` → start at Step 1.
- `canvascli: MISSING` → start at Step 2.
- `session: MISSING` only → jump to Step 3.

## Step 1: Create AutoStudy's venv

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
```

That's it. Python 3.9+ is required; macOS/Linux ship with one.

## Step 2: Install canvascli + Chromium

One pip command pulls canvascli straight from GitHub. Playwright is a transitive dep; Chromium needs a separate one-shot install.

```bash
.venv/bin/pip install "git+https://github.com/Aurorra1123/canvascli" --quiet
.venv/bin/playwright install chromium
```

**Verify:**

```bash
.venv/bin/canvascli version    # should print "canvascli 0.1.0" or higher
```

### If `pip install` or `playwright install` is slow (Mainland China)

Try the Tsinghua PyPI mirror for pip:

```bash
.venv/bin/pip install "git+https://github.com/Aurorra1123/canvascli" \
    -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
```

For Chromium, set an HTTP proxy before `playwright install` (replace with whatever proxy the user actually has):

```bash
export http_proxy=http://127.0.0.1:6666 https_proxy=http://127.0.0.1:6666 \
       HTTP_PROXY=http://127.0.0.1:6666 HTTPS_PROXY=http://127.0.0.1:6666
.venv/bin/playwright install chromium
```

### Pitfall: `chromium_headless_shell` is not enough

`playwright install chromium` may install only `chromium_headless_shell`, which can't pop a real window for SSO. If `canvascli init` later complains about a missing browser, re-run:

```bash
.venv/bin/playwright install chromium --with-deps
```

This installs the full headed Chromium build alongside the headless one.

## Step 3: One-time SSO login

`canvascli init` launches a real browser, waits for the user to complete HKUST(GZ) SSO, and saves a cookie. **This is an explicit login/refresh command, not a health check.** To check whether the current saved session already works, run `canvascli whoami`; do not run `init` just to "try logging in".

This step needs a real terminal — Claude Code's `!` bash channel has no TTY — but `init` doesn't use `input()` (it polls), so you can still launch it from the agent. The user just has to be at their keyboard when the browser pops.

Before launching:

```
✋ The next command opens a Chromium window for HKUST(GZ) SSO.
   Complete the login in that window — it auto-detects success and closes itself.
   If the SSO page offers "remember login" or "trust this browser", select it.
```

The remember-login checkbox is separate from `state.json`: a successful `init`
creates `state.json` either way, but selecting the checkbox lets the school's
SSO remember this browser for the next re-login. If the user skips it, today's
`state.json` can still work, but the next `init` after expiration may require a
full manual login again.

Then:

```bash
.venv/bin/canvascli init
```

What you'll see in stderr:

- `Opening browser at https://hkust-gz.instructure.com/ ...`
- (user finishes SSO in the window)
- `logged in as <Name> (id=<uid>)`
- `session saved to ~/Library/Application Support/canvascli/state.json`

The cookie lives outside the repo, in the user's OS-standard config dir (`~/Library/Application Support/canvascli/` on macOS, `~/.config/canvascli/` on Linux), so it can never accidentally leak into a git commit.

## Step 4: Verify

```bash
.venv/bin/canvascli whoami --pretty
```

Should print the user's Canvas profile. Interpret failures carefully:

- `No saved session` means `state.json` is missing or was never written.
- HTTP 401 / "session expired" means `state.json` exists but Canvas no longer accepts it.
- Network or SSL errors are not login failures; retry the command or check proxy/network first.

For the first two cases, re-run Step 3. For network/SSL errors, do not ask the user to re-login unless a retry proves the saved session is actually rejected.

Once `whoami` is happy, return to the calling task.

## Cookie expiration

When `canvascli` returns "Canvas session expired" or HTTP 401:

1. Tell the user: "Your Canvas session has expired — I'll re-run the login."
2. Jump straight to **Step 3**.
3. **Never silently retry** — Canvas cookies expire when the school's SAML assertion does, and only a fresh SSO can re-issue them.
4. During re-login, remind the user to select "remember login" / "trust this browser" if the SSO page offers it.

## Files this skill creates

| Path | Purpose | Sensitive? |
|---|---|---|
| `.venv/` (in the AutoStudy working dir) | Python virtualenv | No |
| `~/Library/Caches/ms-playwright/` (macOS) | Chromium binary | No |
| `~/Library/Application Support/canvascli/state.json` (macOS)<br>or `~/.config/canvascli/state.json` (Linux) | Canvas session cookie | **YES — never echo, never commit** |

`.gitignore` already excludes `.venv/`, and the cookie lives outside the repo, so neither can leak into git.

## Pitfalls

1. **Don't `pip install -e` a clone.** That was the old developer flow. End users install from GitHub directly via `pip install "git+https://github.com/Aurorra1123/canvascli"` — no clone needed, no path assumptions.
2. **Don't drive `canvascli init` non-interactively.** The user must actually be at their machine to complete SSO; the `init` command can't be automated end-to-end.
3. **Don't use `canvascli init` as a status check.** It always opens a browser. Use `canvascli whoami` to verify the existing `state.json`.
4. **Remember login is not `state.json`.** `state.json` is the Canvas API cookie saved by canvascli; the SSO remember-login checkbox only affects how much manual work the next SSO refresh needs.
5. **HKUST(GZ) only.** canvascli hardcodes `hkust-gz.instructure.com`. Multi-instance support is explicitly out of scope.
6. **Treat HTTP 404 from canvascli as "feature disabled"**, not as an error. Some HKUST(GZ) courses turn off Quizzes / Modules / Discussions; canvascli returns empty arrays in that case.
