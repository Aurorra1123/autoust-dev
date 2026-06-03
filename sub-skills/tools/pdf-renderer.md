---
name: pdf-renderer
description: Render markdown to a PDF file with Chinese fonts, LaTeX math, code blocks, and callout boxes. The default workhorse for any task producing a PDF deliverable.
---

# pdf-renderer

Markdown → PDF via `pandoc + xelatex`. Supports:

- Chinese (uses `PingFang SC` on macOS, `Noto Sans CJK SC` on Linux)
- LaTeX math (`$...$` and `$$...$$`)
- Code blocks with syntax highlighting
- Callout boxes (`> [!NOTE] / [!TIP] / [!WARN]`) via a Lua filter
- Page numbers, custom geometry

## Capabilities

- `render_pdf` — markdown file → PDF file

## Inputs / Outputs

```
Input:  path/to/document.md         (UTF-8 markdown)
        + optional: path/to/figures/  (referenced images)
        + optional: title, author, date metadata in frontmatter
Output: path/to/document.pdf
```

## Setup

There are two supported LaTeX engines. Pick whichever is installed:

### Option A: Tectonic (recommended — single binary, auto-downloads packages)

```bash
brew install tectonic pandoc      # macOS
# or
curl -fsSL https://drop-sh.fullyjustified.net | sh  # cross-platform installer
```

Tectonic doesn't integrate directly with `--pdf-engine`. We do a **two-step pipeline** instead:

1. `pandoc input.md -o output.tex` (markdown → LaTeX source)
2. `tectonic -o output_dir output.tex` (LaTeX → PDF, fetching CJK packages on first run)

See "Invocation: Tectonic two-step" below.

### Option B: Full TeX Live + pandoc native

**macOS** (Homebrew):
```bash
brew install pandoc
brew install --cask mactex-no-gui    # ~4 GB; full LaTeX
# Or smaller: brew install --cask basictex && sudo tlmgr install xecjk ctex ...
```

**Linux** (apt):
```bash
sudo apt install pandoc texlive-xetex texlive-fonts-recommended \
                 texlive-lang-chinese fonts-noto-cjk
```

### Verify

```bash
pandoc --version | head -1
tectonic --version 2>/dev/null || xelatex --version | head -1
fc-list :lang=zh | head -5     # confirm Chinese fonts present
```

If neither tectonic nor xelatex is available, **fail loudly** rather than silently producing a broken PDF.

## Invocation

### Tectonic two-step (use if you have tectonic)

```bash
mkdir -p "$(dirname OUTPUT.pdf)"

# Step 1: pandoc emits standalone LaTeX
pandoc INPUT.md \
  -o /tmp/autostudy_render.tex \
  --standalone \
  -V CJKmainfont="PingFang SC" \
  -V monofont="Menlo" \
  -V geometry:margin=1in \
  -V documentclass=ctexart    # ctexart handles CJK out of the box

# Step 2: tectonic compiles (first run downloads ~50MB of packages)
tectonic /tmp/autostudy_render.tex --outdir "$(dirname OUTPUT.pdf)" --keep-logs --print
mv "$(dirname OUTPUT.pdf)/autostudy_render.pdf" OUTPUT.pdf
```

**Notes for tectonic path**:
- Use `documentclass=ctexart` (not `article`) — it bundles CJK + xeCJK setup
- Use `-V CJKmainfont` (not `mainfont`) when going through ctex
- First run is slow (network fetch); subsequent runs are fast (cached)

### Pandoc native (use if you have xelatex)

```bash
pandoc INPUT.md \
  -o OUTPUT.pdf \
  --pdf-engine=xelatex \
  -V mainfont="PingFang SC" \
  -V monofont="Menlo" \
  -V geometry:margin=1in \
  -V documentclass=article
```

### With LaTeX math and code highlighting (works for both paths)

Add to either invocation:

```bash
  --highlight-style=tango \
  --toc                       # optional table of contents
```

### With callout boxes

Callouts require a Lua filter. Save this once as `data/tools/callout.lua`:

```lua
-- Recognizes "> [!NOTE]", "> [!TIP]", "> [!WARN]", "> [!EX]" in blockquotes
-- and converts them to tcolorbox environments.
-- Source: adapted from AutoPku's callout.lua (see docs/PITFALLS.md for the bugs we hit).

local LABELS = {
  NOTE = "[NOTE]", TIP = "[TIP]", WARN = "[WARN]", EX = "[EX]",
}

local function escape_latex(s)
  -- Without this, & $ % # _ ^ { } ~ \ in the title crashes tcolorbox.
  s = s:gsub("\\", "\\textbackslash{}")
  s = s:gsub("([&%$%#_%^{}~])", "\\%1")
  return s
end

function BlockQuote(el)
  if #el.content == 0 then return nil end
  local first = el.content[1]
  if first.t ~= "Para" then return nil end
  local inlines = first.content
  if #inlines < 1 or inlines[1].t ~= "Str" then return nil end
  local tag = inlines[1].text:match("^%[!(%w+)%]")
  if not tag or not LABELS[tag] then return nil end

  -- Strip the [!TAG] marker; everything after first SoftBreak is body.
  local title_parts = {}
  local body_parts = {}
  local seen_break = false
  for i = 2, #inlines do
    if inlines[i].t == "SoftBreak" then seen_break = true
    elseif seen_break then table.insert(body_parts, inlines[i])
    else table.insert(title_parts, inlines[i])
    end
  end
  local title = pandoc.utils.stringify(title_parts):gsub("^%s+", "")
  if title == "" then title = LABELS[tag] else title = LABELS[tag] .. " " .. title end

  return {
    pandoc.RawBlock("latex", "\\begin{tcolorbox}[title={" .. escape_latex(title) .. "}]"),
    pandoc.Para(body_parts),
    pandoc.RawBlock("latex", "\\end{tcolorbox}"),
  }
end
```

