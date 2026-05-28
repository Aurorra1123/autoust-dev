---
name: problem-extractor
description: Ground every homework deliverable in real problem text. Canvas descriptions often contain only a PDF attachment link — this tool downloads the attachment and emits problem.md so downstream tools (writing-helper, code-writer, slide-maker) work from the actual problem statement, not the assignment title.
---

# problem-extractor

The data-grounding tool. **Without this step, the agent ends up writing template content with `[PROBLEM N]` placeholders, because the Canvas API's `description` field is frequently just an attachment link, not the problem statement itself.**

Real example (DSAA2043 Lab Assignment 1, `assignment.json.description`):

```html
<p><a class="instructure_file_link"
      title="DSAA2043_Assignment_1.pdf"
      href="https://hkust-gz.instructure.com/courses/2151/files/475078?wrap=1"
      data-api-endpoint="https://hkust-gz.instructure.com/api/v1/courses/2151/files/475078"
      data-api-returntype="File">DSAA2043_Assignment_1.pdf</a></p>
```

The problem statement (5 actual proof problems, recurrences, definitions) lives inside `DSAA2043_Assignment_1.pdf`. The agent must fetch and read that PDF before anything else.

## Capabilities

- `extract_problem` — `assignment.json` (+ `course_id`) → `problem.md` (real problem text, attachments downloaded)

## Inputs / Outputs

```
Input:  <work_dir>/assignment.json        (from `canvascli assignment <id> -c <cid>`)
        course_id                          (numeric, from the same canvascli call)
Output: <work_dir>/attachments/<file>.pdf  (raw downloaded attachments)
        <work_dir>/attachments/<file>.txt  (extracted text per attachment)
        <work_dir>/problem.md              (assembled, grounded problem statement)
```

`problem.md` is the canonical source for `writing-helper`, `code-writer`, and `slide-maker`. They MUST read it instead of `assignment.json.description`.

## Setup

Two text-extraction backends. Try `pdftotext` first, fall back to `pdfminer.six`:

```bash
# Preferred (better math/layout fidelity)
which pdftotext || brew install poppler

# Fallback (pure Python, no system dep)
.venv/bin/pip install pdfminer.six -i https://pypi.tuna.tsinghua.edu.cn/simple
```

The fallback alone is fine for MVP. Don't block on installing poppler.

## Invocation

The agent writes `<work_dir>/scripts/extract_problem.py` and runs it. Template:

```python
"""Extract real problem text from a Canvas assignment + its attachments."""
import json, re, subprocess, sys, shutil
from pathlib import Path

WORK_DIR = Path(sys.argv[1])
COURSE_ID = sys.argv[2]                       # passed by do-homework [A]
ATTACH_DIR = WORK_DIR / "attachments"
ATTACH_DIR.mkdir(parents=True, exist_ok=True)

data = json.loads((WORK_DIR / "assignment.json").read_text())
desc_html = data.get("description") or ""

# --- Find every (file_id, filename) pair embedded in the description HTML.
# Canvas uses two patterns: data-api-endpoint and href. Capture both.
fid_to_title: dict[str, str] = {}

# Pair pattern A: title="..." before href/data-api-endpoint
for m in re.finditer(
    r'<a\b[^>]*?\btitle="([^"]+)"[^>]*?(?:href|data-api-endpoint)='
    r'"[^"]*?/files/(\d+)[^"]*"',
    desc_html, flags=re.IGNORECASE | re.DOTALL,
):
    fid_to_title[m.group(2)] = m.group(1)

# Pair pattern B: href/data-api-endpoint before title="..."
for m in re.finditer(
    r'<a\b[^>]*?(?:href|data-api-endpoint)="[^"]*?/files/(\d+)[^"]*"'
    r'[^>]*?\btitle="([^"]+)"',
    desc_html, flags=re.IGNORECASE | re.DOTALL,
):
    fid_to_title[m.group(1)] = m.group(2)

# Catch any file_id without a title attribute
for pat in (r'href="[^"]*?/files/(\d+)', r'data-api-endpoint="[^"]*?/files/(\d+)'):
    for fid in re.findall(pat, desc_html):
        fid_to_title.setdefault(fid, f"file_{fid}")

# --- Download each attachment via canvascli
def safe_name(s: str) -> str:
    return re.sub(r'[/\\:*?"<>|]', "_", (s or "").strip())[:120] or "file"

CANVASCLI = ".venv/bin/canvascli"
attachments: list[tuple[str, Path]] = []     # (display_title, local_path)
for fid, title in fid_to_title.items():
    local = ATTACH_DIR / safe_name(title)
    if not local.exists():
        subprocess.check_call([CANVASCLI, "download", fid, "-o", str(local)])
    attachments.append((title, local))

# --- Extract text per attachment
def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf" or path.read_bytes()[:4] == b"%PDF":
        if shutil.which("pdftotext"):
            return subprocess.check_output(
                ["pdftotext", "-layout", str(path), "-"]
            ).decode("utf-8", errors="replace")
        from pdfminer.high_level import extract_text as pdfminer_extract
        return pdfminer_extract(str(path))
    # Plain text / HTML / other
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""

# --- Strip description HTML to plain text via pandoc (already installed)
plain_desc = subprocess.run(
    ["pandoc", "-f", "html", "-t", "plain", "--wrap=none"],
    input=desc_html, capture_output=True, text=True,
).stdout.strip()

# --- Assemble problem.md
parts: list[str] = []
parts += [
    "---",
    f"course: {data.get('course_code') or ''}",
    f"assignment_name: {data.get('name') or ''}",
    f"assignment_id: {data.get('id') or ''}",
    f"course_id: {COURSE_ID}",
    f"due_at: {data.get('due_at') or ''}",
    f"points_possible: {data.get('points_possible') or ''}",
    f"submission_types: {data.get('submission_types') or []}",
    f"attachments_processed: {[t for t, _ in attachments]}",
    "---",
    "",
    f"# {data.get('name', 'Assignment')}",
    "",
    "## Inline description (from Canvas HTML, plain-text)",
    "",
    plain_desc or "_(empty — see attachments)_",
    "",
]

total_text_bytes = 0
for title, local in attachments:
    text = extract_text(local).strip()
    total_text_bytes += len(text)
    (local.with_suffix(local.suffix + ".txt")).write_text(text)
    parts += [
        f"## Attached: {title}",
        "",
        text if text else "_(extraction failed — image-only PDF or unsupported format?)_",
        "",
    ]

rubric = data.get("rubric") or []
if rubric:
    parts += ["## Rubric", ""]
    for r in rubric:
        parts.append(f"- {r.get('description', '')} ({r.get('points', '?')} pts)")
    parts.append("")

(WORK_DIR / "problem.md").write_text("\n".join(parts))

print(f"Wrote {WORK_DIR / 'problem.md'} ({(WORK_DIR / 'problem.md').stat().st_size} bytes)")
print(f"Attachments: {len(attachments)}, total extracted text: {total_text_bytes} bytes")

# Non-zero exit if neither inline nor any attachment yielded usable text.
if total_text_bytes < 200 and len(plain_desc) < 200:
    print("WARN: problem.md is thin — extraction may have failed.", file=sys.stderr)
    sys.exit(2)
```

