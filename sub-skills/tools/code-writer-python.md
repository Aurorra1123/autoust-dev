---
name: code-writer-python
description: Python-specific conventions for code-writer. Loaded by code-writer.md when lang is python. Do not load from _index.md.
---

# code-writer-python

Loaded by `code-writer.md` on demand. Do not load directly from `_index.md`.

These are **reference defaults** — if the task spec explicitly requires a different
setup (e.g. "use pip instead of uv", "flat structure"), follow the spec.

## Environment management

- Default: use `uv` for Python project management (init, add, run)
- If `uv` is not available, fall back to `pip` + `venv`
- If spec says "no package manager" or "use conda", follow spec

## Project structure

Default structure for non-trivial projects (more than one file):

```text
src/
├── __init__.py
├── <module>.py          # main implementation
├── test_<module>.py     # pytest tests
└── README.md
```

For notebook-based assignments:

```text
draft/
├── <name>.ipynb         # main notebook
└── requirements.txt     # dependencies (pip freeze)
```

Do NOT dump all files flat in the work_dir root. Keep source code in `src/`
and notebooks in `draft/`.

## Notebook conventions

- Build notebooks using `nbformat` — do not manually write JSON
- **The notebook must be executed after creation** — output cells must contain
  actual execution results, not fabricated estimates
- If execution fails, fix and re-execute; do not leave empty output cells
- Include `requirements.txt` with exact versions (`pip freeze`)

## pytest conventions

- One test file per source module: `test_<module>.py`
- Use `@pytest.mark.parametrize` for data-driven tests from spec
- Use `pytest.skip` with reason for unimplemented parts (with `[CLARIFICATION NEEDED]` comment)
- Fixtures for shared setup (datasets, temp directories)
- All tests must pass for the stage to be considered complete

## Common pitfalls (Python-specific)

1. **`if __name__ == "__main__":` is mandatory** — pytest imports the file, module-level code breaks tests
2. **Don't shadow stdlib names** — `solution.py` is fine; `os.py`/`sys.py`/`json.py` break imports
3. **Use `pathlib`** for path handling, never hard-code paths
4. **Seed random/numpy.random** with 42 if spec requires reproducibility
5. **Don't add `print()` debug statements** — auto-graders parse stdout
6. **Function names follow spec verbatim** — if spec says `fit_ols(X, y)`, don't write `train_ordinary_least_squares(X, y)`
