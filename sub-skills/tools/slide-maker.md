---
name: slide-maker
description: Generate presentation slides as LaTeX beamer source, then compile to PDF via tectonic. Uses the same tectonic toolchain as pdf-renderer — no marp / no Node.js dependency.
---

# slide-maker

Produce a slide deck for group presentations / talks. Writes `slides.tex` (LaTeX beamer source) into `<work_dir>/`, then invokes tectonic to compile.

**MVP choice**: LaTeX beamer over marp/reveal-md because (a) tectonic is already installed for `pdf-renderer`, (b) no Node.js dependency, (c) shares the CJK font config we already validated, (d) output is direct PDF (no HTML middleware).

## Capabilities

- `render_slides` — slide spec → slides.pdf (via tectonic + beamer)

## Inputs / Outputs

```
Input:  <work_dir>/task_profile.yaml      (title, language, length: n_slides ~= 8)
        <work_dir>/assignment.json        (Canvas description with topic)
        <work_dir>/figures/*.{pdf,png}    (optional, embed in slides)
Output: <work_dir>/slides.tex             (LaTeX beamer source)
        <work_dir>/slides.pdf             (final deliverable)
```

## Setup

```bash
brew install tectonic                     # already installed
```

CJK in beamer requires `ctexbeamer` documentclass (not `ctexart`). Tectonic auto-downloads it on first compile.

If your machine fails to fetch `ctexbeamer` (rare; mirror issue), fall back to: change the documentclass to `beamer` and add `\usepackage{ctex}` in the preamble. Both work; ctexbeamer is just cleaner.

## Invocation

### Step 1 — Write the .tex source

The agent writes `<work_dir>/slides.tex` directly. Template:

```latex
\documentclass[aspectratio=169,UTF8]{ctexbeamer}
\usetheme{Madrid}
\usecolortheme{seahorse}

% Fonts (PingFang SC matches pdf-renderer's setup)
\setCJKmainfont{PingFang SC}
\setmonofont{Menlo}

% For embedded figures
\usepackage{graphicx}
\graphicspath{{./figures/}}

\title{<Slide title from task_profile.title>}
\author{<leave blank — student fills>}
\date{\today}

\begin{document}

\frame{\titlepage}

\begin{frame}{Outline}
  \tableofcontents
\end{frame}

\section{Introduction}

\begin{frame}{Background}
  \begin{itemize}
    \item Context point 1
    \item Context point 2
    \item Why this matters
  \end{itemize}
\end{frame}

\section{Main content}

\begin{frame}{Approach}
  \begin{itemize}
    \item Step 1
    \item Step 2
  \end{itemize}
\end{frame}

\begin{frame}{Results}
  % If figure-maker produced figures, embed:
  \begin{center}
    \includegraphics[width=0.8\textwidth]{fig_1.pdf}
  \end{center}
  Caption / takeaway
\end{frame}

\section{Conclusion}

\begin{frame}{Takeaways}
  \begin{itemize}
    \item Key point 1
    \item Key point 2
  \end{itemize}
\end{frame}

\begin{frame}{Q\&A}
  \begin{center}
    \LARGE Thank you. Questions?
  \end{center}
\end{frame}

\end{document}
```

The agent adapts content per assignment. Target slide count from `task_profile.length` (default 8). Rules of thumb:
- 1 title + 1 outline + 1 Q&A = 3 boilerplate slides
- Body slides = `n_slides - 3`, distributed across sections roughly evenly
- ≤5 bullets per slide; if more, split into 2 slides
- Every section gets a `\section{}` header for the outline auto-fill

### Step 2 — Compile via tectonic

```bash
cd "<work_dir>"
tectonic slides.tex --keep-logs --print 2>&1 | tail -20
```

Tectonic writes `slides.pdf` in the same dir. First run is slow (downloads ctexbeamer + CJK packages, ~50MB cached).

If compilation fails, the most common reasons:
- Unescaped `&`, `%`, `_`, `#` in slide text → wrap in `\&`, `\%`, `\_`, `\#`
- Missing image path → check `\graphicspath` matches actual `figures/` location
- Stray `&` in `\title{}` or `\author{}` → escape

### Step 3 — Verify

```bash
ls -lh "<work_dir>/slides.pdf"
# Should be 100KB+ for a typical 8-slide deck
```

## What this tool is NOT for

- ❌ HTML / web slides — beamer outputs PDF only
- ❌ Interactive slides (clicking through animations) — beamer overlays are static
- ❌ Real-time editing — generates the .tex once, then compile
- ❌ PowerPoint .pptx output — that needs marp / pandoc → pptx (separate path)

## Pitfalls

1. **`%` is a LaTeX comment** — if any slide text contains `%` (e.g. "30% improvement"), escape as `\%` or the rest of the line vanishes.
2. **`\&` inside `\title{}`** can break beamer parsing — use `\&` not `\and`. Same for `_` (must be `\_`) and `#` (must be `\#`).
3. **Don't use `\section{}` inside a `\begin{frame}`** — they go between frames. Putting one inside a frame causes "missing \endcsname" errors.
4. **CJK requires `ctexbeamer` + `\setCJKmainfont`.** Plain beamer with `\usepackage{xeCJK}` works too but ctexbeamer's defaults are friendlier.
5. **Image paths**: `\graphicspath{{./figures/}}` (note the double braces — they're the LaTeX syntax for multiple search paths). Just `figures/` without braces silently fails.
6. **Aspect ratio**: `aspectratio=169` for modern projectors. Default beamer is 4:3 and looks dated.
7. **Themes affect color of headers + footers, but not the body.** `Madrid` is a safe default. Avoid `Warsaw` (very busy) and `Berlin` (cluttered).
8. **`\maketitle` doesn't exist in beamer** — use `\frame{\titlepage}` instead.
