# UCUG1808 Reference Collector Recon Validation

Date: 2026-06-15

## Superseding Contract Note

This report records the validation contract used at the time it was written. It
is now a historical note, not the current complete acceptance checklist.

Current clean `reference_collector` acceptance also requires:

- a real `reference_collector` row in `stage_reviews/child_dispatch_ledger.json`
  with child identity or transcript handle; `explore_manifest.json` and
  `review_a.json` are summaries, not identity authority;
- relevant announcements preserved one object per
  `references/canvas_native/announcement-<id-or-slug>/source.json`, with
  `REFERENCE_INDEX.md` raw origins such as `canvas/announcements.json#id=...`;
- no `references/canvas_native/announcements/source.json` mirror of the full
  `canvas/announcements.json` collection;
- `review_a.json.relevant_announcements` entries that name preserved
  announcement paths or an empty list when no announcement is relevant.

## Scope

This was an independent `do-homework` coordinator execution for UCUG1808-L01 / Project Proposal Files through `[A]` only.

- Repository: `/Users/deepwisdom/Desktop/project/autoust-test`
- Workbench: `data/homework/UCUG1808-L01`
- Course ID: `2963`
- Assignment ID: `23014`
- Stop point: after `[A]` reconnaissance, before `[B]`
- Draft generated: no
- Canvas submission attempted: no
- Commit created: no

The coordinator deleted and rebuilt `data/homework/UCUG1808-L01`, fetched Stage 1 raw Canvas snapshots, then dispatched a real child subagent for the `reference_collector` role.

## Child Dispatch

`reference_collector` was a real child dispatch, not main-agent mechanical preservation logic.

- Transport: `multi_agent_v1.spawn_agent`
- Child id: `019eca22-91a3-7162-addf-3fac320838e6`
- Child nickname: `Arendt`
- Child status: completed
- Recorded in: `data/homework/UCUG1808-L01/investigation/explore_manifest.json`
- Recorded executed_by: `child-subagent`
- Recorded child reads: 43
- Recorded child writes: 44

The child wrote `references/REFERENCE_INDEX.md`, Canvas-native source copies, original PDFs, `.pdf.txt` text extracts, `.pdf.links.json` manifests, and `references/pdf_links.json`. The child did not write terminal reconnaissance artifacts.

## Commands And Results

Removed stale workbench:

```bash
rm -rf data/homework/UCUG1808-L01
```

Result: workbench was rebuilt from scratch.

Canvas CLI setup check:

```bash
test -d .venv && .venv/bin/canvascli version > /dev/null 2>&1 && .venv/bin/canvascli whoami > /dev/null 2>&1 && echo OK || echo NEEDS_SETUP
```

Result: `OK`.

Stage 1 raw snapshots:

```bash
.venv/bin/canvascli assignment 23014 -c 2963 > data/homework/UCUG1808-L01/canvas/assignment.json
.venv/bin/canvascli rubric 23014 -c 2963 > data/homework/UCUG1808-L01/canvas/rubric.json
.venv/bin/canvascli front-page -c 2963 > data/homework/UCUG1808-L01/canvas/front-page.json
.venv/bin/canvascli syllabus -c 2963 > data/homework/UCUG1808-L01/canvas/syllabus.json
.venv/bin/canvascli modules -c 2963 > data/homework/UCUG1808-L01/canvas/modules.json
.venv/bin/canvascli assignment-files 23014 -c 2963 > data/homework/UCUG1808-L01/canvas/assignment-files.json
.venv/bin/canvascli announcements > data/homework/UCUG1808-L01/canvas/announcements.json
```

Result: all commands exited 0. Follow-up module/file fetches produced 12 `module-items-*.json` files and 24 `file-*.json` files. `canvas/announcements.json` exists.

Forbidden old artifacts:

```bash
find data/homework/UCUG1808-L01 -path '*reading_plan.compact*' -o -path '*source_findings.compact.md' -o -path '*_appendix/source_index.json' -o -path '*_appendix/body_evidence_fragments*' -o -path '*_appendix/scout_receipts*'
```

Result: no output.

Required reference collector artifacts:

```bash
find data/homework/UCUG1808-L01 -maxdepth 5 \( -path '*references/REFERENCE_INDEX.md' -o -path '*references/canvas_native/*/source.json' -o -path '*references/source_docs/*/*.pdf' -o -path '*references/source_docs/*/*.pdf.txt' -o -path '*references/source_docs/*/*.pdf.links.json' \) | sort
```

Result: found `references/REFERENCE_INDEX.md`, 10 Canvas-native `source.json` files, and three PDFs with matching `.pdf.txt` and `.pdf.links.json` companions.

Terminal reconnaissance artifacts:

```bash
find data/homework/UCUG1808-L01 -maxdepth 4 \( -name spec.md -o -name rubric.md -o -name review_a.json -o -name recon_summary.md -o -name explore_context.md -o -name explore_manifest.json -o -name unreachable.txt \) | sort
```

