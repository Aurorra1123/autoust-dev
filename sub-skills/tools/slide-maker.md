---
name: slide-maker
description: Generate presentation decks. Default path uses the guizang-ppt-skill (magazine / Swiss-style HTML decks via the upstream skill at ~/.claude/skills/guizang-ppt-skill). LaTeX-beamer remains available as a fallback for strict-PDF / math-heavy academic submissions.
---

# slide-maker

Produce a slide deck for group presentations / talks. Two paths:

| Path | Output | When to pick |
|---|---|---|
| **guizang (default)** | `index.html` (single-file) + `slides.pdf` (Playwright print) | Most decks — magazine humanities, Swiss data / product, anything where visual quality matters |
| **beamer (fallback)** | `slides.tex` + `slides.pdf` (tectonic) | Strict-PDF academic submissions, math-heavy proofs, or when guizang skill not installed |

## Controlled Renderer Policy

The final renderer path is controlled by this tool contract:

- `guizang`: final HTML source plus Playwright PDF export.
- `beamer`: final LaTeX source plus tectonic PDF export.

Do not silently introduce a third final renderer path. PyMuPDF may be used only
as a bounded repair, preview, or debug fallback when the stage brief explicitly
authorizes it or when it regenerates a deliverable that still satisfies the
selected `guizang` or `beamer` contract. PyMuPDF is not a third final renderer path by default.

If a PyMuPDF repair/preview fallback is used, the stage result must record:

- the exact render script path or inline render script;
- the command used to run it;
- the font strategy, including font file paths or an explicit ASCII-only list
  marker strategy;
- the `pdffonts` output;
- the `pdftotext` replacement-glyph check result.

Do not use PyMuPDF's default Helvetica/WinAnsi output for final slides that need
Unicode list bullets, CJK, math symbols, or other non-ASCII glyphs. Either embed
a Unicode-capable font, use ASCII list markers such as `-`, or stop with an
`auto_fixable`/`revision_needed` issue. A PDF with line-leading question marks,
tofu boxes, or replacement characters produced by glyph substitution is not a
passing final deliverable.

## Capabilities

- `render_slides` — slide spec → final deliverable (HTML+PDF or PDF)

## Inputs / Outputs

```
Input:  <work_dir>/spec.md               (PRIMARY: standardized reconnaissance report)
        <work_dir>/pipeline_design.md    (slides stage, count, audience, constraints, verification plan)
        <work_dir>/investigation/rubric.md
        <work_dir>/references/           (fetched spec text, slides/readings, images if relevant)
        <work_dir>/problem.md            (compatibility presentation topic / brief)
        <work_dir>/investigation/user_notes.md  (optional)
        <work_dir>/investigation/user_scope.md  (optional)
        <work_dir>/canvas/assignment.json (metadata only: due_at, rubric, points)
        <work_dir>/figures/*.{pdf,png}   (optional, embed in slides)
Output (guizang):
        <work_dir>/guizang/index.html    (single-file deck, ~50KB)
        <work_dir>/guizang/images/       (image assets, 1600px wide)
        <work_dir>/guizang/slides.pdf    (Playwright print, 16:9 1600×900)
Output (beamer):
        <work_dir>/slides.tex
        <work_dir>/slides.pdf            (tectonic, A4 or beamer 16:9)
```

**Read `spec.md` first, then `pipeline_design.md`, rubric, references, user
supplements, and finally `problem.md`, completely.** The workbench files contain
the presentation brief — the assigned topic, required content, length, audience,
and supporting context. The assignment title alone (e.g. "Group presentation")
tells you nothing. If `spec.md` says the main spec is an external document and
another module item is nearby supporting context, ground the deck in that source
trail. Do not fall back to a generic "topic overview / methods / findings"
template.

For group presentations specifically: if `spec.md` requires the group to choose
a sub-topic and the user has not specified which sub-topic, write one
`[CLARIFICATION NEEDED: which sub-topic? options from spec.md: A / B / C]`
marker in slide 2 and continue with the most general framing. This is surfaced
at do-homework [E]. Do not leave `[此处由小组成员填入选题]` placeholders throughout
the deck.

## Path A — guizang-ppt-skill (default)

### Setup (once)

