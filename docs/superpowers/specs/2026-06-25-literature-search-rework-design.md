# Literature Search Rework Design

## Context

AutoStudy currently has two different "collection" concepts that are easy to
confuse:

- `reference_collector` is the homework reconnaissance preservation child. It
  saves task-relevant Canvas, PDF, deck, external page, dataset, and
  Canvas-native evidence under `references/`. It does not write final source
  judgments.
- `paper-search` is a narrow post-recon writing tool. It searches arXiv
  metadata, writes `references.bib` and `references.json`, and explicitly does
  not download or read paper full text.

The current `paper-search` contract was acceptable for the M3 MVP because it
only needed to supply a few BibTeX entries. It is not robust enough for
cross-disciplinary homework: humanities, social science, education, biomedical,
professional, and applied policy topics often need sources that are not on
arXiv, and the current fallback is only a Google Scholar URL stub.

External search practice points in the same direction. PRISMA-S emphasizes
reporting search sources and strategies. Cochrane guidance emphasizes planning
the search process, documenting sources searched, terms used, screening
decisions, and access limits. Modern open scholarly APIs split coverage across
OpenAlex, Crossref, Semantic Scholar, PubMed/PMC, CORE, Europe PMC, ERIC, and
identifier-based metadata import workflows such as Zotero. These providers do
not have the same authentication model: some are usable without keys, some use
optional keys for rate limits, and some require keys for normal API access.
AutoStudy must treat authentication as provider capability metadata, not an
implementation detail.

## Goals

1. Replace the narrow arXiv-only workflow with one unified
   `literature-search` tool.
2. Preserve the fast arXiv path as an internal provider option for
   CS/AI/math/physics-style preprint searches.
3. Require every candidate source to declare access depth:
   `metadata_only`, `abstract_read`, `outline_read`, `full_text_available`,
   `full_text_read`, `needs_manual_download`, or `blocked`.
4. Make literature search outputs auditable enough for writing-helper and human
   review without pretending that metadata or abstracts are full-text evidence.
5. Support parallel Subagent exploration for broad topics, while keeping final
   inclusion and source-use judgment with the Main Agent.
6. Record manual-download blockers plainly so the user can provide PDFs or
   library access when needed.

## Non-Goals

- Do not build a full systematic-review platform.
- Do not scrape Google Scholar or paywalled databases.
- Do not bypass publishers, libraries, robots rules, or access controls.
- Do not restore the old `metadata_scout -> reading_plan.compact.json ->
  content_scout -> source_findings.compact.md` standard interface.
- Do not make Subagents write final `spec.md`, final literature conclusions, or
  final citation claims.
- Do not assume every named provider works without an API key. The first slice
  should run with no configured keys by using no-key or optional-key providers,
  and should mark key-required providers as unavailable until configured.

## Proposed Tool Shape

Add one top-level `literature-search` tool for all scholarly source discovery.
Do not expose separate discipline tools or profile names to the pipeline. The
tool reads the assignment context, writes a search plan, chooses providers based
on topic hints and available credentials, and records what it did.

The existing `paper-search` name should become a compatibility alias or be
retired after downstream docs move to `literature-search`. arXiv remains an
internal provider, not a standalone user-facing tool.

The tool should read:

```text
spec.md
investigation/alignment_brief.md
pipeline_design.md
investigation/rubric.md
references/REFERENCE_INDEX.md
references/**
```

It should write:

```text
literature/
├── search_plan.md
├── search_log.jsonl
├── candidates.json
├── included_sources.json
├── excluded_sources.json
├── access_blockers.md
├── references.bib
└── literature_search_report.md
```

The report is the Main Agent and writing-helper handoff. The JSON files are the
machine-checkable audit trail.

## Provider Selection

Provider choice is internal to `literature-search`. The first implementation
should use a simple ranked plan instead of separate profile contracts:

1. Always start with broadly useful metadata sources that are available without
   configured keys: Crossref plus one topic-sensitive provider when appropriate.
2. Use arXiv when the assignment context contains CS, AI, ML, math, statistics,
   physics, quantitative finance, or preprint-oriented language.
3. Use PubMed/NCBI E-utilities and Europe PMC when the context is biomedical,
   health, life-science, clinical, or psychology-adjacent.
4. Use ERIC when the context is education, pedagogy, curriculum, student
   learning, teaching, or education policy.
5. Use Semantic Scholar only through endpoints that work in the current
   authentication mode; record degraded mode when no key is configured.
6. Use OpenAlex and CORE only when keys are configured; otherwise record them as
   unavailable rather than silently depending on them.
7. If API sources are thin or mismatched, use web search and parallel Subagents
   as a fallback discovery path, with stronger blocker/access reporting.

The generated `search_plan.md` must show which providers were selected, which
were skipped, and why. This keeps the interface simple while preserving audit
quality.

## Provider Authentication Matrix

The implementation must keep provider authentication explicit. Current expected
status:

| Provider | Auth status | Use without configured key |
|---|---|---|
| arXiv API | none required | Yes, with polite rate limiting. |
| Crossref REST API | none required for public access; `mailto` strongly recommended | Yes, use `mailto`/User-Agent when configured. |
| PubMed/NCBI E-utilities | optional key increases rate limit | Yes, throttle to unauthenticated limits. |
| Europe PMC | no key for article REST API | Yes, with polite rate limiting. |
| ERIC API | no account in normal public API flow | Yes, but smoke-test during implementation. |
| Semantic Scholar | optional key for reliability; some endpoints require auth | Yes only for endpoints that allow unauthenticated use; record degraded mode. |
| OpenAlex | API key required for normal API use | No; skip or mark `blocked` until `OPENALEX_API_KEY` or equivalent is configured. |
| CORE | API key required | No; skip or mark `blocked` until configured. |