Then invoke with the filter and the required preamble:

```bash
mkdir -p data/tools  # if it doesn't exist
# (write callout.lua there once, as above)

pandoc INPUT.md \
  -o OUTPUT.pdf \
  --pdf-engine=xelatex \
  --lua-filter=data/tools/callout.lua \
  -H <(echo '\usepackage{tcolorbox}\tcbuselibrary{breakable,skins}') \
  -V mainfont="PingFang SC" \
  -V monofont="Menlo" \
  -V geometry:margin=1in
```

### Python helper (for orchestrator to call programmatically)

When the orchestrator wants to render a PDF inside its own pipeline, drop this snippet into a working file under `data/homework/<course>/<hw>/` and run it:

```python
import subprocess
from pathlib import Path

def render_pdf(md_path, pdf_path, *, with_callouts=False, font="PingFang SC"):
    md_path = Path(md_path)
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pandoc", str(md_path), "-o", str(pdf_path),
        "--pdf-engine=xelatex",
        "-V", f"mainfont={font}",
        "-V", "monofont=Menlo",
        "-V", "geometry:margin=1in",
        "-V", "documentclass=article",
    ]
    if with_callouts:
        cmd += ["--lua-filter=data/tools/callout.lua"]
        cmd += ["-H", "/tmp/callout_preamble.tex"]
        Path("/tmp/callout_preamble.tex").write_text(
            r"\usepackage{tcolorbox}\tcbuselibrary{breakable,skins}"
        )

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc failed: {r.stderr}")
    return pdf_path

# Example
render_pdf("draft.md", "data/homework/DSAA2043/hw3/final.pdf")
```

## Post-processing (fallback chain)

If the primary rendering path fails, try in order:

1. **Tectonic two-step** (preferred) — `pandoc → tex → tectonic → PDF`
2. **Pandoc + xelatex** — `pandoc --pdf-engine=xelatex → PDF`
3. **fpdf2 pure Python** — if neither LaTeX engine is available:
   ```bash
   pip install fpdf2
   ```
   Render a simplified text-only PDF. Record in `human_review_items`:
   "PDF rendered via fpdf2 fallback — formatting quality may be degraded."

If the final PDF is suspiciously small (<10KB for a multi-page report),
it likely failed silently. Re-run with a different path.

## Self-check

- [ ] Output PDF exists and is > 1KB
- [ ] Magic bytes are `%PDF` (run: `head -c 4 output.pdf`)
- [ ] Page count matches expectations (run: `pdfinfo output.pdf | grep Pages` if available)
- [ ] Chinese characters render correctly (not tofu boxes) — open and visually verify
- [ ] No LaTeX errors in stderr output
- [ ] For multi-page documents: page count >= 3 (sanity minimum)

## Pitfalls

These came from AutoPku phase 11 and our own validation — fix them once, here, for everyone:

1. **`xelatex` is mandatory for Chinese.** Don't fall through to `pdflatex` even if it's faster — Chinese characters become tofu boxes.
2. **Callout titles must be LaTeX-escaped.** Markdown like `> [!NOTE] 100% accurate` was crashing `tcolorbox` because `%` is a LaTeX comment. The `escape_latex()` in the Lua filter handles `& $ % # _ ^ { } ~ \`.
3. **Don't use emoji icons in callouts.** macOS LaTeX's default fonts don't ship emoji glyphs → ugly warnings + missing chars. Use text tags `[NOTE]`/`[TIP]`/`[WARN]`/`[EX]` instead.
4. **Specify both `mainfont` AND `monofont`.** Without `monofont`, Chinese-mixed code blocks (e.g. comments in Chinese) render with mismatched widths.
5. **` ` (non-breaking space) in markdown breaks pandoc.** If you generated the markdown from web text, normalize: `sed 's/\xc2\xa0/ /g' input.md > clean.md`.
6. **Mermaid diagrams don't render natively.** If a markdown file has ` ```mermaid ` blocks, pre-process with `mermaid-cli` to PNG/SVG first, then pandoc renders the image. Do not ignore — they'll silently become text dumps.
7. **lualatex differs from xelatex.** Some workflows online show `lualatex` config — don't paste those wholesale, our setup is `xelatex`-specific.

## What this tool is NOT for

- ❌ Native `.pptx` generation — use `slide-maker.md` (M3 later) which knows marp/reveal-md
- ❌ PDF parsing/reading — that's `pdf-reader.md` (separate tool, planned)
- ❌ HTML rendering — pandoc supports HTML but if you want HTML output use a different invocation; this tool's contract is markdown→PDF only
