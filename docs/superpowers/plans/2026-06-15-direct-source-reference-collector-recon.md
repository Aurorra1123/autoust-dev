# Direct-Source Reference Collector Recon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the normal homework reconnaissance source-scout pipeline with an always-on `reference_collector` that preserves complete original task sources under `references/`, then validate the flow with a fresh UCUG1808 proposal reconnaissance run through `[A]`.

**Architecture:** Keep `assignment-recon.md` as the broad Canvas raw snapshot workflow, add announcements to Stage 1, and make `reference_collector` the only child role for narrowing and preserving source evidence. The collector writes full original files or verbatim Canvas-native source copies plus `references/REFERENCE_INDEX.md`; the Main Agent reads references and writes terminal reconnaissance artifacts. Normal runs no longer create `reading_plan.compact.json`, `source_findings.compact.md`, or source-scout appendix files.

**Tech Stack:** Markdown runtime policy docs, Python `pytest` policy tests, local Canvas CLI commands documented in `canvascli-api.md`, git for checkpoint commits.

---

## File Structure

Modify these files:

- `tests/test_source_body_audit_policy.py`  
  Rewrite source reconnaissance policy tests from scout-chain assertions to direct-source reference collector assertions.

- `sub-skills/tasks/do-homework.md`  
  Update the `[A]` coordinator contract, workbench shape, `[A3]` rules, `[B]` summary rules, and pre-`[B]` completion checklist.

- `sub-skills/tools/assignment-recon.md`  
  Update Stage 1-5 to include announcements, always dispatch `reference_collector`, preserve references, copy Canvas-native source blocks verbatim, and remove source-scout artifacts as normal outputs.

- `skill.md`  
  Update the top-level Homework/Drafting source-of-truth chain and Main Agent read boundary.

- `docs/runtime-agent-protocol.md`  
  Replace `metadata_scout`/`content_scout` source taxonomy with `reference_collector` and update artifact/read boundaries.

- `sub-skills/tools/canvascli-api.md`  
  Update the Canvas Generic recipe to include announcements and the reference collector flow.

- `docs/development-validation-standard.md`  
  Update validation criteria from source-scout evidence to reference collector evidence.

- `sub-skills/tasks/task-orchestrator.md`  
  Update downstream source-read guidance to use `references/` and `references/canvas_native/` instead of `source_findings.compact.md`.

- `docs/PITFALLS.md`  
  Replace the old scout-chain warning with the direct-source reference collector failure mode and correct practice.

Create or update no production Python modules in this plan. This is a runtime-contract documentation and validation change.

---

### Task 0: Clean Interrupted WIP Before Implementation

**Files:**
- Restore: `docs/development-validation-standard.md`
- Restore: `docs/runtime-agent-protocol.md`
- Restore: `skill.md`
- Restore: `sub-skills/tasks/do-homework.md`
- Restore: `sub-skills/tools/assignment-recon.md`
- Restore: `sub-skills/tools/canvascli-api.md`
- Restore: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Confirm current dirty files are only the interrupted pre-plan WIP**

Run:

```bash
git status --short --untracked-files=all
```

Expected: the dirty files are exactly the seven files listed above. The committed design spec and this implementation plan should not be dirty.

- [ ] **Step 2: Restore the interrupted WIP**

Run:

```bash
git restore \
  docs/development-validation-standard.md \
  docs/runtime-agent-protocol.md \
  skill.md \
  sub-skills/tasks/do-homework.md \
  sub-skills/tools/assignment-recon.md \
  sub-skills/tools/canvascli-api.md \
  tests/test_source_body_audit_policy.py
```

Expected: these files return to the committed baseline before the direct-source implementation begins.

- [ ] **Step 3: Verify a clean implementation starting point**

Run:

```bash
git status --short --untracked-files=all
```

Expected: no dirty runtime/test files remain, except this plan file if it has not already been committed.

- [ ] **Step 4: Commit only the plan if it is not already committed**

Run:

```bash
git add docs/superpowers/plans/2026-06-15-direct-source-reference-collector-recon.md
git commit -m "Plan direct-source reference collector recon"
```

Expected: a commit containing only this plan file. If the plan has already been committed, skip this step.

---

### Task 1: Rewrite Policy Tests For Direct-Source Reference Collector

**Files:**
- Modify: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Replace scout-chain tests with collector tests**

Edit `tests/test_source_body_audit_policy.py` so the source reconnaissance tests assert the new contract. Replace the current tests that require `metadata_scout`, `content_scout`, `reading_plan.compact.json`, `source_findings.compact.md`, source index appendix, or body evidence fragments with these tests:

```python
def test_assignment_recon_uses_reference_collector_and_announcements():
    text = read("sub-skills/tools/assignment-recon.md")

    assert "reference_collector" in text
    assert "canvas/announcements.json" in text
    assert "references/REFERENCE_INDEX.md" in text
    assert "references/canvas_native/" in text
    assert "copy" in text
    assert "verbatim" in text
    assert "references/**/*.pdf.links.json" in text
    assert "references/syllabus/" not in text


def test_do_homework_defines_direct_source_reference_boundary():
    text = read("sub-skills/tasks/do-homework.md")

    assert "reference_collector" in text
    assert "references/REFERENCE_INDEX.md" in text
    assert "references/canvas_native/" in text
    assert "Main Agent" in text
    assert "complete original" in text
    assert "Do not create `reading_plan.compact.json`" in text
    assert "Do not create `source_findings.compact.md`" in text
    assert "Subagents must not write final `spec.md`" in text
    assert "proposal/research/open-ended" in text


def test_standard_homework_recon_removes_source_scout_pipeline():
    policy_text = "\n".join(
        [
            read("skill.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tools/assignment-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "source_scout_pipeline_used" in policy_text
    assert "source_scout_pipeline_used\": false" in policy_text or '"source_scout_pipeline_used": false' in policy_text
    assert "metadata_scout -> reading_plan.compact.json -> content_scout -> source_findings.compact.md" not in policy_text
    assert "must dispatch real child subagents with" not in policy_text
    assert "Do not dispatch `content_scout` until `metadata_scout` has produced" not in policy_text


def test_reference_collector_preserves_canvas_native_sources_verbatim():
    policy_text = "\n".join(
        [
            read("sub-skills/tools/assignment-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "references/canvas_native/" in policy_text
    assert "source.json" in policy_text
    assert "source.txt" in policy_text
    assert "ORIGIN.md" in policy_text
    assert "verbatim" in policy_text
    assert "must not summarize" in policy_text or "must not paraphrase" in policy_text


def test_main_agent_reads_references_not_old_source_findings():
    policy_text = "\n".join(
        [
            read("skill.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/task-orchestrator.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "references/REFERENCE_INDEX.md" in policy_text
    assert "references/source_docs/" in policy_text
    assert "references/canvas_native/" in policy_text
    assert "source_findings.compact.md" not in policy_text
    assert "parent_source_read_requests" not in policy_text


def test_reference_collector_review_fields_are_documented():
    policy_text = "\n".join(
        [
            read("sub-skills/tools/assignment-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert '"announcements_checked": true' in policy_text
    assert '"reference_collector_used": true' in policy_text
    assert '"source_scout_pipeline_used": false' in policy_text
    assert '"reference_index_checked": true' in policy_text
    assert '"canvas_native_sources": []' in policy_text
    assert '"downloaded_references": []' in policy_text
    assert '"pdf_link_manifests_checked": true' in policy_text
```

