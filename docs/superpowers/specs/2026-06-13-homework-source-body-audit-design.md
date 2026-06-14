# Homework Source Body Audit Design

> 2026-06-13 · Design for strengthening `do-homework` reconnaissance so broad Canvas indexing is paired with bounded, subagent-driven source body reading.

## Context

The current homework flow already indexes Canvas assignment surfaces broadly:
assignment, rubric, front page, syllabus, modules, module items, pages, files,
external URLs, and fetched references. The failure mode exposed by the
UCUG1808 proposal dry run was not lack of a Canvas surface list. The failure was
that a proposal PDF and final-project PDF were treated as enough context before
the run had truly read the course's Week 8 research-methods material.

The improved flow must make a stronger distinction between:

- source discovery through metadata and Canvas structure;
- source body reading through PDFs, PPTX slide text, Google Docs, pages, and
  extracted text artifacts;
- final assignment judgment, which remains the Main Agent's responsibility.

## Goals

1. Make the Main Agent/subagent boundary explicit during homework
   reconnaissance.
2. Add appendix body evidence plus a compact findings layer that records which
   candidate sources were truly read, how they were read, and why they matter or
   do not matter.
3. Use subagents for scalable reading of suspicious sources without flooding the
   Main Agent context.
4. Avoid over-reading whole courses by using a bounded candidate ranking and
   reading budget.
5. Support long PDFs/PPTX files by extracting text and reading relevant evidence
   windows before escalating to full read.
6. Keep `references/` navigable even when each PDF has sibling `.txt` and
   `.links.json` artifacts.
7. Validate the new contract on the real UCUG1808 project proposal
   reconnaissance after clearing its current workbench.

## Non-Goals

- Do not build a standalone multi-agent runtime.
- Do not let subagents write the final `spec.md`, final `review_a.json`, or user
  alignment decisions.
- Do not recursively download arbitrary Canvas file folders.
- Do not add course-specific rules for UCUG1808 or any other course.
- Do not replace existing PDF link annotation preservation. PDF visible text and
  link annotations remain separate source evidence.

## Actor Boundaries

### Main Agent

The Main Agent owns coordination and final judgment. It:

1. Creates or refreshes the workbench and `prelaunch_startup_inventory.json`.
2. Defines forbidden context, including old submissions, stale pipelines, old
   reviews, transcripts, and archive contents unless explicitly allowlisted.
3. Reads the user request, Canvas assignment shell, rubric summary, and current
   startup inventory to classify the task shape.
4. Dispatches `metadata_scout` for full Canvas/source indexing.
5. Reviews and approves a bounded `reading_plan.compact.json`.
6. Dispatches one or more `content_scout` children using the templates below.
7. Reads `source_findings.compact.md` plus any exact parent source windows
   requested by content scouts.
8. Runs the parent self-check against the compact plan, compact findings,
   syllabus, direct-spec strong matches, blocked resources, and terminal
   artifacts.
9. Writes the final `spec.md`, `explore_context.md`, `review_a.json`, and
   `pipeline_design.md`.

The Main Agent should not do broad source body reading as a substitute for
content scouts unless child dispatch is unavailable. Inline fallback for a
non-trivial run must be recorded in `explore_manifest.json` as a process
concern.

### Metadata Scout

The `metadata_scout` is a read-only child that performs broad indexing and
initial candidate ranking. It may read raw Canvas JSON, module item lists, file
metadata, assignment-file listings, titles, links, and short Canvas summaries.
If it reads a full Canvas page, syllabus body, front-page body, PDF/PPTX body,
or external document body, that read must be recorded as body evidence or
assigned to a `content_scout`.

It writes:

```text
investigation/_appendix/scout_receipts/metadata_scout_result.json
investigation/_appendix/source_index.json
investigation/reading_plan.compact.json
```

Legacy `investigation/source_candidates.json` and
`investigation/reading_plan.json` may remain as compatibility aliases during
migration, but they are not the normal parent interface.

