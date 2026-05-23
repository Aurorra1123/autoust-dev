---
name: paper-search
description: Search arxiv for paper references on a topic, produce a BibTeX file and JSON for downstream tools. No full-text scraping — metadata only.
---

# paper-search

Find references for a paper-writing task. Uses the `arxiv` Python package (installed in `.venv`). Outputs a BibTeX file ready for citation and a JSON file for the writing-helper to know what's available.

## Capabilities

- `search_papers` — query → bib + json with author/title/year/url

## Inputs / Outputs

```
Input:  topic keywords (list of strings, from task_profile or do-homework summary)
        max_results: int (default 5)
Output: <work_dir>/references.bib    (BibTeX, one @article per result)
        <work_dir>/references.json   (parallel JSON: [{key, title, authors, year, url, summary}, ...])
```

## Setup

```bash
.venv/bin/pip install arxiv          # already installed for MVP
```

No API key required. The `arxiv` package wraps the public arxiv export.arxiv.org API. Rate-limit: don't exceed ~1 query/3s.

## Invocation

The orchestrator (or do-homework) writes a small script into `<work_dir>/scripts/run_paper_search.py` and executes it. Template:

```python
# <work_dir>/scripts/run_paper_search.py
import arxiv
import json
import re
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parents[1]      # work_dir
QUERY = "deep learning fairness"                     # ← edit this per task
MAX_RESULTS = 5

def bib_key(authors, year, title):
    first_author_last = authors[0].split()[-1].lower()
    title_word = re.sub(r'[^a-z0-9]', '', title.lower().split()[0])
    return f"{first_author_last}{year}{title_word}"

search = arxiv.Search(
    query=QUERY,
    max_results=MAX_RESULTS,
    sort_by=arxiv.SortCriterion.Relevance,
)

bib_entries = []
json_entries = []

for r in arxiv.Client().results(search):
    authors = [a.name for a in r.authors]
    year = r.published.year
    key = bib_key(authors, year, r.title)
    bib_entries.append(f"""@article{{{key},
  title   = {{{r.title}}},
  author  = {{{' and '.join(authors)}}},
  year    = {{{year}}},
  journal = {{arXiv preprint arXiv:{r.entry_id.split('/')[-1]}}},
  url     = {{{r.entry_id}}}
}}""")
    json_entries.append({
        "key": key,
        "title": r.title,
        "authors": authors,
        "year": year,
        "url": r.entry_id,
        "summary": r.summary[:300],
    })

(WORK_DIR / "references.bib").write_text("\n\n".join(bib_entries), encoding="utf-8")
(WORK_DIR / "references.json").write_text(json.dumps(json_entries, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(bib_entries)} references")
```

Run:

```bash
.venv/bin/python "<work_dir>/scripts/run_paper_search.py"
```

## Fallback when arxiv has no hits

For non-CS / humanities topics (e.g. DLED3020 communication papers), arxiv often returns nothing relevant. In that case, write `references.json` with Google Scholar search URLs and a stub bib:

```python
json_entries = [{
    "key": "TODO",
    "title": "Search Google Scholar",
    "url": f"https://scholar.google.com/scholar?q={urllib.parse.quote(query)}",
    "summary": "arxiv returned no relevant hits — please search manually and add to references.bib",
}]
```

And drop a one-line `references.bib`:

```bibtex
% No arxiv hits for: <query>
% Add manual entries below.
```

`writing-helper` knows to use `[CITATION NEEDED]` placeholders when entries are missing.

## What this tool is NOT for

- ❌ Downloading PDFs of papers — metadata only
- ❌ Generating citations in-text — that's `writing-helper`'s job, this just supplies the bib
- ❌ Cross-checking citation accuracy — the agent must verify rough relevance before using

## Pitfalls

1. **Don't fabricate citations.** If arxiv returns 0 results, write the empty-bib + Scholar-URL fallback. Never invent a fake `@article{smith2023}`.
2. **The arxiv package can hang on a flaky network.** Wrap the loop in a 30s timeout if running unattended. Add `arxiv.Client(num_retries=2, page_size=10)` for robustness.
3. **Author names are sometimes `"Anonymous"` or single tokens** for preprints. The `bib_key` helper falls back to `lastword` — still produces a unique-ish key.
4. **arxiv IDs sometimes have version suffixes** (`2401.12345v3`). The split at `/` extracts the full versioned id — that's fine for citation. If you want a stable URL, strip `vN` at the end.
5. **Rate limit**: arxiv export API is generous (no key) but if running many queries back-to-back, sleep 3s between calls.