Keep unrelated tests that still apply, such as UCUG1808 appearing only in historical acceptance design docs and recon summary depth behavior. Remove or rewrite assertions that require old scout artifacts.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py -q
```

Expected: FAIL. Failures should point to missing `reference_collector`, `canvas/announcements.json`, `references/REFERENCE_INDEX.md`, `references/canvas_native/`, or old source-scout text still present.

- [ ] **Step 3: Commit the failing tests**

Run:

```bash
git add tests/test_source_body_audit_policy.py
git commit -m "test: define reference collector recon policy"
```

Expected: commit contains only `tests/test_source_body_audit_policy.py`.

---

### Task 2: Update Top-Level Skill And Do-Homework Coordinator Contract

**Files:**
- Modify: `skill.md`
- Modify: `sub-skills/tasks/do-homework.md`

- [ ] **Step 1: Update `skill.md` Homework/Drafting section**

In `skill.md`, update the source-of-truth chain to remove `reading_plan.compact.json` and `source_findings.compact.md`, and add:

```text
-> references/REFERENCE_INDEX.md
-> references/source_docs/ and references/canvas_native/
```

Add this contract:

```md
Standard homework reconnaissance always uses `reference_collector` after the
Canvas raw snapshot. The collector narrows task-relevant sources and preserves
complete original evidence under `references/`. It may download files, extract
PDF text, preserve PDF link annotations, and copy Canvas-native source JSON
blocks verbatim into `references/canvas_native/`.

The collector must not interpret the assignment, summarize requirements as the
only evidence path, or write final reconnaissance artifacts. The Main Agent
reads `references/REFERENCE_INDEX.md`, preserved reference files, and
Canvas-native `source.json` / `source.txt` copies before writing `spec.md`,
`rubric.md`, `review_a.json`, `recon_summary.md`, and `explore_context.md`.

Do not create `reading_plan.compact.json`, `reading_plan.compact.approved.json`,
`source_findings.compact.md`, source index appendix files, source body fragments,
or source scout receipts in standard runs.
```

- [ ] **Step 2: Update `do-homework.md` required artifact chain**

In `sub-skills/tasks/do-homework.md`, set the `[A]` required chain to:

```text
prelaunch_startup_inventory.json
-> investigation/explore_manifest.json
-> investigation/explore_context.md
-> references/REFERENCE_INDEX.md
-> references/
   -> source_docs/<slug>/<slug>.pdf + .pdf.txt + .pdf.links.json
   -> slides/<slug>/<slug>.pptx + .pptx.txt
   -> external/<slug>.txt
   -> canvas_native/<slug>/source.json + source.txt + ORIGIN.md
-> investigation/recon_summary.md
-> spec.md
-> investigation/rubric.md
-> investigation/review_a.json
-> investigation/alignment_brief.md
-> pipeline_design.md
   -> Pipeline Review Status: awaiting_user_review
-> result.json
```

- [ ] **Step 3: Update `do-homework.md` actor rules**

Replace old source-scout actor rules with:

```md
- `reference_collector` is the only standard homework reconnaissance child role.
  It is a preservation worker, not a source judge.
- The Main Agent owns final source interpretation, `spec.md`, `rubric.md`,
  `review_a.json`, `recon_summary.md`, `explore_context.md`, user alignment,
  pipeline approval, and Canvas submission decisions.
- Subagents must not write final `spec.md`, final `review_a.json`,
  `pipeline_design.md`, or user alignment decisions.
- Normal runs must not create `reading_plan.compact.json`,
  `source_findings.compact.md`, or source-scout appendix files.
```

- [ ] **Step 4: Update `[A3]` and pre-`[B]` completion rules**

In `do-homework.md [A3]`, require:

```md
1. Fetch raw Canvas snapshots through `assignment-recon.md`.
2. Dispatch `reference_collector` for every homework run.
3. Wait for `references/REFERENCE_INDEX.md`.
4. Read preserved references, not broad raw Canvas snapshots.
5. Write terminal artifacts.
```

Before `[B]`, require:

```md
- `references/REFERENCE_INDEX.md` exists.
- `references/canvas_native/` contains verbatim source copies for relevant
  Canvas-native syllabus, announcement, assignment page, or Canvas page content.
- PDFs that affect the assignment have original PDF, `.pdf.txt`, and
  `.pdf.links.json` companions.
- `review_a.json` records `reference_collector_used: true`,
  `source_scout_pipeline_used: false`, `announcements_checked`,
  `reference_index_checked`, `downloaded_references`, `canvas_native_sources`,
  and `pdf_link_manifests_checked`.
