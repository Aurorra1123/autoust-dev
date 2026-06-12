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
        + render provenance under path/to/render/ when practical
```

If the assignment or `pipeline_design.md` declares `required_spec_constraints`,
the input must include the evidence needed to satisfy those exact constraints,
or an explicit blocker receipt explaining why they are unavailable. A fallback
renderer can produce a preview/debug artifact, but it does not satisfy the final
deliverable when the spec requires different evidence and
`fallback_allowed_for_final: false`.

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
  --resource-path="$(dirname INPUT.md):." \
  -V mainfont="PingFang SC" \
  -V monofont="Menlo" \
  -V geometry:margin=1in \
  -V documentclass=article
```

Pandoc native does not preserve the generated `.tex` or `.log` files by
default. If later review needs render provenance, also write a standalone TeX
sidecar before or after rendering:

```bash
mkdir -p "$(dirname INPUT.md)/render"
pandoc INPUT.md \
  -o "$(dirname INPUT.md)/render/$(basename INPUT.md .md).tex" \
  --standalone \
  --resource-path="$(dirname INPUT.md):." \
  -V mainfont="PingFang SC" \
  -V monofont="Menlo" \
  -V geometry:margin=1in
```

Record the exact engine path in the stage receipt, e.g. `pandoc+xelatex` or
`pandoc->tectonic`, plus whether TeX/log sidecars were preserved. For
development validation and final deliverable PDFs, preserve the log sidecar
under `draft/render/` when the renderer exposes one and the stage has permission
to copy it. If the engine does not expose a log under the allowed write set, or
the stage intentionally records only a warning summary, record that reason in
render provenance. Do not leave a reviewer guessing why no `.tex` or `.log`
file exists.

For deliverables governed by hard spec requirements, preserve specific evidence
as part of render provenance: generated source, build log, command line, input
files, page/layout checks, or other proof named by `required_spec_constraints`.
If the required evidence is missing, render only a clearly named preview/debug
PDF when useful and return the appropriate blocker for the final deliverable.

For report PDFs with multiple figures, preserve enough render provenance for
reviewers to diagnose float placement: source Markdown, generated TeX when
available, log or warning summary, page count, and image-embedding evidence.
If figures drift into an unrelated later section in the rendered PDF, or if the
TeX log reports an `Overfull \vbox` near figure placement and visual inspection
shows a figure clipped by a page boundary, treat it as an auto-fixable
report-quality issue. Do not accept `pdfimages` evidence alone: it can prove an
image is embedded while missing that the visible placement is clipped. For
consecutive large figures, prefer an explicit grouped LaTeX figure block, a
float barrier, a size change, or a section/page break that keeps the figure(s)
with their captions and nearby discussion.

For English deliverables rendered through CTeX or other localized templates,
check generated labels such as table of contents and figure/table prefixes. If
the PDF mixes localized labels into an otherwise English report, configure
English names or record the remaining issue explicitly.

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
  --resource-path="$(dirname INPUT.md):." \
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
        "--resource-path", f"{md_path.parent}:.",
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

Before rendering, **check each engine in order** — do NOT skip to fpdf2
without first attempting the higher-quality paths:

```bash
# Step 1: Check tectonic
tectonic --version 2>/dev/null && echo "TECTONIC_OK" || echo "TECTONIC_MISSING"
# Step 2: Check xelatex
xelatex --version 2>/dev/null | head -1 && echo "XELATEX_OK" || echo "XELATEX_MISSING"
```

Then try rendering paths **in this order, stopping at first success**:

1. **Tectonic two-step** (preferred) — `pandoc → tex → tectonic → PDF`
   - Only attempt if `tectonic --version` succeeds
   - Do NOT `brew install tectonic` in background and skip ahead — wait for install
     or skip this path entirely

2. **Pandoc + xelatex** — `pandoc --pdf-engine=xelatex → PDF`
   - Only attempt if `xelatex --version` succeeds