It must not promote any source to `precise_match` because it has not read the
source body. It may classify candidates as `required`, `high_signal`,
`supporting`, `low_signal`, `forbidden`, or `blocked`.

### Content Scouts

`content_scout` children read source bodies. The Main Agent splits them by
scope so they can run in parallel without overlapping work:

- `spec_content_scout`: direct assignment, proposal, final project, rubric, or
  external spec files.
- `methods_content_scout`: research-methods, topic-selection, timeline,
  literature-review, questionnaire, fieldwork, or methodology sources.
- `theme_content_scout`: course topic slides/readings that may influence an
  open-ended topic choice.
- `policy_content_scout`: syllabus, collaboration, late policy,
  academic-integrity, AI/tool policy, or submission rules when these are not
  already resolved.

Each content scout writes:

```text
investigation/_appendix/scout_receipts/<scope>_content_result.json
investigation/_appendix/body_evidence_fragments/<scope>_content.json
```

Content scouts also write parent-readable findings into:

```text
investigation/source_findings.compact.md
```

Content scouts must record `read_mode`, evidence windows, and relevance
classification in their own receipt or fragment. Legacy
`source_body_audit_fragments/` and `source_body_audit.json` may remain as
compatibility aliases. Content scouts must not write final `spec.md` or
concurrently write shared parent verdict artifacts.

### Parent Self-Check

After content scout receipts and `source_findings.compact.md` exist, the Main
Agent performs the final source sufficiency check. It reads
`reading_plan.compact.json`, `source_findings.compact.md`, terminal
reconnaissance artifacts, and any exact parent source windows requested by
content scouts.

It must block `proceed` when:

- a `required` or `high_signal` source remains `metadata_only`;
- a proposal/research/open-ended task lacks methods/topic-selection evidence
  and no explicit evidence proves such material is unavailable;
- a source is used as spec/rubric/input/context evidence without body-read
  evidence;
- forbidden prior submissions or stale process artifacts were read as task
  context.

## Candidate Ranking

`metadata_scout` assigns each candidate one of these levels:

| Level | Meaning | Content scout body-read default |
|---|---|---|
| `required` | Direct assignment file, direct spec, rubric, final project/proposal file, required input | Assign to `content_scout`; Main Agent fully reads only if it is syllabus or a direct-spec strong match |
| `high_signal` | Title/context suggests proposal, research, methods, timeline, topic selection, literature review, questionnaire, fieldwork, grading criteria | Assign to `content_scout` unless explicitly excluded by Main Agent |
| `supporting` | Same week/module/project topic source that may inform an open-ended topic or course framing | Read selectively under budget |
| `low_signal` | Course material with no clear relation to the assignment | Metadata only |
| `forbidden` | Prior submission, stale pipeline, old review, archive, transcript, or startup-forbidden context | Do not read |
| `blocked` | Login wall, unavailable download, parse failure, or unclear access | Record in `unreachable.txt` or process concerns |

The ranking should prefer recall for open-ended assignments, but the reading
plan must remain bounded. A normal first pass should include all `required` and
`high_signal` candidates, plus a small number of `supporting` candidates chosen
by module proximity and topic relevance.

## Long Document Reading

For long PDFs/PPTX files, content scouts should not dump full text into the
Main Agent context. They should:

1. Save the file under `references/`.
2. Save extracted text beside the file, preserving existing PDF sibling
   conventions such as `.pdf.txt` and `.pdf.links.json`.
3. Record page count, slide count, byte count, and extraction status.
4. Search for task-sensitive terms such as assignment title terms, proposal,
   final project, research, method, timeline, literature review, questionnaire,
   field research, rubric, grading, submission, and topic-selection terms.
5. Read and summarize relevant evidence windows around matching pages/slides.
6. Escalate to broader read only when the document is a direct spec or when
   sparse windows cannot answer the assignment question.

Appendix body evidence must preserve the evidence window pointers, and
`source_findings.compact.md` must summarize those pointers so the Main Agent can
verify the content scout's judgment without re-reading the entire document.

## Workbench Artifacts

The strengthened reconnaissance writes:

```text
investigation/_appendix/source_index.json
investigation/reading_plan.compact.json
investigation/_appendix/body_evidence_fragments/
investigation/source_findings.compact.md
```

`_appendix/source_index.json` is metadata-level indexing.
`reading_plan.compact.json` is the Main Agent-approved bounded reading budget.
Content scouts write full fragments under `_appendix/body_evidence_fragments/`.
`source_findings.compact.md` is the normal parent-readable interface for
relevant source-body findings and parent source read requests. Existing
`source_candidates.json`, `reading_plan.json`, `source_body_audit_fragments/`,
and `source_body_audit.json` may remain as compatibility aliases, but they are
not normal Main Agent reads.

## Reference Organization

`references/` must remain easy for downstream agents to scan. New runs should
organize source material by type while preserving source-adjacent companion
files:

```text
references/
├── source_docs/
│   └── <slug>/
│       ├── <slug>.pdf
│       ├── <slug>.pdf.txt
│       └── <slug>.pdf.links.json
├── slides/
│   └── <slug>/
│       ├── <slug>.pptx
│       └── <slug>.pptx.txt
├── external/
│   └── <slug>.txt
└── pdf_links.json
```

Canvas-native bodies stay canonical under `canvas/*.json`; optional readable
syllabus or page notes may exist, but they are derived convenience copies and
must not become evidence gates. The key invariant for source documents is that
companion artifacts stay beside their source within the same directory. Policy
text and tests should use `references/**/*.pdf.links.json` when describing new
behavior, while still allowing old `references/*.pdf.links.json` workbenches.

## Open-Ended Assignment Gate

For proposal, research, final-project, essay-topic, or other open-ended tasks,
`review_a.json.verdict` must not be `proceed` unless:

- deliverables are concrete;
- at least one assignment/spec source has body-read evidence;
- methods/topic-selection/course guidance has body-read evidence, or a reviewer
  records why no such source exists;
- supporting course-topic material is either read enough to inform topic choice
  or explicitly judged unnecessary;
- no `required` or `high_signal` candidate remains unread;
- source reading stayed within the bounded plan or over-budget reading is
  justified in `source_findings.compact.md` and `review_a.json`.

## Reconvergence Gate

Missing terminal reconnaissance artifacts are a failed acceptance run. A run
that writes appendix body evidence and `source_findings.compact.md` but omits
`spec.md`, `investigation/rubric.md`, or `investigation/review_a.json` has not
reached the end of reconnaissance. source_findings.compact.md alone is
insufficient because it only summarizes source findings; it does not contain the
Main Agent's final assignment spec, rubric/criteria interpretation, or proceed /
recover / stop verdict.
Acceptance check sentence: source_findings.compact.md alone is insufficient.

If a coordinator stalls after scout receipts or compact findings, it must
either complete those terminal artifacts or record a recover/blocking
`review_a.json` or `stage_reviews/process_concerns.jsonl` before stopping.
Filesystem receipts without transcript evidence are recovery evidence, not clean
child-isolation validation; they may support an inline continuation, but the
acceptance report must say that clean child isolation was not validated.
Acceptance check sentence: filesystem receipts without transcript evidence are recovery evidence, not clean child-isolation validation.

## Subagent Prompt Templates

### Metadata Scout

```text
You are metadata_scout for one homework reconnaissance workbench.
Read only current-run allowed Canvas/source metadata. Do not read forbidden old
submissions, archives, old pipelines, old reviews, or transcripts.

Inputs:
- prelaunch_startup_inventory.json
- canvas/assignment.json
- canvas/rubric.json
- canvas/front-page.json
- canvas/syllabus.json
- canvas/modules.json
- canvas/module-items-*.json
- canvas/page-*.json
- canvas/file-*.json
- canvas/assignment-files.json

Write:
- investigation/_appendix/scout_receipts/metadata_scout_result.json
- investigation/_appendix/source_index.json
- investigation/reading_plan.compact.json

Classify each candidate as required, high_signal, supporting, low_signal,
forbidden, or blocked. Explain the origin and reason. Do not classify any
source as precise_match because you are not reading bodies. If you need to read
full page, syllabus, front-page, PDF/PPTX, or external body text, stop and ask
the Main Agent to assign it to a content scout or record the read through a
body-audit fragment.
```