```

- [ ] **Step 5: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_do_homework_defines_direct_source_reference_boundary tests/test_source_body_audit_policy.py::test_main_agent_reads_references_not_old_source_findings -q
```

Expected: these tests still FAIL until `assignment-recon.md`, runtime protocol, and downstream docs are updated; failures should no longer be due to `skill.md` or `do-homework.md`.

- [ ] **Step 6: Commit coordinator docs**

Run:

```bash
git add skill.md sub-skills/tasks/do-homework.md
git commit -m "docs: route homework recon through reference collector"
```

Expected: commit includes only `skill.md` and `sub-skills/tasks/do-homework.md`.

---

### Task 3: Update Assignment-Recon Reference Collector Workflow

**Files:**
- Modify: `sub-skills/tools/assignment-recon.md`

- [ ] **Step 1: Update workbench contract**

In `sub-skills/tools/assignment-recon.md`, change the workbench tree so `canvas/` includes:

```text
announcements.json
```

Change `references/` to include:

```text
references/
├── REFERENCE_INDEX.md
├── source_docs/
├── slides/
├── external/
├── canvas_native/
│   └── <slug>/
│       ├── source.json
│       ├── source.txt
│       └── ORIGIN.md
└── pdf_links.json
```

Remove `reading_plan.compact.json`, `source_findings.compact.md`, `source_index.json`, `body_evidence_fragments/`, and `scout_receipts/` from the normal workbench tree.

- [ ] **Step 2: Add announcements to Stage 1 commands**

Add this command to Stage 1:

```bash
.venv/bin/canvascli announcements > "<work_dir>/canvas/announcements.json"
```

Document that 0 announcements is a valid checked state and that command failure is recorded in `investigation/unreachable.txt` plus `review_a.json`.

- [ ] **Step 3: Replace Source Candidate And Body Audit section**

Replace the old section beginning `### Source Candidate And Body Audit` with:

```md
### Reference Collector

Always dispatch `reference_collector` after Stage 1 raw Canvas snapshots.

The collector reads raw Canvas snapshots and preserves task-relevant source
evidence under `references/`. It does not write `spec.md`, `rubric.md`,
`review_a.json`, `source_findings.compact.md`, or `reading_plan.compact.json`.

Classifications for `references/REFERENCE_INDEX.md`:

```text
direct_spec | rubric_source | syllabus_constraint | required_input |
announcement_update | supporting_only | irrelevant | forbidden_or_stale | blocked
```

The collector downloads file references only when they are direct specs, rubric
sources, required inputs, announcement updates, or directly required supporting
sources. It must not download every course file.
```

- [ ] **Step 4: Add Canvas-native preservation contract**

Add:

```md
When task-relevant information lives in Canvas-native JSON, copy the relevant
object verbatim to:

```text
references/canvas_native/<slug>/source.json
references/canvas_native/<slug>/source.txt
references/canvas_native/<slug>/ORIGIN.md
```

`source.json` must be copied from the raw Canvas snapshot without paraphrase. If
the raw JSON has no safe section boundary, copy the complete source object.
`source.txt` is an exact body-text export when available. `ORIGIN.md` may record
origin, copied object id, classification, and selection reason, but must not
summarize requirements.
```

- [ ] **Step 5: Preserve PDF companion rule**

Keep the existing PDF link annotation extraction section, but make it part of the collector contract. Ensure it still names both:

```text
references/<name>.pdf.links.json
references/**/*.pdf.links.json
```

and the three-layer source-adjacent pattern:

```text
<slug>.pdf
<slug>.pdf.txt
<slug>.pdf.links.json
```

- [ ] **Step 6: Update Stage 4 review JSON**

Replace old fields such as `compact_reading_plan_approved`, `source_findings_checked`, `required_high_signal_body_evidence_checked`, `appendix_paths`, and `parent_source_read_requests` with:

```json
{
  "assignment_shell_checked": true,
  "rubric_checked": true,
  "syllabus_checked": true,
  "announcements_checked": true,
  "reference_collector_used": true,
  "source_scout_pipeline_used": false,
  "reference_index_checked": true,
  "direct_spec_sources": [],
  "rubric_sources": [],
  "required_inputs": [],
  "canvas_native_sources": [],
  "relevant_announcements": [],
  "downloaded_references": [],
  "pdf_link_manifests_checked": true,
  "blocked_sources": [],
  "forbidden_or_stale_sources": [],
  "supporting_sources_skipped": [],
  "inputs_complete": true,
  "parent_self_check_complete": true,
  "verdict": "proceed"
}
```

- [ ] **Step 7: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_assignment_recon_uses_reference_collector_and_announcements tests/test_source_body_audit_policy.py::test_reference_collector_preserves_canvas_native_sources_verbatim tests/test_source_body_audit_policy.py::test_reference_collector_review_fields_are_documented -q
```

Expected: PASS for these tests after this task.

- [ ] **Step 8: Commit assignment recon docs**

Run:

```bash
git add sub-skills/tools/assignment-recon.md
git commit -m "docs: define assignment reference collector"
```

Expected: commit includes only `sub-skills/tools/assignment-recon.md`.

---

### Task 4: Update Runtime, Tool, Validation, Pitfall, And Orchestrator Docs

**Files:**
- Modify: `docs/runtime-agent-protocol.md`
- Modify: `sub-skills/tools/canvascli-api.md`
- Modify: `docs/development-validation-standard.md`
- Modify: `sub-skills/tasks/task-orchestrator.md`
- Modify: `docs/PITFALLS.md`

- [ ] **Step 1: Update runtime protocol source taxonomy**

In `docs/runtime-agent-protocol.md`, replace the source/spec child role model with:

```md
- source/spec exploration domain: the Main Agent owns source/spec judgment.
- reference_collector: always-on preservation child for homework reconnaissance.
  It reads raw Canvas snapshots, narrows task-relevant source evidence, downloads
  files, copies Canvas-native JSON verbatim, and writes
  `references/REFERENCE_INDEX.md`.
- `reference_collector` must not write terminal reconnaissance artifacts or
  summarize source requirements as the evidence path.
```

Remove current-runtime requirements for `metadata_scout`, `content_scout`,
`reading_plan.compact.json`, `source_findings.compact.md`, source index appendix,
body evidence fragments, and source scout receipts.

- [ ] **Step 2: Update runtime workbench tree and read boundary**

In `docs/runtime-agent-protocol.md`, update the workbench tree to include `references/REFERENCE_INDEX.md`, `references/canvas_native/`, and `canvas/announcements.json`. Add:

```md
The Main Agent reads preserved references and terminal Canvas shells, not old
source-scout compact findings. `references/` is the source evidence interface.
`canvas/` remains durable raw evidence.
```

- [ ] **Step 3: Update canvascli recipe**

In `sub-skills/tools/canvascli-api.md`, update the Canvas Generic recipe so it says:

```md
1. Calls atomic context commands: `assignment`, `rubric`, `front-page`,
   `syllabus`, `modules`, `module-items`, `page`, `file`,
   `assignment-files`, and `announcements`.
2. Stores raw CLI JSON under `<work_dir>/canvas/`.
3. Runs `reference_collector` to preserve task-relevant source evidence under
   `<work_dir>/references/`.
4. Writes `<work_dir>/spec.md` as the Main Agent reconnaissance report.
```

Remove the mature-pattern sentence that names `metadata_scout`, compact reading plans, `content_scout`, and compact source findings.

- [ ] **Step 4: Update development validation standard**

In `docs/development-validation-standard.md`, replace source-scout evidence requirements with:

```md
For clean-start proposal/research/open-ended homework, source/spec evidence is
complete only when:

- raw Canvas snapshots include assignment, rubric, syllabus, modules,
  module-items, assignment files, pages when relevant, file metadata, and
  announcements;