3. **fpdf2 pure Python** (last resort) — only if both LaTeX engines are unavailable:
   ```bash
   pip install fpdf2
   ```
   Render a simplified text-only PDF. **fpdf2 cannot embed images or complex
   formatting** — expect degraded output. Record in `human_review_items`:
   "PDF rendered via fpdf2 fallback — formatting quality may be degraded.
   Consider installing tectonic for better output."

If the final PDF is suspiciously small (<10KB for a multi-page report),
it likely failed silently. Re-run with a different path.

If fpdf2 output doesn't meet `min_quality` (e.g., < 5 pages when required),
record this as a FAIL in verification.log and add to `human_review_items`.

## Self-check

- [ ] Output PDF exists and is > 1KB
- [ ] Magic bytes are `%PDF` (run: `head -c 4 output.pdf`)
- [ ] Page count matches expectations (run: `pdfinfo output.pdf | grep Pages` if available)
- [ ] Chinese characters render correctly (not tofu boxes) — open and visually verify
- [ ] No LaTeX errors in stderr output
- [ ] For multi-page documents: page count >= 3 (sanity minimum)
- [ ] Referenced images are embedded (for reports with figures, run
      `pdfimages -list output.pdf` or inspect the PDF visually)
- [ ] Stage receipt records render engine and whether `.tex`/`.log`
      provenance was preserved, or why a separate log sidecar is unavailable
- [ ] Multi-figure reports keep figures near their intended sections; important
      figures do not float under unrelated later headings, lose their captions,
      or get clipped at page boundaries
- [ ] TeX logs do not contain unresolved figure-placement `Overfull \vbox`
      warnings; if they do, visually inspect the affected pages and repair
      clipped/drifted figures before marking quality review PASS
- [ ] Language-specific labels match the deliverable language, or the mismatch
      is explicitly classified

## Pitfalls

These came from AutoPku phase 11 and our own validation — fix them once, here, for everyone:

1. **`xelatex` is mandatory for Chinese.** Don't fall through to `pdflatex` even if it's faster — Chinese characters become tofu boxes.
2. **Callout titles must be LaTeX-escaped.** Markdown like `> [!NOTE] 100% accurate` was crashing `tcolorbox` because `%` is a LaTeX comment. The `escape_latex()` in the Lua filter handles `& $ % # _ ^ { } ~ \`.
3. **Don't use emoji icons in callouts.** macOS LaTeX's default fonts don't ship emoji glyphs → ugly warnings + missing chars. Use text tags `[NOTE]`/`[TIP]`/`[WARN]`/`[EX]` instead.
4. **Specify both `mainfont` AND `monofont`.** Without `monofont`, Chinese-mixed code blocks (e.g. comments in Chinese) render with mismatched widths.
5. **` ` (non-breaking space) in markdown breaks pandoc.** If you generated the markdown from web text, normalize: `sed 's/\xc2\xa0/ /g' input.md > clean.md`.
6. **Mermaid diagrams don't render natively.** If a markdown file has ` ```mermaid ` blocks, pre-process with `mermaid-cli` to PNG/SVG first, then pandoc renders the image. Do not ignore — they'll silently become text dumps.
7. **lualatex differs from xelatex.** Some workflows online show `lualatex` config — don't paste those wholesale, our setup is `xelatex`-specific.
8. **Pandoc native hides intermediate TeX.** `pandoc --pdf-engine=xelatex`
   creates temporary TeX files and deletes them. If provenance matters, write a
   sidecar under `draft/render/` with `pandoc --standalone -o ...tex`.
   A missing `.log` is acceptable only when render provenance records the
   engine, warnings, and the reason the log could not be preserved.
9. **Image paths are relative to render cwd unless resource paths are set.**
   Use `--resource-path="$(dirname INPUT.md):."` so `draft/report.md` can embed
   `figures/foo.png` reliably.

## What this tool is NOT for

- ❌ Native `.pptx` generation — use `slide-maker.md` (M3 later) which knows marp/reveal-md
- ❌ PDF parsing/reading — that's `pdf-reader.md` (separate tool, planned)
- ❌ HTML rendering — pandoc supports HTML but if you want HTML output use a different invocation; this tool's contract is markdown→PDF only
