# Homework Source Body Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen homework reconnaissance so candidate source discovery, body reading, subagent responsibilities, reference organization, and real UCUG1808 validation are explicit and test-protected.

**Architecture:** Add policy tests first, then update the runtime documents that drive `do-homework`: `assignment-recon.md`, `do-homework.md`, `runtime-agent-protocol.md`, and `PITFALLS.md`. The design keeps the Main Agent as coordinator/final judge, moves broad source body reading to content scouts, stores full source/body evidence in an appendix, and exposes only `reading_plan.compact.json` plus `source_findings.compact.md` as the normal parent interface before the Main Agent writes `review_a.json`.

**Tech Stack:** Markdown runtime docs, pytest policy tests, Canvas workbench files under `data/homework/...`.

---

## File Structure

- Create `tests/test_source_body_audit_policy.py`: policy assertions for source candidate ranking, source body audit, scout boundaries, long-document reading, reference organization, and UCUG1808 acceptance.
- Modify `sub-skills/tools/assignment-recon.md`: workbench contract, Stage 3 body audit, content scout templates, reference organization, Stage 4 review fields, quality bar.
- Modify `sub-skills/tasks/do-homework.md`: artifact chain, Main Agent/subagent boundary, scout dispatch rules, pre-alignment gates, UCUG1808 acceptance note.
- Modify `docs/runtime-agent-protocol.md`: source/spec scout split into metadata/content roles and reference layout.
- Modify `docs/PITFALLS.md`: generic UCUG1808-style pitfall for proposal/research assignments.
- Optionally modify `skill.md`: short source-of-truth chain update if needed after the detailed docs are stable.

## Task 1: Add Failing Policy Tests

**Files:**
- Create: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Write tests for the new reconnaissance contract**

Create `tests/test_source_body_audit_policy.py` with:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_assignment_recon_requires_source_body_audit_and_read_modes():
    text = read("sub-skills/tools/assignment-recon.md")

    assert "source_findings.compact.md" in text
    assert "body_evidence_fragments/" in text
    assert "source_findings.compact.md" in text
    assert "source_index.json" in text
    assert "reading_plan.compact.json" in text
    assert "source_findings.compact.md" in text
    assert "metadata_only" in text
    assert "pdf_text_plus_links" in text
    assert "keyword windows" in text
    assert "references/**/*.pdf.links.json" in text
    assert "references/syllabus/" not in text


def test_do_homework_defines_main_agent_and_scout_boundaries():
    text = read("sub-skills/tasks/do-homework.md")

    assert "metadata_scout" in text
    assert "content_scout" in text
    assert "parent self-check" in text
    assert "The Main Agent approves `reading_plan.compact.json`" in text
    assert "Subagents must not write final `spec.md`" in text
    assert "proposal/research/open-ended" in text
    assert "body_evidence_fragments/" in text
    assert "The Main Agent must not normally read full appendix artifacts" in text
    assert "source_findings.compact.md`, or a recorded inline" in text
    assert "supporting topic context" in text
    assert "reading budget" in text


def test_do_homework_stage_four_reviews_source_audit_inputs():
    text = read("sub-skills/tasks/do-homework.md")

    stage_four = text.split("4. **Stage 4 review investigation**", 1)[1]
    stage_four = stage_four.split("5. **Stage 5 classify-output**", 1)[0]

    assert "reading_plan.compact.json" in stage_four
    assert "source_findings.compact.md" in stage_four
    assert "source_findings.compact.md" in stage_four
    assert "content scout receipts" in stage_four


def test_runtime_protocol_splits_source_spec_scout_roles():
    text = read("docs/runtime-agent-protocol.md")

    assert "metadata_scout" in text
    assert "content_scout" in text
    assert "parent self-check" in text
    assert "source_findings.compact.md" in text
    assert "body_evidence_fragments/" in text
    assert "Main Agent remains the final reconnaissance judge" in text
    assert "references/syllabus/" not in text


def test_pitfalls_record_generic_proposal_methods_failure_mode():
    text = read("docs/PITFALLS.md")

    assert "proposal framework is not complete reconnaissance" in text
    assert "methods/topic-selection" in text
    assert "source_findings.compact.md" in text