Run it:

```bash
mkdir -p "<work_dir>/scripts"
# Write the script above to <work_dir>/scripts/extract_problem.py
.venv/bin/python "<work_dir>/scripts/extract_problem.py" "<work_dir>" "<course_id>"
```

## Quality bar — non-negotiable

After this tool runs, `problem.md` MUST contain one of:

(a) Real problem text inside `## Attached: <filename>` sections (the common case), OR
(b) Real problem text inside `## Inline description` (rare — only when the instructor pasted everything into the Canvas WYSIWYG), OR
(c) A clear failure marker (`_(extraction failed ...)_` or non-zero exit) that signals `do-homework [A4]` to fall back to AskUserQuestion.

**This tool exists for one reason: stop the agent from producing `[PROBLEM N]` / `[TODO: align with actual project spec]` template content.** If `problem.md` ends up empty/thin, downstream tools must REFUSE to proceed and instead surface the gap to the user via `do-homework`.

## Cross-references

- Called from: `tasks/do-homework.md` step `[A3]`
- Consumed by: `tools/writing-helper.md`, `tools/code-writer.md`, `tools/slide-maker.md`
- Depends on: `tools/canvascli-api.md` (`download` command), pandoc (already installed for pdf-renderer), pdftotext OR pdfminer.six

## What this tool is NOT for

- ❌ Doing the homework. It only fetches + extracts. Reasoning happens in the deliverable tools.
- ❌ Parsing tables/equations into structured data. PDF text extraction loses some structure; the downstream tool engages with the raw extracted text.
- ❌ OCR for image-only PDFs (out of MVP scope — surface as failure, ask user).
- ❌ Talking to Canvas's `discussion_topics` / `quizzes` endpoints. Only assignment files.

## Pitfalls

1. **`canvascli download <id> -o <path>` writes exactly to that path.** If you pass `-o file_475078`, you get a file named `file_475078` with no extension. The script above uses the HTML `title="..."` attribute to recover the real filename when present.
2. **Image-only PDFs return empty text.** Some instructors scan paper handouts. Both `pdftotext` and `pdfminer.six` will return `""`. The script exits with status 2 in this case so `do-homework` can prompt the user.
3. **Filenames with Chinese / spaces** are normalized via `safe_name()` (only replaces filesystem-reserved chars; keeps Chinese + spaces).
4. **Some Canvas descriptions embed the SAME file ID twice** (once in `href`, once in `data-api-endpoint`). The dict-based dedup handles this.
5. **Multiple attachments per assignment is common** (problem set + dataset + solution template). All are downloaded and concatenated into `problem.md`. Downstream tools decide which sections matter.
6. **Don't re-run if `problem.md` already exists and is non-trivial.** The script's `if not local.exists()` check is per-attachment; for the assembled `problem.md`, `do-homework [A3]` should skip when the file is already populated (idempotency on re-runs of `[重做]` flow).
7. **`pdftotext -layout` preserves column layout, which is often what you want for math problem sets.** Without `-layout`, two-column PDFs get interleaved.
