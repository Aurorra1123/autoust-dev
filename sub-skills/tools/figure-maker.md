---
name: figure-maker
description: Generate a figure (line / bar / scatter) via matplotlib, output PDF + PNG. Used by paper / report / lab pipelines to produce charts referenced in draft markdown.
---

# figure-maker

Produce a single figure from a spec. The agent writes a matplotlib script and runs it. The figure lands at a deterministic path so `writing-helper` can reference it.

## Capabilities

- `make_figure` — figure spec → fig.pdf + fig.png

## Inputs / Outputs

```
Input:  figure_spec (a dict, usually written inline by the orchestrator):
          type: "line" | "bar" | "scatter"
          title: str
          xlabel: str
          ylabel: str
          data: dict (keys depend on type — see Invocation)
          style: "default" | "publication"
Output: <work_dir>/draft/figures/fig_<N>.pdf     (vector, for LaTeX embedding)
        <work_dir>/draft/figures/fig_<N>.png     (raster, for previews)
```

## Setup

```bash
.venv/bin/pip install matplotlib numpy     # already installed for MVP
```

## Invocation

Write the script to `<work_dir>/scripts/make_fig_N.py` and run it. The script template is short — the agent fills in the data inline.

### Line chart

```python
# <work_dir>/scripts/make_fig_1.py
import matplotlib.pyplot as plt
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = WORK_DIR / "draft" / "figures"
OUT_DIR.mkdir(exist_ok=True)
N = 1

x = [1, 2, 3, 4, 5]                       # ← fill from spec
y1 = [0.65, 0.71, 0.78, 0.82, 0.85]       # ← fill from spec
y2 = [0.60, 0.66, 0.70, 0.73, 0.76]

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(x, y1, marker="o", label="Method A")
ax.plot(x, y2, marker="s", label="Baseline")
ax.set_xlabel("Epoch")
ax.set_ylabel("Accuracy")
ax.set_title("Training accuracy over epochs")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()

fig.savefig(OUT_DIR / f"fig_{N}.pdf")
fig.savefig(OUT_DIR / f"fig_{N}.png", dpi=150)
print(f"wrote fig_{N}.pdf and fig_{N}.png")
```

### Bar chart

```python
# Replace the plot block with:
import numpy as np
categories = ["A", "B", "C", "D"]
values = [4.2, 3.1, 5.7, 2.8]
ax.bar(categories, values, color="steelblue")
ax.set_xlabel("Category")
ax.set_ylabel("Score")
ax.set_title("Comparison across categories")
```

### Scatter

```python
import numpy as np
rng = np.random.default_rng(0)
x = rng.normal(0, 1, 100)
y = 2 * x + rng.normal(0, 0.5, 100)
ax.scatter(x, y, alpha=0.6, s=20)
ax.set_xlabel("Feature 1")
ax.set_ylabel("Target")
ax.set_title("Feature vs target")
```

### Run

```bash
.venv/bin/python "<work_dir>/scripts/make_fig_1.py"
```

### Publication style (optional)

For a cleaner look without grid:

```python
plt.rcParams.update({
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
})
```

## What this tool is NOT for

- ❌ Multi-panel figures with complex subplot layouts — for MVP, one figure per script. If you need 4 panels, run 4 times.
- ❌ Reading data from external files (CSVs, etc.) — the agent inlines numeric data into the script directly. The data comes from the user's brief / rubric.
- ❌ Animations or interactive plots — static figure only.
- ❌ 3D rendering — use a different tool when needed.

## Pitfalls

1. **`fig.tight_layout()` before `savefig`** — without it, axis labels get clipped in the PDF.
2. **PDF figures embed in LaTeX vector** — don't include `dpi=` for the PDF version (only matters for PNG).
3. **Chinese in titles needs the same font as pdf-renderer**. matplotlib defaults won't have CJK. Add this once at the top:
   ```python
   import matplotlib
   matplotlib.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial']
   matplotlib.rcParams['axes.unicode_minus'] = False  # so the minus sign renders
   ```
4. **`numpy` default integer overflow on Apple Silicon**: if you compute large products, cast `np.int64`. For typical homework figures this never bites.
5. **Don't `plt.show()`** in the script — it blocks indefinitely when run non-interactively. Use `fig.savefig` then exit.
6. **The orchestrator embeds the figure later via writing-helper.** This tool just makes the file; it does NOT inject markdown.
7. **Keep report assets near the report.** For homework reports, prefer
   `draft/figures/` so `draft/report.md` can reference `figures/fig_1.png`.
   Older `figures/` workbench-root output is compatibility only.