```bash
mkdir -p ~/.claude/skills/
git clone https://github.com/op7418/guizang-ppt-skill.git ~/.claude/skills/guizang-ppt-skill
ls ~/.claude/skills/guizang-ppt-skill/   # → SKILL.md assets/ references/ scripts/
```

Skill installs once and is shared across all decks.

### Step 1 — Read the upstream SKILL.md

Always invoke the skill's instructions in full before generating a deck. Read in this order:

1. `~/.claude/skills/guizang-ppt-skill/SKILL.md` (overview + Step 0–6 workflow)
2. Pick **Style A or B**:
   - Style A (electronic magazine) — humanities, critical reading, narrative talks → `references/themes.md` + `references/layouts.md`
   - Style B (Swiss international) — data, product, STEM dashboards → `references/themes-swiss.md` + `references/layouts-swiss.md` + `references/swiss-layout-lock.md`
3. Read the chosen template (`assets/template.html` or `assets/template-swiss.html`) **end-to-end before writing slides** — the template's `<style>` block is the only source of valid CSS class names.
4. Read `references/checklist.md` and verify against it before delivery.

### Step 2 — Generate the deck

Copy the template into `<work_dir>/guizang/index.html`, fill in slides per the layouts file. Hard rules from upstream (do not skip):

- Pick exactly **one** preset theme from the 5 (A) or 4 (B) options; never custom hex.
- For Style B: every `<section class="slide">` needs `data-layout="Sxx"` (S01-S22 only); validate with `node ~/.claude/skills/guizang-ppt-skill/scripts/validate-swiss-deck.mjs index.html`.
- Theme rhythm: `hero-dark / light / hero-light / dark` mix, no 3-in-a-row, ≥1 of each hero polarity for 8+ pages.
- All content in the assignment's language (zh-CN for HKUST(GZ) Chinese-language assignments).

### Step 3 — Export to PDF (Playwright headless)

`.venv` already has playwright; chromium is installed.

```python
# Save as <work_dir>/render_pdf.py and invoke via .venv/bin/python
from playwright.sync_api import sync_playwright
from pathlib import Path

WORK = Path(__file__).parent / "guizang"
HTML = WORK / "index.html"
OUT  = WORK / "slides.pdf"

PRINT_CSS = """
/* stack horizontal-swipe slides into a vertical print column */
html, body { overflow: visible !important; height: auto !important; }
.deck { display: block !important; transform: none !important; height: auto !important; }
.slide {
  width: 1600px !important;
  height: 900px !important;
  page-break-after: always;
  break-after: page;
  position: relative !important;
  transform: none !important;
}
nav, .hint, canvas { display: none !important; }
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 900})
    page.goto(f"file://{HTML.absolute()}")
    # low-power mode kills WebGL canvases that fight print
    page.evaluate("localStorage.setItem('guizang-ppt-low-power', '1')")
    page.add_style_tag(content=PRINT_CSS)
    page.wait_for_timeout(2000)  # let Motion One reveal + fonts settle
    page.pdf(path=str(OUT), width="1600px", height="900px", print_background=True,
             margin={"top":"0","bottom":"0","left":"0","right":"0"})
    browser.close()
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
```

Run:
```bash
.venv/bin/python "<work_dir>/render_pdf.py"
```

Expected output: `<work_dir>/guizang/slides.pdf` at ~1-2 MB for a 10-slide deck (HTML is the source of truth — PDF is for Canvas submission).

### Step 4 — Verify

```bash
grep -c 'class="slide' "<work_dir>/guizang/index.html"   # should equal n_slides
file "<work_dir>/guizang/slides.pdf"                      # PDF document, version 1.x
mdls -name kMDItemNumberOfPages "<work_dir>/guizang/slides.pdf"
pdffonts "<work_dir>/guizang/slides.pdf"                  # record font embedding evidence
pdftotext "<work_dir>/guizang/slides.pdf" - | rg '^[[:space:]]*[?]' && exit 1 || true
```

## Path B — LaTeX beamer (fallback)

Use when: math-heavy academic submission, strict-PDF-only required, or guizang skill not installed.

### Step 1 — Write the .tex source

The agent writes `<work_dir>/slides.tex`:

```latex
\documentclass[aspectratio=169,UTF8]{ctexbeamer}
\usetheme{Madrid}
\usecolortheme{seahorse}
\setCJKmainfont{PingFang SC}
\setmonofont{Menlo}
\usepackage{graphicx}
\graphicspath{{./figures/}}

\title{<from spec.md or pipeline_design.md>}
\author{}
\date{\today}

\begin{document}
\frame{\titlepage}
\begin{frame}{Outline}\tableofcontents\end{frame}
\section{Introduction}
\begin{frame}{Background}\begin{itemize}\item Context 1\item Context 2\end{itemize}\end{frame}
% ... more frames ...
\end{document}
```

### Step 2 — Compile via tectonic

```bash
cd "<work_dir>"
tectonic slides.tex 2>&1 | tail -10
```

First run downloads ctexbeamer (~50MB cached). Subsequent compiles are seconds.

### Step 3 — Verify

```bash
file "<work_dir>/slides.pdf"
mdls -name kMDItemNumberOfPages "<work_dir>/slides.pdf"
pdffonts "<work_dir>/slides.pdf"                          # record font embedding evidence
pdftotext "<work_dir>/slides.pdf" - | rg '^[[:space:]]*[?]' && exit 1 || true
```

Treat line-leading question marks, tofu boxes, or Unicode replacement characters
as replacement-glyph failures unless they are expected literal source text and
documented with a source excerpt.

## What this tool is NOT for

- ❌ PowerPoint .pptx output — that needs pandoc → pptx (separate path)
- ❌ Animated / interactive HTML decks beyond what guizang ships
- ❌ Real-time co-editing — both paths generate once, then re-render

## Pitfalls

### guizang path

1. **Ground every slide in `spec.md`, `references/`, and
   `pipeline_design.md`.** A presentation deck that doesn't name the actual
   topic, doesn't engage with the assigned content, and instead leaves
   `[此处由小组成员填入选题]` / `[此处填入论点]` placeholders is failing the quality
   bar — even if the visual is pretty. Acceptable placeholder:
   `[CLARIFICATION NEEDED: which sub-topic from spec.md options A/B/C]` (one per
   ambiguous decision, surfaced at do-homework [E]).
2. **Class names are template-specific.** `h-hero` in Style A is serif (Noto Serif SC), in Style B is sans (Inter). Don't mix layouts.md and layouts-swiss.md class names.
3. **`<title>` placeholder.** `assets/template.html` has `[必填] 替换为 PPT 标题` — replace immediately or browser tabs look broken. Grep `[必填]` after copy.
4. **Style B layout lock.** Every `data-layout` must be `S01`–`S22` (or the `SWISS-COVER-ASCII` / `SWISS-CLOSING-ASCII` extensions). Inventing `S23` or "Swiss Image Split" is rejected by `validate-swiss-deck.mjs`.
5. **Playwright PDF needs low-power mode.** Without `localStorage.setItem('guizang-ppt-low-power','1')` the WebGL backgrounds fight the print loop and you get black pages.
6. **Lucide icons may race.** Wrap `lucide.createIcons()` in `if(window.lucide)` — upstream template does not.
7. **Image folder convention**: `images/{pageNumber}-{semantic}.{ext}` (e.g. `01-cover.jpg`), all JPEG/PNG ≥1600px wide.
8. **One theme per deck.** Picking `ink-classic` for one page and `dune` for another breaks the visual.

### beamer path

1. **`%` is a LaTeX comment** — escape as `\%` in slide text or the rest of the line vanishes.
2. **`&`, `_`, `#` inside `\title{}` / `\author{}`** must be escaped (`\&` `\_` `\#`).
3. **Don't put `\section{}` inside `\begin{frame}`** — they go between frames.
4. **CJK requires `ctexbeamer` documentclass** + `\setCJKmainfont{PingFang SC}`.
5. **`\graphicspath{{./figures/}}`** — double braces are the LaTeX syntax for multiple search paths.
6. **`aspectratio=169`** for modern projectors; default beamer 4:3 looks dated.
7. **`\maketitle` doesn't exist in beamer** — use `\frame{\titlepage}`.

## Cross-references

- Guizang upstream: https://github.com/op7418/guizang-ppt-skill — read `SKILL.md` + the chosen `themes.md` / `layouts.md` before generating any deck
- LaTeX font + ctex notes: `pdf-renderer.md`
- For Canvas submission deliverable: `docs/PITFALLS.md` (Canvas accepts both PDF and HTML; PDF is the safer bet)
