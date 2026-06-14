# Generic Canvas Instance Support Design

## Status

Approved direction from the pasted handoff: support Canvas users beyond
HKUST(GZ) by following Canvas Copilot's first-run strategy, while keeping
AutoStudy's layer boundary intact.

This design is ready for implementation planning. It covers one Canvas instance
per local user installation. Multi-profile and simultaneous multi-school
switching are intentionally out of scope for this slice.

## Problem

AutoStudy presents itself and behaves as an HKUST(GZ)-only assistant in several
places:

- `canvascli` hardcodes `https://hkust-gz.instructure.com` as the Canvas origin.
- `canvascli init`, `CanvasClient`, and generated help text assume that origin.
- AutoStudy setup docs tell agents that `canvascli` is HKUST(GZ)-only.
- `scripts/select_plan_item.py` manufactures an HKUST(GZ) assignment URL when
  `html_url` is missing.
- `scripts/write_scan_plan.py` preserves `html_url` in `pending_assignments.json`
  but drops it from `plan.json`, increasing the chance that selection code has
  to guess.
- `sub-skills/tasks/do-homework.md` shows a fixed HKUST(GZ) Canvas URL in its
  output template.
- User-facing README and `skill.md` copy describe AutoStudy as an HKUST(GZ)
  product rather than a generic Canvas LMS assistant validated on HKUST(GZ).

Changing only AutoStudy's wording would be false generalization. The real
Canvas access contract lives in `canvascli`, so the data layer must support a
configurable Canvas instance first.

## References

### Canvas Copilot

Canvas Copilot's `canvas-setup` flow is the model for first-run behavior:

1. Ask for the school or domain.
2. Try to discover a Canvas login URL from that school identifier.
3. Accept a direct Canvas login URL when discovery fails.
4. Normalize the web login root and API root separately:
   - `CANVAS_WEB_BASE`, such as `https://canvas.example.edu`
   - `CANVAS_BASE`, such as `https://canvas.example.edu/api/v1`
5. Open the web base for browser login and use the API base for REST calls.

AutoStudy should borrow the URL model and first-run interaction, not Canvas
Copilot's turnkey batch automation posture.

### AutoStudy / canvascli Boundary

`docs/COLLABORATION.md` defines `canvascli` as the Canvas data layer. Therefore:

- URL normalization, login origin, API origin, saved session paths, and CLI
  output contracts belong in `canvascli`.
- AutoStudy owns the agent-facing setup instructions, skill routing, docs, and
  consumption of returned `html_url` values.
- AutoStudy must not duplicate Canvas REST URL construction as a workaround.

## Goals

1. A new user at another Canvas school can configure `canvascli` with their
   Canvas URL and complete browser login.
2. Existing HKUST(GZ) users keep working without a forced migration.
3. `canvascli` distinguishes web origin from API origin internally.
4. AutoStudy describes itself as a Canvas LMS assistant validated on HKUST(GZ),
   not as an HKUST(GZ)-only tool.
5. AutoStudy no longer invents HKUST(GZ) URLs when upstream Canvas JSON omits
   `html_url`.
6. The first implementation has focused offline tests for URL normalization and
   selection behavior, plus compile/help verification.

## Non-Goals

- Multiple named profiles in one installation.
- Switching between schools per command.
- Token authentication.
- Replacing Playwright cookie login.
- Building a fully automated web searcher inside `canvascli`.
- Reworking homework reconnaissance or dynamic pipeline behavior.

## User Experience

For a fresh AutoStudy setup, the agent asks one domain question:

```text
你在哪个学校用 Canvas？学校名、域名，或者 Canvas 登录页网址都行。
```

The agent then follows this order:

1. If the answer already looks like a Canvas URL, pass it to `canvascli init`
   with that URL, such as `canvascli init --canvas-url https://canvas.example.edu`.
2. If the answer is a school name or domain, search for the school's Canvas
   login page using the agent's normal browsing/search capability.
3. If a Canvas-shaped URL is found, pass it to `canvascli init --canvas-url`.
4. If discovery is unclear, ask the user for the direct Canvas login page URL.
5. `canvascli init` opens the normalized web base and saves the selected
   instance config before writing the session cookie.

The setup docs should make clear that all non-login work is the agent's job.
The user's only required actions are answering the school/URL question and
logging into the browser window.

## URL Model

`canvascli` owns a `CanvasInstanceConfig` with these fields:

```text
web_base: login and browser root, for example https://canvas.example.edu
api_base: REST root, for example https://canvas.example.edu/api/v1
```

Accepted inputs:

- `canvas.example.edu`
- `https://canvas.example.edu`
- `https://canvas.example.edu/login/canvas`
- `https://canvas.example.edu/api/v1`
- `https://school.instructure.com`
- `https://school.instructure.com/api/v1`

Normalization rules:

- Add `https://` when the scheme is missing.
- Lowercase the scheme and host.
- Drop query, fragment, and trailing slash.
- If the path contains `/api/v1`, set `api_base` to that prefix and derive
  `web_base` from the host root.
- Otherwise derive `api_base = web_base + "/api/v1"`.
- Reject strings without a host.

This covers both Canvas Cloud domains and school-owned Canvas domains without
hardcoding either family.

## Data Layer Design

### `canvascli.config`

Add a small configuration object and persistence helpers:

- `CanvasInstanceConfig`
- `DEFAULT_WEB_BASE = "https://hkust-gz.instructure.com"`
- `normalize_canvas_url(raw: str) -> CanvasInstanceConfig`
- `instance_config_file() -> Path`
- `load_instance_config() -> CanvasInstanceConfig`
- `save_instance_config(config: CanvasInstanceConfig) -> None`

