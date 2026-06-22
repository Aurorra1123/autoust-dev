# Homework A Compact Findings Design

> 2026-06-14 · Design update for shrinking `do-homework [A]` Main Agent context while preserving scout evidence and auditability.

## Context

The source-body audit flow fixed one problem: metadata discovery is no longer
mistaken for source-body reading. The next problem is context growth. A
clean-start proposal run can dispatch scouts, write many JSON files, then have
the Main Agent read those files again. That makes child isolation expensive.

The updated design keeps only two required source-reading child roles:
`metadata_scout` and `content_scout`. It removes any third source-review child
from the normal `[A]` flow. The Main Agent receives a compact source findings
report, then performs the final parent self-check in `review_a.json` and
`recon_summary.md`.

## Goals

1. Use scouts to lock precise source ranges instead of handing the Main Agent
   every intermediate artifact.
2. Define which source bodies the Main Agent must fully read.
3. Move full scout outputs into an audit appendix that is not normal Main Agent
   context.
4. Add `source_findings.compact.md` as the parent-readable source findings
   interface.
5. Make `review_a.json` the parent self-check report before `[B]`.

## Non-Goals

- Do not add a third source-review child role.
- Do not let subagents decide user alignment, final assignment interpretation,
  or pipeline approval.
- Do not weaken evidence requirements for proposal, research, or open-ended
  assignments.
- Do not redesign `task-orchestrator.md` execution stages in this change.

## Main Agent Read Boundary

During `do-homework [A]`, the Main Agent reads full source bodies only for:

1. `canvas/syllabus.json` or the equivalent fetched syllabus body.
2. Direct-spec strong matches.

A direct-spec strong match is a source that satisfies at least two of these
conditions:

- its file name, Canvas title, page title, or module item title contains current
  task terms such as `proposal`, `project proposal`, `writing research
  proposal`, or the exact assignment name;
- it appears in assignment-linked files, the current assignment module, or a
  `required` source selected by `metadata_scout`;
- its opening pages or visible body describe the current deliverable, format,
  deadline, sections, submission requirement, grading requirement, or task
  prompt.

For all other sources, including methods guidance, topic readings, theme
readings, policy support, examples, and low-signal course materials, content
scouts read the body and provide compact findings with exact pointers. The Main
Agent reads those source bodies only when `source_findings.compact.md` asks for
a specific parent source window, the pointer is ambiguous, or the user asks for
deeper inspection.

## Artifact Layers

Main Agent interface artifacts:

```text
investigation/reading_plan.compact.json
investigation/source_findings.compact.md
investigation/recon_summary.md
spec.md
investigation/rubric.md
investigation/review_a.json
```

Audit appendix artifacts:

```text
investigation/_appendix/source_index.json
investigation/_appendix/body_evidence_fragments/
investigation/_appendix/scout_receipts/
```

The appendix is durable evidence. The Main Agent does not normally read it in
full. Recovery runs, audits, or test debugging may read it.

Existing names such as `source_candidates.json`, `reading_plan.json`, and
`source_body_audit.json` may remain as compatibility aliases during migration,
but only under `investigation/_appendix/compatibility_aliases/`. Scout receipts
belong under `investigation/_appendix/scout_receipts/`. The runtime contract
must treat compact files as the normal parent interface and full JSON files as
appendix evidence.

## Scout Data Flow

The source flow is ordered:

```text
metadata_scout
  -> _appendix/source_index.json
  -> reading_plan.compact.json

content_scout(s)
  -> _appendix/body_evidence_fragments/*.json
  -> source_findings.compact.md

Main Agent
  -> review_a.json
  -> recon_summary.md
```

`metadata_scout` owns broad source discovery. It writes the full source index
for audit and a compact reading plan for Main Agent approval. The compact plan
must contain counts, selected source ids, source titles, assigned scopes,
forbidden/blocked ids, and a short reason for each selected read.

`content_scout` children own non-parent source body reading. They write full
body evidence fragments to the appendix and parent-readable findings shaped as:

```md
## <source title>

- Relevance: required | high_signal | supporting | excluded | blocked.
- What it says: concise task-relevant finding.
- Planning impact: how this changes spec, rubric, methods, timeline, policy, or gaps.
- Pointer: path plus page/section/line/window.
- Parent source read: required | not_required, with reason.
```

The Main Agent reads `source_findings.compact.md` to learn what the scouts found
inside PDFs, Canvas pages, or external sources. It does not read appendix body
fragments unless the compact findings request a specific source window or
recovery requires it.

## Parent Self-Check

Before `[B]`, the Main Agent writes `investigation/review_a.json`. It must check:

- syllabus was fully read or a blocked reason is recorded;
- every direct-spec strong match was fully read;
- `reading_plan.compact.json` was approved;
- `source_findings.compact.md` covers required and high-signal sources;
- forbidden/prior/stale sources were excluded from task context;
- source gaps, blocked sources, date conflicts, rubric gaps, or policy gaps are
  recorded;
- `parent_source_read_requests` were handled or explicitly deferred;
- terminal artifacts exist: `spec.md`, `investigation/rubric.md`,
  `investigation/review_a.json`, and `investigation/recon_summary.md`.

`source_findings.compact.md` alone is insufficient. The parent self-check is the
terminal machine-readable verdict. `recon_summary.md` is the user-readable
status report and next `[B]` question.

## Completion Rules Before `[B]`

The Main Agent may proceed to `[B]` when:

1. syllabus was fetched and fully read by the Main Agent, or a blocked reason is
   recorded;
2. every direct-spec strong match was fully read by the Main Agent;
3. `reading_plan.compact.json` was approved;
4. `source_findings.compact.md` exists and names task-relevant findings with
   exact pointers;
5. any requested parent source windows were read or explicitly deferred as
   non-blocking;
6. `review_a.json` records a non-recover verdict;
7. `recon_summary.md` gives the user-readable status and next question;
8. full appendix artifacts exist for audit but are not required Main Agent
   reads.

## Testing Strategy

Policy tests should assert that the docs now contain:

- parent full-read allowlist for syllabus and direct-spec strong matches;
- `reading_plan.compact.json` and `source_findings.compact.md`;
- appendix placement for full source index, body fragments, and scout receipts;
- language saying the Main Agent must not normally read full appendix artifacts;
- no third source-review child role and no separate gate file in the normal
  `[A]` contract;
- compatibility language for old artifact names during migration.
