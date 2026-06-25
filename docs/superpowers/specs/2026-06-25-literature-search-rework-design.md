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
identifier-based metadata import workflows such as Zotero.

## Goals

1. Preserve the fast arXiv path for CS/AI/math/physics-style preprint searches.
2. Add a general cross-disciplinary literature-search contract that can route
   to different source profiles.
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
- Do not require API keys for the first implementation slice unless the chosen
  provider cannot function without one.

## Proposed Tool Shape

### `paper-search-arxiv`

Rename or reposition the existing `paper-search` contract as the arXiv profile.
It remains useful for:

- CS, AI, ML, math, physics, statistics, quantitative methods;
- quick preprint discovery;
- simple BibTeX generation when the assignment only needs supporting citations.

The updated contract must state:

- output status is normally `metadata_only` or `abstract_read`, not
  `full_text_read`;
- arXiv is one provider, not the default answer for all disciplines;
- if the `.venv` lacks `arxiv`, the stage either uses a documented HTTP fallback
  or records a tool dependency blocker;
- generated BibTeX must include identifier and provider provenance.

### `literature-search`

Add a new top-level tool for cross-disciplinary search. It should read:

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

## Source Profiles

The first implementation should define profiles as guidance, not as hard-coded
pipelines:

| Profile | When to use | Primary sources | Notes |
|---|---|---|---|
| `cs_ai` | AI, CS, ML, systems, data science | arXiv, Semantic Scholar, OpenAlex, Crossref | Prefer DOI/published version when available. |
| `general` | mixed academic topics | OpenAlex, Crossref, Semantic Scholar | Good default when discipline is unclear. |
| `biomed` | medicine, health, biology, psychology adjacent to health | PubMed/NCBI E-utilities, PMC, Europe PMC, Crossref | Distinguish PubMed abstract from PMC full text. |
| `education_social` | education, pedagogy, sport/social science, sociology, communication | ERIC, OpenAlex, Crossref, Semantic Scholar | ERIC is especially useful for education literature and reports. |
| `humanities_policy` | history, literature, policy, area studies, professional practice | OpenAlex, Crossref, web search, library/manual blockers | Expect more books, chapters, reports, and paywalls. |
| `manual_broad` | when APIs underperform or the task is open-ended | parallel Subagents using web and preserved course sources | Emphasize search log and blockers over false completeness. |

The tool may search more than one profile when the topic crosses fields.

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

For broad or non-CS topics, the stage may dispatch focused Subagents. Good
splits:

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

- `paper-search`/`paper-search-arxiv` must declare arXiv as a profile, not a
  universal search tool.
- Literature outputs must include access-depth vocabulary and forbid treating
  abstract/metadata as full-text evidence.
- `literature-search` must define provider profiles for at least `cs_ai`,
  `general`, `biomed`, `education_social`, and `manual_broad`.
- Manual blockers must be documented with `needs_manual_download`.
- `writing-helper` must know to read `literature/references.bib` and the
  literature report when present.
- Existing tests that forbid `source_findings.compact.md` as a standard
  interface must remain valid.

Implementation verification should include one no-network or mocked-provider
unit test and one live smoke test with a small query in at least two profiles:
`cs_ai` and `education_social` or `biomed`.

## Open Questions For Implementation

1. Should the first slice use only no-key providers (`OpenAlex`, `Crossref`,
   arXiv HTTP, PubMed E-utilities) and leave Semantic Scholar/CORE API-key
   support for later?
2. Should `literature/` live beside `draft/` in the workbench, or under
   `references/external/literature/` for stronger preservation semantics?
3. Should `references.bib` remain at the workbench root for compatibility, or
   should downstream tools move fully to `literature/references.bib`?
4. Should the first implementation include automatic PDF text extraction for
   open-access URLs, or only record `full_text_available` and leave full reading
   to a follow-up?

Recommended first slice: implement profile-aware metadata and abstract search
with no-key providers, structured access statuses, blocker reporting, and
writing-helper integration. Defer automatic full-text download/extraction until
the audit trail is stable.