### Content Scout

```text
You are <scope>_content_scout for one homework reconnaissance workbench.
Read only the candidates assigned to your scope in investigation/reading_plan.compact.json.
Do not read forbidden candidates.

For each assigned source:
- fetch or inspect the body artifact when allowed;
- extract/save text when needed;
- preserve source-adjacent companion artifacts such as PDF text and PDF links;
- for long PDFs/PPTX, use keyword windows and page/slide evidence before
  escalating to full read;
- classify as precise_match, supporting_context, weak_related, excluded, or
  blocked;
- record evidence pointers and reading cost.

Write:
- investigation/_appendix/scout_receipts/<scope>_content_result.json
- investigation/_appendix/body_evidence_fragments/<scope>_content.json
- investigation/source_findings.compact.md

Do not write final spec.md, review_a.json, or pipeline_design.md.
Do not write shared parent verdict artifacts directly.
```

### Parent Self-Check Prompt

```text
You are the Main Agent parent self-check for one homework reconnaissance
workbench. Read reading_plan.compact.json, source_findings.compact.md, terminal
reconnaissance artifacts, and any exact parent source windows requested by
content scouts.

Check:
- required/high_signal candidates have body-read evidence or justified blockers;
- metadata_only sources are not used as precise evidence;
- proposal/research/open-ended assignments include methods/topic-selection
  evidence or a clear unavailable judgment;
- forbidden/stale sources were not read as task context;
- reading cost is bounded and justified.

Write the verdict and any recover/blocking items into investigation/review_a.json.
Do not outsource this final judgment to another child role.
```

## UCUG1808 Acceptance Scenario

After implementation, validate with a clean UCUG1808 workbench:

1. Remove or archive
   `data/homework/UCUG1808/23014-project-proposal-files` so the run simulates a
   first attempt.
2. Dispatch a child agent to run `do-homework` for the UCUG1808 project
   proposal through the reconnaissance stage only.
3. Observe whether the coordinator creates the expected scout ledger rows and
   receipts.
4. Verify `metadata_scout` indexes all modules and module items.
5. Verify `content_scout` reads the direct proposal/final-project files and the
   Week 8 research-methods source.
6. Verify the Week 8 `Timeline& Research in Sport Social Sciences` PDF is
   classified as methods/topic-selection guidance, not missed.
7. Verify related topic materials such as Week 8 mega-events and Week 10
   celebrity/fandom slides are either read as supporting context or explicitly
   excluded with evidence.
8. Verify prior submitted artifacts are forbidden and unread.
9. Verify `review_a.json` would not proceed if methods/topic-selection evidence
   is missing.
10. Verify reading cost is acceptable: no arbitrary full-course file dump and no
    unbounded reading of unrelated course documents.
11. Verify the reconvergence gate: `spec.md`, `investigation/rubric.md`, and
    `investigation/review_a.json` exist, or a recover/blocking process concern
    explicitly names the missing terminal artifacts.

If the acceptance run misses a required/high-signal source, over-reads low-value
materials, relies on Main Agent manual rescue, lacks terminal reconnaissance
artifacts, or relies only on filesystem receipts without transcript evidence,
the implementation must be iterated before treating the workflow as accepted.

## Tests

Policy tests should assert that:

- `assignment-recon.md` documents compact reading plans, appendix body evidence,
  read modes, candidate ranking, content scouts, long-document windows, and
  reference organization.
- `do-homework.md` documents the Main Agent/subagent boundary and requires
  metadata/content scout receipts before alignment for non-trivial
  source-heavy assignments.
- `runtime-agent-protocol.md` documents the source/spec scout split and
  preserves Main Agent final judgment.
- `docs/PITFALLS.md` records the UCUG1808 proposal failure mode generically.
- new policy wording is course-agnostic except for the dedicated acceptance
  scenario.