Result: found `spec.md`, `investigation/rubric.md`, `investigation/review_a.json`, `investigation/recon_summary.md`, `investigation/explore_context.md`, `investigation/explore_manifest.json`, and `investigation/unreachable.txt`.

`review_a.json` field validation:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

root = Path("data/homework/UCUG1808-L01")
review_paths = list(root.glob("**/investigation/review_a.json"))
assert len(review_paths) == 1, review_paths
data = json.loads(review_paths[0].read_text())
required = {
    "assignment_shell_checked": True,
    "rubric_checked": True,
    "syllabus_checked": True,
    "announcements_checked": True,
    "reference_collector_used": True,
    "source_scout_pipeline_used": False,
    "reference_index_checked": True,
    "pdf_link_manifests_checked": True,
    "parent_self_check_complete": True,
}
missing = {k: (data.get(k), v) for k, v in required.items() if data.get(k) != v}
assert not missing, missing
assert data.get("direct_spec_sources"), "direct_spec_sources is empty"
assert data.get("downloaded_references"), "downloaded_references is empty"
assert "compact_reading_plan_approved" not in data
assert "source_findings_checked" not in data
print(review_paths[0])
PY
```

Result: command printed `data/homework/UCUG1808-L01/investigation/review_a.json` and exited 0.

Reference index inspection:

```bash
sed -n '1,220p' "$(find data/homework/UCUG1808-L01 -path '*references/REFERENCE_INDEX.md' | head -1)"
```

Result: index lists classification, reference path, raw origin, selection reason, and companion files. It does not replace source reading with a requirements summary.

Child identity check:

```bash
jq '{dispatch_id:.reference_collector.dispatch_id,status:.reference_collector.status,executed_by:.reference_collector.executed_by, read_count:(.reference_collector.reads|length), write_count:(.reference_collector.writes|length)}' data/homework/UCUG1808-L01/investigation/explore_manifest.json
```

Result:

```json
{
  "dispatch_id": "019eca22-91a3-7162-addf-3fac320838e6",
  "status": "completed",
  "executed_by": "child-subagent",
  "read_count": 43,
  "write_count": 44
}
```

No draft/pipeline/stage artifacts:

```bash
find data/homework/UCUG1808-L01 \( -path '*draft*' -o -path '*stage_results*' -o -path '*stage_reviews*' -o -path '*stage_briefs*' -o -name 'alignment_brief.md' -o -name 'pipeline_design.md' -o -name 'result.json' \) -print
```

Result: no output.

## Reference Artifacts

Preserved Canvas-native sources include:

- `references/canvas_native/assignment-shell/source.json`
- `references/canvas_native/course-syllabus/source.json`
- `references/canvas_native/rubric-status/source.json`
- `references/canvas_native/assignment-files-empty/source.json`
- `references/canvas_native/final-project-module-items/source.json`
- `references/canvas_native/week-8-module-items/source.json`
- `references/canvas_native/file-writing-research-proposal-group-work/source.json`
- `references/canvas_native/file-final-group-research-project/source.json`
- `references/canvas_native/file-timeline-research-in-sport-social-sciences-week-8/source.json`
- `references/canvas_native/front-page-status/source.json`

Downloaded references include:

- `references/source_docs/writing-research-proposal-group-work/writing-research-proposal-group-work.pdf`
- `references/source_docs/final-group-research-project/final-group-research-project.pdf`
- `references/source_docs/timeline-research-in-sport-social-sciences-week-8/timeline-research-in-sport-social-sciences-week-8.pdf`

Each downloaded PDF has `.pdf.txt` and `.pdf.links.json` companions. Link manifests were checked and contained empty arrays for all three PDFs.

## Review Fields

`review_a.json` correctly sets:

- `assignment_shell_checked: true`
- `rubric_checked: true`
- `syllabus_checked: true`
- `announcements_checked: true`
- `reference_collector_used: true`
- `source_scout_pipeline_used: false`
- `reference_index_checked: true`
- `direct_spec_sources`: non-empty
- `downloaded_references`: non-empty
- `pdf_link_manifests_checked: true`
- `parent_self_check_complete: true`

It does not contain `compact_reading_plan_approved` or `source_findings_checked`.

## Observed Shortcomings

- Canvas front page returned `not_enabled_or_not_found`; this was preserved as checked status and did not block because direct assignment, syllabus, modules, and PDFs were available.
- `canvas/announcements.json` contained an announcement for course_id `2799`, not course_id `2963`; it was recorded as checked but irrelevant.
- Canvas rubric endpoint reports no assignment-specific rubric.
- The assignment snapshot includes prior submission attachments, but this clean `[A]` validation did not inspect them as retained draft context.

## Verdict

DONE_WITH_CONCERNS.

The runtime Task 6 acceptance criteria were met, including real `reference_collector` child dispatch and absence of legacy source-scout artifacts. The concerns above are non-blocking source conditions, not workflow failures.