Provider configuration should be read from environment variables or a local
ignored config file, never hard-coded in skill docs or workbench artifacts.

## Candidate Schema

Each candidate must be represented with stable fields:

```json
{
  "id": "smith2024topic",
  "title": "Source title",
  "authors": ["Author One", "Author Two"],
  "year": 2024,
  "source_type": "journal_article",
  "provider": "openalex",
  "provider_url": "https://openalex.org/...",
  "doi": "10.xxxx/example",
  "pmid": null,
  "arxiv_id": null,
  "venue": "Journal or conference",
  "abstract": "Abstract text when available",
  "open_access_url": "https://...",
  "full_text_path": null,
  "access_status": "abstract_read",
  "read_depth_note": "Abstract and metadata read; no full text available through open source.",
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
- `full_text_available`: a legal full text URL exists, but the run did not read
  it yet.
- `full_text_read`: full text was read or extracted enough to support claims.
- `needs_manual_download`: likely relevant but blocked by login, library access,
  paywall, broken PDF extraction, or manual file requirement.
- `blocked`: provider/network/search failure prevented meaningful assessment.

Writing stages must not cite a source as body evidence unless its status is
`full_text_read` or the text explicitly states that only metadata/abstract was
used.

## Parallel Subagent Pattern

For broad or source-sparse topics, the stage may dispatch focused Subagents.
Good splits:

- theory/background literature;
- empirical/domain studies;
- methods and measurement;
- official reports, grey literature, or professional guidance;
- counterarguments and limitations.

Each Subagent returns candidates, access status, exact queries, source URLs,
saved paths if any, and blockers. It must not decide the final bibliography or
write final prose. The Main Agent merges and screens the candidates, writes
`included_sources.json`, `excluded_sources.json`, and the user-facing report.

## Integration With Existing Recon

`reference_collector` remains the source-preservation child for Canvas homework
reconnaissance. It should not become a scholarly search engine.

`literature-search` runs after recon and alignment when the approved
`pipeline_design.md` contains a literature stage. It may read preserved course
sources to ground queries, but it writes its own `literature/` outputs instead
of changing `references/REFERENCE_INDEX.md` unless a future design explicitly
adds external scholarly preservation to the collector.

`writing-helper` should consume `literature/references.bib` and
`literature/literature_search_report.md`, not only root-level `references.bib`.
For backward compatibility, the tool may also copy or symlink the final BibTeX
to `<work_dir>/references.bib`.

## Manual Download Flow

When a candidate is likely useful but blocked:

1. Add it to `access_blockers.md` with title, authors, DOI/URL, why it matters,
   and exactly what the user should provide.
2. Mark the candidate `needs_manual_download`.
3. Continue with other sources when enough evidence remains for a draft.
4. If the assignment requires that exact source or the literature base is too
   thin, pause and ask the user for the PDF or library export.

The assistant must not silently replace a blocked required source with a weaker
source unless it records the substitution in the report.

## Testing Strategy

Add policy tests before implementation:

- `_index.md` and pipeline guidance expose one `literature-search` tool, not a
  family of discipline-specific search tools.
- The legacy `paper-search` path must either point to `literature-search` as a
  compatibility alias or be removed from active pipeline guidance.
- `literature-search` must declare arXiv as one provider, not a universal
  search backend.
- Literature outputs must include access-depth vocabulary and forbid treating
  abstract/metadata as full-text evidence.
- `literature-search` must document provider selection, skipped providers, and
  authentication state in `search_plan.md` or `search_log.jsonl`.
- Manual blockers must be documented with `needs_manual_download`.
- `writing-helper` must know to read `literature/references.bib` and the
  literature report when present.
- Existing tests that forbid `source_findings.compact.md` as a standard
  interface must remain valid.

Implementation verification should include one no-network or mocked-provider
unit test and one live smoke test with two small queries that exercise different
provider choices, such as one CS/AI query and one education or biomedical query.

## Open Questions For Implementation

1. Should the first slice support optional provider keys for OpenAlex,
   Semantic Scholar, and CORE, or explicitly defer all key-required provider
   wiring until the no-key audit trail is stable?
2. Should `literature/` live beside `draft/` in the workbench, or under
   `references/external/literature/` for stronger preservation semantics?
3. Should `references.bib` remain at the workbench root for compatibility, or
   should downstream tools move fully to `literature/references.bib`?
4. Should the first implementation include automatic PDF text extraction for
   open-access URLs, or only record `full_text_available` and leave full reading
   to a follow-up?

Recommended first slice: implement one `literature-search` contract with
metadata and abstract search through providers that work without configured keys
(`arXiv`, `Crossref`, `PubMed/NCBI E-utilities`, `Europe PMC`, and ERIC if live
smoke confirms the public endpoint), plus optional Semantic Scholar
unauthenticated endpoints when available. Treat OpenAlex and CORE as
key-required providers and report them as unavailable unless configured. Defer
automatic full-text download/extraction until the audit trail is stable.