The default HKUST(GZ) base remains a compatibility fallback only. Once a user
runs `canvascli init --canvas-url https://canvas.example.edu`,
`canvas_instance.json` becomes the source of truth.

The existing `state_file()` remains single-instance for this slice. Because
multi-profile switching is out of scope, the saved cookie belongs to whichever
instance was most recently configured.

### `canvascli auth/client`

`auth.login()` should load or save the instance config, open `web_base`, and
poll `api_base + "/users/self"`.

`CanvasClient` should load the instance config on construction and route
relative API paths through it:

- Absolute `http://` or `https://` URLs are used as-is.
- Paths beginning with `/api/v1` are appended to `web_base`.
- Other leading-slash paths are appended to `api_base`.

This preserves existing resource code that calls paths such as
`/api/v1/courses`.

### CLI

`canvascli init` gains:

```text
--canvas-url TEXT  Canvas login URL or Canvas API root for this installation.
```

When omitted, `init` uses the saved instance config. If no saved config exists,
it uses the HKUST(GZ) compatibility default.

The CLI help string and package metadata become generic Canvas LMS wording.

## AutoStudy Design

### Setup Skill

`sub-skills/tools/canvascli-setup.md` changes from HKUST(GZ)-only setup to
generic Canvas setup:

- Step 0 should check whether `canvascli` is installed and whether `whoami`
  succeeds.
- Fresh setup should ask for school/domain/Canvas URL.
- The agent may search for a Canvas login URL when given a school name.
- The login command should pass `--canvas-url` when a new URL was selected.
- Session refresh for an already configured instance can still run
  `.venv/bin/canvascli init` without repeating the school question.

### API Reference

`sub-skills/tools/canvascli-api.md` records the new contract:

- `canvascli init --canvas-url https://canvas.example.edu` configures the
  instance and logs in.
- JSON returned by Canvas remains unchanged.
- AutoStudy should consume `html_url` returned by Canvas data, not derive a
  school URL locally.

### Selection Script

`scripts/select_plan_item.py` should stop inventing
`https://hkust-gz.instructure.com/courses/...` when `html_url` is missing.
`scripts/write_scan_plan.py` should also carry `html_url` into each plan item so
the stable handoff preserves Canvas-provided browser links.

For this slice, missing `html_url` should produce:

```json
"canvas_url": null
```

The downstream agent can still run reconnaissance from `course_id` and
`assignment_id`; a clickable URL is convenience metadata, not an identity field.

### Homework Output Template

`sub-skills/tasks/do-homework.md` should render the Canvas URL from the selected
plan item or `canvas/assignment.json.html_url`. If no Canvas URL is known, it
should render `not available` rather than a host-specific placeholder.

### User-Facing Docs

Update the public positioning to:

```text
AutoStudy is a local Canvas LMS study assistant. It has been validated on
HKUST(GZ)'s Canvas instance.
```

Historical validation notes may keep HKUST(GZ) examples. Current setup,
runtime entry, and marketing copy should not imply that other Canvas users are
unsupported.

## Testing Strategy

`canvascli` should gain offline tests for:

- Canvas Cloud URL normalization.
- School-owned Canvas URL normalization.
- `/api/v1` input normalization.
- Missing scheme normalization.
- Invalid input rejection.
- Compatibility fallback when no config file exists.
- Config save/load round trip using a temporary config dir.

AutoStudy should gain an offline test for:

- `select_plan_item.py` returns `canvas_url: null` when neither plan nor pending
  assignment has `html_url`.
- Existing `html_url` remains preserved.
- `write_scan_plan.py` carries `html_url` from pending items into `plan.json`.

Manual verification for this planning slice:

- `python3 -m compileall canvascli`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `.venv/bin/canvascli init --help`
- `.venv/bin/canvascli whoami --pretty` on the configured HKUST(GZ) instance
  when a valid local session is available.
- AutoStudy JSON syntax check for `docs/plans/feature-list.json`.
- `git diff --check` in both repos.

## Risks

- Existing users may have `state.json` from HKUST(GZ) but no
  `canvas_instance.json`. The compatibility fallback handles this.
- A user may configure a different school while keeping an old cookie. The next
  `whoami` should fail with an auth error, and setup should rerun `init` for the
  selected instance.
- Some schools use nonstandard Canvas hostnames. The implementation accepts any
  valid host and does not require `canvas.` or `instructure.com`.
- Auto-discovery from school name may pick the wrong site. That logic stays in
  the agent setup workflow, where the agent can show or correct the chosen URL,
  rather than in `canvascli` core.

## Acceptance Criteria

- `canvascli init --canvas-url https://canvas.example.edu/api/v1 --help` style
  command shape exists and normalizes to a web/API pair.
- `CanvasClient._url("/api/v1/users/self")` targets the configured instance.
- `canvascli` no longer describes itself as HKUST(GZ)-only in help/package docs.
- AutoStudy setup docs ask for school/domain/Canvas URL on first run.
- AutoStudy setup docs preserve the direct browser-login UX.
- `scripts/select_plan_item.py` no longer contains `hkust-gz.instructure.com`.
- `scripts/write_scan_plan.py` carries `html_url` into `plan.json`.
- `sub-skills/tasks/do-homework.md` no longer shows a hardcoded HKUST(GZ)
  assignment URL template.
- Public AutoStudy entry docs say generic Canvas LMS, validated on HKUST(GZ).
- Focused offline tests pass in both repositories.
