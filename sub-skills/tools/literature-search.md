---
name: literature-search
description: Unified scholarly source discovery with provider fallback, parallel Subagent search, access-depth reporting, BibTeX output, and manual-download blockers.
---

# literature-search

Find scholarly sources for a writing or research stage. This is the single
active literature search tool. It replaces the old arXiv-only `paper-search`
contract while keeping arXiv as one internal provider.

This tool is best-effort and evidence-honest: search broadly, degrade
automatically when a provider is unavailable, and report access depth instead of
pretending that metadata or abstracts are full-text evidence.

## Contract

- **reads:**
  - `spec.md`
  - `investigation/alignment_brief.md`
  - `pipeline_design.md`
  - `investigation/rubric.md`
  - `references/REFERENCE_INDEX.md`
  - `references/**`
- **writes:**
  - `literature/search_log.jsonl`
  - `literature/candidates.json`
  - `literature/included_sources.json`
  - `literature/excluded_sources.json`
  - `literature/access_blockers.md`
  - `literature/references.bib`
  - `literature/literature_search_report.md`
  - `references.bib` as a compatibility copy when downstream tools still expect
    the root-level BibTeX file
- **does not write:**
  - final prose
  - final `spec.md`

## Guidance

### Ground the search

Do not search from the assignment title alone. Read the assignment workbench and
derive 2-4 query angles from the actual topic, required methodology, citation
style, and preserved course sources.

Good query angles include:

- core topic terms from `spec.md`;
- method terms from rubric or course materials;
- population/context terms from the assignment;
- discipline-specific terms from preserved source documents.

### Provider selection and automatic fallback

Provider choice is internal to this tool. Start with broadly useful providers
and add topic-sensitive sources. If any provider is blocked, unavailable,
rate-limited, thin, or mismatched, use automatic fallback instead of stopping.

Default sequence:

1. Try Crossref for broad DOI metadata.
2. Try arXiv when the topic is CS, AI, ML, math, statistics, physics,
   quantitative finance, or preprint-oriented.
3. Try PubMed/NCBI E-utilities and Europe PMC for biomedical, health,
   life-science, clinical, or psychology-adjacent topics.
4. Try ERIC for education, pedagogy, curriculum, student learning, teaching, or
   education policy topics.
5. Try Semantic Scholar only through endpoints available in the current auth
   mode; record degraded mode when no key is configured.
6. Try OpenAlex and CORE only when keys are configured; otherwise mark them as
   unavailable or `blocked`.
7. If API sources remain thin, use web search and parallel Subagents.

Record each attempt in `literature/search_log.jsonl` with provider, query,
result count, status, and fallback reason.

### Provider authentication

Keep provider authentication explicit. Do not hard-code keys in skill docs,
scripts, or workbench artifacts.

| Provider | Auth status | Use without configured key |
|---|---|---|
| arXiv API | none required | Yes, with polite rate limiting. |
| Crossref REST API | none required for public access; `mailto` strongly recommended | Yes, use `mailto`/User-Agent when configured. |
| PubMed/NCBI E-utilities | optional key increases rate limit | Yes, throttle to unauthenticated limits. |
| Europe PMC | no key for article REST API | Yes, with polite rate limiting. |
| ERIC API | no account in normal public API flow | Yes, but smoke-test before relying on it. |
| Semantic Scholar | optional key for reliability; some endpoints require auth | Yes only for unauthenticated endpoints; record degraded mode. |
| OpenAlex | API key required for normal API use | No; skip or mark `blocked` until `OPENALEX_API_KEY` or equivalent is configured. |
| CORE | API key required | No; skip or mark `blocked` until configured. |

### Parallel Subagents

Use parallel Subagents for broad, source-sparse, or cross-disciplinary topics.
They are a robustness layer, not final authority.

Good splits:

- theory/background literature;
- empirical/domain studies;
- methods and measurement;
- official reports, grey literature, or professional guidance;
- counterarguments and limitations.

Each Subagent returns candidates, access status, exact queries, source URLs,
saved paths if any, and blockers. Subagents must not decide the final
bibliography or write final prose. The Main Agent merges and screens candidates.

### Candidate schema

Every candidate in `literature/candidates.json` must include stable fields:

```json
{
  "id": "smith2024source",
  "title": "Source title",
  "authors": ["Author One", "Author Two"],
  "year": 2024,
  "source_type": "journal_article",
  "provider": "crossref",
  "provider_url": "https://example.org/source",
  "doi": "10.xxxx/example",
  "pmid": null,
  "arxiv_id": null,
  "venue": "Journal or conference",
  "abstract": "Abstract text when available",
  "open_access_url": "https://example.org/fulltext",
  "full_text_path": null,
  "access_status": "abstract_read",
  "read_depth_note": "Abstract and metadata read; full text was not available.",
  "relevance_note": "Why this source may support the assignment.",
  "used_for": ["background", "method"],
  "blocker": null,
  "bibtex_key": "smith2024source"
}
```

Allowed `access_status` values:

- `metadata_only`: title/authors/year/source identifiers only.
- `abstract_read`: metadata plus abstract read.
- `outline_read`: table of contents, landing page, abstract, or chapter outline
  read, but not the full body.
- `full_text_available`: a legal full text URL exists, but this run did not
  read it yet.
- `full_text_read`: full text was read or extracted enough to support claims.
- `needs_manual_download`: likely relevant but blocked by login, library access,
  paywall, broken PDF extraction, or manual file requirement.
- `blocked`: provider/network/search failure prevented meaningful assessment.

Writing stages must not treat abstracts or metadata as full-text evidence. If a
draft cites a source that is not `full_text_read`, the citation context must
make the evidence depth clear or use the source only for shallow background.

### Manual-download blockers

When a candidate is likely useful but blocked:

1. Add it to `literature/access_blockers.md` with title, authors, DOI/URL, why
   it matters, and exactly what the user should provide.
2. Mark the candidate `needs_manual_download`.
3. Continue automatically with other providers, web search, and parallel
   Subagent discovery.
4. Pause only when every route fails and no minimally usable source set remains.

Do not silently replace a blocked required source with a weaker source unless
the substitution is recorded in `literature/literature_search_report.md`.

## Output expectations

`literature/literature_search_report.md` must include:

- query angles used;
- providers attempted, skipped, degraded, or blocked;
- included sources grouped by how they will support the assignment;
- excluded sources with short reasons;
- access-depth summary;
- manual-download items and remaining evidence gaps.

`literature/references.bib` must include only sources present in
`included_sources.json`. Do not fabricate BibTeX entries. If metadata is
incomplete, write the source to `access_blockers.md` or
`excluded_sources.json` instead of inventing missing fields.

## Self-check

- [ ] Search terms came from `spec.md`, confirmed alignment, rubric, or
      preserved references, not the title alone.
- [ ] `search_log.jsonl` records attempted providers and fallback reasons.
- [ ] Key-required providers without configured keys are marked unavailable or
      `blocked`.
- [ ] Access status is present for every candidate.
- [ ] Abstracts and metadata are not described as full-text evidence.
- [ ] Parallel Subagents were used for broad or thin topics, or the report
      explains why single-pass search was sufficient.
- [ ] `access_blockers.md` lists manual-download needs.
- [ ] `literature/references.bib` and compatibility `references.bib` contain no
      fabricated entries.