def test_source_body_policy_keeps_ucug1808_only_in_acceptance_context():
    policy_text = "\n".join(
        [
            read("sub-skills/tools/assignment-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "UCUG1808" not in policy_text

    design_text = read("docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md")
    assert "UCUG1808 Acceptance Scenario" in design_text
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py -q
```

Expected: failures because the runtime docs do not yet mention the new audit contract and scout roles.

## Task 2: Update Assignment Recon Contract

**Files:**
- Modify: `sub-skills/tools/assignment-recon.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Add source body audit to the workbench contract**

Update the workbench structure so `investigation/` includes:

```text
│   ├── reading_plan.compact.json
│   ├── source_findings.compact.md
│   ├── _appendix/
│   │   ├── source_index.json
│   │   ├── body_evidence_fragments/
│   │   └── scout_receipts/
```

- [ ] **Step 2: Add Stage 3 source body audit rules**

Add a Stage 3 subsection requiring candidate ranking, bounded `reading_plan.compact.json`, per-content-scout `_appendix/body_evidence_fragments/`, parent-readable `source_findings.compact.md`, `read_mode`, evidence windows, and these classifications:

```text
required | high_signal | supporting | low_signal | forbidden | blocked
precise_match | supporting_context | weak_related | excluded | forbidden | blocked
```

Include the rule that `metadata_only` cannot be used as `precise_match`.

- [ ] **Step 3: Add long-document reading and reference organization rules**

Document that long PDFs/PPTX files use extracted text, keyword windows, page/slide evidence, and escalation to full read only when needed. Add the organized `references/` layout and preserve companion artifacts beside their source. Mention `references/**/*.pdf.links.json` while allowing old flat `references/*.pdf.links.json`.

- [ ] **Step 4: Extend Stage 4 review schema**

Add review fields:

```json
{
  "compact_reading_plan_approved": true,
  "source_findings_checked": true,
  "required_high_signal_body_evidence_checked": true,
  "parent_self_check_complete": true,
  "unread_required_or_high_signal_sources": [],
  "open_ended_coverage": {
    "assignment_spec_body_read": true,
    "methods_or_topic_guidance_body_read": true,
    "supporting_topic_context_checked": true
  }
}
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_assignment_recon_requires_source_body_audit_and_read_modes -q
```

Expected: PASS.

## Task 3: Update Do-Homework Coordinator Contract

**Files:**
- Modify: `sub-skills/tasks/do-homework.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Add artifacts to required chain**

Add:

```text
-> investigation/_appendix/source_index.json
-> investigation/reading_plan.compact.json
-> investigation/_appendix/body_evidence_fragments/
-> investigation/source_findings.compact.md
```

- [ ] **Step 2: Define Main Agent and child scout boundaries**

Document:

```text
The Main Agent approves `reading_plan.compact.json`, dispatches content scouts,
reads `source_findings.compact.md` and exact parent source windows, runs the
parent self-check, and writes final `spec.md`.
Subagents must not write final `spec.md`, `review_a.json`, `pipeline_design.md`,
or user alignment decisions.
```

- [ ] **Step 3: Define dispatch decision rules**

Document when to use:

```text
metadata_scout: non-trivial source-heavy homework; full Canvas/source indexing.
content_scout: required/high_signal body reading or selected supporting context.
parent self-check: proposal/research/open-ended tasks and other non-trivial multi-source runs.
```

- [ ] **Step 4: Add open-ended gate**

Require proposal/research/open-ended runs to have assignment/spec body evidence plus methods/topic-selection evidence before `review_a.verdict: proceed`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_do_homework_defines_main_agent_and_scout_boundaries -q
```

Expected: PASS.

## Task 4: Update Runtime Protocol And Pitfalls

**Files:**
- Modify: `docs/runtime-agent-protocol.md`
- Modify: `docs/PITFALLS.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Update runtime protocol source/spec scout model**

Replace the single broad source/spec scout description with a split model:

```text
metadata_scout
content_scout
parent self-check
```

Include the line:

```text
Main Agent remains the final reconnaissance judge.
```

- [ ] **Step 2: Update runtime workbench contract**

Add `_appendix/source_index.json`, `reading_plan.compact.json`, `_appendix/body_evidence_fragments/`, `source_findings.compact.md`, and organized `references/` guidance. Keep Canvas-native bodies canonical under `canvas/*.json`; any readable syllabus/page export is an optional derived convenience copy, not an evidence gate.

- [ ] **Step 3: Add a generic pitfall**

Add a pitfall section titled:

```text
proposal framework is not complete reconnaissance
```

Explain that proposal/research assignments require methods/topic-selection and course-topic evidence when available.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_runtime_protocol_splits_source_spec_scout_roles tests/test_source_body_audit_policy.py::test_pitfalls_record_generic_proposal_methods_failure_mode tests/test_source_body_audit_policy.py::test_source_body_policy_keeps_ucug1808_only_in_acceptance_context -q
```

Expected: PASS.

## Task 5: Full Policy Verification

**Files:**
- Test: `tests/test_source_body_audit_policy.py`
- Test: `tests/test_pdf_link_annotation_policy.py`
- Test: `tests/test_spec_hard_requirement_policy.py`

- [ ] **Step 1: Run related policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py tests/test_pdf_link_annotation_policy.py tests/test_spec_hard_requirement_policy.py -q
```

Expected: PASS.

- [ ] **Step 2: Inspect git diff**

Run:

```bash
git diff -- docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md docs/superpowers/plans/2026-06-13-homework-source-body-audit.md tests/test_source_body_audit_policy.py sub-skills/tools/assignment-recon.md sub-skills/tasks/do-homework.md docs/runtime-agent-protocol.md docs/PITFALLS.md
```

Expected: only source-body audit design, tests, and runtime policy docs changed.

## Task 6: UCUG1808 Reconnaissance Acceptance Run

**Files:**
- Runtime target: `data/homework/UCUG1808/23014-project-proposal-files`

- [ ] **Step 1: Archive or remove the current workbench**

Before deletion, verify no user-visible draft is needed for this test. Then archive/remove the workbench so the run simulates a first attempt.

- [ ] **Step 2: Dispatch a child agent for a reconnaissance-only do-homework run**

Prompt the child to run `do-homework` for UCUG1808 Project Proposal through reconnaissance only. It must stop before draft production and report child scout dispatches, receipts, and the parent self-check verdict.

- [ ] **Step 3: Verify acceptance criteria**

Check:

```text
metadata_scout indexed all modules and module items
content_scout read direct proposal/final-project files
content_scout read Week 8 research-methods source
parent self-check blocked proceed if methods/topic-selection evidence was absent
source_findings.compact.md exists and contains task-relevant findings with exact pointers
_appendix/body_evidence_fragments/ exists when content scouts ran
prior submitted artifacts stayed forbidden and unread
reading cost stayed bounded
```

- [ ] **Step 4: Iterate if acceptance fails**

If the run misses a high-signal source, over-reads unrelated materials, or relies on Main Agent manual rescue, update the docs/tests and rerun focused verification before accepting the workflow.