- `reference_collector` has produced `references/REFERENCE_INDEX.md`;
- task-relevant Canvas-native evidence is copied verbatim under
  `references/canvas_native/`;
- fetched PDFs include original file, extracted text, and link annotation
  manifest;
- Main Agent `review_a.json` records `reference_collector_used: true` and
  `source_scout_pipeline_used: false`.
```

- [ ] **Step 5: Update task orchestrator downstream reads**

In `sub-skills/tasks/task-orchestrator.md`, replace guidance that depends on `source_findings.compact.md` with:

```md
If a stage depends on assignment source details, include the relevant preserved
reference paths from `references/REFERENCE_INDEX.md` in the stage brief:
`references/source_docs/**`, `references/slides/**`, `references/external/**`,
or `references/canvas_native/**/source.json`. Do not rely on
`source_findings.compact.md` or old source-scout appendix files.
```

- [ ] **Step 6: Update pitfalls**

In `docs/PITFALLS.md`, replace the old UCUG1808 correct-practice paragraph with:

```md
Correct practice: `do-homework.md [A3]` must call agent-led
`tools/assignment-recon.md`. The flow fetches broad Canvas raw snapshots,
including announcements, then always runs `reference_collector` to preserve
task-relevant original source evidence under `references/`. The Main Agent
reads complete preserved references and writes terminal reconnaissance artifacts.
Do not revive `metadata_scout -> reading_plan.compact.json -> content_scout ->
source_findings.compact.md`.
```

- [ ] **Step 7: Run policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py -q
```

Expected: PASS for the rewritten source body audit policy tests.

- [ ] **Step 8: Commit runtime and downstream docs**

Run:

```bash
git add docs/runtime-agent-protocol.md sub-skills/tools/canvascli-api.md docs/development-validation-standard.md sub-skills/tasks/task-orchestrator.md docs/PITFALLS.md
git commit -m "docs: update runtime for reference collector recon"
```

Expected: commit contains only these five docs.

---

### Task 5: Run Full Policy Test Suite

**Files:**
- No edits expected.

- [ ] **Step 1: Run source recon policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py -q
```

Expected: PASS.

- [ ] **Step 2: Run PDF link policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_pdf_link_annotation_policy.py -q
```

Expected: PASS. If this fails because old doc wording changed, update only policy text or tests needed to preserve the existing PDF three-layer companion requirement.

- [ ] **Step 3: Run hard requirement policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_spec_hard_requirement_policy.py -q
```

Expected: PASS.

- [ ] **Step 4: Run all tests if the targeted suites pass**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: PASS, or only unrelated failures with clear explanation. Do not proceed to UCUG1808 runtime validation if source recon policy tests fail.

- [ ] **Step 5: Commit any test/doc fixups**

If Task 5 required fixups, run:

```bash
git add tests docs sub-skills skill.md
git commit -m "test: align policy suites with reference collector recon"
```

Expected: commit contains only fixups needed for tests.

---

### Task 6: Fresh UCUG1808 Reconnaissance Validation Through `[A]`

**Files:**
- Runtime output under: `data/homework/UCUG1808-L01/`
- No source-code commit expected for generated homework data unless explicitly requested.

- [ ] **Step 1: Remove stale UCUG1808 workbench**

Run:

```bash
rm -rf data/homework/UCUG1808-L01
```

Expected: no `data/homework/UCUG1808-L01` directory remains.

- [ ] **Step 2: Run `do-homework` for UCUG1808 Project Proposal Files through `[A]` only**

Use the `do-homework` skill in this repository for:

```text
Course: UCUG1808-L01
Assignment: Project Proposal Files
Stop point: after `[A]` reconnaissance, before `[B]` user alignment
```

Expected behavior:

- `assignment-recon.md` runs Stage 1 raw Canvas snapshot collection.
- `canvas/announcements.json` is fetched or a failure is recorded.
- `reference_collector` runs for the assignment.
- The run stops after `[A]` and does not draft or submit.

- [ ] **Step 3: Inspect forbidden old artifacts**

Run:

```bash
find data/homework/UCUG1808-L01 -path '*reading_plan.compact*' -o -path '*source_findings.compact.md' -o -path '*_appendix/source_index.json' -o -path '*_appendix/body_evidence_fragments*' -o -path '*_appendix/scout_receipts*'
```

Expected: no output. If output appears, the implementation is not complete.

- [ ] **Step 4: Inspect required reference collector artifacts**

Run:

```bash
find data/homework/UCUG1808-L01 -maxdepth 5 \( -path '*references/REFERENCE_INDEX.md' -o -path '*references/canvas_native/*/source.json' -o -path '*references/source_docs/*/*.pdf' -o -path '*references/source_docs/*/*.pdf.txt' -o -path '*references/source_docs/*/*.pdf.links.json' \) | sort
```

Expected:

- one `references/REFERENCE_INDEX.md`;
- at least one `references/canvas_native/**/source.json` for syllabus, announcement if relevant, assignment/page if relevant, or other Canvas-native task evidence;
- proposal direct-spec PDF or equivalent source file under `references/source_docs/`;
- matching `.pdf.txt` and `.pdf.links.json` for every fetched spec-impacting PDF.

- [ ] **Step 5: Inspect terminal reconnaissance artifacts**

Run:

```bash
find data/homework/UCUG1808-L01 -maxdepth 4 \( -name spec.md -o -name rubric.md -o -name review_a.json -o -name recon_summary.md -o -name explore_context.md -o -name explore_manifest.json -o -name unreachable.txt \) | sort
```

Expected: `spec.md`, `investigation/rubric.md`, `investigation/review_a.json`, `investigation/recon_summary.md`, `investigation/explore_context.md`, and `investigation/explore_manifest.json` exist.

- [ ] **Step 6: Validate `review_a.json` fields**

Run:

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

Expected: command prints the `review_a.json` path and exits 0.

- [ ] **Step 7: Validate reference index does not summarize source requirements**

Run:

```bash
sed -n '1,220p' "$(find data/homework/UCUG1808-L01 -path '*references/REFERENCE_INDEX.md' | head -1)"
```

Expected: index lists classification, reference path, raw origin, reason selected, and companions. It should not contain paragraph summaries of assignment requirements that replace reading the source.

- [ ] **Step 8: Record validation result**

Create a short validation note under:

```text
docs/verification/2026-06-15/ucug1808-reference-collector-recon.md
```

Include:

- command or exact prompt used to run `do-homework` to `[A]`;
- whether old source-scout artifacts were absent;
- required reference collector artifacts found;
- `review_a.json` field check result;
- any shortcomings observed in the generated workbench;
- whether the implementation is accepted or needs a follow-up patch.

- [ ] **Step 9: Commit validation note and any required flow fixes**

If the UCUG1808 run passes without source doc changes:

```bash
git add docs/verification/2026-06-15/ucug1808-reference-collector-recon.md
git commit -m "test: validate UCUG1808 reference collector recon"
```

If validation exposes runtime doc/test problems, fix those problems first, rerun Task 6 checks, then commit the fixes and validation note together:

```bash
git add docs/verification/2026-06-15/ucug1808-reference-collector-recon.md skill.md sub-skills docs tests
git commit -m "fix: harden reference collector recon validation"
```

---

## Final Verification Checklist

- [ ] `git status --short` shows no unintended source-doc changes.
- [ ] `tests/test_source_body_audit_policy.py` passes.
- [ ] `tests/test_pdf_link_annotation_policy.py` passes.
- [ ] `tests/test_spec_hard_requirement_policy.py` passes.
- [ ] Full `pytest -q` passes or any unrelated failure is documented.
- [ ] Fresh `data/homework/UCUG1808-L01` run through `[A]` exists and has no old source-scout artifacts.
- [ ] UCUG1808 references include complete original source files or verbatim Canvas-native source copies.
- [ ] UCUG1808 `review_a.json` records `reference_collector_used: true` and `source_scout_pipeline_used: false`.
- [ ] Validation note exists under `docs/verification/2026-06-15/`.
